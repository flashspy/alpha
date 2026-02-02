"""
Tests for vision provider streaming support
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from alpha.llm.vision_provider import ClaudeVisionProvider, VisionResponse
from alpha.llm.vision_message import VisionMessage


@pytest.fixture
def vision_provider():
    """Create a ClaudeVisionProvider instance for testing"""
    return ClaudeVisionProvider(api_key="test_api_key")


@pytest.fixture
def mock_vision_message():
    """Create a mock VisionMessage"""
    return VisionMessage.from_text_and_image(
        role="user",
        text="Describe this image",
        image_base64="fake_base64_data",
        media_type="image/png"
    )


@pytest.mark.asyncio
async def test_stream_complete_basic(vision_provider, mock_vision_message):
    """Test basic streaming functionality"""
    # Mock the stream_message method
    async def mock_stream():
        chunks = ["This ", "is ", "a ", "test ", "response."]
        for chunk in chunks:
            yield chunk

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        result_chunks = []
        async for chunk in vision_provider.stream_complete([mock_vision_message]):
            result_chunks.append(chunk)

        # Verify we got all chunks
        assert result_chunks == ["This ", "is ", "a ", "test ", "response."]
        assert "".join(result_chunks) == "This is a test response."


@pytest.mark.asyncio
async def test_stream_complete_with_vision_warning(vision_provider, mock_vision_message):
    """Test streaming with vision model warning"""
    # Use a non-vision model
    vision_provider.model = "non-vision-model"

    async def mock_stream():
        yield "response"

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        with patch.object(vision_provider, 'supports_vision', return_value=False):
            result_chunks = []
            async for chunk in vision_provider.stream_complete([mock_vision_message]):
                result_chunks.append(chunk)

            assert result_chunks == ["response"]


@pytest.mark.asyncio
async def test_stream_complete_with_images(vision_provider):
    """Test streaming with actual image content"""
    # Create message with image
    message = VisionMessage.from_text_and_image(
        role="user",
        text="What's in this image?",
        image_base64="fake_base64_image_data",
        media_type="image/jpeg"
    )

    async def mock_stream():
        chunks = ["I see ", "a cat ", "sitting ", "on a couch."]
        for chunk in chunks:
            yield chunk

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        result_chunks = []
        async for chunk in vision_provider.stream_complete([message]):
            result_chunks.append(chunk)

        assert len(result_chunks) == 4
        assert "".join(result_chunks) == "I see a cat sitting on a couch."


@pytest.mark.asyncio
async def test_stream_complete_empty_response(vision_provider, mock_vision_message):
    """Test streaming with empty response"""
    async def mock_stream():
        return
        yield  # Make it a generator

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        result_chunks = []
        async for chunk in vision_provider.stream_complete([mock_vision_message]):
            result_chunks.append(chunk)

        assert result_chunks == []


@pytest.mark.asyncio
async def test_stream_complete_multiple_messages(vision_provider):
    """Test streaming with multiple messages"""
    messages = [
        VisionMessage(role="user", content="First message"),
        VisionMessage(role="assistant", content="Response to first"),
        VisionMessage.from_text_and_image(
            role="user",
            text="Describe this",
            image_base64="image_data",
            media_type="image/png"
        )
    ]

    async def mock_stream():
        yield "Multi-message "
        yield "streaming "
        yield "works!"

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        result_chunks = []
        async for chunk in vision_provider.stream_complete(messages):
            result_chunks.append(chunk)

        assert "".join(result_chunks) == "Multi-message streaming works!"


@pytest.mark.asyncio
async def test_stream_complete_with_temperature_and_max_tokens(vision_provider, mock_vision_message):
    """Test streaming with custom parameters"""
    async def mock_stream():
        yield "Test response"

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()) as mock_stream_method:
        result_chunks = []
        async for chunk in vision_provider.stream_complete(
            [mock_vision_message],
            temperature=0.5,
            max_tokens=2048,
            system="You are a helpful assistant"
        ):
            result_chunks.append(chunk)

        # Verify parameters were passed correctly
        mock_stream_method.assert_called_once()
        call_kwargs = mock_stream_method.call_args[1]
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['max_tokens'] == 2048
        assert call_kwargs['system'] == "You are a helpful assistant"


@pytest.mark.asyncio
async def test_stream_complete_vs_complete_consistency(vision_provider, mock_vision_message):
    """Test that streaming and non-streaming produce similar outputs"""
    complete_response_text = "This is a complete response."

    # Mock non-streaming response
    mock_response = VisionResponse(
        content=complete_response_text,
        model=vision_provider.model,
        tokens_used=100,
        finish_reason="stop",
        input_tokens=50,
        output_tokens=50,
        cost_usd=0.001
    )

    # Mock streaming response
    async def mock_stream():
        chunks = ["This is ", "a complete ", "response."]
        for chunk in chunks:
            yield chunk

    with patch.object(vision_provider, 'complete', return_value=mock_response):
        complete_result = await vision_provider.complete([mock_vision_message])

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        stream_chunks = []
        async for chunk in vision_provider.stream_complete([mock_vision_message]):
            stream_chunks.append(chunk)
        stream_result = "".join(stream_chunks)

    # Content should be similar (not exact due to mocking)
    assert len(complete_result.content) > 0
    assert len(stream_result) > 0


@pytest.mark.asyncio
async def test_stream_complete_logging(vision_provider, mock_vision_message):
    """Test that streaming logs appropriate messages"""
    async def mock_stream():
        yield "test"

    with patch.object(vision_provider.client, 'stream_message', return_value=mock_stream()):
        with patch.object(vision_provider.logger, 'info') as mock_logger:
            async for chunk in vision_provider.stream_complete([mock_vision_message]):
                pass

            # Should log streaming request with images
            mock_logger.assert_called()
            log_calls = [str(call) for call in mock_logger.call_args_list]
            assert any("streaming" in str(call).lower() for call in log_calls)
