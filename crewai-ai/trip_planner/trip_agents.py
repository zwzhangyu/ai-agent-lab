"""行程规划团队中所有 Agent 的定义。

对照原示例（trip_agents.py）：
- 原示例使用默认 OpenAI；这里改为统一注入 DashScope/通义千问 的 llm。
- 三个 Agent 的角色、目标、工具和职责与原示例保持一致。
"""

from crewai import Agent

from llm_config import get_llm
from tools.browser_tools import BrowserTools
from tools.calculator_tools import CalculatorTools
from tools.search_tools import SearchTools


class TripAgents:

    def city_selection_agent(self):
        """城市选择专家：根据天气、季节、价格选出最合适的城市。"""
        return Agent(
            role="城市选择专家",
            goal="根据天气、季节和价格，选出最合适的目的地城市",
            backstory="擅长分析旅行数据，为旅行者挑选最理想的目的地。",
            llm=get_llm(),
            tools=[
                SearchTools.search_internet,
                BrowserTools.scrape_and_summarize_website,
            ],
            verbose=True,
        )

    def local_expert(self):
        """当地专家：提供所选城市最地道、深入的玩法建议。"""
        return Agent(
            role="当地城市专家",
            goal="就所选城市给出最精彩、最实用的深度建议",
            backstory="知识渊博的当地向导，对城市的景点、美食和风土人情了如指掌。",
            llm=get_llm(),
            tools=[
                SearchTools.search_internet,
                BrowserTools.scrape_and_summarize_website,
            ],
            verbose=True,
        )

    def travel_concierge(self):
        """旅行管家：产出完整的逐日行程、行李建议与预算明细。"""
        return Agent(
            role="金牌旅行管家",
            goal="为该城市设计最精彩的旅行行程，并给出预算和行李建议",
            backstory="拥有数十年经验，精通旅行规划与出行后勤保障。",
            llm=get_llm(),
            tools=[
                SearchTools.search_internet,
                BrowserTools.scrape_and_summarize_website,
                CalculatorTools.calculate,
            ],
            verbose=True,
        )
