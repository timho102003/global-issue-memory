"""Minimal Reproducible Example (MRE) synthesis module."""

import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .patterns import CODE_NAME_PATTERNS


@dataclass
class MREResult:
    """Result of MRE synthesis.

    Attributes:
        original_code: The original code snippet.
        synthesized_mre: The synthesized minimal reproducible example.
        imports_kept: List of import statements kept.
        names_replaced: Dict mapping original names to generic names.
        line_count: Number of lines in the MRE.
        quality_score: Quality score of the MRE (0.0-1.0).
        syntax_valid: Whether the MRE has valid syntax.
        warnings: List of warnings during synthesis.
    """

    original_code: str = ""
    synthesized_mre: str = ""
    imports_kept: List[str] = field(default_factory=list)
    names_replaced: Dict[str, str] = field(default_factory=dict)
    line_count: int = 0
    quality_score: float = 0.0
    syntax_valid: bool = True
    warnings: List[str] = field(default_factory=list)


# Generic name mappings for abstraction
GENERIC_CLASS_NAMES = [
    "ServiceA", "ServiceB", "ClientA", "ClientB",
    "HandlerA", "HandlerB", "ProcessorA", "ProcessorB",
    "ManagerA", "ManagerB", "ControllerA", "ControllerB",
]

GENERIC_FUNCTION_NAMES = [
    "process_item", "handle_request", "validate_data",
    "fetch_data", "update_record", "create_item",
    "delete_item", "get_config", "run_task",
]

GENERIC_VARIABLE_NAMES = [
    "item", "data", "result", "config",
    "client", "response", "request", "value",
]


def _detect_language(code: str) -> str:
    """Detect the programming language of the code.

    Args:
        code: The code snippet.

    Returns:
        str: Detected language (python, javascript, etc.) or 'unknown'.
    """
    # Python indicators - check for common Python keywords
    python_keywords = ["def ", "import ", "from ", "class ", "elif ", "except:", "try:", "with "]
    has_python_keyword = any(keyword in code for keyword in python_keywords)

    # Strong Python indicators (def/class with or without proper syntax)
    if has_python_keyword:
        # If has def or class, likely Python even with syntax errors
        if "def " in code or "class " in code:
            return "python"
        # import/from statements are strong Python indicators
        if "import " in code or "from " in code:
            return "python"

    # JavaScript/TypeScript indicators
    if any(keyword in code for keyword in ["const ", "let ", "function ", "=> ", "async "]):
        return "javascript"

    # Go indicators
    if "func " in code and "package " in code:
        return "go"

    # Rust indicators
    if "fn " in code and ("let " in code or "mut " in code):
        return "rust"

    return "unknown"


def _extract_python_imports(code: str) -> Tuple[List[str], str]:
    """Extract import statements from Python code.

    Args:
        code: The Python code.

    Returns:
        Tuple of (list of import statements, code without imports).
    """
    imports = []
    non_import_lines = []

    for line in code.split('\n'):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            imports.append(line)
        else:
            non_import_lines.append(line)

    return imports, '\n'.join(non_import_lines)


# Standard library modules that should be kept
STANDARD_MODULES = {
    'json', 'os', 'sys', 're', 'typing', 'datetime', 'collections',
    'functools', 'itertools', 'pathlib', 'logging', 'abc', 'math',
    'dataclasses', 'enum', 'copy', 'io', 'time', 'random', 'hashlib',
    'base64', 'urllib', 'http', 'asyncio', 'threading', 'multiprocessing',
}

# Common third-party modules that should be kept
COMMON_MODULES = {
    'requests', 'httpx', 'aiohttp', 'numpy', 'pandas', 'pydantic',
    'fastapi', 'flask', 'django', 'sqlalchemy', 'pytest', 'unittest',
    'boto3', 'google', 'azure', 'openai', 'anthropic', 'langchain',
}


def _filter_imports(imports: List[str]) -> List[str]:
    """Filter imports to keep only standard/common libraries.

    Args:
        imports: List of import statements.

    Returns:
        List[str]: Filtered import statements.
    """
    filtered = []

    for imp in imports:
        # Get the module name
        if imp.strip().startswith('from '):
            # from module import ...
            match = re.match(r'from\s+(\w+)', imp.strip())
            if match:
                module = match.group(1)
            else:
                continue
        else:
            # import module
            match = re.match(r'import\s+(\w+)', imp.strip())
            if match:
                module = match.group(1)
            else:
                continue

        # Keep standard library and common modules
        if module in STANDARD_MODULES or module in COMMON_MODULES:
            filtered.append(imp)
        else:
            # Replace internal imports with a generic comment
            filtered.append(f"# import {module}  # internal module removed")

    return filtered


def _validate_python_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validate Python syntax.

    Args:
        code: The Python code to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, str(e)


def _replace_domain_names(code: str) -> Tuple[str, Dict[str, str]]:
    """Replace domain-specific names with generic ones.

    Args:
        code: The code to process.

    Returns:
        Tuple of (processed code, mapping of original->generic names).
    """
    replacements: Dict[str, str] = {}
    result = code

    class_counter = 0
    func_counter = 0
    var_counter = 0

    # Replace class names (both patterns)
    for pattern_name in ["domain_class", "domain_class_prefix"]:
        if pattern_name not in CODE_NAME_PATTERNS:
            continue
        class_pattern = CODE_NAME_PATTERNS[pattern_name]
        for match in class_pattern.finditer(code):
            original = match.group(1)
            if original not in replacements:
                if class_counter < len(GENERIC_CLASS_NAMES):
                    replacements[original] = GENERIC_CLASS_NAMES[class_counter]
                    class_counter += 1
                else:
                    replacements[original] = f"Class{class_counter}"
                    class_counter += 1

    # Replace function names
    func_pattern = CODE_NAME_PATTERNS["domain_function"]
    for match in func_pattern.finditer(code):
        original = match.group(1)
        if original not in replacements:
            if func_counter < len(GENERIC_FUNCTION_NAMES):
                replacements[original] = GENERIC_FUNCTION_NAMES[func_counter]
                func_counter += 1
            else:
                replacements[original] = f"func_{func_counter}"
                func_counter += 1

    # Replace variable names
    var_pattern = CODE_NAME_PATTERNS["domain_variable"]
    for match in var_pattern.finditer(code):
        original = match.group(1)
        # Skip if it's a common Python keyword or built-in
        if original.lower() in ('if', 'else', 'for', 'while', 'return', 'import', 'from', 'class', 'def'):
            continue
        if original not in replacements:
            if var_counter < len(GENERIC_VARIABLE_NAMES):
                replacements[original] = GENERIC_VARIABLE_NAMES[var_counter]
                var_counter += 1
            else:
                replacements[original] = f"var_{var_counter}"
                var_counter += 1

    # Apply replacements (sort by length descending to avoid partial replacements)
    for original, replacement in sorted(replacements.items(), key=lambda x: -len(x[0])):
        # Use word boundaries to avoid partial replacements
        result = re.sub(rf'\b{re.escape(original)}\b', replacement, result)

    return result, replacements


def _add_error_markers(code: str, error_message: Optional[str] = None) -> str:
    """Add error location markers to code.

    Args:
        code: The code to annotate.
        error_message: Optional error message to include.

    Returns:
        str: Code with error markers.
    """
    lines = code.split('\n')

    # Look for common error indicators
    error_indicators = [
        "raise", "assert", "except", "error", "fail",
        "# TODO", "# FIXME", "# BUG",
    ]

    marked = False
    for i, line in enumerate(lines):
        lower_line = line.lower()
        if any(indicator.lower() in lower_line for indicator in error_indicators):
            if not marked and "# ERROR" not in line:
                lines[i] = line + "  # <-- ERROR OCCURS HERE"
                marked = True
                break

    if not marked and error_message:
        # Add error context at the end
        lines.append("")
        lines.append(f"# Error: {error_message[:100]}...")

    return '\n'.join(lines)


def _trim_to_max_lines(code: str, max_lines: int = 50) -> str:
    """Trim code to maximum number of lines.

    Args:
        code: The code to trim.
        max_lines: Maximum number of lines.

    Returns:
        str: Trimmed code.
    """
    lines = code.split('\n')
    if len(lines) <= max_lines:
        return code

    # Keep imports and first part of code
    return '\n'.join(lines[:max_lines]) + "\n# ... (truncated)"


def synthesize_mre(
    code: str,
    error_message: Optional[str] = None,
    max_lines: int = 50,
) -> MREResult:
    """Synthesize a minimal reproducible example from code.

    This function:
    1. Detects the programming language
    2. Extracts and preserves necessary imports
    3. Replaces domain-specific names with generic ones
    4. Adds error location markers
    5. Trims to a reasonable size

    Args:
        code: The original code snippet.
        error_message: Optional error message for context.
        max_lines: Maximum lines for the MRE.

    Returns:
        MREResult: The synthesis result.
    """
    if not code or not code.strip():
        return MREResult(
            original_code=code,
            synthesized_mre="",
            quality_score=0.0,
            syntax_valid=True,
            warnings=["Empty code provided"],
        )

    result = MREResult(original_code=code)
    warnings = []

    # Detect language
    language = _detect_language(code)

    # Process based on language
    if language == "python":
        # Extract imports
        imports, code_body = _extract_python_imports(code)

        # Replace domain names in code body first
        processed_code, replacements = _replace_domain_names(code_body)
        result.names_replaced = replacements

        # Also replace domain names in imports
        processed_imports = []
        for imp in imports:
            processed_imp, imp_replacements = _replace_domain_names(imp)
            processed_imports.append(processed_imp)
            # Merge import replacements
            for orig, repl in imp_replacements.items():
                if orig not in replacements:
                    replacements[orig] = repl

        # Filter out internal/private package imports
        filtered_imports = _filter_imports(processed_imports)
        result.imports_kept = filtered_imports
        result.names_replaced = replacements

        # Reconstruct with imports
        mre_parts = filtered_imports + ['', processed_code] if filtered_imports else [processed_code]
        mre = '\n'.join(mre_parts)

        # Add error markers
        mre = _add_error_markers(mre, error_message)

        # Trim if needed
        mre = _trim_to_max_lines(mre, max_lines)

        # Validate syntax
        is_valid, error = _validate_python_syntax(mre)
        result.syntax_valid = is_valid
        if not is_valid:
            warnings.append(f"Syntax validation failed: {error}")

    else:
        # For other languages, do basic processing
        processed_code, replacements = _replace_domain_names(code)
        result.names_replaced = replacements

        mre = _add_error_markers(processed_code, error_message)
        mre = _trim_to_max_lines(mre, max_lines)

        # Can't validate syntax for unknown languages
        result.syntax_valid = True
        if language == "unknown":
            warnings.append("Language not detected, limited processing applied")

    result.synthesized_mre = mre
    result.line_count = len(mre.split('\n'))
    result.warnings = warnings

    # Calculate quality score
    result.quality_score = _calculate_quality_score(result)

    return result


def _calculate_quality_score(result: MREResult) -> float:
    """Calculate the quality score of an MRE.

    Factors:
    - Line count (10-50 is ideal)
    - Name abstraction (more replacements = better)
    - Syntax validity
    - Has error markers

    Args:
        result: The MRE result.

    Returns:
        float: Quality score between 0.0 and 1.0.
    """
    score = 0.0

    # Line count score (0.3 weight)
    if 10 <= result.line_count <= 50:
        score += 0.3
    elif result.line_count < 10:
        score += 0.2  # Too short
    else:
        score += 0.1  # Too long

    # Name abstraction score (0.3 weight)
    if result.names_replaced:
        abstraction_score = min(len(result.names_replaced) / 5, 1.0) * 0.3
        score += abstraction_score
    else:
        score += 0.1  # No domain names found (might be generic already)

    # Syntax validity (0.2 weight)
    if result.syntax_valid:
        score += 0.2

    # Has error markers (0.2 weight)
    if "ERROR" in result.synthesized_mre or "error" in result.synthesized_mre.lower():
        score += 0.2
    else:
        score += 0.1  # Partial credit

    return min(score, 1.0)
