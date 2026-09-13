"""网络搜索工具（适配版）。

原示例使用 Serper（google.serper.dev）；本项目改用 Tavily，
因为你的 .env 中已有 TAVILY_API_KEY，无需额外注册 Serper。
"""

import os

import requests
from crewai.tools import tool


class SearchTools:

    @tool("搜索互联网")
    def search_internet(query):
        """用于搜索互联网上某个主题的最新信息，并返回相关结果。"""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "未配置 TAVILY_API_KEY，无法进行网络搜索。"

        top_result_to_return = 4
        url = "https://api.tavily.com/search"
        payload = {"api_key": api_key, "query": query, "max_results": top_result_to_return}
        headers = {"content-type": "application/json"}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            results = response.json().get("results", [])
        except requests.RequestException as exc:
            return f"搜索请求失败：{exc}"

        if not results:
            return "抱歉，没有找到相关信息，请检查 TAVILY_API_KEY 是否有效。"

        string = []
        for result in results[:top_result_to_return]:
            string.append("\n".join([
                f"标题: {result.get('title', '')}",
                f"链接: {result.get('url', '')}",
                f"摘要: {result.get('content', '')}",
                "\n-----------------",
            ]))
        return "\n".join(string)
