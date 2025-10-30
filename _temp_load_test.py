# _temp_load_test.py
import sys
# 确保能找到 src 目录
sys.path.insert(0, '.') # Adds the current directory to the path

try:
    from src.main_app.tool_registry import load_tools, list_tools
    print("--- Tool Registry Load Test ---")
    # Ensure we load from the correct directory relative to execution
    loaded_keys = list(load_tools("src/plugins").keys()) # Specify plugin dir relative to root
    print("loaded:", loaded_keys)
except Exception as e:
    print(f"Error during tool loading: {e}")
    import traceback
    traceback.print_exc()