import os
import re
import random
from typing import Dict, List, Tuple


_WILDCARD_PATTERN = re.compile(r"__([A-Za-z0-9_./\\-]+)__")


def _resolve_wildcards_dir() -> str:
    # 1) Environment override
    env_dir = os.environ.get("COMFYUI_WILDCARDS_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir

    # 2) Try ComfyUI's folder_paths if available
    try:
        import folder_paths  # type: ignore

        # Some builds may expose a helper; prefer explicit functions if present
        for attr in ("get_wildcards_dir", "get_wildcard_dir"):
            if hasattr(folder_paths, attr):
                d = getattr(folder_paths, attr)()
                if isinstance(d, str) and os.path.isdir(d):
                    return d

        # Otherwise derive ComfyUI root from module path and use 'wildcards'
        import pathlib
        root = pathlib.Path(folder_paths.__file__).resolve().parents[1]
        candidate = root / "wildcards"
        if candidate.is_dir():
            return str(candidate)
    except Exception:
        pass

    # 3) Fallback to local ./wildcards
    local = os.path.abspath("wildcards")
    return local


def _read_wildcard_file(base_dir: str, token: str) -> Tuple[str, List[Tuple[str, int]]]:
    # Resolve path: if token has extension, use as-is; otherwise append .txt
    # Allow subdirectories inside base_dir
    filename = token if os.path.splitext(token)[1] else f"{token}.txt"
    path = os.path.join(base_dir, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Wildcard file not found: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = f.readlines()
    # Keep original 1-based line numbers for non-empty, non-comment lines
    lines: List[Tuple[str, int]] = []
    for idx, line in enumerate(raw_lines, start=1):
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        lines.append((text, idx))
    if not lines:
        raise ValueError(f"Wildcard file has no usable lines: {path}")
    return os.path.basename(filename), lines


class SFWildcardsPromptMatrixExt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "A photo of __animals__ in __colors__"}),
                "count": ("INT", {"default": 4, "min": 1, "max": 1024}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1}),
                "deterministic": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompts", "wildcard_lines", "tags", "tags_list", "wildcards_dir")
    OUTPUT_IS_LIST = (True, True, True, True, False)
    FUNCTION = "generate"
    CATEGORY = "SF/Text"

    def generate(self, prompt: str, count: int, seed: int, deterministic: bool):
        wildcards_dir = _resolve_wildcards_dir()
        # Find all wildcard occurrences in order of appearance
        tokens_in_order = list(_WILDCARD_PATTERN.finditer(prompt))
        token_names = [m.group(1) for m in tokens_in_order]

        # Preload files per unique token
        unique_tokens = list(dict.fromkeys(token_names))  # preserve order
        file_to_choices: Dict[str, Tuple[str, List[str]]] = {}
        for tok in unique_tokens:
            filename, choices = _read_wildcard_file(wildcards_dir, tok)
            file_to_choices[tok] = (filename, choices)

        rng = random.Random(seed if deterministic else None)

        out_prompts: List[str] = []
        out_meta: List[str] = []
        out_tags: List[str] = []
        out_tags_list: List[List[str]] = []

        for i in range(count):
            current_prompt = prompt
            tags: List[str] = []

            # For deterministic behavior, reseed per iteration for reproducibility
            if deterministic:
                # Seed must be a single supported type; derive an int from seed and iteration
                rng.seed((seed * 1_000_003 + i) & 0xFFFFFFFF)

            # Replace occurrences from left-to-right; choose a line index each time
            replacements: List[Tuple[Tuple[int, int], str, str, str]] = []
            for m in tokens_in_order:
                tok = m.group(1)
                filename, choices = file_to_choices[tok]
                idx = rng.randrange(len(choices)) if len(choices) > 1 else 0
                value, lineno = choices[idx]
                # Split once on '|': use first segment for replacement; keep second as label (if present)
                head, sep, tail = value.partition("|")
                replacement_value = (head.strip() or value.strip())
                label_text = tail.strip() if sep else ""
                tag = f"[{filename}:{lineno}]"
                replacements.append(((m.start(), m.end()), replacement_value, tag, label_text))

            # Apply replacements from end to start to keep indices valid
            for (start, end), value, tag, label_text in reversed(replacements):
                current_prompt = current_prompt[:start] + value + current_prompt[end:]

            # Build ordered tags and unique labels in original occurrence order
            tags = [tag for (_, _), _, tag, _ in replacements]
            seen = set()
            labels_ordered: List[str] = []
            for (_, _), _, _, label_text in replacements:
                if not label_text:
                    continue
                for tok in (t.strip() for t in label_text.split(",")):
                    if not tok:
                        continue
                    tok_norm = tok.lower()
                    if tok_norm not in seen:
                        seen.add(tok_norm)
                        labels_ordered.append(tok_norm)

            out_prompts.append(current_prompt)
            out_meta.append("".join(tags))
            out_tags.append(",".join(labels_ordered))
            out_tags_list.append(labels_ordered)

        return (out_prompts, out_meta, out_tags, out_tags_list, wildcards_dir)


NODE_CLASS_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": SFWildcardsPromptMatrixExt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFWildcardsPromptMatrixExt": "SF Wildcards Prompt Matrix+",
}


