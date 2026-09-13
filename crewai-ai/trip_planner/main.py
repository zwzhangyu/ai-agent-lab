"""行程规划 Crew 的入口。

运行方式（务必在 trip_planner 目录下运行，保证 `from tools...` 能导入）：
    cd crewai-ai/trip_planner

方式一（交互式，需真实终端，不要用 conda run）：
    python main.py

方式二（命令行传参，适合 conda run / 脚本 / 无法交互的场景）：
    python main.py --origin 北京 --cities "东京,大阪" \\
        --date-range "10.1-10.7" --interests 美食,购物

对照原示例（main.py）：整体流程一致，额外把结果保存成 Markdown 文件，
方便查看。
"""

import argparse

from crewai import Crew

from trip_agents import TripAgents
from trip_tasks import TripTasks


class TripCrew:

    def __init__(self, origin, cities, date_range, interests):
        self.cities = cities
        self.origin = origin
        self.interests = interests
        self.date_range = date_range

    def run(self):
        agents = TripAgents()
        tasks = TripTasks()

        city_selector_agent = agents.city_selection_agent()
        local_expert_agent = agents.local_expert()
        travel_concierge_agent = agents.travel_concierge()

        identify_task = tasks.identify_task(
            city_selector_agent,
            self.origin,
            self.cities,
            self.interests,
            self.date_range,
        )
        gather_task = tasks.gather_task(
            local_expert_agent,
            self.origin,
            self.interests,
            self.date_range,
        )
        plan_task = tasks.plan_task(
            travel_concierge_agent,
            self.origin,
            self.interests,
            self.date_range,
        )

        crew = Crew(
            agents=[
                city_selector_agent,
                local_expert_agent,
                travel_concierge_agent,
            ],
            tasks=[identify_task, gather_task, plan_task],
            verbose=True,
        )

        result = crew.kickoff()
        return result


def _ask(prompt, value=None):
    """命令行已传参就直接用；否则回退到交互式输入。

    注意：`conda run python main.py` 不会把键盘输入(stdin)转发给脚本，
    此时 input() 会抛 EOFError。要么用命令行参数跑，要么先
    `conda activate LangChainCode` 再用 `python main.py` 交互运行。
    """
    if value:
        return value
    try:
        return input(prompt)
    except EOFError:
        raise SystemExit(
            "\n[错误] 读取键盘输入失败（EOF）。\n"
            "原因：conda run 不转发 stdin。请改用命令行参数，例如：\n"
            '  python main.py --origin 北京 --cities "东京,大阪" \\\n'
            '      --date-range "10.1-10.7" --interests 美食,购物\n'
            "或先 `conda activate LangChainCode` 再运行 `python main.py`。"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="旅行规划 Crew（Trip Planner Crew）")
    parser.add_argument("--origin", help="出发城市，例如：北京")
    parser.add_argument("--cities", help="候选目的地，多个用逗号分隔，例如：东京,大阪")
    parser.add_argument("--date-range", dest="date_range", help="出行日期范围，例如：10.1-10.7")
    parser.add_argument("--interests", help="兴趣爱好，例如：美食,历史,自然")
    args = parser.parse_args()

    print("## 欢迎使用旅行规划 Crew")
    print("-------------------------------")
    location = _ask("你将从哪里出发？", args.origin)
    cities = _ask("你有兴趣访问哪些候选城市？（多个城市用逗号分隔）", args.cities)
    date_range = _ask("你计划出行的日期范围是？", args.date_range)
    interests = _ask("你有哪些主要的兴趣爱好？（例如：美食、历史、自然徒步）", args.interests)

    trip_crew = TripCrew(location, cities, date_range, interests)
    result = trip_crew.run()

    print("\n\n########################")
    print("## 这是为你定制的旅行计划")
    print("########################\n")
    print(result)

    with open("trip_plan.md", "w", encoding="utf-8") as f:
        f.write(str(result))
    print("\n✅ 行程已保存到 trip_plan.md")
