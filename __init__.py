# Aggregate all node class mappings for ComfyUI
from .nodes.sf_nodes_wildcards import SFWildcardsPromptMatrixExt
from .nodes.sf_nodes_preview import SFPreviewCompare

NODE_CLASS_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": SFWildcardsPromptMatrixExt,
    "SFPreviewCompare": SFPreviewCompare,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": "SF Wildcards Prompt Matrix+",
    "SFPreviewCompare": "SF Preview Compare (A/B)",
}


WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]