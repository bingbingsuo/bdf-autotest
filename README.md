# BDF Auto Test Framework

Automated testing framework for continuous integration and validation of the BDF package.

## Project Overview

This framework automates the complete testing workflow:
1. **Git Integration**: Pulls latest code from remote repository
2. **Build System**: Configures and compiles package with configurable compiler settings
3. **LLM-Powered Analysis**: Analyzes compilation and test failures using AI (local or remote LLM)
4. **Test Execution**: Runs predefined tests and compares with reference data
5. **Report Generation**: Produces comprehensive HTML and JSON test reports

## Project Structure

```
BDFAutoTest/
├── README.md                 # This file
├── TROUBLESHOOTING.md        # Common issues and fixes
├── requirements.txt          # Python dependencies
├── config/
│   ├── config.yaml          # Main configuration file
│   └── config.yaml.example   # Example configuration template
├── src/
│   ├── __init__.py
│   ├── config_loader.py      # YAML configuration loader
│   ├── logger.py            # Logging setup
│   ├── models.py            # Data models
│   ├── git_manager.py       # Git pull operations
│   ├── build_manager.py     # Setup/configuration management
│   ├── compile_manager.py   # Compilation (make) management
│   ├── compilation_analyzer.py  # Build error analysis
│   ├── llm_analyzer.py       # LLM integration (local/remote)
│   ├── test_runner.py       # Test execution
│   ├── result_comparator.py # Compare test outputs with reference
│   ├── report_generator.py  # Generate HTML/JSON reports
│   ├── orchestrator.py      # Main workflow coordinator
│   └── utils.py             # Utility functions
├── package_source/           # Cloned package repository
├── reports/                  # Generated test reports (HTML/JSON)
└── logs/                     # Execution logs
```

## Technology Suggestions

### Language
- **Python 3.8+**: Recommended for rapid development, rich ecosystem, and LLM API integration

### Key Libraries
- `pyyaml` or `toml`: Configuration management
- `gitpython`: Git operations
- `openai` or `anthropic`: LLM API clients
- `pytest` or `unittest`: Test framework (optional, for testing this framework itself)
- `jinja2`: Report template rendering
- `click` or `argparse`: CLI interface

### LLM Provider Options
- **OpenAI GPT-4**: Strong code analysis capabilities
- **Anthropic Claude**: Excellent for technical analysis
- **Local LLM** (via Ollama/LlamaCpp): For privacy/offline use

## Configuration Design

### Compiler Configuration Example
```yaml
build:
  source_dir: "./package_source"
  build_dir: "./build"
  compilers:
    fortran:
      command: "gfortran"
      flags: ["-O2", "-Wall", "-fPIC"]
    c:
      command: "gcc"
      flags: ["-O2", "-Wall", "-std=c11"]
    cpp:
      command: "g++"
      flags: ["-O2", "-Wall", "-std=c++17"]
  build_command: "make"  # or "cmake", "configure && make", etc.
  build_args: []

git:
  remote_url: "https://github.com/user/repo.git"
  branch: "main"
  local_path: "./package_source"

llm:
  provider: "openai"  # or "anthropic", "local"
  model: "gpt-4"
  api_key_env: "OPENAI_API_KEY"
  max_tokens: 2000

tests:
  test_dir: "./tests"
  reference_dir: "./reference_data"
  tolerance: 1e-6  # Numerical comparison tolerance
  timeout: 3600    # Test timeout in seconds

reporting:
  output_dir: "./reports"
  format: ["html", "json"]  # Report formats
```

## Workflow Design

```
┌─────────────┐
│   Start     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Git Pull       │
│  (Update Code)  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Compile        │
│  Package        │
└──────┬──────────┘
       │
       ├─── Success ──► ┌──────────────┐
       │                │ Run Tests    │
       │                └──────┬───────┘
       │                       │
       │                       ▼
       │                ┌──────────────┐
       │                │ Compare with │
       │                │ Reference    │
       │                └──────┬───────┘
       │                       │
       │                       ▼
       │                ┌──────────────┐
       │                │ Generate     │
       │                │ Report       │
       │                └──────┬───────┘
       │                       │
       └─── Failure ──► ┌──────────────┐
                        │ LLM Analyze  │
                        │ Errors       │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Generate     │
                        │ Report       │
                        └──────┬───────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   End        │
                        └──────────────┘
```

## Implementation Phases

### Phase 1: Foundation (Tasks 1-2, 12)
- Set up project structure
- Create configuration system
- Document dependencies

### Phase 2: Core Operations (Tasks 3-4, 11)
- Git integration
- Build system
- Logging infrastructure

### Phase 3: Intelligence (Tasks 5-6)
- LLM integration
- Compilation error analysis

### Phase 4: Testing (Tasks 7-8)
- Test execution
- Result comparison

### Phase 5: Reporting & Integration (Tasks 9-10, 13)
- Report generation
- Main orchestrator
- Documentation

## Next Steps

1. Review and customize the configuration structure
2. Choose your LLM provider
3. Start with Phase 1 tasks
4. Iterate and test each component

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip3 install --user -r requirements.txt
```

### 2. Configuration

Copy and customize the configuration file:

```bash
cp config/config.yaml.example config/config.yaml
# Edit config/config.yaml with your settings
```

Or use the interactive configuration script:

```bash
python3 customize_config.py
```

Key configuration sections:
- **Git**: Repository URL, branch, local path
- **Build**: Compiler sets (GNU/Intel/LLVM), math library (MKL/custom), build mode
- **LLM**: Local and/or remote LLM settings for failure analysis
- **Tests**: Test directory, reference data, tolerance settings
- **Reporting**: Output directory and formats

### 3. Usage

```bash
# Run full workflow: git pull → setup → compile → test → report
python3 -m src.orchestrator --config config/config.yaml

# Skip git pull (use existing code)
python3 -m src.orchestrator --config config/config.yaml --skip-git

# Skip build steps (assume already compiled)
python3 -m src.orchestrator --config config/config.yaml --skip-git --skip-build

# Skip tests (only build)
python3 -m src.orchestrator --config config/config.yaml --skip-tests

# Compare test reports
python3 -m src.orchestrator compare -n 2  # Compare latest 2 reports
python3 -m src.orchestrator compare --before report1.json --after report2.json
```

### 4. View Results

Reports are generated in the `reports/` directory:
- **HTML reports**: Open `reports/report_YYYY-MM-DD_HH-MM-SS.html` in a browser
- **JSON reports**: Machine-readable format in `reports/report_YYYY-MM-DD_HH-MM-SS.json`

Logs are stored in `logs/autotest_YYYY-MM-DD_HH-MM-SS.log`

### 5. Compare Reports

Compare test results across different runs to track trends:

```bash
# Compare the latest 2 reports
python3 -m src.orchestrator compare -n 2

# Compare specific reports
python3 -m src.orchestrator compare --before report1.json --after report2.json

# Compare with custom reports directory
python3 -m src.orchestrator compare --reports-dir ./reports -n 3
```

Comparison reports show:
- **New Failures**: Tests that passed before but failed now (regressions)
- **Fixed Tests**: Tests that failed before but pass now
- **Still Failing**: Tests that failed in both runs
- **Still Passing**: Tests that passed in both runs
- **New Tests**: Tests only in the new report
- **Removed Tests**: Tests only in the old report

### 6. CI Integration (GitHub Actions)

An example GitHub Actions workflow is provided in `.github/workflows/ci.yml`.
It will:
- Check out the repository
- Set up Python and system dependencies
- Install Python dependencies from `requirements.txt`
- Run the orchestrator (by default with `--skip-git --skip-build`)
- Optionally compare the latest two reports
- Upload reports and logs as build artifacts

Basic usage:

1. Ensure your repository is pushed to GitHub.
2. If you want to use a remote LLM in CI, add `OPENAI_API_KEY` as a GitHub secret.
3. Adjust `config/config.yaml` for the CI environment (e.g., math libraries, test range).
4. Push changes; the workflow will run automatically on `push`/`pull_request` to `master`/`main`.

## Troubleshooting

If you run into problems (git/SSH issues, setup or build failures, LLM connectivity, test failures, etc.), see:

- `TROUBLESHOOTING.md` – detailed guide with common symptoms, causes, and fixes.

## Features

### Build System
- Supports multiple compiler sets (GNU, Intel, LLVM)
- Configurable math libraries (MKL or custom BLAS/LAPACK)
- Release and debug build modes
- Automatic clean build (removes old build directory)

### LLM Integration
- **Local LLM**: Supports Ollama and compatible endpoints
- **Remote LLM**: OpenAI API integration
- **Auto mode**: Tries local first, falls back to remote
- Configurable timeout for local LLM requests
- Detailed failure analysis for build and test failures

### Test Execution
- Pattern-based test discovery (`test*.inp`)
- Automatic CHECKDATA extraction from logs
- Numerical tolerance comparison with per-key tolerances
- Environment variable management (BDFHOME, BDF_TMPDIR, OMP settings)
- Test range filtering (run specific test subsets)
- Named test profiles (e.g. smoke/core/full) via `tests.profiles` and `tests.profile`
- Optional parallel execution via `tests.max_parallel`

### Result Comparison
- Whitespace-ignoring comparison
- Per-key absolute tolerances for different CHECKDATA types
- Relative tolerance for ELECOUP data
- Strict/loose tolerance modes
- Detailed difference reporting

### Reporting
- HTML reports with styling
- JSON reports for programmatic access
- Includes Git information, build configuration, version info
- LLM analysis for failures
- Summary statistics and detailed failure information
- **Report Comparison**: Track trends across runs, identify regressions and improvements

