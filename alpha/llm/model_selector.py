"""
Alpha - Model Selector

Automatic model selection based on task difficulty and characteristics.
"""

import re
import logging
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TaskDifficulty(Enum):
    """Task difficulty levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class TaskCharacteristics:
    """Characteristics of a task used for model selection."""
    difficulty: TaskDifficulty
    is_coding: bool
    requires_reasoning: bool
    message_count: int
    estimated_tokens: int


class TaskAnalyzer:
    """Analyze task characteristics to determine difficulty."""

    # Keywords indicating complex tasks
    COMPLEX_KEYWORDS = [
        'refactor', 'architect', 'design', 'optimize', 'algorithm',
        'analyze', 'debug', 'performance', 'system', 'integrate',
        'complex', 'advanced', 'sophisticated'
    ]

    # Keywords indicating reasoning tasks
    REASONING_KEYWORDS = [
        'why', 'explain', 'reason', 'analyze', 'compare', 'evaluate',
        'understand', 'logic', 'think', 'consider', 'determine'
    ]

    # Keywords indicating coding tasks
    CODING_KEYWORDS = [
        'write code', 'write a function', 'write a class',
        'function', 'class ', 'implement', 'def ', 'return ',
        'develop', 'program', 'script', 'debug', 'fix bug',
        'refactor code', 'python code', 'javascript', 'java code',
        'programming', 'syntax error', 'compile', 'import ',
        'variable', 'loop', 'array', 'object', 'method'
    ]

    # Keywords indicating expert-level tasks
    EXPERT_KEYWORDS = [
        'machine learning', 'deep learning', 'distributed system',
        'scalability', 'security audit', 'cryptography', 'optimization',
        'concurrency', 'multi-threading', 'database design'
    ]

    @classmethod
    def analyze(cls, messages: List[Dict]) -> TaskCharacteristics:
        """
        Analyze messages to determine task characteristics.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            TaskCharacteristics
        """
        # Combine all user messages
        user_messages = [
            msg.get('content', '') if isinstance(msg, dict) else msg.content
            for msg in messages
            if (isinstance(msg, dict) and msg.get('role') == 'user') or
               (hasattr(msg, 'role') and msg.role == 'user')
        ]
        combined_text = ' '.join(user_messages).lower()

        # Detect characteristics
        is_coding = cls._contains_keywords(combined_text, cls.CODING_KEYWORDS)
        requires_reasoning = cls._contains_keywords(combined_text, cls.REASONING_KEYWORDS)
        is_expert = cls._contains_keywords(combined_text, cls.EXPERT_KEYWORDS)
        is_complex = cls._contains_keywords(combined_text, cls.COMPLEX_KEYWORDS)

        # Estimate tokens (rough estimate: ~4 chars per token)
        estimated_tokens = len(combined_text) // 4

        # Determine difficulty
        if is_expert:
            difficulty = TaskDifficulty.EXPERT
        elif is_complex or (is_coding and requires_reasoning):
            difficulty = TaskDifficulty.COMPLEX
        elif is_coding or requires_reasoning or len(combined_text) > 500:
            difficulty = TaskDifficulty.MEDIUM
        elif len(combined_text) > 100:
            difficulty = TaskDifficulty.MEDIUM
        else:
            difficulty = TaskDifficulty.SIMPLE

        return TaskCharacteristics(
            difficulty=difficulty,
            is_coding=is_coding,
            requires_reasoning=requires_reasoning,
            message_count=len(user_messages),
            estimated_tokens=estimated_tokens
        )

    @classmethod
    def _contains_keywords(cls, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        return any(keyword in text for keyword in keywords)


class ModelSelector:
    """Select the best model based on task characteristics."""

    def __init__(self, models_config: Dict):
        """
        Initialize model selector.

        Args:
            models_config: Dictionary mapping model names to ModelConfig objects
        """
        self.models_config = models_config

    def select_model(
        self,
        messages: List[Dict],
        default_model: str = "deepseek-chat"
    ) -> str:
        """
        Select the best model for the given task.

        Args:
            messages: List of chat messages
            default_model: Default model to use if auto-selection fails

        Returns:
            Selected model name
        """
        # Analyze task
        characteristics = TaskAnalyzer.analyze(messages)

        logger.info(
            f"Task analysis - Difficulty: {characteristics.difficulty.value}, "
            f"Coding: {characteristics.is_coding}, "
            f"Reasoning: {characteristics.requires_reasoning}"
        )

        # Priority 1: Expert-level tasks with reasoning -> deepseek-reasoner
        if (characteristics.difficulty == TaskDifficulty.EXPERT or
            (characteristics.difficulty == TaskDifficulty.COMPLEX and characteristics.requires_reasoning)):
            if "deepseek-reasoner" in self.models_config:
                logger.info("Using deepseek-reasoner for expert/complex reasoning task")
                return "deepseek-reasoner"

        # Priority 2: Coding tasks (medium/complex) -> deepseek-coder
        if characteristics.is_coding and not characteristics.requires_reasoning:
            if (characteristics.difficulty in [TaskDifficulty.MEDIUM, TaskDifficulty.COMPLEX] and
                "deepseek-coder" in self.models_config):
                logger.info("Using deepseek-coder for coding task")
                return "deepseek-coder"

        # Priority 3: Select by difficulty range
        selected_model = self._select_by_difficulty(characteristics, default_model)

        logger.info(f"Selected model: {selected_model}")
        return selected_model

    def _select_by_difficulty(
        self,
        characteristics: TaskCharacteristics,
        default_model: str
    ) -> str:
        """
        Select model based on difficulty level.

        Args:
            characteristics: Task characteristics
            default_model: Default model to use

        Returns:
            Model name
        """
        difficulty = characteristics.difficulty.value

        # Find best matching model
        best_model = default_model
        for model_name, model_config in self.models_config.items():
            if model_config.difficulty_range and difficulty in model_config.difficulty_range:
                # Prefer reasoner for expert tasks
                if difficulty == "expert" and "reasoner" in model_name:
                    return model_name
                # Prefer complex-capable models for complex tasks
                if difficulty == "complex" and "complex" in model_config.difficulty_range:
                    best_model = model_name

        return best_model

    def get_model_config(self, model_name: str):
        """
        Get configuration for a specific model.

        Args:
            model_name: Model name

        Returns:
            ModelConfig object or None
        """
        return self.models_config.get(model_name)
