import os
import re
import random
import pathlib
import folder_paths
from typing import Dict, List, Tuple


_WILDCARD_PATTERN = re.compile(r"__([A-Za-z0-9_./\\-]+)__")


def _resolve_wildcards_dir() -> str:
    # 1) Environment override
    env_dir = os.environ.get("COMFYUI_WILDCARDS_DIR")
    if env_dir and os.path.isdir(env_dir):
        return env_dir
    # 2) Try ComfyUI's folder_paths if available
    try:
        # Some builds may expose a helper; prefer explicit functions if present
        for attr in ("get_wildcards_dir", "get_wildcard_dir"):
            if hasattr(folder_paths, attr):
                d = getattr(folder_paths, attr)()
                if isinstance(d, str) and os.path.isdir(d):
                    return d

        # Otherwise derive ComfyUI root from module path and use 'wildcards'

        root = pathlib.Path(folder_paths.__file__).resolve().parents[1]
        candidate = root / "models" / "wildcards"
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


class SFWildcardsPromptMatrix:
    # Class variable to track odometer position per node instance
    _odometer_positions = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "default": "A photo of __animals__ in __colors__",
                    "multiline": True
                }),
                "count": ("INT", {"default": 4, "min": 1, "max": 2048}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1}),
                "sequential": ("BOOLEAN", {"default": True}),
                "offset": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("prompts", "wildcard_lines", "tags", "tags_list", "seeds")
    OUTPUT_IS_LIST = (True, True, True, True, True)
    FUNCTION = "generate"
    CATEGORY = "SF/Text"

    def generate(self, prompt: str, count: int, seed: int, sequential: bool, offset: int = 0):
        wildcards_dir = _resolve_wildcards_dir()
        # Find all wildcard occurrences in order of appearance
        matches_in_order = list(_WILDCARD_PATTERN.finditer(prompt))
        token_names = [match.group(1) for match in matches_in_order]

        # Preload files per unique token
        unique_tokens = list(dict.fromkeys(token_names))  # preserve order
        file_to_choices: Dict[str, Tuple[str, List[str]]] = {}
        for tok in unique_tokens:
            filename, choices = _read_wildcard_file(wildcards_dir, tok)
            file_to_choices[tok] = (filename, choices)

        # Create a unique key for this node instance based on prompt content
        node_key = hash(prompt + str(seed))
        
        # Get or initialize odometer position for this node
        if node_key not in self._odometer_positions:
            self._odometer_positions[node_key] = offset
        
        current_odometer_pos = self._odometer_positions[node_key]
        
        rng = random.Random(seed if not sequential else None)

        out_prompts: List[str] = []
        out_meta: List[str] = []
        out_tags: List[str] = []
        out_tags_list: List[List[str]] = []
        out_seeds: List[int] = []

        # In sequential mode, calculate total combinations and cap iterations
        if sequential and matches_in_order:
            # Calculate total combinations (product of all wildcard sizes)
            sizes = [len(file_to_choices[token_names[idx]][1]) for idx in range(len(matches_in_order))]
            total_combinations = 1
            for size in sizes:
                total_combinations *= size
            # Cap count to total combinations
            actual_count = min(count, total_combinations)
        else:
            actual_count = count

        for i in range(actual_count):
            current_prompt = prompt
            tags: List[str] = []

            if sequential:
                # Deterministic mode: systematic iteration, but output random seeds
                iteration_seed = random.randint(0, 2**31 - 1)
            else:
                # Non-deterministic mode: random selection with random seed
                iteration_seed = random.randint(0, 2**31 - 1)
                rng.seed(iteration_seed)

            # Replace occurrences from left-to-right
            replacements: List[Tuple[Tuple[int, int], str, str, str]] = []

            if sequential:
                # Cartesian product iteration: rightmost wildcard increments fastest
                # Like an odometer: [0,0,0] -> [0,0,1] -> [0,0,2] -> [0,1,0] -> [0,1,1] ...
                # Calculate indices for each wildcard position using current odometer position
                iteration_offset = current_odometer_pos + i
                wildcard_indices: List[int] = []

                # Get the size of each wildcard's choices (in order of appearance)
                sizes = [len(file_to_choices[token_names[idx]][1]) for idx in range(len(matches_in_order))]

                # Calculate index for each wildcard using base conversion logic
                temp_offset = iteration_offset
                for size in reversed(sizes):
                    wildcard_indices.insert(0, temp_offset % size)
                    temp_offset //= size

            for wildcard_idx, matches in enumerate(matches_in_order):
                tok = matches.group(1)
                filename, choices = file_to_choices[tok]

                if sequential:
                    # Use pre-calculated index from cartesian product
                    idx = wildcard_indices[wildcard_idx]
                else:
                    # Random selection for non-sequential mode
                    idx = rng.randrange(len(choices)) if len(choices) > 1 else 0

                value, lineno = choices[idx]
                # Split once on '|': use first segment for replacement; keep second as label (if present)
                head, sep, tail = value.partition("|")
                replacement_value = head.strip() or value.strip()
                label_text = tail.strip() if sep else ""
                tag = f"[{filename}:{lineno}]"
                replacements.append(((matches.start(), matches.end()), replacement_value, tag, label_text))

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
            out_seeds.append(iteration_seed)

        # Update odometer position for next run
        if sequential and matches_in_order:
            new_position = current_odometer_pos + actual_count
            # Reset to 0 if we've exceeded total combinations
            if new_position >= total_combinations:
                self._odometer_positions[node_key] = 0
            else:
                self._odometer_positions[node_key] = new_position

        return (out_prompts, out_meta, out_tags, out_tags_list, out_seeds)
