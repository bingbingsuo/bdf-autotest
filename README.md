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

#### Full Workflow
```bash
# Run full workflow: git pull → setup → compile → test → report
python3 -m src.orchestrator --config config/config.yaml

# Skip git pull (use existing code)
python3 -m src.orchestrator --config config/config.yaml --skip-git

# Skip build steps (assume already compiled)
python3 -m src.orchestrator --config config/config.yaml --skip-git --skip-build

# Skip tests (only build)
python3 -m src.orchestrator --config config/config.yaml --skip-tests

# Use a specific test profile
python3 -m src.orchestrator --config config/config.yaml --profile smoke
```

#### Run User Input File
```bash
# Run a user-specified input file (must have .inp extension)
python3 -m src.orchestrator run-input /path/to/test.inp --config config/config.yaml

# Example
python3 -m src.orchestrator run-input /Users/bsuo/check/bdf/h2o.inp --config config/config.yaml
```

**Features:**
- Input file must have `.inp` extension (enforced)
- Standard output saved to `{filename}.log`
- Standard error saved to `{filename}.err`
- Automatically detects BDFOPT detailed output (`{filename}.out.tmp`)
- Uses input file's directory as working directory
- Configurable `BDF_WORKDIR` and `BDF_TMPDIR` in config

#### Compare Test Reports
```bash
# Compare latest 2 reports
python3 -m src.orchestrator compare -n 2

# Compare specific reports
python3 -m src.orchestrator compare --before report1.json --after report2.json

# Compare with custom reports directory
python3 -m src.orchestrator compare --reports-dir ./reports -n 3
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

### 1. Complete Workflow Automation
- **Git Integration**: Automatic repository synchronization (`git pull`)
- **Build System**: Automated setup and compilation
  - Supports multiple compiler sets (GNU, Intel, LLVM)
  - Configurable math libraries (MKL or custom BLAS/LAPACK)
  - Release and debug build modes
  - Automatic clean build (removes old build directory)
- **Test Execution**: Automated test discovery and execution
- **Report Generation**: Comprehensive HTML and JSON reports
- **Flexible Execution**: Skip any step with command-line flags (`--skip-git`, `--skip-build`, `--skip-tests`)

### 2. User Input File Execution (`run-input`)
- **Direct Calculation**: Run BDF calculations with user-specified input files
- **File Format Validation**: Enforces `.inp` extension for input files (required)
- **Output Management**:
  - Standard output redirected to `{filename}.log` (extractor-processed results)
  - Standard error redirected to `{filename}.err`
  - Automatic detection of BDFOPT detailed output (`{filename}.out.tmp`) when BDFOPT module is used
- **Working Directory**: 
  - Default: Uses input file's directory as working directory
  - Configurable: Set `BDF_WORKDIR` in `config.yaml` under `tests.env`
- **Temporary Directory**: 
  - Default: System temporary directory
  - Configurable: Set `BDF_TMPDIR` in `config.yaml` (supports `$RANDOM` placeholder)
- **Error Handling**: 
  - Validates input file existence before execution
  - Provides clear error messages with tried paths if file not found
  - Does not execute calculation if input file is invalid
- **Output Analysis**: Lists all generated files for easy result inspection

### 3. LLM-Powered Error Analysis
- **Local LLM**: Supports Ollama and compatible endpoints
- **Remote LLM**: OpenAI API integration
- **Auto Mode**: Tries local first, falls back to remote
- **Domain Knowledge Integration**: 
  - MCSCF/GRAD module dependencies
  - TDDFT default settings awareness
  - NMR and NRCC module bug awareness
- **Detailed Analysis**: 
  - Build failure analysis with compilation error context
  - Test failure analysis with numerical differences and runtime errors
  - Context-aware suggestions based on module-specific knowledge
- **Configurable Timeout**: For local LLM requests

### 4. Test Execution and Comparison
- **Pattern-Based Discovery**: Automatic test discovery (`test*.inp`)
- **CHECKDATA Extraction**: Automatic extraction of numerical results from logs
- **Numerical Comparison**: 
  - Per-key absolute tolerances for different CHECKDATA types
  - Multi-value comparison for complex data (e.g., GRAD:GS+EX, BDFOPT:OPTGEOM)
  - Relative tolerance for ELECOUP data
  - Strict/loose tolerance modes
- **Environment Management**: 
  - BDFHOME, BDF_TMPDIR, OMP settings
  - Configurable OpenMP thread count and stack size
- **Test Filtering**:
  - Test range filtering (run specific test subsets via `enabled_range`)
  - Named test profiles (e.g. smoke/core/full) via `tests.profiles` and `tests.profile`
- **Parallel Execution**: Optional parallel test execution via `tests.max_parallel`
- **Detailed Reporting**: Whitespace-ignoring comparison with detailed difference reporting

### 5. Report Generation and Comparison
- **HTML Reports**: Styled HTML reports with comprehensive information
- **JSON Reports**: Machine-readable format for programmatic access
- **Report Contents**:
  - Git information (commit hash, branch, remote URL)
  - Build configuration (compiler settings, math library)
  - Version information
  - Test results with pass/fail status
  - LLM analysis for failures
  - Summary statistics
- **Report Comparison**: 
  - Compare latest N reports or specific reports
  - Track trends across runs
  - Identify regressions (new failures)
  - Identify improvements (fixed tests)
  - Show still failing and still passing tests
  - Detect new and removed tests

### 6. Configuration Management
- **YAML Configuration**: Flexible YAML-based configuration system
- **Configuration Validation**: Automatic validation of configuration structure
- **Example Template**: `config.yaml.example` with comprehensive documentation
- **Section Support**:
  - Git settings (remote URL, branch, local path)
  - Build settings (compiler sets, math libraries, build modes)
  - LLM settings (local/remote endpoints, API keys, timeouts)
  - Test settings (test directory, reference data, tolerances, profiles)
  - Reporting settings (output directory, formats, error event saving)
  - Logging settings (log level, log directory)

### 6. User Input File Execution
The `run-input` command allows you to run BDF calculations directly with any input file:

**Key Features:**
- **File Format Validation**: Only accepts `.inp` files (enforced)
- **Output Files**:
  - `{filename}.log`: Standard output (extractor-processed results)
  - `{filename}.err`: Standard error output
  - `{filename}.out.tmp`: BDFOPT detailed output (automatically detected when BDFOPT module is used)
- **Working Directory**: 
  - Default: Input file's directory
  - Configurable: Set `BDF_WORKDIR` in `config.yaml` under `tests.env`
- **Temporary Directory**:
  - Default: System temporary directory
  - Configurable: Set `BDF_TMPDIR` in `config.yaml` (supports `$RANDOM` placeholder)
- **Error Handling**: 
  - Validates file existence before execution
  - Provides clear error messages if file not found
  - Lists all generated output files after execution

**Example Output:**
```
Output files:
  - Stdout: /path/to/test.log
  - Stderr: /path/to/test.err
  - BDFOPT detailed output: /path/to/test.out.tmp
    ⚠️  IMPORTANT: This file contains detailed BDF module outputs
       and is essential for error analysis when calculation fails.
```

### 7. Error Event Tracking
- **Structured Error Events**: JSON-based error event storage
- **Error Parsing**: Automatic parsing of build and test errors
- **Event Storage**: Optional saving of error events for analysis
- **Event Summary**: Summary of all error events in a run

### 8. Logging and Debugging
- **Structured Logging**: Comprehensive logging with configurable levels
- **Log Files**: Timestamped log files in `logs/` directory
- **Console Output**: Real-time console output for immediate feedback
- **Error Details**: Detailed error information in logs and reports

