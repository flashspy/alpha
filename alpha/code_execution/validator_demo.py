"""
CodeValidator Demonstration Script

This script demonstrates the usage of the CodeValidator module
for validating code syntax, security, and quality.

Usage:
    python validator_demo.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from alpha.code_execution.validator import CodeValidator, ValidationResult, SecurityReport, QualityReport


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_python_validation():
    """Demonstrate Python code validation"""
    print_section("Python Code Validation")

    validator = CodeValidator()

    # Example 1: Well-written Python code
    good_code = '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers"""
    try:
        if not numbers:
            return 0
        return sum(numbers) / len(numbers)
    except TypeError:
        print("Error: Invalid input type")
        return None

# Test the function
result = calculate_average([1, 2, 3, 4, 5])
print(f"Average: {result}")
'''

    print("\n📝 Code Sample:")
    print(good_code)

    print("\n🔍 Syntax Validation:")
    syntax = validator.validate_syntax(good_code, "python")
    print(syntax)

    print("\n🛡️  Security Check:")
    security = validator.check_security(good_code, "python")
    print(security)

    print("\n⭐ Quality Assessment:")
    quality = validator.assess_quality(good_code, "python")
    print(quality)


def demo_dangerous_code():
    """Demonstrate security detection on dangerous code"""
    print_section("Dangerous Code Detection")

    validator = CodeValidator()

    # Example: Dangerous code with security issues
    dangerous_code = '''
import subprocess
import os

# Dangerous: Execute shell commands
subprocess.call("rm -rf /tmp/*", shell=True)

# Dangerous: Arbitrary code execution
user_input = input("Enter code: ")
eval(user_input)

# Warning: File system access
os.system("cat /etc/passwd")
'''

    print("\n📝 Code Sample:")
    print(dangerous_code)

    print("\n🛡️  Security Check:")
    security = validator.check_security(dangerous_code, "python")
    print(security)


def demo_javascript_validation():
    """Demonstrate JavaScript code validation"""
    print_section("JavaScript Code Validation")

    validator = CodeValidator()

    js_code = '''
/**
 * Fetch user data from API
 */
async function getUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch user data');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching user data:', error);
        return null;
    }
}
'''

    print("\n📝 Code Sample:")
    print(js_code)

    print("\n🔍 Syntax Validation:")
    syntax = validator.validate_syntax(js_code, "javascript")
    print(syntax)

    print("\n🛡️  Security Check:")
    security = validator.check_security(js_code, "javascript")
    print(security)

    print("\n⭐ Quality Assessment:")
    quality = validator.assess_quality(js_code, "javascript")
    print(quality)


def demo_bash_validation():
    """Demonstrate Bash script validation"""
    print_section("Bash Script Validation")

    validator = CodeValidator()

    bash_code = '''#!/bin/bash
#
# Backup Script
#
# Creates a backup of specified directory
#

set -e  # Exit on error
set -u  # Exit on undefined variable

BACKUP_DIR="/backup"
SOURCE_DIR="/data"

main() {
    if [ ! -d "$SOURCE_DIR" ]; then
        echo "Error: Source directory does not exist"
        return 1
    fi

    echo "Creating backup..."
    tar -czf "${BACKUP_DIR}/backup_$(date +%Y%m%d).tar.gz" "$SOURCE_DIR"
    echo "Backup complete"
    return 0
}

main "$@"
'''

    print("\n📝 Code Sample:")
    print(bash_code)

    print("\n🔍 Syntax Validation:")
    syntax = validator.validate_syntax(bash_code, "bash")
    print(syntax)

    print("\n🛡️  Security Check:")
    security = validator.check_security(bash_code, "bash")
    print(security)

    print("\n⭐ Quality Assessment:")
    quality = validator.assess_quality(bash_code, "bash")
    print(quality)


def demo_invalid_syntax():
    """Demonstrate handling of invalid syntax"""
    print_section("Invalid Syntax Handling")

    validator = CodeValidator()

    invalid_code = '''
def broken_function(
    print("Missing closing parenthesis")
    return "This won't work"
'''

    print("\n📝 Code Sample:")
    print(invalid_code)

    print("\n🔍 Syntax Validation:")
    syntax = validator.validate_syntax(invalid_code, "python")
    print(syntax)


def main():
    """Run all demonstrations"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║              CodeValidator Module Demonstration                   ║
║                                                                   ║
║  Phase 4.1: Code Generation & Safe Execution                      ║
║  Alpha's Code Validation System                                   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    try:
        demo_python_validation()
        demo_dangerous_code()
        demo_javascript_validation()
        demo_bash_validation()
        demo_invalid_syntax()

        print_section("✅ Demonstration Complete")
        print("\nThe CodeValidator module successfully:")
        print("  ✓ Validates syntax for Python, JavaScript, and Bash")
        print("  ✓ Detects dangerous security patterns")
        print("  ✓ Assesses code quality with metrics")
        print("  ✓ Provides actionable recommendations")
        print("  ✓ Handles errors gracefully")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
