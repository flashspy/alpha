"""
Vision Provider - LLM Provider with Vision Support

Extends LLM providers to support image understanding capabilities.
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from alpha.llm.service import LLMProvider, LLMResponse
from alpha.llm.vision_message import VisionMessage, Message
from alpha.llm.claude_code_client import ClaudeCodeClient

logger = logging.getLogger(__name__)


@dataclass
class VisionResponse:
    """Response from vision-capable LLM"""

    content: str
    model: str
    tokens_used: int
    finish_reason: str
    input_tokens: int = 0  # Separate tracking for vision tokens
    output_tokens: int = 0
    cost_usd: float = 0.0  # Estimated cost


class ClaudeVisionProvider(LLMProvider):
    """
    Claude Vision Provider using Claude 3.5 Sonnet

    Supports multimodal messages with images.
    """

    # Vision-capable models
    VISION_MODELS = {
        "claude-3-5-sonnet-20241022",  # Latest sonnet with vision
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    }

    # Pricing (per million tokens)
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.0,  # $3 per 1M input tokens
            "output": 15.0,  # $15 per 1M output tokens
        },
    }

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key, model, **kwargs)

        if model not in self.VISION_MODELS:
            logger.warning(
                f"Model {model} may not support vision. "
                f"Recommended: {', '.join(self.VISION_MODELS)}"
            )

        self.client = ClaudeCodeClient(api_key)
        self.logger = logger

    def supports_vision(self) -> bool:
        """Check if current model supports vision"""
        return self.model in self.VISION_MODELS

    def _calculate_cost(
        self, input_tokens: int, output_tokens: int, model: str
    ) -> float:
        """Calculate API cost in USD"""
        if model not in self.PRICING:
            return 0.0

        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _convert_messages(self, messages: List[VisionMessage]) -> List[Dict]:
        """Convert VisionMessage objects to Claude API format"""
        api_messages = []

        for msg in messages:
            api_messages.append(msg.to_dict())

        return api_messages

    async def complete(
        self,
        messages: List[VisionMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system: Optional[str] = None,
        **kwargs,
    ) -> VisionResponse:
        """
        Generate completion with vision support

        Args:
            messages: List of VisionMessage objects (can include images)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            VisionResponse with content and token usage
        """
        if not self.supports_vision():
            logger.warning(
                f"Model {self.model} may not support vision, "
                "images may be ignored"
            )

        # Check if any message has images
        has_images = any(msg.has_images() for msg in messages)

        if has_images:
            self.logger.info(
                f"Sending vision request with {len(messages)} messages "
                f"(contains images)"
            )

        # Convert messages to API format
        api_messages = self._convert_messages(messages)

        # Call Claude API
        response = await self.client.create_message(
            model=self.model,
            messages=api_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
        )

        # Parse response
        content = response["content"][0]["text"]
        usage = response["usage"]

        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens

        # Calculate cost
        cost = self._calculate_cost(input_tokens, output_tokens, self.model)

        self.logger.info(
            f"Vision API response: {total_tokens} tokens "
            f"(input: {input_tokens}, output: {output_tokens}), "
            f"cost: ${cost:.4f}"
        )

        return VisionResponse(
            content=content,
            model=self.model,
            tokens_used=total_tokens,
            finish_reason=response["stop_reason"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )

    async def stream_complete(self, messages: List[VisionMessage], **kwargs):
        """
        Stream completion (vision models support streaming)

        Note: For simplicity, using non-streaming for now.
        Full streaming implementation can be added later.
        """
        # For now, use non-streaming and yield the complete response
        response = await self.complete(messages, **kwargs)
        yield response.content

    async def analyze_image(
        self,
        image_base64: str,
        prompt: str,
        media_type: str = "image/png",
        **kwargs,
    ) -> VisionResponse:
        """
        Convenience method to analyze a single image

        Args:
            image_base64: Base64 encoded image
            prompt: Analysis prompt/question
            media_type: Image media type (image/png, image/jpeg, etc.)
            **kwargs: Additional parameters

        Returns:
            VisionResponse with analysis
        """
        message = VisionMessage.from_text_and_image(
            role="user", text=prompt, image_base64=image_base64, media_type=media_type
        )

        return await self.complete(messages=[message], **kwargs)

    async def analyze_images(
        self,
        images: List[tuple[str, str]],  # [(base64, media_type), ...]
        prompt: str,
        **kwargs,
    ) -> VisionResponse:
        """
        Analyze multiple images at once

        Args:
            images: List of (base64, media_type) tuples
            prompt: Analysis prompt/question
            **kwargs: Additional parameters

        Returns:
            VisionResponse with analysis
        """
        message = VisionMessage.from_text_and_images(
            role="user", text=prompt, images=images
        )

        return await self.complete(messages=[message], **kwargs)
