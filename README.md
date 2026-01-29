# Alpha AI Assistant

English | [简体中文](README.zh.md)

A personal super AI assistant that runs 24/7 to help you accomplish various tasks.

## Features

- 🤖 LLM-based Agent Architecture
- 🔧 Extensible Tool System (Shell, File, Browser, Code, HTTP, DateTime, Calculator)
- 🧠 Long-term Memory & Personalization
- ⚡ Asynchronous Task Management
- 🔄 Continuous Running & Auto Recovery
- 💬 Multiple Interfaces (CLI, API)
- 🌐 Multi-LLM Support (Anthropic Claude, OpenAI GPT, DeepSeek)
- 🔌 Custom API Endpoint Support
- 📅 Advanced Task Scheduler with Cron Support

## Architecture

See [Architecture Design](docs/en/architecture.md) for details.

## System Requirements

- Python 3.10+
- At least one API key: Anthropic, OpenAI, or DeepSeek

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration file
cp config.example.yaml config.yaml

# Configure API key (choose one)

# Option 1: Use Anthropic Claude
export ANTHROPIC_AUTH_TOKEN="your-api-key"
# or
export ANTHROPIC_API_KEY="your-api-key"

# Option 2: Use DeepSeek (Most Cost-Effective)
export DEEPSEEK_API_KEY="your-deepseek-api-key"

# Option 3: Use OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Custom API endpoint
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

## Usage

```bash
# Start interactive CLI
python -m alpha.interface.cli

# Or use quick start script
./start.sh

# Execute specific task
python -m alpha.main --task "Summarize AI news"

# Run in background
python -m alpha.main --daemon
```

## Example Interaction

```
You> List files in current directory

Alpha> I'll list the files in your current directory.

[Files listed here...]

You> exit
```

## Available Commands

- `help` - Show help message
- `status` - Show system status
- `clear` - Clear conversation history
- `quit` or `exit` - Exit Alpha

## LLM Provider Comparison

Alpha supports multiple LLM providers. Choose based on your needs:

| Provider | Speed | Cost | Chinese | Coding | Reasoning | Best For |
|----------|-------|------|---------|--------|-----------|----------|
| **DeepSeek** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Cost-effective, Chinese, Daily use |
| **Claude** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Complex reasoning, Code generation |
| **GPT-4** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General tasks, English-first |

### Pricing Comparison (per million tokens)

| Provider | Input | Output | Value |
|----------|-------|--------|-------|
| DeepSeek | $0.14 | $0.28 | 🏆 Best |
| Claude Sonnet | $3.00 | $15.00 | Fair |
| GPT-4 | $5.00 | $15.00 | Lower |

### Quick Testing

```bash
# Test DeepSeek
export DEEPSEEK_API_KEY="your-key"
python test_deepseek.py

# Test Anthropic fallback mechanism
python test_fallback.py

# Check API configuration
./check_api_config.sh
```

### Switching Providers

In `config.yaml`:

```yaml
llm:
  default_provider: "deepseek"  # Change to: anthropic, openai, deepseek
```

Or dynamically in code:

```python
# Use DeepSeek for general chat
response = await llm_service.complete(messages, provider="deepseek")

# Use Claude for complex tasks
response = await llm_service.complete(messages, provider="anthropic")
```

## Available DeepSeek Models

1. **deepseek-chat** - General conversation model
   - Best for daily conversations and general tasks
   - Most cost-effective

2. **deepseek-reasoner** (DeepSeek-R1)
   - Advanced reasoning capabilities
   - Best for complex analysis and math problems

3. **deepseek-coder**
   - Specialized for code generation
   - Best for programming tasks

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black alpha/
isort alpha/
```

## Project Structure

```
alpha/
├── core/           # Core runtime engine
├── llm/            # LLM integration
├── tools/          # Tool system
├── memory/         # Memory system
├── tasks/          # Task management
├── scheduler/      # Task scheduler with cron support
├── events/         # Event system
├── interface/      # User interfaces
└── utils/          # Utility functions
```

## Documentation

### English Documentation
- [Quick Start](docs/en/quickstart.md) - Get started in 5 minutes
- [Features](docs/en/features.md) - Complete feature guide
- [Requirements](docs/en/requirements.md) - Requirements definition
- [Architecture](docs/en/architecture.md) - System architecture
- [Anthropic Config](docs/en/anthropic_config.md) - Anthropic configuration
- [DeepSeek Guide](docs/DEEPSEEK_GUIDE.md) - DeepSeek API integration
- [API Setup](docs/API_SETUP.md) - Multi-provider setup and troubleshooting
- [Phase 1 Report](docs/en/phase1_report.md) - Phase 1 development report
- [Project Summary](docs/en/project_summary.md) - Project summary

### 中文文档
- [快速开始](docs/zh/quickstart.md) - 5分钟上手
- [功能详解](docs/zh/features.md) - 完整功能说明
- [需求文档](docs/zh/requirements.md) - 需求定义
- [架构设计](docs/zh/architecture.md) - 系统架构
- [Anthropic配置](docs/zh/anthropic_config.md) - Anthropic配置指南
- [DeepSeek集成](docs/DEEPSEEK_GUIDE.md) - DeepSeek API使用说明
- [API配置](docs/API_SETUP.md) - 多provider配置和故障排查
- [Phase 1报告](docs/zh/phase1_report.md) - 第一阶段开发报告
- [项目总结](docs/zh/project_summary.md) - 项目总结

### Project Documents
- [Changelog](CHANGELOG.md)
- [Release Notes](RELEASE_NOTES.md)
- [Next Steps](NEXT_STEPS.md)
- [Completion Report](PROJECT_COMPLETE.md)
- [Update Summary](UPDATE_SUMMARY.md)

## Status

✅ **Phase 1 Enhanced - Tools Expansion** (Completed)

- [x] Requirements definition
- [x] Architecture design
- [x] Core engine implementation
- [x] LLM integration (OpenAI, Anthropic, DeepSeek)
- [x] Basic tools (Shell, File, Search)
- [x] Utility tools (HTTP, DateTime, Calculator)
- [x] CLI interface
- [x] Test suite (61 tests, 100% passing)
- [x] Complete documentation

🟡 **Phase 2 - Autonomous Operation** (50% Complete)

- [x] Task scheduler with cron support
- [x] Multi-provider LLM support with fallback
- [x] DeepSeek integration
- [ ] Vector database (ChromaDB)
- [ ] Self-monitoring and log analysis

## Troubleshooting

### Import Errors
Ensure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API Key Errors
Check if environment variables are set:
```bash
echo $DEEPSEEK_API_KEY
echo $ANTHROPIC_API_KEY
```

### Database Errors
Create data directory:
```bash
mkdir -p data
```

### DeepSeek Setup
1. Visit [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. Create API key
3. Set environment variable: `export DEEPSEEK_API_KEY="your-key"`
4. Test: `python test_deepseek.py`

### API Configuration
Run the configuration checker:
```bash
./check_api_config.sh
```

For detailed troubleshooting, see [API Setup Guide](docs/API_SETUP.md).

## Why DeepSeek?

DeepSeek is now the **default provider** for Alpha due to:

- 💰 **Most Cost-Effective**: 20x cheaper than Claude, 30x cheaper than GPT-4
- 🇨🇳 **Excellent Chinese Support**: Best-in-class Chinese understanding
- 🧠 **Strong Reasoning**: DeepSeek-R1 rivals top models in reasoning tasks
- 🚀 **Fast Response**: Quick inference with streaming support
- 🔓 **Open Source**: Transparent model architecture

### Cost Comparison Example

For 1 million tokens of conversation:
- DeepSeek: **$0.28** (output) + $0.14 (input) = **$0.42**
- Claude: **$15** (output) + $3 (input) = **$18**
- GPT-4: **$15** (output) + $5 (input) = **$20**

**DeepSeek saves you 40-50x on API costs!**

## Multi-Provider Strategy

You can use different providers for different tasks:

```python
# Use DeepSeek for daily chat (cost-effective)
await llm_service.complete(messages, provider="deepseek")

# Use Claude for complex code generation (high quality)
await llm_service.complete(messages, provider="anthropic")

# Use DeepSeek Reasoner for math/logic problems
await llm_service.complete(messages, provider="deepseek", model="deepseek-reasoner")

# Use DeepSeek Coder for programming tasks
await llm_service.complete(messages, provider="deepseek", model="deepseek-coder")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

---

**Current Version**: v0.2.0
**Status**: Production Ready - Task Scheduling & Enhanced Tools
**Quality Rating**: ⭐⭐⭐⭐⭐
**Default Provider**: DeepSeek (Most Cost-Effective)
**Test Coverage**: 61 tests (100% passing)
