## Developer Guide

This guide is for contributors who want to extend or modify the BDF Auto Test Framework.

---

### 1. Code Layout (Quick Recap)

- `src/orchestrator.py` – main CLI and workflow coordinator.
- `src/test_runner.py` – regression test discovery and execution.
- `src/result_comparator.py` – CHECKDATA comparison logic and tolerances.
- `src/compilation_analyzer.py` – build/compile error summarization.
- `src/error_event_schema.py` / `src/error_event_parser.py` – structured error events.
- `src/llm_analyzer.py` – LLM integration and domain knowledge rules.
- `src/report_generator.py` – HTML/JSON report creation.
- `src/models.py` – shared dataclasses (`BuildResult`, `TestResult`, etc.).
- `config/config.yaml(.example)` – configuration.
- `tests/input` / `tests/check` – regression tests and reference data.

See `doc/overview.md` for an architectural overview.

---

### 2. Adding a New CLI Subcommand

The orchestrator uses `argparse` in `src/orchestrator.py`.

Steps to add a new subcommand:

1. **Define the function**  
   Implement the logic near `run_input_command` / `run_single_test_command`.

2. **Extend `parse_args`**  
   Add a subparser:
   ```python
   subparsers = parser.add_subparsers(dest="command", help="Commands")
   new_parser = subparsers.add_parser("my-command", help="Description")
   new_parser.add_argument("--foo", help="Example option")
   ```

3. **Dispatch in `main`**  
   In `main`, add:
   ```python
   elif args.command == "my-command":
       return my_command_function(foo=args.foo, config_path=args.config)
   ```

4. **Document it**  
   - Add a short section to `README.md` and/or `doc/orchestrator.md`.

---

### 3. Extending Result Comparison (`ResultComparator`)

File: `src/result_comparator.py`

Responsibilities:
- Read generated `.check` and reference `.check` files.
- Handle key‑specific tolerances (e.g. `CHECKDATA:HF:ENERGY`, `CHECKDATA:GRAD:GS`).
- Implement special rules (e.g. ignore some lines, treat others as multi‑value).

To add or adjust rules:

1. **Locate tolerance maps** and per‑key logic in `ResultComparator`.
2. **Add new keys** with appropriate absolute or relative tolerances.
3. **Update multi‑value handling** if your key prints multiple floats on one line.
4. **Add tests**:
   - Create small `.check` pairs in `tests/check` or a dedicated test file under a future `tests/` directory for the framework itself.

When changing tolerances, be conservative:
- Prefer adjusting only the affected keys.
- Avoid global tolerance increases unless truly necessary.

---

### 4. Extending Error Parsing & False‑Positive Handling

Files:
- `src/compilation_analyzer.py`
- `src/error_event_parser.py`
- `src/llm_analyzer.py`

These modules:
- Detect error patterns in build/test logs.
- Classify error types and categories.
- Filter out **false positives** – lines that contain words like "error" but are not real failures.

To add a new known non‑error pattern:

1. Add a regex to the relevant `FALSE_POSITIVE_PATTERNS` list, e.g.:
   ```python
   FALSE_POSITIVE_PATTERNS = [
       re.compile(r"(?i)IsOrthogonalizeDiisErrorMatrix\s*=", re.IGNORECASE),
       re.compile(r"(?i)SomeKnownNonErrorPattern", re.IGNORECASE),
   ]
   ```
2. Ensure it is used in:
   - Primary message extraction.
   - Error details collection.
   - Any LLM‑related error line gathering.

Be careful not to over‑filter; make patterns as specific as possible.

---

### 5. Adding Domain Knowledge Rules for LLM Analysis

File: `src/llm_analyzer.py`

Domain knowledge appears in:
- `_test_failure_prompt` (inline text added to the LLM prompt).
- `_build_module_context` (per‑module descriptions).
- Simple analysis in `_simple_test_analysis`.

To add a new module hint:

1. In `_build_module_context`, extend `module_descriptions`:
   ```python
   module_descriptions = {
       "mcscf": "...",
       "grad": "...",
       "mynewmod": "Description of the module and typical failure modes.",
   }
   ```
2. If needed, add special casing in `_test_failure_prompt` or `_simple_test_analysis`
   to append additional notes when that module appears in `failed_modules`
   or in comparison differences.

Keep descriptions short but specific, highlighting:
- What the module does.
- Typical reasons it fails.
- What the user should check first.

---

### 6. Working on Tests & References

The tests them selves are part of the BDF source tree under `package_source/tests`.
See `doc/tests.md` for details.

When you change BDF code:
- Re‑run relevant regression tests (`run-test` is your friend).
- If differences are **expected and acceptable**, update the corresponding
  `tests/check/testNNN.check` from the new `build/check/testNNN.check`.
- If differences are unexpected, investigate before modifying references.

---

### 7. Development Workflow Suggestions

1. **Local iteration**
   - Start with `--skip-git --skip-build` once the build is stable.
   - Use `run-test` to focus on affected tests.

2. **Logging**
   - Set `logging.level` to `DEBUG` in `config.yaml` when debugging framework
     logic; reset to `INFO` afterwards.

3. **Git usage**
   - Make small, focused commits:
     - One for comparison logic changes.
     - One for LLM prompt/domain‑knowledge changes.
     - One for orchestrator/CLI changes.

4. **Documentation**
   - Keep `doc/` in sync with behavior:
     - When you add a new option or subcommand, update the relevant doc file.


