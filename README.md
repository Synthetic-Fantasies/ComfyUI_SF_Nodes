## ComfyUI SF Nodes

Minimal scaffold for custom ComfyUI nodes.

### Setup
- Ensure Python 3.10 is active (pyenv local set in this folder).
- Create a virtualenv if needed:
```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

### Install into ComfyUI
- Copy or symlink this folder into your ComfyUI `custom_nodes` directory and restart ComfyUI.

Example symlink (adjust the ComfyUI path):
```bash
ln -s "$(pwd)" ~/ComfyUI/custom_nodes/ComfyUI_SF_Nodes
```

### Develop locally
```bash
source .venv/bin/activate
python -c "import sf_hello_nodes as m; print('Loaded nodes:', list(m.NODE_CLASS_MAPPINGS.keys()))"
```

### Included nodes
- `SFHello` (category: `SF/Utility`): returns a greeting string.
