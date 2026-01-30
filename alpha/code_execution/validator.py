"""
Code Validator Module

Provides comprehensive code validation including syntax checking,
security scanning, and quality assessment for generated code.

This module integrates with language-specific handlers to validate code
before execution in the sandbox environment.

Phase: 4.1 - Code Generation & Safe Execution
Requirements: REQ-4.1 (Code Quality Validation, Syntax Error Detection)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .languages import get_handler

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of syntax validation.

    Attributes:
        is_valid: Whether the code has valid syntax
        errors: List of syntax errors found
        warnings: List of potential issues (non-fatal)
        suggestions: List of improvement suggestions
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation of validation result"""
        status = "VALID" if self.is_valid else "INVALID"
        parts = [f"Validation: {status}"]

        if self.errors:
            parts.append(f"Errors: {len(self.errors)}")
            for error in self.errors:
                parts.append(f"  - {error}")

        if self.warnings:
            parts.append(f"Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                parts.append(f"  - {warning}")

        if self.suggestions:
            parts.append(f"Suggestions: {len(self.suggestions)}")
            for suggestion in self.suggestions:
                parts.append(f"  - {suggestion}")

        return "\n".join(parts)


@dataclass
class SecurityReport:
    """
    Security analysis report for code.

    Attributes:
        is_safe: Whether the code passes security checks
        dangerous_patterns: List of dangerous patterns detected
        risk_level: Overall risk level ("low", "medium", "high")
        recommendations: List of security recommendations
    """
    is_safe: bool
    dangerous_patterns: List[str] = field(default_factory=list)
    risk_level: str = "low"  # "low", "medium", "high"
    recommendations: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        """String representation of security report"""
        status = "SAFE" if self.is_safe else "UNSAFE"
        parts = [f"Security: {status} (Risk Level: {self.risk_level.upper()})"]

        if self.dangerous_patterns:
            parts.append(f"Dangerous Patterns Found: {len(self.dangerous_patterns)}")
            for pattern in self.dangerous_patterns:
                parts.append(f"  - {pattern}")

        if self.recommendations:
            parts.append(f"Recommendations: {len(self.recommendations)}")
            for rec in self.recommendations:
                parts.append(f"  - {rec}")

        return "\n".join(parts)


@dataclass
class QualityReport:
    """
    Code quality assessment report.

    Attributes:
        score: Quality score from 0.0 to 1.0 (higher is better)
        issues: List of quality issues found
        metrics: Dictionary of quality metrics
    """
    score: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation of quality report"""
        percentage = int(self.score * 100)
        parts = [f"Quality Score: {percentage}% ({self.score:.2f}/1.0)"]

        if self.metrics:
            parts.append("Metrics:")
            for key, value in self.metrics.items():
                parts.append(f"  - {key}: {value}")

        if self.issues:
            parts.append(f"Issues: {len(self.issues)}")
            for issue in self.issues:
                parts.append(f"  - {issue}")

        return "\n".join(parts)


class CodeValidator:
    """
    Comprehensive code validator for syntax, security, and quality checks.

    This class integrates with language-specific handlers to provide
    multi-layered validation before code execution.

    Example:
        >>> validator = CodeValidator()
        >>> result = validator.validate_syntax("print('hello')", "python")
        >>> if result.is_valid:
        ...     security = validator.check_security("print('hello')", "python")
        ...     if security.is_safe:
        ...         quality = validator.assess_quality("print('hello')", "python")
    """

    def __init__(self):
        """Initialize the code validator"""
        logger.info("Initializing CodeValidator")
        self._handlers_cache: Dict[str, Any] = {}

    def _get_handler(self, language: str):
        """
        Get language handler with caching.

        Args:
            language: Programming language name

        Returns:
            Language handler instance

        Raises:
            ValueError: If language is not supported
        """
        language_lower = language.lower()

        if language_lower not in self._handlers_cache:
            try:
                handler = get_handler(language)
                self._handlers_cache[language_lower] = handler
                logger.debug(f"Cached handler for language: {language}")
            except ValueError as e:
                logger.error(f"Failed to get handler for language {language}: {e}")
                raise

        return self._handlers_cache[language_lower]

    def validate_syntax(self, code: str, language: str) -> ValidationResult:
        """
        Validate code syntax using language-specific handler.

        This method checks for syntax errors and provides warnings
        about potential issues in the code structure.

        Args:
            code: Source code to validate
            language: Programming language (python, javascript, bash)

        Returns:
            ValidationResult with validation status and details

        Example:
            >>> validator = CodeValidator()
            >>> result = validator.validate_syntax("def foo():\\n    print('hi')", "python")
            >>> print(result.is_valid)
            True
        """
        logger.info(f"Validating {language} syntax ({len(code)} chars)")

        if not code or not code.strip():
            logger.warning("Empty code provided for validation")
            return ValidationResult(
                is_valid=False,
                errors=["Code is empty"],
                suggestions=["Provide valid code to validate"]
            )

        try:
            # Get language handler
            handler = self._get_handler(language)

            # Validate syntax using handler
            is_valid, error_msg = handler.validate_syntax(code)

            result = ValidationResult(is_valid=is_valid)

            if not is_valid and error_msg:
                result.errors.append(error_msg)
                logger.warning(f"Syntax validation failed: {error_msg}")

            # Add general warnings
            warnings = self._check_general_warnings(code, language)
            result.warnings.extend(warnings)

            # Add suggestions
            suggestions = self._generate_suggestions(code, language)
            result.suggestions.extend(suggestions)

            logger.info(f"Syntax validation complete: {'VALID' if is_valid else 'INVALID'}")
            return result

        except ValueError as e:
            # Unsupported language
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[str(e)]
            )
        except Exception as e:
            # Unexpected error during validation
            logger.error(f"Unexpected validation error: {e}", exc_info=True)
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=["Validation encountered an unexpected error"]
            )

    def check_security(self, code: str, language: str) -> SecurityReport:
        """
        Perform security analysis on code.

        This method scans for dangerous operations, evaluates risk level,
        and provides security recommendations based on detected patterns.

        Args:
            code: Source code to analyze
            language: Programming language (python, javascript, bash)

        Returns:
            SecurityReport with safety status and recommendations

        Example:
            >>> validator = CodeValidator()
            >>> report = validator.check_security("import os\\nos.system('ls')", "python")
            >>> print(report.is_safe)
            False
            >>> print(report.risk_level)
            high
        """
        logger.info(f"Performing security check on {language} code")

        if not code or not code.strip():
            logger.warning("Empty code provided for security check")
            return SecurityReport(
                is_safe=True,
                risk_level="low",
                recommendations=["No code to analyze"]
            )

        try:
            # Get language handler
            handler = self._get_handler(language)

            # Get dangerous patterns from handler
            dangerous_patterns = handler.get_dangerous_patterns()

            # Scan for dangerous patterns
            detected_patterns = []
            for pattern in dangerous_patterns:
                if pattern in code:
                    detected_patterns.append(pattern)
                    logger.warning(f"Detected dangerous pattern: {pattern}")

            # Determine risk level based on pattern severity
            risk_level = self._assess_risk_level(detected_patterns, language)

            # Determine if code is safe
            # High risk = unsafe, medium/low risk = conditional safety
            is_safe = risk_level == "low"

            # Get security recommendations from handler
            security_recs = handler.get_security_recommendations()
            recommendations = []

            # Add relevant recommendations based on detected patterns
            if detected_patterns:
                for pattern in detected_patterns:
                    # Map patterns to recommendation categories
                    if any(keyword in pattern.lower() for keyword in ['eval', 'exec', 'function']):
                        if 'eval_exec' in security_recs:
                            recommendations.append(security_recs['eval_exec'])
                    elif 'subprocess' in pattern.lower() or 'child_process' in pattern.lower():
                        if 'subprocess' in security_recs:
                            recommendations.append(security_recs['subprocess'])
                        if 'child_process' in security_recs:
                            recommendations.append(security_recs['child_process'])
                    elif any(keyword in pattern.lower() for keyword in ['file', 'open', 'fs']):
                        if 'file_access' in security_recs:
                            recommendations.append(security_recs['file_access'])
                    elif any(keyword in pattern.lower() for keyword in ['http', 'network', 'fetch']):
                        if 'network' in security_recs:
                            recommendations.append(security_recs['network'])
                    elif 'rm' in pattern.lower() or 'delete' in pattern.lower():
                        if 'rm_commands' in security_recs:
                            recommendations.append(security_recs['rm_commands'])

                # Add general recommendations
                if 'permissions' in security_recs:
                    recommendations.append(security_recs['permissions'])
            else:
                # No dangerous patterns detected, provide general best practices
                recommendations.append("Code appears safe - no dangerous patterns detected")
                if 'permissions' in security_recs:
                    recommendations.append(security_recs['permissions'])

            # Remove duplicates while preserving order
            recommendations = list(dict.fromkeys(recommendations))

            report = SecurityReport(
                is_safe=is_safe,
                dangerous_patterns=detected_patterns,
                risk_level=risk_level,
                recommendations=recommendations
            )

            logger.info(
                f"Security check complete: {'SAFE' if is_safe else 'UNSAFE'} "
                f"(Risk: {risk_level}, Patterns: {len(detected_patterns)})"
            )

            return report

        except ValueError as e:
            # Unsupported language
            logger.error(f"Security check error: {e}")
            return SecurityReport(
                is_safe=False,
                risk_level="high",
                recommendations=[str(e), "Cannot perform security check on unsupported language"]
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected security check error: {e}", exc_info=True)
            return SecurityReport(
                is_safe=False,
                risk_level="high",
                recommendations=[
                    f"Security check failed: {str(e)}",
                    "Manual review recommended due to check failure"
                ]
            )

    def assess_quality(self, code: str, language: str) -> QualityReport:
        """
        Assess code quality based on various metrics.

        This method evaluates code based on:
        - Code length (conciseness)
        - Comment ratio (documentation)
        - Error handling presence
        - Best practices adherence

        Args:
            code: Source code to assess
            language: Programming language (python, javascript, bash)

        Returns:
            QualityReport with score, metrics, and issues

        Example:
            >>> validator = CodeValidator()
            >>> report = validator.assess_quality("def add(a, b):\\n    return a + b", "python")
            >>> print(report.score)
            0.65
        """
        logger.info(f"Assessing quality of {language} code")

        if not code or not code.strip():
            logger.warning("Empty code provided for quality assessment")
            return QualityReport(
                score=0.0,
                issues=["Code is empty"],
                metrics={}
            )

        try:
            # Get language handler
            handler = self._get_handler(language)

            # Calculate metrics
            metrics = self._calculate_quality_metrics(code, language)

            # Identify issues
            issues = self._identify_quality_issues(code, language, metrics)

            # Calculate overall score (0.0 to 1.0)
            score = self._calculate_quality_score(metrics, issues)

            report = QualityReport(
                score=score,
                issues=issues,
                metrics=metrics
            )

            logger.info(f"Quality assessment complete: Score {score:.2f} ({len(issues)} issues)")

            return report

        except ValueError as e:
            # Unsupported language
            logger.error(f"Quality assessment error: {e}")
            return QualityReport(
                score=0.0,
                issues=[str(e)],
                metrics={}
            )
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected quality assessment error: {e}", exc_info=True)
            return QualityReport(
                score=0.0,
                issues=[f"Quality assessment failed: {str(e)}"],
                metrics={}
            )

    def _check_general_warnings(self, code: str, language: str) -> List[str]:
        """
        Check for general code warnings.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of warning messages
        """
        warnings = []

        # Check code length
        lines = code.split('\n')
        if len(lines) > 500:
            warnings.append("Code is very long (>500 lines) - consider splitting into functions")

        # Check for TODO/FIXME comments
        if re.search(r'\bTODO\b', code, re.IGNORECASE):
            warnings.append("Code contains TODO comments - incomplete implementation")
        if re.search(r'\bFIXME\b', code, re.IGNORECASE):
            warnings.append("Code contains FIXME comments - known issues exist")

        return warnings

    def _generate_suggestions(self, code: str, language: str) -> List[str]:
        """
        Generate improvement suggestions.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of suggestion messages
        """
        suggestions = []

        # Check for comments
        comment_chars = {
            'python': '#',
            'javascript': '//',
            'bash': '#'
        }

        comment_char = comment_chars.get(language.lower(), '#')
        comment_lines = [line for line in code.split('\n') if line.strip().startswith(comment_char)]

        if not comment_lines and len(code.split('\n')) > 10:
            suggestions.append("Consider adding comments to explain complex logic")

        # Language-specific suggestions
        if language.lower() == 'python':
            if 'def ' in code and '"""' not in code and "'''" not in code:
                suggestions.append("Consider adding docstrings to functions")

        elif language.lower() in ['javascript', 'js']:
            if 'function ' in code and '/**' not in code:
                suggestions.append("Consider adding JSDoc comments to functions")

        elif language.lower() in ['bash', 'sh']:
            if not code.strip().startswith('#!'):
                suggestions.append("Consider adding shebang line (#!/bin/bash)")

        return suggestions

    def _assess_risk_level(self, dangerous_patterns: List[str], language: str) -> str:
        """
        Assess overall risk level based on detected patterns.

        Args:
            dangerous_patterns: List of detected dangerous patterns
            language: Programming language

        Returns:
            Risk level: "low", "medium", or "high"
        """
        if not dangerous_patterns:
            return "low"

        # Define high-risk patterns
        high_risk_keywords = [
            'eval', 'exec', '__import__', 'compile',  # Code execution
            'rm -rf /', 'mkfs', 'fdisk',  # System destruction
            '> /dev/sda',  # Disk overwrite
        ]

        # Define medium-risk patterns
        medium_risk_keywords = [
            'subprocess', 'child_process', 'system',  # Command execution
            'rmtree', 'unlink', 'rm -rf',  # File deletion
            'open(', 'fs',  # File access
            'chmod 777', 'curl | bash',  # Security issues
        ]

        # Check for high-risk patterns
        for pattern in dangerous_patterns:
            if any(keyword in pattern.lower() for keyword in high_risk_keywords):
                return "high"

        # Check for medium-risk patterns
        for pattern in dangerous_patterns:
            if any(keyword in pattern.lower() for keyword in medium_risk_keywords):
                return "medium"

        # Default to medium if patterns exist but not categorized as high
        return "medium" if dangerous_patterns else "low"

    def _calculate_quality_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """
        Calculate various code quality metrics.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Dictionary of metrics
        """
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Basic metrics
        total_lines = len(lines)
        code_lines = len(non_empty_lines)

        # Comment detection
        comment_chars = {
            'python': '#',
            'javascript': '//',
            'bash': '#'
        }
        comment_char = comment_chars.get(language.lower(), '#')
        comment_lines = [line for line in lines if line.strip().startswith(comment_char)]

        # Calculate comment ratio
        comment_ratio = len(comment_lines) / code_lines if code_lines > 0 else 0.0

        # Check for error handling
        error_handling_keywords = {
            'python': ['try', 'except', 'raise', 'assert'],
            'javascript': ['try', 'catch', 'throw'],
            'bash': ['set -e', 'trap', '||', 'if [']
        }

        has_error_handling = False
        keywords = error_handling_keywords.get(language.lower(), [])
        for keyword in keywords:
            if keyword in code:
                has_error_handling = True
                break

        # Check for documentation
        has_documentation = False
        if language.lower() == 'python':
            has_documentation = '"""' in code or "'''" in code
        elif language.lower() in ['javascript', 'js']:
            has_documentation = '/**' in code
        elif language.lower() in ['bash', 'sh']:
            has_documentation = code.strip().startswith('#!')

        # Average line length
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0

        return {
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': len(comment_lines),
            'comment_ratio': round(comment_ratio, 2),
            'has_error_handling': has_error_handling,
            'has_documentation': has_documentation,
            'avg_line_length': round(avg_line_length, 1),
        }

    def _identify_quality_issues(
        self,
        code: str,
        language: str,
        metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Identify code quality issues based on metrics.

        Args:
            code: Source code
            language: Programming language
            metrics: Quality metrics dictionary

        Returns:
            List of quality issues
        """
        issues = []

        # Check code length
        if metrics['code_lines'] > 200:
            issues.append("Code is very long - consider refactoring into smaller functions")
        elif metrics['code_lines'] < 5:
            issues.append("Code is very short - ensure it implements required functionality")

        # Check comment ratio
        if metrics['comment_ratio'] < 0.1 and metrics['code_lines'] > 20:
            issues.append("Low comment ratio - code may be hard to understand")
        elif metrics['comment_ratio'] > 0.5:
            issues.append("Very high comment ratio - code may be overly commented")

        # Check error handling
        if not metrics['has_error_handling'] and metrics['code_lines'] > 15:
            issues.append("No error handling detected - consider adding try/catch or validation")

        # Check documentation
        if not metrics['has_documentation'] and metrics['code_lines'] > 30:
            issues.append("No documentation detected - consider adding docstrings or comments")

        # Check line length
        if metrics['avg_line_length'] > 120:
            issues.append("Long average line length - consider breaking lines for readability")

        return issues

    def _calculate_quality_score(
        self,
        metrics: Dict[str, Any],
        issues: List[str]
    ) -> float:
        """
        Calculate overall quality score from metrics and issues.

        Score calculation:
        - Start with 1.0 (perfect)
        - Subtract points for each issue
        - Add bonus points for good practices

        Args:
            metrics: Quality metrics dictionary
            issues: List of quality issues

        Returns:
            Quality score from 0.0 to 1.0
        """
        score = 0.5  # Start with base score

        # Deduct points for issues (each issue -0.1, max -0.3)
        issue_penalty = min(len(issues) * 0.1, 0.3)
        score -= issue_penalty

        # Add points for good practices
        if metrics['has_error_handling']:
            score += 0.15

        if metrics['has_documentation']:
            score += 0.15

        # Good comment ratio (0.1 to 0.3 is ideal)
        comment_ratio = metrics['comment_ratio']
        if 0.1 <= comment_ratio <= 0.3:
            score += 0.1

        # Reasonable code length (20-100 lines is good)
        code_lines = metrics['code_lines']
        if 20 <= code_lines <= 100:
            score += 0.1
        elif 10 <= code_lines <= 150:
            score += 0.05

        # Reasonable line length (60-100 chars average)
        avg_length = metrics['avg_line_length']
        if 60 <= avg_length <= 100:
            score += 0.05

        # Clamp score between 0.0 and 1.0
        return max(0.0, min(1.0, score))
