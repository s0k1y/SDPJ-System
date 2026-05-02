"""LLMAdapterLib 主模块"""
import aiohttp
from enum import Enum


class LLMErrorType(Enum):
    """LLM 错误类型"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    UNKNOWN_ERROR = "unknown_error"


class LLMAdapterLib:
    """大模型 API 适配库"""

    @staticmethod
    async def call_openai(prompt: str, api_key: str, model: str = "gpt-4") -> dict:
        """调用 OpenAI API"""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"model": model, "messages": [{"role": "user", "content": prompt}]}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": LLMErrorType.API_ERROR.value, "status": resp.status}
        except aiohttp.ClientError as e:
            return {"error": LLMErrorType.NETWORK_ERROR.value, "message": str(e)}
        except Exception as e:
            return {"error": LLMErrorType.UNKNOWN_ERROR.value, "message": str(e)}

    @staticmethod
    async def call_anthropic(prompt: str, api_key: str, model: str = "claude-3") -> dict:
        """调用 Anthropic API"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        data = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {"error": LLMErrorType.API_ERROR.value, "status": resp.status}
        except aiohttp.ClientError as e:
            return {"error": LLMErrorType.NETWORK_ERROR.value, "message": str(e)}
        except Exception as e:
            return {"error": LLMErrorType.UNKNOWN_ERROR.value, "message": str(e)}
