"""Flask 服务：把 trip_planner Crew 封装成 HTTP API，并托管前端 UI。

启动方式（务必先进入 trip_planner 目录，保证 `from tools...` 能导入）：
    cd crewai-ai/trip_planner
    python server.py                       # 默认 http://127.0.0.1:8000
    python server.py --host 0.0.0.0 --port 8080

端口选型：默认用 8000，而非 Flask 习惯的 5000。
    因为 macOS Monterey (12)+ 的 AirPlay Receiver 会占用 5000/7000，
    导致 Flask 启不起或返回 403（实际命中系统的 AirPlay 服务）。

主要接口：
    GET  /                        -> ui/index.html
    GET  /api/health              -> 健康检查（含密钥是否配置）
    POST /api/plan                -> 创建规划任务，立即返回 job_id
    GET  /api/plan/<job_id>       -> 前端轮询用：返回状态/步骤/最终结果
    GET  /api/plan/<job_id>/md    -> 直接下载最终的 Markdown

为什么用「异步 job + 轮询」而不是同步返回：
    CrewAI 三个 Agent 串行 + 多次联网/LLM 调用，单次执行通常 3~8 分钟。
    直接同步 HTTP 请求极易被浏览器或反向代理超时截断。这里在后台线程
    跑 Crew，用 `task_callback` 记录每个 Task 的完成情况，前端 2s 轮询
    一次即可看到实时进度。
"""

import argparse
import os
import threading
import time
import traceback
import uuid
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

# llm_config 在 import 时就会加载根目录 .env 并设置 NO_PROXY，
# 因此必须早于 trip_agents/tools 导入。
import llm_config  # noqa: F401  仅为触发 .env 加载
from main import TripCrew

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"
PLAN_FILE = BASE_DIR / "trip_plan.md"

STEP_NAMES = ["城市筛选", "深度攻略", "行程生成"]

app = Flask(__name__, static_folder=None)

# ------------------------- 内存任务存储 -------------------------
# 生产环境建议换成 Redis / DB，这里为教学示例保持简单。
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def _new_job() -> str:
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "pending",           # pending / running / done / error
            "current_step": 0,
            "steps": [
                {"name": name, "status": "pending", "output": None}
                for name in STEP_NAMES
            ],
            "result": None,
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
    return job_id


def _touch(job_id: str, **fields) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job.update(fields)
        job["updated_at"] = time.time()


def _snapshot(job_id: str) -> dict | None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return None
        # 深拷贝，避免前端读到一半被后台线程改坏
        return {
            **job,
            "steps": [dict(s) for s in job["steps"]],
        }


def _run_crew(job_id: str, origin: str, cities: str,
              date_range: str, interests: str) -> None:
    """后台线程：真正执行 Crew，并把进度写回 JOBS。"""
    completed = {"count": 0}

    def _on_task_done(output):
        idx = completed["count"]
        raw = getattr(output, "raw", None) or str(output)
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                if idx < len(job["steps"]):
                    job["steps"][idx]["status"] = "done"
                    # 只留前 4000 字，避免 JSON 响应过大
                    job["steps"][idx]["output"] = raw[:4000]
                    if idx + 1 < len(job["steps"]):
                        job["steps"][idx + 1]["status"] = "active"
                job["current_step"] = min(idx + 1, len(job["steps"]) - 1)
                job["updated_at"] = time.time()
        completed["count"] += 1

    try:
        _touch(job_id, status="running", current_step=0)
        with JOBS_LOCK:
            JOBS[job_id]["steps"][0]["status"] = "active"

        crew_wrapper = TripCrew(origin, cities, date_range, interests)
        result = crew_wrapper.run(task_callback=_on_task_done, verbose=True)
        result_text = str(result)

        # 同步落一份到磁盘，方便命令行查看
        try:
            PLAN_FILE.write_text(result_text, encoding="utf-8")
        except OSError:
            pass

        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                for step in job["steps"]:
                    step["status"] = "done"
                job["current_step"] = len(STEP_NAMES) - 1
                job["result"] = result_text
                job["status"] = "done"
                job["updated_at"] = time.time()

    except Exception as exc:  # noqa: BLE001  后台线程要兜住所有异常
        traceback.print_exc()
        _touch(job_id, status="error",
               error=f"{type(exc).__name__}: {exc}")


# ------------------------- HTTP 路由 -------------------------
@app.get("/")
def index():
    return send_from_directory(UI_DIR, "index.html")


@app.get("/ui/<path:filename>")
def ui_asset(filename):
    return send_from_directory(UI_DIR, filename)


@app.get("/api/health")
def health():
    return jsonify({
        "success": True,
        "service": "trip_planner",
        "model": os.getenv("CREWAI_MODEL", llm_config.DEFAULT_MODEL),
        "dashscope_key_configured": bool(os.getenv("DASHSCOPE_API_KEY")),
        "tavily_key_configured": bool(os.getenv("TAVILY_API_KEY")),
        "active_jobs": sum(1 for j in JOBS.values() if j["status"] == "running"),
    })


@app.post("/api/plan")
def create_plan():
    data = request.get_json(force=True, silent=True) or {}
    origin = (data.get("origin") or "").strip()
    cities = (data.get("cities") or "").strip()
    date_range = (data.get("date_range") or "").strip()
    interests = (data.get("interests") or "").strip()

    missing = [
        name for name, value in (
            ("origin", origin),
            ("cities", cities),
            ("date_range", date_range),
        ) if not value
    ]
    if missing:
        return jsonify({
            "success": False,
            "message": f"缺少必填字段：{', '.join(missing)}",
        }), 400

    if not os.getenv("DASHSCOPE_API_KEY"):
        return jsonify({
            "success": False,
            "message": "服务端未配置 DASHSCOPE_API_KEY，无法调用大模型。",
        }), 500

    job_id = _new_job()
    thread = threading.Thread(
        target=_run_crew,
        args=(job_id, origin, cities, date_range, interests),
        name=f"trip-crew-{job_id}",
        daemon=True,
    )
    thread.start()
    return jsonify({"success": True, "job_id": job_id})


@app.get("/api/plan/<job_id>")
def get_plan(job_id):
    job = _snapshot(job_id)
    if not job:
        return jsonify({"success": False, "message": "任务不存在或已过期"}), 404
    return jsonify({"success": True, "job": job})


@app.get("/api/plan/<job_id>/md")
def download_plan(job_id):
    job = _snapshot(job_id)
    if not job:
        return jsonify({"success": False, "message": "任务不存在"}), 404
    if job["status"] != "done" or not job["result"]:
        return jsonify({"success": False, "message": "任务尚未完成"}), 409
    return Response(
        job["result"],
        mimetype="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="trip_plan_{job_id}.md"'
        },
    )


def main():
    parser = argparse.ArgumentParser(description="Trip Planner Flask 服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    # 默认用 8000：避开 macOS Monterey+ 上 AirPlay Receiver 占的 5000/7000
    parser.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    parser.add_argument("--debug", action="store_true", help="开启 Flask 调试模式")
    args = parser.parse_args()

    print("=" * 60)
    print("  TripMind · AI 旅行规划服务")
    print("=" * 60)
    print(f"  监听地址 : http://{args.host}:{args.port}")
    print(f"  默认模型 : {llm_config.DEFAULT_MODEL}")
    print(f"  DashScope: {'✅ 已配置' if os.getenv('DASHSCOPE_API_KEY') else '❌ 未配置'}")
    print(f"  Tavily   : {'✅ 已配置' if os.getenv('TAVILY_API_KEY') else '⚠️  未配置（搜索工具将不可用）'}")
    print("=" * 60)

    # 注意：开启 debug/reloader 时后台线程会被重启杀掉，
    # 因此默认关闭 reloader；如需调试请显式加 --debug。
    app.run(host=args.host, port=args.port, debug=args.debug,
            use_reloader=False, threaded=True)


if __name__ == "__main__":
    main()
