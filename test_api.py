# -*- coding: utf-8 -*-
"""
独立的 Gemini API 密钥测试脚本
(功能：列出此 API 密钥可用的所有模型 - 修正版)
"""
import os
from dotenv import load_dotenv
# 确保您已安装新版库: pip install google-genai
from google import genai
from loguru import logger

def list_available_models():
    """
    加载 API 密钥，并打印出所有可用的模型列表。
    """
    logger.info("--- 启动 API 模型列表测试 (修正版) ---")
    
    # 1. 加载 .env 文件
    try:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("在 .env 文件中未找到 'GEMINI_API_KEY'。")
            return
        logger.info(f"成功读取 API 密钥 (格式: ...{api_key[-4:]})。")
    except Exception as e:
        logger.error(f"加载 .env 文件失败: {e}")
        return

    # 2. 尝试初始化 Client
    try:
        logger.info("正在初始化 genai.Client(api_key=...)")
        client = genai.Client(api_key=api_key)
        
        logger.info("正在向 API 请求可用模型列表...")
        
        # 3. 循环并打印所有可用的模型
        print("\n--- 您的 API 密钥可用的模型列表 ---")
        found_models = False
        
        # [FIXED] 修正了循环，只打印模型名称
        for model in client.models.list():
            print(f"  -> 模型名称: {model.name}")
            found_models = True
        
        if not found_models:
             print("  (未找到任何模型)")
        
        print("--------------------------------------\n")
        logger.success("模型列表获取成功。")
        logger.info("请在上面的列表中，找到一个您想使用的模型名称 (例如 'models/gemini-pro')，并将其复制给我。")

    except Exception as e:
        logger.error("--- API 测试失败！ ---")
        logger.error(f"在调用 API (list_models) 期间发生错误: {e}")
        logger.error("这仍然指向一个认证或项目启用问题。请再次确认 'Generative Language API' 已在 Google Cloud Console 中启用。")

if __name__ == "__main__":
    list_available_models()