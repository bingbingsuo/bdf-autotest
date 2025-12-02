## Orchestrator CLI Manual

The `orchestrator` module is the main entry point for the BDF Auto Test Framework.
It coordinates build, tests, reports, and provides utility subcommands.

### 1. Full Workflow

Run the complete CI-style workflow:

```bash
python3 -m src.orchestrator --config config/config.yaml
```

This performs:
- Git sync (unless `--skip-git`)
- Setup / build
- Compile (typically `make install`)
- Run regression tests
- Generate HTML/JSON reports

Common variations:

```bash
# Use existing source (no git pull)
python3 -m src.orchestrator --config config/config.yaml --skip-git

# Assume package already built (skip setup/build)
python3 -m src.orchestrator --config config/config.yaml --skip-git --skip-build

# Only build, do not run tests
python3 -m src.orchestrator --config config/config.yaml --skip-tests

# Use a specific test profile from config.tests.profiles
python3 -m src.orchestrator --config config/config.yaml --profile smoke
```

### 2. `run-input`: Single BDF Calculation

The `run-input` subcommand runs a **single BDF input file** independent of the
regression test machinery:

```bash
python3 -m src.orchestrator run-input /path/to/input.inp --config config/config.yaml
```

Requirements and behavior:
- Input file **must** have a `.inp` extension.
- The framework locates `BDFHOME` from the build configuration and verifies that BDF
  has been installed under `package_source/build/bdf-pkg-full`.
- By default, the **working directory** is the directory of the input file.  
  You can override this by setting `tests.env.BDF_WORKDIR` in `config.yaml`.
- A temporary directory for scratch files is taken from `tests.env.BDF_TMPDIR`
  (supports `$RANDOM`), or falls back to the system temp directory.
- Output files:
  - `{stem}.log`: Standard output
  - `{stem}.err`: Standard error
  - `{stem}.out.tmp`: Detailed BDFOPT output, if present
- If the working directory differs from the input directory, the code will copy
  the input and all support files with the same stem (`stem.*`) into the work
  directory so that BDF can find everything it needs.

Example:

```bash
python3 -m src.orchestrator run-input /home/user/bdf-tests/h2o.inp --config config/config.yaml
```

After completion, the console will list all generated files in the working directory.

### 3. `run-test`: Single Regression Test

The `run-test` subcommand reruns **one test from the regression suite** (located
under `package_source/tests/input`) using the same environment and comparison rules
as a full test run.

```bash
# Run by full test name
python3 -m src.orchestrator run-test test149 --config config/config.yaml

# Run by numeric id (normalized to test149)
python3 -m src.orchestrator run-test 149 --config config/config.yaml
```

Key points:
- Uses the configuration in `config.yaml` (no need to change `tests.enabled_range`).
- Discovers all `test*.inp` files, then selects the requested test by name.
- Executes it via the `TestRunner`:
  - Input and all support files with the same stem (`testXXX.*`) are copied to
    `package_source/build/check`.
  - The test is run there with proper `BDFHOME`, `BDF_TMPDIR`, OpenMP settings, etc.
  - A `.check` file is generated from the log and compared against
    `tests/check/testXXX.check`.
- On success: prints a short **PASSED** summary.  
  On failure: prints **CHECKDATA** differences so you can see exactly what changed.

### 4. `compare`: Report Comparison

Compare test reports across runs:

```bash
# Compare the latest 2 reports in ./reports
python3 -m src.orchestrator compare -n 2

# Compare specific JSON reports
python3 -m src.orchestrator compare --before reports/report_A.json --after reports/report_B.json

# Use a custom reports directory
python3 -m src.orchestrator compare --reports-dir ./reports -n 3
```

This generates a comparison report summarizing:
- New failures
- Fixed tests
- Still failing / still passing tests
- New and removed tests

### 5. Exit Codes (High Level)

- `0`: Full workflow completed and all tests passed (or single test passed).
- `1`: Git or configuration errors, or a single test requested by `run-test` failed.
- `2`: Setup/build stage failed.
- `3`: Compilation stage failed.
- `4`: Tests executed but at least one regression test failed in the full workflow.


