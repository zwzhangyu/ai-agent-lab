# 用 LlamaIndex 搭个人知识库问答应用实战笔记

这个仓库里有个我做的个人知识库问答应用：把 PDF、Word、Markdown 这些资料传进去，之后直接用自然语言提问，回答下面附引用来源，点开能看到命中的原文片段、匹配度，PDF 还会标出页码。

做的动机很具体：资料散在几十个文件里，关键词搜索经常找不到想找的那段，翻到了还得自己核对出处。我想要的就是"问一句，答案和出处一起给"。

技术栈四句话：界面 Streamlit，索引和检索 LlamaIndex，模型通义千问（DashScope），向量库 Chroma 存在项目本地。这篇按实现拆开讲：功能、配置、索引管线、问答编排、界面细节，以及过程中踩到的坑。代码和参数都取自项目现状，涉及运行输出的地方以实际输出为准。

## 一、能做什么

界面是三栏：左侧导航和最近对话，中间对话流，右侧知识库概览和参数面板。左侧导航有四个视图：对话、知识库、文件管理、模型设置。

目前这些可用：

- 上传 PDF / DOCX / PPTX / XLSX / CSV / TXT / MD，三条上传路径：侧边栏"上传文件"弹窗、文件管理页批量上传、对话输入框的附件按钮（附件随问题一起发，先入库再回答）
- 所有提问都走知识库检索，回答下方"引用来源"里能看到文件名、匹配度、页码或工作表名、片段预览
- 消息操作：复制、点赞 / 点踩、重新生成
- 深度思考开关：开启后走模型原生思考，回答上方可展开完整思考过程
- 联网搜索开关（Tavily）：网页结果与知识库片段一起进上下文，来源里标"联网"
- 模型切换：底部输入区可切 qwen3.7-max / qwen-max / qwen-plus / qwen-turbo
- 多会话：新建、切换、按首次提问自动命名、重命名
- 参数可调：Top-K、相似度阈值、chunk_size / chunk_overlap（切块参数重建索引后生效）
- 文件管理：列表、下载、删除、手动重建索引

一次提问的完整链路：

```text
文件
 │  SimpleDirectoryReader 解析
 ▼
Document
 │  SentenceSplitter 切块
 ▼
Node ──▶ text-embedding-v4 嵌入 ──▶ Chroma（本地持久化）
                                      ▲
                                      │ VectorIndexRetriever · Top-K
                                      │
提问 ──▶ 命中片段 ──▶ 阈值过滤 ──▶ 拼上下文 ◀── Tavily 联网结果（可选，转 TextNode）
                                      │
                                      ▼
                                qwen3.7-max 生成
                                      │
                                      ▼
                               回答 + 引用来源
```

## 二、目录结构

```text
rag-knowledge-chat/
├── streamlit_app.py              # 入口：页面配置、全局样式、视图分发
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml               # 主题：品牌蓝 #2563EB、大圆角
├── app/
│   ├── config.py                 # 路径、模型名、批大小、支持格式
│   ├── models.py                 # AppSettings：检索与回答设置
│   ├── state.py                  # 多会话状态（st.session_state）
│   ├── services/
│   │   ├── document_service.py   # 上传保存、文件清单、解析
│   │   ├── index_service.py      # 模型配置 + 索引加载 / 重建
│   │   ├── chat_service.py       # 检索 → 联网 → 生成
│   │   └── web_search.py         # Tavily 联网搜索
│   ├── components/
│   │   ├── sidebar.py            # 左侧导航 + 上传弹窗 + 最近对话
│   │   ├── chat_view.py          # 对话主视图 + 底部输入区
│   │   ├── right_panel.py        # 右侧知识库 / 模型面板
│   │   ├── manage_views.py       # 知识库 / 文件管理 / 模型设置
│   │   └── common.py             # 跨视图复用组件
│   └── utils/
│       └── formatting.py         # 图标、字节、相对时间
├── data/
│   └── uploads/                  # 上传的原始文件
└── storage/
    ├── chroma/                   # 向量索引
    └── meta/                     # files.json 文件清单
```

分层很直白：入口只管分发，services 干脏活，components 管渲染，互相不交叉。

## 三、环境与模型配置

### 3.1 依赖

Python 用 3.12。依赖都在 requirements.txt：

```text
streamlit>=1.39.0
python-dotenv>=1.0.1
requests>=2.31.0

llama-index-core==0.14.25
llama-index-llms-dashscope>=0.6.1
llama-index-embeddings-dashscope>=0.6.0
llama-index-vector-stores-chroma>=0.6.0
llama-index-readers-file>=0.5.0

chromadb>=1.0.0
pypdf>=5.0.0
python-docx>=1.1.2
python-pptx>=1.0.2
openpyxl>=3.1.5
pandas>=2.2.0
```

llama-index-core 锁了 0.14.25。后面 pypdf、python-docx、python-pptx、openpyxl 这几个解析依赖（加 pandas 读表格）是给 SimpleDirectoryReader 按扩展名分派解析器用的，少一个对应格式就报错。

### 3.2 .env 配置项

```env
DASHSCOPE_API_KEY=
LLM_MODEL=qwen3.7-max
EMBED_MODEL=text-embedding-v4
APP_TITLE=HomeRag
APP_SUBTITLE=你的个人知识库助手
# 可选：联网搜索，不配则开关置灰
TAVILY_API_KEY=
```

读取集中在 app/config.py，全部走 `os.getenv` 带默认值：

```python
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env", override=False)

APP_TITLE = os.getenv("APP_TITLE", "HomeRag")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.7-max")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-v4")
```

这种写法 .env 缺项也能跑起来。路径全部基于 `__file__` 定位，从哪个目录启动都不影响数据目录的位置。

### 3.3 两个必须显式传的模型参数

第一个是 api_key。DashScope 的 LLM 类不会自动读 `DASHSCOPE_API_KEY` 环境变量，不传就抛 pydantic 的 ValidationError，报错里只有一个 api_key 为 None 的字段，第一次遇到得反应一会儿才能定位到环境变量这层。处理方式就是显式取出来显式传：

```python
def _require_api_key() -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("未找到 DASHSCOPE_API_KEY，请在本目录 .env 中配置。")
    return api_key

Settings.llm = DashScope(model_name=LLM_MODEL, api_key=api_key)
```

第二个是 embedding 批大小。`DashScopeEmbedding` 的默认 `embed_batch_size` 是 25，这个数字对应 text-embedding-v1/v2 的限制；换成 text-embedding-v4 后单次请求最多 10 条，超出直接 400：`batch size should not be larger than 10`。这个错误出现在 dashscope 的 logger.error 里，堆栈上看不出原因，我第一次碰上时排查了一阵。解法：

```python
# text-embedding-v3/v4 单次请求最多 10 条文本，必须显式调小
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "10"))

Settings.embed_model = DashScopeEmbedding(
    model_name=EMBED_MODEL,
    api_key=api_key,
    embed_batch_size=EMBED_BATCH_SIZE,
)
```

实测 12 条文本按 10 + 2 两批走完，返回 1024 维向量（以实际输出为准）。这类第三方适配层的默认值，换模型版本时要翻一眼源码里的常量，别只盯着异常堆栈看。

## 四、索引管线：从文件到向量

### 4.1 上传与文件清单

三个上传入口都汇到同一个函数：文件落到 `data/uploads/`，同时在 `storage/meta/files.json` 登记一条（名称、路径、大小）。校验扩展名，不在支持列表里的直接跳过。

```python
def save_uploaded_files(uploaded_files: Iterable) -> list[Path]:
    saved = []
    manifest = _load_manifest()

    for uploaded in uploaded_files:
        suffix = Path(uploaded.name).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        target = UPLOAD_DIR / Path(uploaded.name).name
        target.write_bytes(uploaded.getbuffer())

        manifest[target.name] = {
            "path": str(target),
            "size": target.stat().st_size,
        }
        saved.append(target)

    _save_manifest(manifest)
    return saved
```

用清单而不是直接扫目录，是为了让"文件管理"里的删除、列表、下载有统一的依据，也方便后面做多知识库时按清单分桶。

### 4.2 解析与切块

解析用 `SimpleDirectoryReader`，把清单里的文件一次性读成 Document 列表，解析器按扩展名自动分派：

```python
def load_documents():
    files = [Path(item["path"]) for item in list_files()]
    if not files:
        return []

    return SimpleDirectoryReader(
        input_files=[str(path) for path in files],
    ).load_data()
```

切块用 `SentenceSplitter`，默认 `chunk_size=512`、`chunk_overlap=50`，两个参数在界面"高级切块参数"里可调（128–2048 / 0–300），改完重建索引生效：

```python
splitter = SentenceSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
)

nodes = splitter.get_nodes_from_documents(documents)
```

### 4.3 写入 Chroma 与重建

向量库使用 `chromadb.PersistentClient`，指向项目内的 `storage/chroma`；集合名叫 `rag_knowledge_chat`。重建的逻辑是先把旧集合整个删掉再建新集合，然后解析、切块、嵌入一路写进去：

```python
client = get_client()
try:
    client.delete_collection(COLLECTION_NAME)
except Exception:
    pass

collection = client.get_or_create_collection(COLLECTION_NAME)
vector_store = ChromaVectorStore(chroma_collection=collection)

documents = load_documents()
nodes = SentenceSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
).get_nodes_from_documents(documents)

VectorStoreIndex(
    nodes,
    storage_context=StorageContext.from_defaults(vector_store=vector_store),
)
```

完成后界面上会 toast 一条"索引重建完成：2 份文档 / 14 个片段"这样的汇总（数字以实际输出为准）。另外每次重建会在 `storage/chroma/` 下多留一个 UUID 命名的段目录，这是 Chroma 的内部机制，不影响使用，想清理就把应用停掉、删掉旧目录再重新建一次索引。

### 4.4 加载索引

提问时走的不是这条重建路径，而是直接从已有向量库挂载：

```python
vector_store = ChromaVectorStore(chroma_collection=get_collection())

return VectorStoreIndex.from_vector_store(
    vector_store=vector_store,
)
```

不重新解析、不重新嵌入，所以提问是秒级响应。一个推论：换 LLM 不影响索引，随便切；换 embedding 模型必须重建索引，不然新旧向量不在一个语义空间里。界面上嵌入模型做成只读，锁死 text-embedding-v4，就是为了不给自己留这个坑。

## 五、问答编排：检索、思考与联网

### 5.1 检索与相似度过滤

检索按当前设置取 Top-K，默认 3，界面可调 1–10。取完之后做一步手动过滤：

```python
retriever = index.as_retriever(similarity_top_k=settings.top_k)
nodes = retriever.retrieve(question)

# 该版本的 VectorIndexRetriever 不识别 similarity_cutoff，手动过滤。
cutoff = settings.similarity_cutoff
if cutoff and cutoff > 0:
    nodes = [node for node in nodes if node.score is None or node.score >= cutoff]
```

手动过滤的原因：这个版本的 `VectorIndexRetriever` 静默忽略 `similarity_cutoff` 参数，传了不报错也不生效。阈值默认 0.3，是按我实测的分数分布定的：命中片段大多在 0.5 上下，0.3 能滤掉完全不相关的，又不会把勉强相关的全砍掉（以实际输出为准）。

### 5.2 提示词

回答质量的大头在这一段。全文照抄项目的 QA_TEMPLATE：

```text
你是一个严谨的知识库问答助手。

请只依据下面提供的【参考资料】回答问题，资料可能来自本地知识库或联网搜索。

规则：
1. 不要把模型自身记忆当成知识库事实，不要虚构来源。
2. 如果资料不足以支持答案，请明确回答：
   "当前知识库中没有足够信息回答这个问题。"
3. 如果可以回答，先给出直接结论，再分点补充关键细节，保持清晰、简洁。
4. 回答中的关键信息都应能在参考资料中找到依据。

---------------------
参考资料：
{context_str}
---------------------

用户问题：
{query_str}

回答：
```

两个点是有意为之：规则 1 压住模型拿自己记忆凑答案的倾向；规则 2 给一个固定话术，资料不够时直接说没有，而不是硬编。检索一个片段都没命中时，代码里也是直接返回这句固定话术，不调模型，省一次请求。

### 5.3 深度思考

"深度思考"开关对应的是模型原生思考，不开独立提示词。调用时透传 DashScope 的 `enable_thinking` 参数：

```python
try:
    response = llm.complete(prompt, enable_thinking=settings.deep_thinking)
except Exception as exc:
    # 当前模型不支持该参数时自动降级为默认调用。
    if "enable_thinking" not in str(exc):
        raise
    response = llm.complete(prompt)
```

这里有个容易搞反的点：qwen3.7-max 默认就是开启思考的，不传参数它也会返回思考过程；要真正关掉，必须显式传 `enable_thinking=False`，"开启时传参、关闭时不传"的做法是无效的。实测同一个问题，关掉 3.8 秒返回、开启 14 秒左右带完整思考（以实际输出为准），所以把它做成开关，默认关。

思考过程从原始响应里取：

```python
def _extract_thinking(response) -> str | None:
    message = response.raw["output"]["choices"][0]["message"]
    return message.get("reasoning_content") or None
```

拿到之后放在回答上方的"深度思考过程"折叠区里，不占正文。界面步骤条也会跟着变：开启时显示"深度思考并生成回答"，关闭时就是"生成回答"。

### 5.4 联网搜索

联网走 Tavily，一次取 4 条：

```python
response = requests.post(
    TAVILY_ENDPOINT,
    json={"api_key": api_key, "query": query, "max_results": 4},
    timeout=30,
)
```

搜索结果的标题、链接、摘要包装成 `TextNode`，和知识库片段共用同一套引用和提示词管道：

```python
node = TextNode(
    text="[联网搜索结果] " + item.get("content", ""),
    metadata={
        "file_name": item.get("title") or "网页结果",
        "url": item.get("url"),
        "source_type": "web",
    },
)
```

文本前缀让模型能区分资料来源，metadata 里的 `source_type` 让引用区渲染成"联网"徽标加可点链接，而不是匹配度。网页结果没有向量分数，`NodeWithScore` 的 score 传 None。没配 `TAVILY_API_KEY` 时开关是置灰的，不会误开。

## 六、界面上的几个实现细节

### 6.1 输入区固定在底部

`st.chat_input` 只有放在主区域顶层时才会自动吸底，放进 `st.columns` 或 `st.container` 就退化成行内输入框，跟着内容走。所以底部输入区用 `st.bottom` 容器，内部再按和主布局同比例的列划分，让输入框对齐中间的对话列：

```python
with st.bottom:
    composer_col, _ = st.columns([2.6, 1], gap="medium")

    with composer_col:
        deep_col, web_col, _, model_col = st.columns(
            [2.2, 2.2, 2.2, 3.4], vertical_alignment="center"
        )
        # 深度思考开关、联网开关、模型选择……

        submission = st.chat_input(
            "输入你的问题，按 Enter 发送，Shift + Enter 换行",
            accept_file="multiple",
            file_type=UPLOAD_FILE_TYPES,
        )
```

输入框带附件按钮（`accept_file="multiple"`），传的文件先落盘，再和问题一起处理。

### 6.2 提交后先重跑

固定底部的输入区提交后不能就地渲染消息，否则内容会被渲染进底部容器里，位置和顺序全乱。做法是提交时只写状态、不渲染，然后立即 `st.rerun()`：

```python
if text:
    add_message(conv, "user", text, attachments=attachment_names)
    if attachment_names:
        st.session_state.pending_ingest = attachment_names
    st.session_state.pending_question = text
...
st.rerun()
```

重跑的下一轮里，`render_chat_view` 按固定顺序处理：先渲染消息流（新用户消息此时自然出现在正确位置），然后处理 `pending_ingest` 把附件入库并重建索引，再处理 `pending_question` 生成回答。整个问答过程用分步的 `st.status` 展示：检索知识库（命中 N 个相关片段）→ 联网搜索（可选）→ 生成回答，完成后自动折叠。

### 6.3 引用来源的展示

这块踩过一个坑：片段原文里的 `###`、`#` 这些 Markdown 标题记号，`st.caption` 也会按完整 Markdown 渲染，预览区直接变成几个巨型标题。修法是两步清洗加一步转义：

```python
_MARKDOWN_SPECIALS = re.compile(r"([\\`*_{}\[\]<>#+\-.!|~$])")

def _plain_text(text: str) -> str:
    """转义 Markdown 特殊字符，避免片段被当作标题、列表等渲染。"""
    return _MARKDOWN_SPECIALS.sub(r"\\\1", text)

def _clean_snippet(text: str) -> str:
    """去掉行首的 Markdown 标题记号并压平空白，便于单行展示。"""
    text = re.sub(r"(?m)^\s*#{1,6}\s*", "", text)
    return " ".join(text.split())
```

最终每条来源渲染成两行小号灰字：第一行是图标、文件名、匹配度徽标（或"联网"徽标加链接）、页码 / 工作表名；第二行是压平后的片段预览，`st.caption(wrap=False)` 单行省略，太长的内容悬停原生 tooltip 看全文。同一条回答里只有最新的那一条默认展开引用来源，往上的历史消息折叠着。

### 6.4 用户消息右对齐

聊天界面里用户消息默认靠左，和助手消息一个方向。整个应用唯一一处 CSS 覆盖用在这：借助 `:has()` 选中带用户头像的消息行，把 flex 方向反过来，内容靠右：

```css
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    width: fit-content;
    margin-left: auto;
}
```

现代 Chrome / Edge 内核都支持 `:has()`。除此之外整个界面全是原生组件，配色交给 `.streamlit/config.toml`：品牌蓝 `#2563EB`、大圆角、浅色底。

## 七、状态与存储：存在哪、什么会丢

### 7.1 数据都在哪

```text
data/uploads/                    上传的原始文件
storage/meta/files.json          文件清单（名称、路径、大小）
storage/chroma/chroma.sqlite3    向量索引（chunk 文本 + 向量 + 元数据）
```

对话历史不进磁盘，放在 `st.session_state` 里，结构是一张会话表加一个活跃指针：

```python
st.session_state.conversations = {
    "<10 位会话 id>": {
        "title": ..., "messages": [...],
        "created_at": ..., "updated_at": ...,
    },
}
st.session_state.active_conversation_id = "<会话 id>"
```

会话标题在第一条用户消息进来时自动生成，取前 18 个字符，超长补省略号；"最近对话"列表按 `updated_at` 倒序。

### 7.2 重启后什么留下

留下：上传的文件、文件清单、向量索引。索引是 `PersistentClient` 写在项目内的，跟进程的工作目录无关，服务重启后新进程直接就能检索，不用重建。我实测的方式是全新 Python 进程连上同一个目录，查集合拿到的 chunk 数和界面上显示的一致，检索问题能正常命中（以实际输出为准）。

丢：对话历史。刷新页面或者重启服务，之前的会话就没了。当前版本就是这样，接受这个设定：聊天记录当临时产物用，知识库本身是持久的。

### 7.3 删掉文件后要重建索引

删除源文件只动两处：`data/uploads/` 里的文件和 `files.json` 里的登记，向量库不动。我实测过一次这个不一致：从文件管理里把文件删完，`files.json` 已经清空，直接查 Chroma 还能数出 14 个残留片段（以实际输出为准）。也就是说删掉的文件仍可能被检索到、出现在引用来源里。

对齐的方式是删完去"知识库"页点一下"重建索引"。删除操作的 toast 里也带了这句提示，但确实容易忽略，记着这个行为就行。

## 八、跑起来

### 8.1 安装与配置

```bash
cd llamaindex-rag/study/rag-knowledge-chat

# 虚拟环境或 conda 环境都行，Python 3.12
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env，至少填上 DASHSCOPE_API_KEY
```

### 8.2 启动与使用

```bash
streamlit run streamlit_app.py
```

默认开在 8501 端口。使用流程：

1. 左侧"上传文件"（或文件管理页、对话附件），默认上传后自动重建索引
2. 对话里提问，空会话时也可以先点推荐问题
3. 展开回答下方的"引用来源"核对命中片段和匹配度
4. 需要深入分析开"深度思考"，需要实时信息开"联网搜索"
5. 底部随时切模型，右侧面板调 Top-K 和相似度阈值

## 九、限制与下一步

- Reranker：检索结果质量还能再上一档
- Metadata filter：按文件、类型过滤检索范围
- 多知识库：现在所有文件进同一个 collection
- OCR：pypdf 走的是文本层，扫描版 PDF 解析不出文字
- 会话持久化：把 conversations 结构写一份到 `storage/meta/conversations.json`
- 增量索引：现在重建是全量，文件多了之后解析和嵌入都要重来
- Agent / Tool Calling：问答之外的动作型需求

---

想读代码的话，先看 `app/services/index_service.py` 和 `app/services/chat_service.py`，一个负责索引，一个负责问答编排，这两个文件读通，剩下的都是界面。

- 仓库地址：<https://github.com/zwzhangyu/ai-agent-lab>
- 项目目录：`llamaindex-rag/study/rag-knowledge-chat`
