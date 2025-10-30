# -*- coding: utf-8 -*-
"""
Routing Policy (A4-Revised Specification Implementation)
========================================================
VERSION: V4.2 (Fix: Corrected 'chat' routing)

- [FIX V4.2] Moves 'chat' and 'web_search' to 'cloud_intents'.
- 'local_intents' is now ONLY for explicit local file tools.
- This correctly implements "Intelligent Scheduling" (A4).
"""
from loguru import logger
from typing import Dict, Any

class RoutingPolicy:
    """
    (A4 / V4.2) Implements the Routing Policy Layer.
    Decides the execution path based on the classified intent.
    """

    def __init__(self):
        logger.info("Initializing RoutingPolicy (A4 / V4.2)...")
        
        # (A4, 3.3 / V4.2) Hardcoded routing rules
        
        # [FIX V4.2] 'chat' and 'web_search' MUST go to the
        # powerful cloud model ('gemini-pro-latest').
        self.cloud_intents = {
            "get_weather",
            "get_news",
            "translate_text",
            "web_search", # For '分析', '是什么' etc.
            "chat"        # General chat
        }
        
        # [FIX V4.2] 'local_intents' is now ONLY for
        # specific local tool actions.
        self.local_intents = {
            "search_files",
            "read_file_lines",
        }

        self.direct_intents = {
            "get_time"
        }

    def resolve(self, intent_meta: Dict[str, Any]) -> str:
        """
        (A4, 6) Resolves the route based on the A1 intent.
        """
        intent = intent_meta.get("intent", "chat") # Default to 'chat'
        
        if intent in self.cloud_intents:
            logger.debug(f"RoutingPolicy: Intent '{intent}' resolved to CLOUD.")
            return "cloud"
        
        if intent in self.local_intents:
            logger.debug(f"RoutingPolicy: Intent '{intent}' resolved to LOCAL.")
            return "local"

        if intent in self.direct_intents:
            logger.debug(f"RoutingPolicy: Intent '{intent}' resolved to DIRECT.")
            return "direct"
        
        # (A4, 3.2 / V4.2) Fallback for 'unknown' (which defaults to 'chat')
        logger.warning(f"RoutingPolicy: Intent '{intent}' is unknown. Defaulting to CLOUD (chat).")
        return "cloud" # [FIX V4.2] Fallback to cloud