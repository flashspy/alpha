# Agent Skills Usage Guide

## Introduction

Alpha's Agent Skill System allows you to **dynamically expand its capabilities** through auto-discovery and installation of skills. Unlike built-in tools, skills are modular, versioned, and can be contributed by the community.

## Quick Start

### Using Skills in Conversation

Skills are automatically discovered and installed when needed:

```
You: Convert "hello world" to uppercase

Alpha: I'll use the text-processing skill for this.

SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

Result: "HELLO WORLD"
```

No manual installation required - Alpha handles it automatically!

### CLI Commands

```bash
# List installed skills
skills

# Search for skills
search skill text
search skill json
search skill data

# Get help
help skills
```

## Builtin Skills

Alpha comes with **3 preinstalled builtin skills** ready to use immediately:

### 1. text-processing
20+ text operations for common text manipulation tasks.

**Available Operations:**

**Case Transformations:**
```python
# Uppercase
operation: "uppercase"
text: "hello world"
Result: "HELLO WORLD"

# Lowercase
operation: "lowercase"
text: "HELLO WORLD"
Result: "hello world"

# Title Case
operation: "titlecase"
text: "hello world"
Result: "Hello World"

# Capitalize
operation: "capitalize"
text: "hello world"
Result: "Hello world"
```

**String Operations:**
```python
# Reverse
operation: "reverse"
text: "hello"
Result: "olleh"

# Trim whitespace
operation: "trim"
text: "  hello  "
Result: "hello"
```

**Extraction:**
```python
# Extract emails
operation: "extract_emails"
text: "Contact: john@example.com or jane@test.org"
Result: ["john@example.com", "jane@test.org"]

# Extract URLs
operation: "extract_urls"
text: "Visit https://example.com or http://test.org"
Result: ["https://example.com", "http://test.org"]

# Extract numbers
operation: "extract_numbers"
text: "There are 42 apples and 15 oranges"
Result: [42.0, 15.0]
```

**Complete Operation List:**
- uppercase, lowercase, titlecase, capitalize
- reverse, trim, strip
- split, join, replace, remove
- count_words, count_chars, count_lines
- extract_emails, extract_urls, extract_numbers
- truncate, pad_left, pad_right

### 2. json-processor
8 JSON operations for parsing, formatting, and transformation.

**Available Operations:**

```python
# Parse JSON string
operation: "parse"
json_str: '{"name": "Alpha", "version": "1.0"}'
Result: {"name": "Alpha", "version": "1.0"}

# Format JSON (pretty-print)
operation: "format"
json_str: '{"name":"Alpha"}'
indent: 2
Result: {
  "name": "Alpha"
}

# Minify JSON
operation: "minify"
json_str: '{  "name":  "Alpha"  }'
Result: '{"name":"Alpha"}'

# Validate JSON
operation: "validate"
json_str: '{"valid": true}'
Result: {"valid": true, "error": null}

# Extract value by path
operation: "extract"
json_str: '{"user": {"name": "Alice", "age": 30}}'
path: "user.name"
Result: "Alice"

# Merge multiple JSON objects
operation: "merge"
json_objects: [{"a": 1}, {"b": 2}, {"c": 3}]
Result: {"a": 1, "b": 2, "c": 3}

# Filter by keys
operation: "filter"
json_str: '{"a": 1, "b": 2, "c": 3}'
keys: ["a", "c"]
Result: {"a": 1, "c": 3}
```

**Complete Operation List:**
- parse, stringify, format, minify
- validate, extract, merge, filter

### 3. data-analyzer
17 statistical operations for data analysis and aggregation.

**Available Operations:**

**Basic Statistics:**
```python
# Mean (average)
operation: "mean"
data: [1, 2, 3, 4, 5]
Result: 3.0

# Median
operation: "median"
data: [1, 2, 3, 4, 5]
Result: 3.0

# Mode (most common)
operation: "mode"
data: [1, 2, 2, 3, 3, 3]
Result: 3

# Min, Max, Range
operation: "min"
data: [10, 5, 20, 15]
Result: 5

operation: "max"
data: [10, 5, 20, 15]
Result: 20

operation: "range"
data: [10, 5, 20, 15]
Result: 15  # max - min
```

**Advanced Statistics:**
```python
# Standard deviation
operation: "stdev"
data: [2, 4, 6, 8, 10]
Result: 2.8284

# Variance
operation: "variance"
data: [2, 4, 6, 8, 10]
Result: 8.0

# Percentile
operation: "percentile"
data: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
percentile: 75
Result: 7.75
```

**Data Operations:**
```python
# Group by key
operation: "group_by"
data: [
  {"type": "A", "value": 1},
  {"type": "B", "value": 2},
  {"type": "A", "value": 3}
]
key: "type"
Result: {
  "A": [{"type": "A", "value": 1}, {"type": "A", "value": 3}],
  "B": [{"type": "B", "value": 2}]
}

# Aggregate
operation: "aggregate"
data: [
  {"category": "fruit", "price": 10},
  {"category": "fruit", "price": 15},
  {"category": "veg", "price": 5}
]
group_key: "category"
value_key: "price"
agg_func: "sum"
Result: {"fruit": 25, "veg": 5}

# Sort data
operation: "sort"
data: [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]
key: "age"
Result: [{"name": "Bob", "age": 25}, {"name": "Alice", "age": 30}]

# Get statistical summary
operation: "summary"
data: [10, 20, 30, 40, 50]
Result: {
  "count": 5,
  "mean": 30.0,
  "median": 30.0,
  "min": 10,
  "max": 50,
  "stdev": 14.14,
  "variance": 200.0
}
```

**Complete Operation List:**
- mean, median, mode, min, max, range, sum, count
- variance, stdev, percentile, quartiles
- group_by, aggregate, sort, filter, summary

## Custom Skills

### Installing Custom Skills

Skills from the marketplace are automatically installed when referenced:

```
You: Use the weather-api skill to get weather for Beijing

Alpha: Installing weather-api skill...
Installing dependencies...
Skill installed successfully!

[Executes weather-api skill]
```

### Creating Your Own Skill

Create a new skill directory:

```
my-custom-skill/
├── skill.yaml        # Metadata (required)
├── skill.py          # Implementation (required)
├── README.md         # Documentation (optional)
└── requirements.txt  # Dependencies (optional)
```

**skill.yaml:**
```yaml
name: my-custom-skill
version: "1.0.0"
description: "My awesome custom skill"
author: "Your Name"
category: "utility"
tags:
  - helper
  - automation
dependencies:
  - requests
python_version: ">=3.8"
homepage: "https://github.com/user/my-custom-skill"
repository: "https://github.com/user/my-custom-skill"
license: "MIT"
```

**skill.py:**
```python
from alpha.skills.base import AgentSkill, SkillResult

class MyCustomSkill(AgentSkill):
    """My custom skill implementation."""

    async def initialize(self) -> bool:
        """Initialize the skill."""
        # Setup resources, load models, etc.
        return True

    async def execute(self, **kwargs) -> SkillResult:
        """
        Execute the skill.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            SkillResult
        """
        try:
            # Your skill logic here
            param1 = kwargs.get('param1')
            result = f"Processed: {param1}"

            return SkillResult(
                success=True,
                output=result
            )

        except Exception as e:
            return SkillResult(
                success=False,
                output=None,
                error=str(e)
            )

    async def cleanup(self):
        """Clean up resources."""
        pass

    def get_schema(self):
        """Define parameter schema."""
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                }
            },
            "required": ["param1"]
        }
```

### Publishing Skills

1. Create a GitHub repository for your skill
2. Add it to the skill marketplace registry
3. Submit a pull request to the Alpha skills repository

## Best Practices

### When to Use Skills vs Tools

| Feature | Tools | Skills |
|---------|-------|--------|
| Built-in | Yes | No |
| Installation | Always available | Auto-install on demand |
| Versioning | No | Yes |
| Dependencies | No | Yes |
| Community contributions | No | Yes |

**Use Tools for:**
- Core system operations (shell, file, HTTP)
- Always-needed functionality
- Simple, standalone operations

**Use Skills for:**
- Specialized functionality
- Domain-specific operations
- Operations requiring external dependencies
- Community-contributed capabilities

### Skill Development Tips

1. **Single Responsibility** - Each skill should do one thing well
2. **Clear Parameters** - Use descriptive names and provide schemas
3. **Error Handling** - Always return meaningful error messages
4. **Documentation** - Include a comprehensive README
5. **Testing** - Write tests for your skill
6. **Performance** - Lazy-load heavy resources in `initialize()`

## Troubleshooting

### Skill Not Found

**Problem:**
```
Error: Skill not found: my-skill
```

**Solutions:**
1. Enable auto-install (it's enabled by default)
2. Check skill name spelling
3. Verify skill exists in marketplace
4. Check network connectivity

### Installation Failed

**Problem:**
```
Error: Failed to install skill: my-skill
```

**Solutions:**
1. Check internet connection
2. Verify Python version compatibility
3. Install dependencies manually: `pip install -r requirements.txt`
4. Check repository URL is accessible

### Execution Failed

**Problem:**
```
Error: Missing required parameters: ['param1']
```

**Solutions:**
1. Provide all required parameters
2. Check skill documentation for parameter names
3. Verify parameter types match schema

### Builtin Skills Not Loading

**Problem:**
```
Builtin skills not found
```

**Solutions:**
1. Check `alpha/skills/builtin/` directory exists
2. Verify all skill.yaml files are present
3. Restart Alpha
4. Check logs in `logs/alpha.log`

## Advanced Usage

### Programmatic Usage

```python
from alpha.skills.executor import SkillExecutor
from alpha.skills.registry import SkillRegistry
from alpha.skills.marketplace import SkillMarketplace
from alpha.skills.installer import SkillInstaller

# Setup
registry = SkillRegistry()
marketplace = SkillMarketplace()
installer = SkillInstaller()
executor = SkillExecutor(
    registry=registry,
    marketplace=marketplace,
    installer=installer,
    auto_install=True
)

# Execute skill
result = await executor.execute(
    "text-processing",
    operation="uppercase",
    text="hello world"
)

if result.success:
    print(result.output)  # "HELLO WORLD"
else:
    print(f"Error: {result.error}")
```

### Disable Auto-Install

If you prefer manual control:

```python
executor = SkillExecutor(
    registry=registry,
    marketplace=marketplace,
    installer=installer,
    auto_install=False  # Disable auto-install
)

# Now you must manually install skills
await installer.install(skill_path)
```

## See Also

- [Agent Skills Documentation](../../AGENT_SKILLS.md) - Technical documentation
- [Builtin Skills Reference](../../BUILTIN_SKILLS.md) - Complete builtin skills reference
- [Features Guide](features.md) - All Alpha features

---

**Version**: v0.4.0
**Last Updated**: 2026-01-29
**Status**: Production Ready
