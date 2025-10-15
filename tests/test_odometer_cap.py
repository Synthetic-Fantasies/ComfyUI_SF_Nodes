"""
Test that deterministic mode caps at total combinations.
"""
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Mock folder_paths module
class MockFolderPaths:
    __file__ = str(project_root / "backend" / "wildcard_nodes.py")

sys.modules['folder_paths'] = MockFolderPaths()

from backend.wildcard_nodes import SFWildcardsPromptMatrix


def test_odometer_cap():
    """Test that deterministic mode stops at total combinations"""
    print("\n" + "=" * 70)
    print("  ODOMETER CAP TEST")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    
    # Test case: 3 animals × 2 colors = 6 total combinations
    prompt = "__animals__ in __colors__"
    
    test_cases = [
        {"count": 3, "expected": 3, "desc": "Request 3, get 3"},
        {"count": 6, "expected": 6, "desc": "Request 6 (exact), get 6"},
        {"count": 10, "expected": 6, "desc": "Request 10, get 6 (capped)"},
        {"count": 100, "expected": 6, "desc": "Request 100, get 6 (capped)"},
    ]
    
    for test in test_cases:
        results = node.generate(prompt, test["count"], 0, deterministic=True)
        prompts, _, _, _, seeds = results
        actual = len(prompts)
        
        status = "✓" if actual == test["expected"] else "✗"
        print(f"\n{status} {test['desc']}")
        print(f"   Requested: {test['count']}, Got: {actual}, Expected: {test['expected']}")
        
        if actual <= 10:  # Only show prompts if reasonable number
            for i, (p, s) in enumerate(zip(prompts, seeds)):
                print(f"   [{i}] Seed: {s:10d} | {p}")


def test_single_wildcard_cap():
    """Test with single wildcard"""
    print("\n" + "=" * 70)
    print("  SINGLE WILDCARD CAP TEST")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    
    # 3 animals total
    prompt = "A __animals__"
    
    print(f"\nPrompt: {prompt}")
    print("Total combinations: 3 (cat, dog, fox)")
    
    results = node.generate(prompt, 10, 0, deterministic=True)
    prompts, _, _, _, seeds = results
    
    print(f"\nRequested: 10, Got: {len(prompts)}")
    for i, (p, s) in enumerate(zip(prompts, seeds)):
        print(f"  [{i}] Seed: {s:10d} | {p}")


def test_three_wildcards_cap():
    """Test with three wildcards"""
    print("\n" + "=" * 70)
    print("  THREE WILDCARDS CAP TEST")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    
    # 2 colors × 3 animals × 2 colors = 12 combinations
    prompt = "__colors__ __animals__ wearing __colors__"
    
    print(f"\nPrompt: {prompt}")
    print("Total combinations: 2 × 3 × 2 = 12")
    
    results = node.generate(prompt, 20, 0, deterministic=True)
    prompts, _, _, _, seeds = results
    
    print(f"\nRequested: 20, Got: {len(prompts)}")
    print("\nAll combinations:")
    for i, (p, s) in enumerate(zip(prompts, seeds)):
        print(f"  [{i:2d}] Seed: {s:10d} | {p}")


def test_no_wildcards():
    """Test with no wildcards (should use requested count)"""
    print("\n" + "=" * 70)
    print("  NO WILDCARDS TEST")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    
    prompt = "Just a plain prompt"
    
    print(f"\nPrompt: {prompt}")
    print("No wildcards - should use requested count")
    
    results = node.generate(prompt, 5, 0, deterministic=True)
    prompts, _, _, _, seeds = results
    
    print(f"\nRequested: 5, Got: {len(prompts)}")
    for i, (p, s) in enumerate(zip(prompts, seeds)):
        print(f"  [{i}] Seed: {s:10d} | {p}")


def test_non_deterministic_no_cap():
    """Test that non-deterministic mode doesn't cap"""
    print("\n" + "=" * 70)
    print("  NON-DETERMINISTIC MODE (NO CAP)")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    
    prompt = "__animals__ in __colors__"
    
    print(f"\nPrompt: {prompt}")
    print("Total combinations: 6")
    print("Non-deterministic mode should NOT cap")
    
    results = node.generate(prompt, 10, 0, deterministic=False)
    prompts, _, _, _, seeds = results
    
    print(f"\nRequested: 10, Got: {len(prompts)}")
    print("(Should get 10, with possible duplicates)")
    
    for i, (p, s) in enumerate(zip(prompts, seeds)):
        print(f"  [{i}] Seed: {s:10d} | {p}")


def main():
    print("\n" + "█" * 70)
    print("  DETERMINISTIC ODOMETER CAP TEST SUITE")
    print("█" * 70)
    
    try:
        test_odometer_cap()
        test_single_wildcard_cap()
        test_three_wildcards_cap()
        test_no_wildcards()
        test_non_deterministic_no_cap()
        
        print("\n" + "=" * 70)
        print("  ALL TESTS COMPLETE")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
