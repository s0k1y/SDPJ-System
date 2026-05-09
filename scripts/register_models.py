"""注册用户提供的 LLM 模型到系统中"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sdpj.infrastructure.llm_adapters.llm_adapter_lib import LLMAdapterLib

MODELS = [
    {
        "model_id": "GLM-Z1-Flash",
        "config": {
            "request_format": "openai",
            "api_url": "https://open.bigmodel.cn/api/paas/v4/",
            "api_key": "148e9d4b43084e81ba68d685ce9e6337.ulOfWumT5HMdggYT",
            "model": "GLM-Z1-Flash",
        },
    },
    {
        "model_id": "GLM-4-Flash-250414",
        "config": {
            "request_format": "openai",
            "api_url": "https://open.bigmodel.cn/api/paas/v4/",
            "api_key": "148e9d4b43084e81ba68d685ce9e6337.ulOfWumT5HMdggYT",
            "model": "GLM-4-Flash-250414",
        },
    },
    {
        "model_id": "GLM-4.7-Flash",
        "config": {
            "request_format": "openai",
            "api_url": "https://open.bigmodel.cn/api/paas/v4/",
            "api_key": "148e9d4b43084e81ba68d685ce9e6337.ulOfWumT5HMdggYT",
            "model": "GLM-4.7-Flash",
        },
    },
    {
        "model_id": "deepseek-v4-pro",
        "config": {
            "request_format": "openai",
            "api_url": "https://api.deepseek.com",
            "api_key": "sk-95033b3c11914e7484298d3b736f2d95",
            "model": "deepseek-v4-pro",
        },
    },
]


async def main():
    lib = LLMAdapterLib()
    for m in MODELS:
        adapter_content = json.dumps(m["config"], ensure_ascii=False)
        try:
            instance = await lib.install_adapter(m["model_id"], adapter_content)
            print(f"OK 已注册模型: {m['model_id']} (active={instance.active})")
        except Exception as e:
            print(f"FAIL 注册失败 {m['model_id']}: {e}")

    print(f"\n已注册模型清单: {[a['model_id'] for a in lib.list_adapters()]}")


if __name__ == "__main__":
    asyncio.run(main())
