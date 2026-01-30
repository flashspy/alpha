# Alpha AI Assistant - Dependencies Guide

## Quick Start (Minimal Installation)

The default `requirements.txt` includes only essential dependencies for core functionality:

```bash
pip install -r requirements.txt
```

This installs:
- Core libraries (yaml, aiohttp)
- LLM provider (OpenAI-compatible API for DeepSeek/OpenAI)
- CLI interface (rich)
- Logging (structlog)
- Web API server (FastAPI, uvicorn, pydantic)
- System monitoring (psutil)
- Search tools (ddgs)
- Date/time utilities

## Optional Features

### Vector Memory (Semantic Search)

If you need vector storage and semantic search capabilities:

```bash
pip install -r requirements-vector.txt
```

This adds:
- **chromadb**: Vector database for semantic search
- **sentence-transformers**: Local embeddings (no API key needed)
- **voyageai**: Voyage AI embeddings (requires API key)

**Note**: Vector memory dependencies are **large** (~2GB+) and include PyTorch and transformers.
Only install if you specifically need semantic search features.

## What Was Removed?

The following packages were removed from requirements.txt because they were **not used**:

- `anthropic` - Not currently integrated
- `aiosqlite` - Using standard library sqlite3 instead
- `python-dotenv` - Environment handling done differently
- `click` - Using rich for CLI instead
- `python-multipart` - Handled internally by FastAPI

## Development Dependencies

For development and testing:

```bash
pip install -r requirements-dev.txt
```

## Dependency Size Comparison

| Configuration | Install Size | Install Time (approx) |
|--------------|-------------|----------------------|
| Minimal (requirements.txt) | ~200MB | 1-2 minutes |
| With Vector Memory | ~2.5GB | 5-10 minutes |

## Troubleshooting

If you see warnings about missing vector memory:
```
Vector Memory not available: No module named 'chromadb'
```

This is **normal** if you haven't installed `requirements-vector.txt`. The system will continue working without semantic search features.

To enable vector memory, install the optional dependencies:
```bash
pip install -r requirements-vector.txt
```
