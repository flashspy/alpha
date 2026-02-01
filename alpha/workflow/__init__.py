"""
Workflow Orchestration System - Proactive Integration Components

This module provides proactive workflow pattern detection, suggestion generation,
and optimization capabilities.
"""

from .pattern_detector import (
    WorkflowPattern,
    WorkflowPatternDetector
)
from .suggestion_generator import (
    WorkflowSuggestion,
    WorkflowSuggestionGenerator
)
from .optimizer import (
    WorkflowOptimization,
    WorkflowOptimizer
)

__all__ = [
    "WorkflowPattern",
    "WorkflowPatternDetector",
    "WorkflowSuggestion",
    "WorkflowSuggestionGenerator",
    "WorkflowOptimization",
    "WorkflowOptimizer",
]
