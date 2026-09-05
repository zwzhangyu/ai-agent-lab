# ReAct Agent from Scratch - 启动命令

## 前置准备

```bash
# 进入项目目录
cd awesome-agentic-ai-zh/react-agent-from-scratch

# 激活虚拟环境
source ../../../venv/bin/activate

# 安装依赖（首次运行）
pip install -r requirements.txt
```

## 启动命令

### Streamlit Web 界面

```bash
streamlit run web_app.py
```

### CLI 交互模式

```bash
python agent.py
```

## 测试查询示例

```
北京今天天气怎么样？
计算 123 * 456 + 789
搜索 Python 3.13 新特性
介绍一下量子计算
```
