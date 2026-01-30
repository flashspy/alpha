"""
JavaScript Language Handler

Provides JavaScript-specific code generation templates,
syntax validation, and execution configuration.

Supports: Node.js 20+
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class JavaScriptHandler:
    """Handler for JavaScript code generation and validation"""

    def __init__(self):
        self.language = "javascript"
        self.version = "20"
        self.docker_image = "node:20-slim"

    def get_template(self, task_type: str) -> str:
        """Get code template for specific task type"""

        templates = {
            "data_processing": '''/**
 * Data Processing Script
 *
 * Task: {task}
 */

async function main() {
    try {
        // Your code here
        console.log("Processing complete");
        return 0;
    } catch (error) {
        console.error("Error:", error.message);
        return 1;
    }
}

main().then(code => process.exit(code));
''',
            "api_call": '''/**
 * API Call Script
 *
 * Task: {task}
 */

async function main() {
    try {
        // Your API call code here
        // Example: const response = await fetch(url);
        console.log("API call complete");
        return 0;
    } catch (error) {
        console.error("Error:", error.message);
        return 1;
    }
}

main().then(code => process.exit(code));
''',
            "file_operation": '''/**
 * File Operation Script
 *
 * Task: {task}
 */

const fs = require('fs').promises;
const path = require('path');

async function main() {
    try {
        // Your file operation code here
        console.log("File operation complete");
        return 0;
    } catch (error) {
        console.error("Error:", error.message);
        return 1;
    }
}

main().then(code => process.exit(code));
''',
            "default": '''/**
 * JavaScript Script
 *
 * Task: {task}
 */

async function main() {
    try {
        // Your code here
        console.log("Complete");
        return 0;
    } catch (error) {
        console.error("Error:", error.message);
        return 1;
    }
}

main().then(code => process.exit(code));
'''
        }

        return templates.get(task_type, templates["default"])

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate JavaScript syntax (basic validation).

        Note: For full validation, would need esprima package.
        This is a basic check for common syntax errors.
        """
        try:
            # Basic syntax checks
            errors = []

            # Check for balanced braces
            if code.count('{') != code.count('}'):
                errors.append("Unbalanced curly braces")

            # Check for balanced parentheses
            if code.count('(') != code.count(')'):
                errors.append("Unbalanced parentheses")

            # Check for balanced brackets
            if code.count('[') != code.count(']'):
                errors.append("Unbalanced square brackets")

            # Check for unterminated strings (basic)
            # Count quotes (excluding escaped quotes)
            single_quotes = len(re.findall(r"(?<!\\)'", code))
            double_quotes = len(re.findall(r'(?<!\\)"', code))
            if single_quotes % 2 != 0:
                errors.append("Unterminated single quote string")
            if double_quotes % 2 != 0:
                errors.append("Unterminated double quote string")

            if errors:
                return False, "; ".join(errors)

            return True, None

        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"JavaScript validation failed: {error_msg}")
            return False, error_msg

    def get_dangerous_patterns(self) -> list[str]:
        """Get list of dangerous code patterns to detect"""

        return [
            "require('child_process')",  # Warning: can execute commands
            "require('fs')",  # Warning: file access
            "eval(",  # Dangerous: code execution
            "Function(",  # Dangerous: dynamic function creation
            "process.exit",  # Warning: can terminate process
            "require('http')",  # Warning: network access
            "require('https')",  # Warning: network access
            "unlink(",  # Warning: file deletion
            "rm -rf",  # Dangerous: file deletion
        ]

    def get_security_recommendations(self) -> Dict[str, str]:
        """Get security recommendations for JavaScript"""

        return {
            "require": "Restrict require() to safe modules only",
            "file_access": "Use read-only file access when possible",
            "child_process": "Avoid child_process unless necessary",
            "eval": "Never use eval() or Function() with untrusted input",
            "network": "Restrict network access unless required",
        }

    def get_execution_config(self) -> Dict[str, Any]:
        """Get default execution configuration"""

        return {
            "docker_image": self.docker_image,
            "command": ["node"],
            "timeout": 30,
            "memory": "256m",
            "cpu_quota": 50000,
            "working_dir": "/workspace",
        }

    def get_test_template(self) -> str:
        """Get Jest test template"""

        return '''/**
 * Tests for generated code
 */

describe('Generated Code Tests', () => {
    test('basic functionality', () => {
        // Import your code here
        // const myFunction = require('./your_code');

        // Your test code here
        expect(true).toBe(true);  // Replace with actual test
    });

    test('error handling', () => {
        // Test error cases
        expect(true).toBe(true);  // Replace with actual test
    });

    // Add more test cases as needed
});
'''

    def format_code(self, code: str) -> str:
        """Format JavaScript code (basic formatting)"""

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
        """Extract require statements to identify dependencies"""

        dependencies = []

        # Find require() calls
        require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
        matches = re.findall(require_pattern, code)

        for match in matches:
            # Skip built-in modules
            if not match.startswith('.') and not match.startswith('/'):
                # Extract package name (before first /)
                package = match.split('/')[0]
                dependencies.append(package)

        # Remove duplicates and built-in modules
        builtin_modules = {
            'fs', 'path', 'http', 'https', 'url', 'util', 'events',
            'stream', 'crypto', 'os', 'child_process', 'buffer'
        }
        unique_deps = list(set(dependencies))
        external_deps = [dep for dep in unique_deps if dep not in builtin_modules]

        return external_deps
