# Intelligent Multi-Model Selection Guide

## Overview

Alpha v0.4.0 introduces **Intelligent Multi-Model Selection**, a feature that automatically analyzes your tasks and routes them to the most appropriate AI model. This ensures optimal performance while minimizing API costs.

## Supported Models

Alpha supports three DeepSeek models, each optimized for different task types:

### 1. deepseek-chat
**Best For**: General conversation and simple tasks

**Characteristics:**
- Fast response time
- Cost-effective for everyday use
- Excellent for Q&A and simple queries
- Max tokens: 4096
- Temperature: 0.7

**Use Cases:**
- General questions ("What is the capital of France?")
- Simple explanations
- Basic conversations
- Casual information queries

### 2. deepseek-coder
**Best For**: Programming and development tasks

**Characteristics:**
- Specialized for code generation
- Optimized for development workflows
- Strong syntax understanding
- Max tokens: 4096
- Temperature: 0.7

**Use Cases:**
- Writing code ("Write a Python function to sort a list")
- Code refactoring
- Bug fixing
- Script development
- Code review and explanation

### 3. deepseek-reasoner
**Best For**: Complex reasoning and expert-level analysis

**Characteristics:**
- Advanced reasoning capabilities (DeepSeek-R1)
- Handles complex problem-solving
- Suitable for expert topics
- Max tokens: 8192
- Temperature: 0.6

**Use Cases:**
- Algorithm design with trade-off analysis
- System architecture decisions
- Distributed systems concepts
- Machine learning explanations
- Security analysis
- Complex problem-solving

## How It Works

### Task Difficulty Levels

The system classifies tasks into four difficulty levels:

| Level | Description | Typical Tasks |
|-------|-------------|---------------|
| **Simple** | Basic questions, short queries | "What time is it?", "Convert 10km to miles" |
| **Medium** | Moderate complexity, explanations | "Explain async/await", "Write a sorting function" |
| **Complex** | Advanced coding, refactoring | "Refactor this class", "Optimize database queries" |
| **Expert** | Distributed systems, ML/DL, security | "Explain Raft consensus", "Design a fault-tolerant system" |

### Automatic Selection Logic

The model selector uses a **priority-based approach**:

```
Priority 1: Expert/Complex Reasoning Tasks
  ↓
  deepseek-reasoner

Priority 2: Coding Tasks (without heavy reasoning)
  ↓
  deepseek-coder

Priority 3: Other Tasks
  ↓
  Based on difficulty_range configuration
  (defaults to deepseek-chat for simple/medium)
```

### Task Analysis

The system analyzes messages for:

1. **Coding Keywords**: "write code", "function", "implement", "debug", "refactor"
2. **Reasoning Keywords**: "why", "explain", "analyze", "compare", "evaluate"
3. **Expert Topics**: "machine learning", "distributed system", "cryptography", "scalability"
4. **Message Complexity**: Length and structure of the request

## Configuration

### Enable Automatic Selection

Edit `config.yaml`:

```yaml
llm:
  default_provider: "deepseek"
  providers:
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"

      # Enable automatic model selection
      auto_select_model: true

      # Default model when auto-selection is disabled
      default_model: "deepseek-chat"

      # Model configurations
      models:
        deepseek-chat:
          max_tokens: 4096
          temperature: 0.7
          difficulty_range: ["simple", "medium"]

        deepseek-reasoner:
          max_tokens: 8192
          temperature: 0.6
          difficulty_range: ["complex", "expert"]

        deepseek-coder:
          max_tokens: 4096
          temperature: 0.7
          difficulty_range: ["medium", "complex"]
```

### Disable Automatic Selection

To use a specific model for all tasks:

```yaml
deepseek:
  auto_select_model: false
  model: "deepseek-coder"  # Always use this model
```

## Usage Examples

### Example 1: Simple Question → deepseek-chat

**User Input:**
```
What is the capital of France?
```

**Model Selected:** `deepseek-chat`

**Reason:** Simple factual query, no coding or complex reasoning required.

---

### Example 2: Coding Task → deepseek-coder

**User Input:**
```
Write a Python function to calculate Fibonacci numbers recursively.
```

**Model Selected:** `deepseek-coder`

**Reason:** Coding task detected (keywords: "write", "function", "Python"), medium complexity.

---

### Example 3: Complex Reasoning → deepseek-reasoner

**User Input:**
```
Explain the trade-offs between different distributed consensus algorithms like Raft and Paxos.
```

**Model Selected:** `deepseek-reasoner`

**Reason:** Expert-level topic (distributed systems), requires complex reasoning and analysis.

---

### Example 4: Code with Reasoning → deepseek-reasoner

**User Input:**
```
Design a scalable authentication system with JWT tokens. Explain security considerations and trade-offs.
```

**Model Selected:** `deepseek-reasoner`

**Reason:** Coding task + reasoning requirement + expert topics (security, scalability).

## Cost Optimization

Automatic model selection helps optimize costs:

| Scenario | Without Auto-Selection | With Auto-Selection | Savings |
|----------|----------------------|---------------------|---------|
| 100 simple queries | All use reasoner | 100 use chat | ~40% |
| 50 coding tasks | All use chat | 50 use coder | Better quality |
| 20 expert analyses | All use chat | 20 use reasoner | Better quality |

**Key Benefits:**
1. **Lower costs** - Simple tasks use cheaper models
2. **Better quality** - Complex tasks get specialized models
3. **Automatic** - No manual model selection needed

## Monitoring

Check logs to see model selection decisions:

```
INFO: Task analysis - Difficulty: medium, Coding: True, Reasoning: False
INFO: Using deepseek-coder for coding task
INFO: Using DeepSeek model: deepseek-coder (temp=0.7, max_tokens=4096)
```

Log location: `logs/alpha.log`

## Customization

### Adjust Keywords

Edit `alpha/llm/model_selector.py`:

```python
class TaskAnalyzer:
    CODING_KEYWORDS = [
        'write code', 'function', 'implement',
        # Add your custom keywords
        'create script', 'develop app'
    ]

    EXPERT_KEYWORDS = [
        'machine learning', 'distributed system',
        # Add your custom keywords
        'blockchain', 'kubernetes'
    ]
```

### Modify Difficulty Ranges

In `config.yaml`, adjust which models handle which difficulty levels:

```yaml
models:
  deepseek-chat:
    difficulty_range: ["simple"]  # Only simple tasks

  deepseek-coder:
    difficulty_range: ["medium"]  # Only medium tasks

  deepseek-reasoner:
    difficulty_range: ["complex", "expert"]  # Complex and expert
```

## Troubleshooting

### Wrong Model Being Selected

**Problem:** Expected deepseek-coder but got deepseek-chat.

**Solutions:**
1. Check if auto-selection is enabled: `auto_select_model: true`
2. Review task keywords in logs
3. Add more specific keywords to your request
4. Adjust difficulty ranges in config

**Example Fix:**
```
# Instead of: "Write code for sorting"
# Use: "Write a Python function to implement quicksort"
```

### Model Not Available

**Problem:** "Model not found: deepseek-reasoner"

**Solutions:**
1. Verify `models` section in config.yaml includes the model
2. Check API key has access to the model
3. Ensure model name is spelled correctly

### Auto-Selection Not Working

**Problem:** Always uses default_model.

**Solutions:**
1. Check `auto_select_model: true` is set
2. Verify models configuration exists
3. Check logs for selection errors
4. Ensure DEEPSEEK_API_KEY is valid

## Best Practices

1. **Let Auto-Selection Work** - Don't override unless necessary
2. **Use Descriptive Requests** - Include keywords that help classification
3. **Monitor Logs** - Review selection decisions periodically
4. **Adjust as Needed** - Customize keywords for your use cases
5. **Test Different Phrasings** - See how wording affects selection

## API Reference

### TaskDifficulty Enum
```python
class TaskDifficulty(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"
```

### TaskAnalyzer
```python
class TaskAnalyzer:
    @classmethod
    def analyze(cls, messages: List[Dict]) -> TaskCharacteristics
```

### ModelSelector
```python
class ModelSelector:
    def __init__(self, models_config: Dict)

    def select_model(
        self,
        messages: List[Dict],
        default_model: str = "deepseek-chat"
    ) -> str

    def get_model_config(self, model_name: str)
```

## See Also

- [Features Guide](features.md) - Complete feature documentation
- [DEEPSEEK_MODELS.md](../../DEEPSEEK_MODELS.md) - Technical details
- [Configuration Guide](../../../README.md#configuration) - API setup

---

**Version**: v0.4.0
**Last Updated**: 2026-01-29
**Status**: Production Ready
