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
git:
  # Root of the BDF source tree (where git clones into)
  remote_url: "ssh://user@host:port/path/to/bdf-pkg"
  branch: "master"
  local_path: "./package_source"

build:
  # Only two path-related options are needed:
  # - git.local_path : root directory where git pulls the code
  # - build_dir      : build directory inside that source_dir (relative path)
  build_dir: "build"
  build_command: "./setup"  # Run from source_dir

  # Compiler combinations (choose one)
  # Options: "gnu", "intel", "llvm"
  compiler_set: "gnu"
  compilers:
    gnu:
      fortran: "gfortran"
      c: "gcc"
      cpp: "g++"
    intel:
      fortran: "ifx"
      c: "icx"
      cpp: "icpx"
    llvm:
      fortran: "Flang"
      c: "clang"
      cpp: "clang++"

  # Math library configuration
  # Option 1: Use MKL library
  use_mkl: false  # Set to true if you want BDF to link against MKL
  mkl_option: "TBB"  # Value for --mkl option (ignored if use_mkl: false)

  # Option 2: Custom math library (configure below)
  math_library:
    # Example placeholders; replace with your LAPACK/BLAS installation paths
    mathinclude_flags: "-I/path/to/lapack/include -I/path/to/cblas/include"
    mathlib_flags: "-L/path/to/lapack/lib -llapack -lblas -lcblas -llapacke"
    blasdir: "/path/to/blas"
    lapackdir: "/path/to/lapack"

  # Build mode
  # Options: "release", "debug"
  build_mode: "release"

  # Preserve build directory (if true, don't remove existing build dir before setup)
  preserve_build: false

  # Always used options
  always_use:
    - "--int64"
    - "--omp"

  # Additional build arguments (optional)
  additional_args: []

compile:
  # working_dir is derived automatically as: build.source_dir/build.build_dir
  command: "make"
  jobs: "auto"
  target: "install"
  extra_args: []
  log_file: "make.log"

llm:
  # Overall behavior:
  # - local : only use local LLM
  # - remote: only use remote LLM (e.g. OpenAI)
  # - auto  : try local first, fall back to remote if local fails
  mode: "auto"
  analysis_mode: "simple"
  max_tokens: 2000
  temperature: 0.3

  local:
    enabled: true
    endpoint: "http://localhost:11434"
    model: "my-local-llm"
    timeout: 300

  remote:
    enabled: true
    # Supported providers (all use OpenAI‑compatible chat completion APIs):
    # - "openai"     → https://api.openai.com/v1/chat/completions
    # - "openrouter" → https://openrouter.ai/api/v1/chat/completions
    # - "deepseek"   → https://api.deepseek.com/chat/completions
    # - "groq"       → https://api.groq.com/openai/v1/chat/completions
    provider: "openai"
    model: "gpt-4o"
    # Environment variable holding your API key.
    # For OpenAI, a common choice is OPENAI_API_KEY.
    # For OpenRouter, you can set api_key_env: "OPENROUTER_API_KEY".
    api_key_env: "OPENAI_API_KEY"

tests:
  # Test directories are relative to source_dir (inside the repository)
  test_dir: "tests/input"
  reference_dir: "tests/check"
  tolerance: 1e-6
  timeout: 3600
  enabled_range:
    min: 1
    max: 161

reporting:
  output_dir: "./reports"
  format: ["html", "json"]
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

#### Run a Single Regression Test

Sometimes you only want to rerun one test from the regression suite (for example, after editing BDF code affecting a specific module).  
Use the `run-test` subcommand instead of changing `config.yaml` ranges:

```bash
# Run a single test by full name
python3 -m src.orchestrator run-test test149 --config config/config.yaml

# Or by numeric id (auto-normalized to test149)
python3 -m src.orchestrator run-test 149 --config config/config.yaml
```

**Behavior:**
- Uses the existing configuration from `config/config.yaml` (no need to edit `tests.enabled_range`).
- Discovers all tests, then executes **only** the requested one.
- Reuses the same environment and comparison logic as the full regression run.
- Prints a concise pass/fail summary and, on failure, the detailed CHECKDATA differences.

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

