"""
Text Processing Skill

Advanced text processing and transformation capabilities.
"""

import re
import logging
from typing import List, Dict, Any
from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


class TextProcessingSkill(AgentSkill):
    """
    Text processing skill with various transformation operations.

    Operations:
    - uppercase/lowercase/titlecase/capitalize
    - reverse, trim, strip
    - split, join
    - replace, remove
    - count (words, chars, lines)
    - extract (emails, urls, numbers)
    - truncate, pad
    """

    async def initialize(self) -> bool:
        """Initialize the skill."""
        logger.info(f"Initializing {self.metadata.name}")
        return True

    async def execute(self, operation: str, text: str = "", **kwargs) -> SkillResult:
        """
        Execute text processing operation.

        Args:
            operation: Operation to perform
            text: Input text
            **kwargs: Operation-specific parameters

        Returns:
            Skill execution result
        """
        self.validate_params(["operation"], {"operation": operation})

        logger.info(f"Executing {operation} on text")

        try:
            # Case transformations
            if operation == "uppercase":
                return SkillResult(success=True, output={"result": text.upper()})

            elif operation == "lowercase":
                return SkillResult(success=True, output={"result": text.lower()})

            elif operation == "titlecase":
                return SkillResult(success=True, output={"result": text.title()})

            elif operation == "capitalize":
                return SkillResult(success=True, output={"result": text.capitalize()})

            # String operations
            elif operation == "reverse":
                return SkillResult(success=True, output={"result": text[::-1]})

            elif operation == "trim":
                return SkillResult(success=True, output={"result": text.strip()})

            elif operation == "strip":
                chars = kwargs.get("chars", None)
                return SkillResult(success=True, output={"result": text.strip(chars)})

            # Split and join
            elif operation == "split":
                delimiter = kwargs.get("delimiter", " ")
                parts = text.split(delimiter)
                return SkillResult(success=True, output={"result": parts, "count": len(parts)})

            elif operation == "join":
                parts = kwargs.get("parts", [])
                delimiter = kwargs.get("delimiter", " ")
                result = delimiter.join(parts)
                return SkillResult(success=True, output={"result": result})

            # Replace and remove
            elif operation == "replace":
                old = kwargs.get("old", "")
                new = kwargs.get("new", "")
                count = kwargs.get("count", -1)
                result = text.replace(old, new, count)
                return SkillResult(success=True, output={"result": result})

            elif operation == "remove":
                pattern = kwargs.get("pattern", "")
                result = text.replace(pattern, "")
                return SkillResult(success=True, output={"result": result})

            # Counting
            elif operation == "count_words":
                words = text.split()
                return SkillResult(success=True, output={"count": len(words), "words": words})

            elif operation == "count_chars":
                return SkillResult(success=True, output={"count": len(text)})

            elif operation == "count_lines":
                lines = text.split('\n')
                return SkillResult(success=True, output={"count": len(lines)})

            # Extraction
            elif operation == "extract_emails":
                pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(pattern, text)
                return SkillResult(success=True, output={"emails": emails, "count": len(emails)})

            elif operation == "extract_urls":
                pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
                urls = re.findall(pattern, text)
                return SkillResult(success=True, output={"urls": urls, "count": len(urls)})

            elif operation == "extract_numbers":
                pattern = r'-?\d+\.?\d*'
                numbers = re.findall(pattern, text)
                return SkillResult(success=True, output={"numbers": numbers, "count": len(numbers)})

            # Formatting
            elif operation == "truncate":
                max_length = kwargs.get("max_length", 100)
                suffix = kwargs.get("suffix", "...")
                if len(text) <= max_length:
                    result = text
                else:
                    result = text[:max_length - len(suffix)] + suffix
                return SkillResult(success=True, output={"result": result})

            elif operation == "pad_left":
                width = kwargs.get("width", 20)
                fillchar = kwargs.get("fillchar", " ")
                result = text.rjust(width, fillchar)
                return SkillResult(success=True, output={"result": result})

            elif operation == "pad_right":
                width = kwargs.get("width", 20)
                fillchar = kwargs.get("fillchar", " ")
                result = text.ljust(width, fillchar)
                return SkillResult(success=True, output={"result": result})

            else:
                return SkillResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"Error executing text processing: {e}", exc_info=True)
            return SkillResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up {self.metadata.name}")

    def get_schema(self):
        """Get parameter schema."""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "uppercase", "lowercase", "titlecase", "capitalize",
                        "reverse", "trim", "strip",
                        "split", "join", "replace", "remove",
                        "count_words", "count_chars", "count_lines",
                        "extract_emails", "extract_urls", "extract_numbers",
                        "truncate", "pad_left", "pad_right"
                    ],
                    "description": "Operation to perform"
                },
                "text": {
                    "type": "string",
                    "description": "Input text"
                }
            },
            "required": ["operation"]
        }
