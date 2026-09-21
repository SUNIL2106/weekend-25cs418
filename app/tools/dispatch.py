from .print_tools import TOOL_REGISTRY

def dispatch(name, args):
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")
    return TOOL_REGISTRY[name]["fn"](**args)

def describe_tools():
    return {
        name: {k:v for k,v in meta.items() if k != "fn"}
        for name,meta in TOOL_REGISTRY.items()
    }
