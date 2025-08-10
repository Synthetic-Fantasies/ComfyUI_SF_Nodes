class SFMathOps:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "a": ("FLOAT", {"default": 1.0}),
                "b": ("FLOAT", {"default": 2.0}),
                "op": (["add", "sub", "mul", "div"], {"default": "add"}),
            }
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("result",)
    FUNCTION = "compute"
    CATEGORY = "SF/Math"

    def compute(self, a: float, b: float, op: str):
        if op == "add":
            res = a + b
        elif op == "sub":
            res = a - b
        elif op == "mul":
            res = a * b
        else:
            res = a / b if b != 0 else float("inf")
        return (float(res),)


NODE_CLASS_MAPPINGS = {
    "SFMathOps": SFMathOps,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SFMathOps": "SF Math Ops",
}
