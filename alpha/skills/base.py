"""
Agent Skill Base Classes

Defines the core abstractions for Agent Skills.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SkillMetadata:
    """Skill metadata."""
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    python_version: str = ">=3.8"
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SkillResult:
    """Skill execution result."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0


class AgentSkill(ABC):
    """
    Abstract base class for Agent Skills.

    An Agent Skill is a self-contained unit of functionality that can be
    dynamically discovered, installed, and executed by Alpha.

    Skills are similar to Tools but:
    - Can be dynamically loaded from external sources
    - Have metadata and versioning
    - Support dependency management
    - Can be sandboxed for security
    """

    def __init__(self, metadata: SkillMetadata):
        self.metadata = metadata
        self.installed_at: Optional[Path] = None
        self.initialized: bool = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the skill.

        Called once after installation/loading.
        Use this to set up resources, load models, etc.

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            Skill execution result
        """
        pass

    @abstractmethod
    async def cleanup(self):
        """
        Clean up resources.

        Called when skill is unloaded or system shuts down.
        """
        pass

    def validate_params(self, required: List[str], provided: Dict[str, Any]):
        """Validate required parameters."""
        missing = [p for p in required if p not in provided]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

    def get_schema(self) -> Dict[str, Any]:
        """
        Get skill parameter schema.

        Returns JSON schema for skill parameters.
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def __repr__(self) -> str:
        return f"<AgentSkill: {self.metadata.name} v{self.metadata.version}>"
