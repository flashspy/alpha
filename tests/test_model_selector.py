"""
Tests for Model Selector

Tests the automatic model selection functionality for different task types.
"""

import pytest
from dataclasses import dataclass
from alpha.llm.model_selector import TaskAnalyzer, ModelSelector, TaskDifficulty


@dataclass
class ModelConfig:
    """Model configuration for testing."""
    difficulty_range: list
    max_tokens: int = 4096
    temperature: float = 0.7


class TestTaskAnalyzer:
    """Test task analysis functionality."""

    def test_simple_task_detection(self):
        """Test detection of simple tasks."""
        messages = [{"role": "user", "content": "Hello"}]
        result = TaskAnalyzer.analyze(messages)

        assert result.difficulty == TaskDifficulty.SIMPLE
        assert not result.is_coding
        assert not result.requires_reasoning

    def test_coding_task_detection(self):
        """Test detection of coding tasks."""
        messages = [{"role": "user", "content": "Write a function to sort a list in Python"}]
        result = TaskAnalyzer.analyze(messages)

        assert result.is_coding
        assert result.difficulty in [TaskDifficulty.MEDIUM, TaskDifficulty.COMPLEX]

    def test_reasoning_task_detection(self):
        """Test detection of reasoning tasks."""
        messages = [{"role": "user", "content": "Explain why asynchronous programming is important"}]
        result = TaskAnalyzer.analyze(messages)

        assert result.requires_reasoning
        assert result.difficulty in [TaskDifficulty.MEDIUM, TaskDifficulty.COMPLEX]

    def test_expert_task_detection(self):
        """Test detection of expert-level tasks."""
        messages = [{
            "role": "user",
            "content": "Explain distributed system consensus, machine learning optimization algorithms"
        }]
        result = TaskAnalyzer.analyze(messages)

        assert result.difficulty == TaskDifficulty.EXPERT

    def test_complex_coding_task(self):
        """Test detection of complex coding tasks."""
        messages = [{
            "role": "user",
            "content": "Refactor this class to improve performance and implement caching"
        }]
        result = TaskAnalyzer.analyze(messages)

        assert result.is_coding
        assert result.difficulty in [TaskDifficulty.COMPLEX, TaskDifficulty.EXPERT]


class TestModelSelector:
    """Test model selection functionality."""

    @pytest.fixture
    def models_config(self):
        """Create test model configuration."""
        return {
            "deepseek-chat": ModelConfig(
                difficulty_range=["simple", "medium"],
                max_tokens=4096,
                temperature=0.7
            ),
            "deepseek-coder": ModelConfig(
                difficulty_range=["medium", "complex"],
                max_tokens=4096,
                temperature=0.7
            ),
            "deepseek-reasoner": ModelConfig(
                difficulty_range=["complex", "expert"],
                max_tokens=8192,
                temperature=0.6
            )
        }

    def test_simple_task_uses_chat(self, models_config):
        """Test that simple tasks use deepseek-chat."""
        selector = ModelSelector(models_config)
        messages = [{"role": "user", "content": "What time is it?"}]

        model = selector.select_model(messages, default_model="deepseek-chat")

        assert model == "deepseek-chat"

    def test_coding_task_uses_coder(self, models_config):
        """Test that coding tasks use deepseek-coder."""
        selector = ModelSelector(models_config)
        messages = [{"role": "user", "content": "Write a Python function to calculate factorial"}]

        model = selector.select_model(messages, default_model="deepseek-chat")

        assert model == "deepseek-coder"

    def test_expert_task_uses_reasoner(self, models_config):
        """Test that expert tasks use deepseek-reasoner."""
        selector = ModelSelector(models_config)
        messages = [{
            "role": "user",
            "content": "Explain the Byzantine Generals problem in distributed systems"
        }]

        model = selector.select_model(messages, default_model="deepseek-chat")

        assert model == "deepseek-reasoner"

    def test_complex_reasoning_uses_reasoner(self, models_config):
        """Test that complex reasoning tasks use deepseek-reasoner."""
        selector = ModelSelector(models_config)
        messages = [{
            "role": "user",
            "content": "Analyze and compare different consensus algorithms and explain their trade-offs"
        }]

        model = selector.select_model(messages, default_model="deepseek-chat")

        assert model == "deepseek-reasoner"

    def test_coding_with_reasoning_uses_reasoner(self, models_config):
        """Test that coding tasks with reasoning use deepseek-reasoner."""
        selector = ModelSelector(models_config)
        messages = [{
            "role": "user",
            "content": "Design a scalable caching system and explain the architectural trade-offs"
        }]

        model = selector.select_model(messages, default_model="deepseek-chat")

        assert model == "deepseek-reasoner"

    def test_get_model_config(self, models_config):
        """Test getting model configuration."""
        selector = ModelSelector(models_config)

        config = selector.get_model_config("deepseek-coder")

        assert config is not None
        assert config.max_tokens == 4096
        assert "medium" in config.difficulty_range


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
