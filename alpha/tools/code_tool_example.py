"""
Code Execution Tool - Usage Examples

This file demonstrates how to use the CodeExecutionTool in Alpha.

The CodeExecutionTool is automatically registered when Alpha starts if:
1. code_execution.enabled is true in config.yaml
2. Docker is available on the system
"""

import asyncio
from alpha.tools.code_tool import CodeExecutionTool
from alpha.llm.service import LLMService
from alpha.utils.config import load_config


async def example_1_generate_and_execute():
    """
    Example 1: Generate and execute code from a task description.

    This is the most common use case - provide a natural language
    description and let Alpha generate and execute the code.
    """
    print("\n" + "="*80)
    print("Example 1: Generate and Execute Code from Task")
    print("="*80)

    # Initialize (normally done by Alpha's CLI)
    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # Execute a task
    result = await tool.execute(
        task="Calculate the factorial of 10 and print the result",
        language="python",
        require_approval=False  # Skip approval for demo
    )

    if result.success:
        print(f"\n✓ Success!")
        print(f"\n{result.output}")
        print(f"\nExecution time: {result.metadata.get('execution_time', 'N/A')}s")
    else:
        print(f"\n✗ Failed: {result.error}")


async def example_2_execute_provided_code():
    """
    Example 2: Execute provided code directly.

    Use this when you already have the code and just need to
    execute it safely in a sandbox.
    """
    print("\n" + "="*80)
    print("Example 2: Execute Provided Code")
    print("="*80)

    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # Python code to execute
    python_code = """
import math

# Calculate area of a circle
radius = 5
area = math.pi * radius ** 2

print(f"Circle with radius {radius} has area: {area:.2f}")
"""

    result = await tool.execute(
        code=python_code,
        language="python",
        require_approval=False
    )

    if result.success:
        print(f"\n✓ Success!")
        print(f"\n{result.output}")
    else:
        print(f"\n✗ Failed: {result.error}")


async def example_3_javascript_execution():
    """
    Example 3: Execute JavaScript code.

    The tool supports multiple languages including JavaScript.
    """
    print("\n" + "="*80)
    print("Example 3: Execute JavaScript Code")
    print("="*80)

    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # JavaScript code
    js_code = """
// Calculate Fibonacci sequence
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// Calculate first 10 Fibonacci numbers
console.log("First 10 Fibonacci numbers:");
for (let i = 0; i < 10; i++) {
    console.log(`F(${i}) = ${fibonacci(i)}`);
}
"""

    result = await tool.execute(
        code=js_code,
        language="javascript",
        require_approval=False
    )

    if result.success:
        print(f"\n✓ Success!")
        print(f"\n{result.output}")
    else:
        print(f"\n✗ Failed: {result.error}")


async def example_4_bash_script():
    """
    Example 4: Execute Bash script.

    Useful for system operations and shell commands.
    """
    print("\n" + "="*80)
    print("Example 4: Execute Bash Script")
    print("="*80)

    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # Bash script
    bash_code = """
#!/bin/bash

# System information script
echo "System Information:"
echo "=================="
echo "Date: $(date)"
echo "User: $(whoami)"
echo "Working Directory: $(pwd)"
echo "Available Space:"
df -h / | tail -1
"""

    result = await tool.execute(
        code=bash_code,
        language="bash",
        require_approval=False
    )

    if result.success:
        print(f"\n✓ Success!")
        print(f"\n{result.output}")
    else:
        print(f"\n✗ Failed: {result.error}")


async def example_5_with_timeout():
    """
    Example 5: Code execution with custom timeout.

    Protect against infinite loops or long-running code.
    """
    print("\n" + "="*80)
    print("Example 5: Execution with Timeout")
    print("="*80)

    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # Code that takes some time
    code = """
import time

print("Starting computation...")
for i in range(3):
    time.sleep(1)
    print(f"Step {i+1} completed")
print("Done!")
"""

    result = await tool.execute(
        code=code,
        language="python",
        timeout=10,  # 10 second timeout
        require_approval=False
    )

    if result.success:
        print(f"\n✓ Success!")
        print(f"\n{result.output}")
    else:
        print(f"\n✗ Failed: {result.error}")


async def example_6_error_handling():
    """
    Example 6: Error handling.

    See how the tool handles code with errors.
    """
    print("\n" + "="*80)
    print("Example 6: Error Handling")
    print("="*80)

    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # Code with intentional error
    code = """
# This will cause a division by zero error
result = 10 / 0
print(result)
"""

    result = await tool.execute(
        code=code,
        language="python",
        require_approval=False
    )

    if result.success:
        print(f"\n✓ Success!")
        print(f"\n{result.output}")
    else:
        print(f"\n✗ Failed (as expected):")
        print(f"\n{result.error}")


async def example_7_statistics():
    """
    Example 7: Get tool statistics.

    Track usage and success rate of the code execution tool.
    """
    print("\n" + "="*80)
    print("Example 7: Tool Statistics")
    print("="*80)

    config = load_config()
    llm_service = LLMService.from_config(config.llm)
    tool = CodeExecutionTool(llm_service, config.dict())

    # Run a few executions
    await tool.execute(
        task="Print 'Hello, World!'",
        language="python",
        require_approval=False
    )

    await tool.execute(
        task="Calculate 2 + 2",
        language="python",
        require_approval=False
    )

    # Get statistics
    stats = tool.get_statistics()

    print("\n📊 Tool Statistics:")
    print(f"  Total Executions: {stats['total_executions']}")
    print(f"  Successful: {stats['successful_executions']}")
    print(f"  Failed: {stats['failed_executions']}")
    print(f"  Success Rate: {stats['success_rate']}%")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("CodeExecutionTool - Usage Examples")
    print("="*80)

    # Check if Docker is available first
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("\n✓ Docker is available and running")
    except Exception as e:
        print(f"\n✗ Docker not available: {e}")
        print("\nPlease install Docker to run these examples:")
        print("  https://docs.docker.com/get-docker/")
        return

    # Run examples
    examples = [
        example_1_generate_and_execute,
        example_2_execute_provided_code,
        example_3_javascript_execution,
        example_4_bash_script,
        example_5_with_timeout,
        example_6_error_handling,
        example_7_statistics,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\nExample failed with error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
