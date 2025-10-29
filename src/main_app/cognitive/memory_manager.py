# -*- coding: utf-8 -*-
"""
Cognitive Memory Manager for HALO (Phase 3)
"""
from loguru import logger
from typing import List, Dict, Any, Tuple, Optional

# Define constants for memory limits (can be moved to config later)
SHORT_TERM_MEMORY_LIMIT = 20

class MemoryManager:
    """
    管理短期与长期记忆，供认知层推理与状态层共享。
    (当前为基础实现)
    """
    def __init__(self):
        """Initializes short-term and long-term memory structures."""
        logger.info("Initializing MemoryManager...")
        # Short-term memory: Stores recent interaction traces or key info as tuples/dicts
        self.short_term: List[Any] = [] 
        # Long-term memory: Placeholder for structured or semantic memory
        self.long_term: Dict[str, Any] = {} 
        logger.info("MemoryManager initialized.")

    def store_trace(self, content: Any):
        """用于记录每次推理或交互的痕迹到短期记忆。"""
        logger.debug(f"Storing trace to short-term memory: {content}")
        self.short_term.append(content)
        # Apply memory limit by removing the oldest entry if over limit
        if len(self.short_term) > SHORT_TERM_MEMORY_LIMIT:
            removed_item = self.short_term.pop(0)
            logger.debug(f"Short-term memory limit reached. Removed oldest item: {removed_item}")

    # Example method for storing structured data (can be expanded)
    def store_fact(self, key: str, value: Any, long_term: bool = False):
        """Stores a key-value fact into memory."""
        if long_term:
            logger.debug(f"Storing fact to long-term memory: {key} = {value}")
            self.long_term[key] = value
        else:
            # Store as tuple to distinguish from traces? Or use a structured dict?
            fact_entry = {"type": "fact", "key": key, "value": value}
            logger.debug(f"Storing fact to short-term memory: {fact_entry}")
            self.short_term.append(fact_entry)
            if len(self.short_term) > SHORT_TERM_MEMORY_LIMIT:
                 self.short_term.pop(0)

    # Example method for recalling structured data
    def recall_fact(self, key: str) -> Optional[Any]:
        """Recalls a fact by key, checking short-term then long-term."""
        # Check short-term memory first (most recent) - iterate backwards
        for item in reversed(self.short_term):
             if isinstance(item, dict) and item.get("type") == "fact" and item.get("key") == key:
                  logger.debug(f"Recalled fact '{key}' from short-term memory.")
                  return item.get("value")
        # Check long-term memory if not found in short-term
        value = self.long_term.get(key)
        if value is not None:
             logger.debug(f"Recalled fact '{key}' from long-term memory.")
        return value

    def recall_recent(self, n: int = 5) -> List[Any]:
        """返回最近 n 条短期记忆条目（包括 traces 和 facts）。"""
        n = max(0, n) # Ensure n is not negative
        return self.short_term[-n:]

    def get_short_term_memory(self) -> List[Any]:
         """Returns the entire short-term memory."""
         return list(self.short_term) # Return a copy

    def clear_short_term(self):
         """Clears the short-term memory."""
         logger.info("Clearing short-term memory.")
         self.short_term = []