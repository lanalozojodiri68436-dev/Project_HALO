# -*- coding: utf-8 -*-
"""
Configuration Manager
=====================

Handles loading and accessing application configuration from .env files.
"""
import os
from dotenv import load_dotenv
from loguru import logger

class ConfigManager:
    """Manages application settings by loading them from a .env file."""
    
    def __init__(self, env_path: str = '.env'):
        """
        Initializes the ConfigManager and loads environment variables.
        
        Args:
            env_path (str): The path to the .env file.
        """
        self.env_path = env_path
        self.load_config()

    def load_config(self):
        """Loads environment variables from the .env file."""
        if os.path.exists(self.env_path):
            load_dotenv(dotenv_path=self.env_path)
            logger.info(f"Configuration loaded from {self.env_path}")
        else:
            logger.warning(f"Configuration file not found at {self.env_path}. Using environment variables.")

    def get(self, key: str, default: str = None) -> str | None:
        """
        Retrieves a configuration value by its key.
        
        Args:
            key (str): The configuration key.
            default (str, optional): Default value if key is not found.

        Returns:
            str | None: The configuration value or the default.
        """
        return os.getenv(key, default)