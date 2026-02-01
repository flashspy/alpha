"""
Multimodal Capabilities Module

Provides image understanding and visual AI capabilities.
"""

from .image_encoder import ImageEncoder, ImageEncodeError
from .image_processor import ImageProcessor, ImageValidationError

__all__ = [
    "ImageProcessor",
    "ImageValidationError",
    "ImageEncoder",
    "ImageEncodeError",
]
