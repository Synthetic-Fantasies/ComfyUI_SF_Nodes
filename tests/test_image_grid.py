#!/usr/bin/env python3

import sys
import os
import torch
import numpy as np
from PIL import Image

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock ComfyUI dependencies
class MockFolderPaths:
    def get_temp_directory(self):
        return "temp"
    def get_output_directory(self):
        return "output"

class MockSaveImage:
    pass

class MockPreviewImage:
    pass

# Mock the ComfyUI modules
sys.modules['folder_paths'] = MockFolderPaths()
sys.modules['nodes'] = type('MockNodes', (), {
    'SaveImage': MockSaveImage,
    'PreviewImage': MockPreviewImage
})()

from backend.image_nodes import SFImageGrid


def create_test_image_tensor(width: int, height: int, color: tuple = (255, 0, 0)) -> torch.Tensor:
    """Create a test image tensor in NHWC format with specified dimensions and color."""
    # Create RGB image array
    img_array = np.full((height, width, 3), color, dtype=np.uint8)
    
    # Convert to PIL and then to tensor (following the same path as the actual code)
    pil_img = Image.fromarray(img_array, mode="RGB")
    arr = np.asarray(pil_img.convert("RGB"), dtype="float32") / 255.0
    tensor = torch.from_numpy(arr).unsqueeze(0)  # Add batch dimension -> NHWC
    
    return tensor


def test_single_image():
    """Test grid with a single image."""
    print("Testing single image...")
    
    node = SFImageGrid()
    
    # Create a single 100x100 red image
    img = create_test_image_tensor(100, 100, (255, 0, 0))
    
    result = node.execute(img, favor_portrait=True, filename_prefix="test_single")
    canvas = result[0]
    
    print(f"  Input: 1 image (100x100)")
    print(f"  Output shape: {canvas.shape}")
    print(f"  Expected: Should be close to input size with padding")
    
    # Check basic properties
    assert canvas.shape[0] == 1, "Batch size should be 1"
    assert canvas.shape[3] == 3, "Should have 3 channels (RGB)"
    assert canvas.shape[1] >= 100, "Height should be at least input height"
    assert canvas.shape[2] >= 100, "Width should be at least input width"
    
    print("  ✓ Single image test passed")


def test_multiple_same_size():
    """Test grid with multiple images of the same size."""
    print("\nTesting multiple images (same size)...")
    
    node = SFImageGrid()
    
    # Create 4 images of same size with different colors
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    images = []
    
    for color in colors:
        img = create_test_image_tensor(100, 100, color)
        images.append(img)
    
    # Concatenate along batch dimension
    batch_tensor = torch.cat(images, dim=0)
    
    result = node.execute(batch_tensor, favor_portrait=True, filename_prefix="test_multi_same")
    canvas = result[0]
    
    print(f"  Input: 4 images (100x100 each)")
    print(f"  Output shape: {canvas.shape}")
    
    # For 4 images with portrait preference, expect 2x2 or similar layout
    assert canvas.shape[0] == 1, "Batch size should be 1"
    assert canvas.shape[3] == 3, "Should have 3 channels (RGB)"
    assert canvas.shape[1] >= 200, "Height should accommodate at least 2 rows"
    assert canvas.shape[2] >= 200, "Width should accommodate at least 2 columns"
    
    print("  ✓ Multiple same-size images test passed")


def test_different_sizes():
    """Test grid with images of different sizes."""
    print("\nTesting images with different sizes...")
    
    node = SFImageGrid()
    
    # Create images with different sizes
    sizes_colors = [
        ((100, 50), (255, 0, 0)),    # Wide red
        ((50, 100), (0, 255, 0)),    # Tall green  
        ((75, 75), (0, 0, 255)),     # Square blue
        ((120, 80), (255, 255, 0)),  # Wide yellow
    ]
    
    images = []
    for (w, h), color in sizes_colors:
        img = create_test_image_tensor(w, h, color)
        images.append(img)
    
    # Concatenate along batch dimension
    batch_tensor = torch.cat(images, dim=0)
    
    result = node.execute(batch_tensor, favor_portrait=True, filename_prefix="test_multi_diff")
    canvas = result[0]
    
    print(f"  Input: 4 images with different sizes")
    print(f"  Sizes: {[(w, h) for (w, h), _ in sizes_colors]}")
    print(f"  Output shape: {canvas.shape}")
    
    # Basic checks
    assert canvas.shape[0] == 1, "Batch size should be 1"
    assert canvas.shape[3] == 3, "Should have 3 channels (RGB)"
    
    # Should be large enough to contain all images
    max_w = max(w for (w, h), _ in sizes_colors)
    max_h = max(h for (w, h), _ in sizes_colors)
    assert canvas.shape[2] >= max_w, f"Width should be at least {max_w}"
    assert canvas.shape[1] >= max_h, f"Height should be at least {max_h}"
    
    print("  ✓ Different sizes test passed")


def test_landscape_preference():
    """Test landscape vs portrait preference."""
    print("\nTesting landscape preference...")
    
    node = SFImageGrid()
    
    # Create 6 small images
    images = []
    for i in range(6):
        color = (i * 40, (i * 60) % 255, (i * 80) % 255)
        img = create_test_image_tensor(50, 50, color)
        images.append(img)
    
    batch_tensor = torch.cat(images, dim=0)
    
    # Test portrait preference
    result_portrait = node.execute(batch_tensor, favor_portrait=True, filename_prefix="test_portrait")
    canvas_portrait = result_portrait[0]
    
    # Test landscape preference  
    result_landscape = node.execute(batch_tensor, favor_portrait=False, filename_prefix="test_landscape")
    canvas_landscape = result_landscape[0]
    
    print(f"  Input: 6 images (50x50 each)")
    print(f"  Portrait output: {canvas_portrait.shape}")
    print(f"  Landscape output: {canvas_landscape.shape}")
    
    # Portrait should be taller than wide, landscape should be wider than tall
    portrait_ratio = canvas_portrait.shape[1] / canvas_portrait.shape[2]  # height/width
    landscape_ratio = canvas_landscape.shape[1] / canvas_landscape.shape[2]  # height/width
    
    print(f"  Portrait ratio (H/W): {portrait_ratio:.2f}")
    print(f"  Landscape ratio (H/W): {landscape_ratio:.2f}")
    
    # Portrait should have higher ratio (taller), landscape should have lower ratio (wider)
    assert portrait_ratio > landscape_ratio, "Portrait should be taller relative to width than landscape"
    
    print("  ✓ Landscape preference test passed")


def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")
    
    node = SFImageGrid()
    
    # Test with very small image
    tiny_img = create_test_image_tensor(1, 1, (128, 128, 128))
    result = node.execute(tiny_img, favor_portrait=True, filename_prefix="test_tiny")
    canvas = result[0]
    
    print(f"  Tiny image (1x1) output: {canvas.shape}")
    assert canvas.shape[1] >= 1 and canvas.shape[2] >= 1, "Should handle tiny images"
    
    # Test with single very wide image
    wide_img = create_test_image_tensor(500, 10, (200, 100, 50))
    result = node.execute(wide_img, favor_portrait=True, filename_prefix="test_wide")
    canvas = result[0]
    
    print(f"  Wide image (500x10) output: {canvas.shape}")
    assert canvas.shape[2] >= 500, "Should preserve wide image width"
    
    print("  ✓ Edge cases test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("SFImageGrid Test Harness")
    print("=" * 60)
    
    try:
        test_single_image()
        test_multiple_same_size()
        test_different_sizes()
        test_landscape_preference()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! SFImageGrid is working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)