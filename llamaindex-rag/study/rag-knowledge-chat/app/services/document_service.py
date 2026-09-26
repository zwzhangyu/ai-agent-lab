"""文档服务：管理上传文件的保存/删除，以及 files.json 元数据清单。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from llama_index.core import SimpleDirectoryReader

from app.config import UPLOAD_DIR, META_DIR, SUPPORTED_EXTENSIONS


MANIFEST_PATH = META_DIR / "files.json"


def _load_manifest() -> dict:
    """读取 files.json 清单；文件不存在或损坏时返回空字典。"""
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_manifest(data: dict) -> None:
    """把文件清单写回磁盘。"""
    MANIFEST_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_uploaded_files(uploaded_files: Iterable) -> list[Path]:
    """保存上传文件到数据目录并登记清单，返回实际落盘的路径列表。"""
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


def list_files() -> list[dict]:
    """列出清单中仍实际存在的文件（含大小与修改时间）。"""
    manifest = _load_manifest()
    result = []

    for name, info in manifest.items():
        path = Path(info["path"])
        if path.exists():
            stat = path.stat()
            result.append({
                "name": name,
                "path": str(path),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            })

    return sorted(result, key=lambda x: x["name"].lower())


def delete_file(name: str) -> None:
    """从磁盘与清单中删除指定文件。"""
    manifest = _load_manifest()
    item = manifest.pop(name, None)

    if item:
        path = Path(item["path"])
        if path.exists():
            path.unlink()

    _save_manifest(manifest)


def load_documents():
    """把全部已上传文件加载为 LlamaIndex Document 列表。"""
    files = [Path(item["path"]) for item in list_files()]
    if not files:
        return []

    return SimpleDirectoryReader(
        input_files=[str(path) for path in files],
    ).load_data()
