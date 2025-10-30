# -*- coding: utf-8 -*-
"""
Cognitive Memory Manager for HALO (Phase 3.4.3)
Based on GPT specification for interaction logging.
"""
from loguru import logger
from datetime import datetime
from typing import List, Dict, Any, Optional

MEMORY_LOG_LIMIT = 50 # Store last 50 interactions

class MemoryManager:
    """
    管理短期与长期记忆，供认知层推理与状态层共享。
    (V3.4.3 Implementation)
    """
    def __init__(self):
        """Initializes the memory log."""
        logger.info("Initializing MemoryManager (V3.4.3)...")
        self.memory_log: List[Dict[str, Any]] = []
        logger.info("MemoryManager initialized.")

    def store_interaction(self, user_input: str, reasoning_result: Dict[str, Any]):
        """
        Stores a record of the user input and the reasoning result.
        (GPT Step 3.4.3)
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "result": reasoning_result
        }
        logger.debug(f"Storing interaction to memory log: {record}")
        self.memory_log.append(record)
        
        if len(self.memory_log) > MEMORY_LOG_LIMIT:
            self.memory_log.pop(0) # Remove the oldest entry

    def recall_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        返回最近 n 条短期记忆（交互记录）。
        (GPT Step 3.4.3)
        """
        limit = max(0, limit) # Ensure limit is non-negative
        return self.memory_log[-limit:]

    # --- (V3.1 Methods - Deprecated) ---
    
    def store_trace(self, content: Any):
        """(V3.1 Method) Deprecated in favor of store_interaction."""
        logger.warning("store_trace() is deprecated. Use store_interaction().")
        # Adapt to new structure
        trace_record = {
            "timestamp": datetime.now().isoformat(),
            "input": "trace", # Mark as trace
            "result": content
        }
        self.memory_log.append(trace_record)
        if len(self.memory_log) > MEMORY_LOG_LIMIT:
            self.memory_log.pop(0)

    def recall_fact(self, key: str) -> Optional[Any]:
        """(V3.1 Method) Recalls a fact by key (placeholder)."""
        logger.warning("recall_fact() is not fully implemented in V3.4.3 structure.")
        for item in reversed(self.memory_log):
             if item.get("input") == "fact" and item.get("result", {}).get("key") == key:
                  return item["result"].get("value")
        return None