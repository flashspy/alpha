"""
Code Generator

LLM-powered code generation engine that creates executable code from task descriptions.
Supports context-aware generation, test generation, and iterative refinement.

Phase: 4.1 - REQ-4.1
Author: Alpha Development Team
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


class CodeGenerationError(Exception):
    """Raised when code generation fails"""
    pass


@dataclass
class GeneratedCode:
    """Container for generated code and metadata"""
    code: str
    language: str
    description: str
    tests: Optional[str] = None
    dependencies: Optional[List[str]] = None
    complexity: str = "simple"  # simple, moderate, complex
    estimated_runtime: Optional[int] = None  # seconds


class CodeGenerator:
    """
    LLM-powered code generation engine.

    Generates executable code from natural language task descriptions
    using Alpha's LLM service with context awareness and quality validation.
    """

    def __init__(self, llm_service):
        """
        Initialize code generator.

        Args:
            llm_service: Alpha's LLM service instance for code generation
        """
        self.llm_service = llm_service
        self.generation_count = 0
        self.success_count = 0

        logger.info("CodeGenerator initialized")

    async def generate_code(
        self,
        task: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate code from task description.

        Args:
            task: Natural language description of what the code should do
            language: Target programming language (python, javascript, bash)
            context: Optional context information (variables, data, constraints)

        Returns:
            GeneratedCode object with code and metadata

        Raises:
            CodeGenerationError: If generation fails
        """
        logger.info(f"Generating {language} code for task: {task[:100]}...")

        try:
            # Build generation prompt
            prompt = self._build_generation_prompt(task, language, context)

            # Use LLM to generate code
            response = await self._call_llm_for_generation(prompt, language)

            # Parse and validate response
            generated = self._parse_generation_response(response, language)

            self.generation_count += 1
            self.success_count += 1

            logger.info(f"Successfully generated {len(generated.code)} characters of {language} code")
            return generated

        except Exception as e:
            self.generation_count += 1
            logger.error(f"Code generation failed: {str(e)}")
            raise CodeGenerationError(f"Failed to generate code: {str(e)}") from e

    async def generate_with_tests(
        self,
        task: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None
    ) -> GeneratedCode:
        """
        Generate code with accompanying test cases.

        Args:
            task: Task description
            language: Target language
            context: Optional context

        Returns:
            GeneratedCode with both code and tests
        """
        logger.info(f"Generating {language} code with tests for task: {task[:100]}...")

        try:
            # Build prompt that requests both code and tests
            prompt = self._build_generation_with_tests_prompt(task, language, context)

            # Generate code and tests
            response = await self._call_llm_for_generation(prompt, language)

            # Parse response to extract code and tests
            generated = self._parse_generation_with_tests_response(response, language)

            self.generation_count += 1
            self.success_count += 1

            logger.info(
                f"Successfully generated {len(generated.code)} chars of code "
                f"and {len(generated.tests or '')} chars of tests"
            )
            return generated

        except Exception as e:
            self.generation_count += 1
            logger.error(f"Code+tests generation failed: {str(e)}")
            raise CodeGenerationError(f"Failed to generate code with tests: {str(e)}") from e

    async def refine_code(
        self,
        code: str,
        feedback: str,
        language: str = "python"
    ) -> GeneratedCode:
        """
        Refine existing code based on feedback.

        Args:
            code: Existing code to refine
            feedback: User feedback or error messages
            language: Programming language

        Returns:
            Refined code
        """
        logger.info(f"Refining {language} code based on feedback: {feedback[:100]}...")

        try:
            prompt = self._build_refinement_prompt(code, feedback, language)

            response = await self._call_llm_for_generation(prompt, language)

            refined = self._parse_generation_response(response, language)

            self.generation_count += 1
            self.success_count += 1

            logger.info("Successfully refined code")
            return refined

        except Exception as e:
            self.generation_count += 1
            logger.error(f"Code refinement failed: {str(e)}")
            raise CodeGenerationError(f"Failed to refine code: {str(e)}") from e

    def _build_generation_prompt(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build LLM prompt for code generation"""

        prompt = f"""Generate {language} code to accomplish the following task:

Task: {task}

Requirements:
- Write clean, readable, well-commented code
- Include error handling
- Use best practices for {language}
- Make the code self-contained and executable
"""

        if context:
            prompt += f"\nContext:\n{json.dumps(context, indent=2)}\n"

        prompt += f"""
Response format (JSON):
{{
    "code": "<generated code here>",
    "description": "<brief description of what the code does>",
    "dependencies": ["<list of required packages/modules>"],
    "complexity": "<simple|moderate|complex>",
    "estimated_runtime": <estimated seconds to run>
}}

Generate the code now:"""

        return prompt

    def _build_generation_with_tests_prompt(
        self,
        task: str,
        language: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for generation with tests"""

        test_framework = {
            "python": "pytest",
            "javascript": "jest",
            "bash": "bats"
        }.get(language, "appropriate testing framework")

        prompt = f"""Generate {language} code with test cases for the following task:

Task: {task}

Requirements:
- Write clean, testable, well-commented code
- Generate comprehensive test cases using {test_framework}
- Include edge cases and error scenarios in tests
- Make both code and tests executable
"""

        if context:
            prompt += f"\nContext:\n{json.dumps(context, indent=2)}\n"

        prompt += f"""
Response format (JSON):
{{
    "code": "<main code here>",
    "tests": "<test code here>",
    "description": "<brief description>",
    "dependencies": ["<list of required packages>"],
    "complexity": "<simple|moderate|complex>"
}}

Generate the code and tests now:"""

        return prompt

    def _build_refinement_prompt(
        self,
        code: str,
        feedback: str,
        language: str
    ) -> str:
        """Build prompt for code refinement"""

        prompt = f"""Refine the following {language} code based on feedback:

Original Code:
```{language}
{code}
```

Feedback: {feedback}

Requirements:
- Address all issues mentioned in the feedback
- Maintain the original functionality
- Improve code quality and readability
- Keep error handling robust

Response format (JSON):
{{
    "code": "<refined code here>",
    "description": "<what was changed and why>",
    "dependencies": ["<updated dependencies if any>"]
}}

Generate the refined code now:"""

        return prompt

    async def _call_llm_for_generation(self, prompt: str, language: str) -> str:
        """
        Call LLM service to generate code.

        Uses appropriate model based on complexity:
        - Use coder model for code generation tasks
        - Use reasoner model for complex algorithmic tasks
        """
        try:
            # Determine if this is a complex task requiring reasoning
            is_complex = any(keyword in prompt.lower() for keyword in [
                "algorithm", "optimize", "efficient", "complex", "advanced"
            ])

            # Use appropriate model (will be handled by multi-model selector)
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more deterministic code
                max_tokens=4000,  # Allow for longer code generation
                metadata={
                    "task_type": "code_generation",
                    "language": language,
                    "is_complex": is_complex
                }
            )

            return response.text

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise CodeGenerationError(f"LLM generation failed: {str(e)}") from e

    def _parse_generation_response(self, response: str, language: str) -> GeneratedCode:
        """Parse LLM response into GeneratedCode object"""

        try:
            # Try to parse as JSON first
            if response.strip().startswith("{"):
                data = json.loads(response)
                return GeneratedCode(
                    code=data["code"],
                    language=language,
                    description=data.get("description", "Generated code"),
                    dependencies=data.get("dependencies"),
                    complexity=data.get("complexity", "simple"),
                    estimated_runtime=data.get("estimated_runtime")
                )

            # Fallback: Extract code from markdown code blocks
            code = self._extract_code_from_markdown(response, language)
            if code:
                return GeneratedCode(
                    code=code,
                    language=language,
                    description="Generated code (extracted from response)"
                )

            # Last resort: Use entire response as code
            return GeneratedCode(
                code=response.strip(),
                language=language,
                description="Generated code (raw response)"
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response, trying fallback: {e}")
            # Try fallback parsing
            code = self._extract_code_from_markdown(response, language)
            if code:
                return GeneratedCode(
                    code=code,
                    language=language,
                    description="Generated code (extracted from markdown)"
                )
            raise CodeGenerationError("Failed to parse LLM response")

    def _parse_generation_with_tests_response(
        self,
        response: str,
        language: str
    ) -> GeneratedCode:
        """Parse response containing both code and tests"""

        try:
            # Try JSON parsing
            if response.strip().startswith("{"):
                data = json.loads(response)
                return GeneratedCode(
                    code=data["code"],
                    language=language,
                    description=data.get("description", "Generated code with tests"),
                    tests=data.get("tests"),
                    dependencies=data.get("dependencies"),
                    complexity=data.get("complexity", "simple")
                )

            # Fallback: Extract code blocks
            code_blocks = self._extract_all_code_blocks(response, language)
            if len(code_blocks) >= 2:
                return GeneratedCode(
                    code=code_blocks[0],
                    language=language,
                    description="Generated code with tests (extracted)",
                    tests=code_blocks[1]
                )
            elif len(code_blocks) == 1:
                return GeneratedCode(
                    code=code_blocks[0],
                    language=language,
                    description="Generated code (tests not found)"
                )

            raise CodeGenerationError("Could not extract code and tests from response")

        except json.JSONDecodeError:
            # Try fallback
            code_blocks = self._extract_all_code_blocks(response, language)
            if code_blocks:
                return GeneratedCode(
                    code=code_blocks[0],
                    language=language,
                    description="Generated code (fallback extraction)",
                    tests=code_blocks[1] if len(code_blocks) > 1 else None
                )
            raise CodeGenerationError("Failed to parse code and tests from response")

    def _extract_code_from_markdown(self, text: str, language: str) -> Optional[str]:
        """Extract code from markdown code blocks"""

        # Try language-specific code block
        marker = f"```{language}"
        if marker in text:
            parts = text.split(marker)[1:]
            if parts:
                code = parts[0].split("```")[0].strip()
                return code

        # Try generic code block
        if "```" in text:
            parts = text.split("```")[1:]
            if parts:
                code = parts[0].split("```")[0].strip()
                # Remove language identifier if present
                lines = code.split("\n")
                if lines and lines[0].strip() in ["python", "javascript", "js", "bash", "sh"]:
                    code = "\n".join(lines[1:])
                return code.strip()

        return None

    def _extract_all_code_blocks(self, text: str, language: str) -> List[str]:
        """Extract all code blocks from markdown text"""

        code_blocks = []

        # Find all code blocks
        parts = text.split("```")
        for i in range(1, len(parts), 2):  # Odd indices are code blocks
            block = parts[i].strip()
            # Remove language identifier
            lines = block.split("\n")
            if lines and lines[0].strip() in ["python", "javascript", "js", "bash", "sh", language]:
                block = "\n".join(lines[1:])
            code_blocks.append(block.strip())

        return code_blocks

    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics"""

        success_rate = (
            (self.success_count / self.generation_count * 100)
            if self.generation_count > 0
            else 0.0
        )

        return {
            "total_generations": self.generation_count,
            "successful_generations": self.success_count,
            "success_rate": round(success_rate, 2),
        }
