# -*- coding: utf-8 -*-
"""
State Manager for HALO
======================

Manages the application's state and memory.
"""
from loguru import logger

class StateManager:
    """Handles saving and retrieving application state."""

    def __init__(self):
        """Initializes the StateManager."""
        logger.info("Initializing StateManager...")
        self.state = {}
        logger.info("StateManager initialized.")

    def set_state(self, key: str, value):
        """
        Saves a value to the application state.
        
        Args:
            key (str): The key for the state variable.
            value: The value to store.
        """
        logger.debug(f"Setting state for '{key}'.")
        self.state[key] = value

    def get_state(self, key: str, default=None):
        """
        Retrieves a value from the application state.

        Args:
            key (str): The key of the state variable to retrieve.
            default: The default value to return if the key is not found.
        
        Returns:
            The stored value or the default.
        """
        return self.state.get(key, default)