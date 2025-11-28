#!/usr/bin/env python3
"""
Interactive configuration customization script
Helps create a customized config.yaml file for your package
"""

import yaml
import os
from pathlib import Path


def ask_question(prompt, default=None, required=True):
    """Ask a question and return the answer"""
    if default:
        full_prompt = f"{prompt} [default: {default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    while True:
        answer = input(full_prompt).strip()
        if answer:
            return answer
        elif default:
            return default
        elif not required:
            return None
        else:
            print("This field is required. Please provide a value.")


def ask_yes_no(prompt, default=True):
    """Ask a yes/no question"""
    default_str = "Y/n" if default else "y/N"
    answer = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not answer:
        return default
    return answer in ['y', 'yes']


def ask_list(prompt, item_name="item"):
    """Ask for a list of items"""
    items = []
    print(f"{prompt} (press Enter with empty value to finish):")
    while True:
        item = input(f"  {item_name}: ").strip()
        if not item:
            break
        items.append(item)
    return items


def main():
    print("=" * 60)
    print("BDF Auto Test Framework - Configuration Customization")
    print("=" * 60)
    print()
    
    config = {}
    
    # Git Configuration
    print("\n[1/6] Git Configuration")
    print("-" * 60)
    config['git'] = {
        'remote_url': ask_question("Git repository URL (HTTPS or SSH)"),
        'branch': ask_question("Branch name", "main"),
        'local_path': ask_question("Local directory path", "./package_source")
    }
    
    # Build Configuration
    print("\n[2/6] Build Configuration")
    print("-" * 60)
    config['build'] = {
        'source_dir': ask_question("Source directory", "./package_source"),
        'build_dir': ask_question("Build directory", "./build"),
        'compilers': {}
    }
    
    # Compilers
    print("\nCompiler Configuration:")
    use_fortran = ask_yes_no("Do you use Fortran?", True)
    if use_fortran:
        config['build']['compilers']['fortran'] = {
            'command': ask_question("Fortran compiler command", "gfortran"),
            'flags': ask_list("Fortran compiler flags", "flag")
        }
        if not config['build']['compilers']['fortran']['flags']:
            config['build']['compilers']['fortran']['flags'] = ["-O2", "-Wall"]
    
    use_c = ask_yes_no("Do you use C?", True)
    if use_c:
        config['build']['compilers']['c'] = {
            'command': ask_question("C compiler command", "gcc"),
            'flags': ask_list("C compiler flags", "flag")
        }
        if not config['build']['compilers']['c']['flags']:
            config['build']['compilers']['c']['flags'] = ["-O2", "-Wall", "-std=c11"]
    
    use_cpp = ask_yes_no("Do you use C++?", False)
    if use_cpp:
        config['build']['compilers']['cpp'] = {
            'command': ask_question("C++ compiler command", "g++"),
            'flags': ask_list("C++ compiler flags", "flag")
        }
        if not config['build']['compilers']['cpp']['flags']:
            config['build']['compilers']['cpp']['flags'] = ["-O2", "-Wall", "-std=c++17"]
    
    # Build command
    print("\nBuild System:")
    build_system = ask_question("Build system (make/cmake/configure/custom)", "make")
    config['build']['build_command'] = build_system
    
    if build_system == "cmake":
        config['build']['build_args'] = ask_list("CMake arguments", "arg")
        if not config['build']['build_args']:
            config['build']['build_args'] = ["..", "-DCMAKE_BUILD_TYPE=Release"]
    elif build_system == "configure":
        config['build']['build_command'] = "./configure && make"
        config['build']['build_args'] = []
    else:
        config['build']['build_args'] = ask_list("Build command arguments", "arg")
    
    # LLM Configuration
    print("\n[3/6] LLM Configuration")
    print("-" * 60)
    provider = ask_question("LLM Provider (openai/anthropic/local)", "openai")
    config['llm'] = {
        'provider': provider,
        'model': ask_question("Model name", "gpt-4" if provider == "openai" else "claude-3-sonnet"),
        'api_key_env': ask_question("API key environment variable name", 
                                   "OPENAI_API_KEY" if provider == "openai" else "ANTHROPIC_API_KEY"),
        'max_tokens': int(ask_question("Max tokens for analysis", "2000")),
        'temperature': float(ask_question("Temperature (0.0-1.0)", "0.3"))
    }
    
    # Test Configuration
    print("\n[4/6] Test Configuration")
    print("-" * 60)
    config['tests'] = {
        'test_dir': ask_question("Test directory", "./tests"),
        'reference_dir': ask_question("Reference data directory", "./reference_data"),
        'tolerance': float(ask_question("Numerical comparison tolerance", "1e-6")),
        'timeout': int(ask_question("Test timeout (seconds)", "3600")),
        'test_configs': []
    }
    
    print("\nTest Definitions:")
    add_tests = ask_yes_no("Do you want to add test configurations now?", True)
    if add_tests:
        test_num = 1
        while True:
            print(f"\nTest #{test_num}:")
            test_name = ask_question("Test name", required=False)
            if not test_name:
                break
            
            test_config = {
                'name': test_name,
                'command': ask_question("Test command/executable"),
                'args': ask_list("Test arguments", "arg"),
                'reference_file': ask_question("Reference output file path")
            }
            config['tests']['test_configs'].append(test_config)
            test_num += 1
            
            if not ask_yes_no("Add another test?", False):
                break
    
    # Reporting Configuration
    print("\n[5/6] Reporting Configuration")
    print("-" * 60)
    formats = []
    if ask_yes_no("Generate HTML reports?", True):
        formats.append("html")
    if ask_yes_no("Generate JSON reports?", True):
        formats.append("json")
    
    config['reporting'] = {
        'output_dir': ask_question("Report output directory", "./reports"),
        'format': formats if formats else ["html"],
        'include_llm_analysis': ask_yes_no("Include LLM analysis in reports?", True),
        'timestamp_format': ask_question("Timestamp format", "%Y-%m-%d_%H-%M-%S")
    }
    
    # Logging Configuration
    print("\n[6/6] Logging Configuration")
    print("-" * 60)
    config['logging'] = {
        'level': ask_question("Log level (DEBUG/INFO/WARNING/ERROR)", "INFO"),
        'log_dir': ask_question("Log directory", "./logs"),
        'log_file': ask_question("Log file pattern", "autotest_{timestamp}.log")
    }
    
    # Save configuration
    print("\n" + "=" * 60)
    config_path = Path("config/config.yaml")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"✓ Configuration saved to: {config_path}")
    print("\nNext steps:")
    print("1. Review the configuration file: config/config.yaml")
    print("2. Set your API key: export OPENAI_API_KEY='your-key' (or ANTHROPIC_API_KEY)")
    print("3. Test the configuration loading")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nConfiguration customization cancelled.")
    except Exception as e:
        print(f"\nError: {e}")

