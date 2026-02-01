"""
Vision Message Types

Support for multimodal messages with images for vision-capable LLMs.
"""

from dataclasses import dataclass, field
from typing import List, Union, Optional, Any


@dataclass
class TextContent:
    """Text content block"""

    type: str = "text"
    text: str = ""


@dataclass
class ImageSource:
    """Image source (base64 or URL)"""

    type: str  # "base64" or "url"
    media_type: str  # "image/png", "image/jpeg", etc.
    data: str  # base64 string or URL


@dataclass
class ImageContent:
    """Image content block"""

    type: str = "image"
    source: ImageSource = None


ContentBlock = Union[TextContent, ImageContent]


@dataclass
class VisionMessage:
    """
    Multimodal message supporting text and images

    Compatible with Claude Vision API and GPT-4V format.

    Examples:
        # Text-only message (backward compatible)
        msg = VisionMessage(
            role="user",
            content="What is this?"
        )

        # Message with image
        msg = VisionMessage(
            role="user",
            content=[
                TextContent(text="What do you see in this image?"),
                ImageContent(source=ImageSource(
                    type="base64",
                    media_type="image/png",
                    data="iVBORw0KGgo..."
                ))
            ]
        )
    """

    role: str  # system, user, assistant
    content: Union[str, List[ContentBlock]]  # Text string or content blocks

    def to_dict(self) -> dict:
        """Convert to API-compatible dictionary"""
        if isinstance(self.content, str):
            # Simple text message
            return {"role": self.role, "content": self.content}
        else:
            # Multimodal message with content blocks
            content_list = []
            for block in self.content:
                if isinstance(block, TextContent):
                    content_list.append({"type": "text", "text": block.text})
                elif isinstance(block, ImageContent):
                    content_list.append(
                        {
                            "type": "image",
                            "source": {
                                "type": block.source.type,
                                "media_type": block.source.media_type,
                                "data": block.source.data,
                            },
                        }
                    )
            return {"role": self.role, "content": content_list}

    @classmethod
    def from_text(cls, role: str, text: str) -> "VisionMessage":
        """Create text-only message"""
        return cls(role=role, content=text)

    @classmethod
    def from_text_and_image(
        cls, role: str, text: str, image_base64: str, media_type: str = "image/png"
    ) -> "VisionMessage":
        """Create message with text and base64 image"""
        return cls(
            role=role,
            content=[
                TextContent(text=text),
                ImageContent(
                    source=ImageSource(
                        type="base64", media_type=media_type, data=image_base64
                    )
                ),
            ],
        )

    @classmethod
    def from_text_and_images(
        cls,
        role: str,
        text: str,
        images: List[tuple[str, str]],  # [(base64, media_type), ...]
    ) -> "VisionMessage":
        """Create message with text and multiple images"""
        content = [TextContent(text=text)]

        for image_base64, media_type in images:
            content.append(
                ImageContent(
                    source=ImageSource(
                        type="base64", media_type=media_type, data=image_base64
                    )
                )
            )

        return cls(role=role, content=content)

    def has_images(self) -> bool:
        """Check if message contains images"""
        if isinstance(self.content, str):
            return False
        return any(isinstance(block, ImageContent) for block in self.content)

    def get_text(self) -> str:
        """Extract text content"""
        if isinstance(self.content, str):
            return self.content

        text_blocks = [
            block.text for block in self.content if isinstance(block, TextContent)
        ]
        return " ".join(text_blocks)


# Backward compatibility alias
Message = VisionMessage
