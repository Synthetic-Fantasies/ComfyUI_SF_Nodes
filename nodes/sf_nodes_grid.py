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
    # kept for potential future use; not used when pasting original sizes
    _ensure_torch()
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


def _choose_layout_by_sizes(sizes: List[Tuple[int, int]], target_ratio: float = 1.5) -> Tuple[int, int, int, List[int]]:
    """Choose columns count to approximate portrait aspect using original sizes.
    Returns: (total_w, total_h, cols, row_heights)
    """
    n = len(sizes)
    best = None
    best_layout = None
    for cols in range(1, n + 1):
        rows = (n + cols - 1) // cols
        row_heights: List[int] = []
        row_widths: List[int] = []
        for r in range(rows):
            start = r * cols
            end = min(start + cols, n)
            if start >= n:
                row_heights.append(0)
                row_widths.append(0)
                continue
            w_sum = 0
            h_max = 0
            for (w, h) in sizes[start:end]:
                w_sum += int(w)
                h_max = max(h_max, int(h))
            row_heights.append(h_max)
            row_widths.append(w_sum)
        total_w = max(row_widths) if row_widths else 0
        total_h = sum(row_heights)
        if total_w == 0 or total_h == 0:
            continue
        ratio = total_h / total_w
        empty = rows * cols - n
        score = (abs(ratio - target_ratio), empty, total_w * total_h)
        if best is None or score < best:
            best = score
            best_layout = (total_w, total_h, cols, row_heights)
    # Fallback to 1 column if needed
    if best_layout is None:
        total_w = max(w for w, _ in sizes)
        total_h = sum(h for _, h in sizes)
        return total_w, total_h, 1, [h for _, h in sizes]
    return best_layout


class SFImageGridAuto:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {}),
            },
            "optional": {
                "favor_portrait": ("BOOLEAN", {"default": True}),
                "pad_to_multiple": ("INT", {"default": 8, "min": 1, "max": 128}),
                "filename_prefix": ("STRING", {"default": "SFGrid"}),
                "save_result": ("BOOLEAN", {"default": False}),
            },
        }

    @classmethod
    def UI(cls):
        return {
            "title": "SF Image Grid (Auto)",
            "type": "node",
            "props": [
                {"name": "favor_portrait", "label": "Favor Portrait", "type": "boolean", "default": True},
                {"name": "pad_to_multiple", "label": "Pad Multiple", "type": "int", "default": 8, "min": 1, "max": 128},
                {"name": "filename_prefix", "label": "Filename Prefix", "type": "text", "default": "SFGrid"},
                {"name": "save_result", "label": "Save Result", "type": "boolean", "default": False},
            ],
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "make_grid"
    CATEGORY = "SF/Image"

    def make_grid(self, images, favor_portrait: bool = True, pad_to_multiple: int = 8, filename_prefix: str = "SFGrid", save_result: bool = False):
        _ensure_torch()
        img_list = _to_list_of_images(images)
        if not img_list:
            raise ValueError("No images provided")
        # Normalize to RGB
        img_list = [_ensure_rgb(im) for im in img_list]
        # Determine layout using original image sizes; do not resize tiles
        sizes: List[Tuple[int, int]] = [(int(t.shape[2]), int(t.shape[1])) for t in img_list]  # (w, h) from NHWC
        target_ratio = 1.5 if favor_portrait else (1.0 / 1.5)
        total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=target_ratio)

        # Prepare tiles as PIL for pasting
        if Image is not None:
            tiles_pil = [_tensor_to_pil(im.to(dtype=torch.float32, device="cpu")) for im in img_list]
            grid_pil = Image.new("RGB", (int(total_w), int(total_h)))
            y_cursor = 0
            idx = 0
            for r, row_h in enumerate(row_heights):
                x_cursor = 0
                for c in range(cols):
                    if idx >= len(tiles_pil):
                        break
                    tile = tiles_pil[idx]
                    grid_pil.paste(tile, (int(x_cursor), int(y_cursor)))
                    x_cursor += tile.width
                    idx += 1
                y_cursor += row_h
            canvas = _pil_to_tensor_nhwc_float(grid_pil).to(dtype=torch.float32, device="cpu").contiguous()
        else:
            # Fallback: compose tensor canvas with original sizes
            canvas = torch.zeros((1, int(total_h), int(total_w), 3), dtype=torch.float32, device="cpu")
            y_cursor = 0
            idx = 0
            for r, row_h in enumerate(row_heights):
                x_cursor = 0
                for c in range(cols):
                    if idx >= len(img_list):
                        break
                    tile = img_list[idx].to(dtype=torch.float32, device="cpu").contiguous()
                    h = int(tile.shape[1]); w = int(tile.shape[2])
                    canvas[:, y_cursor:y_cursor + h, x_cursor:x_cursor + w, :] = _ensure_rgb(tile)
                    x_cursor += w
                    idx += 1
                y_cursor += row_h
            canvas = canvas.clamp(0.0, 1.0).contiguous()
        # Optionally pad to nearest multiple (height/width) for downstream node compatibility
        if isinstance(pad_to_multiple, int) and pad_to_multiple > 1:
            mul = pad_to_multiple
            h, w = int(canvas.shape[1]), int(canvas.shape[2])
            pad_h = (mul - (h % mul)) % mul
            pad_w = (mul - (w % mul)) % mul
            if pad_h or pad_w:
                canvas = torch.nn.functional.pad(
                    canvas, (0, 0, 0, pad_w, 0, pad_h), mode="constant", value=0.0
                )
        # Optionally save to output directory
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


