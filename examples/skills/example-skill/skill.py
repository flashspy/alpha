"""
Example Skill - Demonstrates the Agent Skill system.

This skill provides simple text processing capabilities.
"""

import logging
from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


class ExampleSkill(AgentSkill):
    """
    Example skill that demonstrates how to create an Agent Skill.

    Features:
    - Text transformation (uppercase, lowercase, reverse)
    - Character counting
    - Word counting
    """

    async def initialize(self) -> bool:
        """Initialize the skill."""
        logger.info(f"Initializing {self.metadata.name}")
        # Add any initialization logic here (load models, connect to services, etc.)
        return True

    async def execute(self, operation: str, text: str, **kwargs) -> SkillResult:
        """
        Execute the skill.

        Args:
            operation: Operation to perform (uppercase, lowercase, reverse, count_chars, count_words)
            text: Input text
            **kwargs: Additional parameters

        Returns:
            Skill execution result
        """
        self.validate_params(["operation", "text"], {"operation": operation, "text": text})

        logger.info(f"Executing {operation} on text: '{text[:50]}...'")

        try:
            if operation == "uppercase":
                result_text = text.upper()
                return SkillResult(
                    success=True,
                    output={"original": text, "result": result_text, "operation": operation}
                )

            elif operation == "lowercase":
                result_text = text.lower()
                return SkillResult(
                    success=True,
                    output={"original": text, "result": result_text, "operation": operation}
                )

            elif operation == "reverse":
                result_text = text[::-1]
                return SkillResult(
                    success=True,
                    output={"original": text, "result": result_text, "operation": operation}
                )

            elif operation == "count_chars":
                char_count = len(text)
                return SkillResult(
                    success=True,
                    output={"text": text, "char_count": char_count, "operation": operation}
                )

            elif operation == "count_words":
                word_count = len(text.split())
                return SkillResult(
                    success=True,
                    output={"text": text, "word_count": word_count, "operation": operation}
                )

            else:
                return SkillResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"Error executing skill: {e}", exc_info=True)
            return SkillResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up {self.metadata.name}")
        # Add any cleanup logic here

    def get_schema(self):
        """Get parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["uppercase", "lowercase", "reverse", "count_chars", "count_words"],
                    "description": "Operation to perform"
                },
                "text": {
                    "type": "string",
                    "description": "Input text"
                }
            },
            "required": ["operation", "text"]
        }
