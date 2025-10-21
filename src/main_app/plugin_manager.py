# -*- coding: utf-8 -*-
"""
Plugin Manager for HALO
=======================

Handles the dynamic loading and management of plugins.
"""
from loguru import logger
import importlib.util
from pathlib import Path

class PluginManager:
    """Manages the lifecycle of HALO plugins."""

    def __init__(self):
        """Initializes the PluginManager."""
        logger.info("Initializing PluginManager...")
        self.plugins = {}
        # [NEW] A mapping from command keywords to the plugin that handles them.
        self.command_map = {}
        logger.info("PluginManager initialized.")

    def load_plugins(self, plugin_dir: str = "src/plugins"):
        """
        Dynamically loads plugins from a specified directory.
        """
        logger.info(f"Scanning for plugins in: '{plugin_dir}'")
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists() or not plugin_path.is_dir():
            logger.warning(f"Plugin directory '{plugin_dir}' not found. Skipping plugin loading.")
            return

        for file in plugin_path.glob("*.py"):
            if file.name.startswith("_"):
                continue

            try:
                module_name = file.stem
                spec = importlib.util.spec_from_file_location(module_name, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "get_plugin_class"):
                    plugin_class = module.get_plugin_class()
                    plugin_instance = plugin_class()
                    
                    # Register the plugin and its commands
                    if hasattr(plugin_instance, "commands"):
                        self.plugins[module_name] = plugin_instance
                        for command in plugin_instance.commands:
                            self.command_map[command] = plugin_instance
                            logger.info(f"Registered command '{command}' for plugin '{module_name}'.")
                    else:
                        logger.warning(f"Plugin '{module_name}' has no 'commands' property.")
                else:
                    logger.warning(f"File '{file.name}' is not a valid plugin (missing get_plugin_class function).")

            except Exception as e:
                logger.error(f"Failed to load plugin from '{file.name}': {e}")

    def execute_command(self, command: str, *args, **kwargs) -> str | None:
        """
        Finds the appropriate plugin for a command and executes it.
        
        Args:
            command (str): The command keyword to execute.
            
        Returns:
            str | None: The result from the plugin, or None if no plugin is found.
        """
        plugin = self.command_map.get(command)
        if plugin and hasattr(plugin, "execute"):
            return plugin.execute(*args, **kwargs)
        return None