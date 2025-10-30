# -*- coding: utf-8 -*-
"""
State Manager for HALO (Phase 3 - V33 - Final JSON Serialization Fix)
=====================================================================
Correctly handling serialization of FunctionResponse objects within Parts.
"""
import json
from pathlib import Path
from loguru import logger
# Import necessary types for deserialization and type hinting
from google.genai.types import Content, Part, FunctionCall, FunctionResponse # Added FunctionResponse
from typing import Any

STATE_FILE_PATH = Path("halo_state.json")
MAX_HISTORY_TURNS = 20 # Limit history pairs

# --- Manual Serialization/Deserialization Helpers ---

def _part_to_dict(part: Part) -> dict[str, Any]:
    """Manually convert a Part object to a serializable dict."""
    data = {}
    # Check for text attribute safely
    try:
        if part.text:
            data['text'] = part.text
    except AttributeError:
        pass # Ignore if text attribute doesn't exist or is None

    # Check for function_call attribute safely
    try:
        if part.function_call:
            data['function_call'] = {
                'name': part.function_call.name,
                'args': dict(part.function_call.args) # Convert args to simple dict
            }
    except AttributeError:
        pass

    # [FIXED] Correctly serialize FunctionResponse
    try:
        if part.function_response:
            # function_response object has .name and .response attributes
            # .response should already be a serializable dict based on CoreDispatcher
            data['function_response'] = {
                 'name': part.function_response.name,
                 'response': part.function_response.response
            }
    except AttributeError:
        pass

    return data

def _content_to_dict(content_obj: Content) -> dict[str, Any]:
    """Manually convert a Content object to a serializable dict."""
    return {
        'role': content_obj.role,
        'parts': [_part_to_dict(part) for part in content_obj.parts]
    }

def _dict_to_part(part_dict: dict[str, Any]) -> Part:
    """Manually convert a dict back to a Part object."""
    if 'text' in part_dict:
        return Part(text=part_dict['text'])
    if 'function_call' in part_dict:
        fc_data = part_dict['function_call']
        return Part(function_call=FunctionCall(name=fc_data['name'], args=fc_data['args']))
    if 'function_response' in part_dict:
         fr_data = part_dict['function_response']
         # [FIXED] Recreate FunctionResponse object correctly using keyword arguments
         # Assuming the structure is {'name': 'tool_name', 'response': {...}}
         return Part(function_response=FunctionResponse(name=fr_data.get('name'), response=fr_data.get('response')))

    logger.warning(f"Could not fully deserialize part: {part_dict}. Returning empty Part.")
    return Part()

def _dict_to_content(content_dict: dict[str, Any]) -> Content:
    """Manually convert a dict back to a Content object."""
    role = content_dict.get('role', 'user')
    parts_list = [_dict_to_part(pd) for pd in content_dict.get('parts', [])]
    return Content(role=role, parts=parts_list)

# --- StateManager Class (Uses fixed helpers) ---

class StateManager:
    """Handles loading, saving, and accessing application state."""

    def __init__(self):
        """Initializes the StateManager and loads the initial state."""
        logger.info("Initializing StateManager...")
        self.state = {"conversation_history": []}
        self.load_state()
        logger.info("StateManager initialized.")

    def load_state(self):
        """Loads state from the JSON file and deserializes it."""
        if STATE_FILE_PATH.exists():
            try:
                with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content:
                        logger.warning(f"{STATE_FILE_PATH} is empty. Starting fresh.")
                        self.state["conversation_history"] = []; return
                    loaded_data = json.loads(content)

                loaded_history_dicts = loaded_data.get("conversation_history")
                if isinstance(loaded_history_dicts, list):
                     self.state["conversation_history"] = [_dict_to_content(d) for d in loaded_history_dicts]
                     logger.info(f"Loaded {len(self.state['conversation_history'])} turns from {STATE_FILE_PATH}")
                     self._trim_history()
                else:
                     logger.warning(f"Invalid format in {STATE_FILE_PATH}. Starting fresh.")
                     self.state["conversation_history"] = []
            except json.JSONDecodeError as e:
                 logger.error(f"Error decoding JSON from {STATE_FILE_PATH}: {e}. Starting fresh.")
                 # Optionally delete or rename the corrupted file here
                 # os.remove(STATE_FILE_PATH)
                 self.state["conversation_history"] = []
            except Exception as e:
                logger.exception(f"Unexpected error loading state from {STATE_FILE_PATH}: {e}")
                self.state["conversation_history"] = []
        else:
            logger.info(f"State file {STATE_FILE_PATH} not found. Starting fresh.")

    def save_state(self):
        """Serializes the current state and saves it to the JSON file."""
        try:
            self._trim_history()
            serializable_state = {
                # Use the fixed serialization helper
                "conversation_history": [_content_to_dict(c) for c in self.state["conversation_history"]]
            }
            with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, ensure_ascii=False, indent=4)
            logger.debug(f"Saved state ({len(self.state['conversation_history'])} turns) to {STATE_FILE_PATH}")
        except Exception as e:
            # Log the exception that occurred during saving
            logger.exception(f"Error saving state to {STATE_FILE_PATH}: {e}")

    def get_conversation_history(self) -> list[Content]:
        return list(self.state.get("conversation_history", []))

    def update_conversation_history(self, new_history: list[Content]):
        self.state["conversation_history"] = new_history
        self.save_state()

    def _trim_history(self):
        current_length = len(self.state.get("conversation_history", []))
        limit = MAX_HISTORY_TURNS * 2 # Assuming pairs
        if current_length > limit:
            start_index = current_length - limit
            self.state["conversation_history"] = self.state["conversation_history"][start_index:]
            logger.info(f"Trimmed history from {current_length} to {len(self.state['conversation_history'])} entries.")