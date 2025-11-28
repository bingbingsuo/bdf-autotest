"""
Test runner: discover test inputs, execute commands, and compare results
"""

import logging
import os
import random
import shlex
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Optional

from .models import TestCase, TestResult, CommandResult, ComparisonResult
from .result_comparator import ResultComparator
from .utils import resolve_source_path, wildcard_to_name


class TestRunner:
    """Execute tests defined by input/reference patterns"""

    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.config = config
        self.build_cfg = config.get("build", {})
        self.tests_cfg = config.get("tests", {})
        self.source_dir = Path(self.build_cfg.get("source_dir", "./package_source")).resolve()
        # build/check directory inside the build tree for all test artefacts
        self.build_dir = self.source_dir / self.build_cfg.get("build_dir", "build")
        # Installed package root for BDFHOME
        self.bdf_home = self.build_dir / "bdf-pkg-full"
        self.check_dir = self.build_dir / "check"
        self.check_dir.mkdir(parents=True, exist_ok=True)

        # Environment configuration (including a single scratch directory)
        self.env_cfg = self.tests_cfg.get("env", {})
        tmp_template = str(self.env_cfg.get("BDF_TMPDIR", "/tmp/$RANDOM"))
        rnd = random.randint(0, 999999)
        self.tmp_dir = Path(tmp_template.replace("$RANDOM", str(rnd)))
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

        self.test_dir = self.tests_cfg.get("test_dir", "tests/input")
        self.reference_dir = self.tests_cfg.get("reference_dir", "tests/check")
        self.input_pattern = self.tests_cfg.get("input_pattern", "test*.inp")
        # Reference and check file patterns (both *.check)
        self.reference_pattern = self.tests_cfg.get("reference_pattern", "test*.check")
        self.check_pattern = self.tests_cfg.get("check_pattern", "test*.check")
        self.log_pattern = self.tests_cfg.get("log_file_pattern", "test*.log")
        self.test_command_template = self.tests_cfg.get("test_command", "{BDFHOME}/sbin/bdf.drv")
        self.test_args_template = self.tests_cfg.get("test_args_template", "-r {input_file}")
        self.test_args_template_list = shlex.split(self.test_args_template)
        self.result_pattern = self.tests_cfg.get("result_extraction", {}).get("pattern", "DATACHECK")
        # Optional named test profiles (smoke/core/full) and enabled range
        self.profiles_cfg = self.tests_cfg.get("profiles", {})
        self.current_profile = self.tests_cfg.get("profile")
        tolerance = self.tests_cfg.get("tolerance", 0.0)
        mode = self.tests_cfg.get("tolerance_mode", "strict")
        scale_cfg = self.tests_cfg.get("tolerance_scale", {})
        scale_map = {
            "strict": float(scale_cfg.get("strict", 1.0)),
            "loose": float(scale_cfg.get("loose", 5.0)),
        }
        self.comparator = ResultComparator(tolerance=tolerance, mode=mode, scale_map=scale_map)
        self.timeout = self.tests_cfg.get("timeout", 3600)
        # Max number of tests to run in parallel (1 = sequential)
        self.max_parallel = int(self.tests_cfg.get("max_parallel", 1) or 1)

        # Derive a sensible default for OMP_NUM_THREADS if not set in config:
        # use (num_cores / max_parallel), at least 1.
        cores = os.cpu_count() or 1
        if "OMP_NUM_THREADS" not in self.env_cfg:
            per_test_threads = max(1, cores // max(self.max_parallel, 1))
            self.env_cfg["OMP_NUM_THREADS"] = per_test_threads
        self.logger = logger or logging.getLogger("bdf_autotest.tests")

    def discover_tests(self) -> List[TestCase]:
        """Find all tests matching the glob pattern"""
        test_path = resolve_source_path(self.source_dir, self.test_dir)
        reference_path = resolve_source_path(self.source_dir, self.reference_dir)
        input_files = sorted(test_path.glob(self.input_pattern))
        cases = []

        # Optional numeric range filter for enabled tests (e.g. 1-20)
        range_cfg = self.tests_cfg.get("enabled_range", {})
        min_id = range_cfg.get("min")
        max_id = range_cfg.get("max")

        # If a named profile is selected, override min/max with profile settings
        if self.current_profile and isinstance(self.profiles_cfg, dict):
            prof = self.profiles_cfg.get(self.current_profile)
            if prof:
                prof_min = prof.get("min")
                prof_max = prof.get("max")
                if prof_min is not None:
                    min_id = prof_min
                if prof_max is not None:
                    max_id = prof_max

        for input_file in input_files:
            name = input_file.stem

            # Apply enabled_range filter if configured
            if name.startswith("test") and (min_id is not None or max_id is not None):
                try:
                    idx = int(name[4:])
                except ValueError:
                    idx = None
                if idx is not None:
                    if min_id is not None and idx < min_id:
                        continue
                    if max_id is not None and idx > max_id:
                        continue

            check_input = self.check_dir / input_file.name
            shutil.copy2(input_file, check_input)

            log_name = wildcard_to_name(self.log_pattern, name)
            log_file = self.check_dir / log_name

            # Reference file is tests/check/testXXX.check
            reference_file = reference_path / f"{name}.check"

            command = self._build_command(check_input.name)
            cases.append(
                TestCase(
                    name=name,
                    input_file=check_input,
                    log_file=log_file,
                    reference_file=reference_file,
                    command=command,
                )
            )

        self.logger.info("Discovered %s test(s)", len(cases))
        return cases

    def _build_command(self, input_name: str) -> List[str]:
        command_str = self.test_command_template.replace("{BDFHOME}", str(self.bdf_home))
        command = shlex.split(command_str)
        args = [arg.format(input_file=input_name) for arg in self.test_args_template_list]
        command.extend(args)
        return command

    def run_all(self) -> List[TestResult]:
        """Run all discovered tests (optionally in parallel)."""
        results: List[TestResult] = []
        cases = self.discover_tests()
        try:
            if not cases:
                return []

            if self.max_parallel <= 1:
                # Sequential execution (default, preserves previous behavior)
                for case in cases:
                    result = self._run_test_case(case)
                    results.append(result)
            else:
                # Parallel execution with ThreadPoolExecutor
                self.logger.info("Running tests in parallel with max_parallel=%s", self.max_parallel)
                with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
                    future_to_case = {executor.submit(self._run_test_case, case): case for case in cases}
                    for future in as_completed(future_to_case):
                        case = future_to_case[future]
                        try:
                            result = future.result()
                        except Exception as exc:  # noqa: BLE001
                            self.logger.error("Test %s raised an exception: %s", case.name, exc)
                            # Create a failure result stub if something unexpected happens
                            duration = 0.0
                            result = TestResult(
                                success=False,
                                command=case.command,
                                cwd=str(self.source_dir),
                                exit_code=1,
                                stdout="",
                                stderr=str(exc),
                                duration=duration,
                                test_case=case,
                            )
                        results.append(result)
        finally:
            # Clean up scratch directory after all tests
            try:
                if self.tmp_dir.exists():
                    shutil.rmtree(self.tmp_dir)
            except Exception:
                # Do not fail the whole run if cleanup fails
                self.logger.warning("Failed to remove scratch directory %s", self.tmp_dir)
        return results

    def _run_test_case(self, case: TestCase) -> TestResult:
        self.logger.info("Running test %s", case.name)
        case.log_file.parent.mkdir(parents=True, exist_ok=True)
        start_time = time.monotonic()

        # Prepare environment variables
        env = os.environ.copy()
        # BDFHOME: installed package directory
        env["BDFHOME"] = str(self.bdf_home)
        # BDF_TMPDIR: per-test scratch directory under the global tmp_dir
        case_tmp_dir = self.tmp_dir / case.name
        case_tmp_dir.mkdir(parents=True, exist_ok=True)
        env["BDF_TMPDIR"] = str(case_tmp_dir)
        # OpenMP settings with defaults
        env["OMP_NUM_THREADS"] = str(self.env_cfg.get("OMP_NUM_THREADS", 8))
        env["OMP_STACKSIZE"] = str(self.env_cfg.get("OMP_STACKSIZE", "512M"))
        # Any additional env keys from config.env
        for key, value in self.env_cfg.items():
            if key not in {"BDF_TMPDIR", "OMP_NUM_THREADS", "OMP_STACKSIZE"}:
                env[str(key)] = str(value)

        process = subprocess.run(
            case.command,
            cwd=self.check_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )

        duration = time.monotonic() - start_time

        test_result = TestResult(
            success=process.returncode == 0,
            command=case.command,
            cwd=str(self.source_dir),
            exit_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            duration=duration,
            test_case=case,
        )

        case.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(case.log_file, "w", encoding="utf-8") as log_f:
            log_f.write(process.stdout or "")
        if process.stderr:
            with open(case.log_file, "a", encoding="utf-8") as log_f:
                log_f.write("\n--- STDERR ---\n")
                log_f.write(process.stderr)

        check_file = self._extract_check_file(case)
        # Use specialized CHECKDATA comparison with per-key tolerances
        comparator_result = self.comparator.compare_check_files(check_file, case.reference_file)
        test_result.comparison = comparator_result
        test_result.success = test_result.success and comparator_result.matched

        if test_result.success:
            self.logger.info("Test %s passed", case.name)
        else:
            self.logger.error("Test %s failed", case.name)
        return test_result

    def _extract_check_file(self, case: TestCase) -> Path:
        """
        Extract CHECKDATA lines from the log file into a .check file.
        Equivalent to: grep CHECKDATA testXXX.log > testXXX.check
        """
        pattern = self.result_pattern
        check_name = wildcard_to_name(self.check_pattern, case.name)
        check_file = self.check_dir / check_name
        matched_lines: List[str] = []
        for line in case.log_file.read_text().splitlines():
            if pattern in line:
                matched_lines.append(line.strip())
        check_file.write_text("\n".join(matched_lines))
        return check_file

