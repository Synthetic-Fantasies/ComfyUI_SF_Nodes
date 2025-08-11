# Aggregate all node class mappings for ComfyUI
from .nodes.sf_nodes_wildcards import SFWildcardsPromptMatrixExt
from .nodes.sf_nodes_preview import SFPreviewCompare
from .nodes.sf_nodes_grid import SFImageGridAuto

NODE_CLASS_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": SFWildcardsPromptMatrixExt,
    "SFPreviewCompare": SFPreviewCompare,
    "SFImageGridAuto": SFImageGridAuto,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": "SF Wildcards Prompt Matrix+",
    "SFPreviewCompare": "SF Preview Compare (A/B)",
    "SFImageGridAuto": "SF Image Grid (Auto Portrait)",
}


import os as _os
WEB_DIRECTORY = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "web"))

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]