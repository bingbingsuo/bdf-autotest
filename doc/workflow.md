## Workflow Tutorials & Examples

This document shows common end‑to‑end workflows using the BDF Auto Test Framework.

---

### 1. Fresh Setup and Full Regression Run

**Goal:** Clone/update BDF, build it, run all configured regression tests, and
generate reports.

1. **Prepare config**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config/config.yaml: git.remote_url, compilers, math_library, etc.
   ```

2. **Install Python dependencies**
   ```bash
   pip3 install --user -r requirements.txt
   ```

3. **Run the full workflow**
   ```bash
   python3 -m src.orchestrator --config config/config.yaml
   ```

4. **Inspect results**
   - HTML report: `reports/report_YYYY-MM-DD_HH-MM-SS.html`
   - JSON report: `reports/report_YYYY-MM-DD_HH-MM-SS.json`
   - Logs: `logs/autotest_YYYY-MM-DD_HH-MM-SS.log`

If any tests fail, the report shows which ones and the detailed `CHECKDATA`
differences.

---

### 2. Rebuild and Rerun Tests After Code Changes

**Goal:** You modified BDF source code and want to recompile and rerun tests.

1. **Pull or modify code in `package_source/`** as usual.

2. **Rebuild and rerun tests**
   ```bash
   # Skip git sync if the source is already up to date
   python3 -m src.orchestrator --config config/config.yaml --skip-git
   ```

3. **Optional:** If you did not touch the build system and just want to rerun
   tests:
   ```bash
   python3 -m src.orchestrator --config config/config.yaml --skip-git --skip-build
   ```

Use the new report to compare with previous runs (see Workflow 5).

---

### 3. Run a Single Regression Test (`run-test`)

**Goal:** Quickly rerun one `testNNN` without editing `config.yaml`.

Examples:

```bash
# Run test149 by full name
python3 -m src.orchestrator run-test test149 --config config/config.yaml

# Run the same test by numeric id (auto-normalized to test149)
python3 -m src.orchestrator run-test 149 --config config/config.yaml
```

What happens:
- The framework loads `config.yaml` and discovers all tests.
- It selects `test149` and:
  - Copies `tests/input/test149.inp` and all `test149.*` support files into
    `build/check`.
  - Runs BDF there via `bdfdrv.py`.
  - Extracts `CHECKDATA` from `test149.log` into `build/check/test149.check`.
  - Compares against `tests/check/test149.check`.
- It prints a short **PASSED/FAILED** summary and, on failure, the detailed
  `CHECKDATA` differences.

This is ideal for iterating on a single failing test.

---

### 4. Run a User Input File (`run-input`)

**Goal:** Run any `.inp` file (not necessarily part of the regression suite),
with correct BDF environment, and collect its outputs.

Example:

```bash
python3 -m src.orchestrator run-input /home/user/bdf-tests/hf-h2o.inp --config config/config.yaml
```

Behavior:
- Checks that the file exists and has `.inp` extension.
- Uses `tests.env.BDF_WORKDIR` if configured; otherwise uses the input file’s
  directory as the working directory.
- Sets `BDFHOME` and `BDF_TMPDIR` appropriately.
- Writes:
  - `/home/user/bdf-tests/hf-h2o.log` (stdout)
  - `/home/user/bdf-tests/hf-h2o.err` (stderr)
  - `/home/user/bdf-tests/hf-h2o.out.tmp` (if BDFOPT produces it)
- At the end, prints a summary and lists all generated files.

Tip: If your input needs support files (e.g. `hf-h2o.extcharge`), place them in
the same directory as the `.inp` file.

---

### 5. Compare Two Test Runs (`compare`)

**Goal:** See how test results changed between two runs (e.g. after a code
change).

1. **Run the workflow twice** (e.g. before and after your change).  
   Each run generates a report in `reports/`.

2. **Compare the latest two reports**
   ```bash
   python3 -m src.orchestrator compare -n 2
   ```

   or specify reports explicitly:

   ```bash
   python3 -m src.orchestrator compare \
     --before reports/report_2025-12-01_13-17-16.json \
     --after  reports/report_2025-12-02_12-21-18.json
   ```

3. **Open the comparison report**  
   The generated comparison HTML/JSON summarizes:
   - New failures
   - Fixed tests
   - Still failing / still passing tests
   - New and removed tests

---

### 6. Using Test Profiles (Smoke/Core/Full)

**Goal:** Run smaller subsets of tests (quick smoke vs core vs full).

Configure profiles in `tests.profiles` and `tests.profile` in `config.yaml`
(see `doc/configuration.md`), then:

```bash
# Use the "smoke" profile via CLI
python3 -m src.orchestrator --config config/config.yaml --profile smoke

# Shortcut flag for smoke (equivalent to --profile smoke)
python3 -m src.orchestrator --config config/config.yaml --smoke
```

This is useful for:
- Fast checks during development (`smoke`).
- Deeper but still partial runs (`core`).
- Full regression prior to commits/releases (`full`).


