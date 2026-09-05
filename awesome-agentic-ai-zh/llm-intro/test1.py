import os
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


# ========== 实验 1: max_tokens=1 ==========
print("=" * 50)
print("实验 1: max_tokens=1")
print("=" * 50)
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': '请详细介绍一下你自己'}
]
resp = call_api(messages, max_tokens=1)
print(f"输出内容: {resp.output.text if resp.output else 'None'}")
print(f"Token 用量: {resp.usage}")
print(f"状态码: {resp.status_code}, 消息: {resp.message}")
print()


# ========== 实验 2: temperature=0 多次调用 ==========
print("=" * 50)
print("实验 2: temperature=0，连续调用 3 次")
print("=" * 50)
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': '1+1等于几？'}
]
for i in range(3):
    resp = call_api(messages, temperature=0)
    text = resp.output.text if resp.output else 'None'
    print(f"第 {i+1} 次: {text}")
print()


# ========== 实验 3: 中文 vs 英文 token 对比 ==========
print("=" * 50)
print("实验 3: 中文 vs 英文 token 数量对比")
print("=" * 50)

zh_messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': '请详细介绍人工智能的发展历史和未来趋势'}
]
en_messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': 'Please provide a detailed introduction to the history and future trends of artificial intelligence development'}
]

resp_zh = call_api(zh_messages, max_tokens=5)
resp_en = call_api(en_messages, max_tokens=5)

print(f"中文 prompt: {zh_messages[1]['content']}")
print(f"  输入 token: {resp_zh.usage.input_tokens}")
print()
print(f"English prompt: {en_messages[1]['content']}")
print(f"  输入 token: {resp_en.usage.input_tokens}")
print()
print(f"Token 比例 (中/英): {resp_zh.usage.input_tokens / resp_en.usage.input_tokens:.2f}")
