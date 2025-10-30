# -*- coding: utf-8 -*-
"""
Core Dispatcher (Phase 4.9 - Final API Call Fix)
=====================================================
VERSION: V4.9 (Fixes V4.8 silent hang)

- [FIX V4.9] Updates the call to 'send_tool_result_back_to_llm'
  to match the new (V4.9) signature, removing the redundant
  parameter that caused the history bug and API hang.
- Retains V4.8 response handling, V4.7 prompting, V4.6 history isolation.
"""
from loguru import logger
import threading
import json
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

# ... (Imports remain the same as V4.8) ...
from .voice_module import VoiceModule
from .ui_interface import UIDashboard
from .state_manager import StateManager
from .conversation_plugin import ConversationPlugin # V4.9
from . import tool_registry
from .tool_registry import get_tool, get_all_tools
from .security_manager import SecurityManager # V3.7
from .intent_layer import IntentLayer # V4.5
from .cognitive_graph import CognitiveGraph
from .routing_policy import RoutingPolicy
from google.genai.types import FunctionDeclaration, Tool, FunctionCall, Content, Part, GenerateContentResponse, ToolConfig, GenerateContentConfig

# ... (PROJECT_ROOT_FOR_PROMPT definition unchanged from V4.7) ...
try:
    PROJECT_ROOT_FOR_PROMPT = SecurityManager.PROJECT_ROOT
except AttributeError:
     try:
          PROJECT_ROOT_FOR_PROMPT = SecurityManager().PROJECT_ROOT
          logger.warning("V4.7: Accessing PROJECT_ROOT via SecurityManager instance.")
     except Exception:
          PROJECT_ROOT_FOR_PROMPT = Path(".").resolve()
          logger.error("V4.7: Could not determine PROJECT_ROOT for prompt enhancement!")


class CoreDispatcher:
    """
    (V4.9) Orchestrates the cognitive sequence with Final API Call Fix.
    """

    def __init__(self, voice_module: VoiceModule, ui_dashboard: UIDashboard,
                 state_manager: StateManager, conversation_plugin: ConversationPlugin, # V4.9
                 tools: dict):
        """
        Initializes the V4.9 Dispatcher.
        """
        logger.info("Initializing CoreDispatcher (Phase 4.9 - Final API Call Fix)...") # V4.9
        self.voice = voice_module
        self.ui = ui_dashboard
        self.state_manager = state_manager
        self.conversation: ConversationPlugin = conversation_plugin # V4.9
        self.tools = tools

        # ... (Cognitive modules init unchanged from V4.8) ...
        self.intent_layer = IntentLayer() # V4.5
        self.cognitive_graph = CognitiveGraph()
        self.routing_policy = RoutingPolicy()
        self.security = SecurityManager() # V3.7

        # ... (LLM Configs unchanged from V4.8) ...
        self.gemini_tool_schema = self.conversation._convert_tool_schema(tools)
        if self.gemini_tool_schema:
            tool_config_any = ToolConfig(function_calling_config={"mode": "ANY"})
            self.tool_generation_config = GenerateContentConfig(tools=self.gemini_tool_schema, tool_config=tool_config_any)
        else:
            self.tool_generation_config = None
        tool_config_none = ToolConfig(function_calling_config={"mode": "NONE"})
        self.text_generation_config = GenerateContentConfig(tools=[], tool_config=tool_config_none)

        # ... (UI Binding unchanged from V4.8) ...
        self.ui.voice_button.config(command=self.start_voice_thread)
        self.ui.text_button.config(command=self.start_text_thread)
        logger.info(f"CoreDispatcher (V4.9) initialized. Project root for prompts: {PROJECT_ROOT_FOR_PROMPT}") # V4.9 log


    # --- UI Lock/Unlock, Thread Starters, Interaction Handlers (Unchanged from V4.8) ---
    def _lock_ui(self):
        self.ui.voice_button.config(state="disabled")
        self.ui.text_button.config(state="disabled")
    def _unlock_ui(self):
        self.ui.update_status("Idle")
        self.ui.voice_button.config(state="normal")
        self.ui.text_button.config(state="normal")
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
    def handle_voice_interaction(self):
        final_response_text = "抱歉..." ; display_data = None
        try:
           self.ui.update_status("Listening..."); self.voice.speak("我在听")
           recognized_text = self.voice.listen()
           if recognized_text:
                self.ui.add_log(f"User said: '{recognized_text}'"); self.ui.update_status("Thinking...")
                final_response_text, display_data = self._handle_user_input(recognized_text) # Calls V4.9
                self.ui.update_status("Speaking...")
                if display_data: self.ui.add_search_result(display_data[0], display_data[1])
                self.ui.add_log(f"HALO Response: {final_response_text}"); self.voice.speak(final_response_text)
           else: final_response_text = "我没听清..." ; self.ui.add_log(final_response_text); self.voice.speak(final_response_text)
        except Exception as e: logger.error(f"...: {e}"); final_response_text = f"...: {e}"; self.ui.add_log(final_response_text)
        finally: self._unlock_ui()
    def handle_text_interaction(self, user_input: str):
        final_response_text = "抱歉..." ; display_data = None
        try:
            final_response_text, display_data = self._handle_user_input(user_input) # Calls V4.9
            if display_data: self.ui.add_search_result(display_data[0], display_data[1])
            self.ui.add_log(f"HALO Response: {final_response_text}")
        except Exception as e: logger.error(f"...: {e}"); final_response_text = f"...: {e}"; self.ui.add_log(final_response_text)
        finally: self._unlock_ui()

    # --- [Unchanged] Central Cognitive Processing Logic (V4.1 structure) ---
    def _handle_user_input(self, user_input: str) -> tuple[str, Any | None]:
        """
        V4.1 core logic structure remains, but calls V4.9 path functions.
        """
        logger.info(f"Handling user input (V4.9 Path): '{user_input}'") # V4.9 log
        final_text: str = "(默认内部错误回复)"
        display_data: Any | None = None
        dispatch_context = {
            "session_id": "halo_session_001", "user_input": user_input,
            "timestamp": datetime.now().isoformat(), "intent_meta": None,
            "intent_node_id": None, "route": None, "graph_nodes_created": []
        }
        try:
            intent_meta = self.intent_layer.analyze_intent(user_input, context={})
            dispatch_context["intent_meta"] = intent_meta
            logger.info(f"A1 IntentLayer result: {intent_meta}")
            intent_node = {
                 "type": "Intent", "label": intent_meta.get("intent", "unknown"),
                 "meta": {"confidence": intent_meta.get("confidence", 0.0), "raw_text": user_input, "route_suggestion": intent_meta.get("route")}
            }
            intent_node_id = self.cognitive_graph.add_node(intent_node)
            dispatch_context["intent_node_id"] = intent_node_id
            dispatch_context["graph_nodes_created"].append(intent_node_id)
            route = self.routing_policy.resolve(intent_meta)
            dispatch_context["route"] = route
            logger.info(f"A4 RoutingPolicy decision: '{route}'")
            if route == "cloud":
                final_text, display_data = self._process_with_gemini_cloud( # Calls V4.9
                    user_input, dispatch_context
                )
            elif route == "local":
                final_text, display_data = self._process_with_llm_tool_use( # Calls V4.9
                    user_input, dispatch_context
                )
            else: # Direct
                if intent_meta.get("intent") == "get_time":
                     final_text, display_data = self._direct_tool_execute( # Unchanged from V4.8
                         user_input, "get_time", {}, dispatch_context
                     )
                else:
                     logger.error(f"Unknown route '{route}' and not get_time. Defaulting to LLM.")
                     final_text, display_data = self._process_with_llm_tool_use( # Calls V4.9
                         user_input, dispatch_context
                     )
        except Exception as e:
            logger.exception(f"Error during V4.9 dispatch: {e}") # V4.9 log
            final_text = f"认知核心处理时发生内部错误: {e}"
        logger.debug(f"Dispatch context completed: {dispatch_context}")
        return final_text, display_data

    # --- [MODIFIED V4.9] Cloud Path (A4 / V4.4 / V4.8) ---
    def _process_with_gemini_cloud(self, user_input: str, dispatch_context: Dict[str, Any]) -> tuple[str, Any | None]:
        """
        (V4.4) Handles cloud tasks using cloud model with history=None.
        (V4.8) Added robust response handling.
        (V4.9) Calls V4.9 ConversationPlugin.
        """
        logger.info("Using Cloud Path (A4 / V4.9): Calling Gemini (Cloud Model, No History)...") # V4.9 log
        final_text: str = "(AI 未能提供云端回复)"
        llm_response: Optional[GenerateContentResponse] = None
        try:
            # V4.4 Fix: history=None
            logger.info("V4.4 Fix: Calling execute_llm_call with history=None")
            llm_response = self.conversation.execute_llm_call( # Calls V4.9 plugin
                 query=user_input, 
                 config=None, 
                 history=None, # V4.4 Fix
                 model_name=self.conversation.cloud_model_name 
            )
            # V4.8 Robust Response Handling
            logger.debug("Cloud Path: Processing LLM Response...")
            if not llm_response:
                logger.error("Cloud Path: LLM call returned None response.")
                final_text = "(AI服务未返回有效响应)"
            elif not llm_response.candidates:
                 logger.warning("Cloud Path: LLM response missing candidates.")
                 block_reason = getattr(llm_response.prompt_feedback, 'block_reason', None)
                 if block_reason: final_text = f"(抱歉，回复被安全策略阻止: {block_reason})"
                 else: final_text = "(AI未能生成有效回复，原因未知)"
            else:
                 try:
                     final_text = llm_response.candidates[0].content.parts[0].text
                     logger.debug("Cloud Path: Successfully extracted final text.")
                 except (AttributeError, IndexError, TypeError) as e:
                     logger.error(f"Cloud Path: Could not extract text from LLM response candidate: {e}")
                     final_text = "(AI回复格式错误，无法解析)"
            
            # V4.4 History Saving Logic
            current_history_before_save: list[Content] = self.state_manager.get_conversation_history()
            history_for_save = current_history_before_save + [Content(role="user", parts=[Part(text=user_input)])]
            history_for_save.append(Content(role="model", parts=[Part(text=final_text)]))
            self.state_manager.update_conversation_history(history_for_save)
            
            # A2/A3 Graph Hook
            memory_node_id = self.cognitive_graph.add_node({"type": "Memory", "label": "cloud_result", "meta": {"summary": final_text[:150], "route": "cloud", "source": self.conversation.cloud_model_name}})
            self.cognitive_graph.add_edge(dispatch_context["intent_node_id"], memory_node_id, "produces_memory")
            dispatch_context["graph_nodes_created"].append(memory_node_id)
            return final_text, None
        except Exception as e:
            logger.exception(f"Error during Cloud Path processing (V4.9): {e}") # V4.9 log
            return f"执行云端查询时出错: {e}", None


    # --- [MODIFIED V4.9] Local Path (A3 / V4.6 / V4.7 / V4.8 / V4.9) ---
    def _process_with_llm_tool_use(self, text_input: str, dispatch_context: Dict[str, Any]) -> tuple[str, Any | None]:
        """
        (V4.6) Logic for LLM Tool Use (local model, history=None).
        (V4.7) Uses enhanced prompt.
        (V4.8) Added robust response handling.
        [MODIFIED V4.9] Calls V4.9 ConversationPlugin with correct signature.
        """
        logger.info("Using Local Path (A3 / V4.9): Calling LLM (Local Model, No History, Abs Path Prompt)...") # V4.9 Log
        display_data: Any | None = None
        final_text: str = "(默认内部错误回复)"
        llm_response: Optional[GenerateContentResponse] = None
        final_llm_response: Optional[GenerateContentResponse] = None
        history_for_save = []
        try:
            # --- Step 1: First call to LLM (V4.7 Prompt, V4.6 History) ---
            prompt_prefix = (
                f"You are HALO's reasoning engine for local tasks. "
                f"Current project root is: '{PROJECT_ROOT_FOR_PROMPT}'. " 
                f"Analyze the User Input. If it matches a tool's function (like searching or reading files), "
                f"respond ONLY with a FunctionCall. IMPORTANT: For file paths (like 'file_path' parameter), "
                f"you MUST provide the full, absolute path based on the user request and the project root context. " 
                f"Do not use relative paths. Otherwise, respond with text.\n"
                f"User Input: "
            )
            llm_query = f"{prompt_prefix}{text_input}" 
            logger.info("V4.7 Fix: Calling execute_llm_call with enhanced prompt and history=None") 
            llm_response = self.conversation.execute_llm_call( # Calls V4.9 plugin
                 query=llm_query, 
                 config=self.tool_generation_config, 
                 history=None, # V4.6 Fix
                 model_name=self.conversation.local_model_name 
            )
            current_history_before_save: list[Content] = self.state_manager.get_conversation_history()
            history_for_save = current_history_before_save + [Content(role="user", parts=[Part(text=text_input)])]

            # V4.8 Robust Initial Response Handling
            if not llm_response:
                logger.error("Local Path: Initial LLM call returned None.")
                final_text = "(AI服务未返回有效响应)"
                self.state_manager.update_conversation_history(history_for_save + [Content(role="model", parts=[Part(text=final_text)])])
                return final_text, None
            elif not llm_response.candidates:
                 logger.warning("Local Path: Initial LLM response missing candidates.")
                 block_reason = getattr(llm_response.prompt_feedback, 'block_reason', None)
                 if block_reason: final_text = f"(抱歉，初步回复被阻止: {block_reason})"
                 else: final_text = "(AI未能生成初步回复)"
                 self.state_manager.update_conversation_history(history_for_save + [Content(role="model", parts=[Part(text=final_text)])])
                 return final_text, None
            else:
                history_for_save.append(llm_response.candidates[0].content)

            # --- Step 2: Check for Tool Call ---
            function_call: FunctionCall | None = None
            try:
                 candidate = llm_response.candidates[0]
                 if candidate.content.parts and hasattr(candidate.content.parts[0], 'function_call') and candidate.content.parts[0].function_call:
                      function_call = candidate.content.parts[0].function_call
            except (AttributeError, IndexError): pass

            if function_call:
                # ... (Tool call logic remains the same as V4.7) ...
                tool_name = function_call.name
                tool_args = dict(function_call.args) if function_call.args else {}
                logger.info(f"LLM requested tool call: '{tool_name}' with args: {tool_args}")
                dispatch_context["tool_call"] = {"name": tool_name, "args": tool_args}
                tool_node_id = self.cognitive_graph.add_node({"type": "Tool", "label": tool_name, "meta": {"module": "local_plugin"}})
                self.cognitive_graph.add_edge(dispatch_context["intent_node_id"], tool_node_id, "uses_tool")
                dispatch_context["graph_nodes_created"].extend([tool_node_id, f"edge_{tool_node_id}"])
                
                logger.debug(f"V4.7: Args received from LLM: {tool_args}")
                tool_args = self.security.sanitize_params(tool_name, tool_args)
                is_allowed, reason = self.security.is_action_allowed(tool_name, tool_args)
                
                if not is_allowed:
                     logger.warning(f"V4.7: Security check failed. Reason: {reason}")
                     tool_result_dict = {"status": "error", "message": f"安全策略拒绝: {reason}"}
                elif tool_name in self.tools:
                     logger.info(f"V4.7: Security check passed. Executing '{tool_name}'...")
                     try: tool_result_dict = self.tools[tool_name]["func"](tool_args)
                     except Exception as tool_e: tool_result_dict = {"status": "error", "message": f"工具执行失败: {tool_e}"}
                else: tool_result_dict = {"status": "error", "message": f"未知工具 '{tool_name}'"}
                dispatch_context["tool_result"] = tool_result_dict
                
                tool_api_result: Any
                if tool_result_dict.get("status") == "ok":
                     result_content = tool_result_dict["result"]
                     if isinstance(result_content, tuple): display_data = result_content; tool_api_result = {"status": "success", "files_found": len(result_content[1])}
                     else: tool_api_result = {"status": "success", "value": str(result_content)}
                else: tool_api_result = {"status": "error", "message": tool_result_dict.get("message", "Error.")}

                # Graph Hook: Memory & Entity Nodes
                memory_node_id = self.cognitive_graph.add_node({"type": "Memory", "label": "local_tool_result", "meta": {"summary": str(tool_api_result), "route": "local", "tool": tool_name}})
                self.cognitive_graph.add_edge(dispatch_context["intent_node_id"], memory_node_id, "produces_memory")
                dispatch_context["graph_nodes_created"].append(memory_node_id)
                if tool_name == "read_file_lines" and "file_path" in tool_args:
                    fp_arg = tool_args.get("file_path", ""); entity_label="invalid_path"
                    if fp_arg: 
                         try: entity_label = Path(fp_arg).name
                         except Exception: pass
                    entity_node_id = self.cognitive_graph.add_node({"type": "Entity", "label": entity_label, "meta": {"category": "file", "full_path": fp_arg}})
                    self.cognitive_graph.add_edge(dispatch_context["intent_node_id"], entity_node_id, "targets_entity")
                    dispatch_context["graph_nodes_created"].append(entity_node_id)


                # --- Step 4: Send Tool Result back (Minimal History) ---
                tool_response_part = Part(function_response={ "name": tool_name, "response": {"result": tool_api_result} })
                tool_response_content = Content(role="model", parts=[tool_response_part])
                
                # V4.6 Minimal history construction
                history_for_final_call = [
                    Content(role="user", parts=[Part(text=text_input)]),
                    llm_response.candidates[0].content, 
                    tool_response_content             
                ]

                logger.info("V4.6: Sending tool result back with MINIMAL constructed history")
                
                # [FIX V4.9] Removed redundant 'tool_response_content' parameter
                final_llm_response = self.conversation.send_tool_result_back_to_llm(
                    history=history_for_final_call, 
                    config=self.text_generation_config, # Force text
                    model_name=self.conversation.local_model_name 
                )
                
                # V4.8 Robust FINAL Response Handling
                logger.debug("Local Path: Processing FINAL LLM Response after tool call...")
                final_text = "(AI未能根据工具结果生成回复)" 
                history_for_save.append(tool_response_content) 
                if not final_llm_response:
                    logger.error("Local Path: Final LLM call returned None.")
                elif not final_llm_response.candidates:
                    logger.warning("Local Path: Final LLM response missing candidates.")
                    block_reason = getattr(final_llm_response.prompt_feedback, 'block_reason', None)
                    if block_reason: final_text = f"(抱歉，最终回复被阻止: {block_reason})"
                    else: final_text = "(AI未能根据工具结果生成回复，原因未知)"
                else:
                    try:
                        final_text = final_llm_response.candidates[0].content.parts[0].text
                        logger.debug("Local Path: Successfully extracted final text after tool call.")
                        history_for_save.append(final_llm_response.candidates[0].content) 
                    except (AttributeError, IndexError, TypeError) as e:
                         logger.error(f"Local Path: Could not extract final text: {e}")
                         final_text = "(AI最终回复格式错误，无法解析)"

            else:
                # --- Step 5: No Tool Call ---
                 final_text = "(AI未能生成聊天回复)"
                 try:
                    if llm_response.candidates: # Use initial response
                         final_text = llm_response.candidates[0].content.parts[0].text
                         logger.debug("Local Path: No tool call needed, using initial response text.")
                 except (AttributeError, IndexError): pass

            # (V4.8) Save history AFTER processing final response
            self.state_manager.update_conversation_history(history_for_save)
            
            return final_text, display_data

        except Exception as e:
             logger.exception(f"Error in _process_with_llm_tool_use (Local Path V4.9): {e}") # V4.9 Log
             current_history = self.state_manager.get_conversation_history()
             failed_user_content = Content(role="user", parts=[Part(text=text_input)])
             failed_model_content = Content(role="model", parts=[Part(text=f"处理本地命令时发生内部错误: {e}")])
             if not history_for_save or history_for_save[-1].role != "model":
                self.state_manager.update_conversation_history(current_history + [failed_user_content, failed_model_content])
             return f"处理本地命令时发生内部错误: {e}", None


    # --- [Unchanged from V4.4] Direct Path (A3 / V3.8) ---
    def _direct_tool_execute(self, user_input: str, tool_name: str, args: dict, dispatch_context: Dict[str, Any]) -> tuple[str, Any | None]:
        # ... (This function remains exactly the same as in V4.4) ...
        logger.info(f"Using Direct Path (A3/V3.8): Executing '{tool_name}'...")
        display_data: Any | None = None
        is_allowed, reason = self.security.is_action_allowed(tool_name, args)
        if not is_allowed: return f"安全策略阻止: {reason}", None
        tool_data = get_tool(tool_name) 
        if not tool_data or not callable(tool_data.get("func")): return f"错误: 未知的直接工具 '{tool_name}'。", None
        tool_node_id = self.cognitive_graph.add_node({"type": "Tool", "label": tool_name, "meta": {"module": "time_plugin"}})
        self.cognitive_graph.add_edge(dispatch_context["intent_node_id"], tool_node_id, "uses_tool")
        dispatch_context["graph_nodes_created"].extend([tool_node_id, f"edge_{tool_node_id}"])
        func = tool_data["func"]; result_dict = func(args) 
        dispatch_context["tool_result"] = result_dict
        if result_dict.get("status") == "ok": final_text = str(result_dict["result"])
        else: final_text = f"执行 {tool_name} 失败: {result_dict.get('message')}"
        memory_node_id = self.cognitive_graph.add_node({"type": "Memory", "label": "direct_tool_result", "meta": {"summary": final_text, "route": "direct", "tool": tool_name}})
        self.cognitive_graph.add_edge(dispatch_context["intent_node_id"], memory_node_id, "produces_memory")
        dispatch_context["graph_nodes_created"].append(memory_node_id)
        user_content = Content(role="user", parts=[Part(text=user_input)])
        model_content = Content(role="model", parts=[Part(text=final_text)])
        current_history = self.state_manager.get_conversation_history()
        self.state_manager.update_conversation_history(current_history + [user_content, model_content])
        return final_text, display_data