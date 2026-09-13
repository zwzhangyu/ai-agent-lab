"""博客创作团队的 Task 定义。

顺序执行下，research_task 的输出会作为上下文流入 write_task。
"""

from textwrap import dedent

from crewai import Task


class BlogTasks:
    """提供团队所需的各个任务。"""

    def research_task(self, agent, topic):
        """就指定主题做调研，产出带可运行代码的研究报告。"""
        return Task(
            description=dedent(f"""
                深入研究主题：{topic}。
                覆盖该主题的常见痛点、核心概念与最佳实践，
                并给出完整、可运行的代码示例佐证结论。
            """),
            agent=agent,
            expected_output="一份研究报告，包含问题分类、解决方案代码和完整落地流程。",
        )

    def write_task(self, agent, topic, title, context):
        """基于研究报告撰写入门级技术博客。"""
        return Task(
            description=dedent(f"""
                基于研究团队提供的报告，围绕主题「{topic}」撰写一篇入门级技术博客。
                文章标题：《{title}》。
                要求结构清晰、示例完整，适合初学者阅读。
            """),
            agent=agent,
            context=context,
            expected_output="不少于 800 字的 Markdown 技术博客。",
        )
