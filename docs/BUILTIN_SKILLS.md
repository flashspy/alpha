# Builtin Skills Documentation

## Overview

Alpha comes with **3 preinstalled builtin skills** that provide commonly needed capabilities. These skills are automatically loaded when Alpha starts, requiring no installation or configuration.

## Available Builtin Skills

### 1. text-processing

**Description**: Advanced text processing and transformation

**Category**: utility

**Version**: 1.0.0

**Operations**:

#### Case Transformations
- `uppercase` - Convert to UPPERCASE
- `lowercase` - Convert to lowercase
- `titlecase` - Convert To Title Case
- `capitalize` - Capitalize first letter

#### String Operations
- `reverse` - Reverse string
- `trim` - Remove leading/trailing whitespace
- `strip` - Strip specific characters

#### Split and Join
- `split` - Split string by delimiter
- `join` - Join array with delimiter
- `replace` - Replace substring
- `remove` - Remove pattern

#### Counting
- `count_words` - Count words
- `count_chars` - Count characters
- `count_lines` - Count lines

#### Extraction
- `extract_emails` - Extract email addresses
- `extract_urls` - Extract URLs
- `extract_numbers` - Extract numbers

#### Formatting
- `truncate` - Truncate with suffix
- `pad_left` - Left pad
- `pad_right` - Right pad

**Usage Examples**:

```python
# Uppercase
SKILL: text-processing
PARAMS:
  operation: "uppercase"
  text: "hello world"

# Extract emails
SKILL: text-processing
PARAMS:
  operation: "extract_emails"
  text: "Contact us at support@alpha.ai or sales@alpha.ai"

# Split text
SKILL: text-processing
PARAMS:
  operation: "split"
  text: "apple,banana,orange"
  delimiter: ","
```

---

### 2. json-processor

**Description**: JSON parsing, formatting, validation and transformation

**Category**: data

**Version**: 1.0.0

**Operations**:

- `parse` - Parse JSON string to object
- `stringify` - Convert object to JSON string
- `format` - Pretty-print JSON
- `minify` - Minify JSON (remove whitespace)
- `validate` - Validate JSON syntax
- `extract` - Extract value by path (e.g., "user.name")
- `merge` - Merge multiple JSON objects
- `filter` - Filter JSON by keys

**Usage Examples**:

```python
# Parse JSON
SKILL: json-processor
PARAMS:
  operation: "parse"
  json_str: '{"name": "Alpha", "version": "1.0"}'

# Format JSON
SKILL: json-processor
PARAMS:
  operation: "format"
  json_str: '{"name":"Alpha","version":"1.0"}'
  indent: 2

# Extract value by path
SKILL: json-processor
PARAMS:
  operation: "extract"
  json_str: '{"user": {"name": "Alice", "age": 30}}'
  path: "user.name"

# Validate JSON
SKILL: json-processor
PARAMS:
  operation: "validate"
  json_str: '{"valid": true}'
```

---

### 3. data-analyzer

**Description**: Statistical analysis and data aggregation

**Category**: data

**Version**: 1.0.0

**Operations**:

#### Basic Statistics
- `mean` - Calculate average
- `median` - Calculate median
- `mode` - Find most common value
- `min` - Find minimum
- `max` - Find maximum
- `range` - Calculate range (max - min)
- `sum` - Calculate sum
- `count` - Count elements

#### Advanced Statistics
- `variance` - Calculate variance
- `stdev` - Calculate standard deviation
- `percentile` - Calculate percentile
- `quartiles` - Calculate Q1, Q2, Q3

#### Data Operations
- `group_by` - Group data by key
- `aggregate` - Aggregate with function (count, sum, avg, min, max)
- `sort` - Sort data
- `filter` - Filter data by condition
- `summary` - Get complete statistical summary

**Usage Examples**:

```python
# Calculate mean
SKILL: data-analyzer
PARAMS:
  operation: "mean"
  data: [1, 2, 3, 4, 5]

# Get statistical summary
SKILL: data-analyzer
PARAMS:
  operation: "summary"
  data: [10, 20, 30, 40, 50]

# Sort data
SKILL: data-analyzer
PARAMS:
  operation: "sort"
  data: [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
  key: "age"
  reverse: false

# Group by key
SKILL: data-analyzer
PARAMS:
  operation: "group_by"
  data: [{"type": "A", "value": 1}, {"type": "B", "value": 2}, {"type": "A", "value": 3}]
  key: "type"
```

---

## Automatic Loading

Builtin skills are **automatically loaded** when Alpha starts. You'll see a message:

```
Loading builtin skills...
✓ Loaded 3 builtin skills
```

No configuration or installation required!

## Advantages of Builtin Skills

1. **Always Available** - No installation needed
2. **Fast Loading** - Preinstalled and ready to use
3. **No Dependencies** - Pure Python implementations
4. **Reliable** - Tested and maintained by Alpha team
5. **Offline Ready** - Work without internet connection

## Performance

All builtin skills are optimized for:
- Fast execution (< 1ms for simple operations)
- Low memory footprint
- No external dependencies
- Python 3.8+ compatibility

## Extending Builtin Skills

You cannot modify builtin skills directly, but you can:

1. **Create Custom Skills** - Build your own skills with similar functionality
2. **Combine Skills** - Use multiple skills together
3. **Request Features** - Suggest new operations via GitHub issues

## Troubleshooting

### Builtin Skills Not Loading

If builtin skills fail to load:

1. Check logs in `logs/alpha.log`
2. Verify `alpha/skills/builtin/` directory exists
3. Ensure all skill.yaml files are present
4. Restart Alpha

### Skill Execution Errors

If a skill operation fails:

1. Check parameter requirements in this documentation
2. Verify data types match expected formats
3. Review error message for details
4. Check `logs/alpha.log` for stack traces

## Source Code

Builtin skills source code is located at:
- `alpha/skills/builtin/text-processing/`
- `alpha/skills/builtin/json-processor/`
- `alpha/skills/builtin/data-analyzer/`

Feel free to review the code for implementation details!

## Version History

### v1.0.0 (2026-01-29)
- Initial release
- 3 builtin skills: text-processing, json-processor, data-analyzer
- Automatic preinstallation
- Full test coverage

---

For more information about the Agent Skill system, see:
- [Agent Skills Documentation](AGENT_SKILLS.md)
- [Quick Start Guide](AGENT_SKILLS_QUICKSTART.md)
