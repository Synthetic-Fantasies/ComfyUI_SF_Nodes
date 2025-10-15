"""
Visualize the deterministic cartesian product sweep behavior.
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


def visualize_cartesian_sweep():
    """Visualize how deterministic mode sweeps through all combinations"""
    print("\n" + "=" * 70)
    print("  DETERMINISTIC CARTESIAN PRODUCT SWEEP VISUALIZATION")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    
    # Test with different prompts to show the pattern
    test_cases = [
        {
            "prompt": "__animals__ in __colors__",
            "count": 6,
            "seed": 0,
            "description": "2 wildcards (3 animals × 2 colors = 6 combinations)"
        },
        {
            "prompt": "__animals__",
            "count": 5,
            "seed": 0,
            "description": "1 wildcard (3 animals, cycling)"
        },
        {
            "prompt": "__colors__ __animals__ wearing __colors__",
            "count": 12,
            "seed": 0,
            "description": "3 wildcards (2 × 3 × 2 = 12 combinations)"
        }
    ]
    
    for test_idx, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {test_idx}: {test['description']}")
        print(f"Prompt: {test['prompt']}")
        print(f"{'─' * 70}")
        
        results = node.generate(
            test['prompt'],
            test['count'],
            test['seed'],
            deterministic=True
        )
        
        prompts, wildcard_lines, _, _, seeds = results
        
        # Display in table format
        print(f"\n{'Iter':<6} {'Prompt':<45} {'Wildcards':<25}")
        print("─" * 70)
        
        for i, (prompt, wl, seed) in enumerate(zip(prompts, wildcard_lines, seeds)):
            # Truncate long prompts
            prompt_display = prompt if len(prompt) <= 43 else prompt[:40] + "..."
            print(f"{i:<6} {prompt_display:<45} {wl:<25}")
    
    print("\n" + "=" * 70)


def compare_seed_offsets():
    """Show how different seed values offset the iteration"""
    print("\n" + "=" * 70)
    print("  SEED OFFSET COMPARISON")
    print("=" * 70)
    print("\nSame prompt with different seeds shows offset in iteration:\n")
    
    node = SFWildcardsPromptMatrix()
    prompt = "__animals__ in __colors__"
    
    seeds_to_test = [0, 1, 2, 5]
    
    for seed in seeds_to_test:
        results = node.generate(prompt, 4, seed, deterministic=True)
        prompts = results[0]
        
        print(f"Seed {seed}:")
        for i, p in enumerate(prompts):
            print(f"  [{i}] {p}")
        print()


def show_pattern_with_matrix():
    """Show the pattern as a matrix to visualize the odometer behavior"""
    print("\n" + "=" * 70)
    print("  ODOMETER PATTERN MATRIX")
    print("=" * 70)
    print("\nShowing wildcard indices [animal_idx, color_idx]:\n")
    
    node = SFWildcardsPromptMatrix()
    prompt = "__animals__ in __colors__"
    
    # Generate enough to show full cycle
    results = node.generate(prompt, 9, 0, deterministic=True)
    prompts, wildcard_lines = results[0], results[1]
    
    # Parse the wildcard line numbers to show indices
    print(f"{'Iter':<6} {'Animal Idx':<12} {'Color Idx':<12} {'Result':<30}")
    print("─" * 70)
    
    # We have 3 animals (cat, dog, fox) and 2 colors (red, green)
    # Pattern should be: [0,0], [0,1], [1,0], [1,1], [2,0], [2,1], [0,0], ...
    animals = ["cat", "dog", "fox"]
    colors = ["red", "green"]
    
    for i, (prompt, wl) in enumerate(zip(prompts, wildcard_lines)):
        # Calculate expected indices
        animal_idx = (i // 2) % 3
        color_idx = i % 2
        
        print(f"{i:<6} {animal_idx:<12} {color_idx:<12} {prompt:<30}")
    
    print("\nNotice: Color (rightmost) increments fastest, like an odometer!")
    print("        When color wraps (0→1→0), animal increments (0→1→2→0)")


def test_reproducibility():
    """Verify that deterministic mode produces identical results"""
    print("\n" + "=" * 70)
    print("  REPRODUCIBILITY TEST")
    print("=" * 70)
    
    node = SFWildcardsPromptMatrix()
    prompt = "__animals__ wearing __colors__ hat"
    
    # Run 3 times with same parameters
    runs = []
    for run_num in range(3):
        results = node.generate(prompt, 5, 42, deterministic=True)
        runs.append(results[0])
    
    # Check if all runs are identical
    all_match = all(runs[0] == run for run in runs[1:])
    
    print(f"\nRan generation 3 times with seed=42, count=5")
    print(f"\nRun 1:")
    for i, p in enumerate(runs[0]):
        print(f"  [{i}] {p}")
    
    print(f"\nRun 2:")
    for i, p in enumerate(runs[1]):
        print(f"  [{i}] {p}")
    
    print(f"\nRun 3:")
    for i, p in enumerate(runs[2]):
        print(f"  [{i}] {p}")
    
    if all_match:
        print("\n✓ All runs produced IDENTICAL results (fully deterministic)")
    else:
        print("\n✗ Runs differ (not deterministic)")


def main():
    print("\n" + "█" * 70)
    print("  DETERMINISTIC SWEEP BEHAVIOR TEST SUITE")
    print("█" * 70)
    
    try:
        visualize_cartesian_sweep()
        compare_seed_offsets()
        show_pattern_with_matrix()
        test_reproducibility()
        
        print("\n" + "=" * 70)
        print("  ALL VISUALIZATIONS COMPLETE")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
