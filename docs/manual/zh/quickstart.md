# Alpha AI Assistant - Quick Start Guide

## Installation

### 1. Clone or navigate to project directory
```bash
cd /path/to/agents-7b5dad6160
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
```bash
cp config.example.yaml config.yaml
```

Set environment variables (choose one method):

**Method 1: Using ANTHROPIC_AUTH_TOKEN (Recommended)**
```bash
export ANTHROPIC_AUTH_TOKEN="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
```

**Method 2: Using ANTHROPIC_API_KEY (Compatible)**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional
```

**For OpenAI (if needed)**
```bash
export OPENAI_API_KEY="your-openai-key-here"
```

## Usage

### Start Interactive CLI
```bash
python -m alpha.interface.cli
```

### Example Interaction
```
You> Hello, what can you do?

Alpha> Hi! I'm Alpha, your AI assistant. I can help you with:
- Executing shell commands
- Reading and writing files
- Searching for information
- General questions and tasks

What would you like me to help with?

You> List files in the current directory

Alpha> TOOL: shell
PARAMS: {"command": "ls -la"}

Executing tool: shell
Tool succeeded: total 48
drwxr-xr-x 10 user staff  320 Jan 29 12:00 .
...

You> quit
```

### Available Commands
- `help` - Show help message
- `status` - Show system status
- `clear` - Clear conversation history
- `quit` or `exit` - Exit Alpha

## Testing

Run tests to verify installation:
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v
```

## Project Structure
```
alpha/
├── core/           # Core runtime engine
├── events/         # Event system
├── tasks/          # Task management
├── memory/         # Memory system
├── llm/            # LLM integration
├── tools/          # Tool system
├── interface/      # User interfaces
└── utils/          # Utilities

docs/               # Documentation
tests/              # Test suite
config.yaml         # Configuration (create from example)
```

## Troubleshooting

### Import errors
Make sure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### API key errors
Verify your API keys are set in `config.yaml` or environment variables:
```bash
echo $OPENAI_API_KEY
```

### Database errors
Create the data directory:
```bash
mkdir -p data
```

### Permission errors (shell tool)
Ensure the shell commands you're running are safe and have proper permissions.

## Next Steps

1. Read [Architecture Documentation](docs/architecture.md)
2. Check [Requirements](docs/requirements.md)
3. Review [Phase 1 Report](docs/phase1_report.md)
4. Explore the code in `alpha/` directory

## Support

For issues, check:
- Documentation in `docs/`
- Test examples in `tests/`
- Code comments and docstrings
