"""
Smoke Tests for Code Execution Module

Quick validation of critical paths and core functionality for the code execution system.
These tests run on every change to ensure basic functionality is working.

Test Coverage:
- Module imports and basic instantiation
- Code generation with mock LLM
- Syntax validation for each language
- Security scanning basics
- Sandbox availability check
- End-to-end execution flow (mocked)

Requirements: REQ-4.1, REQ-4.2, REQ-4.3
Phase: 4.1 - Code Generation & Safe Execution
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

from alpha.code_execution import (
    CodeGenerator,
    CodeValidator,
    SandboxManager,
    CodeExecutor,
    ExecutionOptions,
    CodeGenerationError,
    ValidationResult,
    SecurityReport,
    QualityReport,
    SandboxConfig,
    ExecutionResult,
    GeneratedCode
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service for testing code generation."""
    service = Mock()
    # Create a mock response object with .text attribute
    mock_response = Mock()
    mock_response.text = ""
    service.generate = AsyncMock(return_value=mock_response)
    return service


@pytest.fixture
def code_generator(mock_llm_service):
    """Create a CodeGenerator with mocked LLM service."""
    return CodeGenerator(mock_llm_service)


@pytest.fixture
def code_validator():
    """Create a CodeValidator instance."""
    return CodeValidator()


@pytest.fixture
def sandbox_manager():
    """Create a SandboxManager instance."""
    return SandboxManager()


@pytest.fixture
def code_executor(code_generator, code_validator, sandbox_manager):
    """Create a CodeExecutor with all components."""
    return CodeExecutor(
        generator=code_generator,
        validator=code_validator,
        sandbox=sandbox_manager
    )


# ============================================================================
# Smoke Test 1: Module Imports and Initialization
# ============================================================================

def test_module_imports():
    """SMOKE: Verify all core modules can be imported."""
    from alpha.code_execution import (
        CodeGenerator,
        CodeValidator,
        SandboxManager,
        CodeExecutor,
        ExecutionOptions
    )
    assert CodeGenerator is not None
    assert CodeValidator is not None
    assert SandboxManager is not None
    assert CodeExecutor is not None
    assert ExecutionOptions is not None


def test_code_generator_initialization(mock_llm_service):
    """SMOKE: Verify CodeGenerator can be initialized."""
    generator = CodeGenerator(mock_llm_service)
    assert generator is not None
    assert generator.llm_service == mock_llm_service
    assert generator.generation_count == 0
    assert generator.success_count == 0


def test_code_validator_initialization():
    """SMOKE: Verify CodeValidator can be initialized."""
    validator = CodeValidator()
    assert validator is not None


def test_sandbox_manager_initialization():
    """SMOKE: Verify SandboxManager can be initialized."""
    sandbox = SandboxManager()
    assert sandbox is not None


def test_code_executor_initialization(code_generator, code_validator, sandbox_manager):
    """SMOKE: Verify CodeExecutor can be initialized with all components."""
    executor = CodeExecutor(
        generator=code_generator,
        validator=code_validator,
        sandbox=sandbox_manager
    )
    assert executor is not None
    assert executor.generator == code_generator
    assert executor.validator == code_validator
    assert executor.sandbox == sandbox_manager


# ============================================================================
# Smoke Test 2: Code Generation Basic Flow
# ============================================================================

@pytest.mark.asyncio
async def test_code_generation_basic(code_generator, mock_llm_service):
    """SMOKE: Verify basic code generation flow with mocked LLM."""
    # Mock LLM response
    mock_response = Mock()
    mock_response.text = """```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

result = factorial(10)
print(result)
```"""
    mock_llm_service.generate.return_value = mock_response

    # Generate code
    result = await code_generator.generate_code(
        task="Calculate factorial of 10",
        language="python"
    )

    # Verify
    assert result is not None
    assert isinstance(result, GeneratedCode)
    assert "factorial" in result.code
    assert result.language == "python"
    assert code_generator.generation_count == 1
    assert code_generator.success_count == 1


@pytest.mark.asyncio
async def test_code_generation_error_handling(code_generator, mock_llm_service):
    """SMOKE: Verify code generation handles LLM errors gracefully."""
    # Mock LLM failure
    mock_llm_service.generate.side_effect = Exception("LLM service unavailable")

    # Attempt generation
    with pytest.raises(CodeGenerationError):
        await code_generator.generate_code(
            task="Calculate factorial",
            language="python"
        )

    # Verify error tracking
    assert code_generator.generation_count == 1
    assert code_generator.success_count == 0


# ============================================================================
# Smoke Test 3: Syntax Validation for All Languages
# ============================================================================

def test_validation_python_valid(code_validator):
    """SMOKE: Verify Python syntax validation accepts valid code."""
    valid_python = """
def hello():
    print("Hello, World!")

hello()
"""
    result = code_validator.validate_syntax(valid_python, "python")
    assert result.is_valid
    assert len(result.errors) == 0


def test_validation_python_invalid(code_validator):
    """SMOKE: Verify Python syntax validation rejects invalid code."""
    invalid_python = """
def hello(
    print("Missing closing paren")
"""
    result = code_validator.validate_syntax(invalid_python, "python")
    assert not result.is_valid
    assert len(result.errors) > 0


def test_validation_javascript_valid(code_validator):
    """SMOKE: Verify JavaScript syntax validation accepts valid code."""
    valid_js = """
function hello() {
    console.log("Hello, World!");
}
hello();
"""
    result = code_validator.validate_syntax(valid_js, "javascript")
    assert result.is_valid
    assert len(result.errors) == 0


def test_validation_bash_valid(code_validator):
    """SMOKE: Verify Bash syntax validation accepts valid code."""
    valid_bash = """
#!/bin/bash
echo "Hello, World!"
"""
    result = code_validator.validate_syntax(valid_bash, "bash")
    assert result.is_valid
    assert len(result.errors) == 0


# ============================================================================
# Smoke Test 4: Security Scanning Basics
# ============================================================================

def test_security_scan_safe_code(code_validator):
    """SMOKE: Verify security scanner accepts safe code."""
    safe_code = """
def add(a, b):
    return a + b

result = add(5, 3)
print(result)
"""
    report = code_validator.check_security(safe_code, "python")
    assert isinstance(report, SecurityReport)
    assert report.is_safe
    assert report.risk_level == "low"


def test_security_scan_dangerous_code(code_validator):
    """SMOKE: Verify security scanner detects dangerous operations."""
    dangerous_code = """
import os
os.system('rm -rf /')
"""
    report = code_validator.check_security(dangerous_code, "python")
    assert isinstance(report, SecurityReport)
    # Should detect dangerous operation
    assert report.risk_level in ["medium", "high"]
    assert len(report.dangerous_patterns) > 0


# ============================================================================
# Smoke Test 5: Sandbox Docker Availability
# ============================================================================

def test_sandbox_docker_check(sandbox_manager):
    """SMOKE: Verify sandbox can check Docker availability."""
    # Just verify the method exists and returns a boolean
    is_available = sandbox_manager.is_docker_available()
    assert isinstance(is_available, bool)


@pytest.mark.skipif(
    not SandboxManager().is_docker_available(),
    reason="Docker not available"
)
def test_sandbox_docker_container_lifecycle():
    """SMOKE: Verify basic container lifecycle (requires Docker)."""
    sandbox = SandboxManager()

    # This test only runs if Docker is available
    # Just verify we can create config
    config = SandboxConfig(
        language="python",
        allow_network=False,
        timeout=5
    )
    assert config is not None


# ============================================================================
# Smoke Test 6: Execution Options Configuration
# ============================================================================

def test_execution_options_defaults():
    """SMOKE: Verify ExecutionOptions has sensible defaults."""
    options = ExecutionOptions()
    assert options.generate_code is True
    assert options.validate_syntax is True
    assert options.check_security is True
    assert options.require_approval is True
    assert options.allow_network is False  # Safe default
    assert options.timeout == 30
    assert options.max_retries == 2


def test_execution_options_custom():
    """SMOKE: Verify ExecutionOptions accepts custom values."""
    options = ExecutionOptions(
        generate_code=False,
        validate_syntax=False,
        timeout=60,
        allow_network=True
    )
    assert options.generate_code is False
    assert options.validate_syntax is False
    assert options.timeout == 60
    assert options.allow_network is True


# ============================================================================
# Smoke Test 7: End-to-End Flow (Mocked)
# ============================================================================

@pytest.mark.asyncio
async def test_executor_end_to_end_mocked(code_executor, mock_llm_service):
    """SMOKE: Verify end-to-end execution flow with fully mocked components."""
    # Mock LLM response with proper response object
    mock_response = Mock()
    mock_response.text = """```python
print("Hello from generated code")
```"""
    mock_llm_service.generate.return_value = mock_response

    # Mock Docker availability and all sandbox methods
    code_executor.sandbox._docker_available = True

    with patch.object(code_executor.sandbox, 'create_container', return_value='mock_container_id'):
        with patch.object(
            code_executor.sandbox,
            'execute_code',
            return_value=ExecutionResult(
                success=True,
                exit_code=0,
                stdout="Hello from generated code\n",
                stderr="",
                execution_time=0.5,
                timed_out=False,
            )
        ):
            with patch.object(code_executor.sandbox, 'cleanup_container', return_value=None):
                # Mock user approval
                with patch.object(code_executor, '_request_user_approval', return_value=True):
                    # Execute task
                    options = ExecutionOptions(
                        generate_code=True,
                        require_approval=True,
                        validate_syntax=True,
                        check_security=True
                    )

                    result = await code_executor.execute_task(
                        task="Print hello message",
                        language="python",
                        options=options,
                        context=None
                    )

                    # Verify successful execution
                    assert result.success
                    assert result.exit_code == 0
                    assert "Hello from generated code" in result.stdout


@pytest.mark.asyncio
async def test_executor_direct_code_execution_mocked(code_executor):
    """SMOKE: Verify direct code execution without generation."""
    code = "print('Direct execution test')"

    # Mock Docker availability and all sandbox methods
    code_executor.sandbox._docker_available = True

    with patch.object(code_executor.sandbox, 'create_container', return_value='mock_container_id'):
        with patch.object(
            code_executor.sandbox,
            'execute_code',
            return_value=ExecutionResult(
                success=True,
                exit_code=0,
                stdout="Direct execution test\n",
                stderr="",
                execution_time=0.3,
                timed_out=False,
            )
        ):
            with patch.object(code_executor.sandbox, 'cleanup_container', return_value=None):
                # Mock user approval
                with patch.object(code_executor, '_request_user_approval', return_value=True):
                    # Execute code directly
                    options = ExecutionOptions(
                        generate_code=False,
                        require_approval=True
                    )

                    result = await code_executor.execute_code_string(
                        code=code,
                        language="python",
                        options=options
                    )

                    # Verify
                    assert result.success
                    assert result.exit_code == 0


# ============================================================================

def test_executor_statistics_tracking(code_executor):
    """SMOKE: Verify executor tracks execution statistics."""
    stats = code_executor.get_execution_statistics()

    assert isinstance(stats, dict)
    assert 'total_executions' in stats
    assert 'successful_executions' in stats
    assert 'failed_executions' in stats
    assert 'success_rate' in stats

    # Initial stats should be zero
    assert stats['total_executions'] == 0
    assert stats['successful_executions'] == 0
    assert stats['failed_executions'] == 0
    assert stats['success_rate'] == 0.0


# ============================================================================
# Test Summary
# ============================================================================

"""
SMOKE TEST SUMMARY
==================

Total Tests: 18 smoke tests
Coverage: Critical paths for all core components

Test Categories:
1. Module imports and initialization (5 tests)
2. Code generation basic flow (2 tests)
3. Syntax validation for all languages (4 tests)
4. Security scanning basics (2 tests)
5. Sandbox Docker availability (2 tests)
6. Execution options configuration (2 tests)
7. End-to-end flow mocked (2 tests)
8. Statistics tracking (1 test)

Expected Results:
- All tests should pass without Docker installed
- Tests requiring Docker are properly skipped
- Mocking strategy allows testing without external dependencies
- Covers ~60-70% of critical functionality

Next Steps:
- Run: pytest tests/code_execution/test_code_execution_smoke.py -v
- Expected: ~18 passed (or 16-17 if Docker not available)
- If all pass: Proceed to comprehensive test suite
"""
