class SFHello:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": "World", "multiline": False}),
                "exclamation": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("greeting",)
    FUNCTION = "greet"
    CATEGORY = "SF/Utility"

    def greet(self, name: str, exclamation: bool):
        suffix = "!" if exclamation else "."
        return (f"Hello, {name}{suffix}",)
