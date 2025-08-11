try:
    import torch
    import torch.nn.functional as F
except Exception:
    torch = None
    F = None

from typing import List, Tuple


def _ensure_torch():
    if torch is None:
        raise ImportError("torch is required at runtime (provided by ComfyUI environment)")


def _to_list_of_images(x) -> List[object]:
    if isinstance(x, list):
        return x
    # Expect NHWC tensor; allow single image or batch
    if hasattr(x, 'ndim') and x.ndim == 4 and x.shape[0] >= 1:
        # Split along batch dim
        return [x[i:i+1] for i in range(x.shape[0])]
    return [x]


def _ensure_rgb(image):
    # Expect NHWC; convert 1 or 4 channels to 3
    c = image.shape[-1]
    if c == 3:
        return image
    if c == 1:
        return image.repeat(1, 1, 1, 3)
    if c >= 3:
        return image[..., :3]
    raise ValueError("Unsupported channel count")


def _resize_letterbox_to_square(img_nhwc, size: int):
    _ensure_torch()
    # Convert to NCHW for interpolate
    n, h, w, c = img_nhwc.shape
    img = img_nhwc.permute(0, 3, 1, 2)
    # Compute scale to fit into size while preserving aspect
    scale = min(size / max(1, h), size / max(1, w))
    new_h = max(1, int(round(h * scale)))
    new_w = max(1, int(round(w * scale)))
    img_r = F.interpolate(img, size=(new_h, new_w), mode='bilinear', align_corners=False)
    # Pad to square
    pad_top = (size - new_h) // 2
    pad_bottom = size - new_h - pad_top
    pad_left = (size - new_w) // 2
    pad_right = size - new_w - pad_left
    img_p = F.pad(img_r, (pad_left, pad_right, pad_top, pad_bottom))
    # Back to NHWC
    return img_p.permute(0, 2, 3, 1)


def _choose_portrait_grid(num: int, target_ratio: float = 1.5) -> Tuple[int, int]:
    # target_ratio = rows / cols ; rows >= cols ensures portrait
    best = None
    for cols in range(1, num + 1):
        rows = (num + cols - 1) // cols
        if rows < cols:
            rows, cols = cols, rows
        ratio = rows / cols
        score = abs(ratio - target_ratio)
        empty = rows * cols - num
        cand = (score, empty, rows, cols)
        if best is None or cand < best:
            best = cand
    assert best is not None
    _, _, rows, cols = best
    return rows, cols


class SFImageGridAuto:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "make_grid"
    CATEGORY = "SF/Image"

    def make_grid(self, images):
        _ensure_torch()
        img_list = _to_list_of_images(images)
        if not img_list:
            raise ValueError("No images provided")
        # Normalize to RGB
        img_list = [_ensure_rgb(im) for im in img_list]
        # Determine grid
        n = len(img_list)
        rows, cols = _choose_portrait_grid(n)
        # Create tiles
        cell = 256
        tiles = [_resize_letterbox_to_square(im, cell) for im in img_list]
        # Compose canvas (NHWC)
        canvas = torch.zeros((1, rows * cell, cols * cell, 3), dtype=tiles[0].dtype, device=tiles[0].device)
        for i, tile in enumerate(tiles):
            r = i // cols
            c = i % cols
            y0, y1 = r * cell, (r + 1) * cell
            x0, x1 = c * cell, (c + 1) * cell
            canvas[:, y0:y1, x0:x1, :] = tile
        return (canvas,)


NODE_CLASS_MAPPINGS = {
    "SFImageGridAuto": SFImageGridAuto,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFImageGridAuto": "SF Image Grid (Auto Portrait)",
}


