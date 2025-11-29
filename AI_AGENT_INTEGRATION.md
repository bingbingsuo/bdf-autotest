# BDF Auto Test - AI Agent Integration Guide

This document describes the structured error event system designed for integration with BDFDev AI Agent.

## Overview

The BDF Auto Test framework now outputs structured error events in JSON format, enabling:
- **Unified Schema**: Consistent error representation across all failure types
- **Structured Parsing**: Abstracted log parsing into error events
- **Prompt Templates**: Pre-built prompts with few-shot learning examples
- **Validation Framework**: Tools to verify effectiveness with real failure samples

## Error Event Schema

All errors are represented using the unified `ErrorEvent` schema defined in `src/error_event_schema.py`:

```python
{
    "event_id": "evt_abc123...",
    "timestamp": "2025-11-29T12:00:00Z",
    "error_type": "compilation|linker|test_execution|test_comparison|runtime|timeout",
    "severity": "critical|high|medium|low|info",
    "category": "syntax|type_mismatch|undefined_symbol|linker_error|numerical|...",
    "message": "Primary error message",
    "details": ["Additional error details"],
    "location": {
        "file": "src/file.c",
        "line": 123,
        "module": "mcscf"
    },
    "context": {
        "command": ["make", "-j8"],
        "compiler": "gnu",
        "test_name": "test015"
    },
    "failed_modules": ["mcscf", "scf"],
    "suggestions": ["Fix suggestion 1", "Fix suggestion 2"]
}
```

## Configuration

Enable structured error event output in `config.yaml`:

```yaml
reporting:
  structured_events_dir: "./reports/error_events"
  save_error_events: true
```

## Output Structure

Error events are saved to the configured directory:

```
reports/error_events/
├── error_event_evt_abc123.json
├── error_event_evt_def456.json
└── events_summary.json
```

Each event file contains a complete `ErrorEvent` JSON object. The `events_summary.json` contains all events from a single run.

## Using Error Events with AI Agent

### 1. Load Error Events

```python
import json
from pathlib import Path
from src.error_event_schema import ErrorEvent

def load_error_events(events_dir: Path) -> List[ErrorEvent]:
    events = []
    for json_file in events_dir.glob("error_event_*.json"):
        with open(json_file) as f:
            data = json.load(f)
            events.append(ErrorEvent.from_dict(data))
    return events
```

### 2. Generate Prompts

```python
from src.prompt_templates import PromptTemplates

for event in error_events:
    prompt = PromptTemplates.get_prompt(event, include_examples=True)
    # Send prompt to LLM
    response = llm_client.complete(prompt)
```

### 3. Few-Shot Learning

The prompt templates include few-shot examples for each error type:
- Compilation errors (syntax, undefined symbols)
- Linker errors (missing libraries, symbol conflicts)
- Test comparison errors (numerical precision, significant differences)
- Runtime errors (segfaults, module failures)
- Test execution errors (timeouts, exit codes)

### 4. Validation

Use the validation framework to test with real failure samples:

```python
from src.error_event_validator import ErrorEventValidator

validator = ErrorEventValidator(output_dir=Path("./validation"))
summary = validator.run_validation_suite(error_events)
```

## Error Event Parser

The `ErrorEventParser` class abstracts log parsing:

```python
from src.error_event_parser import ErrorEventParser
from src.models import BuildResult, TestResult

parser = ErrorEventParser()

# Parse build failure
build_event = parser.parse_build_result(build_result, config)

# Parse test failure (may return multiple events)
test_events = parser.parse_test_result(test_result, config)
```

## Integration Points

### With BDFDev AI Agent

1. **Error Detection**: BDF Auto Test automatically detects and structures errors
2. **Event Storage**: Events saved to JSON for agent consumption
3. **Prompt Generation**: Use `PromptTemplates` to generate LLM prompts
4. **Analysis**: Agent can analyze events and suggest fixes
5. **Learning**: Few-shot examples help agent understand BDF-specific issues

### Workflow

```
BDF Auto Test Run
    ↓
Error Detection (build/test failures)
    ↓
Error Event Parsing (structured JSON)
    ↓
Event Storage (./reports/error_events/)
    ↓
AI Agent Integration
    ├─ Load events
    ├─ Generate prompts
    ├─ LLM analysis
    └─ Suggested fixes
```

## Example: Processing Error Events

```python
import json
from pathlib import Path
from src.error_event_schema import ErrorEvent
from src.prompt_templates import PromptTemplates

# Load events
events_dir = Path("./reports/error_events")
events = []
for json_file in events_dir.glob("error_event_*.json"):
    with open(json_file) as f:
        events.append(ErrorEvent.from_dict(json.load(f)))

# Process each event
for event in events:
    # Generate prompt
    prompt = PromptTemplates.get_prompt(event, include_examples=True)
    
    # Get LLM analysis
    analysis = your_llm_client.analyze(prompt)
    
    # Store analysis back in event
    event.llm_analysis = analysis
    event.suggestions = extract_suggestions(analysis)
    
    # Save updated event
    with open(f"analyzed_{event.event_id}.json", 'w') as f:
        json.dump(event.to_dict(), f, indent=2)
```

## Validation

Run validation on error events:

```python
from src.error_event_validator import ErrorEventValidator

validator = ErrorEventValidator(output_dir=Path("./validation"))
summary = validator.run_validation_suite(events)

print(f"Valid events: {summary['parsing']['valid']}/{summary['parsing']['total']}")
print(f"Valid prompts: {summary['prompts']['valid']}/{summary['prompts']['total']}")
```

## Error Types and Categories

### Error Types
- `build_setup`: Setup/configure phase failure
- `compilation`: Compilation error
- `linker`: Linker error
- `test_execution`: Test execution failure
- `test_comparison`: Test output mismatch
- `runtime`: Runtime error (segfault, abort)
- `timeout`: Process timeout

### Error Categories
- `syntax`: Syntax errors
- `type_mismatch`: Type errors
- `undefined_symbol`: Missing symbols
- `linker_error`: Linker issues
- `numerical`: Numerical precision issues
- `convergence`: Convergence failures
- `memory`: Memory issues
- `module_failure`: BDF module-specific failure
- `configuration`: Configuration errors
- `environment`: Environment setup issues

## Next Steps

1. **Collect Real Failures**: Run tests to collect real error events
2. **Validate Parsing**: Use validator to ensure events are correctly parsed
3. **Test Prompts**: Verify prompt quality with LLM
4. **Refine Examples**: Add more few-shot examples based on real failures
5. **Integrate Agent**: Connect error events to BDFDev AI Agent

## Files

- `src/error_event_schema.py`: Unified JSON schema
- `src/error_event_parser.py`: Log parsing abstraction
- `src/prompt_templates.py`: Prompt templates with few-shot examples
- `src/error_event_validator.py`: Validation framework

