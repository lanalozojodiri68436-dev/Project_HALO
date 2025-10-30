# -*- coding: utf-8 -*-
"""
Cognitive Reasoning Engine for HALO (Phase 3.4.2 - V2 - Logic Fixed)
Based on GPT specification for rule-based fuzzy intent inference.
[FIXED] Logic in infer_intent to match V3.5 smoke test expectations.
"""
from loguru import logger
from typing import Dict, Any
# 导入 MemoryManager 以便进行类型提示
from .memory_manager import MemoryManager 

class ReasoningEngine:
    """
    Phase3 Cognitive Core - Handles reasoning, inference, and goal planning.
    (V3.4.2 Implementation with Corrected Init and Logic)
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initializes the ReasoningEngine with a MemoryManager instance.
        """
        logger.info("Initializing ReasoningEngine (V3.4.2 Corrected)...")
        self.memory = memory_manager # Store the passed memory manager
        logger.info("ReasoningEngine initialized.")

    def infer_intent(self, text: str) -> Dict[str, Any]:
        """
        尝试基于模糊语义或上下文判断意图。
        (GPT Step 3.4.2 - Logic Fixed)
        
        Args:
            text (str): The user's input text (expected to be lowercased by classifier).
        
        Returns:
            Dict[str, Any]: A dictionary representing the inferred intent.
        """
        logger.debug(f"ReasoningEngine inferring from: '{text}'")
        
        # [FIXED] 1. File Read Intent (Added "读取", "打开")
        if ("文件" in text and ("读" in text or "看" in text or "查看" in text or "读取" in text)) or "打开" in text:
            logger.debug("ReasoningEngine: Inferred 'read_file_lines'")
            return {"intent": "execute", "tool": "read_file_lines", "confidence": 0.7}
            
        # [FIXED] 2. File Search Intent (Ensured "找" is checked)
        if "找" in text or "搜索" in text:
            logger.debug("ReasoningEngine: Inferred 'search_files'")
            return {"intent": "execute", "tool": "search_files", "confidence": 0.65}
            
        # 3. Time Intent (Fallback)
        if "时间" in text or "几点" in text:
            logger.debug("ReasoningEngine: Inferred 'get_time'")
            return {"intent": "execute", "tool": "get_time", "confidence": 0.9} 

        # 4. Fallback to Chat
        logger.debug("ReasoningEngine: No specific intent inferred. Falling back to chat.")
        return {"intent": "chat", "tool": None, "confidence": 0.2}

    def process(self, input_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        (V3.1 Deprecated Method - Kept for reference)
        """
        logger.warning("ReasoningEngine.process() is deprecated. Use infer_intent().")
        user_input = input_context.get("user_input", "")
        
        reasoning_trace = f"推理输入：{input_context}"
        try:
            self.memory.store_trace(reasoning_trace) 
        except Exception as e:
             logger.error(f"Failed to store reasoning trace: {e}")
             
        return self.infer_intent(user_input)