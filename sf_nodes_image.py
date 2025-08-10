try:
    import torch  # Provided by ComfyUI runtime
except Exception:
    torch = None

class SFImagePassthrough:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE", {})}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "forward"
    CATEGORY = "SF/Image"

    def forward(self, image):
        return (image,)

class SFImageGrayscale:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE", {})}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "to_gray"
    CATEGORY = "SF/Image"

    def to_gray(self, image):
        if torch is None:
            raise ImportError("torch is required at runtime (provided by ComfyUI environment)")
        if not isinstance(image, torch.Tensor):
            raise TypeError("Expected IMAGE tensor")
        if image.ndim != 4 or image.shape[-1] not in (1, 3, 4):
            raise ValueError("Expected IMAGE tensor with channels 1, 3, or 4")
        rgb = image[..., :3]
        gray = (0.299 * rgb[..., 0:1] + 0.587 * rgb[..., 1:2] + 0.114 * rgb[..., 2:3])
        out = gray.repeat(1, 1, 1, rgb.shape[-1]) if rgb.shape[-1] > 1 else gray
        return (out,)

NODE_CLASS_MAPPINGS = {
    "SFImagePassthrough": SFImagePassthrough,
    "SFImageGrayscale": SFImageGrayscale,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFImagePassthrough": "SF Image Passthrough",
    "SFImageGrayscale": "SF Image Grayscale",
}
