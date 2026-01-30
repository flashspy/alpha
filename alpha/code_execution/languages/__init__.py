"""
Language-Specific Handlers

This module contains language-specific code generation templates,
syntax validators, and execution configurations.

Supported Languages:
- Python 3.12+
- JavaScript (Node.js 20+)
- Bash 5.2+
"""

from .python import PythonHandler
from .javascript import JavaScriptHandler
from .bash import BashHandler

__all__ = [
    "PythonHandler",
    "JavaScriptHandler",
    "BashHandler",
]

# Language registry for dynamic handler selection
LANGUAGE_HANDLERS = {
    "python": PythonHandler,
    "javascript": JavaScriptHandler,
    "js": JavaScriptHandler,  # Alias
    "bash": BashHandler,
    "sh": BashHandler,  # Alias
}


def get_handler(language: str):
    """Get language handler by name"""
    language_lower = language.lower()
    if language_lower not in LANGUAGE_HANDLERS:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported languages: {list(LANGUAGE_HANDLERS.keys())}"
        )
    return LANGUAGE_HANDLERS[language_lower]()
