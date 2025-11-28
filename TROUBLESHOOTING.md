# Troubleshooting Guide - BDF Auto Test Framework

This guide summarizes common problems you may encounter when running the BDF Auto Test Framework and how to fix them.

---

## 1. Configuration Issues

### 1.1 Validation errors when loading `config.yaml`

**Symptom**: The orchestrator exits with an error like:

- `Configuration validation failed: ...`
- Messages about missing keys or wrong types (e.g. `'tests.tolerance' must be a number.`)

**Causes & Fixes**:

- **String vs number**:
  - If you see a message like `'tests.tolerance' must be a number.`:
    - Make sure numeric values are valid numbers (e.g. `1e-6`, `0.3`, `8`) and not empty strings.
    - Example (correct):
      ```yaml
      tests:
        tolerance: 1e-6
      ```

- **Missing required keys**:
  - Example errors:
    - `Missing required key 'build.compiler_set'.`
    - `Missing required key 'build.math_library.mathinclude_flags'.`
  - Check that your `config.yaml` contains all required keys:
    - `git.remote_url`, `git.branch`, `git.local_path`
    - `build.source_dir`, `build.build_dir`, `build.build_command`, `build.compiler_set`
    - `build.compilers.<set>.fortran`, `.c`, `.cpp`
    - If `build.use_mkl: false`, ensure `build.math_library` has `mathinclude_flags`, `mathlib_flags`, `blasdir`, `lapackdir`.

- **Enabled ranges**:
  - If you see errors about `tests.enabled_range.min` or `.max`:
    - Ensure they are positive integers and `min <= max`:
      ```yaml
      tests:
        enabled_range:
          min: 1
          max: 20
      ```

**How to re-check**:

```bash
python3 - << 'EOF'
from src.config_loader import ConfigLoader
ConfigLoader('config/config.yaml').load()
print("Config OK")
EOF
```

---

## 2. Git / Repository Problems

### 2.1 Git clone/pull fails (SSH issues)

**Symptoms**:
- `Permission denied (publickey)`
- `Could not resolve hostname ...`
- `Repository not found`

**Checks**:
- Ensure you can clone the repository manually using the same URL as in `config.yaml`:
  ```bash
  git clone "ssh://user@host:port/path/to/repo"
  ```
- Confirm your SSH keys are configured and loaded (`ssh-agent`, `ssh-add`).
- If running in CI, ensure CI has access to the repository (deploy keys or PAT if using HTTPS).

**Workarounds**:
- Use `--skip-git` with the orchestrator if the local `package_source` is already up to date:
  ```bash
  python3 -m src.orchestrator --config config/config.yaml --skip-git
  ```

---

## 3. Setup / Build Problems

### 3.1 `./setup` fails, or build directory issues

**Symptoms**:
- `build directory ... already exists`
- CMake errors in `setup.log`

**What the framework does**:
- `BuildManager` automatically **removes** the existing build directory before running `./setup` to ensure a fresh build.
- All setup output is written to `build/setup.log`.

**What to check**:
- Run setup manually to inspect errors:
  ```bash
  cd package_source
  ./setup ...  > setup.log 2>&1
  ```
- Inspect `package_source/build/setup.log` for:
  - Missing compilers (`gfortran`, `gcc`, `g++`, etc.)
  - Missing BLAS/LAPACK libraries
  - Wrong `--mathinclude-flags` or `--mathlib-flags`

**Quick fixes**:
- Confirm paths in `build.math_library` are correct.
- Ensure compilers (`gfortran`, `ifx`, etc.) are in `PATH`.

---

## 4. Compile (`make`) Problems

### 4.1 `make` fails or exits with non-zero status

**Symptoms**:
- The orchestrator logs: `Compilation failed; analyzing error`
- `make` errors in `package_source/build/make.log`

**What to do**:
- Open `package_source/build/make.log` and search for:
  - `error:`
  - `undefined reference`
  - Missing headers or libraries.

**Common issues**:
- Incompatible BLAS/LAPACK versions.
- Missing `-fPIC` or other required flags in vendor math libraries.

---

## 5. LLM Issues (Local & Remote)

### 5.1 Local LLM timeouts or connection errors

**Symptoms**:
- `Local LLM request failed ... Read timed out`
- `Connection refused` to local endpoint

**Checks**:
- Verify the local LLM server is running and the endpoint in `config.yaml` is correct:
  ```yaml
  llm:
    local:
      enabled: true
      endpoint: "http://192.168.6.230:11434"
      model: "gpt-oss:120b"
      timeout: 300
  ```
- Try a simple curl test:
  ```bash
  curl http://192.168.6.230:11434
  ```

**Adjust timeout**:
- Increase `llm.local.timeout` in `config.yaml` if the model is slow:
  ```yaml
  timeout: 300
  ```

### 5.2 Remote LLM (OpenAI) errors

**Symptoms**:
- `Remote LLM API key not found in environment variable OPENAI_API_KEY`

**Fix**:
- Set the environment variable before running the orchestrator:
  ```bash
  export OPENAI_API_KEY="your_real_key"
  python3 -m src.orchestrator --config config/config.yaml
  ```

---

## 6. Test Execution Problems

### 6.1 Wrong test executable or BDFHOME

**Symptoms**:
- `FileNotFoundError` for `bdfdrv.py` or other executables.

**Checks**:
- Ensure `tests.test_command` in `config.yaml` is correct:
  ```yaml
  tests:
    test_command: "{BDFHOME}/sbin/bdfdrv.py"
  ```
- Confirm BDF is installed in `build/bdf-pkg-full` and that `bdfdrv.py` exists in `sbin/`.

### 6.2 Scratch directory (`BDF_TMPDIR`) issues

**Symptoms**:
- Errors about writing scratch files.

**Behavior**:
- `TestRunner` creates one `BDF_TMPDIR` per run and deletes it at the end.

**Fixes**:
- Ensure `BDF_TMPDIR` in `config.yaml` points to a writable filesystem:
  ```yaml
  tests:
    env:
      BDF_TMPDIR: "/tmp/$RANDOM"
  ```

---

## 7. Test Result / Comparison Problems

### 7.1 Mismatched check files (`*.check`)

**Symptoms**:
- Reports show differences like:
  - `Line count differs between generated and reference`

**Checks**:
- Confirm `reference_pattern` and `check_pattern` in `config.yaml` are correct:
  ```yaml
  tests:
    reference_pattern: "test*.check"
    check_pattern: "test*.check"
  ```
- Ensure the reference files (`tests/check/testNNN.check`) exist and match the intended format.

### 7.2 Specific CHECKDATA tolerances

**Symptoms**:
- Failing tests due to small numerical differences.

**Controls**:
- Tolerance mode and scaling:
  ```yaml
  tests:
    tolerance_mode: "strict"  # or "loose"
    tolerance_scale:
      strict: 1.0
      loose: 5.0
  ```
- Some keys (e.g. `ELECOUP`, specific GRAD/MCSCF keys) have per-key tolerances; others use base rules.

### 7.3 Confusion between `enabled_range` and profiles

**Symptoms**:
- You change `tests.enabled_range` but the set of tests that run does not change.
- Only `test001`–`test020` run even though `enabled_range.max` is larger, or vice versa.

**How it works**:
- If `tests.profile` is set (e.g. `core`, `smoke`, `full`), the selected profile’s `min`/`max` **override** `enabled_range.min`/`max`.
- If `tests.profile` is **not** set, `enabled_range` controls which `testNNN` are enabled.

**Fixes**:
- To use profiles:
  ```yaml
  tests:
    enabled_range:
      min: 1
      max: 161
    profiles:
      smoke:
        min: 1
        max: 5
      core:
        min: 1
        max: 20
      full:
        min: 1
        max: 161
    profile: core  # active profile
  ```
- To use only `enabled_range` and ignore profiles, either:
  - Remove or comment out `tests.profile`, or
  - Remove `tests.profiles` entirely.

---

## 8. LLM Analysis & Module Detection

### 8.1 Module detection seems wrong

**How it works**:
- The analyzer scans test log files for:
  - `Start running module <name>`
  - `End running module <name>`
- A module is considered failed if it has **Start** but no **End**.

**Checks**:
- Open `build/check/testNNN.log` and verify that:
  - The expected `Start running module <name>` / `End running module <name>` lines exist.

If the pattern changes in future BDF versions, you may need to adapt `_detect_failed_modules` in `src/llm_analyzer.py`.

---

## 9. CI / GitHub Actions Issues

### 9.1 CI fails due to environment or missing libraries

**Symptoms**:
- GitHub Actions job fails at build or test steps.

**Checks**:
- Open the CI logs and check:
  - `apt-get install` steps: BLAS/LAPACK, gfortran installed?
  - Python dependency installation: `pip install -r requirements.txt` succeeded?

**Adjustments**:
- If BDF cannot be fully built in CI (e.g., due to heavy mathlibs), you can:
  - Run a smaller smoke test subset (adjust `tests.enabled_range`).
  - Or run only some stages (e.g., `--skip-tests` in CI).

---

If you encounter an issue that is not covered here, check:

- Latest log in `logs/`
- Corresponding report in `reports/`

and we can extend this guide based on your new findings.


