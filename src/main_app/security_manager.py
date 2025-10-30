# -*- coding: utf-8 -*-
"""
Security Manager for HALO (Phase 3.7)
=====================================
Provides centralized security checks for tool execution.
"""
from loguru import logger
from pathlib import Path
from typing import Dict, Any, Tuple

# --- 安全配置 (未来应移至 config_manager) ---

# 路径白名单：只允许在这些目录及其子目录中执行文件操作
# (出于安全考虑，暂时只允许项目根目录)
ALLOWED_PATH_ROOTS = [
    Path(__file__).resolve().parents[2] # C:\...\Project_HALO
    # 以后可以从 config_manager 加载, e.g.:
    # Path.home() / "Documents",
    # Path.home() / "Desktop",
]

# 危险工具列表：需要额外确认的工具（当前为空）
DANGEROUS_TOOLS = {
    "run_powershell_command", # 示例
    "delete_file"             # 示例
}

# 参数限制
MAX_STRING_LENGTH = 512
MAX_LIST_RESULTS = 100

class SecurityManager:
    """
    Handles security checks for tool names and parameters.
    """
    def __init__(self):
        logger.info("Initializing SecurityManager (Phase 3.7)...")
        # 将路径字符串转换为已解析的 Path 对象
        self.allowed_roots = [Path(p).resolve() for p in ALLOWED_PATH_ROOTS]
        logger.info(f"Allowed path roots: {self.allowed_roots}")

    def sanitize_params(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理和截断参数，防止注入或超长输入。
        (GPT Step 3)
        """
        sanitized_params = {}
        for key, value in params.items():
            if isinstance(value, str):
                # 截断超长字符串
                if len(value) > MAX_STRING_LENGTH:
                    logger.warning(f"Sanitizing '{tool_name}': Param '{key}' truncated (>{MAX_STRING_LENGTH} chars).")
                    value = value[:MAX_STRING_LENGTH]
                # (未来可在此处添加 SQL 注入、路径遍历等的清理逻辑)
                
            elif isinstance(value, int):
                # 限制 'max_results' 等参数的上限
                if "max_results" in key and value > MAX_LIST_RESULTS:
                     logger.warning(f"Sanitizing '{tool_name}': Param '{key}' capped at {MAX_LIST_RESULTS}.")
                     value = MAX_LIST_RESULTS
                     
            sanitized_params[key] = value
            
        return sanitized_params

    def is_action_allowed(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        核心安全检查：检查工具是否危险，检查文件路径是否在白名单内。
        (GPT Step E, 3)
        
        Returns:
            Tuple[bool, str]: (is_allowed, reason_message)
        """
        logger.debug(f"Security check: Requesting tool '{tool_name}' with params: {params}")

        # 1. 危险工具检查 (GPT Step 3)
        if tool_name in DANGEROUS_TOOLS:
            # (lllan: 此处未来需要集成 UI 弹窗确认)
            logger.warning(f"Security check DENIED: Tool '{tool_name}' is high-risk and requires user confirmation (not implemented).")
            return False, f"工具 '{tool_name}' 属于高风险操作，需要用户确认。"

        # 2. 路径白名单检查 (针对 file_reader 和 search_files)
        # (我们假设所有与文件相关的参数都叫 'file_path' 或 'query'/'file_name')
        path_to_check_str = None
        if tool_name == "read_file_lines":
            path_to_check_str = params.get("file_path")
        elif tool_name == "search_files":
            # (搜索目前是安全的, 因为它只读 Everything 索引。但如果我们要限制搜索范围, 可以在此添加)
            pass 
        
        if path_to_check_str:
            try:
                file_path = Path(path_to_check_str).resolve()
                
                # 检查是否在任一白名单根目录下
                if not any(file_path.is_relative_to(root) for root in self.allowed_roots):
                    logger.warning(f"Security check DENIED: Path '{file_path}' is outside allowed roots: {self.allowed_roots}")
                    return False, f"安全策略拒绝：路径 '{file_path_str}' 不在允许的访问目录中。"
                    
            except Exception as e:
                logger.error(f"Security check FAILED during path validation: {e}")
                return False, f"安全检查失败：路径 '{path_to_check_str}' 格式无效。"

        # 3. (未来可添加速率限制等)

        logger.debug(f"Security check PASSED for tool '{tool_name}'.")
        return True, "Allowed"