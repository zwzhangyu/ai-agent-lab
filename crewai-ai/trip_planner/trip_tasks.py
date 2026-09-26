"""行程规划团队中所有 Task 的定义。

对照原示例（trip_tasks.py）：三个任务分别交给三个 Agent。
在 Process.sequential（默认顺序执行）下，前一个任务的产出会自动
作为上下文传给后一个任务，因此无需手动写 context。
"""

from textwrap import dedent

from crewai import Task


class TripTasks:

    def identify_task(self, agent, origin, cities, interests, range):
        """从候选城市中选最佳目的地。"""
        return Task(
            description=dedent(f"""
                分析并从候选城市中，为本次旅行选出最合适的城市，
                需要综合考虑天气模式、季节性活动、旅行成本等因素。
                你要对比多个城市，权衡当前天气、即将举办的文化或季节性活动，
                以及整体旅行开销。

                你的最终答案必须是一份关于所选城市的详细报告，
                包含你查到的所有信息：真实的机票价格、天气预报和景点。
                {self.__tip_section()}

                出发地: {origin}
                候选城市: {cities}
                旅行日期: {range}
                旅行者兴趣: {interests}
            """),
            agent=agent,
            expected_output="关于所选城市的详细报告，包含机票价格、天气预报和景点信息",
        )

    def gather_task(self, agent, origin, interests, range):
        """深入研究这个城市。"""
        return Task(
            description=dedent(f"""
                作为这座城市的当地专家，你要为想要拥有完美旅程的旅行者
                整理一份深度攻略。收集关键景点、当地风俗、特色活动和
                每日玩法建议，找出只有本地人才知道的宝藏去处。
                攻略要全面覆盖城市的精华：小众秘境、文化热点、必去地标、
                天气预报和大致花费。

                最终答案必须是一份内容详实的城市指南，兼具文化洞察与实用贴士。
                {self.__tip_section()}

                旅行日期: {range}
                出发地: {origin}
                旅行者兴趣: {interests}
            """),
            agent=agent,
            expected_output="全面的城市指南，包含小众秘境、文化热点和实用旅行贴士",
        )

    def plan_task(self, agent, origin, interests, range):
        """产出完整的 7 日行程与预算。"""
        return Task(
            description=dedent(f"""
                把上面的城市指南扩展成一份完整的 7 天旅行行程，
                包含逐日安排、天气预报、餐饮推荐、行李清单和预算明细。

                你必须给出真实可去的景点、真实可住的酒店和真实可吃的餐厅。
                行程要覆盖从抵达至返程的方方面面，把城市指南的信息
                与实用的出行 logistics 结合起来。

                最终答案必须是一份完整的行程计划，用 Markdown 排版，
                包含每日安排、天气情况、穿衣与打包建议，以及详细预算。
                每个推荐地点都要说明为什么选它、它特别在哪里！
                {self.__tip_section()}

                旅行日期: {range}
                出发地: {origin}
                旅行者兴趣: {interests}
            """),
            agent=agent,
            expected_output="完整的行程计划，含每日安排、天气、打包建议和预算明细",
        )

    def __tip_section(self):
        return "如果你做到最好，我会给你 100 美元小费！"
