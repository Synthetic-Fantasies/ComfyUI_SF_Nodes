import os
try:
    import torch  # Provided by ComfyUI runtime
    import torch.nn.functional as F
except Exception:
    torch = None
    F = None
from typing import List, Union


def _ensure_torch():
    if torch is None:
        raise ImportError("torch is required at runtime (provided by ComfyUI environment)")


def _normalize_images(x: Union[object, List[object]]) -> List[object]:
    return x if isinstance(x, list) else [x]


def _select_by_index(images: List[object], index: int):
    if not images:
        raise ValueError("Empty image list")
    return images[index % len(images)]


def _pick_first_batch(img):
    # Expect NHWC float tensor in [0,1]
    if hasattr(img, 'ndim') and img.ndim == 4 and img.shape[0] > 1:
        return img[0:1]
    return img


def _resize_to_same_height(a, b):
    # Resize B,H,W,C to same H using bilinear on NCHW
    if a.shape[1] == b.shape[1]:
        return a, b
    _ensure_torch()
    def to_nchw(t):
        return t.permute(0, 3, 1, 2)
    def to_nhwc(t):
        return t.permute(0, 2, 3, 1)
    if a.shape[1] < b.shape[1]:
        target_h = a.shape[1]
        b_n = to_nchw(b)
        b_r = F.interpolate(b_n, size=(target_h, int(round(b.shape[2] * target_h / b.shape[1]))), mode='bilinear', align_corners=False)
        b = to_nhwc(b_r)
    else:
        target_h = b.shape[1]
        a_n = to_nchw(a)
        a_r = F.interpolate(a_n, size=(target_h, int(round(a.shape[2] * target_h / a.shape[1]))), mode='bilinear', align_corners=False)
        a = to_nhwc(a_r)
    return a, b


class SFPreviewCompare:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_a": ("IMAGE", {}),
                "image_b": ("IMAGE", {}),
                "index": ("INT", {"default": 0, "min": 0, "max": 10_000}),
            }
        }

    RETURN_TYPES = ("IMAGE", "INT")
    RETURN_NAMES = ("image", "index")
    FUNCTION = "render"
    CATEGORY = "SF/Preview"

    def render(self, image_a, image_b, index: int):
        _ensure_torch()
        a_list = _normalize_images(image_a)
        b_list = _normalize_images(image_b)
        max_len = max(len(a_list), len(b_list))
        sel = index % max_len
        a = _select_by_index(a_list, sel)
        b = _select_by_index(b_list, sel)

        a = _pick_first_batch(a)
        b = _pick_first_batch(b)

        a, b = _resize_to_same_height(a, b)
        # Normalize to float32 NHWC on CPU, 3 channels
        def to_rgb_float_nhwc_cpu(t):
            c = t.shape[-1]
            if c == 1:
                t = t.repeat(1, 1, 1, 3)
            elif c >= 3:
                t = t[..., :3]
            return t.to(dtype=torch.float32, device="cpu").contiguous()

        a = to_rgb_float_nhwc_cpu(a)
        b = to_rgb_float_nhwc_cpu(b)
        # Always output side-by-side combined image so UI can choose A/B/Swipe/Area without re-execution
        combined = torch.cat([a, b], dim=2).clamp(0.0, 1.0).contiguous()
        return (combined, sel)


NODE_CLASS_MAPPINGS = {
    "SFPreviewCompare": SFPreviewCompare,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFPreviewCompare": "SF Preview Compare (A/B)",
}

# Serve frontend assets; resolve to repo root's web directory
WEB_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))


