"""联网搜索（Tavily API）。

未配置 Key 或请求失败时抛出异常，由 UI 层决定降级方式。
"""
from __future__ import annotations

import os

import requests

TAVILY_ENDPOINT = "https://api.tavily.com/search"


def is_configured() -> bool:
    """是否已配置 Tavily API Key。"""
    return bool(os.getenv("TAVILY_API_KEY"))


def search(query: str, max_results: int = 4, timeout: int = 30) -> list[dict]:
    """调用 Tavily 检索网页，返回标题/链接/摘要列表。"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 TAVILY_API_KEY，无法进行联网搜索。")

    response = requests.post(
        TAVILY_ENDPOINT,
        json={
            "api_key": api_key,
            "query": query,
            "max_results": max_results,
        },
        timeout=timeout,
    )
    response.raise_for_status()

    return [
        {
            "title": item.get("title", "网页结果"),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
        }
        for item in response.json().get("results", [])
    ]
