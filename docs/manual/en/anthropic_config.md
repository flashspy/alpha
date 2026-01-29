# Anthropic Configuration Guide

## Overview

Alpha uses Anthropic Claude as the default LLM provider, supporting flexible configuration methods.

## Environment Variable Configuration

### Method 1: Using ANTHROPIC_AUTH_TOKEN (Recommended)

```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
```

### Method 2: Using ANTHROPIC_API_KEY (Compatible)

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
```

### Fallback Mechanism

The configuration file uses the following fallback order:
1. Prioritize `ANTHROPIC_AUTH_TOKEN`
2. If not set, use `ANTHROPIC_API_KEY`
3. If neither is set, startup will fail

## Configuration File

### config.yaml

```yaml
llm:
  default_provider: "anthropic"
  providers:
    anthropic:
      # API key (with fallback support)
      api_key: "${ANTHROPIC_AUTH_TOKEN:-${ANTHROPIC_API_KEY}}"

      # Optional: Custom API endpoint
      base_url: "${ANTHROPIC_BASE_URL}"

      # Model configuration
      model: "claude-3-5-sonnet-20241022"
      max_tokens: 8192
      temperature: 0.7
```

## Supported Models

### Claude 3.5 Series (Recommended)
- `claude-3-5-sonnet-20241022` - Latest Sonnet (default)
- `claude-3-5-sonnet-20240620` - Earlier Sonnet

### Claude 3 Series
- `claude-3-opus-20240229` - Most powerful
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-haiku-20240307` - Fastest

## Custom API Endpoint

If using a self-hosted Anthropic-compatible API, you can set a custom endpoint:

```bash
export ANTHROPIC_BASE_URL="https://your-custom-api.example.com"
```

The configuration file will automatically apply this setting.

## Quick Start

### 1. Set API Key

```bash
# Using AUTH_TOKEN (recommended)
export ANTHROPIC_AUTH_TOKEN="sk-ant-..."

# Or using API_KEY (compatible)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Optional: Set Custom Endpoint

```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 3. Start Alpha

```bash
source venv/bin/activate
python -m alpha.interface.cli
```

## Verify Configuration

Run configuration test:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

## Complete Examples

### Using Official API

```bash
#!/bin/bash
export ANTHROPIC_AUTH_TOKEN="sk-ant-api03-your-key-here"

source venv/bin/activate
python -m alpha.interface.cli
```

### Using Custom Endpoint

```bash
#!/bin/bash
export ANTHROPIC_AUTH_TOKEN="your-custom-token"
export ANTHROPIC_BASE_URL="https://api.your-company.com"

source venv/bin/activate
python -m alpha.interface.cli
```

## FAQ

### Q: Why support two environment variables?

A: `ANTHROPIC_AUTH_TOKEN` is the recommended standard name, while `ANTHROPIC_API_KEY` is for backward compatibility. The configuration will automatically fallback.

### Q: Is ANTHROPIC_BASE_URL required?

A: Not required. If not set, the Anthropic SDK will use the default official API address.

### Q: How to switch to OpenAI?

A: Modify the `default_provider` in config.yaml to `"openai"`, and set the `OPENAI_API_KEY` environment variable.

### Q: Can I use multiple providers simultaneously?

A: Yes. The configuration file supports both OpenAI and Anthropic simultaneously, just set the corresponding API keys.

## Technical Details

### Environment Variable Parsing

The configuration system supports the following syntax:

```yaml
# Simple variable
api_key: "${ANTHROPIC_API_KEY}"

# Fallback syntax
api_key: "${VAR1:-${VAR2}}"

# Default value
api_key: "${VAR1:-default-value}"
```

### Base URL Passing

The `base_url` parameter is automatically passed to the Anthropic SDK:

```python
client = AsyncAnthropic(
    api_key=api_key,
    base_url=base_url  # If set
)
```

## More Information

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Claude Models Overview](https://docs.anthropic.com/claude/docs/models-overview)
- [Alpha Configuration Documentation](features.md)
