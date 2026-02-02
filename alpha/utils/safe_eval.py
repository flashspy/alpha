"""
Safe Expression Evaluation Module

Provides secure alternatives to eval() for evaluating:
1. Boolean conditions (for workflow executor)
2. Mathematical expressions (for calculator tool)

Security features:
- AST-based parsing and validation
- Whitelist of allowed operations
- No access to builtins or system functions
- Input sanitization and validation
"""

import ast
import operator
import math
from typing import Any, Dict, Union


class SafeExpressionEvaluator:
    """
    Safe evaluator for boolean conditions and mathematical expressions.
    Uses AST parsing instead of eval() to prevent code injection.
    """

    # Allowed operators for mathematical expressions
    MATH_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Allowed comparison operators for conditions
    COMPARISON_OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    # Allowed boolean operators
    BOOLEAN_OPERATORS = {
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
        ast.Not: operator.not_,
    }

    # Safe mathematical functions
    SAFE_MATH_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow,
        # Math module functions
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        'sqrt': math.sqrt,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'ceil': math.ceil,
        'floor': math.floor,
        'factorial': math.factorial,
        'radians': math.radians,
        'degrees': math.degrees,
    }

    # Safe constants
    SAFE_CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf,
    }

    def __init__(self):
        """Initialize the safe evaluator."""
        self.allowed_names = set(self.SAFE_MATH_FUNCTIONS.keys()) | set(
            self.SAFE_CONSTANTS.keys()
        )

    def evaluate_condition(
        self, condition: str, context: Dict[str, Any] = None
    ) -> bool:
        """
        Safely evaluate a boolean condition.

        Args:
            condition: Boolean condition string (e.g., "x > 5 and y < 10")
            context: Dictionary of variable names and values

        Returns:
            Boolean result

        Raises:
            ValueError: If condition is invalid or unsafe

        Examples:
            >>> evaluator = SafeExpressionEvaluator()
            >>> evaluator.evaluate_condition("5 > 3")
            True
            >>> evaluator.evaluate_condition("x > 5", {"x": 10})
            True
        """
        if context is None:
            context = {}

        try:
            # Parse the condition
            tree = ast.parse(condition, mode='eval')
            # Evaluate the AST
            result = self._eval_node(tree.body, context)
            return bool(result)
        except Exception as e:
            raise ValueError(f"Invalid condition '{condition}': {str(e)}")

    def evaluate_math(
        self, expression: str, context: Dict[str, Any] = None
    ) -> float:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: Mathematical expression string (e.g., "2 + 3 * 4")
            context: Dictionary of variable names and values

        Returns:
            Numerical result as float

        Raises:
            ValueError: If expression is invalid or unsafe

        Examples:
            >>> evaluator = SafeExpressionEvaluator()
            >>> evaluator.evaluate_math("2 + 3 * 4")
            14.0
            >>> evaluator.evaluate_math("sqrt(16)")
            4.0
        """
        if context is None:
            context = {}

        # Add constants to context
        full_context = {**self.SAFE_CONSTANTS, **context}

        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            # Evaluate the AST
            result = self._eval_node(tree.body, full_context)
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression '{expression}': {str(e)}")

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        Recursively evaluate an AST node.

        Args:
            node: AST node to evaluate
            context: Variable context

        Returns:
            Evaluation result

        Raises:
            ValueError: If node type is not allowed
        """
        # Literal values (numbers, strings, booleans)
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # For Python 3.7 compatibility
            return node.n
        elif isinstance(node, ast.Str):  # For Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.NameConstant):  # For Python 3.7 compatibility
            return node.value

        # Variable lookup
        elif isinstance(node, ast.Name):
            name = node.id
            if name in context:
                return context[name]
            elif name in self.SAFE_CONSTANTS:
                return self.SAFE_CONSTANTS[name]
            else:
                raise ValueError(f"Undefined variable: {name}")

        # Binary operations (e.g., 2 + 3)
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.MATH_OPERATORS:
                raise ValueError(f"Operator not allowed: {op_type.__name__}")
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            return self.MATH_OPERATORS[op_type](left, right)

        # Unary operations (e.g., -5)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type == ast.Not:
                operand = self._eval_node(node.operand, context)
                return not operand
            elif op_type in self.MATH_OPERATORS:
                operand = self._eval_node(node.operand, context)
                return self.MATH_OPERATORS[op_type](operand)
            else:
                raise ValueError(f"Unary operator not allowed: {op_type.__name__}")

        # Comparison operations (e.g., x > 5)
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                op_type = type(op)
                if op_type not in self.COMPARISON_OPERATORS:
                    raise ValueError(f"Comparison operator not allowed: {op_type.__name__}")
                right = self._eval_node(comparator, context)
                if not self.COMPARISON_OPERATORS[op_type](left, right):
                    return False
                left = right
            return True

        # Boolean operations (e.g., x and y)
        elif isinstance(node, ast.BoolOp):
            op_type = type(node.op)
            if op_type not in self.BOOLEAN_OPERATORS:
                raise ValueError(f"Boolean operator not allowed: {op_type.__name__}")

            # Evaluate with short-circuit logic
            if op_type == ast.And:
                for value in node.values:
                    result = self._eval_node(value, context)
                    if not result:
                        return False
                return True
            elif op_type == ast.Or:
                for value in node.values:
                    result = self._eval_node(value, context)
                    if result:
                        return True
                return False

        # Function calls (e.g., sqrt(16))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed")

            func_name = node.func.id
            if func_name not in self.SAFE_MATH_FUNCTIONS:
                raise ValueError(f"Function not allowed: {func_name}")

            # Evaluate arguments
            args = [self._eval_node(arg, context) for arg in node.args]

            # Call the function
            func = self.SAFE_MATH_FUNCTIONS[func_name]
            return func(*args)

        # List/Tuple (for functions like min/max/sum)
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [self._eval_node(elt, context) for elt in node.elts]

        else:
            raise ValueError(f"Node type not allowed: {type(node).__name__}")


# Singleton instance for convenience
_default_evaluator = SafeExpressionEvaluator()


def safe_eval_condition(condition: str, context: Dict[str, Any] = None) -> bool:
    """
    Convenience function to safely evaluate a boolean condition.

    Args:
        condition: Boolean condition string
        context: Dictionary of variable names and values

    Returns:
        Boolean result
    """
    return _default_evaluator.evaluate_condition(condition, context)


def safe_eval_math(expression: str, context: Dict[str, Any] = None) -> float:
    """
    Convenience function to safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression string
        context: Dictionary of variable names and values

    Returns:
        Numerical result as float
    """
    return _default_evaluator.evaluate_math(expression, context)
