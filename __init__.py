# Aggregate all node class mappings for ComfyUI
from .backend.wildcard_nodes import SFWildcardsPromptMatrix
from .backend.image_nodes import SFPreviewImage, SFCompareImage, SFImageGrid, SFSaveImage, SFWaitForAll, SFWaitForImages, SFCombinePath, SFPathInfo, SFMakePath, SFUniqueDir, SFIncrementalPath, SFTimestampPath, SFOdometer, SFSequence, SFTimer


NODE_CLASS_MAPPINGS = {
    "SFWildcardsPromptMatrix": SFWildcardsPromptMatrix,
    "SFPreviewImage": SFPreviewImage,
    "SFCompareImage": SFCompareImage,
    "SFImageGrid": SFImageGrid,
    "SFSaveImage": SFSaveImage,
    "SFWaitForAll": SFWaitForAll,
    "SFWaitForImages": SFWaitForImages,
    "SFCombinePath": SFCombinePath,
    "SFPathInfo": SFPathInfo,
    "SFMakePath": SFMakePath,
    "SFUniqueDir": SFUniqueDir,
    "SFIncrementalPath": SFIncrementalPath,
    "SFTimestampPath": SFTimestampPath,
    "SFOdometer": SFOdometer,
    "SFSequence": SFSequence,
    "SFTimer": SFTimer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFWildcardsPromptMatrix": "SF Wildcards Prompt Matrix+",
    "SFPreviewImage": "SF Preview Image",
    "SFCompareImage": "SF Compare",
    "SFImageGrid": "SF Image Grid",
    "SFSaveImage": "SF Save Image",
    "SFWaitForAll": "SF Wait For All",
    "SFWaitForImages": "SF Wait For Images",
    "SFCombinePath": "SF Combine Path",
    "SFPathInfo": "SF Path Info",
    "SFMakePath": "SF Make Path",
    "SFUniqueDir": "SF Unique Directory",
    "SFIncrementalPath": "SF Incremental Path",
    "SFTimestampPath": "SF Timestamp Path",
    "SFOdometer": "SF Odometer",
    "SFSequence": "SF Sequence",
    "SFTimer": "SF Timer",
}


WEB_DIRECTORY = "web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]