#!/bin/bash
#
# Alpha Client Startup Script
#
# Connects to Alpha server via WebSocket
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check virtual environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please run from project directory with venv"
    exit 1
fi

# Activate virtual environment and start client
cd "$PROJECT_ROOT"
source venv/bin/activate

python3 -m alpha.client.cli "$@"
