import importlib
import os
import sys

# Ensure package parent directory is importable so we can import by package name
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
PARENT_DIR = os.path.dirname(REPO_ROOT)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)


def main():
    mods = [
        "ComfyUI_SF_Nodes",
    ]
    for m in mods:
        mod = importlib.import_module(m)
        print(m, "OK", sorted(mod.NODE_CLASS_MAPPINGS.keys()))


if __name__ == "__main__":
    # Ensure the parent of the repo root is importable
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)
    main()


