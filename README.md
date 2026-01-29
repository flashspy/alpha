# Alpha AI Assistant

Personal super AI assistant that runs 24/7 to help with various tasks.

## Features

- 🤖 Agent-based architecture powered by LLM
- 🔧 Extensible tool system (Shell, File, Browser, Code)
- 🧠 Long-term memory and personalization
- ⚡ Async task management
- 🔄 Continuous operation with auto-recovery
- 💬 Multiple interfaces (CLI, API)

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed system design.

## Requirements

- Python 3.10+
- OpenAI API key or Anthropic API key

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys
```

## Usage

```bash
# Start alpha in interactive mode
python -m alpha.main

# Run specific task
python -m alpha.main --task "summarize news about AI"

# Start as daemon
python -m alpha.main --daemon
```

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
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
├── events/         # Event system
├── interface/      # User interfaces
├── utils/          # Utilities
└── main.py         # Entry point
```

## Documentation

- [Quick Start Guide](docs/quickstart.md) - 快速开始
- [Features & Usage](docs/features.md) - 功能详解和使用指南
- [Requirements](docs/requirements.md) - 需求文档
- [Architecture](docs/architecture.md) - 架构设计
- [Phase 1 Report](docs/phase1_report.md) - 第一阶段开发报告

## Status

✅ **Phase 1 - Foundation** (Completed)

- [x] Requirements definition
- [x] Architecture design
- [x] Core engine implementation
- [x] LLM integration (OpenAI, Anthropic)
- [x] Basic tools (Shell, File, Search)
- [x] CLI interface
- [x] Test suite (4/4 passing)
- [x] Documentation

## License

MIT
