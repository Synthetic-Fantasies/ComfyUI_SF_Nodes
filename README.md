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
- Or install via git:
```bash
cd /path/to/ComfyUI/custom_nodes
git clone git@github.com:Synthetic-Fantasies/ComfyUI_SF_Nodes.git
```
Symlink example (adjust the ComfyUI path):
```bash
ln -s "$(pwd)" ~/ComfyUI/custom_nodes/ComfyUI_SF_Nodes
```

### Develop locally
```bash
source .venv/bin/activate
python -c "import sf_nodes_all as m; print('Loaded nodes:', list(m.NODE_CLASS_MAPPINGS.keys()))"
```

### Included nodes
- `SFWildcardsPromptMatrixExt` (category: `SF/Text`)
  - Replaces `__token__` wildcards using ComfyUI's global wildcards directory (or `COMFYUI_WILDCARDS_DIR`, fallback `./wildcards`).
  - Uses text before `|` for replacement, captures labels after `|` as lowercase unique tags.
  - Outputs:
    - `prompts`: list of expanded prompts
    - `wildcard_lines`: list of concatenated `[filename:line]` tags per prompt
    - `tags`: comma-joined unique, lowercased labels per prompt
    - `tags_list`: list of unique, lowercased label tokens per prompt
    - `wildcards_dir`: resolved directory path used

- `SFPreviewCompare` (category: `SF/Preview`)
  - Compare A/B images with circular `index` across arrays of IMAGE.
  - UI toggles A/B/Swipe/Area at display time; ◀ ▶ buttons for `index`.
 - `SFImageGridAuto` (category: `SF/Image`)
   - Composes an image grid without resizing tiles; optional save with `filename_prefix` and `save_result` like SaveImage.
   - UI preview is embedded in the node via extension.

 
