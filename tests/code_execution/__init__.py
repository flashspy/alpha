"""
Code Execution Tests

Comprehensive test suite for Alpha Phase 4.1 Code Execution system.
Tests cover code generation, validation, sandbox execution, orchestration, and tool integration.
"""

import pytest
from unittest.mock import Mock, AsyncMock


# Shared fixtures for code execution tests
@pytest.fixture
def mock_llm_service():
    """Mock LLM service for code generation testing"""
    service = Mock()
    service.generate = AsyncMock(return_value=Mock(
        text='{"code": "print(\\"Hello, World!\\")", "description": "Simple print statement", "complexity": "simple"}'
    ))
    return service


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for sandbox testing"""
    client = Mock()

    # Mock ping
    client.ping = Mock(return_value=True)

    # Mock images
    mock_image = Mock()
    client.images = Mock()
    client.images.get = Mock(return_value=mock_image)
    client.images.pull = Mock(return_value=mock_image)

    # Mock container
    mock_container = Mock()
    mock_container.id = "test_container_123"
    mock_container.start = Mock()
    mock_container.wait = Mock(return_value={"StatusCode": 0})
    mock_container.logs = Mock(side_effect=lambda stdout=True, stderr=False:
        b"Hello, World!\n" if stdout else b"")
    mock_container.stop = Mock()
    mock_container.remove = Mock()
    mock_container.reload = Mock()
    mock_container.stats = Mock(return_value={
        "memory_stats": {"usage": 1000000, "limit": 256000000},
        "cpu_stats": {}
    })

    # Mock containers
    client.containers = Mock()
    client.containers.create = Mock(return_value=mock_container)
    client.containers.get = Mock(return_value=mock_container)

    return client


@pytest.fixture
def sample_python_code():
    """Sample valid Python code for testing"""
    return '''def factorial(n):
    """Calculate factorial of n"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
'''


@pytest.fixture
def sample_javascript_code():
    """Sample valid JavaScript code for testing"""
    return '''function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log(fibonacci(10));
'''


@pytest.fixture
def sample_bash_code():
    """Sample valid Bash code for testing"""
    return '''#!/bin/bash
for i in {1..5}; do
    echo "Number: $i"
done
'''
