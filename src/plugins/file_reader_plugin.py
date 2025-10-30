# -*- coding: utf-8 -*-
"""
File Reader Plugin for HALO (Phase 3 - Encoding Fix)
=====================================================

A plugin to read specified lines from a local text file.
[FIXED] Prioritizes UTF-8 encoding before falling back to system default.
"""
import os
from pathlib import Path
from loguru import logger
import locale

# --- Tool Specification (remains the same) ---
tool_spec = {
    "name": "read_file_lines",
    "description": "读取指定本地文本文件的特定行范围。例如，文件的最后N行、最前N行或指定行号范围。",
    "parameters": {
        "file_path": {
            "type": "string", 
            "required": True, 
            "description": "要读取的文件的完整绝对路径。例如：'C:\\Users\\User\\Documents\\report.txt'"
        },
        "lines_spec": {
            "type": "string", 
            "required": False, 
            "default": "last:10", 
            "description": "指定要读取的行范围。支持格式：'last:N', 'first:N', 'start-end'。默认为 'last:10'。"
        }
    },
    "keywords": ["读取", "查看", "读取文件", "查看文件", "打开文件内容", "给我文件内容"] # <-- 添加了 "读取", "查看"
}

# --- Security Configuration (remains the same) ---
ALLOWED_EXTENSIONS = {".txt", ".log", ".md", ".py", ".json", ".csv"} 
PROJECT_ROOT = Path(__file__).resolve().parents[2] 
ALLOWED_DIRECTORY = PROJECT_ROOT 

def is_path_allowed(file_path: Path) -> bool:
    """Checks if the file path is within allowed directories and has an allowed extension."""
    logger.debug(f"Checking security for path: {file_path}")
    
    if not file_path.is_absolute():
        logger.warning(f"Security check failed: Path is not absolute: {file_path}")
        return False
    if not file_path.exists() or not file_path.is_file():
         logger.warning(f"Security check failed: File does not exist or is not a file: {file_path}")
         return False

    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        logger.warning(f"Security check failed: Disallowed file extension: {file_path.suffix}")
        return False
        
    try:
        if not file_path.resolve().is_relative_to(ALLOWED_DIRECTORY.resolve()):
             logger.warning(f"Security check failed: Path is outside allowed directory ({ALLOWED_DIRECTORY}): {file_path}")
             return False
    except ValueError: 
         logger.warning(f"Security check failed: Path comparison error (possibly different drives): {file_path}")
         return False
    except Exception as e:
         logger.error(f"Unexpected error during path security check: {e}")
         return False

    logger.debug(f"Security check passed for: {file_path}")
    return True

# --- Main Execute Function (Encoding Logic Fixed) ---
def execute(params: dict) -> dict:
    """
    Reads specified lines from a file after security checks.
    [FIXED] Tries UTF-8 first, then system default encoding.
    """
    file_path_str = params.get("file_path")
    lines_spec = params.get("lines_spec", tool_spec["parameters"]["lines_spec"]["default"])

    if not file_path_str:
        return {"status": "error", "message": "错误：缺少必要的 'file_path' 参数。"}

    try:
        file_path = Path(file_path_str)

        if not is_path_allowed(file_path):
            return {"status": "error", "message": f"错误：出于安全原因，不允许访问指定的文件路径 ({file_path_str})。"}

        logger.info(f"Executing 'read_file_lines' tool for: '{file_path}' with spec: '{lines_spec}'")

        # --- [MODIFIED] Encoding Logic ---
        lines = []
        try:
            # Try UTF-8 first, as it's the most common for code/text files
            logger.debug("Attempting to read file with UTF-8...")
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # If UTF-8 fails, fallback to the system's preferred encoding
            system_encoding = locale.getpreferredencoding()
            logger.warning(f"UTF-8 decoding failed. Retrying with system encoding: {system_encoding}")
            try:
                with open(file_path, 'r', encoding=system_encoding, errors='ignore') as f:
                    lines = f.readlines()
            except Exception as e:
                logger.error(f"Failed to read file with both UTF-8 and system encoding: {e}")
                return {"status": "error", "message": f"读取文件时解码失败: {e}"}
        # --- End of Modified Encoding Logic ---

        total_lines = len(lines)
        start_line = 0
        end_line = total_lines

        spec_parts = lines_spec.lower().split(':')
        
        # ... (Rest of the line parsing logic remains the same) ...
        if len(spec_parts) == 2:
            spec_type = spec_parts[0]
            try:
                num = int(spec_parts[1])
                if spec_type == 'last': start_line = max(0, total_lines - num)
                elif spec_type == 'first': end_line = min(total_lines, num)
                else: logger.warning(f"Invalid lines_spec type: '{spec_type}'.")
            except ValueError: logger.warning(f"Invalid number in lines_spec: '{spec_parts[1]}'.")
        elif '-' in lines_spec:
             try:
                 start, end = map(int, lines_spec.split('-'))
                 start_line = max(0, start - 1); end_line = min(total_lines, end)
                 if start_line >= end_line: logger.warning(f"Invalid range: '{lines_spec}'."); start_line = 0; end_line = total_lines
             except ValueError: logger.warning(f"Invalid range format: '{lines_spec}'.")
        else:
            logger.warning(f"Unrecognized lines_spec format: '{lines_spec}'.")

        selected_lines = lines[start_line:end_line]
        
        # ... (Rest of the output limiting logic remains the same) ...
        MAX_OUTPUT_LINES = 50; MAX_OUTPUT_CHARS = 2000 
        output_str = "".join(selected_lines)
        if len(selected_lines) > MAX_OUTPUT_LINES: output_str = "".join(selected_lines[:MAX_OUTPUT_LINES]) + f"\n... (截断 {len(selected_lines)} 行)"
        if len(output_str) > MAX_OUTPUT_CHARS: output_str = output_str[:MAX_OUTPUT_CHARS] + f"\n... (截断 {len(output_str)} 字符)"

        if not output_str:
            result_message = f"文件 '{file_path.name}' 的指定行范围为空。"
        else:
            result_message = f"文件 '{file_path.name}' 的内容 ({lines_spec}) 如下：\n---\n{output_str}\n---"
            
        return {"status": "ok", "result": result_message}

    except FileNotFoundError:
        return {"status": "error", "message": f"错误：找不到文件 '{file_path_str}'。"}
    except PermissionError:
        return {"status": "error", "message": f"错误：没有权限读取文件 '{file_path_str}'。"}
    except Exception as e:
        logger.exception(f"An unexpected error in 'read_file_lines' for {file_path_str}: {e}")
        return {"status": "error", "message": f"读取文件时发生未知错误: {e}"}