# -*- coding: utf-8 -*-
"""
Core Dispatcher (Phase 3 - Real Tool Use - Chat Service V27 - Mode NONE Fix)
=============================================================================
Explicitly setting ToolConfig mode to "NONE" in the final step.
"""
from loguru import logger
import threading
import json
from pathlib import Path
from typing import Any 

from .voice_module import VoiceModule
from .ui_interface import UIDashboard
from .state_manager import StateManager
from .conversation_plugin import ConversationPlugin
from google.genai.types import FunctionDeclaration, Tool, FunctionCall, Content, Part, GenerateContentResponse, ToolConfig, GenerateContentConfig

class CoreDispatcher:
    """Orchestrates logic using a stateful ChatSession for LLM interaction."""

    def __init__(self, voice_module: VoiceModule, ui_dashboard: UIDashboard,
                 state_manager: StateManager, conversation_plugin: ConversationPlugin,
                 tools: dict):
        logger.info("Initializing CoreDispatcher (Phase 3 - Chat Service)...")
        self.voice = voice_module
        self.ui = ui_dashboard
        self.state = state_manager
        self.conversation = conversation_plugin
        self.tools = tools

        self.gemini_tool_schema = self.conversation._convert_tool_schema(tools)
        
        # [MODIFIED] Create ChatSession WITHOUT tool config first
        self.chat_session: Any | None = self.conversation.start_chat_session(None) 
        
        # [MODIFIED] Config WITH tools (for Step 1)
        if self.gemini_tool_schema:
            tool_config_any = ToolConfig(function_calling_config={"mode": "ANY"})
            self.tool_generation_config = GenerateContentConfig(tools=self.gemini_tool_schema, tool_config=tool_config_any)
        else:
            self.tool_generation_config = None
        
        # [MODIFIED] Config WITHOUT tools (for Step 4, forcing text response)
        tool_config_none = ToolConfig(function_calling_config={"mode": "NONE"})
        self.text_generation_config = GenerateContentConfig(tools=[], tool_config=tool_config_none) # Pass empty tools AND mode=NONE

        self.ui.voice_button.config(command=self.start_voice_thread)
        self.ui.text_button.config(command=self.start_text_thread)
        logger.info("CoreDispatcher initialized and ChatSession started.")

    def _lock_ui(self):
        self.ui.voice_button.config(state="disabled")
        self.ui.text_button.config(state="disabled")

    def _unlock_ui(self):
        self.ui.update_status("Idle")
        self.ui.voice_button.config(state="normal")
        self.ui.text_button.config(state="normal")

    # --- Interaction Threads (Remain the same) ---
    def start_voice_thread(self):
        self._lock_ui()
        self.ui.add_log("Starting listening thread...")
        threading.Thread(target=self.handle_voice_interaction, daemon=True).start()

    def start_text_thread(self):
        user_input = self.ui.get_text_input("Text Command", "Please enter your command:")
        if not user_input:
            self.ui.add_log("Text command cancelled."); return
        self._lock_ui()
        self.ui.add_log(f"User typed: '{user_input}'")
        self.ui.update_status("Processing...")
        threading.Thread(target=self.handle_text_interaction, args=(user_input,), daemon=True).start()

    # --- Interaction Handlers (Remain the same structure) ---
    def handle_voice_interaction(self):
        final_response_text = "抱歉..." ; display_data = None
        try:
           self.ui.update_status("Listening..."); self.voice.speak("我在听")
           recognized_text = self.voice.listen()
           if recognized_text:
                self.ui.add_log(f"User said: '{recognized_text}'"); self.ui.update_status("Thinking...")
                final_response_text, display_data = self._process_input_with_chat_session(recognized_text)
                self.ui.update_status("Speaking...")
                if display_data: self.ui.add_search_result(display_data[0], display_data[1])
                if not isinstance(final_response_text, str): final_response_text = "(处理时发生意外错误)"
                self.ui.add_log(f"HALO Response: {final_response_text}"); self.voice.speak(final_response_text)
           else: final_response_text = "我没听清..." ; self.ui.add_log(final_response_text); self.voice.speak(final_response_text)
        except Exception as e: logger.error(f"...: {e}"); final_response_text = f"...: {e}"; self.ui.add_log(final_response_text)
        finally: self._unlock_ui()

    def handle_text_interaction(self, user_input: str):
        final_response_text = "抱歉..." ; display_data = None
        try:
            final_response_text, display_data = self._process_input_with_chat_session(user_input)
            if display_data: self.ui.add_search_result(display_data[0], display_data[1])
            if not isinstance(final_response_text, str): final_response_text = "(处理时发生意外错误)"
            self.ui.add_log(f"HALO Response: {final_response_text}")
        except Exception as e: logger.error(f"...: {e}"); final_response_text = f"...: {e}"; self.ui.add_log(final_response_text)
        finally: self._unlock_ui()

    # --- [REWRITTEN] Central LLM + Tool Processing Logic (with Loop) ---
    def _process_input_with_chat_session(self, text_input: str) -> tuple[str, Any | None]:
        """
        Core logic for Phase 3 using ChatSession:
        Uses a loop to handle chained tool calls until a text response is returned.
        """
        display_data: Any | None = None
        final_text: str = "(默认内部错误回复)"
        
        if not self.chat_session:
             logger.error("Chat session is not initialized!")
             return "错误：聊天会话未初始化。", None

        try:
            # --- Step 1: Send user input (WITH tool config) ---
            logger.info(f"Sending message to chat session: '{text_input}'")
            llm_response: GenerateContentResponse = self.chat_session.send_message(
                 message=text_input,
                 generation_config=self.tool_generation_config # Pass config WITH tools
            )

            # --- [NEW] Step 2: Loop to handle tool calls ---
            while True:
                function_call: FunctionCall | None = None
                try:
                     candidate = llm_response.candidates[0]
                     if candidate.content.parts and hasattr(candidate.content.parts[0], 'function_call') and candidate.content.parts[0].function_call:
                          function_call = candidate.content.parts[0].function_call
                     else: 
                          logger.debug("No function call found. Breaking loop.")
                          break # Exit loop if no function call
                except (AttributeError, IndexError):
                     logger.debug("Error accessing function call. Breaking loop."); break

                if not function_call:
                     break # Safeguard exit

                # --- Step 3: Function Call Found, Execute Local Tool ---
                tool_name = function_call.name
                tool_args = dict(function_call.args) if function_call.args else {}
                logger.info(f"LLM requested tool call: '{tool_name}' with args: {tool_args}")

                if tool_name in self.tools:
                    # ... (Tool execution logic) ...
                    tool_func = self.tools[tool_name]["func"]
                    spec_params = self.tools[tool_name]["spec"].get("parameters", {})
                    required_params = spec_params.get("required", [])
                    missing_params = [p for p in required_params if p not in tool_args]
                    if missing_params:
                         tool_result_dict = {"status": "error", "message": f"Missing required: {', '.join(missing_params)}"}
                    else:
                         try: tool_result_dict = tool_func(tool_args)
                         except Exception as tool_e:
                              logger.error(f"...: {e}"); tool_result_dict = {"status": "error", "message": f"...: {e}"}
                else:
                    error_message = f"错误：未知工具 '{tool_name}'。"
                    tool_result_dict = {"status": "error", "message": error_message}
                    logger.error(error_message)

                # Process result
                if tool_result_dict.get("status") == "ok":
                     result_content = tool_result_dict["result"]
                     if isinstance(result_content, tuple) and len(result_content) == 2 and isinstance(result_content[1], list):
                          display_data = result_content # Store for UI
                          tool_api_result = {"status": "success", "files_found": len(result_content[1]), "paths": [str(p) for p in result_content[1]]}
                     else: tool_api_result = {"status": "success", "value": str(result_content)}
                else:
                     tool_api_result = {"status": "error", "message": tool_result_dict.get("message", "Error.")}
                     logger.error(f"Tool '{tool_name}' failed: {tool_api_result.get('message')}")
                
                # --- Step 4: Send Tool Result back (WITHOUT tool config) ---
                tool_response_part = Part(function_response={ "name": tool_name, "response": {"result": tool_api_result} })
                
                logger.info("Sending tool result back to chat session for final response...")
                # [MODIFIED] Send the part back WITH the 'text_generation_config' (mode=NONE)
                llm_response: GenerateContentResponse = self.chat_session.send_message(
                    message=tool_response_part,
                    generation_config=self.text_generation_config # Pass config WITHOUT tools
                )
                
                # The loop will now repeat, checking this new llm_response
            
            # --- Step 5: Loop Exited (No Function Call found) ---
            final_text = ""
            try:
                if llm_response.candidates:
                    for part in llm_response.candidates[0].content.parts:
                        if hasattr(part, 'text'):
                            final_text += part.text
                if not final_text:
                    logger.warning("Final LLM response did not contain text parts.")
                    final_text = "(AI未能生成有效回复)"
                    if llm_response.candidates and llm_response.prompt_feedback.block_reason:
                        final_text = f"(AI最终回复被阻止，原因: {llm_response.prompt_feedback.block_reason})"
            except Exception as e:
                logger.error(f"Error manually extracting text from final response: {e}")
                final_text = "(AI解析最终回复时出错)"
            
            if not isinstance(final_text, str):
                logger.error(f"Final response processing resulted in non-string type: {type(final_text)}. Using fallback.")
                final_text = "(处理时发生意外的内部错误)"

            return final_text, display_data

        except ConnectionError as conn_e:
             logger.error(f"LLM Connection Error: {conn_e}")
             return f"连接 AI 服务失败: {conn_e}", None
        except Exception as e:
             logger.exception(f"Unexpected error in _process_input_with_chat_session: {e}")
             return f"处理命令时发生内部错误: {e}", None