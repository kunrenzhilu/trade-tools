#!/usr/bin/env python3
"""
monitor.py — CodeBuddy 任务完成检测器

检查一个正在运行（或最近运行）的 orchestrator 迭代是否完成，
输出结构化状态，包括：进程存活、agent 阶段、空闲时长、代码变更、最终判定。

用法：
    # 检查指定 PID
    python alignment/monitor.py --pid 11226

    # 自动从日志找最近一次 orchestrator 运行
    python alignment/monitor.py --log /tmp/mytrader_iteration_5_orchestrator.log

    # 持续监控直到完成（每 30 秒检查一次，完成时退出）
    python alignment/monitor.py --pid 11226 --wait

    # JSON 输出（便于程序消费）
    python alignment/monitor.py --pid 11226 --json

依赖：仅标准库，无需额外安装。
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# ─── 配置 ────────────────────────────────────────────────────────────────

# 进程空闲判定：日志无新行 + agent phase=idle 持续此秒数 → 可能完成
IDLE_THRESHOLD_SECONDS = 120
# 日志无变化秒数 → 可能卡住/完成
LOG_STALE_THRESHOLD = 120


# ─── 数据结构 ────────────────────────────────────────────────────────────


@dataclass
class OrchestratorStatus:
    """Orchestrator 运行状态"""

    pid: int | None = None
    process_alive: bool = False
    cpu_percent: float = 0.0
    elapsed_seconds: float = 0.0

    cb_process_alive: bool = False          # CodeBuddy --acp 子进程
    cb_pid: int | None = None
    cb_cpu: float = 0.0

    agent_phase: str = "unknown"             # 最后一次 agentPhase
    idle_seconds: float = 0.0                # 距上次 session_update 的秒数
    last_log_time: float = 0.0               # 日志最后修改时间
    log_stale_seconds: float = 0.0           # 日志无变化秒数
    log_size_bytes: int = 0

    git_changed_files: int = 0               # git diff 文件数
    git_changed_lines_insert: int = 0
    git_changed_lines_delete: int = 0
    git_clean: bool = False

    total_updates: int = 0
    total_tools: int = 0

    # 判定
    status: str = "unknown"                  # running / idle / stuck / completed / completed_by_orchestrator / dead
    status_detail: str = ""

    # orchestrator 最终状态行（如"迭代完成 status=passed"）
    orchestrator_final_status: str = ""
    test_result_line: str = ""


# ─── 检测函数 ────────────────────────────────────────────────────────────


def _ps_process(pid: int | None) -> dict[str, Any] | None:
    """获取单个进程信息（ps）。"""
    if pid is None:
        return None
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "pid=,stat=,pcpu=,etime=,command="],
            capture_output=True, text=True, timeout=5,
        )
        out = result.stdout.strip()
        if not out:
            return None
        parts = out.split(None, 4)
        if len(parts) < 5:
            return None
        return {
            "pid": int(parts[0]),
            "stat": parts[1],
            "cpu": float(parts[2]) if parts[2].replace(".", "").isdigit() else 0.0,
            "elapsed_str": parts[3],
            "command": parts[4],
        }
    except Exception:
        return None


def parse_elapsed(elapsed_str: str) -> float:
    """解析 ps etime 为秒数（格式: DD-HH:MM:SS 或 HH:MM:SS 或 MM:SS）。"""
    if "-" in elapsed_str:
        days, rest = elapsed_str.split("-", 1)
        parts = list(map(int, rest.split(":")))
        return int(days) * 86400 + parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) > 2 else 0)
    parts = list(map(int, elapsed_str.split(":")))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return 0.0


def _find_cb_process(parent_pid: int) -> dict[str, Any] | None:
    """找到父进程的子 codebuddy --acp 进程。"""
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(parent_pid), "-a"],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return None
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        child_pid = parts[0]
        if child_pid.isdigit() and "codebuddy" in line and "--acp" in line:
            return _ps_process(int(child_pid))
    return None


def _parse_log(log_path: Path) -> dict[str, Any]:
    """解析 orchestrator 日志，提取 agent phase、idle、最终状态。"""
    result = {
        "agent_phase": "unknown",
        "idle_seconds": 0.0,
        "total_updates": 0,
        "total_tools": 0,
        "orchestrator_final_status": "",
        "test_result_line": "",
    }
    if not log_path.exists():
        return result

    text = log_path.read_text(errors="replace")

    # 最后修改时间
    result["last_log_time"] = log_path.stat().st_mtime
    result["log_stale_seconds"] = time.time() - result["last_log_time"]
    result["log_size_bytes"] = log_path.stat().st_size

    # agentPhase 和 更新时间
    import re
    for m in re.finditer(
        r"\[(\d+)m(\d+)s\]\s+.*phase=(\w+)\s+idle_since_last_update=(\d+)s\s+updates=(\d+)\s+tools=(\d+)",
        text,
    ):
        mins, secs, phase, idle, updates, tools = m.groups()
        result["agent_phase"] = phase
        result["idle_seconds"] = float(idle)
        result["total_updates"] = int(updates)
        result["total_tools"] = int(tools)

    # orchestrator 最终状态
    fm = re.search(r"迭代完成\s+status=(\S+)", text)
    if fm:
        result["orchestrator_final_status"] = fm.group(1)

    test_m = re.search(
        r"(test_count|测试数变化|测试结果).*", text[-2000:], re.IGNORECASE
    )
    if test_m:
        result["test_result_line"] = test_m.group(0)

    return result


def _git_info(project_root: Path) -> dict[str, Any]:
    """获取 git 变更统计。"""
    result = {"changed_files": 0, "insert": 0, "delete": 0, "clean": False}
    try:
        r = subprocess.run(
            ["git", "diff", "--stat"],
            capture_output=True, text=True, timeout=5,
            cwd=str(project_root),
        )
        out = r.stdout
        # 解析: "8 files changed, 669 insertions(+), 26 deletions(-)"
        import re
        fm = re.search(r"(\d+)\s+files?\s+changed", out)
        if fm:
            result["changed_files"] = int(fm.group(1))
        fm = re.search(r"(\d+)\s+insertions?\(", out)
        if fm:
            result["insert"] = int(fm.group(1))
        fm = re.search(r"(\d+)\s+deletions?\(", out)
        if fm:
            result["delete"] = int(fm.group(1))
        if not out.strip():
            result["clean"] = True
    except Exception:
        pass
    return result


def check_status(
    orchestrator_pid: int | None = None,
    log_path: str | Path | None = None,
    project_root: str | Path = ".",
) -> OrchestratorStatus:
    """执行一次完整检测，返回状态对象。"""
    s = OrchestratorStatus()

    # 进程
    if orchestrator_pid:
        ps = _ps_process(orchestrator_pid)
        if ps:
            s.pid = ps["pid"]
            s.process_alive = True
            s.cpu_percent = ps["cpu"]
            s.elapsed_seconds = parse_elapsed(ps["elapsed_str"])

            cb = _find_cb_process(orchestrator_pid)
            if cb:
                s.cb_process_alive = True
                s.cb_pid = cb["pid"]
                s.cb_cpu = cb["cpu"]

    # 日志
    log = Path(log_path) if log_path else None
    if log and log.exists():
        info = _parse_log(log)
        s.agent_phase = info["agent_phase"]
        s.idle_seconds = info["idle_seconds"]
        s.total_updates = info["total_updates"]
        s.total_tools = info["total_tools"]
        s.last_log_time = info["last_log_time"]
        s.log_stale_seconds = info["log_stale_seconds"]
        s.log_size_bytes = info["log_size_bytes"]
        s.orchestrator_final_status = info["orchestrator_final_status"]
        s.test_result_line = info["test_result_line"]

    # git
    root = Path(project_root).resolve()
    if root.exists():
        g = _git_info(root)
        s.git_changed_files = g["changed_files"]
        s.git_changed_lines_insert = g["insert"]
        s.git_changed_lines_delete = g["delete"]
        s.git_clean = g["clean"]

    # ── 判定 ──

    if s.orchestrator_final_status:
        s.status = "completed_by_orchestrator"
        s.status_detail = f"Orchestrator 已输出最终状态: {s.orchestrator_final_status}"
    elif not s.process_alive and orchestrator_pid is not None:
        s.status = "dead"
        s.status_detail = "Orchestrator 进程已退出"
    elif not s.cb_process_alive and orchestrator_pid is not None and s.process_alive:
        # orchestrator 还在等 timeout，但 CB 已退出
        s.status = "completed"
        s.status_detail = "CodeBuddy 已退出，orchestrator 正在等待 timeout 收尾"
    elif s.idle_seconds > IDLE_THRESHOLD_SECONDS and s.agent_phase == "idle":
        s.status = "completed"
        s.status_detail = f"CodeBuddy agent 处于 idle 已 {s.idle_seconds:.0f}s，可能已完成"
    elif s.log_stale_seconds > LOG_STALE_THRESHOLD and s.cb_process_alive:
        s.status = "stuck"
        s.status_detail = (
            f"日志 {LOG_STALE_THRESHOLD}s 无更新 + CodeBuddy 仍在 ({s.cb_cpu}% CPU) → 可能卡住"
        )
    elif s.log_stale_seconds > LOG_STALE_THRESHOLD and not s.cb_process_alive:
        s.status = "completed"
        s.status_detail = f"日志 {LOG_STALE_THRESHOLD}s 无更新 + CodeBuddy 不在运行 → 已结束"
    elif s.process_alive:
        s.status = "running"
        s.status_detail = (
            f"运行 {s.elapsed_seconds:.0f}s, "
            f"phase={s.agent_phase}, "
            f"idle={s.idle_seconds:.0f}s, "
            f"CB alive={s.cb_process_alive}"
        )
    else:
        s.status = "unknown"
        s.status_detail = "无法判定"

    return s


# ─── 输出 ────────────────────────────────────────────────────────────────


def format_status(s: OrchestratorStatus) -> str:
    """人类可读输出。"""
    status_emoji = {
        "running": "🔄",
        "completed": "✅",
        "completed_by_orchestrator": "✅",
        "idle": "⏳",
        "stuck": "⚠️",
        "dead": "❌",
        "unknown": "❓",
    }
    emoji = status_emoji.get(s.status, "❓")

    lines = [
        f"{emoji} Orchestrator Status: {s.status}",
        f"   Detail: {s.status_detail}",
        f"",
        f"   Process:  alive={s.process_alive}, pid={s.pid}, "
        f"cpu={s.cpu_percent:.1f}%, elapsed={s.elapsed_seconds:.0f}s",
        f"   CodeBuddy: alive={s.cb_process_alive}, pid={s.cb_pid}, cpu={s.cb_cpu:.1f}%",
        f"   Agent:    phase={s.agent_phase}, idle={s.idle_seconds:.0f}s",
        f"   Log:      {s.log_size_bytes}B, stale={s.log_stale_seconds:.0f}s",
        f"              updates={s.total_updates}, tools={s.total_tools}",
        f"   Git:      {s.git_changed_files} files changed "
        f"(+{s.git_changed_lines_insert}/-{s.git_changed_lines_delete})",
    ]

    if s.orchestrator_final_status:
        lines.append(f"   Final:    orchestrator status={s.orchestrator_final_status}")
    if s.test_result_line:
        lines.append(f"   Test:     {s.test_result_line}")

    return "\n".join(lines)


# ─── CLI 入口 ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CodeBuddy orchestrator 任务完成检测器"
    )
    parser.add_argument("--pid", type=int, help="Orchestrator 进程 PID")
    parser.add_argument("--log", help="Orchestrator 日志文件路径")
    parser.add_argument(
        "--project", default=".", help="项目根目录（默认当前目录）"
    )
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument(
        "--wait",
        action="store_true",
        help="持续监控直到完成（每 30 秒检查一次，完成时退出码 0）",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=7200,
        help="--wait 最大等待秒数（默认 7200=2h），超时退出码 2",
    )
    args = parser.parse_args()

    log_path = args.log
    if not log_path and args.pid:
        # 如果没指定 log，尝试从进程找
        pass
    if not log_path:
        log_path = "/tmp/mytrader_iteration_5_orchestrator.log"

    start = time.time()

    while True:
        s = check_status(
            orchestrator_pid=args.pid,
            log_path=log_path,
            project_root=args.project,
        )

        if args.json:
            print(json.dumps(asdict(s), indent=2, ensure_ascii=False, default=str))
        else:
            print(format_status(s))

        if not args.wait:
            # 单次检测
            sys.exit(0 if s.status in ("completed", "completed_by_orchestrator") else 1)

        # --wait 模式：持续检测
        if s.status in ("completed", "completed_by_orchestrator"):
            print("\n✅ 任务已完成。")
            sys.exit(0)
        if s.status in ("dead", "stuck"):
            print(f"\n{s.status_emoji.get(s.status, '?')} 任务状态异常: {s.status}")
            sys.exit(1)
        if time.time() - start > args.wait_timeout:
            print(f"\n⏰ 等待超时 ({args.wait_timeout}s)")
            sys.exit(2)

        print(f"\n⏳ 等待中... 下次检测 30 秒后 ({datetime.now().strftime('%H:%M:%S')})\n")
        time.sleep(30)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda *_: sys.exit(130))
    main()
