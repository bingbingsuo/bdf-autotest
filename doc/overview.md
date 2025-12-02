## BDF Auto Test Framework – Overview & Architecture

This document gives a high-level view of the framework: the main components,
how they interact, and the overall data flow from build to reports.

---

### 1. High-Level Goals

- Automate **build + regression tests** for the BDF package.
- Provide **stable, tolerance‑aware comparisons** of numerical results.
- Capture **structured error events** for downstream AI tools.
- Optionally use **LLMs** to explain failures and suggest debugging steps.

---

### 2. Main Components

- **`orchestrator.py`**  
  - CLI entrypoint and high-level workflow controller.
  - Steps:
    1. Load `config/config.yaml`.
    2. Sync git (optional).
    3. Run setup/build and compile.
    4. Run regression tests with `TestRunner`.
    5. Parse errors into structured events (`ErrorEventParser`).
    6. Optionally call LLMs (`LLMAnalyzer`) for analysis.
    7. Generate reports (`ReportGenerator`).

- **`test_runner.py` (`TestRunner`)**  
  - Discovers test inputs (`test*.inp`) and executes them under controlled
    environment settings.
  - Manages per-test working directories (`build/check`), log files, and
    extraction of `CHECKDATA` lines into `.check` files.

- **`result_comparator.py` (`ResultComparator`)**  
  - Compares generated `.check` files against reference `.check` files with
    per-key tolerances and domain-specific rules.
  - Produces structured `ComparisonResult` objects.

- **`compilation_analyzer.py` (`CompilationAnalyzer`)**  
  - Summarizes compile errors and extracts representative error snippets for
    logs and LLM analysis.

- **`error_event_schema.py` / `error_event_parser.py`**  
  - Define the `ErrorEvent` schema and convert raw build/test output into
    structured error events (with type, category, severity, context, etc.).

- **`llm_analyzer.py` (`LLMAnalyzer`)**  
  - Interfaces with local/remote LLMs according to `llm` config.
  - Builds prompts from logs, comparison differences, and error context.
  - Adds domain-specific knowledge (e.g. MCSCF/GRAD relationship, TDDFT
    defaults, NMR/NRCC behavior).

- **`report_generator.py` (`ReportGenerator`)**  
  - Produces HTML and JSON summaries of build + test results.
  - Integrates error events and optional LLM analysis into human‑readable
  reports.

---

### 3. Data Flow (Full Workflow)

At a high level:

```text
config/config.yaml
        │
        ▼
   Orchestrator
        │
        ├─► GitManager: sync source (optional)
        │
        ├─► BuildManager: ./setup (configure build)
        │
        ├─► CompileManager: make install
        │
        └─► TestRunner: run test*.inp
                 │
                 ├─► BDF executables (via bdfdrv.py)
                 │     └─► test logs (testNNN.log) in build/check
                 │
                 └─► ResultComparator:
                         compare build/check/testNNN.check
                         vs tests/check/testNNN.check
```

If there are failures:

```text
Failed Build/Test
        │
        ├─► ErrorEventParser: convert logs → ErrorEvent JSON
        │
        ├─► LLMAnalyzer (optional): explain failure & suggest fixes
        │
        └─► ReportGenerator: include errors + LLM analysis in reports
```

---

### 4. Execution Modes

- **Full regression (`orchestrator` main mode)**  
  - Runs build + all selected tests according to config (`enabled_range` / `profile`).
  - Produces summary + detailed HTML/JSON reports.

- **Single BDF run (`run-input`)**  
  - Runs one `.inp` file directly with appropriate `BDFHOME` and environment.
  - Meant for ad‑hoc calculations outside the regression suite.

- **Single regression test (`run-test`)**  
  - Reruns exactly one `testNNN` from the regression set using the same logic
    as a full test run.
  - Useful for debugging a specific failing test.

- **Report comparison (`compare`)**  
  - Compares two reports (latest N or specific files) to identify new
    failures, fixed tests, and overall trend.

---

### 5. Error Handling & AI Integration (Brief)

- **Structured error events**:  
  - Builds `ErrorEvent` objects with:
    - `error_type` (build, compilation, linker, test_execution, test_comparison, runtime…)
    - `severity` and `category` (syntax, numerical, convergence, module_failure, etc.)
    - Context (command, working dir, git info, modules, etc.)
  - Stored as JSON under `reports/error_events/`.

- **LLM analysis**:
  - When enabled, `LLMAnalyzer` builds prompts that include:
    - Command + exit code.
    - Key portions of stdout/stderr or comparison differences.
    - Detected modules and BDF‑specific hints (e.g. MCSCF/GRAD, TDDFT defaults).
  - The response is summarized and embedded into reports.

For deeper details, see:
- `doc/configuration.md` – configuration of each component.
- `doc/tests.md` – how tests and comparisons work.
- `doc/orchestrator.md` – CLI usage and subcommands.


