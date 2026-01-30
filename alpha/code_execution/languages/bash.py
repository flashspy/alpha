"""
Bash Language Handler

Provides Bash-specific code generation templates,
syntax validation, and execution configuration.

Supports: Bash 5.2+
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BashHandler:
    """Handler for Bash script generation and validation"""

    def __init__(self):
        self.language = "bash"
        self.version = "5.2"
        self.docker_image = "bash:5.2-alpine"

    def get_template(self, task_type: str) -> str:
        """Get code template for specific task type"""

        templates = {
            "file_operation": '''#!/bin/bash
#
# File Operation Script
#
# Task: {task}
#

set -e  # Exit on error
set -u  # Exit on undefined variable

main() {
    # Your code here
    echo "Operation complete"
    return 0
}

main "$@"
''',
            "system_admin": '''#!/bin/bash
#
# System Administration Script
#
# Task: {task}
#

set -e  # Exit on error
set -u  # Exit on undefined variable

main() {
    # Check for required commands
    # command -v somecommand >/dev/null 2>&1 || { echo "Error: somecommand not found"; exit 1; }

    # Your code here
    echo "Task complete"
    return 0
}

main "$@"
''',
            "data_processing": '''#!/bin/bash
#
# Data Processing Script
#
# Task: {task}
#

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Fail on pipe errors

main() {
    # Your data processing code here
    echo "Processing complete"
    return 0
}

main "$@"
''',
            "default": '''#!/bin/bash
#
# Bash Script
#
# Task: {task}
#

set -e  # Exit on error
set -u  # Exit on undefined variable

main() {
    # Your code here
    echo "Complete"
    return 0
}

main "$@"
'''
        }

        return templates.get(task_type, templates["default"])

    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate Bash syntax (basic validation).

        Note: For full validation, would need bashlex package or bash -n.
        This is a basic check for common syntax errors.
        """
        try:
            errors = []

            # Check for shebang
            if not code.strip().startswith('#!'):
                errors.append("Missing shebang line (#!/bin/bash)")

            # Check for balanced quotes
            single_quotes = len(re.findall(r"(?<!\\)'", code))
            double_quotes = len(re.findall(r'(?<!\\)"', code))
            if single_quotes % 2 != 0:
                errors.append("Unbalanced single quotes")
            if double_quotes % 2 != 0:
                errors.append("Unbalanced double quotes")

            # Check for common dangerous patterns
            if re.search(r'\brm\s+-rf\s+/', code):
                errors.append("Dangerous: 'rm -rf /' detected")

            # Check for unclosed constructs
            if_count = len(re.findall(r'\bif\b', code))
            fi_count = len(re.findall(r'\bfi\b', code))
            if if_count != fi_count:
                errors.append(f"Unbalanced if/fi: {if_count} if, {fi_count} fi")

            for_count = len(re.findall(r'\bfor\b', code))
            done_count = len(re.findall(r'\bdone\b', code))
            while_count = len(re.findall(r'\bwhile\b', code))
            if (for_count + while_count) != done_count:
                errors.append("Unbalanced for/while/done")

            case_count = len(re.findall(r'\bcase\b', code))
            esac_count = len(re.findall(r'\besac\b', code))
            if case_count != esac_count:
                errors.append("Unbalanced case/esac")

            if errors:
                return False, "; ".join(errors)

            return True, None

        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.error(f"Bash validation failed: {error_msg}")
            return False, error_msg

    def get_dangerous_patterns(self) -> list[str]:
        """Get list of dangerous code patterns to detect"""

        return [
            "rm -rf /",  # Dangerous: root deletion
            "rm -rf /*",  # Dangerous: root deletion
            "> /dev/sda",  # Dangerous: disk overwrite
            "dd if=",  # Warning: disk operations
            "mkfs",  # Dangerous: filesystem formatting
            "fdisk",  # Dangerous: disk partitioning
            "curl | bash",  # Dangerous: execute remote code
            "wget | bash",  # Dangerous: execute remote code
            "chmod 777",  # Warning: insecure permissions
            "eval ",  # Warning: code execution
        ]

    def get_security_recommendations(self) -> Dict[str, str]:
        """Get security recommendations for Bash"""

        return {
            "quotes": "Always quote variables: \"$var\" not $var",
            "set_flags": "Use 'set -euo pipefail' for safer scripts",
            "rm_commands": "Never use 'rm -rf' without careful validation",
            "user_input": "Validate and sanitize all user input",
            "sudo": "Avoid sudo unless absolutely necessary",
            "eval": "Never use eval with untrusted input",
        }

    def get_execution_config(self) -> Dict[str, Any]:
        """Get default execution configuration"""

        return {
            "docker_image": self.docker_image,
            "command": ["bash"],
            "timeout": 30,
            "memory": "128m",  # Bash typically needs less memory
            "cpu_quota": 50000,
            "working_dir": "/workspace",
        }

    def get_test_template(self) -> str:
        """Get bats test template"""

        return '''#!/usr/bin/env bats
#
# Tests for generated Bash script
#

@test "basic functionality" {
    # Source your script here
    # source your_script.sh

    # Your test code here
    run echo "test"
    [ "$status" -eq 0 ]
}

@test "error handling" {
    # Test error cases
    run echo "test"
    [ "$status" -eq 0 ]
}

# Add more test cases as needed
'''

    def format_code(self, code: str) -> str:
        """Format Bash code (basic formatting)"""

        # Ensure shebang is first line
        lines = code.split("\n")
        formatted_lines = []

        # Find shebang
        shebang = None
        other_lines = []
        for line in lines:
            if line.strip().startswith('#!'):
                shebang = line
            else:
                other_lines.append(line)

        # Add shebang if found
        if shebang:
            formatted_lines.append(shebang)
        else:
            formatted_lines.append("#!/bin/bash")

        # Add rest of lines, removing consecutive blanks
        prev_blank = False
        for line in other_lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            formatted_lines.append(line)
            prev_blank = is_blank

        return "\n".join(formatted_lines)

    def extract_dependencies(self, code: str) -> list[str]:
        """Extract external commands used in script"""

        dependencies = []

        # Find command calls (basic pattern matching)
        # Look for common patterns like: command, $(command), `command`
        command_patterns = [
            r'\b([a-z][a-z0-9_-]+)\s',  # Regular commands
            r'\$\(([a-z][a-z0-9_-]+)',  # Command substitution
            r'`([a-z][a-z0-9_-]+)',  # Backtick substitution
        ]

        for pattern in command_patterns:
            matches = re.findall(pattern, code)
            dependencies.extend(matches)

        # Remove built-in commands
        builtins = {
            'echo', 'cd', 'pwd', 'exit', 'return', 'test', 'set',
            'export', 'source', 'alias', 'unset', 'read', 'shift',
            'if', 'then', 'else', 'elif', 'fi', 'case', 'esac',
            'for', 'while', 'do', 'done', 'function', 'local'
        }

        external_commands = [cmd for cmd in set(dependencies) if cmd not in builtins]

        return external_commands
