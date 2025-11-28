# Configuration Customization Guide

This guide will help you customize the configuration file for your specific package.

## Configuration Sections Overview

### 1. Git Configuration
**Purpose**: Define where to pull your package source code from

**Required Information**:
- Remote repository URL (HTTPS or SSH)
- Branch name to pull from
- Local directory path where code will be cloned/pulled

**Example**:
```yaml
git:
  remote_url: "https://github.com/username/package.git"  # or "git@github.com:username/package.git"
  branch: "main"  # or "master", "develop", etc.
  local_path: "./package_source"
```

### 2. Build Configuration
**Purpose**: Define how to compile your package

**Required Information**:
- Source directory location
- Build directory location
- Compiler commands (Fortran, C, C++)
- Compiler flags
- Build command (make, cmake, configure, etc.)

**Common Build Systems**:
- **Make**: `build_command: "make"`, `build_args: []`
- **CMake**: `build_command: "cmake"`, `build_args: ["..", "-DCMAKE_BUILD_TYPE=Release"]`
- **Autotools**: `build_command: "./configure && make"`, `build_args: []`
- **Custom script**: `build_command: "./build.sh"`, `build_args: []`

**Compiler Examples**:
```yaml
# GNU Compilers
fortran: { command: "gfortran", flags: ["-O2", "-Wall"] }
c: { command: "gcc", flags: ["-O2", "-Wall", "-std=c11"] }
cpp: { command: "g++", flags: ["-O2", "-Wall", "-std=c++17"] }

# Intel Compilers
fortran: { command: "ifort", flags: ["-O2", "-warn"] }
c: { command: "icc", flags: ["-O2", "-Wall"] }
cpp: { command: "icpc", flags: ["-O2", "-Wall"] }

# Clang
c: { command: "clang", flags: ["-O2", "-Wall"] }
cpp: { command: "clang++", flags: ["-O2", "-Wall", "-std=c++17"] }
```

### 3. LLM Configuration
**Purpose**: Configure AI-powered error analysis

**Providers**:
- **OpenAI**: Requires `OPENAI_API_KEY` environment variable
- **Anthropic**: Requires `ANTHROPIC_API_KEY` environment variable
- **Local**: For offline use (requires local LLM setup)

**Model Recommendations**:
- OpenAI: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo` (cheaper)
- Anthropic: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku` (cheaper)

**Settings**:
- `temperature: 0.3` - Lower = more deterministic, good for error analysis
- `max_tokens: 2000` - Adjust based on expected error message length

### 4. Test Configuration
**Purpose**: Define which tests to run and how to compare results

**Key Settings**:
- `test_dir`: Directory containing input files (e.g. `tests/input`)
- `reference_dir`: Directory containing reference `*.check` files (e.g. `tests/check`)
- `input_pattern`: Glob pattern for input files (e.g. `test*.inp`)
- `reference_pattern`: Glob pattern for reference files (e.g. `test*.check`)
- `check_pattern`: Pattern for extracted check data (usually `test*.check`)
- `test_command`: Executable to run tests (e.g. `{BDFHOME}/sbin/bdfdrv.py`)
- `test_args_template`: Command-line arguments template (e.g. `-r {input_file}`)
- `tolerance`: Base numerical tolerance (used by comparison rules)
- `tolerance_mode`: `"strict"` or `"loose"` profile for CHECKDATA tolerances
- `tolerance_scale`: Scale factors for strict/loose modes
- `timeout`: Maximum runtime per test (seconds)
- `enabled_range`: Numeric ID range (e.g. `test001`–`test020`)
- `profiles` / `profile`: Named test profiles (e.g. `smoke`, `core`, `full`)
- `max_parallel`: Maximum number of tests to run in parallel

**Example Test Configuration**:
```yaml
tests:
  test_dir: "tests/input"
  reference_dir: "tests/check"

  # Discover input and reference files
  input_pattern: "test*.inp"
  reference_pattern: "test*.check"
  check_pattern: "test*.check"

  # How to run each test
  test_command: "{BDFHOME}/sbin/bdfdrv.py"
  test_args_template: "-r {input_file}"

  # Numerical comparison
  tolerance: 1e-6
  timeout: 3600
  tolerance_mode: "strict"   # or "loose"
  tolerance_scale:
    strict: 1.0
    loose: 5.0

  # Default enabled range (applied when no profile is set)
  enabled_range:
    min: 1
    max: 200

  # Optional named profiles for convenience
  profiles:
    smoke:
      min: 1
      max: 5
    core:
      min: 1
      max: 20
    full:
      min: 1
      max: 200

  # Select profile (overrides enabled_range)
  profile: "core"   # or "smoke", "full"

  # Parallel execution
  max_parallel: 2   # 1 = sequential, >1 = run tests in parallel
```

### 5. Reporting Configuration
**Purpose**: Control report generation

**Options**:
- `format`: Choose `["html"]`, `["json"]`, or both
- `include_llm_analysis`: Include AI analysis in reports (true/false)
- `timestamp_format`: How to name report files

### 6. Logging Configuration
**Purpose**: Control logging behavior

**Log Levels**:
- `DEBUG`: Very verbose, includes all details
- `INFO`: Normal operation messages
- `WARNING`: Warnings only
- `ERROR`: Errors only

## Quick Start Questions

To customize your config, answer these questions:

1. **Git Repository**:
   - What's your repository URL?
   - Which branch should we pull from?

2. **Build System**:
   - What build system do you use? (make, cmake, autotools, custom)
   - What compilers do you use? (gcc/gfortran, intel, clang, etc.)
   - What compiler flags are important?

3. **LLM Provider**:
   - Which provider do you prefer? (OpenAI, Anthropic, or local)
   - Do you have an API key set up?

4. **Tests**:
   - How many tests do you have?
   - What format are your test outputs? (text, binary, structured)
   - Where are your reference files located?

## Next Steps

1. Answer the questions above
2. We'll create a customized `config.yaml` file
3. Test the configuration loading
4. Adjust as needed

