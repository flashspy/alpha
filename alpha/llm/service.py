"""
Alpha - LLM Service

Interface with large language models for decision making.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Chat message."""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM response."""
    content: str
    model: str
    tokens_used: int
    finish_reason: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion for messages.

        Args:
            messages: List of chat messages
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def stream_complete(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion for messages.

        Args:
            messages: List of chat messages
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    async def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise

    async def stream_complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion using OpenAI API."""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            stream = await client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}", exc_info=True)
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic API provider with automatic fallback."""

    async def complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Anthropic API."""
        from alpha.llm.claude_code_client import ClaudeCodeClient

        # Get configured base URL
        base_url = self.config.get("base_url", "https://api.anthropic.com")

        # Try configured endpoint first
        try:
            return await self._try_complete(
                messages, base_url, temperature, max_tokens
            )
        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's a credential/authorization error
            if "400" in error_msg or "403" in error_msg or "authorized" in error_msg or "credential" in error_msg:
                logger.warning(f"Request to {base_url} failed: {e}")

                # If using non-official endpoint, try fallback to official API
                if base_url != "https://api.anthropic.com":
                    logger.info("Falling back to official Anthropic API...")
                    try:
                        return await self._try_complete(
                            messages, "https://api.anthropic.com", temperature, max_tokens
                        )
                    except Exception as fallback_error:
                        logger.error(f"Fallback also failed: {fallback_error}")
                        raise Exception(
                            f"Both {base_url} and official API failed. "
                            f"Original error: {e}. Fallback error: {fallback_error}"
                        )
                else:
                    raise
            else:
                raise

    async def _try_complete(
        self,
        messages: List[Message],
        base_url: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Attempt to complete using specified base URL."""
        from alpha.llm.claude_code_client import ClaudeCodeClient

        client = ClaudeCodeClient(api_key=self.api_key, base_url=base_url)

        try:
            # Separate system message
            system_msg = None
            user_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    user_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            response = await client.create_message(
                model=self.model,
                messages=user_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg
            )

            return LLMResponse(
                content=response["content"][0]["text"],
                model=response["model"],
                tokens_used=response["usage"]["input_tokens"] + response["usage"]["output_tokens"],
                finish_reason=response["stop_reason"]
            )
        finally:
            await client.close()

    async def stream_complete(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion using Anthropic API with fallback."""
        from alpha.llm.claude_code_client import ClaudeCodeClient

        base_url = self.config.get("base_url", "https://api.anthropic.com")

        # Try configured endpoint first
        try:
            async for chunk in self._try_stream_complete(
                messages, base_url, temperature, max_tokens
            ):
                yield chunk
            return
        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's a credential/authorization error
            if "400" in error_msg or "403" in error_msg or "authorized" in error_msg or "credential" in error_msg:
                logger.warning(f"Streaming to {base_url} failed: {e}")

                # If using non-official endpoint, try fallback to official API
                if base_url != "https://api.anthropic.com":
                    logger.info("Falling back to official Anthropic API for streaming...")
                    try:
                        async for chunk in self._try_stream_complete(
                            messages, "https://api.anthropic.com", temperature, max_tokens
                        ):
                            yield chunk
                        return
                    except Exception as fallback_error:
                        logger.error(f"Fallback streaming also failed: {fallback_error}")
                        raise Exception(
                            f"Both {base_url} and official API failed. "
                            f"Original error: {e}. Fallback error: {fallback_error}"
                        )
                else:
                    raise
            else:
                raise

    async def _try_stream_complete(
        self,
        messages: List[Message],
        base_url: str,
        temperature: float,
        max_tokens: int
    ) -> AsyncIterator[str]:
        """Attempt to stream using specified base URL."""
        from alpha.llm.claude_code_client import ClaudeCodeClient

        client = ClaudeCodeClient(api_key=self.api_key, base_url=base_url)

        try:
            # Separate system message
            system_msg = None
            user_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_msg = msg.content
                else:
                    user_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            async for text in client.stream_message(
                model=self.model,
                messages=user_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_msg
            ):
                yield text
        finally:
            await client.close()


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek API provider with multi-model support and automatic model selection.

    DeepSeek API is OpenAI-compatible, so we use the same implementation
    but with DeepSeek-specific base URL and models.
    """

    def __init__(self, api_key: str, model: str = None, **kwargs):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key
            model: Default model name (can be None if using auto-selection)
            **kwargs: Additional configuration (models_config, default_model, auto_select_model)
        """
        super().__init__(api_key, model, **kwargs)
        self.models_config = kwargs.get('models_config')
        self.default_model = kwargs.get('default_model', 'deepseek-chat')
        self.auto_select_model = kwargs.get('auto_select_model', False)

        # Initialize model selector if multi-model config is provided
        if self.models_config:
            from alpha.llm.model_selector import ModelSelector
            self.model_selector = ModelSelector(self.models_config)
        else:
            self.model_selector = None

    def _select_model(self, messages: List[Message]) -> str:
        """
        Select the best model for the given messages.

        Args:
            messages: Chat messages

        Returns:
            Selected model name
        """
        # Use explicit model if set
        if self.model:
            return self.model

        # Use auto-selection if enabled
        if self.auto_select_model and self.model_selector:
            # Convert Message objects to dicts for analyzer
            message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
            return self.model_selector.select_model(message_dicts, self.default_model)

        # Fall back to default model
        return self.default_model

    def _get_model_params(self, model_name: str) -> dict:
        """
        Get parameters for a specific model.

        Args:
            model_name: Model name

        Returns:
            Dictionary with max_tokens and temperature
        """
        if self.models_config and model_name in self.models_config:
            model_config = self.models_config[model_name]
            return {
                'max_tokens': model_config.max_tokens,
                'temperature': model_config.temperature
            }
        # Default parameters
        return {
            'max_tokens': self.config.get('max_tokens', 4096),
            'temperature': self.config.get('temperature', 0.7)
        }

    async def complete(
        self,
        messages: List[Message],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using DeepSeek API with automatic model selection."""
        try:
            from openai import AsyncOpenAI

            # Select the best model for this task
            selected_model = self._select_model(messages)
            model_params = self._get_model_params(selected_model)

            # Use provided parameters or fall back to model defaults
            actual_temperature = temperature if temperature is not None else model_params['temperature']
            actual_max_tokens = max_tokens if max_tokens is not None else model_params['max_tokens']

            logger.info(f"Using DeepSeek model: {selected_model} (temp={actual_temperature}, max_tokens={actual_max_tokens})")

            # DeepSeek uses OpenAI-compatible API
            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )

            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = await client.chat.completions.create(
                model=selected_model,
                messages=openai_messages,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens,
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                tokens_used=response.usage.total_tokens,
                finish_reason=response.choices[0].finish_reason
            )

        except Exception as e:
            logger.error(f"DeepSeek API error: {e}", exc_info=True)
            raise

    async def stream_complete(
        self,
        messages: List[Message],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream completion using DeepSeek API with automatic model selection."""
        try:
            from openai import AsyncOpenAI

            # Select the best model for this task
            selected_model = self._select_model(messages)
            model_params = self._get_model_params(selected_model)

            # Use provided parameters or fall back to model defaults
            actual_temperature = temperature if temperature is not None else model_params['temperature']
            actual_max_tokens = max_tokens if max_tokens is not None else model_params['max_tokens']

            logger.info(f"Streaming with DeepSeek model: {selected_model}")

            client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )

            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            stream = await client.chat.completions.create(
                model=selected_model,
                messages=openai_messages,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"DeepSeek streaming error: {e}", exc_info=True)
            raise


class LLMService:
    """
    LLM service manager.

    Features:
    - Multi-provider support
    - Automatic provider selection
    - Error handling and retry
    """

    def __init__(self, default_provider: str, providers: Dict[str, LLMProvider]):
        self.default_provider = default_provider
        self.providers = providers

    @classmethod
    def from_config(cls, llm_config):
        """Create LLM service from configuration."""
        providers = {}

        for name, config in llm_config.providers.items():
            if name == "openai":
                providers[name] = OpenAIProvider(
                    api_key=config.api_key,
                    model=config.model,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature
                )
            elif name == "anthropic":
                providers[name] = AnthropicProvider(
                    api_key=config.api_key,
                    model=config.model,
                    max_tokens=config.max_tokens,
                    temperature=config.temperature,
                    base_url=config.base_url
                )
            elif name == "deepseek":
                # Pass multi-model configuration to DeepSeek provider
                providers[name] = DeepSeekProvider(
                    api_key=config.api_key,
                    model=config.model,  # Can be None if using auto-selection
                    max_tokens=getattr(config, 'max_tokens', 4096),
                    temperature=getattr(config, 'temperature', 0.7),
                    models_config=config.models,
                    default_model=getattr(config, 'default_model', 'deepseek-chat'),
                    auto_select_model=getattr(config, 'auto_select_model', False)
                )

        return cls(
            default_provider=llm_config.default_provider,
            providers=providers
        )

    async def complete(
        self,
        messages: List[Message],
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion.

        Args:
            messages: Chat messages
            provider: Provider name (uses default if not specified)
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        provider_name = provider or self.default_provider
        llm_provider = self.providers.get(provider_name)

        if not llm_provider:
            raise ValueError(f"Provider not found: {provider_name}")

        logger.info(f"Generating completion with {provider_name}")
        return await llm_provider.complete(messages, **kwargs)

    async def stream_complete(
        self,
        messages: List[Message],
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream completion.

        Args:
            messages: Chat messages
            provider: Provider name (uses default if not specified)
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        provider_name = provider or self.default_provider
        llm_provider = self.providers.get(provider_name)

        if not llm_provider:
            raise ValueError(f"Provider not found: {provider_name}")

        logger.info(f"Streaming completion with {provider_name}")
        async for chunk in llm_provider.stream_complete(messages, **kwargs):
            yield chunk
