# Aggregate all node class mappings for ComfyUI
from .backend.sf_nodes_wildcards import SFWildcardsPromptMatrixExt
from .backend.sf_compare_image import SFCompareImage
from .backend.sf_image_grid import SFImageGrid

NODE_CLASS_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": SFWildcardsPromptMatrixExt,
    "SFCompare": SFCompareImage,
    "SFImageGrid": SFImageGrid,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": "SF Wildcards Prompt Matrix+",
    "SFCompare": "SF Compare",
    "SFImageGrid": "SF Image Grid",
}


WEB_DIRECTORY = "web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]