class SFTextConcat:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_a": ("STRING", {"default": "Hello"}),
                "text_b": ("STRING", {"default": "World"}),
                "separator": ("STRING", {"default": " "}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "concat"
    CATEGORY = "SF/Text"

    def concat(self, text_a: str, text_b: str, separator: str):
        return (f"{text_a}{separator}{text_b}",)


NODE_CLASS_MAPPINGS = {
    "SFTextConcat": SFTextConcat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFTextConcat": "SF Text Concat",
}
