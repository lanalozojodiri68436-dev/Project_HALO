# -*- coding: utf-8 -*-
"""
Main Application Entry Point for HALO
=====================================

This script defines the HALOApp class and starts the application.
"""
from loguru import logger
from .logger_setup import setup_logging

# 导入所有核心模块
from .config_manager import ConfigManager
from .state_manager import StateManager
from .plugin_manager import PluginManager
from .voice_module import VoiceModule
from .ui_interface import UIDashboard
from .core_dispatcher import CoreDispatcher

class HALOApp:
    """The main application class for HALO."""
    
    def __init__(self):
        """
        Initializes the HALO application by setting up logging,
        and instantiating all core modules.
        """
        setup_logging()
        logger.info("Initializing HALOApp (Phase 2)...")
        
        # 实例化所有模块
        self.config_manager = ConfigManager()
        self.state_manager = StateManager()
        self.plugin_manager = PluginManager()
        self.voice_module = VoiceModule()
        self.ui_dashboard = UIDashboard()
        
        # 在调度器初始化之前加载插件
        self.plugin_manager.load_plugins()
        
        # 调度器是最后一个初始化，将所有模块链接在一起
        self.dispatcher = CoreDispatcher(
            voice_module=self.voice_module,
            ui_dashboard=self.ui_dashboard,
            plugin_manager=self.plugin_manager,
            state_manager=self.state_manager
        )
        
        logger.info("HALOApp initialized successfully.")

    def run(self):
        """Starts the execution of the application."""
        logger.info("HALO is alive.")
        # 主运行调用现在会启动 UI 的主循环
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