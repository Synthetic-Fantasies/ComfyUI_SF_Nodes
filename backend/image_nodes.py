import os
from nodes import  SaveImage, PreviewImage # ty
import folder_paths # type: ignore
import random
from PIL import Image
from typing import List, Tuple
import torch
import torch.nn.functional as F  



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


class SFImageGrid(SaveImage):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {}),
            },
            "optional": {
                "favor_portrait": ("BOOLEAN", {"default": True}),
                "filename_prefix": ("STRING", {"default": "SFGrid"}),
            },
        }



    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "SF/Image"

    def execute(self, images, favor_portrait: bool = True, filename_prefix: str = "SFGrid", save_result: bool = False):
        
        
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
        # Optionally pad to nearest multiple (height/width) for downstream node compatibility (internal default)
        mul = 8
        if mul > 1:
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

class SFCompareImage(PreviewImage):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "A": ("IMAGE", {}),
                "B": ("IMAGE", {}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("A", "B")
    FUNCTION = "execute"
    CATEGORY = "SF/Image"
    DESCRIPTION = "The easiest way to preview, compare current and previous images, and track your prompt history."

    def execute(self, A, B):
        _a = self.save_images(A,)["ui"]["images"]
        _b = self.save_images(B,)["ui"]["images"]

        return {"ui": {"images": _a + _b}, "result": (A, B)}



class SFPreviewImage(SaveImage):
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_temp_" + "".join(
            random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5)
        )
        self.compress_level = 1

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "execute"
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
    
    def execute(self, images, prompt=None, extra_pnginfo=None):
        # Save for preview
        result = self.save_images(images, "preview", prompt, extra_pnginfo)
        # Return images for cascading
        return {"ui": result.get("ui", {}), "result": (images,)}


class SFSaveImage(SFPreviewImage):
    def __init__(self):
        super().__init__()
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "watermark": ("*", {}),  # Generic input that accepts any type
            },
            "optional": {
                "filename_prefix": ("STRING", {"default": "SFSave"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "save_images_with_watermark"
    CATEGORY = "SF/Image"
    DESCRIPTION = "Save images with a watermark in the bottom left corner."

    def _add_watermark_to_image(self, img_tensor, watermark_text):
        """Add watermark to a single image tensor."""
        try:
            # Convert tensor to PIL
            pil_img = _tensor_to_pil(img_tensor.to(dtype=torch.float32, device="cpu"))
            
            # Create a copy to draw on
            watermarked = pil_img.copy()
            
            # Import PIL drawing modules
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(watermarked)
            
            # Try to use a decent font, fallback to default
            try:
                # Try to find a system font
                font_size = max(12, min(watermarked.height // 40, 24))  # Scale with image size
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
            
            # Get text dimensions
            if font:
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # Fallback estimation
                text_width = len(watermark_text) * 8
                text_height = 12
            
            # Position in bottom left with some padding
            padding = 10
            x = padding
            y = watermarked.height - text_height - padding
            
            # Draw semi-transparent background rectangle
            bg_padding = 4
            # Create a semi-transparent overlay
            overlay = Image.new('RGBA', watermarked.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle([
                x - bg_padding, 
                y - bg_padding, 
                x + text_width + bg_padding, 
                y + text_height + bg_padding
            ], fill=(0, 0, 0, 128))  # Semi-transparent black
            
            # Composite the overlay onto the image
            watermarked = Image.alpha_composite(watermarked.convert('RGBA'), overlay).convert('RGB')
            
            # Draw the watermark text in white
            draw.text((x, y), watermark_text, fill=(255, 255, 255), font=font)
            
            # Convert back to tensor
            return _pil_to_tensor_nhwc_float(watermarked)
            
        except Exception as e:
            print(f"Warning: Failed to add watermark: {e}")
            return img_tensor  # Return original if watermarking fails

    def save_images_with_watermark(self, images, watermark, filename_prefix="SFSave", prompt=None, extra_pnginfo=None):
        # Convert watermark input to string
        watermark_text = str(watermark) if watermark is not None else ""
        
        # If watermark is empty, just use regular save
        if not watermark_text.strip():
            return self.save_images(images, filename_prefix, prompt, extra_pnginfo)
        
        # Process each image to add watermark
        img_list = _to_list_of_images(images)
        watermarked_images = []
        
        for img in img_list:
            watermarked = self._add_watermark_to_image(img, watermark_text)
            watermarked_images.append(watermarked)
        
        # Combine back into batch tensor if needed
        if len(watermarked_images) > 1:
            watermarked_batch = torch.cat(watermarked_images, dim=0)
        else:
            watermarked_batch = watermarked_images[0]
        
        # Use parent's save_images method and return images for cascading
        result = self.save_images(watermarked_batch, filename_prefix, prompt, extra_pnginfo)
        return {"ui": result.get("ui", {}), "result": (watermarked_batch,)}

class SFWaitForAll:
    """
    A synchronization node with dynamic inputs that appear as you connect them.
    Returns first input, all inputs, count, and last input for maximum flexibility.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "input_1": ("*", {}),
            },
            "optional": {}
        }
        
        # Add additional input slots (up to 20 for flexibility)
        for i in range(2, 21):
            inputs["optional"][f"input_{i}"] = ("*", {})
        
        return inputs

    RETURN_TYPES = ("*", "*", "INT", "*")
    RETURN_NAMES = ("first", "all", "count", "last")
    FUNCTION = "wait_and_execute"
    CATEGORY = "SF/Flow"
    DESCRIPTION = "Dynamic synchronization node. Returns first input, all inputs as list, count, and last input."

    def wait_and_execute(self, input_1, **kwargs):
        """
        Wait for all connected inputs and return first, all, count, and last.
        """
        # Start with the required input
        inputs = [input_1]
        
        # Collect all optional inputs that are not None
        for i in range(2, 21):
            input_key = f"input_{i}"
            if input_key in kwargs and kwargs[input_key] is not None:
                inputs.append(kwargs[input_key])
        
        count = len(inputs)
        first = inputs[0]
        last = inputs[-1]
        all_inputs = inputs
        
        return (first, all_inputs, count, last)
        
        return (output, count)


class SFWaitForImages:
    """
    A specialized synchronization node for IMAGE types with dynamic inputs.
    Returns first image, batched images, grid, and count for maximum flexibility.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "image_1": ("IMAGE", {}),
            },
            "optional": {
                "grid_favor_portrait": ("BOOLEAN", {"default": True}),
            }
        }
        
        # Add additional image input slots (up to 20 for flexibility)
        for i in range(2, 21):
            inputs["optional"][f"image_{i}"] = ("IMAGE", {})
        
        return inputs

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "INT")
    RETURN_NAMES = ("first", "batch", "grid", "count")
    FUNCTION = "wait_and_combine"
    CATEGORY = "SF/Flow"
    DESCRIPTION = "Dynamic image synchronization. Returns first image, batched images, grid layout, and count."

    def wait_and_combine(self, image_1, grid_favor_portrait=True, **kwargs):
        """
        Wait for all connected image inputs and return first, batch, grid, and count.
        
        Args:
            image_1: Required first image
            grid_favor_portrait: Whether to favor portrait aspect for grid layout
            **kwargs: Dynamic image inputs (image_2, image_3, etc.)
        """
        # Start with the required image
        images = [image_1]
        
        # Collect all optional images that are not None
        for i in range(2, 21):
            image_key = f"image_{i}"
            if image_key in kwargs and kwargs[image_key] is not None:
                images.append(kwargs[image_key])
        
        count = len(images)
        first_image = image_1
        
        # Create batch (combine all images into single tensor)
        try:
            # Convert all to list of individual images
            all_imgs = []
            for img_batch in images:
                img_list = _to_list_of_images(img_batch)
                all_imgs.extend(img_list)
            
            # Combine into single batch
            if len(all_imgs) > 1:
                batched_images = torch.cat(all_imgs, dim=0)
            else:
                batched_images = all_imgs[0]
        except Exception as e:
            print(f"Warning: Failed to batch images: {e}")
            batched_images = image_1
        
        # Create grid layout
        try:
            # Use SFImageGrid logic to create grid
            _ensure_torch()
            img_list = _to_list_of_images(batched_images)
            img_list = [_ensure_rgb(im) for im in img_list]
            
            sizes = [(int(t.shape[2]), int(t.shape[1])) for t in img_list]
            target_ratio = 1.5 if grid_favor_portrait else (1.0 / 1.5)
            total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=target_ratio)

            # Create grid using PIL
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
                grid_image = _pil_to_tensor_nhwc_float(grid_pil).to(dtype=torch.float32, device="cpu").contiguous()
            else:
                # Fallback: just return first image as grid
                grid_image = image_1
            
            # Pad grid to multiples of 8
            mul = 8
            if mul > 1:
                h, w = int(grid_image.shape[1]), int(grid_image.shape[2])
                pad_h = (mul - (h % mul)) % mul
                pad_w = (mul - (w % mul)) % mul
                if pad_h or pad_w:
                    grid_image = torch.nn.functional.pad(
                        grid_image, (0, 0, 0, pad_w, 0, pad_h), mode="constant", value=0.0
                    )
            
        except Exception as e:
            print(f"Warning: Failed to create grid: {e}")
            grid_image = image_1
        
        return (first_image, batched_images, grid_image, count)

class SFCombinePath:
    """
    A utility node for combining path components with proper OS separators.
    Takes dynamic inputs and joins them into a valid file path.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "path_1": ("STRING", {"default": ""}),
            },
            "optional": {}
        }
        
        # Add additional path component slots (up to 10 for flexibility)
        for i in range(2, 11):
            inputs["optional"][f"path_{i}"] = ("STRING", {"default": ""})
        
        return inputs

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "combine_paths"
    CATEGORY = "SF/Utils"
    DESCRIPTION = "Combines path components with proper OS separators. Connect path parts and they'll be joined correctly."

    def combine_paths(self, path_1, **kwargs):
        """
        Combine all connected path components into a single path.
        
        Args:
            path_1: Required first path component
            **kwargs: Dynamic path components (path_2, path_3, etc.)
        """
        import os
        
        # Start with the required path component
        path_components = [path_1] if path_1.strip() else []
        
        # Collect all optional path components that are not empty
        for i in range(2, 11):
            path_key = f"path_{i}"
            if path_key in kwargs:
                component = kwargs[path_key]
                if component and component.strip():
                    path_components.append(component.strip())
        
        # Join all components with proper OS separator
        if not path_components:
            combined_path = ""
        else:
            # Use os.path.join for proper path combination
            combined_path = os.path.join(*path_components)
        
        return (combined_path,)


class SFPathInfo:
    """
    A utility node for extracting information from file paths.
    Returns directory, filename, name without extension, and extension.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("directory", "filename", "name", "extension", "absolute")
    FUNCTION = "extract_path_info"
    CATEGORY = "SF/Utils"
    DESCRIPTION = "Extracts path information: directory, filename, name without extension, extension, and absolute path."

    def extract_path_info(self, path):
        """
        Extract various components from a file path.
        
        Args:
            path: Input file path
            
        Returns:
            directory: Directory part of the path
            filename: Full filename with extension
            name: Filename without extension
            extension: File extension (with dot)
            absolute: Absolute version of the path
        """
        import os
        
        if not path or not path.strip():
            return ("", "", "", "", "")
        
        path = path.strip()
        
        # Get directory and filename
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        
        # Split filename into name and extension
        name, extension = os.path.splitext(filename)
        
        # Get absolute path
        try:
            absolute = os.path.abspath(path)
        except Exception:
            absolute = path  # fallback if abspath fails
        
        return (directory, filename, name, extension, absolute)


class SFMakePath:
    """
    A utility node for constructing paths from components.
    More explicit than SFCombinePath with named inputs for common path parts.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "base_dir": ("STRING", {"default": ""}),
                "subfolder": ("STRING", {"default": ""}),
                "filename": ("STRING", {"default": ""}),
                "extension": ("STRING", {"default": ""}),
                "prefix": ("STRING", {"default": ""}),
                "suffix": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("full_path", "directory", "filename")
    FUNCTION = "make_path"
    CATEGORY = "SF/Utils"
    DESCRIPTION = "Constructs file paths from named components: base_dir/subfolder/prefix+filename+suffix.extension"

    def make_path(self, base_dir="", subfolder="", filename="", extension="", prefix="", suffix=""):
        """
        Construct a file path from named components.
        
        Args:
            base_dir: Base directory
            subfolder: Subdirectory within base
            filename: Base filename
            extension: File extension (with or without dot)
            prefix: Prefix to add to filename
            suffix: Suffix to add to filename
        """
        import os
        
        # Build the filename
        final_filename = ""
        if filename.strip():
            final_filename = filename.strip()
            
            # Add prefix and suffix
            if prefix.strip():
                final_filename = prefix.strip() + final_filename
            if suffix.strip():
                final_filename = final_filename + suffix.strip()
            
            # Add extension
            if extension.strip():
                ext = extension.strip()
                if not ext.startswith('.'):
                    ext = '.' + ext
                final_filename = final_filename + ext
        
        # Build the directory path
        directory_parts = []
        if base_dir.strip():
            directory_parts.append(base_dir.strip())
        if subfolder.strip():
            directory_parts.append(subfolder.strip())
        
        directory = os.path.join(*directory_parts) if directory_parts else ""
        
        # Build the full path
        if directory and final_filename:
            full_path = os.path.join(directory, final_filename)
        elif directory:
            full_path = directory
        elif final_filename:
            full_path = final_filename
        else:
            full_path = ""
        
        return (full_path, directory, final_filename)
class SFUniqueDir:
    """
    A utility node for generating unique directory names with auto-incrementing numbers.
    Creates paths like 'photos/baby/1/', 'photos/baby/2/', etc., automatically finding the next available number.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "path_1": ("STRING", {"default": ""}),
            },
            "optional": {
                "create_directory": ("BOOLEAN", {"default": True}),
                "start_number": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "number_format": (["1", "01", "001", "0001"], {"default": "1"}),
            }
        }
        
        # Add additional path component slots (up to 10 for flexibility)
        for i in range(2, 11):
            inputs["optional"][f"path_{i}"] = ("STRING", {"default": ""})
        
        return inputs

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("full_path", "base_path", "number")
    FUNCTION = "generate_unique_dir"
    CATEGORY = "SF/Utils"
    DESCRIPTION = "Generates unique directory names with auto-incrementing numbers. Creates 'path/1/', 'path/2/', etc."

    def generate_unique_dir(self, path_1, create_directory=True, start_number=1, number_format="1", **kwargs):
        """
        Generate a unique directory path with auto-incrementing number.
        
        Args:
            path_1: Required first path component
            create_directory: Whether to actually create the directory
            start_number: Starting number for the sequence
            number_format: How to format the number (1, 01, 001, 0001)
            **kwargs: Dynamic path components (path_2, path_3, etc.)
        """
        import os
        
        # Collect all path components
        path_components = [path_1] if path_1.strip() else []
        
        for i in range(2, 11):
            path_key = f"path_{i}"
            if path_key in kwargs:
                component = kwargs[path_key]
                if component and component.strip():
                    path_components.append(component.strip())
        
        if not path_components:
            return ("", "", 0)
        
        # Create base path from components
        base_path = os.path.join(*path_components)
        
        # Find the next available number
        current_number = start_number
        while True:
            # Format the number based on the selected format
            if number_format == "01":
                number_str = f"{current_number:02d}"
            elif number_format == "001":
                number_str = f"{current_number:03d}"
            elif number_format == "0001":
                number_str = f"{current_number:04d}"
            else:  # "1"
                number_str = str(current_number)
            
            # Create the full path with number
            full_path = os.path.join(base_path, number_str)
            
            # Check if this path already exists
            if not os.path.exists(full_path):
                break
            
            current_number += 1
            
            # Safety check to prevent infinite loops
            if current_number > 9999:
                print("Warning: Reached maximum directory number (9999)")
                break
        
        # Create the directory if requested
        if create_directory:
            try:
                os.makedirs(full_path, exist_ok=True)
                print(f"Created directory: {full_path}")
            except Exception as e:
                print(f"Warning: Failed to create directory {full_path}: {e}")
        
        return (full_path, base_path, current_number)


class SFIncrementalPath:
    """
    A utility node for creating incremental file paths with auto-incrementing numbers.
    Creates paths like 'output/image_001.png', 'output/image_002.png', etc.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_path": ("STRING", {"default": "output"}),
                "filename": ("STRING", {"default": "image"}),
            },
            "optional": {
                "extension": ("STRING", {"default": "png"}),
                "start_number": ("INT", {"default": 1, "min": 1, "max": 9999}),
                "number_format": (["1", "01", "001", "0001"], {"default": "001"}),
                "separator": ("STRING", {"default": "_"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("full_path", "directory", "filename", "number")
    FUNCTION = "generate_incremental_path"
    CATEGORY = "SF/Utils"
    DESCRIPTION = "Generates incremental file paths with auto-incrementing numbers. Creates 'path/file_001.ext', 'path/file_002.ext', etc."

    def generate_incremental_path(self, base_path, filename, extension="png", start_number=1, 
                                 number_format="001", separator="_"):
        """
        Generate an incremental file path with auto-incrementing number.
        
        Args:
            base_path: Directory path
            filename: Base filename (without extension)
            extension: File extension
            start_number: Starting number for the sequence
            number_format: How to format the number
            separator: Separator between filename and number
        """
        import os
        
        # Clean inputs
        base_path = base_path.strip() if base_path else "output"
        filename = filename.strip() if filename else "file"
        extension = extension.strip() if extension else "png"
        separator = separator.strip() if separator else "_"
        
        # Ensure extension has dot
        if extension and not extension.startswith('.'):
            extension = '.' + extension
        
        # Find the next available number
        current_number = start_number
        while True:
            # Format the number based on the selected format
            if number_format == "01":
                number_str = f"{current_number:02d}"
            elif number_format == "001":
                number_str = f"{current_number:03d}"
            elif number_format == "0001":
                number_str = f"{current_number:04d}"
            else:  # "1"
                number_str = str(current_number)
            
            # Create the filename with number
            numbered_filename = f"{filename}{separator}{number_str}{extension}"
            
            # Create the full path
            full_path = os.path.join(base_path, numbered_filename)
            
            # Check if this file already exists
            if not os.path.exists(full_path):
                break
            
            current_number += 1
            
            # Safety check to prevent infinite loops
            if current_number > 9999:
                print("Warning: Reached maximum file number (9999)")
                break
        
        return (full_path, base_path, numbered_filename, current_number)


class SFTimestampPath:
    """
    A utility node for creating timestamp-based paths.
    Creates paths with current date/time for unique naming.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "base_path": ("STRING", {"default": "output"}),
                "filename": ("STRING", {"default": ""}),
                "extension": ("STRING", {"default": "png"}),
                "timestamp_format": ([
                    "YYYYMMDD_HHMMSS",
                    "YYYY-MM-DD_HH-MM-SS", 
                    "YYYYMMDD",
                    "HHMMSS",
                    "YYYY/MM/DD",
                    "unix"
                ], {"default": "YYYYMMDD_HHMMSS"}),
                "separator": ("STRING", {"default": "_"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("full_path", "directory", "filename")
    FUNCTION = "generate_timestamp_path"
    CATEGORY = "SF/Utils"
    DESCRIPTION = "Generates timestamp-based paths for unique file naming. Uses current date/time."

    def generate_timestamp_path(self, base_path="output", filename="", extension="png", 
                               timestamp_format="YYYYMMDD_HHMMSS", separator="_"):
        """
        Generate a timestamp-based file path.
        
        Args:
            base_path: Directory path
            filename: Base filename (optional)
            extension: File extension
            timestamp_format: Format for the timestamp
            separator: Separator between filename and timestamp
        """
        import os
        from datetime import datetime
        import time
        
        # Clean inputs
        base_path = base_path.strip() if base_path else "output"
        filename = filename.strip() if filename else ""
        extension = extension.strip() if extension else "png"
        separator = separator.strip() if separator else "_"
        
        # Ensure extension has dot
        if extension and not extension.startswith('.'):
            extension = '.' + extension
        
        # Generate timestamp
        now = datetime.now()
        
        if timestamp_format == "YYYYMMDD_HHMMSS":
            timestamp = now.strftime("%Y%m%d_%H%M%S")
        elif timestamp_format == "YYYY-MM-DD_HH-MM-SS":
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        elif timestamp_format == "YYYYMMDD":
            timestamp = now.strftime("%Y%m%d")
        elif timestamp_format == "HHMMSS":
            timestamp = now.strftime("%H%M%S")
        elif timestamp_format == "YYYY/MM/DD":
            timestamp = now.strftime("%Y/%m/%d")
        elif timestamp_format == "unix":
            timestamp = str(int(time.time()))
        else:
            timestamp = now.strftime("%Y%m%d_%H%M%S")  # fallback
        
        # Build filename
        if filename:
            if timestamp_format == "YYYY/MM/DD":
                # Special case: timestamp becomes part of directory structure
                directory = os.path.join(base_path, timestamp)
                final_filename = f"{filename}{extension}"
            else:
                directory = base_path
                final_filename = f"{filename}{separator}{timestamp}{extension}"
        else:
            if timestamp_format == "YYYY/MM/DD":
                directory = os.path.join(base_path, timestamp)
                final_filename = f"file{extension}"
            else:
                directory = base_path
                final_filename = f"{timestamp}{extension}"
        
        # Create full path
        full_path = os.path.join(directory, final_filename)
        
        return (full_path, directory, final_filename)