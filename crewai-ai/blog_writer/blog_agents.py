"""博客创作团队的 Agent 定义。"""

from crewai import Agent

from llm_config import get_llm


class BlogAgents:
    """提供团队所需的各个 Agent 实例。"""

    def researcher(self):
        """技术研究员：围绕主题做调研，并给出可运行的代码佐证。"""
        return Agent(
            role="技术研究员",
            goal="寻找最新、准确、可验证的技术资料，并给出代码证明。",
            backstory="擅长系统性分析技术问题，注重事实和可复现性。",
            llm=get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    def writer(self):
        """技术博客作家：把研究结果整理成面向初学者的文章。"""
        return Agent(
            role="技术博客作家",
            goal="将研究成果整理成适合初学者阅读的技术文章。",
            backstory="擅长将复杂概念拆解为清晰步骤，并提供完整示例。",
            llm=get_llm(),
            verbose=True,
            allow_delegation=True,
        )
