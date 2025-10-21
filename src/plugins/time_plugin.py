# -*- coding: utf-8 -*-
"""
Time Plugin for HALO
====================

A simple plugin that provides the current time.
"""
from datetime import datetime
from loguru import logger

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