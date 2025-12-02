## Tests Manual

This document explains how regression tests are organized, how they are executed
by the framework, and how to add or debug tests.

---

### 1. Directory Layout

All regression tests live inside the BDF source tree under `package_source/tests`:

- **`tests/input/`**  
  - Contains input files named `testNNN.inp` (e.g. `test001.inp`, `test149.inp`).  
  - Some tests also use **support files** with the same stem, e.g.:
    - `test075.extcharge`
    - `test119.something`

- **`tests/check/`**  
  - Contains reference files named `testNNN.check`.  
  - Each `.check` file consists of `CHECKDATA:...` lines extracted from a
    *known good* run of the corresponding test.

During a run, the framework uses a separate build tree area:

- **`package_source/build/check/`**  
  - The `TestRunner` copies each `testNNN.inp` (and any `testNNN.*` support files)
    from `tests/input/` into this directory.  
  - It runs BDF here and generates:
    - `testNNN.log` – full BDF log for that test
    - `testNNN.check` – extracted `CHECKDATA` lines for comparison

---

### 2. How Tests Are Discovered and Run

The `TestRunner` is configured by the `tests` section in `config/config.yaml`:

```yaml
tests:
  test_dir: "tests/input"
  reference_dir: "tests/check"
  input_pattern: "test*.inp"
  reference_pattern: "test*.check"
  check_pattern: "test*.check"
  test_command: "{BDFHOME}/sbin/bdfdrv.py"
  test_args_template: "-r {input_file}"
  log_file_pattern: "test*.log"
  result_extraction:
    method: "grep"
    pattern: "CHECKDATA"
```

**Discovery:**
- All files in `test_dir` matching `input_pattern` (default `test*.inp`) are
  considered tests.
- For each input:
  - The stem (e.g. `test149`) becomes the **test name**.
  - The reference file is `reference_dir/test149.check`.

**Execution:**
- For each discovered test:
  1. Copy the main input file `testNNN.inp` into `build/check/`.
  2. Copy **all support files** matching `testNNN.*` from `tests/input/` into
     `build/check/` (except the `.inp` itself).  
     This ensures tests with extra files (e.g. `test075.extcharge`) work.
  3. Construct the command:
     - Replace `{BDFHOME}` in `test_command` with the actual installation path
       (e.g. `package_source/build/bdf-pkg-full`).
     - Replace `{input_file}` in `test_args_template` with `testNNN.inp`.
  4. Run the command in `build/check/` with:
     - `BDFHOME`, `BDF_TMPDIR`, and OpenMP settings taken from `tests.env`.
  5. Write the full BDF output to `testNNN.log`.
  6. Extract all lines containing `CHECKDATA` from `testNNN.log` into
     `testNNN.check`.
  7. Compare `build/check/testNNN.check` against `tests/check/testNNN.check`.

**Result:**
- If the process exit code is zero **and** the `.check` files match within
  tolerance, the test **passes**.
- Otherwise the test **fails**, and the differences are shown in logs and reports.

---

### 3. Selecting Which Tests to Run

The `tests` configuration provides several ways to control which tests execute:

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
  profile: null
```

- **`enabled_range`**:
  - Restricts tests to those whose names start with `test` followed by a number
    between `min` and `max` (inclusive).
  - Example: `min: 10`, `max: 20` → run `test010` … `test020`.

- **Profiles (`profiles` + `profile`)**:
  - Named shortcuts for commonly used ranges.
  - If `profile` is set to `smoke`, `core`, or `full`, its min/max override
    `enabled_range`.

You can also bypass `enabled_range` for quick experiments using the CLI:

- **Single test run**:

```bash
python3 -m src.orchestrator run-test test149 --config config/config.yaml
python3 -m src.orchestrator run-test 149 --config config/config.yaml
```

This uses the same environment and comparison as a full run, but only for
one test.

---

### 4. Tolerances and Comparison

The framework uses a dedicated `ResultComparator` that understands BDF
`CHECKDATA` formats. The most important configuration knobs are:

```yaml
tests:
  tolerance_mode: "strict"   # strict | loose
  tolerance_scale:
    strict: 1.0
    loose: 5.0
  tolerance: 1e-6            # Base tolerance (not applied directly to CHECKDATA)
```

- **`tolerance_mode`**:
  - `strict`: Use the built-in per-key CHECKDATA tolerances as-is.
  - `loose`: Multiply all per-key tolerances by `tolerance_scale.loose`.

- **`tolerance`**:
  - A base value for generic comparisons (used sparingly, most logic is
    per-CHECKDATA-key inside `ResultComparator`).

The comparator:
- Handles many CHECKDATA keys with custom absolute or relative tolerances.
- Ignores some known non-critical differences (e.g. certain whitespace-only
  changes or SO2EINT lines).
- Reports mismatches with line numbers, key names, and generated vs reference
  values.

---

### 5. Adding a New Regression Test

To add a new test `testXYZ`:

1. **Create the input file**  
   Place it in `package_source/tests/input/`:

   ```text
   package_source/tests/input/testXYZ.inp
   ```

2. **Run the input once to generate CHECKDATA**  
   You can either:
   - Use the framework:

     ```bash
     python3 -m src.orchestrator run-test testXYZ --config config/config.yaml
     ```

     Then copy the generated `build/check/testXYZ.check` to
     `tests/check/testXYZ.check` if you accept it as the reference.

   - Or run BDF manually and grep CHECKDATA from the `.log` file to build a
     reference `.check` file.

3. **Create the reference file**  
   Save the accepted `CHECKDATA` output as:

   ```text
   package_source/tests/check/testXYZ.check
   ```

4. **Add any support files**  
   If your test needs extra files (e.g. `testXYZ.extcharge`, `testXYZ.xyz`),
   place them alongside the `.inp`:

   ```text
   package_source/tests/input/testXYZ.inp
   package_source/tests/input/testXYZ.extcharge
   ```

   The `TestRunner` automatically copies all `testXYZ.*` files into
   `build/check` before running the test.

5. **Run the test suite**  
   Run either a subset or the full suite and confirm `testXYZ` passes.

---

### 6. Special Cases and Known Patterns

- **Tests using `plotspec.py` (e.g. ECD spectra)**:
  - Some inputs contain shell commands like:

    ```text
    % $BDFHOME/sbin/plotspec.py -cd checkdata=1 wavelength=150-200 fwhm=0.2eV $BDFTASK
    ```

  - The framework ensures:
    - `BDFTASK` is set (e.g. `test149`).
    - The log file (`test149.log`) is created in the working directory during the run,
      so `plotspec.py` can open it successfully.
    - `CHECKDATA:PLOTSPEC:` lines produced by `plotspec.py` are captured into
      `test149.check` and compared against the reference.

- **Support files like `test075.extcharge`**:
  - Any `testNNN.*` file next to `testNNN.inp` in `tests/input` is copied into
    `build/check` automatically.
  - This allows tests to depend on external data without changing the runner.

---

### 7. Debugging Test Failures

When a test fails:

1. **Check the log**  
   - Look at `package_source/build/check/testNNN.log` for detailed BDF output.

2. **Inspect `.check` differences**  
   - The orchestrator logs a summary of differences.
   - For full details, compare:
     - Reference: `tests/check/testNNN.check`
     - Generated: `build/check/testNNN.check`

3. **Use `run-test` for quick iteration**  
   - Rerun just the failing test:

     ```bash
     python3 -m src.orchestrator run-test testNNN --config config/config.yaml
     ```

4. **Adjust tolerances cautiously**  
   - If differences are purely numerical noise, consider:
     - Switching to `tolerance_mode: loose`, or
     - Updating the specific reference `.check` file if the new values are the
       desired ones.

5. **Leverage LLM analysis (optional)**  
   - If `llm.analysis_mode` is `detailed` and LLMs are configured, the
     framework can generate a higher-level explanation of the failure.


