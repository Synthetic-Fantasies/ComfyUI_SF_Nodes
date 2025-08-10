# Aggregate all node class mappings for ComfyUI
from sf_hello_nodes import SFHello
from sf_nodes_text import SFTextConcat
from sf_nodes_math import SFMathOps
from sf_nodes_image import SFImagePassthrough, SFImageGrayscale
from sf_nodes_wildcards import SFWildcardsPromptMatrixExt
from sf_nodes_preview import SFPreviewCompare

NODE_CLASS_MAPPINGS = {
    "SFHello": SFHello,
    "SFTextConcat": SFTextConcat,
    "SFMathOps": SFMathOps,
    "SFImagePassthrough": SFImagePassthrough,
    "SFImageGrayscale": SFImageGrayscale,
    "SFWildcardsPromptMatrixExt": SFWildcardsPromptMatrixExt,
    "SFPreviewCompare": SFPreviewCompare,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFHello": "SF Hello",
    "SFTextConcat": "SF Text Concat",
    "SFMathOps": "SF Math Ops",
    "SFImagePassthrough": "SF Image Passthrough",
    "SFImageGrayscale": "SF Image Grayscale",
    "SFWildcardsPromptMatrixExt": "SF Wildcards Prompt Matrix+",
    "SFPreviewCompare": "SF Preview Compare (A/B)",
}
