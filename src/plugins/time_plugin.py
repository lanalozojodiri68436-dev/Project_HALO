# -*- coding: utf-8 -*-
"""
Time Plugin for HALO
====================

A simple plugin that provides the current time.
"""
from datetime import datetime
from loguru import logger

tool_spec = {
    "name": "get_time",
    # [修改] 更清晰地说明功能和触发条件
    "description": "当用户询问当前具体时间或日期时使用此工具。返回当前系统的日期和时间字符串。",
    "parameters": {}, # 此工具不需要参数
    "keywords": ["时间", "几点"] # 保留关键词
}

def execute(params: dict) -> dict:
    """
    Executes the plugin's main logic and returns the current time.

    Args:
        params (dict): An empty dictionary (no parameters needed).

    Returns:
        dict: A dictionary with 'status': 'ok' and 'result': current_time_string.
    """
    logger.info("Executing 'get_time' tool...")
    try:
        now = datetime.now()
        # Using Japan Standard Time based on context, adjust if needed
        # Format: YYYY年MM月DD日 HH点MM分SS秒
        current_time_str = now.strftime('%Y年%m月%d日 %H点%M分%S秒') 
        return {"status": "ok", "result": current_time_str}
    except Exception as e:
        logger.error(f"An unexpected error occurred in 'get_time' tool: {e}")
        return {"status": "error", "message": f"获取时间时发生未知错误: {e}"}
    
class TimePlugin:
    """A plugin to get the current time."""
    
    # The 'commands' property tells the PluginManager which keywords this plugin responds to.
    @property
    def commands(self) -> list[str]:
        """Returns a list of keywords that trigger this plugin."""
        return ["时间", "几点"]

    def execute(self, *args, **kwargs) -> str:
        """
        Executes the plugin's main logic and returns the current time as a string.
        """
        logger.info("Executing TimePlugin...")
        now = datetime.now()
        # Using Japan Standard Time (JST) as per context
        current_time = f"现在是下午{now.strftime('%I点%M分')}"
        return current_time

# This function is required by the PluginManager to know which class to load.
def get_plugin_class():
    """Returns the plugin class definition."""
    return TimePlugin