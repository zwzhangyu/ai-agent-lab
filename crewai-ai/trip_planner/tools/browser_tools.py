"""网页抓取与总结工具（适配版）。

原示例依赖 Browserless 云服务和 unstructured 库；本项目改为
直接用 requests 抓取网页 + BeautifulSoup 提取正文，再用 LLM 总结，
这样无需额外注册 Browserless，也少了一个较重的依赖。
"""

import requests
from bs4 import BeautifulSoup
from crewai import Agent, Task
from crewai.tools import tool

from llm_config import get_llm


class BrowserTools:

    @tool("抓取并总结网页内容")
    def scrape_and_summarize_website(website):
        """用于抓取指定网页并总结其主要内容。"""
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(website, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            return f"抓取网页失败：{exc}"

        soup = BeautifulSoup(response.text, "html.parser")
        # 去掉脚本、样式、导航等噪声标签，只保留正文
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if not text:
            return "该网页没有可总结的正文内容。"

        agent = Agent(
            role="首席研究员",
            goal="基于网页内容做出精准、重点突出的中文总结",
            backstory="你是一名资深研究员，擅长从大量网页文本中提炼最关键的信息。",
            llm=get_llm(),
            allow_delegation=False,
        )
        task = Task(
            agent=agent,
            description=(
                "分析并总结下面的网页内容，只返回总结本身，不要多余解释。\n\n"
                f"网页内容\n----------\n{text[:8000]}"
            ),
            expected_output="一段简洁、覆盖关键信息的中文网页总结。",
        )
        output = task.execute()
        return getattr(output, "raw", str(output))
