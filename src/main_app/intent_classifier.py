# -*- coding: utf-8 -*-
"""
Intent Classifier for HALO (Phase 3.9 - V3.9 Logic)
=====================================================
Implement's lllan's V3.9 directive:
1. Minimalist Rule Layer: Only match high-confidence, no-param tools (get_time).
2. Full Fallback: All other inputs (search, read) fall back to the cognitive layer.
3. Parameter Neutral: No parameter extraction is attempted.

This fixes the V3.7/V3.8 bug where the classifier incorrectly intercepted
complex commands meant for the LLM Tool Use path.
"""
import re
from loguru import logger
from typing import Dict, Any, Optional, List

from . import tool_registry 
from .cognitive.reasoning_engine import ReasoningEngine
from .cognitive.memory_manager import MemoryManager

class IntentClassifier:
    """
    Classifies user intent using a multi-stage process (V3.9):
    1. Direct Regex (High Confidence, e.g., get_time)
    2. Cognitive Reasoning (Fallback for everything else)
    """

    def __init__(self, tool_registry_instance: Optional[Any] = None):
        """
        Initializes the classifier, cognitive modules, and builds the keyword map.
        (Keyword map is no longer used for matching, but kept for cognitive layer context)
        """
        logger.info("Initializing IntentClassifier (V3.9 Logic)...")
        
        self.tool_registry = tool_registry_instance or tool_registry
        
        self.memory = MemoryManager()
        self.reasoner = ReasoningEngine(self.memory) 
        
        # V3.9: Keyword map is no longer used for direct matching,
        # but the reasoning engine might still benefit from knowing the keywords.
        self.keyword_map: Dict[str, List[str]] = {}
        self._build_keyword_map() 
        
        logger.info(f"IntentClassifier (V3.9) initialized.")

    def _build_keyword_map(self):
        """Builds a map from tool names to their associated keywords."""
        self.keyword_map = {}
        all_tools = self.tool_registry.get_all_tools()
        for tool_name, tool_data in all_tools.items():
            spec = tool_data.get("spec", {})
            keywords = spec.get("keywords", []) 
            if keywords and isinstance(keywords, list):
                self.keyword_map[tool_name] = [kw.lower() for kw in keywords if isinstance(kw, str)]
        logger.debug(f"Built keyword map (for cognitive context): {self.keyword_map}")

    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Classifies the intent of the input text using V3.9 logic.
        """
        text_lower = user_input.lower().strip()
        logger.debug(f"Classifying input (V3.9 Path): '{user_input}'")

        # 1️⃣ 尝试直接匹配 (Regex for Time - 极简规则层)
        if re.search(r'(现在|当前).*(几点|时间)|(几点|时间).*现在|what time is it', text_lower):
            logger.debug(f"Intent classified as 'get_time' via regex.")
            result = {"intent": "execute", "tool": "get_time", "confidence": 0.98, "extracted": {}}
            self.memory.store_interaction(user_input, result)
            return result

        # 2️⃣ [REMOVED] V3.9: 移除了有缺陷的“快速关键词匹配” (V3.7)
        # 这一层是导致 search_files 被错误拦截和参数提取失败的根源。
        # logger.debug("V3.9: Skipping defective keyword matching.")

        # 3️⃣ 进入认知层：推理意图 (V3.9 全面回退机制)
        # 所有未被 1️⃣ 匹配的请求 (如 search, read, chat) 都会回退到这里。
        # CoreDispatcher (V3.6) 将捕获此结果 (e.g., 'chat')
        # 并将其路由到 _process_with_llm_tool_use 路径。
        logger.debug("No direct match. Calling ReasoningEngine (Full Fallback)...")
        reasoning_result = self.reasoner.infer_intent(text_lower) 
        
        self.memory.store_interaction(user_input, reasoning_result)
        logger.debug(f"Reasoning complete. Result: {reasoning_result}")

        return reasoning_result

    # 4️⃣ [REMOVED] V3.9: 移除了有缺陷的参数提取 (V3.7)
    # def _extract_params_v3_7(...)
    #    ...

    def reload_keywords(self):
         """Reloads keywords from the tool registry."""
         logger.info("Reloading keywords for IntentClassifier...")
         self._build_keyword_map()

# --- Test Code ---
if __name__ == '__main__':
    logger.remove()
    logger.add(lambda msg: print(msg, end=''), level="DEBUG", format="{level.icon} {message}")
    
    print("--- Intent Classifier Test (V3.9 Logic Test) ---")
    try:
        import sys
        from pathlib import Path
        src_path = str(Path(__file__).resolve().parents[2])
        if src_path not in sys.path:
             sys.path.insert(0, src_path)
        
        from src.main_app import tool_registry
        
        tool_registry.load_tools()
        classifier = IntentClassifier(tool_registry) 
        
        # (使用了 V3.7/V3.8 失败的用例)
        test_phrases = [
            "现在几点",                 # 应被 1️⃣ 匹配
            "你好 HALO",                # 应回退到 3️⃣
            "帮我找一下 requirements.txt 文件" # [关键测试] 应回退到 3️⃣
        ]
        
        print("\n--- Running Classifications ---")
        for phrase in test_phrases:
            result = classifier.classify(phrase)
            print(f"'{phrase}' -> {result}")
            
            if "requirements.txt" in phrase:
                if result.get("tool") == "search_files":
                     print("❌ FAILED: 'search_files' was incorrectly matched.")
                else:
                     print("✅ SUCCESS: 'search_files' was NOT matched, fallback occurred.")
            
            if "几点" in phrase:
                if result.get("tool") == "get_time":
                     print("✅ SUCCESS: 'get_time' was correctly matched.")
                else:
                     print("❌ FAILED: 'get_time' was not matched.")


    except Exception as e:
        print(f"\nError during intent classification test: {e}")
        import traceback
        traceback.print_exc()