#!/usr/bin/env python3
"""
WebSocket Debug Test
Test WebSocket endpoint directly using Starlette TestClient
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from starlette.testclient import TestClient
from alpha.api.server import create_app

def test_websocket():
    """Test WebSocket endpoint"""
    print("Creating app...")
    app = create_app()

    print("Creating test client...")
    client = TestClient(app)

    print("Testing WebSocket endpoint...")
    try:
        with client.websocket_connect("/api/v1/ws/chat") as websocket:
            print("✓ WebSocket connected!")

            # Receive welcome message
            data = websocket.receive_json()
            print(f"✓ Welcome: {data}")

            # Send test message
            websocket.send_json({"type": "message", "content": "Hello"})
            print("✓ Message sent")

            # Receive responses
            count = 0
            while True:
                data = websocket.receive_json()
                msg_type = data.get('type')
                print(f"  << {msg_type}")
                count += 1
                if msg_type == 'done' or count > 10:
                    break

            print(f"✓ Test PASSED! (received {count} messages)")
            return True

    except Exception as e:
        print(f"✗ Test FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_websocket()
    sys.exit(0 if result else 1)
