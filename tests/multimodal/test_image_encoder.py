"""
Tests for ImageEncoder
"""

import base64
import io
import pytest
import httpx
from pathlib import Path
from PIL import Image
from unittest.mock import Mock, patch

from alpha.multimodal.image_encoder import ImageEncoder, ImageEncodeError


@pytest.fixture
def encoder():
    """Create ImageEncoder instance"""
    enc = ImageEncoder()
    yield enc
    enc.close()


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image"""
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (50, 50), color="green")
    img.save(img_path)
    return img_path


class TestImageEncoder:
    """Test ImageEncoder class"""

    def test_encode_image(self, encoder):
        """Test encoding PIL Image to base64"""
        img = Image.new("RGB", (10, 10), color="red")
        encoded = encoder.encode_image(img, format="PNG")

        # Should be valid base64
        assert isinstance(encoded, str)
        assert len(encoded) > 0

        # Should be decodable
        decoded = base64.b64decode(encoded)
        assert len(decoded) > 0

    def test_encode_image_different_formats(self, encoder):
        """Test encoding with different formats"""
        img = Image.new("RGB", (10, 10), color="blue")

        # PNG
        encoded_png = encoder.encode_image(img, format="PNG")
        assert len(encoded_png) > 0

        # JPEG
        encoded_jpeg = encoder.encode_image(img, format="JPEG")
        assert len(encoded_jpeg) > 0

        # Different formats should produce different encodings
        assert encoded_png != encoded_jpeg

    def test_encode_image_file_success(self, encoder, sample_image):
        """Test encoding image file"""
        encoded = encoder.encode_image_file(sample_image)

        assert isinstance(encoded, str)
        assert len(encoded) > 0

        # Verify can decode back
        decoded = base64.b64decode(encoded)
        img = Image.open(io.BytesIO(decoded))
        assert img.width == 50
        assert img.height == 50

    def test_encode_image_file_not_found(self, encoder):
        """Test encoding non-existent file"""
        with pytest.raises(ImageEncodeError, match="not found"):
            encoder.encode_image_file("/nonexistent/image.png")

    def test_encode_image_file_with_format(self, encoder, sample_image):
        """Test encoding with specific format"""
        encoded = encoder.encode_image_file(sample_image, format="JPEG")

        assert isinstance(encoded, str)
        assert len(encoded) > 0

    def test_is_url_valid_urls(self, encoder):
        """Test URL detection with valid URLs"""
        assert encoder.is_url("https://example.com/image.png")
        assert encoder.is_url("http://example.com/photo.jpg")
        assert encoder.is_url("https://cdn.example.com/images/pic.webp")

    def test_is_url_invalid_urls(self, encoder):
        """Test URL detection with invalid URLs"""
        assert not encoder.is_url("/local/path/image.png")
        assert not encoder.is_url("image.png")
        assert not encoder.is_url("relative/path/image.jpg")
        assert not encoder.is_url("C:\\Windows\\image.bmp")

    @patch("httpx.Client.get")
    def test_download_image_success(self, mock_get, encoder):
        """Test successful image download"""
        # Mock response
        img = Image.new("RGB", (20, 20), color="yellow")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        mock_response = Mock()
        mock_response.content = image_bytes
        mock_response.headers = {"content-type": "image/png"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Download
        downloaded = encoder.download_image("https://example.com/test.png")

        assert downloaded == image_bytes

    @patch("httpx.Client.get")
    def test_download_image_not_an_image(self, mock_get, encoder):
        """Test downloading non-image content"""
        mock_response = Mock()
        mock_response.content = b"HTML content"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(ImageEncodeError, match="does not point to an image"):
            encoder.download_image("https://example.com/page.html")

    @patch("httpx.Client.get")
    def test_download_image_http_error(self, mock_get, encoder):
        """Test handling HTTP errors"""
        mock_get.side_effect = httpx.HTTPStatusError(
            "404", request=Mock(), response=Mock(status_code=404)
        )

        with pytest.raises(ImageEncodeError, match="HTTP error"):
            encoder.download_image("https://example.com/missing.png")

    @patch("httpx.Client.get")
    def test_download_image_network_error(self, mock_get, encoder):
        """Test handling network errors"""
        mock_get.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(ImageEncodeError, match="Network error"):
            encoder.download_image("https://example.com/image.png")

    @patch.object(ImageEncoder, "download_image")
    def test_encode_image_url(self, mock_download, encoder):
        """Test encoding image from URL"""
        # Mock download
        img = Image.new("RGB", (15, 15), color="purple")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        mock_download.return_value = buffer.getvalue()

        # Encode from URL
        encoded = encoder.encode_image_url("https://example.com/test.png")

        assert isinstance(encoded, str)
        assert len(encoded) > 0
        mock_download.assert_called_once()

    def test_get_image_data_uri(self, encoder):
        """Test data URI generation"""
        img = Image.new("RGB", (5, 5), color="cyan")
        data_uri = encoder.get_image_data_uri(img, format="PNG")

        assert data_uri.startswith("data:image/png;base64,")
        assert len(data_uri) > len("data:image/png;base64,")

    def test_encode_from_source_file(self, encoder, sample_image):
        """Test encoding from file source"""
        encoded, source_type = encoder.encode_from_source(sample_image)

        assert isinstance(encoded, str)
        assert source_type == "file"

    @patch.object(ImageEncoder, "encode_image_url")
    def test_encode_from_source_url(self, mock_encode_url, encoder):
        """Test encoding from URL source"""
        mock_encode_url.return_value = "base64string"

        encoded, source_type = encoder.encode_from_source(
            "https://example.com/image.png"
        )

        assert encoded == "base64string"
        assert source_type == "url"
        mock_encode_url.assert_called_once()

    def test_context_manager(self, sample_image):
        """Test context manager usage"""
        with ImageEncoder() as encoder:
            encoded = encoder.encode_image_file(sample_image)
            assert isinstance(encoded, str)

        # Client should be closed
        assert encoder.http_client is None

    def test_close(self, encoder):
        """Test closing encoder"""
        # Create client
        encoder._get_http_client()
        assert encoder.http_client is not None

        # Close
        encoder.close()
        assert encoder.http_client is None
