# Aggregate all node class mappings for ComfyUI
from importlib import import_module as _import_module

# Support being imported as a package name or as a plain folder module
try:
    _nodes_pkg = _import_module(__name__ + ".nodes")
except Exception:
    # Fallback: import top-level 'nodes' when __name__ is not a package
    _nodes_pkg = _import_module("nodes")

SFWildcardsPromptMatrixExt = getattr(_nodes_pkg, "sf_nodes_wildcards").SFWildcardsPromptMatrixExt
SFPreviewCompare = getattr(_nodes_pkg, "sf_nodes_preview").SFPreviewCompare

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