"""
Image Encoding Module

Handles image encoding for vision AI APIs (base64, URL fetching).
"""

import base64
import io
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx
from PIL import Image

logger = logging.getLogger(__name__)


class ImageEncodeError(Exception):
    """Raised when image encoding fails"""

    pass


class ImageEncoder:
    """
    Encode images for vision AI APIs

    Features:
    - Base64 encoding for local images
    - Download and encode images from URLs
    - Support multiple image formats
    - HTTP client with timeout and retry
    """

    # HTTP client settings
    TIMEOUT = 30  # seconds
    MAX_RETRIES = 3

    def __init__(self):
        self.logger = logger
        self.http_client: Optional[httpx.Client] = None

    def _get_http_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self.http_client is None:
            self.http_client = httpx.Client(
                timeout=self.TIMEOUT,
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self.http_client

    def close(self):
        """Close HTTP client"""
        if self.http_client:
            self.http_client.close()
            self.http_client = None

    def encode_image(self, image: Image.Image, format: str = "PNG") -> str:
        """
        Encode PIL Image to base64 string

        Args:
            image: PIL Image object
            format: Image format (PNG, JPEG, etc.)

        Returns:
            Base64 encoded string
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        image_bytes = buffer.getvalue()
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        self.logger.debug(
            f"Encoded image to base64: {len(encoded)} chars "
            f"({len(image_bytes) / 1024:.2f}KB)"
        )

        return encoded

    def encode_image_file(self, file_path: str | Path, format: Optional[str] = None) -> str:
        """
        Encode image file to base64 string

        Args:
            file_path: Path to image file
            format: Optional target format (uses original if not specified)

        Returns:
            Base64 encoded string

        Raises:
            ImageEncodeError: If encoding fails
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ImageEncodeError(f"Image file not found: {file_path}")

        try:
            # Load image
            image = Image.open(file_path)
            image.load()

            # Use original format if not specified
            if format is None:
                format = image.format or "PNG"

            # Encode
            encoded = self.encode_image(image, format)

            self.logger.info(f"Encoded image file: {file_path.name}")

            return encoded

        except Exception as e:
            raise ImageEncodeError(f"Failed to encode image: {e}")

    def is_url(self, path: str) -> bool:
        """
        Check if string is a valid URL

        Args:
            path: String to check

        Returns:
            True if valid URL, False otherwise
        """
        try:
            result = urlparse(path)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def download_image(self, url: str) -> bytes:
        """
        Download image from URL

        Args:
            url: Image URL

        Returns:
            Image bytes

        Raises:
            ImageEncodeError: If download fails
        """
        client = self._get_http_client()

        try:
            self.logger.info(f"Downloading image from: {url}")

            response = client.get(url)
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                raise ImageEncodeError(
                    f"URL does not point to an image: {content_type}"
                )

            image_bytes = response.content

            self.logger.debug(
                f"Downloaded image: {len(image_bytes) / 1024:.2f}KB "
                f"({content_type})"
            )

            return image_bytes

        except httpx.HTTPStatusError as e:
            raise ImageEncodeError(f"HTTP error downloading image: {e.response.status_code}")
        except httpx.RequestError as e:
            raise ImageEncodeError(f"Network error downloading image: {e}")
        except Exception as e:
            raise ImageEncodeError(f"Failed to download image: {e}")

    def encode_image_url(self, url: str, format: str = "PNG") -> str:
        """
        Download and encode image from URL

        Args:
            url: Image URL
            format: Target format for encoding

        Returns:
            Base64 encoded string

        Raises:
            ImageEncodeError: If download or encoding fails
        """
        # Download image
        image_bytes = self.download_image(url)

        # Load as PIL Image
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.load()
        except Exception as e:
            raise ImageEncodeError(f"Failed to load downloaded image: {e}")

        # Encode
        encoded = self.encode_image(image, format)

        self.logger.info(f"Encoded image from URL: {url}")

        return encoded

    def get_image_data_uri(
        self, image: Image.Image, format: str = "PNG"
    ) -> str:
        """
        Generate data URI for image

        Args:
            image: PIL Image object
            format: Image format

        Returns:
            Data URI string (data:image/png;base64,...)
        """
        encoded = self.encode_image(image, format)
        mime_type = f"image/{format.lower()}"
        data_uri = f"data:{mime_type};base64,{encoded}"

        self.logger.debug(f"Generated data URI: {len(data_uri)} chars")

        return data_uri

    def encode_from_source(
        self, source: str | Path, format: str = "PNG"
    ) -> tuple[str, str]:
        """
        Encode image from file path or URL

        Args:
            source: File path or URL
            format: Target format for encoding

        Returns:
            Tuple of (base64 string, source type: "file" or "url")

        Raises:
            ImageEncodeError: If encoding fails
        """
        source_str = str(source)

        # Check if URL
        if self.is_url(source_str):
            encoded = self.encode_image_url(source_str, format)
            return encoded, "url"
        else:
            # Treat as file path
            encoded = self.encode_image_file(source, format)
            return encoded, "file"

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
