#!/usr/bin/env python3

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import just the layout function we want to test
from backend.image_nodes import _choose_layout_by_sizes


def test_layout_logic():
    """Test the layout selection logic without requiring torch."""
    print("Testing layout selection logic...")
    
    # Test case 1: 4 square images
    sizes = [(100, 100), (100, 100), (100, 100), (100, 100)]
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    
    print(f"\n4 square images (100x100):")
    print(f"  Layout: {cols} columns")
    print(f"  Total size: {total_w}x{total_h}")
    print(f"  Row heights: {row_heights}")
    print(f"  Aspect ratio: {total_h/total_w:.2f}")
    
    # Should prefer 2x2 layout for portrait
    assert cols == 2, f"Expected 2 columns for 4 squares, got {cols}"
    assert total_w == 200, f"Expected width 200, got {total_w}"
    assert total_h == 200, f"Expected height 200, got {total_h}"
    
    # Test case 2: Different sized images
    sizes = [(200, 100), (100, 150), (150, 120)]
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    
    print(f"\n3 different sized images:")
    print(f"  Sizes: {sizes}")
    print(f"  Layout: {cols} columns")
    print(f"  Total size: {total_w}x{total_h}")
    print(f"  Row heights: {row_heights}")
    print(f"  Aspect ratio: {total_h/total_w:.2f}")
    
    # Test case 3: Single image
    sizes = [(300, 200)]
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    
    print(f"\nSingle image (300x200):")
    print(f"  Layout: {cols} columns")
    print(f"  Total size: {total_w}x{total_h}")
    print(f"  Row heights: {row_heights}")
    
    assert cols == 1, f"Expected 1 column for single image, got {cols}"
    assert total_w == 300, f"Expected width 300, got {total_w}"
    assert total_h == 200, f"Expected height 200, got {total_h}"
    
    # Test case 4: Many small images (should create multiple rows)
    sizes = [(50, 50)] * 9  # 9 small squares
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    
    print(f"\n9 small squares (50x50):")
    print(f"  Layout: {cols} columns")
    print(f"  Total size: {total_w}x{total_h}")
    print(f"  Row heights: {row_heights}")
    print(f"  Aspect ratio: {total_h/total_w:.2f}")
    
    # Should create a roughly square-ish grid, maybe 3x3
    assert cols <= 4, f"Too many columns for 9 images: {cols}"
    assert len(row_heights) >= 2, f"Should have multiple rows, got {len(row_heights)}"
    
    # Test case 5: Landscape preference
    sizes = [(100, 100)] * 6
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=0.67)  # 1/1.5
    
    print(f"\n6 squares with landscape preference:")
    print(f"  Layout: {cols} columns")
    print(f"  Total size: {total_w}x{total_h}")
    print(f"  Row heights: {row_heights}")
    print(f"  Aspect ratio: {total_h/total_w:.2f}")
    
    # Should prefer wider layout (more columns, fewer rows)
    landscape_ratio = total_h / total_w
    assert landscape_ratio < 1.0, f"Landscape should be wider than tall, ratio: {landscape_ratio:.2f}"
    
    print("\n✓ All layout tests passed!")


def test_edge_cases():
    """Test edge cases for layout logic."""
    print("\nTesting edge cases...")
    
    # Empty list (should not crash)
    try:
        sizes = []
        result = _choose_layout_by_sizes(sizes, target_ratio=1.5)
        print("  Empty list handled")
    except Exception as e:
        print(f"  Empty list error (expected): {e}")
    
    # Single very wide image
    sizes = [(1000, 10)]
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    print(f"  Very wide image: {total_w}x{total_h}, cols={cols}")
    assert total_w == 1000 and total_h == 10, "Should preserve original dimensions"
    
    # Single very tall image
    sizes = [(10, 1000)]
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    print(f"  Very tall image: {total_w}x{total_h}, cols={cols}")
    assert total_w == 10 and total_h == 1000, "Should preserve original dimensions"
    
    print("  ✓ Edge cases handled correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("SFImageGrid Layout Logic Test")
    print("=" * 60)
    
    try:
        test_layout_logic()
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("🎉 Layout logic tests passed! Core functionality working.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)