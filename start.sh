#!/bin/bash
#
# Alpha AI Assistant - Quick Start Script
#
# This script helps you quickly start Alpha with any configured LLM provider
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║              Alpha AI Assistant - Quick Start               ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check if dependencies are installed
if ! python -c "import yaml" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

echo

# Read default provider from config.yaml
if [ -f "config.yaml" ]; then
    DEFAULT_PROVIDER=$(python -c "import yaml; print(yaml.safe_load(open('config.yaml'))['llm']['default_provider'])" 2>/dev/null || echo "unknown")
else
    DEFAULT_PROVIDER="unknown"
fi

# Show current provider configuration
echo "Configuration:"
echo -e "  ${BLUE}Provider:${NC} $DEFAULT_PROVIDER"
echo

# Check provider-specific API key
case "$DEFAULT_PROVIDER" in
    "deepseek")
        if [ -n "$DEEPSEEK_API_KEY" ]; then
            echo -e "  ${GREEN}✓${NC} DeepSeek API Key: ${DEEPSEEK_API_KEY:0:20}..."
        else
            echo -e "${RED}Error: DeepSeek API key not found!${NC}"
            echo
            echo "Please set the DeepSeek API key:"
            echo "  export DEEPSEEK_API_KEY=\"your-key\""
            echo
            echo "Get your key at: https://platform.deepseek.com/api_keys"
            echo
            exit 1
        fi
        ;;
    "anthropic")
        if [ -n "$ANTHROPIC_AUTH_TOKEN" ] || [ -n "$ANTHROPIC_API_KEY" ]; then
            if [ -n "$ANTHROPIC_AUTH_TOKEN" ]; then
                echo -e "  ${GREEN}✓${NC} Anthropic API Key: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
            else
                echo -e "  ${GREEN}✓${NC} Anthropic API Key: ${ANTHROPIC_API_KEY:0:20}..."
            fi
            if [ -n "$ANTHROPIC_BASE_URL" ]; then
                echo -e "  ${GREEN}✓${NC} Base URL: $ANTHROPIC_BASE_URL"
            fi
        else
            echo -e "${RED}Error: Anthropic API key not found!${NC}"
            echo
            echo "Please set the Anthropic API key:"
            echo "  export ANTHROPIC_API_KEY=\"your-key\""
            echo "  # or"
            echo "  export ANTHROPIC_AUTH_TOKEN=\"your-key\""
            echo
            echo "Optional: Set custom API endpoint"
            echo "  export ANTHROPIC_BASE_URL=\"https://api.anthropic.com\""
            echo
            exit 1
        fi
        ;;
    "openai")
        if [ -n "$OPENAI_API_KEY" ]; then
            echo -e "  ${GREEN}✓${NC} OpenAI API Key: ${OPENAI_API_KEY:0:20}..."
        else
            echo -e "${RED}Error: OpenAI API key not found!${NC}"
            echo
            echo "Please set the OpenAI API key:"
            echo "  export OPENAI_API_KEY=\"your-key\""
            echo
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Error: Unknown provider '$DEFAULT_PROVIDER'${NC}"
        echo
        echo "Please check config.yaml and set default_provider to one of:"
        echo "  - deepseek (Recommended - Most cost-effective)"
        echo "  - anthropic"
        echo "  - openai"
        echo
        exit 1
        ;;
esac

echo
echo "Starting Alpha AI Assistant..."
echo "Type 'help' for commands, 'quit' to exit"
echo
echo "════════════════════════════════════════════════════════════════"
echo

# Start Alpha
python -m alpha.interface.cli
