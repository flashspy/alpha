"""
Workflow Orchestration System - Complete Workflow Management

This module provides comprehensive workflow management including:
- Core workflow components (definition, builder, executor, library)
- Proactive integration (pattern detection, suggestions, optimization)
"""

# Core workflow components (REQ-6.2.1 to 6.2.4)
from .definition import WorkflowDefinition
from .schema import WorkflowSchema
from .builder import WorkflowBuilder
from .executor import WorkflowExecutor
from .library import WorkflowLibrary

# Proactive integration components (REQ-6.2.5)
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
    # Core components
    "WorkflowDefinition",
    "WorkflowSchema",
    "WorkflowBuilder",
    "WorkflowExecutor",
    "WorkflowLibrary",
    # Proactive components
    "WorkflowPattern",
    "WorkflowPatternDetector",
    "WorkflowSuggestion",
    "WorkflowSuggestionGenerator",
    "WorkflowOptimization",
    "WorkflowOptimizer",
]
