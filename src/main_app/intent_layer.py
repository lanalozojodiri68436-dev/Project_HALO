# -*- coding: utf-8 -*-
"""
Intent Layer (A1 Specification Implementation)
==============================================
VERSION: V4.5 (Fix: Expanded Local regex for file reading)

- [FIX V4.5] Expanded local_patterns regex for 'read_file_lines'
  to catch phrasings like "给出...文件...行".
- Retains V4.2 cloud regex and V4.0.1 datetime fix.
"""
from loguru import logger
import re
from typing import Dict, Any
from datetime import datetime # [FIX V4.0.1]

class IntentLayer:
    """
    (A1) Implements the Intent Layer.
    """
    
    def __init__(self):
        logger.info("Initializing IntentLayer (A1 / V4.5)...") # V4.5
        
        # (A4, 3.3 / V4.2) Cloud Intents
        self.cloud_patterns = {
            "get_weather": re.compile(r'天气|温度|预报'),
            "web_search": re.compile(r'新闻|头条|翻译|译成|搜索|查询|查一下|分析|是什么|怎么样'),
        }
        
        # (V4.5) Local Intents
        self.local_patterns = {
            "search_files": re.compile(r'找文件|搜索文件|本地文件'),
            # [FIX V4.5] Added pattern for "给出...文件...行"
            "read_file_lines": re.compile(r'读取|打开文件|读文件|查看文件|给出.*文件.*行'), 
        }

        # (V4.2) Direct Intents
        self.direct_patterns = {
            "get_time": re.compile(r'(现在|当前).*(几点|时间)|(几点|时间).*现在|what time is it')
        }

    def _classify(self, text_lower: str) -> tuple[str, float]:
        """Internal classification logic based on keyword matching."""
        
        # 1. Check Direct
        for intent, pattern in self.direct_patterns.items():
            if pattern.search(text_lower):
                return intent, 0.98

        # 2. Check Local (Specific file operations first)
        # [MODIFIED V4.5] Check this BEFORE cloud now due to improved regex
        for intent, pattern in self.local_patterns.items():
            if pattern.search(text_lower):
                # Ensure general "搜索" doesn't accidentally match "搜索文件" here
                # if intent == "search_files" and not ("文件" in text_lower or "file" in text_lower):
                #     continue 
                return intent, 0.90 # High confidence for specific local actions

        # 3. Check Cloud (General web queries)
        for intent, pattern in self.cloud_patterns.items():
            if pattern.search(text_lower):
                 # Avoid conflict if 'search_files' was already matched
                 # if intent == "web_search" and "文件" in text_lower:
                 #    continue # Already handled by local_patterns potentially
                 return intent, 0.85

        # 4. Fallback
        return "chat", 0.5

    def analyze_intent(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        (A1/A3 Interface) Analyzes user input and returns IntentMeta.
        """
        logger.debug(f"IntentLayer: Analyzing '{user_input}'")
        text_lower = user_input.lower().strip()
        
        intent, confidence = self._classify(text_lower)
        
        # (A1) Build the Intent Object
        intent_meta = {
            "intent": intent,
            "confidence": confidence,
            "complexity": "medium" if intent not in ["get_time", "chat"] else "low",
            "route": None, 
            "timestamp": datetime.now().isoformat(),
            "raw_text": user_input
        }
        
        return intent_meta