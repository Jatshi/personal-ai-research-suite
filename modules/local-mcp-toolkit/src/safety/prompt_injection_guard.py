from __future__ import annotations

import re


RISK_PATTERNS = [
    r"ignore (all )?(previous|prior) instructions",
    r"忽略(之前|以上|所有).*指令",
    r"泄露.*(密钥|token|api key|secret)",
    r"访问.*(workspace|工作区).*外",
    r"delete .*all files",
    r"删除.*(所有|大量).*文件",
    r"overwrite .*files",
    r"覆盖.*文件",
]


def scan_prompt_injection(text: str) -> dict:
    hits = []
    for pattern in RISK_PATTERNS:
        if re.search(pattern, text or "", flags=re.I):
            hits.append(pattern)
    return {"has_risk": bool(hits), "warnings": hits}

