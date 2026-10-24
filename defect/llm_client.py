"""DeepSeek LLM客户端。APIKEY在 .env 文件里，不要传到GitHub。"""
import os
import requests
import logging

logger = logging.getLogger(__name__)

# 从环境变量读APIKEY（.env文件）
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"


def call_deepseek(prompt: str, system: str = "") -> dict:
    """调用DeepSeek API，返回完整响应。"""
    if not API_KEY:
        logger.warning("DEEPSEEK_API_KEY 未设置，返回空结果")
        return {"choices": [{"message": {"content": "DEEPSEEK_API_KEY未配置"}}], "usage": {}}

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"DeepSeek API调用失败: {e}")
        return {"choices": [{"message": {"content": f"API调用失败: {e}"}}], "usage": {}}
