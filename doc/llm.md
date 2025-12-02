## LLM & Error Analysis

This document explains how the framework uses LLMs and structured error events
to analyze build and test failures.

---

### 1. Goals of LLM Integration

- Provide **human‑readable explanations** of failures (build and tests).
- Suggest **concrete debugging steps** (inputs, modules, code areas).
- Incorporate **BDF‑specific domain knowledge** (module relationships, known
  patterns) into the analysis.

The framework is designed so that all core logic (build, tests, comparison)
works **without** an LLM. LLMs are an optional enhancement.

---

### 2. Configuration Recap (`llm` section)

From `config/config.yaml`:

```yaml
llm:
  mode: "auto"             # local | remote | auto
  analysis_mode: "simple"  # simple | detailed
  max_tokens: 2000
  temperature: 0.3

  local:
    enabled: true
    endpoint: "http://localhost:11434"
    model: "my-local-llm"
    timeout: 300

  remote:
    enabled: true
    provider: "openai"     # openai | openrouter | deepseek | groq
    model: "gpt-4o"
    api_key_env: "OPENAI_API_KEY"
```

- **`mode`**:
  - `local`: Only call the local endpoint.
  - `remote`: Only call the remote provider.
  - `auto`: Try local first, then remote as a fallback.
- **`analysis_mode`**:
  - `simple`: No LLM calls; cheap and fast. Extracts key lines and summaries.
  - `detailed`: Use LLM to produce richer, structured analysis.

---

### 3. Error Events: The Bridge to LLMs

Structured error events are defined in `error_event_schema.py`:

```python
class ErrorEvent:
    event_id: str
    timestamp: str
    error_type: ErrorType
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: List[str]
    location: Optional[ErrorLocation]
    context: ErrorContext
    failed_modules: List[str]
    suggestions: List[str]
    metadata: Dict[str, Any]
```

They are produced by `ErrorEventParser`:
- **Build errors**:
  - Analyze `BuildResult.stderr/stdout`.
  - Classify as `BUILD_SETUP`, `COMPILATION`, or `LINKER`.
  - Extract primary error message and key details.
- **Test errors**:
  - For non‑zero exit codes: classify timeout vs runtime vs generic test failure.
  - For comparison mismatches: capture a summary of `CHECKDATA` differences.
  - Detect failed modules based on `Start/End running module` markers.

All error events can be written as JSON in `reports/error_events/` for later
inspection or as few‑shot examples for other AI tools.

---

### 4. Simple vs Detailed Analysis

#### Simple Mode (`analysis_mode: simple`)

- **Build failures**:
  - Extracts:
    - Command and exit code.
    - Key error lines from stderr (matching `error`, `failed`, `fatal`,
      `undefined`, `cannot`).
  - Produces a markdown-like summary (no LLM, no network calls).

- **Test failures**:
  - Extracts:
    - Test name and exit code.
    - Failed modules from logs (`Start/End running module` markers).
    - Keyword‑based error lines (`error`, `failed`, `segmentation`, `abort`, etc.).
    - Comparison differences (truncated if very long).
  - Adds short domain knowledge notes when specific patterns are detected
    (e.g. TDDFT tolerance issues, NMR/NRCC outputs).

This mode is suitable when LLMs are unavailable or for quick local runs.

#### Detailed Mode (`analysis_mode: detailed`)

- **Build failures**:
  - Build a prompt with:
    - Command and exit code.
    - Captured stdout/stderr.
  - Ask the LLM to:
    - Identify root causes.
    - Suggest fixes and next debugging steps.

- **Test failures**:
  - Build a prompt using:
    - Test name, command, exit code.
    - Tail of the log (focusing on failed modules).
    - Comparison differences (`CHECKDATA` mismatches).
    - Domain knowledge (see next section).
  - Ask the LLM to:
    - Provide TL;DR summary.
    - Identify likely failing modules or stages.
    - Propose concrete debugging steps and checks.

The LLM response is then embedded into the HTML/JSON reports and can be
seen as a human‑oriented commentary on top of the raw logs and diffs.

---

### 5. Domain Knowledge Rules

`LLMAnalyzer` enriches prompts with several BDF‑specific hints when it
detects certain modules or patterns:

- **MCSCF ↔ GRAD**:
  - If `mcscf` is detected as a failed module:
    - Explain that the `grad` module **depends on** MCSCF energy.
    - Missing or incomplete `CHECKDATA:GRAD` lines after an MCSCF failure
      are expected; the root cause is usually MCSCF, not GRAD.

- **TDDFT tolerance issues**:
  - If test comparison differences mention `TDDFT` and `tolerance`:
    - Highlight that default TDDFT settings may have changed.
    - Suggest comparing input defaults between reference and current versions.

- **NMR module**:
  - If `nmr` appears in modules or differences:
    - Note that NMR calculations can fail due to known module bugs.
    - Suggest inspecting NMR code paths when there are segmentation faults
      or missing NMR `CHECKDATA` lines.

- **NRCC module**:
  - For CC/NRCC tests with missing or incomplete `CHECKDATA:NRCC`:
    - Mention that NRCC failures may indicate module bugs and point the
      user to NRCC‑specific code areas.

These hints help the LLM focus on plausible root causes instead of treating
all differences as equal.

---

### 6. False Positives and Noise Filtering

To avoid confusing the LLM and error reports with non‑critical messages, the
framework maintains a small **false‑positive library**:

- Lines matching patterns like:

```text
IsOrthogonalizeDiisErrorMatrix = F
```

are treated as **non‑errors** even though they contain the word “error”.

This filtering is applied when:
- Extracting primary error messages from logs.
- Collecting detailed error lines for summaries and LLM prompts.

You can extend this behavior by adding new regexes to the
`FALSE_POSITIVE_PATTERNS` structures in:
- `error_event_parser.py`
- `compilation_analyzer.py`
- `llm_analyzer.py`

---

### 7. How to Interpret LLM Output

When `analysis_mode` is `detailed` and an LLM is configured:

- **Reports include an LLM section**:
  - For builds: under “Build Errors” in the HTML report.
  - For tests: usually appended as an “LLM Analysis” section.

- Typical structure (for tests):
  1. **TL;DR**: Short summary of the main issue (e.g. “TDDFT excitation
     energies differ slightly, likely parameter change rather than bug”).
  2. **Likely root causes**: Module names and brief reasoning.
  3. **Concrete debugging steps**: Commands to rerun, input changes to try,
     log sections or source files to inspect.
  4. **Notes on tolerances vs real bugs**: Whether deviations appear to be
     numerical noise or serious differences.

Always treat the LLM output as **advice**, not as ground truth:
- Cross‑check with logs, `.check` differences, and your knowledge of the code.
- Use it to prioritize investigation, not to automatically accept changes.

---

### 8. When to Enable/Disable LLMs

**Enable LLMs when:**
- You are debugging persistent or complex failures.
- You want fast, human‑readable summaries for long logs.
- You have a reliable local or remote LLM available.

**Disable or use simple mode when:**
- Running tests frequently during development.
- Operating in offline or restricted environments.
- You only need pass/fail and raw differences, not narrative analysis.


