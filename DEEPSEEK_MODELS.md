# DeepSeek Multi-Model Support and Automatic Model Selection

This document describes the new multi-model support for DeepSeek and automatic model selection based on task difficulty.

## Overview

The system now supports three DeepSeek models, each optimized for different task types:

1. **deepseek-chat** - General-purpose chat model for simple to medium tasks
2. **deepseek-coder** - Specialized coding model for development tasks
3. **deepseek-reasoner** - Advanced reasoning model (DeepSeek-R1) for complex analysis

## Configuration

The configuration is located in `config.yaml` under the `deepseek` provider section:

```yaml
llm:
  default_provider: "deepseek"
  providers:
    deepseek:
      api_key: "${DEEPSEEK_API_KEY}"

      # Default model when auto-selection is disabled
      default_model: "deepseek-chat"

      # Enable automatic model selection
      auto_select_model: true

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

## Automatic Model Selection

When `auto_select_model: true`, the system automatically selects the best model based on:

### Task Difficulty Levels

- **Simple**: Basic questions, simple queries
- **Medium**: Coding tasks, explanations, moderate complexity
- **Complex**: Advanced coding, refactoring, algorithm design
- **Expert**: Distributed systems, ML/DL, security, advanced reasoning

### Selection Logic

The model selector uses a priority-based approach:

1. **Priority 1**: Expert-level or complex reasoning tasks → `deepseek-reasoner`
2. **Priority 2**: Medium/complex coding tasks without heavy reasoning → `deepseek-coder`
3. **Priority 3**: Other tasks → Based on difficulty range configuration

### Task Analysis

The system analyzes messages to detect:

- **Coding tasks**: Presence of programming-related keywords
- **Reasoning tasks**: Questions requiring analysis, comparison, explanation
- **Expert-level tasks**: Complex topics like ML, distributed systems, security
- **Task complexity**: Based on keywords and message length

## Usage Examples

### Automatic Selection Enabled

```python
from alpha.utils.config import load_config
from alpha.llm.service import LLMService, Message

# Load config
config = load_config("config.yaml")
llm_service = LLMService.from_config(config.llm)

# Simple question → deepseek-chat
messages = [Message(role="user", content="What is the capital of France?")]
response = await llm_service.complete(messages)

# Coding task → deepseek-coder
messages = [Message(role="user", content="Write a Python function to calculate fibonacci")]
response = await llm_service.complete(messages)

# Complex reasoning → deepseek-reasoner
messages = [Message(role="user", content="Explain distributed consensus algorithms")]
response = await llm_service.complete(messages)
```

### Manual Model Selection

You can override automatic selection by setting `auto_select_model: false` and specifying a model:

```yaml
deepseek:
  auto_select_model: false
  model: "deepseek-coder"  # Always use this model
```

Or specify model at runtime (if supported by your interface).

## Model Capabilities

### deepseek-chat
- **Best for**: General conversation, Q&A, simple tasks
- **Max tokens**: 4096
- **Temperature**: 0.7
- **Use cases**:
  - General questions
  - Simple explanations
  - Basic conversations

### deepseek-coder
- **Best for**: Programming and development tasks
- **Max tokens**: 4096
- **Temperature**: 0.7
- **Use cases**:
  - Writing code
  - Code refactoring
  - Bug fixing
  - Script development

### deepseek-reasoner
- **Best for**: Complex reasoning and analysis
- **Max tokens**: 8192
- **Temperature**: 0.6
- **Use cases**:
  - Algorithm design with analysis
  - System architecture decisions
  - Complex problem solving
  - Trade-off analysis
  - Distributed systems
  - Machine learning concepts

## Testing

Run the test script to verify model selection:

```bash
python3 test_model_selection.py
```

This will test various task types and show which model is selected for each.

## Monitoring

The system logs model selection decisions:

```
INFO: Task analysis - Difficulty: medium, Coding: True, Reasoning: False
INFO: Using deepseek-coder for coding task
INFO: Using DeepSeek model: deepseek-coder (temp=0.7, max_tokens=4096)
```

Check your logs to see how models are being selected.

## Cost Optimization

Automatic model selection helps optimize costs by:

1. Using `deepseek-chat` for simple tasks (lower cost)
2. Using specialized models only when needed
3. Matching model capabilities to task requirements

## Customization

You can customize model selection by:

1. **Adjusting difficulty ranges** in `config.yaml`
2. **Modifying keywords** in `alpha/llm/model_selector.py`
3. **Adding new models** by extending the configuration
4. **Customizing selection logic** in the `ModelSelector` class

## Architecture

### Files Modified

1. `config.yaml` - Multi-model configuration
2. `alpha/utils/config.py` - Configuration data structures
3. `alpha/llm/service.py` - DeepSeekProvider with model selection
4. `alpha/llm/model_selector.py` - Task analysis and model selection logic
5. `test_model_selection.py` - Test suite

### Key Classes

- `TaskAnalyzer` - Analyzes task characteristics
- `TaskDifficulty` - Difficulty level enum
- `ModelSelector` - Selects best model for task
- `DeepSeekProvider` - Enhanced with auto-selection support

## Troubleshooting

### Model not being auto-selected

- Check `auto_select_model: true` in config
- Verify `models` configuration is present
- Check logs for selection decisions

### Wrong model being selected

- Review task keywords in logs
- Adjust keywords in `model_selector.py`
- Modify difficulty ranges in config

### API errors

- Verify `DEEPSEEK_API_KEY` environment variable
- Check model names are correct
- Ensure API quota is available
