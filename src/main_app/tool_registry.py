# -*- coding: utf-8 -*-
"""
Tool Registry for HALO (Phase 3 - Cognitive Layer - list_tools Fix)
===================================================================
Scans plugin directories, loads tool specifications and execution functions,
and provides access to the registered tools. Includes list_tools function.
"""
import importlib.util
from pathlib import Path
from loguru import logger
from typing import Dict, Any, Callable, List, Optional

# Module-level dictionary to store loaded tools
_tools: Dict[str, Dict[str, Any]] = {}

def _import_module_from_path(path: Path) -> Optional[Any]:
    """Dynamically imports a Python module from a given file path."""
    module_name = path.stem
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            logger.warning(f"Could not create spec for '{path.name}'. Skipping.")
            return None
            
        module = importlib.util.module_from_spec(spec)
        # Add module to sys.modules BEFORE execution to handle potential circular imports within plugins
        # sys.modules[module_name] = module # This might be risky if module names clash
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to import module from '{path.name}': {e}")
        # Optionally re-raise or log traceback for debugging
        # import traceback
        # logger.error(traceback.format_exc())
        return None

def load_tools(plugin_dir: str = "src/plugins") -> Dict[str, Dict[str, Any]]:
    """
    Scans a directory for Python files, dynamically imports them, and registers
    tools that expose 'tool_spec' and 'execute' attributes.

    Args:
        plugin_dir (str): The path to the directory containing plugin files.

    Returns:
        Dict[str, Dict[str, Any]]: The dictionary of registered tools.
    """
    global _tools
    _tools.clear() # Clear previous tools on reload
    
    plugin_path = Path(plugin_dir)
    
    if not plugin_path.is_dir():
        logger.warning(f"Plugin directory not found: '{plugin_dir}'. No tools loaded.")
        return _tools

    logger.info(f"Scanning for tools in directory: '{plugin_dir}'")
    
    for file_path in plugin_path.glob("*.py"):
        # Skip __init__.py files or files starting with underscore
        if file_path.name.startswith("_"):
            continue

        module = _import_module_from_path(file_path)
        if module:
            # Check if the required attributes exist
            if hasattr(module, "tool_spec") and callable(getattr(module, "execute", None)):
                tool_name = module.tool_spec.get("name")
                if not tool_name:
                    logger.warning(f"Plugin '{file_path.stem}' has 'tool_spec' but is missing 'name'. Skipping.")
                    continue
                    
                if tool_name in _tools:
                     logger.warning(f"Duplicate tool name '{tool_name}' found in '{file_path.name}'. Overwriting previous registration.")

                _tools[tool_name] = {
                    "spec": module.tool_spec,
                    "func": module.execute,
                    "module": module # Store module reference if needed later
                }
                logger.info(f"Successfully registered tool: '{tool_name}' from '{file_path.name}'.")
            else:
                logger.debug(f"File '{file_path.name}' is not a valid tool module (missing 'tool_spec' or 'execute' function).")

    logger.info(f"Tool loading complete. Total tools registered: {len(_tools)}")
    return _tools

def get_tool(name: str) -> Optional[Dict[str, Any]]:
    """Retrieves a registered tool by its name."""
    return _tools.get(name)

# --- [ADDED] list_tools function ---
def list_tools() -> List[str]:
    """Returns a list of names of all registered tools."""
    return list(_tools.keys())
# ------------------------------------

def get_all_tools() -> Dict[str, Dict[str, Any]]:
     """Returns the entire dictionary of registered tools."""
     # Return a copy to prevent external modification
     return dict(_tools)

# Optional: Example usage block (won't run when imported)
if __name__ == '__main__':
    print("Running tool_registry.py directly for testing...")
    # Adjust path assuming run from project root, pointing to default plugins dir
    project_root = Path(__file__).parent.parent # Navigate up from src/main_app to src, then to root
    plugin_directory = project_root / "src" / "plugins"
    print(f"Attempting to load tools from: {plugin_directory}")
    
    loaded = load_tools(str(plugin_directory)) # Pass the correct path
    
    print("\nLoaded Tools Dictionary:")
    import pprint
    pprint.pprint(loaded)
    
    print("\nList of Tool Names:")
    print(list_tools())
    
    print("\nGetting 'search_files' tool:")
    search_tool = get_tool("search_files")
    if search_tool:
        print(f"  Spec: {search_tool['spec']}")
        print(f"  Func: {search_tool['func']}")
    else:
        print("  'search_files' tool not found.")