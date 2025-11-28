"""
Main orchestration entrypoint for the BDF Auto Test Framework
"""

import argparse
from pathlib import Path
from typing import Optional, List
import sys
import time

try:
    from .config_loader import ConfigLoader
    from .logger import setup_logger
    from .git_manager import GitManager
    from .build_manager import BuildManager
    from .compile_manager import CompileManager
    from .compilation_analyzer import CompilationAnalyzer
    from .llm_analyzer import LLMAnalyzer
    from .test_runner import TestRunner
    from .report_generator import ReportGenerator
    from .models import BuildResult
except ImportError:  # pragma: no cover
    from config_loader import ConfigLoader  # type: ignore
    from logger import setup_logger  # type: ignore
    from git_manager import GitManager  # type: ignore
    from build_manager import BuildManager  # type: ignore
    from compile_manager import CompileManager  # type: ignore
    from compilation_analyzer import CompilationAnalyzer  # type: ignore
    from llm_analyzer import LLMAnalyzer  # type: ignore
    from test_runner import TestRunner  # type: ignore
    from report_generator import ReportGenerator  # type: ignore
    from models import BuildResult  # type: ignore


def run_workflow(
    config_path: str,
    skip_git: bool = False,
    skip_build: bool = False,
    skip_tests: bool = False,
    profile: Optional[str] = None,
) -> int:
    """
    Execute the full workflow: git pull -> build -> tests -> report
    Returns process exit code (0 success, non-zero failure)
    """
    loader = ConfigLoader(config_path)
    config = loader.load()

    # Optional test profile override from CLI (e.g. --profile smoke, --smoke)
    if profile:
        tests_cfg = config.setdefault("tests", {})
        tests_cfg["profile"] = profile
    logger = setup_logger(config=config)

    # Capture build configuration (compiler and math library settings) for reporting
    build_config = config.get("build", {})
    version_info = None

    git_manager = GitManager(config, logger=logger)
    git_info = None
    if not skip_git:
        logger.info("Step 1: Syncing repository")
        try:
            old_commit, new_commit = git_manager.sync()
            git_info = {
                "remote_url": git_manager.remote_url,
                "branch": git_manager.branch,
                "old_commit": old_commit,
                "new_commit": new_commit,
            }
        except Exception as exc:  # noqa: broad-except
            logger.error("Git sync failed: %s", exc)
            return 1
    else:
        logger.info("Skipping git synchronization step")

    build_manager = BuildManager(config, logger=logger)
    setup_result: Optional[BuildResult] = None
    if not skip_build:
        logger.info("Step 2: Running setup")
        setup_result = build_manager.run()
    else:
        logger.info("Skipping setup step (assumed successful)")
        setup_result = _fake_successful_build(build_manager)

    llm_analyzer = LLMAnalyzer(config, logger=logger)
    report_generator = ReportGenerator(config)

    if not setup_result.success:
        logger.error("Setup failed; analyzing error")
        compilation_analyzer = CompilationAnalyzer(logger=logger)
        build_analysis = compilation_analyzer.analyze(setup_result)
        logger.debug("Compilation analysis: %s", build_analysis)
        llm_analysis = llm_analyzer.analyze_build_failure(setup_result)
        report_generator.generate(
            setup_result,
            test_results=[],
            llm_analysis=llm_analysis,
            git_info=git_info,
            build_config=build_config,
        )
        return 2

    compile_manager = CompileManager(config, logger=logger)
    compile_result = compile_manager.run()
    # Try to read VERSION file from build directory (if present)
    try:
        version_path = compile_manager.working_dir / "VERSION"
        if version_path.exists():
            version_info = version_path.read_text(encoding="utf-8").strip()
    except Exception:
        version_info = None
    if not compile_result.success:
        logger.error("Compilation failed; analyzing error")
        compilation_analyzer = CompilationAnalyzer(logger=logger)
        compile_analysis = compilation_analyzer.analyze(compile_result)
        logger.debug("Compilation analysis: %s", compile_analysis)
        llm_analysis = llm_analyzer.analyze_build_failure(compile_result)
        report_generator.generate(
            compile_result,
            test_results=[],
            llm_analysis=llm_analysis,
            git_info=git_info,
            build_config=build_config,
            version_info=version_info,
        )
        return 3

    test_results = []
    if not skip_tests:
        logger.info("Step 3: Running tests")
        test_runner = TestRunner(config, logger=logger)
        test_results = test_runner.run_all()
    else:
        logger.info("Skipping tests")

    llm_analysis = None
    failed_tests = [result for result in test_results if not result.success]
    if failed_tests:
        logger.warning("%s test(s) failed", len(failed_tests))
        # In simple mode, analyze all failed tests; in detailed mode, analyze first one (LLM is expensive)
        if llm_analyzer.analysis_mode == "simple" and len(failed_tests) > 1:
            # Combine analysis for all failed tests
            analyses = []
            for test_result in failed_tests:
                analysis = llm_analyzer.analyze_test_failure(test_result)
                if analysis:
                    analyses.append(f"### {test_result.test_case.name}\n\n{analysis.summary}")
            if analyses:
                from .models import LLMAnalysis
                combined_summary = "\n\n---\n\n".join(analyses)
                llm_analysis = LLMAnalysis(summary=combined_summary, suggestions=[], raw_response=None)
        else:
            # Detailed mode or single failure: analyze first failed test
            llm_analysis = llm_analyzer.analyze_test_failure(failed_tests[0])
    else:
        logger.info("All tests passed")

    report_generator.generate(
        compile_result,
        test_results,
        llm_analysis,
        git_info=git_info,
        build_config=build_config,
        version_info=version_info,
    )
    return 0 if not failed_tests else 4


def _fake_successful_build(build_manager: BuildManager) -> BuildResult:
    """Create a dummy successful build result when skipping build step"""
    return BuildResult(
        success=True,
        command=[build_manager.build_command],
        cwd=str(build_manager.source_dir),
        exit_code=0,
        stdout="Build skipped",
        stderr="",
        duration=0.0,
        build_dir=build_manager.build_dir,
    )


def compare_reports_command(
    reports_dir: str = "./reports",
    before: Optional[str] = None,
    after: Optional[str] = None,
    n: int = 2,
) -> int:
    """
    Compare test reports
    
    Args:
        reports_dir: Directory containing reports
        before: Path to earlier report (optional, uses Nth latest if not specified)
        after: Path to later report (optional, uses latest if not specified)
        n: Number of reports to compare (if before/after not specified)
    """
    from pathlib import Path
    from .report_comparator import ReportComparator
    
    comparator = ReportComparator(Path(reports_dir))
    
    if before and after:
        comparison = comparator.compare_reports(Path(before), Path(after))
    else:
        comparison = comparator.compare_latest_reports(n)
    
    if not comparison:
        print("Error: Not enough reports to compare. Need at least 2 reports.")
        return 1
    
    # Generate comparison report
    artifacts = comparator.generate_comparison_report(comparison)
    
    print("=== Report Comparison ===")
    print(f"Before: {comparison.before_timestamp}")
    print(f"After: {comparison.after_timestamp}")
    print()
    print("Summary:")
    print(f"  New Failures: {comparison.summary.get('new_failures', 0)}")
    print(f"  Fixed Tests: {comparison.summary.get('fixed', 0)}")
    print(f"  Still Failing: {comparison.summary.get('still_failing', 0)}")
    print(f"  Still Passing: {comparison.summary.get('still_passing', 0)}")
    print(f"  New Tests: {comparison.summary.get('new_tests', 0)}")
    print(f"  Removed Tests: {comparison.summary.get('removed', 0)}")
    print()
    print(f"Comparison report generated:")
    print(f"  HTML: {artifacts.get('html')}")
    print(f"  JSON: {artifacts.get('json')}")
    
    return 0


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BDF Auto Test Framework")
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration file")
    parser.add_argument("--skip-git", action="store_true", help="Skip git pull step")
    parser.add_argument("--skip-build", action="store_true", help="Skip build step")
    parser.add_argument("--skip-tests", action="store_true", help="Skip test step")
    parser.add_argument(
        "--profile",
        help="Override tests.profile from config (e.g. smoke, core, full)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Shortcut for --profile smoke (run small smoke test subset)",
    )
    
    # Report comparison subcommand
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    compare_parser = subparsers.add_parser("compare", help="Compare test reports")
    compare_parser.add_argument("--reports-dir", default="./reports", help="Directory containing reports")
    compare_parser.add_argument("--before", help="Path to earlier report")
    compare_parser.add_argument("--after", help="Path to later report")
    compare_parser.add_argument("-n", type=int, default=2, help="Compare N most recent reports (default: 2)")
    
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "compare":
            return compare_reports_command(
                reports_dir=args.reports_dir,
                before=args.before,
                after=args.after,
                n=args.n,
            )
        else:
            # Determine requested profile override (CLI has precedence over config)
            cli_profile: Optional[str]
            if args.smoke:
                cli_profile = "smoke"
            else:
                cli_profile = args.profile

            return run_workflow(
                config_path=args.config,
                skip_git=args.skip_git,
                skip_build=args.skip_build,
                skip_tests=args.skip_tests,
                profile=cli_profile,
            )
    except KeyboardInterrupt:
        print("Workflow interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())

