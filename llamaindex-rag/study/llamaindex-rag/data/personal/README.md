# Personal RAG 数据目录

把自己的资料直接放到这个目录即可。

支持本课程优先使用的格式：

- `.txt`
- `.md`
- `.pdf`

`projects/personal_rag/app.py` 使用 `recursive=True`，因此可以建立子目录。

当前项目每次启动都会重新读取、切块和生成 Embedding。持久化、Chroma、增量更新属于后续真实项目阶段。
