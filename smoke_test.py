import importlib

mods = [
    "sf_nodes_all",
]

for m in mods:
    mod = importlib.import_module(m)
    print(m, "OK", sorted(mod.NODE_CLASS_MAPPINGS.keys()))
