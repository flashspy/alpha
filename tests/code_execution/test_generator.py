"""
Comprehensive Tests for CodeGenerator

Tests code generation for all supported languages, context-aware generation,
generation with tests, code refinement, error handling, and statistics tracking.

Total tests: 17
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from alpha.code_execution.generator import (
    CodeGenerator,
    GeneratedCode,
    CodeGenerationError
)


class TestCodeGenerator:
    """Test suite for CodeGenerator"""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service for testing"""
        service = Mock()
        service.generate = AsyncMock(return_value=Mock(
            text='{"code": "print(\'Hello, World!\')", "description": "Simple print", "complexity": "simple"}'
        ))
        return service

    @pytest.fixture
    def generator(self, mock_llm_service):
        """Create CodeGenerator instance with mocked LLM"""
        return CodeGenerator(mock_llm_service)

    @pytest.mark.asyncio
    async def test_generate_code_python_success(self, generator, mock_llm_service):
        """Test successful Python code generation"""
        mock_llm_service.generate.return_value = Mock(
            text='{"code": "def add(a, b):\\n    return a + b\\n\\nprint(add(2, 3))", '
                 '"description": "Addition function", "complexity": "simple"}'
        )

        result = await generator.generate_code("write a function to add two numbers", "python")

        assert result.code is not None
        assert result.language == "python"
        assert "def add" in result.code
        assert result.description == "Addition function"
        assert result.complexity == "simple"

    @pytest.mark.asyncio
    async def test_generate_code_javascript_success(self, generator, mock_llm_service):
        """Test successful JavaScript code generation"""
        mock_llm_service.generate.return_value = Mock(
            text='{"code": "function multiply(a, b) { return a * b; }", '
                 '"description": "Multiplication function"}'
        )

        result = await generator.generate_code("create a multiply function", "javascript")

        assert result.code is not None
        assert result.language == "javascript"
        assert "function multiply" in result.code

    @pytest.mark.asyncio
    async def test_generate_code_bash_success(self, generator, mock_llm_service):
        """Test successful Bash code generation"""
        mock_llm_service.generate.return_value = Mock(
            text='{"code": "#!/bin/bash\\necho \\"Hello from Bash\\"", '
                 '"description": "Bash echo script"}'
        )

        result = await generator.generate_code("create a hello script", "bash")

        assert result.code is not None
        assert result.language == "bash"
        assert "echo" in result.code

    @pytest.mark.asyncio
    async def test_generate_code_with_context(self, generator, mock_llm_service):
        """Test context-aware code generation"""
        context = {
            "variables": ["x", "y"],
            "data_type": "integer",
            "constraints": "must be positive"
        }

        await generator.generate_code("process data", "python", context=context)

        # Verify context was passed to LLM
        call_args = mock_llm_service.generate.call_args
        prompt = call_args[1]["prompt"]
        assert "Context:" in prompt
        assert "variables" in prompt

    @pytest.mark.asyncio
    async def test_generate_with_tests_python(self, generator, mock_llm_service):
        """Test code generation with test cases"""
        mock_llm_service.generate.return_value = Mock(
            text='{"code": "def divide(a, b):\\n    return a / b", '
                 '"tests": "def test_divide():\\n    assert divide(10, 2) == 5", '
                 '"description": "Division with tests"}'
        )

        result = await generator.generate_with_tests("create division function", "python")

        assert result.code is not None
        assert result.tests is not None
        assert "def divide" in result.code
        assert "test_divide" in result.tests

    @pytest.mark.asyncio
    async def test_generate_with_tests_javascript(self, generator, mock_llm_service):
        """Test JavaScript code generation with tests"""
        mock_llm_service.generate.return_value = Mock(
            text='{"code": "function square(n) { return n * n; }", '
                 '"tests": "test(\\"square\\", () => { expect(square(4)).toBe(16); })", '
                 '"description": "Square with tests"}'
        )

        result = await generator.generate_with_tests("square function", "javascript")

        assert result.code is not None
        assert result.tests is not None
        assert "square" in result.tests

    @pytest.mark.asyncio
    async def test_refine_code_success(self, generator, mock_llm_service):
        """Test code refinement based on feedback"""
        original_code = "print('hello')"
        feedback = "Add error handling and use logging instead"

        mock_llm_service.generate.return_value = Mock(
            text='{"code": "import logging\\nlogging.info(\\"hello\\")", '
                 '"description": "Improved with logging"}'
        )

        result = await generator.refine_code(original_code, feedback, "python")

        assert result.code is not None
        assert "logging" in result.code.lower() or "improved" in result.description.lower()

    @pytest.mark.asyncio
    async def test_llm_failure_handling(self, generator, mock_llm_service):
        """Test handling of LLM service failures"""
        mock_llm_service.generate.side_effect = Exception("LLM service unavailable")

        with pytest.raises(CodeGenerationError) as exc_info:
            await generator.generate_code("test task", "python")

        assert "LLM generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_response_parsing_json(self, generator, mock_llm_service):
        """Test JSON response parsing"""
        mock_llm_service.generate.return_value = Mock(
            text='{"code": "x = 1", "description": "Variable assignment", '
                 '"dependencies": ["math"], "complexity": "simple", "estimated_runtime": 1}'
        )

        result = await generator.generate_code("create variable", "python")

        assert result.code == "x = 1"
        assert result.description == "Variable assignment"
        assert result.dependencies == ["math"]
        assert result.complexity == "simple"
        assert result.estimated_runtime == 1

    @pytest.mark.asyncio
    async def test_response_parsing_markdown(self, generator, mock_llm_service):
        """Test markdown code block parsing (fallback)"""
        mock_llm_service.generate.return_value = Mock(
            text='Here is the code:\n```python\nprint("test")\n```\nThis prints test.'
        )

        result = await generator.generate_code("print test", "python")

        assert result.code is not None
        assert 'print("test")' in result.code

    @pytest.mark.asyncio
    async def test_response_parsing_raw(self, generator, mock_llm_service):
        """Test raw response parsing (last resort)"""
        mock_llm_service.generate.return_value = Mock(
            text='x = 42\nprint(x)'
        )

        result = await generator.generate_code("create x", "python")

        assert result.code is not None
        assert "x = 42" in result.code

    @pytest.mark.asyncio
    async def test_empty_task_handling(self, generator):
        """Test handling of empty task description"""
        # Empty task should still work (LLM decides what to do)
        result = await generator.generate_code("", "python")
        
        # Should return something from mocked LLM
        assert result.code is not None

    @pytest.mark.asyncio
    async def test_invalid_json_fallback(self, generator, mock_llm_service):
        """Test fallback when JSON parsing fails"""
        mock_llm_service.generate.return_value = Mock(
            text='This is not JSON ```python\ncode_here = True\n```'
        )

        result = await generator.generate_code("test", "python")

        assert result.code is not None
        assert "code_here" in result.code

    def test_statistics_tracking(self, generator):
        """Test statistics tracking"""
        initial_stats = generator.get_statistics()
        assert initial_stats["total_generations"] == 0
        assert initial_stats["successful_generations"] == 0
        assert initial_stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_statistics_on_success(self, generator):
        """Test statistics update on successful generation"""
        await generator.generate_code("test", "python")
        
        stats = generator.get_statistics()
        assert stats["total_generations"] == 1
        assert stats["successful_generations"] == 1
        assert stats["success_rate"] == 100.0

    @pytest.mark.asyncio
    async def test_statistics_on_failure(self, generator, mock_llm_service):
        """Test statistics update on failed generation"""
        mock_llm_service.generate.side_effect = Exception("Failure")

        try:
            await generator.generate_code("test", "python")
        except CodeGenerationError:
            pass

        stats = generator.get_statistics()
        assert stats["total_generations"] == 1
        assert stats["successful_generations"] == 0
        assert stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_complex_task_detection(self, generator, mock_llm_service):
        """Test detection of complex algorithmic tasks"""
        await generator.generate_code(
            "implement an efficient sorting algorithm with optimization",
            "python"
        )

        # Verify metadata includes complexity indicator
        call_args = mock_llm_service.generate.call_args
        metadata = call_args[1].get("metadata", {})
        assert "is_complex" in metadata or "task_type" in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
