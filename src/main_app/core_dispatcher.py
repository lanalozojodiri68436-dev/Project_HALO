# -*- coding: utf-8 -*-
"""
Core Dispatcher
===============

The central orchestrator for the application's main logic.
"""
from loguru import logger
import threading

from .voice_module import VoiceModule
from .ui_interface import UIDashboard
from .plugin_manager import PluginManager
from .state_manager import StateManager

class CoreDispatcher:
    """
    Orchestrates the main business logic of the HALO application.
    """
    def __init__(self, voice_module: VoiceModule, ui_dashboard: UIDashboard, 
                 plugin_manager: PluginManager, state_manager: StateManager):
        """Initializes the CoreDispatcher and links all core modules."""
        logger.info("Initializing CoreDispatcher...")
        self.voice = voice_module
        self.ui = ui_dashboard
        self.plugins = plugin_manager
        self.state = state_manager
        
        # Link the voice button to the voice interaction logic
        self.ui.voice_button.config(command=self.start_listening_thread)
        # [NEW] Link the new text button to the text interaction logic
        self.ui.text_button.config(command=self.handle_text_command)
        
        logger.info("CoreDispatcher initialized and modules linked.")

    # --- Voice Interaction Logic (Unchanged) ---
    def start_listening_thread(self):
        """Starts the voice listening process in a separate thread."""
        self.ui.voice_button.config(state="disabled")
        self.ui.text_button.config(state="disabled")
        self.ui.add_log("Starting listening thread...")
        threading.Thread(target=self.handle_voice_interaction, daemon=True).start()

    def handle_voice_interaction(self):
        """Handles the main voice interaction loop: listen, process, speak."""
        try:
            self.ui.update_status("Listening...")
            self.voice.speak("我在听")
            recognized_text = self.voice.listen()
            
            
            if recognized_text:
                self.ui.add_log(f"User said: '{recognized_text}'")
                self.ui.update_status("Thinking...")
                
                response_data = self._process_command(recognized_text)
                
                # [MODIFIED] Check if the response is a tuple (search result) or string
                if isinstance(response_data, tuple):
                    display_text, _ = response_data
                    self.ui.add_search_result(display_text, _)
                    self.voice.speak("好的，已经为您找到。") # General voice confirmation
                else: # It's a simple string response
                    self.ui.add_log(f"HALO Response: {response_data}")
                    self.voice.speak(response_data)
        finally:
            self.ui.update_status("Idle")
            self.ui.voice_button.config(state="normal")
            self.ui.text_button.config(state="normal")

    # --- [NEW] Text Interaction Logic ---
    def handle_text_command(self):
        """Handles a command entered via the text input dialog."""
        user_input = self.ui.get_text_input("Text Command", "Please enter your command:")
        
        if user_input:
            self.ui.add_log(f"User typed: '{user_input}'")
            self.ui.update_status("Processing...")
            
            response_data = self._process_command(user_input)
            
            # [MODIFIED] Check if the response is a tuple or string
            if isinstance(response_data, tuple):
                display_text, _ = response_data
                self.ui.add_search_result(display_text, _) # Call the new UI method
            else: # It's a simple string response
                self.ui.add_log(f"HALO Response: {response_data}")

            self.ui.update_status("Idle")
        else:
            self.ui.add_log("Text command cancelled.")
    # --- [NEW] Shared Command Processing Logic ---
    def _process_command(self, text_input: str) -> str | tuple:
        """
        A shared function to process both voice and text commands.
        [MODIFIED] Now returns either a string or a tuple.
        """
        response_data = None
        for command_keyword in self.plugins.command_map.keys():
            if command_keyword in text_input:
                query = text_input.partition(command_keyword)[-1].strip()
                logger.info(f"Command '{command_keyword}' detected with query: '{query}'.")
                response_data = self.plugins.execute_command(command_keyword, query=query)
                break
        
        if not response_data:
            response_data = "我暂时还听不懂这个命令。"
            
        return response_data