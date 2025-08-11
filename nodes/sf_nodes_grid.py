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


def _resize_preserve_height(img_nhwc, out_h: int):
    _ensure_torch()
    # Convert to NCHW for interpolate
    _, h, w, _ = img_nhwc.shape
    aspect = float(w) / float(h)
    out_w = max(1, int(round(out_h * aspect)))
    img = img_nhwc.permute(0, 3, 1, 2)
    img_r = F.interpolate(img, size=(out_h, out_w), mode='bilinear', align_corners=False)
    return img_r.permute(0, 2, 3, 1)


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
        # Determine grid arrangement (portrait target), then scale tiles preserving aspect
        n = len(img_list)
        rows, cols = _choose_portrait_grid(n)
        row_height = 256
        # Resize each image to common row height, preserve aspect
        tiles = [_resize_preserve_height(im, row_height) for im in img_list]
        # Compute per-row widths and overall canvas size
        row_widths: List[int] = []
        for r in range(rows):
            start = r * cols
            end = min(start + cols, n)
            if start >= n:
                row_widths.append(0)
                continue
            width_sum = sum(int(t.shape[2]) for t in tiles[start:end])
            row_widths.append(width_sum)
        canvas_w = max(row_widths) if row_widths else 0
        canvas_h = rows * row_height
        if canvas_w <= 0 or canvas_h <= 0:
            raise ValueError("Computed invalid canvas size")
        # Compose canvas (NHWC), no letterboxing inside tiles; right side of shorter rows remains empty
        canvas = torch.zeros((1, canvas_h, canvas_w, 3), dtype=tiles[0].dtype, device=tiles[0].device)
        for i, tile in enumerate(tiles):
            r = i // cols
            # Place sequentially across the row
            y0 = r * row_height
            y1 = y0 + row_height
            # current x is sum of previous widths in this row
            start = r * cols
            idx_in_row = i - start
            x_offset = 0
            for k in range(idx_in_row):
                x_offset += int(tiles[start + k].shape[2])
            x0 = x_offset
            x1 = x0 + int(tile.shape[2])
            canvas[:, y0:y1, x0:x1, :] = tile
        return (canvas,)


NODE_CLASS_MAPPINGS = {
    "SFImageGridAuto": SFImageGridAuto,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFImageGridAuto": "SF Image Grid (Auto Portrait)",
}


