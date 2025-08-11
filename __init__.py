# Aggregate all node class mappings for ComfyUI
from .backend.wildcard_nodes import SFWildcardsPromptMatrix
from .backend.image_nodes import SFPreviewImage, SFCompareImage, SFImageGrid


NODE_CLASS_MAPPINGS = {
    "SFWildcardsPromptMatrix": SFWildcardsPromptMatrix,
    "SFPreviewImage": SFPreviewImage,
    "SFCompare": SFCompareImage,
    "SFImageGrid": SFImageGrid,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFWildcardsPromptMatrix": "SF Wildcards Prompt Matrix+",
    "SFPreviewImage": "SF Preview Image",
    "SFCompare": "SF Compare",
    "SFImageGrid": "SF Image Grid",
}


WEB_DIRECTORY = "web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]