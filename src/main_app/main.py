# -*- coding: utf-8 -*-
"""
Main Application Entry Point for HALO (Phase 3 - State Manager Integrated)
=========================================================================
Instantiating and injecting the StateManager.
"""
from loguru import logger
from .logger_setup import setup_logging
from .config_manager import ConfigManager
from .state_manager import StateManager 
from .plugin_manager import PluginManager 
from .voice_module import VoiceModule
from .ui_interface import UIDashboard
from .core_dispatcher import CoreDispatcher
from .conversation_plugin import ConversationPlugin
from .tool_registry import load_tools

class HALOApp:
    """The main application class for HALO."""
    
    def __init__(self):
        """
        Initializes HALO: logging, config, state manager, tools, core modules.
        """
        setup_logging()
        logger.info("Initializing HALOApp (Phase 3 - StateManager Integrated)...")
        
        self.config_manager = ConfigManager()
        gemini_api_key = self.config_manager.get("GEMINI_API_KEY")

        # Instantiate StateManager early
        self.state_manager = StateManager()

        self.registered_tools = load_tools()

        # Instantiate other core modules
        self.plugin_manager = PluginManager() 
        self.voice_module = VoiceModule()
        self.ui_dashboard = UIDashboard()
        self.conversation_plugin = ConversationPlugin(api_key=gemini_api_key)
        
        # Pass the state_manager instance to the dispatcher
        self.dispatcher = CoreDispatcher(
            voice_module=self.voice_module,
            ui_dashboard=self.ui_dashboard,
            state_manager=self.state_manager, # <-- Inject StateManager
            conversation_plugin=self.conversation_plugin,
            tools=self.registered_tools 
        )
        
        logger.info("HALOApp initialized successfully.")

    def run(self):
        """Starts the execution of the application."""
        logger.info("HALO is alive.")
        self.ui_dashboard.run()

def main():
    """Main function to create and run the HALOApp instance."""
    try:
        app = HALOApp()
        app.run()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()