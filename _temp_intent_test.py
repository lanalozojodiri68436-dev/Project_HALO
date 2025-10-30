# _temp_intent_test.py
import sys
# 确保能找到 src 目录
sys.path.insert(0, '.') # Adds the current directory to the path

try:
    from src.main_app.intent_classifier import IntentClassifier
    from src.main_app.tool_registry import load_tools
    print("--- Intent Classifier Test ---")
    load_tools("src/plugins") # Ensure tools (and keywords) are loaded
    ic = IntentClassifier()
    tests = ["现在几点了","帮我找 project management 表","打开 C:\\secret\\passwd", "你好 HALO", "读取 report.md 文件"]
    for t in tests:
        print(f"'{t}' -> {ic.classify(t)}")
except Exception as e:
    print(f"Error during intent classification test: {e}")
    import traceback
    traceback.print_exc()