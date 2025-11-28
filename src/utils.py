"""
Utility helpers shared across modules
"""

from pathlib import Path
from typing import Tuple


def resolve_source_path(source_dir: Path, relative_path: str) -> Path:
    """Return an absolute path inside the source directory"""
    return (source_dir / relative_path).resolve()


def wildcard_to_name(pattern: str, base_name: str) -> str:
    """
    Replace '*' wildcard in a pattern with the provided base name.
    If no wildcard is present, append the base name before the suffix.

    Special handling to avoid duplicated prefixes like 'testtest001.log'
    when pattern is 'test*.log' and base_name is 'test001':
    - If base_name already starts with the prefix before '*', we drop
      that prefix and only use base_name + suffix.
    """
    if "*" in pattern:
        pre, post = pattern.split("*", 1)
        if pre and base_name.startswith(pre):
            # base already includes the prefix, don't duplicate it
            return f"{base_name}{post}"
        return f"{pre}{base_name}{post}"
    path = Path(pattern)
    suffix = "".join(path.suffixes) or ""
    return f"{base_name}{suffix}"


def derive_test_paths(
    source_dir: Path,
    test_dir: str,
    reference_dir: str,
    log_pattern: str,
    reference_pattern: str,
    input_file: Path,
) -> Tuple[Path, Path]:
    """
    Given an input file, derive the associated log file and reference file paths.
    """
    base_name = input_file.stem
    log_name = wildcard_to_name(log_pattern, base_name)
    ref_name = wildcard_to_name(reference_pattern, base_name)
    log_file = resolve_source_path(source_dir, f"{test_dir}/{log_name}")
    reference_file = resolve_source_path(source_dir, f"{reference_dir}/{ref_name}")
    return log_file, reference_file

