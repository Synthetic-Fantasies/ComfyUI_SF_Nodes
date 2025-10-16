#!/usr/bin/env python3

from typing import List, Tuple


def _choose_layout_by_sizes(sizes: List[Tuple[int, int]], target_ratio: float = 1.5) -> Tuple[int, int, int, List[int]]:
    """Choose columns count to approximate portrait aspect using original sizes.
    Returns: (total_w, total_h, cols, row_heights)
    """
    n = len(sizes)
    if n == 0:
        return 0, 0, 0, []
        
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


def test_layout_logic():
    """Test the layout selection logic."""
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
    
    # Empty list
    sizes = []
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    print(f"  Empty list: {total_w}x{total_h}, cols={cols}")
    assert total_w == 0 and total_h == 0 and cols == 0, "Empty list should return zeros"
    
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
    
    # Mixed aspect ratios
    sizes = [(400, 100), (100, 400), (200, 200)]  # wide, tall, square
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    print(f"  Mixed aspects: {total_w}x{total_h}, cols={cols}, rows={row_heights}")
    
    print("  ✓ Edge cases handled correctly")


def test_layout_decisions():
    """Test specific layout decision scenarios."""
    print("\nTesting layout decision scenarios...")
    
    # 2 images: should they be stacked (1 col) or side-by-side (2 cols)?
    sizes = [(100, 100), (100, 100)]
    
    # Portrait preference should stack them (1 column)
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    print(f"  2 squares (portrait): {cols} cols, ratio={total_h/total_w:.2f}")
    
    # Landscape preference should put them side-by-side (2 columns)
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=0.67)
    print(f"  2 squares (landscape): {cols} cols, ratio={total_h/total_w:.2f}")
    
    # 3 images: various layouts possible
    sizes = [(100, 100), (100, 100), (100, 100)]
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=1.5)
    print(f"  3 squares (portrait): {cols} cols, ratio={total_h/total_w:.2f}")
    
    total_w, total_h, cols, row_heights = _choose_layout_by_sizes(sizes, target_ratio=0.67)
    print(f"  3 squares (landscape): {cols} cols, ratio={total_h/total_w:.2f}")
    
    print("  ✓ Layout decisions look reasonable")


if __name__ == "__main__":
    print("=" * 60)
    print("SFImageGrid Layout Logic Test (Standalone)")
    print("=" * 60)
    
    try:
        test_layout_logic()
        test_edge_cases()
        test_layout_decisions()
        
        print("\n" + "=" * 60)
        print("🎉 Layout logic tests passed! Core functionality working.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)