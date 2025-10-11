# -*- coding: utf-8 -*-
"""
Main Application Entry Point for HALO
=====================================

This script defines the HALOApp class and starts the application.
"""
from loguru import logger
from .logger_setup import setup_logging
from .core_dispatcher import CoreDispatcher
from .config_manager import ConfigManager

class HALOApp:
    """
    The main application class for HALO.
    """
    def __init__(self):
        """
        Initializes the HALO application by setting up logging,
        configuration, and the core dispatcher.
        """
        # Setup logging as the first step
        setup_logging()
        
        logger.info("Initializing HALOApp...")
        # self.config = ConfigManager()
        # self.dispatcher = CoreDispatcher()
        logger.info("HALOApp initialized successfully.")

    def run(self):
        """
        Starts the execution of the application.
        """
        logger.info("HALO alive")
        # In the future, this method will trigger the core dispatcher's logic.


def main():
    """
    Main function to create and run the HALOApp instance.
    """
    try:
        app = HALOApp()
        app.run()
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()