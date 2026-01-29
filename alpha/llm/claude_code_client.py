"""
Custom Anthropic client that mimics Claude Code exactly.
"""

import httpx
import json
from typing import List, Dict, Any, AsyncIterator


class ClaudeCodeClient:
    """
    Custom client that mimics Claude Code requests exactly.
    Bypasses Anthropic SDK to avoid x-stainless-* headers.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)

    def _get_headers(self) -> Dict[str, str]:
        """Get Claude Code compatible headers."""
        return {
            "User-Agent": "claude-code/1.0.0",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            # No x-stainless-* headers at all
        }

    async def create_message(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = None,
    ) -> Dict[str, Any]:
        """Create a message (non-streaming)."""

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system:
            payload["system"] = system

        url = f"{self.base_url}/v1/messages"
        headers = self._get_headers()

        response = await self.client.post(
            url,
            json=payload,
            headers=headers
        )

        # Debug: print response if error
        if response.status_code >= 400:
            print(f"❌ Status: {response.status_code}")
            print(f"Response: {response.text}")

        response.raise_for_status()
        return response.json()

    async def stream_message(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str = None,
    ) -> AsyncIterator[str]:
        """Stream a message."""

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "stream": True,
        }

        if system:
            payload["system"] = system

        url = f"{self.base_url}/v1/messages"
        headers = self._get_headers()

        async with self.client.stream(
            "POST",
            url,
            json=payload,
            headers=headers
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix

                    if data == "[DONE]":
                        break

                    try:
                        event = json.loads(data)

                        # Handle content block delta
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
