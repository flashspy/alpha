"""
Python Language Handler

Provides Python-specific code generation templates,
syntax validation, and execution configuration.

Supports: Python 3.12+
"""

import ast
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PythonHandler:
    """Handler for Python code generation and validation"""

    def __init__(self):
        self.language = "python"
        self.version = "3.12"
        self.docker_image = "python:3.12-slim"

    def get_template(self, task_type: str) -> str:
        """Get code template for specific task type"""

        templates = {
            "data_processing": '''"""
Data Processing Script

Task: {task}
"""

def main():
    """Main function"""
    # Your code here
    pass


if __name__ == "__main__":
    main()
''',
            "api_call": '''"""
API Call Script

Task: {task}
"""

import requests
import json


def main():
    """Main function"""
    try:
        # Your API call code here
        pass
    except requests.RequestException as e:
        print(f"Error: {{e}}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
''',
            "file_operation": '''"""
File Operation Script

Task: {task}
"""

import os
from pathlib import Path


def main():
    """Main function"""
    try:
        # Your file operation code here
        pass
    except (IOError, OSError) as e:
        print(f"Error: {{e}}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
''',
            "default": '''"""
Python Script

Task: {task}
"""


def main():
    """Main function"""
    # Your code here
    pass


if __name__ == "__main__":
    main()
'''
        }

        return templates.get(task_type, templates["default"])

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate Python syntax.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            logger.warning(f"Python syntax validation failed: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Python validation failed: {error_msg}")
            return False, error_msg

    def get_dangerous_patterns(self) -> list[str]:
        """Get list of dangerous code patterns to detect"""

        return [
            "import os",  # Warning: can access filesystem
            "import subprocess",  # Warning: can execute commands
            "import shutil",  # Warning: can delete files
            "open(",  # Warning: file access
            "eval(",  # Dangerous: code execution
            "exec(",  # Dangerous: code execution
            "__import__",  # Dangerous: dynamic imports
            "compile(",  # Dangerous: code compilation
            "rm -rf",  # Dangerous: file deletion
            "rmtree(",  # Dangerous: directory deletion
        ]

    def get_security_recommendations(self) -> Dict[str, str]:
        """Get security recommendations for Python"""

        return {
            "imports": "Restrict imports to safe modules only",
            "file_access": "Use read-only file access when possible",
            "subprocess": "Avoid subprocess calls unless necessary",
            "eval_exec": "Never use eval() or exec() with untrusted input",
            "permissions": "Run with minimal required permissions",
        }

    def get_execution_config(self) -> Dict[str, Any]:
        """Get default execution configuration"""

        return {
            "docker_image": self.docker_image,
            "command": ["python", "-u"],  # -u for unbuffered output
            "timeout": 30,
            "memory": "256m",
            "cpu_quota": 50000,
            "working_dir": "/workspace",
        }

    def get_test_template(self) -> str:
        """Get pytest test template"""

        return '''"""
Tests for generated code
"""

import pytest


def test_basic_functionality():
    """Test basic functionality"""
    # Import your code module here
    # from your_code import main

    # Your test code here
    assert True  # Replace with actual test


def test_error_handling():
    """Test error handling"""
    # Test error cases
    assert True  # Replace with actual test


# Add more test cases as needed
'''

    def format_code(self, code: str) -> str:
        """Format Python code (basic formatting)"""

        # Remove extra blank lines
        lines = code.split("\n")
        formatted_lines = []
        prev_blank = False

        for line in lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue  # Skip consecutive blank lines
            formatted_lines.append(line)
            prev_blank = is_blank

        return "\n".join(formatted_lines)

    def extract_dependencies(self, code: str) -> list[str]:
        """Extract import statements to identify dependencies"""

        dependencies = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
        except SyntaxError:
            # If parsing fails, try regex fallback
            import re
            imports = re.findall(r'^\s*import\s+(\w+)', code, re.MULTILINE)
            from_imports = re.findall(r'^\s*from\s+(\w+)', code, re.MULTILINE)
            dependencies = imports + from_imports

        # Filter to keep only top-level packages
        unique_deps = list(set(dep.split('.')[0] for dep in dependencies))

        # Exclude stdlib modules
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 'time', 're', 'math',
            'random', 'collections', 'itertools', 'functools', 'pathlib'
        }
        external_deps = [dep for dep in unique_deps if dep not in stdlib_modules]

        return external_deps
