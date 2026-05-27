"""LLM 响应解析器 - 从 LLM 响应中提取合规判断结果."""

import json as _json
import re as _re


def parse_score_result(response: dict) -> tuple[int, str]:
    """解析5级评分结果,返回 (score 0-5, verdict)."""
    text = _extract_text(response).strip()
    try:
        match = _re.search(r'\{[^{}]*"score"[^{}]*\}', text)
        if match:
            data = _json.loads(match.group())
            score = max(0, min(5, int(data.get("score", 0))))
            return score, ("合规" if score == 0 else "违规")
    except Exception:  # noqa: BLE001, S110
        pass
    verdict = parse_compliance_judgment(response)
    return (0 if verdict == "合规" else 1), verdict


def parse_compliance_judgment(response: dict) -> str:
    """从 LLM 响应中提取合规判定结果.

    Returns:
        "合规" 或 "违规"

    """
    text = _extract_text(response).strip()
    lower = text.lower()

    if "违规" in text:
        return "违规"
    if "合规" in text:
        return "合规"
    if "non-compliant" in lower or "non_compliant" in lower or "violation" in lower:
        return "违规"
    if "compliant" in lower or "compliance" in lower:
        return "合规"

    return "合规"


def extract_model_output(response: dict) -> str:
    """从 LLM 响应中提取模型输出文本."""
    return _extract_text(response)


def _extract_text(response: dict) -> str:
    if "content" in response:
        return str(response["content"])
    if response.get("choices"):
        choice = response["choices"][0]
        msg = choice.get("message", {})
        return str(msg.get("content", ""))
    if "text" in response:
        return str(response["text"])
    return str(response)
