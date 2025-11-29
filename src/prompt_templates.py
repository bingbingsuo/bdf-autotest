"""
Prompt templates for BDFDev AI Agent integration.

Provides structured prompts with few-shot learning examples for different
error types, enabling the AI agent to better understand and fix BDF issues.
"""

from typing import Dict, Any, List
from .error_event_schema import ErrorEvent, ErrorType, ErrorCategory


class PromptTemplates:
    """Collection of prompt templates with few-shot examples"""
    
    # Few-shot examples for different error types
    FEW_SHOT_EXAMPLES = {
        ErrorType.COMPILATION: """
Example 1: Undefined Symbol Error
Error: undefined reference to `bdf_module_function'
Location: src/module.c:45
Context: Compiling with gcc -O2
Analysis: Missing library link or function declaration. Check if the function is declared in header files and if the corresponding library is linked.
Fix: Add -lmodule flag to linker or include proper header file.

Example 2: Syntax Error
Error: expected ';' before '}' token
Location: src/file.f90:123
Context: Fortran compilation
Analysis: Missing semicolon or syntax error in Fortran code. Check the line before the error.
Fix: Add missing semicolon or correct the syntax at line 123.
""",
        
        ErrorType.LINKER: """
Example 1: Missing Library
Error: undefined reference to `lapack_dgesv'
Context: Linking BDF with custom math library
Analysis: LAPACK library not properly linked. The function exists but linker can't find it.
Fix: Add -llapack to linker flags or check LAPACK installation path.

Example 2: Symbol Conflict
Error: multiple definition of `global_variable'
Location: src/file1.c and src/file2.c
Analysis: Same symbol defined in multiple source files.
Fix: Make the variable static or use extern declaration properly.
""",
        
        ErrorType.TEST_COMPARISON: """
Example 1: Numerical Precision Issue
Error: CHECKDATA mismatch in SCF energy
Reference: -76.123456789
Actual:    -76.123456791
Difference: 2e-9
Analysis: Very small numerical difference, likely due to floating-point precision or compiler optimizations.
Fix: Check if tolerance is appropriate. May need to adjust numerical convergence criteria.

Example 2: Significant Numerical Error
Error: CHECKDATA mismatch in MP2 correlation energy
Reference: -0.123456
Actual:    -0.125000
Difference: 0.001544
Analysis: Significant difference suggests algorithm change or bug in MP2 implementation.
Fix: Review MP2 code changes, check integral evaluation, verify basis set handling.
""",
        
        ErrorType.RUNTIME: """
Example 1: Segmentation Fault
Error: Segmentation fault (core dumped)
Location: During MCSCF calculation
Analysis: Memory access violation, likely array bounds issue or null pointer.
Fix: Check array allocations, verify pointer initialization, use debugger (gdb) to find exact location.

Example 2: Module Failure
Error: Module 'mcscf' failed to converge
Context: CASSCF calculation with active space (6,6)
Analysis: SCF convergence failure in MCSCF module. Could be due to active space definition or initial guess.
Fix: Check active space orbitals, try different initial guess, verify symmetry settings.
""",
        
        ErrorType.TEST_EXECUTION: """
Example 1: Timeout
Error: Test timed out after 3600 seconds
Test: test015 (large system calculation)
Analysis: Calculation taking too long, possibly infinite loop or convergence issue.
Fix: Check for convergence problems, increase timeout if calculation is legitimately slow, or optimize algorithm.

Example 2: Exit Code Error
Error: Process exited with code 1
Test: test042
Analysis: Non-zero exit code indicates failure. Check log file for specific error message.
Fix: Review test log file, identify failing module, check input parameters.
""",
    }
    
    @staticmethod
    def build_error_prompt(event: ErrorEvent, include_examples: bool = True) -> str:
        """Generate prompt for build/compilation errors"""
        prompt_parts = [
            "You are an expert build engineer specializing in scientific computing software, particularly the BDF quantum chemistry package.",
            "",
            "Analyze the following build error and provide:",
            "1. Root cause analysis (specific technical reason)",
            "2. Suggested fixes (concrete steps with commands if applicable)",
            "3. Likely file/location of issue",
            "4. Prevention strategies (how to avoid this in future)",
            "",
        ]
        
        if include_examples and event.error_type in PromptTemplates.FEW_SHOT_EXAMPLES:
            prompt_parts.extend([
                "Few-shot examples:",
                PromptTemplates.FEW_SHOT_EXAMPLES[event.error_type],
                "",
            ])
        
        prompt_parts.extend([
            "Current Error:",
            f"Type: {event.error_type.value}",
            f"Category: {event.category.value}",
            f"Severity: {event.severity.value}",
            f"Message: {event.message}",
            "",
        ])
        
        if event.location:
            loc = event.location
            if loc.file:
                prompt_parts.append(f"Location: {loc.file}")
                if loc.line:
                    prompt_parts.append(f"Line: {loc.line}")
                if loc.module:
                    prompt_parts.append(f"Module: {loc.module}")
                prompt_parts.append("")
        
        if event.details:
            prompt_parts.extend([
                "Error Details:",
                "\n".join(event.details[:10]),  # Limit to first 10 details
                "",
            ])
        
        if event.context.command:
            prompt_parts.extend([
                "Build Context:",
                f"Command: {' '.join(event.context.command)}",
                f"Compiler: {event.context.compiler or 'unknown'}",
                "",
            ])
        
        prompt_parts.append("Please provide a structured analysis following the format above.")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def test_error_prompt(event: ErrorEvent, include_examples: bool = True) -> str:
        """Generate prompt for test execution/comparison errors"""
        prompt_parts = [
            "You are an expert in quantum chemistry program debugging, especially for the BDF package.",
            "",
            "A regression test failed. Analyze and provide:",
            "1. Short TL;DR summary",
            "2. Likely root causes (with specific BDF modules/stages)",
            "3. Concrete debugging steps (commands, input edits, code areas to inspect)",
            "4. Notes about numerical tolerances vs real bugs",
            "",
        ]
        
        if include_examples and event.error_type in PromptTemplates.FEW_SHOT_EXAMPLES:
            prompt_parts.extend([
                "Few-shot examples:",
                PromptTemplates.FEW_SHOT_EXAMPLES[event.error_type],
                "",
            ])
        
        prompt_parts.extend([
            "Test Failure Information:",
            f"Test: {event.context.test_name or 'unknown'}",
            f"Error Type: {event.error_type.value}",
            f"Category: {event.category.value}",
            f"Message: {event.message}",
            "",
        ])
        
        if event.failed_modules:
            prompt_parts.extend([
                "Failed Module(s):",
                ", ".join(event.failed_modules),
                "",
            ])
        
        if event.details:
            prompt_parts.extend([
                "Error Details:",
                "\n".join(event.details[:15]),  # More details for test errors
                "",
            ])
        
        if event.error_type == ErrorType.TEST_COMPARISON and event.metadata.get('differences_count'):
            prompt_parts.extend([
                f"Output Differences: {event.metadata['differences_count']} differences found",
                "First few differences:",
                "\n".join(event.details[:10]),
                "",
            ])
        
        prompt_parts.append("Please provide a structured analysis following the format above.")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def get_prompt(event: ErrorEvent, include_examples: bool = True) -> str:
        """Get appropriate prompt template based on error type"""
        if event.error_type in [ErrorType.BUILD_SETUP, ErrorType.COMPILATION, ErrorType.LINKER]:
            return PromptTemplates.build_error_prompt(event, include_examples)
        elif event.error_type in [ErrorType.TEST_EXECUTION, ErrorType.TEST_COMPARISON, ErrorType.RUNTIME, ErrorType.TIMEOUT]:
            return PromptTemplates.test_error_prompt(event, include_examples)
        else:
            # Generic prompt
            return f"""
You are an expert in debugging scientific computing software.

Analyze the following error:
Type: {event.error_type.value}
Category: {event.category.value}
Message: {event.message}

Error Details:
{chr(10).join(event.details[:10])}

Please provide:
1. Root cause analysis
2. Suggested fixes
3. Prevention strategies
"""


def format_event_for_llm(event: ErrorEvent, include_examples: bool = True) -> str:
    """Format error event as LLM prompt"""
    return PromptTemplates.get_prompt(event, include_examples)

