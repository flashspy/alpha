"""
JSON Processor Skill

JSON parsing, formatting, validation and transformation.
"""

import json
import logging
from typing import Any, Dict
from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


class JSONProcessorSkill(AgentSkill):
    """
    JSON processing skill.

    Operations:
    - parse: Parse JSON string to object
    - stringify: Convert object to JSON string
    - format: Pretty-print JSON
    - minify: Minify JSON (remove whitespace)
    - validate: Validate JSON syntax
    - extract: Extract value by path (e.g., "user.name")
    - merge: Merge multiple JSON objects
    - filter: Filter JSON by keys
    """

    async def initialize(self) -> bool:
        """Initialize the skill."""
        logger.info(f"Initializing {self.metadata.name}")
        return True

    async def execute(self, operation: str, **kwargs) -> SkillResult:
        """
        Execute JSON processing operation.

        Args:
            operation: Operation to perform
            **kwargs: Operation-specific parameters

        Returns:
            Skill execution result
        """
        self.validate_params(["operation"], {"operation": operation})

        logger.info(f"Executing JSON {operation}")

        try:
            # Parse JSON string to object
            if operation == "parse":
                json_str = kwargs.get("json_str", "")
                try:
                    result = json.loads(json_str)
                    return SkillResult(
                        success=True,
                        output={"result": result, "type": type(result).__name__}
                    )
                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Invalid JSON: {str(e)}"
                    )

            # Convert object to JSON string
            elif operation == "stringify":
                obj = kwargs.get("object", {})
                indent = kwargs.get("indent", None)
                result = json.dumps(obj, indent=indent, ensure_ascii=False)
                return SkillResult(success=True, output={"result": result})

            # Pretty-print JSON
            elif operation == "format":
                json_str = kwargs.get("json_str", "")
                indent = kwargs.get("indent", 2)
                try:
                    obj = json.loads(json_str)
                    result = json.dumps(obj, indent=indent, ensure_ascii=False)
                    return SkillResult(success=True, output={"result": result})
                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Invalid JSON: {str(e)}"
                    )

            # Minify JSON
            elif operation == "minify":
                json_str = kwargs.get("json_str", "")
                try:
                    obj = json.loads(json_str)
                    result = json.dumps(obj, separators=(',', ':'), ensure_ascii=False)
                    return SkillResult(success=True, output={"result": result})
                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Invalid JSON: {str(e)}"
                    )

            # Validate JSON
            elif operation == "validate":
                json_str = kwargs.get("json_str", "")
                try:
                    json.loads(json_str)
                    return SkillResult(
                        success=True,
                        output={"valid": True, "message": "Valid JSON"}
                    )
                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=True,
                        output={
                            "valid": False,
                            "error": str(e),
                            "line": e.lineno,
                            "column": e.colno
                        }
                    )

            # Extract value by path
            elif operation == "extract":
                json_str = kwargs.get("json_str", "")
                path = kwargs.get("path", "")

                try:
                    obj = json.loads(json_str)
                    keys = path.split('.')
                    value = obj

                    for key in keys:
                        if isinstance(value, dict):
                            value = value.get(key)
                        elif isinstance(value, list):
                            try:
                                index = int(key)
                                value = value[index]
                            except (ValueError, IndexError):
                                value = None
                        else:
                            value = None

                        if value is None:
                            break

                    return SkillResult(
                        success=True,
                        output={"result": value, "path": path}
                    )

                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Invalid JSON: {str(e)}"
                    )

            # Merge JSON objects
            elif operation == "merge":
                json_objects = kwargs.get("json_objects", [])

                try:
                    result = {}
                    for json_str in json_objects:
                        obj = json.loads(json_str) if isinstance(json_str, str) else json_str
                        if isinstance(obj, dict):
                            result.update(obj)

                    return SkillResult(
                        success=True,
                        output={"result": result, "count": len(json_objects)}
                    )

                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Invalid JSON: {str(e)}"
                    )

            # Filter JSON by keys
            elif operation == "filter":
                json_str = kwargs.get("json_str", "")
                keys = kwargs.get("keys", [])

                try:
                    obj = json.loads(json_str)

                    if isinstance(obj, dict):
                        result = {k: v for k, v in obj.items() if k in keys}
                    else:
                        result = obj

                    return SkillResult(
                        success=True,
                        output={"result": result, "filtered_keys": keys}
                    )

                except json.JSONDecodeError as e:
                    return SkillResult(
                        success=False,
                        output=None,
                        error=f"Invalid JSON: {str(e)}"
                    )

            else:
                return SkillResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"Error executing JSON processing: {e}", exc_info=True)
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
                        "parse", "stringify", "format", "minify",
                        "validate", "extract", "merge", "filter"
                    ],
                    "description": "Operation to perform"
                }
            },
            "required": ["operation"]
        }
