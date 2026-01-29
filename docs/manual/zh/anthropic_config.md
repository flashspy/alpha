# Anthropic Configuration Guide

## Overview

Alpha默认使用Anthropic Claude作为LLM提供商，支持灵活的配置方式。

## 环境变量配置

### 方式1: 使用 ANTHROPIC_AUTH_TOKEN (推荐)

```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # 可选
```

### 方式2: 使用 ANTHROPIC_API_KEY (兼容)

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # 可选
```

### Fallback机制

配置文件使用以下fallback顺序:
1. 优先使用 `ANTHROPIC_AUTH_TOKEN`
2. 如果未设置,则使用 `ANTHROPIC_API_KEY`
3. 如果都未设置,启动会失败

## 配置文件说明

### config.yaml

```yaml
llm:
  default_provider: "anthropic"
  providers:
    anthropic:
      # API密钥 (支持fallback)
      api_key: "${ANTHROPIC_AUTH_TOKEN:-${ANTHROPIC_API_KEY}}"

      # 可选: 自定义API端点
      base_url: "${ANTHROPIC_BASE_URL}"

      # 模型配置
      model: "claude-3-5-sonnet-20241022"
      max_tokens: 8192
      temperature: 0.7
```

## 支持的模型

### Claude 3.5 系列 (推荐)
- `claude-3-5-sonnet-20241022` - 最新Sonnet (默认)
- `claude-3-5-sonnet-20240620` - 早期Sonnet

### Claude 3 系列
- `claude-3-opus-20240229` - 最强大
- `claude-3-sonnet-20240229` - 平衡
- `claude-3-haiku-20240307` - 最快

## 自定义API端点

如果使用自建的Anthropic兼容API,可以设置自定义端点:

```bash
export ANTHROPIC_BASE_URL="https://your-custom-api.example.com"
```

配置文件会自动应用此设置。

## 快速开始

### 1. 设置API密钥

```bash
# 使用AUTH_TOKEN (推荐)
export ANTHROPIC_AUTH_TOKEN="sk-ant-..."

# 或使用API_KEY (兼容)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. 可选: 设置自定义端点

```bash
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### 3. 启动Alpha

```bash
source venv/bin/activate
python -m alpha.interface.cli
```

## 验证配置

运行配置测试:

```bash
source venv/bin/activate
PYTHONPATH=. python tests/test_config.py
```

## 完整示例

### 使用官方API

```bash
#!/bin/bash
export ANTHROPIC_AUTH_TOKEN="sk-ant-api03-your-key-here"

source venv/bin/activate
python -m alpha.interface.cli
```

### 使用自定义端点

```bash
#!/bin/bash
export ANTHROPIC_AUTH_TOKEN="your-custom-token"
export ANTHROPIC_BASE_URL="https://api.your-company.com"

source venv/bin/activate
python -m alpha.interface.cli
```

## 常见问题

### Q: 为什么支持两个环境变量?

A: `ANTHROPIC_AUTH_TOKEN` 是推荐的标准名称,`ANTHROPIC_API_KEY` 是为了向后兼容。配置会自动fallback。

### Q: ANTHROPIC_BASE_URL必须设置吗?

A: 不必须。如果不设置,Anthropic SDK会使用默认的官方API地址。

### Q: 如何切换到OpenAI?

A: 修改config.yaml中的`default_provider`为`"openai"`,并设置`OPENAI_API_KEY`环境变量。

### Q: 可以同时使用多个provider吗?

A: 可以。配置文件同时支持OpenAI和Anthropic,只需设置对应的API密钥即可。

## 技术细节

### 环境变量解析

配置系统支持以下语法:

```yaml
# 简单变量
api_key: "${ANTHROPIC_API_KEY}"

# Fallback语法
api_key: "${VAR1:-${VAR2}}"

# 默认值
api_key: "${VAR1:-default-value}"
```

### Base URL传递

`base_url`参数会自动传递给Anthropic SDK:

```python
client = AsyncAnthropic(
    api_key=api_key,
    base_url=base_url  # 如果设置了的话
)
```

## 更多信息

- [Anthropic API文档](https://docs.anthropic.com/)
- [Claude模型说明](https://docs.anthropic.com/claude/docs/models-overview)
- [Alpha配置文档](features.md)
