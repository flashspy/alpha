#!/bin/bash
#
# Alpha Server Stop Script
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PID_FILE="$PROJECT_ROOT/data/alpha.pid"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}Alpha server is not running (no PID file found)${NC}"
    exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping Alpha server (PID: $PID)..."
    kill -TERM "$PID"

    # Wait for shutdown
    for i in {1..10}; do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        echo "Force stopping..."
        kill -9 "$PID"
    fi

    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Alpha server stopped${NC}"
else
    echo -e "${YELLOW}Alpha server process not found (stale PID file)${NC}"
    rm -f "$PID_FILE"
fi
