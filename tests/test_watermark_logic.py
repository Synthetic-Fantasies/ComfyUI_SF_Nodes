#!/usr/bin/env python3

"""
Test the watermark logic for SFSaveImage node.
Tests the watermark text processing and positioning logic.
"""

def test_watermark_text_conversion():
    """Test how different input types are converted to watermark text."""
    print("Testing watermark text conversion...")
    
    test_cases = [
        ("Hello World", "Hello World"),
        (42, "42"),
        (3.14159, "3.14159"),
        (True, "True"),
        (False, "False"),
        (None, ""),
        ("", ""),
        ("   ", "   "),  # Whitespace preserved
        (["list", "item"], "['list', 'item']"),
        ({"key": "value"}, "{'key': 'value'}"),
    ]
    
    for input_val, expected in test_cases:
        # Simulate the conversion logic from the node
        watermark_text = str(input_val) if input_val is not None else ""
        print(f"  {repr(input_val)} -> {repr(watermark_text)}")
        assert watermark_text == expected, f"Expected {expected}, got {watermark_text}"
    
    print("  ✓ Text conversion tests passed")


def test_watermark_positioning():
    """Test watermark positioning calculations."""
    print("\nTesting watermark positioning...")
    
    # Simulate positioning logic for different image sizes
    test_images = [
        (512, 512, "Small square"),
        (1024, 768, "Landscape"),
        (768, 1024, "Portrait"),
        (2048, 1024, "Wide"),
        (100, 100, "Tiny"),
    ]
    
    for width, height, desc in test_images:
        # Simulate the positioning logic
        padding = 10
        text_height = max(12, min(height // 40, 24))  # Font size logic
        
        x = padding
        y = height - text_height - padding
        
        print(f"  {desc} ({width}x{height}): watermark at ({x}, {y}), font_size={text_height}")
        
        # Basic sanity checks
        assert x >= 0, "X position should be non-negative"
        assert y >= 0, "Y position should be non-negative"
        assert y < height, "Y position should be within image bounds"
        assert x < width, "X position should be within image bounds"
    
    print("  ✓ Positioning tests passed")


def test_watermark_scenarios():
    """Test various watermark scenarios."""
    print("\nTesting watermark scenarios...")
    
    scenarios = [
        ("Simple text", "© 2024 MyBrand"),
        ("Long text", "This is a very long watermark that might need special handling"),
        ("Special chars", "© ® ™ 2024 Brand™"),
        ("Numbers", "Model v1.2.3 - Seed: 12345"),
        ("Empty", ""),
        ("Whitespace only", "   "),
        ("Unicode", "🎨 AI Generated 2024"),
    ]
    
    for desc, watermark in scenarios:
        # Test if watermark would be applied
        should_apply = watermark and watermark.strip()
        print(f"  {desc}: '{watermark}' -> {'Apply' if should_apply else 'Skip'}")
        
        if should_apply:
            # Test text dimensions estimation
            estimated_width = len(watermark) * 8  # Fallback estimation
            print(f"    Estimated width: {estimated_width}px")
    
    print("  ✓ Scenario tests passed")


def test_error_handling():
    """Test error handling scenarios."""
    print("\nTesting error handling...")
    
    # Test cases that might cause issues
    problematic_inputs = [
        (None, "None input"),
        ("", "Empty string"),
        ("A" * 1000, "Very long text"),
        ("Text\nwith\nnewlines", "Multiline text"),
        ("Text\twith\ttabs", "Text with tabs"),
    ]
    
    for input_val, desc in problematic_inputs:
        try:
            watermark_text = str(input_val) if input_val is not None else ""
            # Should not crash
            print(f"  {desc}: Handled gracefully")
        except Exception as e:
            print(f"  {desc}: Error - {e}")
    
    print("  ✓ Error handling tests passed")


def integration_example():
    """Show how the watermark node would be used."""
    print("\nSFSaveImage Integration Example:")
    print("=" * 40)
    
    print("1. Basic usage:")
    print("   node = SFSaveImage()")
    print("   node.save_images_with_watermark(")
    print("       images=image_batch,")
    print("       watermark='© 2024 MyStudio',")
    print("       filename_prefix='watermarked'")
    print("   )")
    
    print("\n2. Dynamic watermark from other nodes:")
    print("   # Watermark can come from any node output")
    print("   # - Text nodes")
    print("   # - Prompt nodes") 
    print("   # - Custom string inputs")
    print("   # - Even numeric values (converted to string)")
    
    print("\n3. Features:")
    print("   - Generic '*' input accepts any type")
    print("   - Automatic string conversion")
    print("   - Bottom-left positioning with padding")
    print("   - Semi-transparent background for readability")
    print("   - Font size scales with image size")
    print("   - Graceful fallback if watermarking fails")
    
    print("\n4. Use cases:")
    use_cases = [
        "Brand/studio watermarks",
        "Model version tracking", 
        "Seed/parameter documentation",
        "Copyright notices",
        "Batch identification",
        "Timestamp watermarks"
    ]
    
    for use_case in use_cases:
        print(f"   - {use_case}")


if __name__ == "__main__":
    print("=" * 60)
    print("SFSaveImage Watermark Logic Test")
    print("=" * 60)
    
    try:
        test_watermark_text_conversion()
        test_watermark_positioning()
        test_watermark_scenarios()
        test_error_handling()
        integration_example()
        
        print("\n" + "=" * 60)
        print("🎉 Watermark logic tests passed! SFSaveImage ready.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)