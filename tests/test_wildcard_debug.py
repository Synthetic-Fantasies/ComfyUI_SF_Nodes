"""
Test harness for debugging SFWildcardsPromptMatrix node.
Run this directly or use the VS Code debugger.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import backend modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock folder_paths module that ComfyUI provides
class MockFolderPaths:
    __file__ = str(project_root / "backend" / "wildcard_nodes.py")

sys.modules['folder_paths'] = MockFolderPaths()

# Now import the node
from backend.wildcard_nodes import SFWildcardsPromptMatrix


def print_separator(title=""):
    print("\n" + "=" * 60)
    if title:
        print(f" {title}")
        print("=" * 60)


def test_basic_generation():
    """Test basic wildcard generation"""
    print_separator("Test: Basic Generation")
    
    node = SFWildcardsPromptMatrix()
    
    # Test parameters
    prompt = "A photo of __animals__ in __colors__"
    count = 4
    seed = 42
    deterministic = True
    
    print(f"Prompt: {prompt}")
    print(f"Count: {count}")
    print(f"Seed: {seed}")
    print(f"Deterministic: {deterministic}")
    
    # Generate
    results = node.generate(prompt, count, seed, deterministic)
    prompts, wildcard_lines, tags, tags_list, seeds = results
    
    # Display results
    print_separator("Results")
    for i, (p, wl, t, tl, s) in enumerate(zip(prompts, wildcard_lines, tags, tags_list, seeds)):
        print(f"\n[{i}] Seed: {s}")
        print(f"    Prompt: {p}")
        print(f"    Wildcards: {wl}")
        print(f"    Tags: {t}")
        print(f"    Tags List: {tl}")


def test_seed_reproducibility():
    """Test that same seed produces same results"""
    print_separator("Test: Seed Reproducibility")
    
    node = SFWildcardsPromptMatrix()
    
    prompt = "A __animals__ wearing __colors__ clothes"
    seed = 123
    
    # Generate twice with same seed
    results1 = node.generate(prompt, 3, seed, True)
    results2 = node.generate(prompt, 3, seed, True)
    
    print("First run:")
    for i, p in enumerate(results1[0]):
        print(f"  [{i}] {p}")
    
    print("\nSecond run:")
    for i, p in enumerate(results2[0]):
        print(f"  [{i}] {p}")
    
    # Check if they match
    if results1[0] == results2[0]:
        print("\n✓ Results are identical (deterministic)")
    else:
        print("\n✗ Results differ (non-deterministic)")


def test_non_deterministic():
    """Test non-deterministic mode"""
    print_separator("Test: Non-Deterministic Mode")
    
    node = SFWildcardsPromptMatrix()
    
    prompt = "__animals__ and __colors__"
    
    # Generate with deterministic=False
    results = node.generate(prompt, 5, 0, False)
    prompts, _, _, _, seeds = results
    
    print("Generated prompts with random seeds:")
    for i, (p, s) in enumerate(zip(prompts, seeds)):
        print(f"  [{i}] Seed {s}: {p}")


def test_single_seed_regeneration():
    """Test regenerating a specific prompt using its seed"""
    print_separator("Test: Single Seed Regeneration")
    
    node = SFWildcardsPromptMatrix()
    
    prompt = "A __colors__ __animals__"
    
    # Generate multiple prompts
    results = node.generate(prompt, 5, 100, True)
    prompts, _, _, _, seeds = results
    
    print("Original batch:")
    for i, (p, s) in enumerate(zip(prompts, seeds)):
        print(f"  [{i}] Seed {s}: {p}")
    
    # Pick one to regenerate (e.g., index 2)
    target_idx = 2
    target_seed = seeds[target_idx]
    target_prompt = prompts[target_idx]
    
    print(f"\nRegenerating prompt at index {target_idx} using seed {target_seed}...")
    
    # Regenerate with that specific seed
    regen_results = node.generate(prompt, 1, target_seed, True)
    regen_prompt = regen_results[0][0]
    
    print(f"  Original: {target_prompt}")
    print(f"  Regenerated: {regen_prompt}")
    
    if target_prompt == regen_prompt:
        print("\n✓ Successfully regenerated exact prompt")
    else:
        print("\n✗ Regeneration mismatch")


def test_edge_cases():
    """Test edge cases"""
    print_separator("Test: Edge Cases")
    
    node = SFWildcardsPromptMatrix()
    
    # Test with no wildcards
    print("\n1. No wildcards:")
    results = node.generate("Just a plain prompt", 2, 0, True)
    for p in results[0]:
        print(f"   {p}")
    
    # Test with single wildcard
    print("\n2. Single wildcard:")
    results = node.generate("Only __animals__", 2, 0, True)
    for p in results[0]:
        print(f"   {p}")
    
    # Test with repeated wildcard
    print("\n3. Repeated wildcard:")
    results = node.generate("__animals__ and __animals__", 2, 0, True)
    for p in results[0]:
        print(f"   {p}")


def main():
    """Run all tests"""
    print("\n" + "█" * 60)
    print("  SFWildcardsPromptMatrix Debug Test Harness")
    print("█" * 60)
    
    try:
        test_basic_generation()
        test_seed_reproducibility()
        test_non_deterministic()
        test_single_seed_regeneration()
        test_edge_cases()
        
        print_separator("All Tests Complete")
        print("✓ Test harness completed successfully\n")
        
    except Exception as e:
        print_separator("ERROR")
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
