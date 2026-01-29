"""
Data Analyzer Skill

Statistical analysis and data aggregation.
"""

import logging
import statistics
from typing import List, Dict, Any
from alpha.skills.base import AgentSkill, SkillMetadata, SkillResult

logger = logging.getLogger(__name__)


class DataAnalyzerSkill(AgentSkill):
    """
    Data analysis skill with statistical operations.

    Operations:
    - mean, median, mode
    - min, max, range
    - sum, count
    - variance, stdev (standard deviation)
    - percentile, quartiles
    - group_by, aggregate
    - sort, filter
    """

    async def initialize(self) -> bool:
        """Initialize the skill."""
        logger.info(f"Initializing {self.metadata.name}")
        return True

    async def execute(self, operation: str, data: List = None, **kwargs) -> SkillResult:
        """
        Execute data analysis operation.

        Args:
            operation: Operation to perform
            data: Input data (list of numbers or objects)
            **kwargs: Operation-specific parameters

        Returns:
            Skill execution result
        """
        self.validate_params(["operation"], {"operation": operation})

        if data is None:
            data = []

        logger.info(f"Executing {operation} on {len(data)} items")

        try:
            # Basic statistics
            if operation == "mean":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                result = statistics.mean(data)
                return SkillResult(success=True, output={"mean": result, "count": len(data)})

            elif operation == "median":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                result = statistics.median(data)
                return SkillResult(success=True, output={"median": result, "count": len(data)})

            elif operation == "mode":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                try:
                    result = statistics.mode(data)
                    return SkillResult(success=True, output={"mode": result, "count": len(data)})
                except statistics.StatisticsError:
                    return SkillResult(success=False, output=None, error="No unique mode")

            # Min/Max/Range
            elif operation == "min":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                result = min(data)
                return SkillResult(success=True, output={"min": result})

            elif operation == "max":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                result = max(data)
                return SkillResult(success=True, output={"max": result})

            elif operation == "range":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                min_val = min(data)
                max_val = max(data)
                range_val = max_val - min_val
                return SkillResult(
                    success=True,
                    output={"min": min_val, "max": max_val, "range": range_val}
                )

            # Sum and count
            elif operation == "sum":
                result = sum(data)
                return SkillResult(success=True, output={"sum": result, "count": len(data)})

            elif operation == "count":
                return SkillResult(success=True, output={"count": len(data)})

            # Variance and standard deviation
            elif operation == "variance":
                if len(data) < 2:
                    return SkillResult(success=False, output=None, error="Need at least 2 data points")
                result = statistics.variance(data)
                return SkillResult(success=True, output={"variance": result, "count": len(data)})

            elif operation == "stdev":
                if len(data) < 2:
                    return SkillResult(success=False, output=None, error="Need at least 2 data points")
                result = statistics.stdev(data)
                return SkillResult(success=True, output={"stdev": result, "count": len(data)})

            # Percentiles and quartiles
            elif operation == "percentile":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                p = kwargs.get("p", 50)  # Default to median
                sorted_data = sorted(data)
                k = (len(sorted_data) - 1) * (p / 100)
                f = int(k)
                c = f + 1
                if c >= len(sorted_data):
                    result = sorted_data[-1]
                else:
                    d0 = sorted_data[f] * (c - k)
                    d1 = sorted_data[c] * (k - f)
                    result = d0 + d1
                return SkillResult(
                    success=True,
                    output={"percentile": p, "value": result}
                )

            elif operation == "quartiles":
                if not data:
                    return SkillResult(success=False, output=None, error="Empty dataset")
                sorted_data = sorted(data)
                q1 = statistics.median(sorted_data[:len(sorted_data)//2])
                q2 = statistics.median(sorted_data)
                q3 = statistics.median(sorted_data[(len(sorted_data)+1)//2:])
                return SkillResult(
                    success=True,
                    output={"q1": q1, "q2": q2, "q3": q3}
                )

            # Aggregation operations
            elif operation == "group_by":
                key = kwargs.get("key", "")
                if not key or not isinstance(data[0], dict):
                    return SkillResult(success=False, output=None, error="Invalid data or missing key")

                groups = {}
                for item in data:
                    group_key = item.get(key)
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(item)

                return SkillResult(
                    success=True,
                    output={"groups": groups, "group_count": len(groups)}
                )

            elif operation == "aggregate":
                agg_func = kwargs.get("func", "count")  # count, sum, avg, min, max
                key = kwargs.get("key", "")

                if agg_func == "count":
                    result = len(data)
                elif key and isinstance(data[0], dict):
                    values = [item.get(key, 0) for item in data if isinstance(item.get(key), (int, float))]
                    if agg_func == "sum":
                        result = sum(values)
                    elif agg_func == "avg":
                        result = sum(values) / len(values) if values else 0
                    elif agg_func == "min":
                        result = min(values) if values else None
                    elif agg_func == "max":
                        result = max(values) if values else None
                    else:
                        return SkillResult(success=False, output=None, error=f"Unknown function: {agg_func}")
                else:
                    return SkillResult(success=False, output=None, error="Invalid data or missing key")

                return SkillResult(
                    success=True,
                    output={"function": agg_func, "result": result}
                )

            # Sort and filter
            elif operation == "sort":
                key = kwargs.get("key", None)
                reverse = kwargs.get("reverse", False)

                if key and isinstance(data[0], dict):
                    sorted_data = sorted(data, key=lambda x: x.get(key, 0), reverse=reverse)
                else:
                    sorted_data = sorted(data, reverse=reverse)

                return SkillResult(success=True, output={"result": sorted_data})

            elif operation == "filter":
                condition = kwargs.get("condition", "")
                key = kwargs.get("key", "")
                value = kwargs.get("value", "")

                if not condition or not key:
                    return SkillResult(success=False, output=None, error="Missing condition or key")

                filtered = []
                for item in data:
                    if isinstance(item, dict):
                        item_value = item.get(key)
                        if condition == "eq" and item_value == value:
                            filtered.append(item)
                        elif condition == "ne" and item_value != value:
                            filtered.append(item)
                        elif condition == "gt" and item_value > value:
                            filtered.append(item)
                        elif condition == "lt" and item_value < value:
                            filtered.append(item)
                        elif condition == "gte" and item_value >= value:
                            filtered.append(item)
                        elif condition == "lte" and item_value <= value:
                            filtered.append(item)

                return SkillResult(
                    success=True,
                    output={"result": filtered, "count": len(filtered)}
                )

            # Statistics summary
            elif operation == "summary":
                if not data or not all(isinstance(x, (int, float)) for x in data):
                    return SkillResult(success=False, output=None, error="Invalid numeric dataset")

                summary = {
                    "count": len(data),
                    "sum": sum(data),
                    "mean": statistics.mean(data),
                    "median": statistics.median(data),
                    "min": min(data),
                    "max": max(data),
                    "range": max(data) - min(data),
                }

                if len(data) >= 2:
                    summary["stdev"] = statistics.stdev(data)
                    summary["variance"] = statistics.variance(data)

                return SkillResult(success=True, output=summary)

            else:
                return SkillResult(
                    success=False,
                    output=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"Error executing data analysis: {e}", exc_info=True)
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
                        "mean", "median", "mode",
                        "min", "max", "range",
                        "sum", "count",
                        "variance", "stdev",
                        "percentile", "quartiles",
                        "group_by", "aggregate",
                        "sort", "filter",
                        "summary"
                    ],
                    "description": "Operation to perform"
                },
                "data": {
                    "type": "array",
                    "description": "Input data"
                }
            },
            "required": ["operation", "data"]
        }
