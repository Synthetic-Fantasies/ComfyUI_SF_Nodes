#!/usr/bin/env python3

"""
Integration example showing how SFImageGrid would be used in ComfyUI.
This doesn't run the actual node (requires ComfyUI environment) but shows the expected usage.
"""

def example_usage():
    """Example of how SFImageGrid would be used in a ComfyUI workflow."""
    
    print("SFImageGrid Usage Example")
    print("=" * 40)
    
    # This is how the node would be instantiated in ComfyUI
    print("1. Node instantiation:")
    print("   node = SFImageGrid()")
    
    print("\n2. Input types:")
    print("   Required:")
    print("     - images: IMAGE tensor (batch of images)")
    print("   Optional:")
    print("     - favor_portrait: BOOLEAN (default: True)")
    print("     - filename_prefix: STRING (default: 'SFGrid')")
    
    print("\n3. Example calls:")
    print("   # Basic usage with 4 images")
    print("   result = node.execute(image_batch)")
    print("   grid_image = result[0]  # Returns single grid image")
    
    print("\n   # Custom settings")
    print("   result = node.execute(")
    print("       images=image_batch,")
    print("       favor_portrait=False,  # Prefer landscape layout")
    print("       filename_prefix='MyGrid'")
    print("   )")
    
    print("\n4. Layout behavior:")
    print("   - Automatically chooses optimal grid layout")
    print("   - Preserves original image sizes (no resizing)")
    print("   - Portrait preference: taller grids (more rows)")
    print("   - Landscape preference: wider grids (more columns)")
    print("   - Handles mixed image sizes intelligently")
    
    print("\n5. Output:")
    print("   - Single IMAGE tensor containing the grid")
    print("   - Padded to multiples of 8 for ComfyUI compatibility")
    print("   - Can be saved or passed to other nodes")
    
    print("\n6. Real-world scenarios:")
    scenarios = [
        ("4 generated variations", "2x2 grid"),
        ("6 style comparisons", "2x3 or 3x2 grid"),
        ("9 parameter tests", "3x3 grid"),
        ("Mixed size images", "Optimal layout preserving sizes")
    ]
    
    for scenario, layout in scenarios:
        print(f"   - {scenario}: {layout}")
    
    print("\n✓ SFImageGrid is ready for ComfyUI integration!")


if __name__ == "__main__":
    example_usage()