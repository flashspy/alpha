"""
Code Execution Module

This module provides autonomous code generation and safe execution capabilities for Alpha.
It enables Alpha to write, validate, and execute custom scripts in Python, JavaScript, and Bash
when existing tools are insufficient.

Components:
- CodeGenerator: LLM-powered code generation with context awareness
- CodeValidator: Syntax and security validation
- SandboxManager: Docker-based isolated execution environment
- CodeExecutor: Orchestration of generation, validation, and execution

Phase: 4.1 - Code Generation & Safe Execution
Requirements: REQ-4.1, REQ-4.2, REQ-4.3
"""

from .generator import CodeGenerator, CodeGenerationError, GeneratedCode
from .validator import CodeValidator, ValidationResult, SecurityReport, QualityReport
from .sandbox import SandboxManager, SandboxConfig, ExecutionResult
from .executor import CodeExecutor, ExecutionOptions, ExecutionError, UserRejectionError

__all__ = [
    # Day 1: Code Generation Engine (✓ Implemented)
    "CodeGenerator",
    "CodeGenerationError",
    "GeneratedCode",
    # Day 2: Code Validation & Quality (✓ Implemented)
    "CodeValidator",
    "ValidationResult",
    "SecurityReport",
    "QualityReport",
    # Day 3: Safe Execution Sandbox (✓ Implemented)
    "SandboxManager",
    "SandboxConfig",
    "ExecutionResult",
    # Day 4: Code Execution Coordinator (✓ Implemented)
    "CodeExecutor",
    "ExecutionOptions",
    "ExecutionError",
    "UserRejectionError",
]

__version__ = "0.7.0"
__author__ = "Alpha Development Team"
