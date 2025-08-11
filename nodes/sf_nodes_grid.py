try:
    import torch
    import torch.nn.functional as F
except Exception:
    torch = None
    F = None
try:
    from PIL import Image  # type: ignore
except Exception:
    Image = None

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


def _tensor_to_pil(img_nhwc):
    # Convert 1xHxWxC tensor in [0,1] to PIL RGB
    import numpy as np  # lazy import
    arr = img_nhwc[0].detach().cpu().clamp(0, 1).numpy()
    arr_u8 = (arr * 255.0 + 0.5).astype("uint8")
    return Image.fromarray(arr_u8, mode="RGB")


def _pil_to_tensor_nhwc_float(img_pil):
    import numpy as np
    arr = np.asarray(img_pil.convert("RGB"), dtype="float32") / 255.0
    t = torch.from_numpy(arr).unsqueeze(0)  # NHWC
    return t


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
            },
            "optional": {
                "filename_prefix": ("STRING", {"default": "SFGrid"}),
                "save_result": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "make_grid"
    CATEGORY = "SF/Image"

    def make_grid(self, images, filename_prefix: str = "SFGrid", save_result: bool = False):
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
        # Resize each image to common row height, preserve aspect; ensure CPU float32 NHWC contiguous
        tiles = [
            _resize_preserve_height(im, row_height)
            .to(dtype=torch.float32, device="cpu")
            .contiguous()
            for im in img_list
        ]
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
        # Compose grid using PIL when available (common pattern), fallback to tensor compose
        if Image is not None:
            grid_pil = Image.new("RGB", (int(canvas_w), int(canvas_h)))
            for i, tile in enumerate(tiles):
                r = i // cols
                # X position is sum of previous widths in this row
                start = r * cols
                idx_in_row = i - start
                x_offset = 0
                for k in range(idx_in_row):
                    x_offset += int(tiles[start + k].shape[2])
                tile_pil = _tensor_to_pil(tile)
                grid_pil.paste(tile_pil, (int(x_offset), int(r * row_height)))
            # Convert back to tensor for pipeline
            canvas = _pil_to_tensor_nhwc_float(grid_pil).to(dtype=torch.float32, device="cpu").contiguous()
        else:
            canvas = torch.zeros((1, canvas_h, canvas_w, 3), dtype=torch.float32, device="cpu")
            for i, tile in enumerate(tiles):
                r = i // cols
                # Place sequentially across the row
                y0 = r * row_height
                # current x is sum of previous widths in this row
                start = r * cols
                idx_in_row = i - start
                x_offset = 0
                for k in range(idx_in_row):
                    x_offset += int(tiles[start + k].shape[2])
                x0 = x_offset
                canvas[:, y0:y0 + row_height, x0:x0 + int(tile.shape[2]), :] = tile
            canvas = canvas.clamp(0.0, 1.0).contiguous()
            # Also derive a PIL image for saving if needed
            if Image is not None:
                grid_pil = _tensor_to_pil(canvas)
        # Optionally save to disk using ComfyUI's folder_paths conventions
        if save_result:
            try:
                import os
                try:
                    import folder_paths  # type: ignore
                    output_dir = folder_paths.get_output_directory()
                    full_output_folder, filename, counter, subfolder, used_prefix = folder_paths.get_save_image_path(
                        filename_prefix or "SFGrid", output_dir
                    )
                    os.makedirs(full_output_folder, exist_ok=True)
                    # Mirror common SaveImage naming: <prefix>_<counter>.png
                    # If the helper exists, use it to get the next number
                    try:
                        next_num = folder_paths.get_next_sequence_number(full_output_folder, used_prefix)
                        counter = max(counter, next_num)
                    except Exception:
                        pass
                    final_name = f"{used_prefix}_{counter:05d}.png"
                    file_path = os.path.join(full_output_folder, final_name)
                except Exception:
                    os.makedirs("output", exist_ok=True)
                    from time import time as _now
                    file_path = os.path.join("output", f"{(filename_prefix or 'SFGrid')}_{int(_now())}.png")

                # Save via PIL grid if available, else from tensor
                if Image is not None and 'grid_pil' in locals():
                    grid_pil.save(file_path)
                else:
                    arr = (canvas[0].detach().cpu().clamp(0, 1).numpy() * 255).astype("uint8")
                    from PIL import Image as _Image  # try lazy import
                    _Image.fromarray(arr, mode="RGB").save(file_path)
            except Exception:
                # Best-effort save; ignore failures at UI/runtime
                pass
        return (canvas,)

NODE_CLASS_MAPPINGS = {
    "SFImageGridAuto": SFImageGridAuto,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFImageGridAuto": "SF Image Grid (Auto Portrait)",
}


