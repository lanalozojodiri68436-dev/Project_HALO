# -*- coding: utf-8 -*-
"""
Everything Search Plugin for HALO
=================================

A plugin to perform fast file searches using the Everything command-line tool.
(With CJK width-aware formatting)
"""
import subprocess
from loguru import logger
from pathlib import Path
from datetime import datetime
import locale
# [NEW] Import unicodedata to check character width
import unicodedata

# --- [NEW] Helper Functions for CJK Formatting ---
tool_spec = {
    "name": "search_files",
    "description": "当用户想要在本地电脑文件系统中查找文件或文件夹时使用此工具。根据提供的关键词进行搜索，并返回匹配结果的列表。",
    "parameters": {
        "file_name": {"type": "string", "required": True, "description": "用户想要搜索的文件名、部分文件名或相关关键词。例如：'年度报告', 'budget.xlsx', '.log'。"},
        "max_results": {"type": "integer", "required": False, "default": 10, "description": "返回的最大结果数量。"}
    },
    "keywords": ["找", "搜索", "查找", "查找文件", "搜索文件"] # <-- 添加了 "找"
}

def get_display_width(text: str) -> int:
    """Calculates the actual display width of a string (CJK chars count as 2)."""
    width = 0
    for char in text:
        # 'F' (Fullwidth), 'W' (Wide), 'A' (Ambiguous) are treated as 2-width
        if unicodedata.east_asian_width(char) in ('F', 'W', 'A'):
            width += 2
        else:
            width += 1
    return width

def truncate_by_width(text: str, max_width: int) -> str:
    """Truncates a string to not exceed a maximum display width."""
    current_width = 0
    for i, char in enumerate(text):
        char_width = 2 if unicodedata.east_asian_width(char) in ('F', 'W', 'A') else 1
        if current_width + char_width > max_width - 3: # -3 for "..."
            return text[:i] + "..."
        current_width += char_width
    return text

# --- (Original _format_size function) ---

def _format_size(size_bytes: int) -> str:
    if size_bytes is None: return "N/A"
    power = 1024; n = 0
    power_labels = {0: '', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size_bytes >= power and n < len(power_labels) -1 :
        size_bytes /= power; n += 1
    return f"{size_bytes:.1f} {power_labels[n]}"

# --- (Plugin Class) ---
def execute(params: dict) -> dict:
    # [MODIFIED] Get 'file_name' instead of 'query'
    query = params.get("file_name") # <-- Use file_name here
    max_results = params.get("max_results", tool_spec["parameters"]["max_results"]["default"])

    if not query:
        # [MODIFIED] Update error message
        return {"status": "error", "message": "错误：缺少必要的 'file_name' 参数。"}

    logger.info(f"Executing 'search_files' tool with query: '{query}', max_results: {max_results}")
    # ... (rest of the execute function remains the same, using the 'query' variable) ...
    try:
        command = ["es", "-n", str(max_results), query] # Still use 'query' variable here
        system_encoding = locale.getpreferredencoding()
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding=system_encoding)
        
        file_paths_str = result.stdout.strip().split('\n')
        
        if not file_paths_str or not file_paths_str[0]:
            return {"status": "ok", "result": f"没有找到与“{query}”相关的任何文件。"} # Still ok status, just no results

        file_path_objects = [Path(p) for p in file_paths_str]
        
        response_lines = [f"好的，为您找到 {len(file_path_objects)} 个结果：\n"]
        COL_NAME_WIDTH = 30; COL_PATH_WIDTH = 55; COL_SIZE_WIDTH = 10
        
        h_name = "名称"; h_path = "路径"; h_size = "大小"; h_time = "修改时间"
        header = h_name + (' ' * (COL_NAME_WIDTH - get_display_width(h_name)))
        header += h_path + (' ' * (COL_PATH_WIDTH - get_display_width(h_path)))
        header += (' ' * (COL_SIZE_WIDTH - get_display_width(h_size))) + h_size
        header += "  " + h_time
        separator = ('-' * COL_NAME_WIDTH) + ('-' * COL_PATH_WIDTH) + ('-' * COL_SIZE_WIDTH) + "  " + ('-' * 19)
        
        response_lines.append(header)
        response_lines.append(separator)

        for file_path in file_path_objects:
            try:
                stats = file_path.stat()
                name = truncate_by_width(file_path.name, COL_NAME_WIDTH)
                parent_path = truncate_by_width(str(file_path.parent), COL_PATH_WIDTH)
                size = _format_size(stats.st_size)
                m_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y/%m/%d %H:%M')

                row = name + (' ' * (COL_NAME_WIDTH - get_display_width(name)))
                row += parent_path + (' ' * (COL_PATH_WIDTH - get_display_width(parent_path)))
                row += (' ' * (COL_SIZE_WIDTH - get_display_width(size))) + size
                row += "  " + m_time
                response_lines.append(row)
            except FileNotFoundError:
                continue
        
        # Return both the display string and the raw path data in the 'result' field
        formatted_result = ("\n".join(response_lines), file_path_objects)
        return {"status": "ok", "result": formatted_result}

    except FileNotFoundError:
        logger.error("'es.exe' not found. Please ensure Everything CLI is installed and in your system's PATH.")
        return {"status": "error", "message": "错误：找不到 Everything 的命令行工具 (es.exe)。"}
    except Exception as e:
        logger.error(f"An unexpected error occurred in 'search_files' tool: {e}")
        return {"status": "error", "message": f"执行搜索时发生未知错误: {e}"}
    
class EverythingPlugin:
    """A plugin to integrate with the Everything search tool."""
    
    @property
    def commands(self) -> list[str]:
        return ["搜索", "查找", "查找文件", "搜索文件"]

    def execute(self, query: str) -> tuple[str, list[Path]] | str:
        """
        [MODIFIED] Executes search and returns a width-formatted table.
        """
        if not query:
            return "请告诉我您想搜索什么文件。"
            
        logger.info(f"Executing EverythingPlugin with query: '{query}'")
        try:
            command = ["es", "-n", "5", query]
            system_encoding = locale.getpreferredencoding()
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding=system_encoding)
            
            file_paths_str = result.stdout.strip().split('\n')
            
            if not file_paths_str or not file_paths_str[0]:
                return f"抱歉，没有找到与“{query}”相关的任何文件。"

            file_path_objects = [Path(p) for p in file_paths_str]
            
            response_lines = [f"好的，为您找到 {len(file_path_objects)} 个结果：\n"]
            
            # --- [MODIFIED] Manual Table Formatting ---
            COL_NAME_WIDTH = 30
            COL_PATH_WIDTH = 55
            COL_SIZE_WIDTH = 10
            
            # Build Header
            h_name = "名称"; h_path = "路径"; h_size = "大小"; h_time = "修改时间"
            header = h_name + (' ' * (COL_NAME_WIDTH - get_display_width(h_name)))
            header += h_path + (' ' * (COL_PATH_WIDTH - get_display_width(h_path)))
            header += (' ' * (COL_SIZE_WIDTH - get_display_width(h_size))) + h_size # Right align
            header += "  " + h_time
            
            # Build Separator
            separator = ('-' * COL_NAME_WIDTH)
            separator += ('-' * COL_PATH_WIDTH)
            separator += ('-' * COL_SIZE_WIDTH)
            separator += "  " + ('-' * 19)
            
            response_lines.append(header)
            response_lines.append(separator)

            for file_path in file_path_objects:
                try:
                    stats = file_path.stat()
                    
                    # Get data and truncate by width
                    name = truncate_by_width(file_path.name, COL_NAME_WIDTH)
                    parent_path = truncate_by_width(str(file_path.parent), COL_PATH_WIDTH)
                    size = _format_size(stats.st_size)
                    m_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y/%m/%d %H:%M')

                    # Build row with manual padding
                    row = name + (' ' * (COL_NAME_WIDTH - get_display_width(name)))
                    row += parent_path + (' ' * (COL_PATH_WIDTH - get_display_width(parent_path)))
                    row += (' ' * (COL_SIZE_WIDTH - get_display_width(size))) + size # Right align
                    row += "  " + m_time
                    
                    response_lines.append(row)
                except FileNotFoundError:
                    continue
            
            return ("\n".join(response_lines), file_path_objects)

        except FileNotFoundError:
            return "错误：找不到 Everything 的命令行工具 (es.exe)。"
        except Exception as e:
            logger.error(f"An error occurred in EverythingPlugin: {e}")
            return "执行搜索时发生未知错误。"

def get_plugin_class():
    return EverythingPlugin