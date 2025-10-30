# -*- coding: utf-8 -*-
"""
Conversation Plugin for HALO (Phase 4.9 - Final API Call Fix)
==============================================================
VERSION: V4.9 (Fixes V4.8 silent hang)

- [FIX V4.9] Corrects the signature and logic for 'send_tool_result_back_to_llm'.
  It no longer accepts a redundant 'tool_response_content' parameter,
  preventing the duplicate history bug that caused API hangs.
- Retains V4.3 logging and V4.2 model switching.
"""
from loguru import logger
from google import genai
from google.genai.types import FunctionDeclaration, Tool, Content, Part, GenerateContentResponse, GenerateContentConfig, ToolConfig
from typing import Any, Optional
import google.api_core.exceptions # V4.3

class ConversationPlugin:
    """
    (V4.9) Handles LLM interaction using stateless client.
    """

    def __init__(self, api_key: str):
        """Initializes the Gemini client and model names."""
        # ... (init unchanged from V4.2) ...
        if not api_key:
            logger.error("ConversationPlugin: API_KEY is missing. Disabling plugin.")
            self.client = None; self.local_model_name = None; self.cloud_model_name = None; return
        try:
            self.client = genai.Client(api_key=api_key)
            self.local_model_name = "models/gemini-2.5-flash" 
            self.cloud_model_name = "models/gemini-pro-latest" 
            logger.info(f"ConversationPlugin (V4.9) initialized.") # V4.9
            logger.info(f"  -> Local Model: {self.local_model_name}")
            logger.info(f"  -> Cloud Model: {self.cloud_model_name}")
        except Exception as e:
            logger.error(f"ConversationPlugin: Failed to configure Gemini Client: {e}")
            self.client = None

    def _convert_tool_schema(self, registered_tools: dict) -> list[Tool] | None:
        """Converts HALO's internal tool registry into Gemini API's Tool format."""
        # ... (unchanged from V30) ...
        if not registered_tools: return None
        gemini_tools = []
        for tool_name, tool_data in registered_tools.items():
            spec = tool_data.get("spec");
            if not spec: continue
            properties = {}; required_params = []
            param_spec = spec.get("parameters", {})
            for param_name, details in param_spec.items():
                param_type = "string"
                if details.get("type") == "integer": param_type = "integer"
                elif details.get("type") == "number": param_type = "number"
                elif details.get("type") == "boolean": param_type = "boolean"
                properties[param_name] = {"type": param_type, "description": details.get("description", "")}
                if details.get("required"): required_params.append(param_name)
            func_decl = FunctionDeclaration(name=tool_name, description=spec.get("description", ""),
                                            parameters={"type": "object", "properties": properties, "required": required_params})
            gemini_tools.append(Tool(function_declarations=[func_decl]))
        return gemini_tools if gemini_tools else None
    
    # [Unchanged V4.3]
    def execute_llm_call(self, query: str, config: GenerateContentConfig | None, 
                         history: list[Content] | None, model_name: str) -> GenerateContentResponse:
        """
        Sends a query (potentially with history) to the specified Gemini model.
        """
        if not self.client or not model_name:
             raise ConnectionError(f"Gemini client or model name '{model_name}' is not initialized.")
             
        logger.info(f"Sending stateless query to Gemini model: '{model_name}' (Query: '{query[:50]}...')")
        response = None
        try:
            # [FIX V4.9] Handle history=None case explicitly
            contents_arg = [Content(role="user", parts=[Part(text=query)])]
            if history:
                contents_arg = history + contents_arg

            logger.debug(f"Calling generate_content with model={model_name}, config={config}")
            response = self.client.models.generate_content(
                model=model_name, 
                contents=contents_arg, 
                config=config,
            )
            logger.debug(f"generate_content call returned. Response received.")
            
            # ... (V4.3 Logging unchanged) ...
            if response:
                 logger.debug(f"Response prompt_feedback: {response.prompt_feedback}")
                 if response.candidates:
                     logger.debug(f"Response candidates count: {len(response.candidates)}")
                     candidate = response.candidates[0]
                     logger.debug(f"  Candidate 0 finish_reason: {candidate.finish_reason}")
                     try:
                         text_preview = candidate.content.parts[0].text[:100] if candidate.content.parts and hasattr(candidate.content.parts[0], 'text') else "No text part"
                         logger.debug(f"  Candidate 0 text preview: '{text_preview}...'")
                     except Exception as log_e:
                         logger.warning(f"Could not log candidate text preview: {log_e}")
                 else:
                     logger.warning("Response received but contains no candidates.")
            else:
                 logger.warning("generate_content call returned None response.")
                 
            return response 
            
        except google.api_core.exceptions.GoogleAPICallError as api_error:
            logger.error(f"ConversationPlugin: GoogleAPICallError during generation (Model: {model_name}): {api_error}")
            try:
                logger.error(f"  API Error Details: {api_error.message}")
                if hasattr(api_error, 'response') and hasattr(api_error.response, 'text'):
                     logger.error(f"  API Response Body: {api_error.response.text}")
            except Exception as detail_e:
                 logger.error(f"  Could not get detailed API error info: {detail_e}")
            raise api_error
        except Exception as e:
            logger.error(f"ConversationPlugin: Unexpected Error during generation (Model: {model_name}): {e}")
            logger.exception("Full traceback for unexpected error:")
            raise e 

    # [MODIFIED V4.9] Fixed signature - removed redundant 'tool_response_content'
    def send_tool_result_back_to_llm(self, history: list[Content], 
                                     config: GenerateContentConfig | None, model_name: str) -> GenerateContentResponse:
        """
        Sends the constructed history (including tool response) back to the LLM.
        """
        if not self.client or not model_name:
            raise ConnectionError(f"Gemini client or model name '{model_name}' is not initialized.")
            
        logger.info(f"Sending stateless tool result back to Gemini model: '{model_name}'...")
        response = None 
        try:
            # [FIX V4.9] 'history' is now the complete payload.
            # No longer need 'updated_history = history + [tool_response_content]'
            logger.debug(f"Calling generate_content (tool response) with model={model_name}, config={config}")
            response = self.client.models.generate_content(
                model=model_name, 
                contents=history, # [FIX V4.9] Send the pre-constructed history
                config=config
            )
            logger.debug(f"generate_content (tool response) call returned.")
            
            # ... (V4.3 Logging unchanged) ...
            if response:
                 logger.debug(f"Tool Response Feedback: {response.prompt_feedback}")
                 if response.candidates:
                     logger.debug(f"Tool Response candidates count: {len(response.candidates)}")
                     candidate = response.candidates[0]
                     logger.debug(f"  Tool Response Candidate 0 finish_reason: {candidate.finish_reason}")
                     try:
                         text_preview = candidate.content.parts[0].text[:100] if candidate.content.parts and hasattr(candidate.content.parts[0], 'text') else "No text part"
                         logger.debug(f"  Tool Response Candidate 0 text preview: '{text_preview}...'")
                     except Exception as log_e:
                         logger.warning(f"Could not log tool response candidate text preview: {log_e}")
                 else:
                     logger.warning("Tool Response received but contains no candidates.")
            else:
                 logger.warning("generate_content (tool response) call returned None response.")

            return response

        except google.api_core.exceptions.GoogleAPICallError as api_error:
            # ... (V4.3 Logging unchanged) ...
            logger.error(f"ConversationPlugin: GoogleAPICallError sending tool result back (Model: {model_name}): {api_error}")
            try:
                logger.error(f"  API Error Details: {api_error.message}")
                if hasattr(api_error, 'response') and hasattr(api_error.response, 'text'):
                     logger.error(f"  API Response Body: {api_error.response.text}")
            except Exception as detail_e:
                 logger.error(f"  Could not get detailed API error info: {detail_e}")
            raise api_error
        except Exception as e:
            # ... (V4.3 Logging unchanged) ...
            logger.error(f"ConversationPlugin: Unexpected Error sending tool result back (Model: {model_name}): {e}")
            logger.exception("Full traceback for unexpected error:")
            raise e