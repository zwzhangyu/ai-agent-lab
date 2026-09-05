import os
import time
import config
import dashscope

dashscope.base_http_api_url = "https://llm-prfefnpw1j843yt8.cn-beijing.maas.aliyuncs.com/api/v1"
api_key = os.getenv('DASHSCOPE_API_KEY')
model = "qwen-max"


def call_api(messages, **kwargs):
    response = dashscope.Generation.call(
        api_key=api_key,
        model=model,
        messages=messages,
        **kwargs,
    )
    return response


# ========== 测试数据集：20 条中文评论（正面/负面/中性） ==========
# 包含反讽、混合情感、口语化等边界案例，增加区分难度
test_data = [
    # (评论文本, 真实标签)
    # --- 简单案例 ---
    ("这部电影太好看了，剧情紧凑，演员演技在线！", "正面"),
    ("浪费了两个半小时，剧情拖沓，毫无逻辑。", "负面"),
    ("电影一般般，不好不坏吧，打发时间可以看看。", "中性"),
    # --- 反讽/隐含负面 ---
    ("真是'好看'啊，好看到我在电影院睡着了。", "负面"),
    ("导演真是个人才，能把这么好的IP拍成这个样子。", "负面"),
    ("这电影太好了，好到我再也不会去看了。", "负面"),
    # --- 混合情感（整体偏某一方） ---
    ("特效不错，但剧情实在拉胯，可惜了。", "负面"),
    ("虽然节奏有点慢，但结尾的反转太精彩了。", "正面"),
    ("演员很努力，可惜剧本不行。", "负面"),
    ("画面很美，故事嘛……算了不说了。", "负面"),
    # --- 口语化/网络用语 ---
    ("笑死我了，这剧情是认真的吗？", "负面"),
    ("绝绝子！看完直接封神！", "正面"),
    ("就……挺无语的，不推荐。", "负面"),
    ("还行，能看，但也没吹的那么好。", "中性"),
    # --- 边界模糊案例 ---
    ("看完心情很复杂，说不上喜欢但也讨厌不起来。", "中性"),
    ("爆米花电影吧，带小孩看看还行。", "中性"),
    ("前半段昏昏欲睡，后半段居然看进去了，整体还行。", "中性"),
    ("本来以为是烂片，没想到居然超出预期！", "正面"),
    ("口碑两极分化的片子，我个人觉得被高估了。", "负面"),
    ("二刷了，越看越觉得细节很多，好片！", "正面"),
]


def extract_label(text: str) -> str:
    """从模型输出中提取分类标签"""
    text = text.strip()
    for label in ["正面", "负面", "中性"]:
        if label in text:
            return label
    return "未知"


# ========== Zero-Shot 分类 ==========
def classify_zero_shot(review: str) -> str:
    messages = [
        {"role": "system", "content": "你是一个电影评论情感分类器。请将以下评论分类为：正面、负面 或 中性。只回复分类结果，不要解释。"},
        {"role": "user", "content": f"请对以下电影评论进行情感分类：\n\n「{review}」\n\n分类（正面/负面/中性）："}
    ]
    resp = call_api(messages, temperature=0)
    if resp.status_code == 200 and resp.output:
        return extract_label(resp.output.text)
    return "未知"


# ========== 3-Shot 分类 ==========
# 示例选取策略：包含一条混合情感的边界案例，帮助模型理解分类标准
def classify_3_shot(review: str) -> str:
    examples = """评论：「本来以为是烂片，没想到居然超出预期！」
分类：正面

评论：「特效不错，但剧情实在拉胯，可惜了。」
分类：负面

评论：「前半段昏昏欲睡，后半段居然看进去了，整体还行。」
分类：中性"""

    messages = [
        {"role": "system", "content": "你是一个电影评论情感分类器。请参考示例，将以下评论分类为：正面、负面 或 中性。只回复分类结果，不要解释。"},
        {"role": "user", "content": f"以下是几个分类示例：\n\n{examples}\n\n现在请分类：\n\n评论：「{review}」\n分类："}
    ]
    resp = call_api(messages, temperature=0)
    if resp.status_code == 200 and resp.output:
        return extract_label(resp.output.text)
    return "未知"


# ========== 运行实验 ==========
def run_experiment(classify_fn, label: str):
    correct = 0
    total = len(test_data)
    results = []

    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")
    print(f"{'序号':<4} {'评论':<30} {'真实':<4} {'预测':<4} {'结果'}")
    print(f"{'-' * 60}")

    for i, (review, true_label) in enumerate(test_data):
        pred_label = classify_fn(review)
        is_correct = pred_label == true_label
        if is_correct:
            correct += 1
        status = "✓" if is_correct else "✗"
        # 截断评论显示
        display_review = review[:26] + "..." if len(review) > 28 else review
        print(f"{i+1:<4} {display_review:<30} {true_label:<4} {pred_label:<4} {status}")
        results.append(is_correct)
        time.sleep(0.3)  # 避免请求过快

    accuracy = correct / total
    print(f"\n  正确: {correct}/{total}  准确率: {accuracy:.1%}")
    return accuracy


if __name__ == "__main__":
    print("Few-Shot vs Zero-Shot 情感分类对比实验")
    print(f"模型: {model}  数据集: {len(test_data)} 条中文电影评论")

    acc_zero = run_experiment(classify_zero_shot, "Zero-Shot（无示例）")
    acc_few = run_experiment(classify_3_shot, "3-Shot（3 个示例）")

    # ========== 汇总 ==========
    print(f"\n{'=' * 60}")
    print("  实验结果汇总")
    print(f"{'=' * 60}")
    print(f"  Zero-Shot 准确率: {acc_zero:.1%}")
    print(f"  3-Shot  准确率: {acc_few:.1%}")
    diff = acc_few - acc_zero
    sign = "+" if diff >= 0 else ""
    print(f"  提升幅度: {sign}{diff:.1%}")
    print()

    if diff > 0:
        print("结论: Few-Shot 提供了示例，帮助模型更准确地理解分类标准。")
    elif diff < 0:
        print("结论: 对于此任务，Zero-Shot 表现更好，可能因为任务本身足够简单。")
    else:
        print("结论: 两者表现一致，任务难度可能不足以体现 Few-Shot 的优势。")
