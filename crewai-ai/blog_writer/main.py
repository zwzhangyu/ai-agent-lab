"""博客创作 Crew 的入口。

用法：
    python main.py                                          # 交互式，回车用默认主题
    python main.py --topic "Redis 持久化机制" \
        --title "Redis 持久化入门" --output redis_blog.md   # 命令行传参
"""

import argparse

from crewai import Crew, Process

from blog_agents import BlogAgents
from blog_tasks import BlogTasks

DEFAULT_TOPIC = (
    "使用 Python 进行自动化数据清洗"
    "（pandas、numpy、缺失值、重复值、格式不一致问题）"
)
DEFAULT_TITLE = "Python 数据清洗入门：用 pandas 告别脏数据"
DEFAULT_OUTPUT = "python_data_cleaning_blog.md"


class BlogCrew:
    """把 Agent 与 Task 组装成一个顺序执行的 Crew。"""

    def __init__(self, topic, title):
        self.topic = topic
        self.title = title

    def run(self):
        agents = BlogAgents()
        tasks = BlogTasks()

        researcher = agents.researcher()
        writer = agents.writer()

        research_task = tasks.research_task(researcher, self.topic)
        write_task = tasks.write_task(
            writer, self.topic, self.title, context=[research_task]
        )

        crew = Crew(
            agents=[researcher, writer],
            tasks=[research_task, write_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew.kickoff()


def _ask(prompt, value=None, default=None):
    """命令行参数优先，其次交互式输入，最后回退默认值。

    无 tty（如 conda run 不转发 stdin）时 input() 会抛 EOFError：
    有默认值就用默认值，否则给出明确提示后退出。
    """
    if value:
        return value
    try:
        answer = input(prompt).strip()
    except EOFError:
        if default is not None:
            return default
        raise SystemExit(
            "无法读取标准输入，请改用命令行参数，例如：\n"
            '  python main.py --topic "Redis 持久化机制" --title "Redis 持久化入门"'
        )
    return answer or default


def main():
    parser = argparse.ArgumentParser(description="技术博客创作 Crew")
    parser.add_argument("--topic", help="要研究并撰写的技术主题")
    parser.add_argument("--title", help="博客标题")
    parser.add_argument("--output", help="结果保存的 Markdown 文件名")
    args = parser.parse_args()

    topic = _ask("技术主题: ", args.topic, DEFAULT_TOPIC)
    title = _ask("博客标题: ", args.title, DEFAULT_TITLE)
    output_file = args.output or DEFAULT_OUTPUT

    result = BlogCrew(topic, title).run()
    print(result)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result.raw)
    print(f"博客已保存到 {output_file}")


if __name__ == "__main__":
    main()
