"""
Analyze compilation results and prepare summaries
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .models import BuildResult

ERROR_PATTERNS = {
    "fortran": re.compile(r"(?i)error.*fortran"),
    "c": re.compile(r"(?i)error.*(gcc|clang|icc)"),
    "linker": re.compile(r"(?i)ld:|linker"),
}


class CompilationAnalyzer:
    """Parse build output and categorize failures"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("bdf_autotest.build_analyzer")

    def analyze(self, result: BuildResult) -> Dict[str, Any]:
        analysis = {
            "success": result.success,
            "exit_code": result.exit_code,
            "error_type": None,
            "error_snippets": [],
        }
        if result.success:
            return analysis

        stderr_lines = result.stderr.splitlines()
        snippets = self._collect_error_snippets(stderr_lines)
        analysis["error_snippets"] = snippets
        analysis["error_type"] = self._classify_error(stderr_lines)

        self.logger.debug("Compilation analysis: %s", analysis)
        return analysis

    def _collect_error_snippets(self, lines: List[str], limit: int = 20) -> List[str]:
        snippets = []
        for line in lines:
            if "error" in line.lower():
                snippets.append(line.strip())
            if len(snippets) >= limit:
                break
        return snippets

    def _classify_error(self, lines: List[str]) -> Optional[str]:
        text = "\n".join(lines)
        for label, pattern in ERROR_PATTERNS.items():
            if pattern.search(text):
                return label
        return "unknown"

