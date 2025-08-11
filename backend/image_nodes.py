import os
from nodes import  SaveImage, PreviewImage # ty
import folder_paths # type: ignore
import random

class SFCompareImage(PreviewImage):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": ("IMAGE", {}),
                "image_b": ("IMAGE", {}),
            }
        }


    FUNCTION = "execute"
    CATEGORY = "SF/Image"
    DESCRIPTION = "The easiest way to preview, compare current and previous images, and track your prompt history."

    def execute(self, A, B):
        _a = self.save_images(A,)["ui"]["images"]
        _b = self.save_images(B,)["ui"]["images"]

        return {"ui": {"images": _a + _b}}



class SFPreviewImage(SaveImage):
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + "".join(
            random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5)
        )
        self.compress_level = 1


    #FUNCTION = "execute"
    CATEGORY = "SF/Image"
    DESCRIPTION = "The easiest way to preview, compare current and previous images, and track your prompt history."

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }
    def execute(self, images):
        pass
