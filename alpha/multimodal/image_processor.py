"""
Image Processing Module

Handles image loading, validation, optimization, and preparation for vision AI.
"""

import base64
import hashlib
import io
import mimetypes
from pathlib import Path
from typing import Optional

from PIL import Image

import logging

logger = logging.getLogger(__name__)


class ImageValidationError(Exception):
    """Raised when image validation fails"""

    pass


class ImageProcessor:
    """
    Process images for vision AI analysis

    Features:
    - Load images from file paths
    - Validate image formats and sizes
    - Optimize large images
    - Calculate content hashes for deduplication
    """

    # Supported image formats
    SUPPORTED_FORMATS = {"PNG", "JPEG", "JPG", "GIF", "WEBP", "BMP"}

    # Size limits
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    MAX_DIMENSION = 4096  # Max width or height
    OPTIMIZE_THRESHOLD = 5 * 1024 * 1024  # Optimize images >5MB

    def __init__(self):
        self.logger = logger

    def load_image(self, file_path: str | Path) -> Image.Image:
        """
        Load image from file path

        Args:
            file_path: Path to image file

        Returns:
            PIL Image object

        Raises:
            ImageValidationError: If image invalid or unsupported
        """
        file_path = Path(file_path)

        # Check file exists
        if not file_path.exists():
            raise ImageValidationError(f"Image file not found: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ImageValidationError(
                f"Image too large: {file_size / 1024 / 1024:.2f}MB "
                f"(max {self.MAX_FILE_SIZE / 1024 / 1024}MB)"
            )

        # Load image
        try:
            image = Image.open(file_path)
            image.load()  # Force load to detect corrupted images
        except Exception as e:
            raise ImageValidationError(f"Failed to load image: {e}")

        # Validate format
        if image.format not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(
                f"Unsupported image format: {image.format}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        self.logger.debug(
            f"Loaded image: {file_path.name} "
            f"({image.format}, {image.width}x{image.height}, "
            f"{file_size / 1024:.2f}KB)"
        )

        return image

    def validate_image(self, image: Image.Image) -> None:
        """
        Validate image meets requirements

        Args:
            image: PIL Image object

        Raises:
            ImageValidationError: If validation fails
        """
        # Check dimensions
        if image.width > self.MAX_DIMENSION or image.height > self.MAX_DIMENSION:
            raise ImageValidationError(
                f"Image dimensions too large: {image.width}x{image.height} "
                f"(max {self.MAX_DIMENSION}x{self.MAX_DIMENSION})"
            )

        # Check format
        if image.format not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(f"Unsupported format: {image.format}")

    def optimize_image(
        self, image: Image.Image, max_size: int = OPTIMIZE_THRESHOLD
    ) -> Image.Image:
        """
        Optimize image if too large

        Args:
            image: PIL Image object
            max_size: Maximum file size in bytes before optimization

        Returns:
            Optimized PIL Image (or original if no optimization needed)
        """
        # Estimate current size
        buffer = io.BytesIO()
        image.save(buffer, format=image.format or "PNG")
        current_size = buffer.tell()

        if current_size <= max_size:
            self.logger.debug("Image size OK, no optimization needed")
            return image

        # Calculate scaling factor to reduce size
        scale_factor = (max_size / current_size) ** 0.5
        new_width = int(image.width * scale_factor)
        new_height = int(image.height * scale_factor)

        self.logger.info(
            f"Optimizing image: {image.width}x{image.height} → "
            f"{new_width}x{new_height} "
            f"({current_size / 1024 / 1024:.2f}MB → "
            f"~{max_size / 1024 / 1024:.2f}MB)"
        )

        # Resize image
        optimized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return optimized

    def calculate_hash(self, image: Image.Image) -> str:
        """
        Calculate content hash for image deduplication

        Args:
            image: PIL Image object

        Returns:
            SHA256 hash of image content
        """
        # Convert image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format=image.format or "PNG")
        image_bytes = buffer.getvalue()

        # Calculate hash
        return hashlib.sha256(image_bytes).hexdigest()

    def get_metadata(self, image: Image.Image, file_path: Optional[Path] = None) -> dict:
        """
        Extract image metadata

        Args:
            image: PIL Image object
            file_path: Optional file path for additional metadata

        Returns:
            Dictionary with image metadata
        """
        metadata = {
            "format": image.format,
            "mode": image.mode,
            "width": image.width,
            "height": image.height,
            "size_kb": None,
        }

        if file_path and file_path.exists():
            metadata["size_kb"] = file_path.stat().st_size / 1024
            metadata["filename"] = file_path.name

        return metadata

    def convert_format(self, image: Image.Image, target_format: str = "PNG") -> Image.Image:
        """
        Convert image to different format

        Args:
            image: PIL Image object
            target_format: Target format (PNG, JPEG, etc.)

        Returns:
            Converted PIL Image
        """
        if target_format.upper() not in self.SUPPORTED_FORMATS:
            raise ImageValidationError(f"Unsupported target format: {target_format}")

        # Convert mode if needed (e.g., RGBA → RGB for JPEG)
        if target_format.upper() == "JPEG" and image.mode in ("RGBA", "P"):
            # Create white background for transparency
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
            image = background

        self.logger.debug(f"Converting image to {target_format}")
        return image

    def process_image(
        self,
        file_path: str | Path,
        optimize: bool = True,
        target_format: Optional[str] = None,
    ) -> tuple[Image.Image, dict]:
        """
        Complete image processing pipeline

        Args:
            file_path: Path to image file
            optimize: Whether to optimize large images
            target_format: Optional target format for conversion

        Returns:
            Tuple of (processed PIL Image, metadata dict)

        Raises:
            ImageValidationError: If processing fails
        """
        file_path = Path(file_path)

        # Load image
        image = self.load_image(file_path)

        # Validate
        self.validate_image(image)

        # Optimize if needed
        if optimize:
            image = self.optimize_image(image)

        # Convert format if requested
        if target_format:
            image = self.convert_format(image, target_format)

        # Calculate hash
        content_hash = self.calculate_hash(image)

        # Get metadata
        metadata = self.get_metadata(image, file_path)
        metadata["content_hash"] = content_hash

        self.logger.info(f"Image processed successfully: {file_path.name}")

        return image, metadata
