"""Node definitions for ComfyUI-EBU-Workflow package."""

class ExampleNode:
    """A simple example node implementation."""
    def execute(self, *args, **kwargs):
        return "Example output"

NODE_CLASS_MAPPINGS = {
    "ExampleNode": ExampleNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExampleNode": "Example Node",
}
