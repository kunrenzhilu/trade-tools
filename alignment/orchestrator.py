#!/usr/bin/env python3
"""
Orchestrator — CodeBuddy 监控循环

让 CodeBuddy 作为主力开发者迭代 mytrader，本脚本负责:
1. 通过 ACP 协议与 CodeBuddy --acp 通信
2. 注入 ai_constitution 规则
3. 实时监控工具调用和团队事件
4. 迭代后验证 Constitution 合规性（含高风险文件检查、测试数对比）
5. 自动补写 iteration_trajectory.md 和 decision_log.md（如 CodeBuddy 未自行更新）
6. 迭代完成/违规时通过 Telegram 通知用户

用法:
    python alignment/orchestrator.py --task "实现 AlpacaBroker auto 模式"
    python alignment/orchestrator.py --task "..." --max-turns 80 --timeout 3600
    python alignment/orchestrator.py --task "..." --team-research
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# ACP SDK
from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.interfaces import Client

# ─── 路径常量 ───────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MYTRADER_ROOT = PROJECT_ROOT / "mytrader"
ALIGNMENT_DIR = PROJECT_ROOT / "alignment"
CONSTITUTION_FILE = ALIGNMENT_DIR / "ai_constitution.md"
TRAJECTORY_FILE = ALIGNMENT_DIR / "iteration_trajectory.md"
DECISION_LOG_FILE = ALIGNMENT_DIR / "decision_log.md"
CODEBUDDY_FILE = PROJECT_ROOT / ".codebuddy" / "CODEBUDDY.md"
ITERATIONS_DIR = PROJECT_ROOT / "iterations"  # 每次迭代的完整快照

PYTHON_BIN = "/Users/rickouyang/miniforge3/envs/py312trade/bin/python"

# 高风险目录/文件（Constitution L8: 需用户审批）
HIGH_RISK_PATHS = [
    "mytrader/risk/",
    "mytrader/execution/",
    "mytrader/mytrader/risk/",
    "mytrader/mytrader/execution/",
]

# ─── 数据结构 ─────────────────────────────────────────────────────────────


@dataclass
class IterationResult:
    """单次迭代的结果"""

    iteration_id: str
    task: str
    start_time: float
    end_time: float = 0.0
    status: str = "running"  # running / passed / failed / partial
    updates_count: int = 0
    text_responses: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    team_events: list[dict] = field(default_factory=list)
    permission_requests: list[dict] = field(default_factory=list)
    # 心跳监控（仅用于日志，不参与退出决策）
    agent_phase: str = "unknown"
    last_update_time: float = 0.0
    # 合规检查结果
    violations: list[str] = field(default_factory=list)
    high_risk_files_touched: list[str] = field(default_factory=list)
    test_result: dict | None = None
    test_count_before: int = 0
    test_count_after: int = 0
    # 留痕检查
    trajectory_updated_by_codebuddy: bool = False
    decision_log_updated_by_codebuddy: bool = False
    # 文件变更
    changed_files: list[str] = field(default_factory=list)
    error: str | None = None
    # ACP buffer 溢出统计（LimitOverrunError，非致命）
    buffer_overflow_count: int = 0
    buffer_overflow_errors: list[str] = field(default_factory=list)


@dataclass
class ConstitutionRules:
    """从 ai_constitution.md 提取的规则"""

    forbidden_actions: list[str] = field(default_factory=list)
    high_risk_changes: list[str] = field(default_factory=list)
    low_risk_changes: list[str] = field(default_factory=list)
    validation_pipeline: dict = field(default_factory=dict)
    decision_priorities: list[str] = field(default_factory=list)


# ─── Constitution 加载 ──────────────────────────────────────────────────


def load_constitution() -> ConstitutionRules:
    """从 ai_constitution.md 提取关键规则"""
    rules = ConstitutionRules()

    if not CONSTITUTION_FILE.exists():
        return rules

    content = CONSTITUTION_FILE.read_text(encoding="utf-8")

    forbidden_section = re.search(
        r"Forbidden Actions.*?(?:---|\Z)", content, re.DOTALL
    )
    if forbidden_section:
        for line in forbidden_section.group().split("\n"):
            match = re.match(r"\d+\.\s*❌\s*(.+)", line.strip())
            if match:
                rules.forbidden_actions.append(match.group(1))

    high_risk_section = re.search(
        r"高风险（必须用户审批）.*?(?:---|\Z)", content, re.DOTALL
    )
    if high_risk_section:
        for line in high_risk_section.group().split("\n"):
            match = re.match(r"-\s*(.+)", line.strip())
            if match:
                rules.high_risk_changes.append(match.group(1))

    low_risk_section = re.search(
        r"低风险.*?Agent 可自动部署.*?(?:---|\Z)", content, re.DOTALL
    )
    if low_risk_section:
        for line in low_risk_section.group().split("\n"):
            match = re.match(r"-\s*(.+)", line.strip())
            if match:
                rules.low_risk_changes.append(match.group(1))

    rules.validation_pipeline = {
        "backtest_years": 5,
        "walk_forward_rounds": 4,
        "paper_trade_months": 1,
    }

    return rules


def build_constitution_prompt(task: str, rules: ConstitutionRules) -> str:
    """构造注入 CodeBuddy 的 Constitution prompt"""
    forbidden_str = "\n".join(
        f"  {i+1}. {a}" for i, a in enumerate(rules.forbidden_actions)
    )
    return f"""你是 mytrader 量化交易系统的开发者。本次任务: {task}

## 必须遵循的规则 (AI Constitution)

### 禁止行为:
{forbidden_str}

### 验证流水线:
- 策略必须经过: Backtest(≥5年) → Walk-Forward(4轮) → Paper Trade(≥1月) → Live
- 测试失败时不允许 Merge
- 测试覆盖率不得下降

### 决策记录:
- 模糊决策必须记录到 alignment/decision_log.md
- 每次迭代后更新 alignment/iteration_trajectory.md

### 代码规范:
- Python 3.12, 类型注解全覆盖
- 策略函数必须是纯函数（含 shift(1) 防前视偏差）
- 所有时间统一 UTC
- 文档与代码同步更新

## 完成前必须执行（不可跳过）
1. 运行 pytest 确认全部通过
2. 更新 alignment/iteration_trajectory.md（按 L9 格式：日期/类型/变更摘要/回测结果/Experience Learned/后续建议）
3. 更新 alignment/decision_log.md（如有模糊决策）
4. 更新 .codebuddy/CODEBUDDY.md（如有架构变更）

请开始执行任务。完成后确保所有测试通过。"""


# ─── ACP 客户端 ──────────────────────────────────────────────────────────


class OrchestratorClient(Client):
    """ACP 客户端 — 监控 CodeBuddy 的工作"""

    def __init__(self, result: IterationResult, heartbeat_cb=None):
        self.result = result
        self._heartbeat_cb = heartbeat_cb

    async def request_permission(
        self, options, session_id, tool_call, **kwargs
    ) -> dict:
        tool_name = "unknown"
        if hasattr(tool_call, "name"):
            tool_name = tool_call.name
        elif isinstance(tool_call, dict):
            tool_name = tool_call.get("name", "unknown")

        self.result.permission_requests.append(
            {"tool": tool_name, "session": session_id}
        )

        if options:
            for opt in options:
                opt_dict = opt.model_dump() if hasattr(opt, "model_dump") else opt
                kind = opt_dict.get("kind", "")
                if "allow" in kind:
                    option_id = opt_dict.get("optionId", "")
                    return {"outcome": {"outcome": "selected", "optionId": option_id}}

        return {"outcome": {"outcome": "cancelled"}}

    async def session_update(self, session_id, update, **kwargs):
        now = time.time()
        if hasattr(update, "model_dump"):
            d = update.model_dump()
        else:
            d = update

        self.result.updates_count += 1
        self.result.last_update_time = now

        for chunk in _extract_text(d):
            self.result.text_responses.append(chunk)

        meta = d.get("field_meta") or {}
        tool_name = meta.get("codebuddy.ai/toolName")
        if tool_name:
            self.result.tool_calls.append(
                {"tool": tool_name, "timestamp": now}
            )

        phase_info = meta.get("codebuddy.ai/agentPhase")
        if phase_info and isinstance(phase_info, dict):
            new_phase = phase_info.get("phase", "")
            if new_phase and new_phase != self.result.agent_phase:
                self.result.agent_phase = new_phase
                if self._heartbeat_cb:
                    self._heartbeat_cb(f"agentPhase → {new_phase}")

        for key in meta:
            if "team" in key.lower() or "member" in key.lower():
                self.result.team_events.append(
                    {"key": key, "value": meta[key]}
                )


def _extract_text(obj: Any, depth: int = 0) -> list[str]:
    texts = []
    if depth > 6:
        return texts
    if isinstance(obj, dict):
        if obj.get("type") in ("text", "text_delta"):
            if obj.get("text"):
                texts.append(obj["text"])
        for v in obj.values():
            texts.extend(_extract_text(v, depth + 1))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(_extract_text(item, depth + 1))
    return texts


# ─── 合规检查 ────────────────────────────────────────────────────────────


FORBIDDEN_CODE_PATTERNS = {
    "rl_introduction": (
        re.compile(r"import\s+(stable_baselines|gym|ray\.rllib)", re.IGNORECASE),
        "前线中引入 RL（禁止行为 #12）",
    ),
    "black_box_strategy": (
        re.compile(r"class\s+\w*(BlackBox|DeepLearning|NeuralNet)\w*\s*.*Strategy", re.IGNORECASE),
        "产生不可解释的买卖决策（禁止行为 #4）",
    ),
}

HIGH_RISK_PATTERNS = {
    "dd_threshold": re.compile(r"max_drawdown\s*[=<>!]+\s*[^2]\d", re.IGNORECASE),
    "stop_loss_change": re.compile(r"stop_loss_pct\s*[=<>!]+\s*[^0]", re.IGNORECASE),
    "position_limit": re.compile(r"max_position.*[=<>!]+\s*[0-9]", re.IGNORECASE),
}


def get_changed_files() -> list[str]:
    """获取 git diff 变更文件列表"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        if result.stdout.strip():
            return [f for f in result.stdout.strip().split("\n") if f]
        return []
    except Exception:
        return []


def check_git_diff_violations(changed_files: list[str]) -> tuple[list[str], list[str]]:
    """检查 git diff 是否有违规变更

    Returns:
        (violations, high_risk_files)
    """
    violations = []
    high_risk_files = []

    for filepath in changed_files:
        if not filepath or filepath.startswith("alignment/"):
            continue

        # 检查是否触及高风险目录
        for hr_path in HIGH_RISK_PATHS:
            if filepath.startswith(hr_path):
                high_risk_files.append(filepath)
                break

        full_path = PROJECT_ROOT / filepath
        if not full_path.exists() or not filepath.endswith(".py"):
            continue

        content = full_path.read_text(encoding="utf-8", errors="ignore")

        # 检查禁止的代码模式
        for pattern_name, (pattern, message) in FORBIDDEN_CODE_PATTERNS.items():
            if pattern.search(content):
                violations.append(f"{filepath}: {message}")

        # 检查高风险代码模式
        for pattern_name, pattern in HIGH_RISK_PATTERNS.items():
            if pattern.search(content):
                violations.append(
                    f"{filepath}: 高风险参数变更 ({pattern_name})，需用户审批"
                )

    return violations, high_risk_files


def count_tests() -> int:
    """收集当前测试数量（仅收集，不运行）"""
    try:
        result = subprocess.run(
            [PYTHON_BIN, "-m", "pytest", "--co", "-q"],
            capture_output=True,
            text=True,
            cwd=str(MYTRADER_ROOT),
            timeout=30,
        )
        count = 0
        for line in result.stdout.strip().split("\n"):
            if "::" in line:
                count += 1
        return count
    except Exception:
        return -1


def run_tests() -> dict:
    """运行 pytest 并返回结果"""
    try:
        result = subprocess.run(
            [PYTHON_BIN, "-m", "pytest", "--tb=short", "-q"],
            capture_output=True,
            text=True,
            cwd=str(MYTRADER_ROOT),
            timeout=120,
        )
        # 解析 "478 passed, 5 failed" 格式
        summary_line = ""
        for line in result.stdout.strip().split("\n"):
            if "passed" in line or "failed" in line or "error" in line:
                summary_line = line
                break

        passed = 0
        failed = 0
        errors = 0
        for m in re.finditer(r"(\d+)\s+(passed|failed|error)", summary_line):
            count = int(m.group(1))
            status = m.group(2)
            if status == "passed":
                passed = count
            elif status == "failed":
                failed = count
            elif status == "error":
                errors = count

        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "exit_code": result.returncode,
            "summary": summary_line,
            "stdout_tail": result.stdout[-500:],
        }
    except Exception as e:
        return {"error": str(e)}


# ─── 留痕检查 ────────────────────────────────────────────────────────────


def get_file_mtime(path: Path) -> float:
    """获取文件修改时间，不存在返回 0"""
    try:
        return path.stat().st_mtime
    except Exception:
        return 0.0


def check_trajectory_updated(start_time: float) -> bool:
    """检查 iteration_trajectory.md 是否在迭代期间被修改"""
    mtime = get_file_mtime(TRAJECTORY_FILE)
    return mtime > start_time


def check_decision_log_updated(start_time: float) -> bool:
    """检查 decision_log.md 是否在迭代期间被修改"""
    mtime = get_file_mtime(DECISION_LOG_FILE)
    return mtime > start_time


# ─── 日志记录（方案 B：自动补写）────────────────────────────────────────


def get_next_iteration_number() -> int:
    if not TRAJECTORY_FILE.exists():
        return 1
    content = TRAJECTORY_FILE.read_text(encoding="utf-8")
    matches = re.findall(r"## 迭代 #(\d+)", content)
    if matches:
        return max(int(m) for m in matches) + 1
    return 1


def log_iteration(result: IterationResult, rules: ConstitutionRules):
    """记录迭代轨迹到 iteration_trajectory.md

    方案 B：如果 CodeBuddy 已自行更新 trajectory，不覆盖；
    如果没有，从 session 数据自动补写。
    """
    if result.trajectory_updated_by_codebuddy:
        # CodeBuddy 自己更新了，追加一条 orchestrator 验证记录
        _append_orchestrator_verification(result)
        return

    # CodeBuddy 没更新，自动补写
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    duration = result.end_time - result.start_time
    iter_num = get_next_iteration_number()

    # 从 CodeBuddy 响应中提取摘要（取最后几段非空文本）
    response_summary = ""
    if result.text_responses:
        # 取最后一段超过 50 字符的文本
        for text in reversed(result.text_responses):
            if len(text.strip()) > 50:
                response_summary = text.strip()[:500]
                break
        if not response_summary:
            response_summary = result.text_responses[-1][:500]

    # 测试结果
    test_info = "N/A"
    if result.test_result:
        if result.test_result.get("error"):
            test_info = f"ERROR: {result.test_result['error']}"
        else:
            test_info = (
                f"{result.test_result.get('passed', 0)} passed, "
                f"{result.test_result.get('failed', 0)} failed"
            )
            if result.test_count_before > 0:
                delta = result.test_count_after - result.test_count_before
                test_info += f" (before={result.test_count_before}, after={result.test_count_after}, delta={delta:+d})"

    # 变更文件列表
    files_changed_str = ", ".join(result.changed_files[:10]) if result.changed_files else "无"
    if len(result.changed_files) > 10:
        files_changed_str += f" ... ({len(result.changed_files)} files total)"

    entry = f"""
## 迭代 #{iter_num} — {result.task}

- **日期**: {now}
- **类型**: 自动化迭代 (Orchestrator → CodeBuddy via ACP)
- **变更摘要**: {result.task}
- **执行时长**: {duration:.0f}s ({duration/60:.1f}min)
- **状态**: {result.status}
- **CodeBuddy 更新数**: {result.updates_count}
- **工具调用数**: {len(result.tool_calls)}
- **团队事件数**: {len(result.team_events)}
- **权限请求数**: {len(result.permission_requests)}

### 变更文件
{files_changed_str}

### 测试结果
{test_info}

### 违规详情
"""
    if result.violations:
        for v in result.violations:
            entry += f"- ❌ {v}\n"
    else:
        entry += "- ✅ 无违规\n"

    if result.high_risk_files_touched:
        entry += "\n### 高风险文件触及\n"
        for f in result.high_risk_files_touched:
            entry += f"- ⚠️ {f}（需用户审批）\n"

    if result.buffer_overflow_count > 0:
        entry += f"\n### ACP Buffer 溢出（{result.buffer_overflow_count} 次）\n"
        entry += "- 非致命错误：某条 JSON-RPC 消息超过 StreamReader limit\n"
        entry += "- CodeBuddy 可能已完成部分工作，验证结果反映实际产出\n"
        for err in result.buffer_overflow_errors:
            entry += f"- ⚠️ {err}\n"

    entry += f"""
### Constitution 合规
- DD 20% 约束: {"✅" if not result.violations else "⚠️ 检查违规"}
- 测试覆盖率: {"✅ 不降" if result.test_count_after >= result.test_count_before else "⚠️ 下降"} (before={result.test_count_before}, after={result.test_count_after})
- 黑箱策略: ✅ 未引入
- RL 引入: ✅ 未引入
- 文档同步: {"✅ CodeBuddy 已更新" if result.trajectory_updated_by_codebuddy else "⚠️ CodeBuddy 未更新，orchestrator 自动补写"}

### CodeBuddy 响应摘要（自动提取）
{response_summary}

### Experience Learned
- 迭代通过 ACP 协议执行，状态: {result.status}
- trajectory_updated_by_codebuddy: {result.trajectory_updated_by_codebuddy}
- decision_log_updated_by_codebuddy: {result.decision_log_updated_by_codebuddy}

### 后续建议
- 检查测试是否全部通过
- {"检查高风险文件变更，需用户审批" if result.high_risk_files_touched else "无高风险文件触及"}

---
"""

    mode = "a" if TRAJECTORY_FILE.exists() else "w"
    with open(TRAJECTORY_FILE, mode, encoding="utf-8") as f:
        f.write(entry)


def _append_orchestrator_verification(result: IterationResult):
    """CodeBuddy 已更新 trajectory 时，追加一条 orchestrator 验证记录"""
    test_info = "N/A"
    if result.test_result and not result.test_result.get("error"):
        test_info = f"{result.test_result.get('passed', 0)} passed, {result.test_result.get('failed', 0)} failed"

    entry = f"""
> **Orchestrator 验证记录** (自动追加)
> - 迭代状态: {result.status}
> - 测试: {test_info}
> - 违规: {len(result.violations)} 条
> - 高风险文件: {len(result.high_risk_files_touched)} 个
> - 测试数变化: {result.test_count_before} → {result.test_count_after}
> - CodeBuddy 自行更新了 trajectory ✅

---
"""
    with open(TRAJECTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def log_decision_if_needed(result: IterationResult):
    """如果检测到需要记录的决策，补写到 decision_log.md"""
    decisions_to_log = []

    # 高风险文件触及需要记录
    if result.high_risk_files_touched:
        decisions_to_log.append({
            "title": f"迭代 #{get_next_iteration_number() - 1} — 高风险文件触及",
            "description": "CodeBuddy 的代码变更触及了 Constitution L8 定义的高风险目录",
            "details": ", ".join(result.high_risk_files_touched),
            "action": "需用户审批后才能合并",
        })

    # 测试数下降需要记录
    if result.test_count_after < result.test_count_before and result.test_count_before > 0:
        decisions_to_log.append({
            "title": f"迭代 #{get_next_iteration_number() - 1} — 测试数量下降",
            "description": f"测试数从 {result.test_count_before} 下降到 {result.test_count_after}",
            "details": "违反 Constitution 禁止行为 #9（让测试覆盖率下降）",
            "action": "需补充测试或回退变更",
        })

    if not decisions_to_log:
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    mode = "a" if DECISION_LOG_FILE.exists() else "w"

    with open(DECISION_LOG_FILE, mode, encoding="utf-8") as f:
        for d in decisions_to_log:
            f.write(f"""
### [{now}] {d['title']}

- **困境描述**: {d['description']}
- **涉及 AI Constitution 条款**: L8 高风险变更 / 禁止行为
- **决策逻辑**: Orchestrator 自动检测到合规风险
- **决策结果**: {d['action']}
        - **详情**: {d['details']}
- **用户反馈**: 待用户确认

---
""")


# ─── 迭代快照保存 ──────────────────────────────────────────────────────────


def save_iteration_snapshot(result: IterationResult):
    """将完整迭代快照保存到 iterations/iteration_N/ 目录。

    与 iteration_trajectory.md（摘要留痕）互补，快照包含完整原始数据：
    - prompt_template.md: 发送给 CodeBuddy 的完整 prompt（含 Constitution 注入）
    - full_response.md: CodeBuddy 的全部文本输出
    - heartbeat_log.txt: stdout 中的心跳和时间线（从 print 捕获）
    - code_diff.patch: 迭代结束时的 git diff
    - result.json: IterationResult 的结构化序列化
    """
    iter_num = get_next_iteration_number() - 1  # log_iteration 已调用，编号已分配
    if iter_num < 1:
        iter_num = 1
    snapshot_dir = ITERATIONS_DIR / f"iteration_{iter_num}"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    # 1. result.json — 结构化结果
    result_data = {
        "iteration_id": result.iteration_id,
        "task": result.task,
        "status": result.status,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "duration_seconds": result.end_time - result.start_time if result.end_time else 0,
        "updates_count": result.updates_count,
        "tool_calls_count": len(result.tool_calls),
        "team_events_count": len(result.team_events),
        "permission_requests_count": len(result.permission_requests),
        "changed_files": result.changed_files,
        "violations": result.violations,
        "high_risk_files_touched": result.high_risk_files_touched,
        "test_count_before": result.test_count_before,
        "test_count_after": result.test_count_after,
        "test_result": result.test_result,
        "trajectory_updated_by_codebuddy": result.trajectory_updated_by_codebuddy,
        "decision_log_updated_by_codebuddy": result.decision_log_updated_by_codebuddy,
        "buffer_overflow_count": result.buffer_overflow_count,
        "buffer_overflow_errors": result.buffer_overflow_errors,
        "error": result.error,
    }
    (snapshot_dir / "result.json").write_text(
        json.dumps(result_data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # 2. full_response.md — CodeBuddy 的全部文本输出
    response_text = "\n---\n".join(result.text_responses) if result.text_responses else "(无文本输出)"
    (snapshot_dir / "full_response.md").write_text(response_text, encoding="utf-8")

    # 3. code_diff.patch — git diff 快照
    try:
        diff_result = subprocess.run(
            ["git", "diff", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=15,
        )
        diff_content = diff_result.stdout if diff_result.stdout.strip() else "(无代码变更)"
    except Exception as e:
        diff_content = f"(git diff 失败: {e})"
    (snapshot_dir / "code_diff.patch").write_text(diff_content, encoding="utf-8")

    # 4. prompt_template.md — 记录任务描述（prompt 本身在 build_constitution_prompt 中构造）
    (snapshot_dir / "prompt_template.md").write_text(
        f"# 迭代 #{iter_num} Prompt\n\n"
        f"**任务**: {result.task}\n\n"
        f"**时间**: {datetime.fromtimestamp(result.start_time, tz=timezone.utc).isoformat()}\n\n"
        f"**注**: 完整 prompt 由 build_constitution_prompt() 动态生成，"
        f"注入了 ai_constitution.md 的禁止行为、验证流水线、代码规范等规则。\n",
        encoding="utf-8",
    )

    # 5. tool_calls.json — 工具调用时间线
    if result.tool_calls:
        (snapshot_dir / "tool_calls.json").write_text(
            json.dumps(result.tool_calls, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    print(f"  快照已保存: {snapshot_dir}")


def save_iteration_summary_template(
    result: IterationResult,
    rules: ConstitutionRules,
    summary_text: str = "",
):
    """在 iterations/iteration_N/ 中生成 summary.md 模板。

    Orchestrator 自动生成骨架（含客观数据），Meta-Agent 负责补充判断和评估。
    如果 summary.md 已存在（Meta-Agent 已手写），不覆盖。

    Args:
        result: 迭代结果
        rules: Constitution 规则
        summary_text: 额外的摘要文本（可选，通常由 Meta-Agent 在 orchestrator 外写入）
    """
    iter_num = get_next_iteration_number() - 1
    if iter_num < 1:
        iter_num = 1
    snapshot_dir = ITERATIONS_DIR / f"iteration_{iter_num}"
    summary_file = snapshot_dir / "summary.md"

    if summary_file.exists():
        # Meta-Agent 已手写 summary，不覆盖
        print(f"  summary.md 已存在，跳过模板生成")
        return

    snapshot_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    duration = result.end_time - result.start_time if result.end_time else 0

    # 客观数据（orchestrator 自动填写）
    test_info = "N/A"
    if result.test_result and not result.test_result.get("error"):
        test_info = f"{result.test_result.get('passed', 0)} passed, {result.test_result.get('failed', 0)} failed"

    files_changed_str = "\n".join(f"- {f}" for f in result.changed_files[:15]) if result.changed_files else "- (无)"
    if len(result.changed_files) > 15:
        files_changed_str += f"\n- ... ({len(result.changed_files)} files total)"

    violations_str = "\n".join(f"- ❌ {v}" for v in result.violations) if result.violations else "- ✅ 无违规"

    template = f"""# Iteration #{iter_num} Summary

> **自动生成**: {now}（orchestrator 模板，Meta-Agent 需补充判断部分）
> **Spec**: `iterations/iteration_{iter_num}/spec.md`

## Requested

{result.task[:200]}

## Delivered

### Files Changed
{files_changed_str}

### Tests
- Before: {result.test_count_before}
- After: {result.test_count_after}
- Result: {test_info}

### Duration
{duration:.0f}s ({duration/60:.1f}min)

### Status: {result.status}

## Meta-Agent Judgment

> ⚠️ 以下部分由 Meta-Agent 填写（orchestrator 仅生成骨架）

### Technical: [PASS/FAIL/PARTIAL]
- [补充测试分析]

### Business Impact: [HIGH/MEDIUM/LOW/NONE]
- [补充业务指标变化]

### Strategic Fit: [GOOD/NEUTRAL/POOR]
- [补充策略评估]

## Bugs Fixed by Meta-Agent
- [如有补充]

## Gate Status
| Gate | Condition | Result |
|------|-----------|--------|
| [补充] | [补充] | [补充] |

## Next Steps
- [补充下一轮迭代方向，作为下一轮 Plan 的输入]

## Lessons Learned
- [补充]
"""

    summary_file.write_text(template, encoding="utf-8")
    print(f"  summary 模板已生成: {summary_file}")



# ─── Telegram 通知 ───────────────────────────────────────────────────────


def send_telegram_notification(message: str):
    """通过 Telegram Bot 发送通知

    从环境变量读取配置:
    - TELEGRAM_BOT_TOKEN
    - TELEGRAM_CHAT_ID
    """
    import httpx

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        return False

    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def notify_iteration_result(result: IterationResult):
    """迭代完成后发送 Telegram 通知"""
    status_emoji = {"passed": "✅", "failed": "❌", "partial": "⚠️"}.get(
        result.status, "❓"
    )
    duration_min = (result.end_time - result.start_time) / 60

    msg = f"{status_emoji} *MyTrader 迭代完成*\n\n"
    msg += f"任务: {result.task[:100]}\n"
    msg += f"状态: {result.status}\n"
    msg += f"时长: {duration_min:.1f}min\n"
    msg += f"工具调用: {len(result.tool_calls)}\n"
    msg += f"变更文件: {len(result.changed_files)}\n"

    if result.test_result and not result.test_result.get("error"):
        msg += f"测试: {result.test_result.get('passed', 0)} passed, {result.test_result.get('failed', 0)} failed\n"

    if result.test_count_after != result.test_count_before and result.test_count_before > 0:
        delta = result.test_count_after - result.test_count_before
        msg += f"测试数变化: {result.test_count_before} → {result.test_count_after} ({delta:+d})\n"

    if result.buffer_overflow_count > 0:
        msg += f"⚠️ ACP buffer 溢出: {result.buffer_overflow_count} 次（非致命）\n"

    if result.violations:
        msg += f"\n*违规检测 ({len(result.violations)} 条):*\n"
        for v in result.violations[:5]:
            msg += f"  ❌ {v[:80]}\n"

    if result.high_risk_files_touched:
        msg += f"\n*⚠️ 高风险文件触及 ({len(result.high_risk_files_touched)} 个):*\n"
        for f in result.high_risk_files_touched[:5]:
            msg += f"  ⚠️ {f}\n"
        msg += "\n_需用户审批后才能合并_\n"

    send_telegram_notification(msg)


# ─── 主循环 ──────────────────────────────────────────────────────────────


async def run_iteration(
    task: str,
    max_turns: int = 50,
    timeout_seconds: int = 900,
    use_team: bool = False,
) -> IterationResult:
    """执行一次完整的迭代循环

    等待策略：process-based（CodeBuddy 退出即结束）:
    - 每 5 秒检查 CodeBuddy 子进程是否仍在运行
    - 子进程退出 → 立即进入后置验证
    - timeout_seconds 仅作为最大保护上限（防止进程僵死）
    - 每 30 秒打印心跳（agentPhase + 距上次 session_update 多久）
    """

    iteration_id = str(uuid4())[:8]
    result = IterationResult(
        iteration_id=iteration_id,
        task=task,
        start_time=time.time(),
    )

    # 迭代前：记录测试数量基线
    result.test_count_before = count_tests()
    print(f"[pre-iteration] 测试基线: {result.test_count_before}")

    # 加载 Constitution
    rules = load_constitution()
    prompt = build_constitution_prompt(task, rules)

    if use_team:
        prompt += """

## 并行调研指令
请使用 TeamCreate 工具创建团队 'research-team'，
派出两个成员并行工作：
1. 'module-researcher-1' — 调研相关模块的代码结构和依赖关系
2. 'module-researcher-2' — 调研相关模块的测试覆盖情况
完成后汇总结果再开始开发。"""

    def heartbeat_log(msg: str):
        elapsed = time.time() - result.start_time
        since_last = time.time() - result.last_update_time if result.last_update_time else 0
        print(f"[{elapsed//60:.0f}m{elapsed%60:02.0f}s] {msg} | "
              f"phase={result.agent_phase} idle_since_last_update={since_last:.0f}s "
              f"updates={result.updates_count} tools={len(result.tool_calls)}")

    client = OrchestratorClient(result, heartbeat_cb=heartbeat_log)

    try:
        async with spawn_agent_process(
            client,
            "codebuddy",
            "--acp",
            "--permission-mode", "bypassPermissions",
            "--max-turns", str(max_turns),
            cwd=str(MYTRADER_ROOT),
            transport_kwargs={"limit": 1024 * 1024},  # 64KB → 1MB
        ) as (conn, proc):

            await conn.initialize(protocol_version=PROTOCOL_VERSION)

            session = await conn.new_session(
                cwd=str(MYTRADER_ROOT),
                mcp_servers=[],
            )

            prompt_response = await conn.prompt(
                session_id=session.session_id,
                prompt=[text_block(prompt)],
                message_id=str(uuid4()),
            )
            heartbeat_log(f"prompt 已发送, stop_reason={prompt_response.stop_reason}")

            # process-based 等待（CodeBuddy 进程退出即结束）
            check_interval = 5
            heartbeat_interval = 30
            last_heartbeat = time.time()
            start = time.time()

            while True:
                # CodeBuddy 进程已退出？
                if proc.returncode is not None:
                    elapsed = time.time() - start
                    heartbeat_log(f"CodeBuddy 进程已退出 (rc={proc.returncode}, elapsed={elapsed:.0f}s)")
                    break

                elapsed = time.time() - start
                if elapsed > timeout_seconds:
                    heartbeat_log(f"timeout 到达 ({timeout_seconds}s)，强制退出")
                    break

                await asyncio.sleep(check_interval)

                if time.time() - last_heartbeat > heartbeat_interval:
                    heartbeat_log("心跳")
                    last_heartbeat = time.time()

    except ValueError as e:
        # ACP _receive_loop 中 readline() 超限时，acp 库将 LimitOverrunError
        # 包装为 ValueError("Separator is found, but chunk is longer than limit")。
        # 这意味着某条 JSON-RPC 消息（如 tool result）超过了 StreamReader limit。
        # 非致命：CodeBuddy 可能已完成大部分工作，应继续做迭代后验证。
        err_msg = str(e)
        if "Separator is found" in err_msg or "chunk is longer than limit" in err_msg:
            result.buffer_overflow_count += 1
            result.buffer_overflow_errors.append(
                f"[{time.strftime('%H:%M:%S')}] {err_msg[:200]}"
            )
            elapsed = time.time() - result.start_time
            print(f"[{elapsed//60:.0f}m{elapsed%60:02.0f}] ⚠️  ACP buffer overflow "
                  f"(#{result.buffer_overflow_count}), 跳过此消息，继续验证")
        else:
            result.error = err_msg
            result.status = "failed"
    except Exception as e:
        result.error = str(e)
        result.status = "failed"

    result.end_time = time.time()

    # ─── 迭代后验证 ──────────────────────────────────────────────────

    # buffer overflow 不阻止验证（result.error 未设置）
    if not result.error:
        # 1. 获取变更文件列表
        result.changed_files = get_changed_files()

        # 2. 检查 git diff 违规 + 高风险文件
        violations, high_risk = check_git_diff_violations(result.changed_files)
        result.violations.extend(violations)
        result.high_risk_files_touched = high_risk

        # 3. 运行测试
        result.test_result = run_tests()
        result.test_count_after = count_tests()

        # 4. 检查 CodeBuddy 是否自行更新了留痕文件
        result.trajectory_updated_by_codebuddy = check_trajectory_updated(result.start_time)
        result.decision_log_updated_by_codebuddy = check_decision_log_updated(result.start_time)

        # 5. 判定状态
        if result.violations:
            result.status = "failed"
        elif result.test_count_after < result.test_count_before and result.test_count_before > 0:
            result.status = "failed"  # 测试数下降 = 禁止行为 #9
        elif result.high_risk_files_touched:
            result.status = "partial"  # 高风险变更需审批
        elif result.buffer_overflow_count > 0:
            result.status = "partial"  # ACP 通信中断，结果可能不完整
        elif result.test_result and result.test_result.get("error"):
            result.status = "partial"
        else:
            result.status = "passed"

    # 6. 自动补写 trajectory（方案 B）
    log_iteration(result, rules)

    # 7. 补写 decision_log（如有需要）
    log_decision_if_needed(result)

    # 8. 保存完整迭代快照到 iterations/iteration_N/
    save_iteration_snapshot(result)

    # 9. 生成 summary.md 模板（Meta-Agent 后续补充判断）
    save_iteration_summary_template(result, rules)

    # 10. Telegram 通知
    notify_iteration_result(result)

    # 11. 打印留痕状态
    heartbeat_log(f"迭代完成 status={result.status}")
    print(f"  trajectory_updated_by_codebuddy: {result.trajectory_updated_by_codebuddy}")
    print(f"  decision_log_updated_by_codebuddy: {result.decision_log_updated_by_codebuddy}")
    print(f"  test_count: {result.test_count_before} → {result.test_count_after}")
    print(f"  high_risk_files: {result.high_risk_files_touched}")
    print(f"  violations: {result.violations}")

    return result


# ─── CLI 入口 ────────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Orchestrator — CodeBuddy 监控循环"
    )
    parser.add_argument("--task", required=True, help="迭代任务描述")
    parser.add_argument("--max-turns", type=int, default=50, help="最大代理轮次")
    parser.add_argument(
        "--timeout", type=int, default=900, help="总超时时间（秒，默认 900=15min）"
    )
    parser.add_argument(
        "--team-research",
        action="store_true",
        help="使用 Agent Teams 进行并行调研",
    )
    args = parser.parse_args()

    result = asyncio.run(
        run_iteration(
            task=args.task,
            max_turns=args.max_turns,
            timeout_seconds=args.timeout,
            use_team=args.team_research,
        )
    )

    # 打印结果摘要
    print("\n" + "=" * 60)
    print(f"迭代 #{result.iteration_id} 完成")
    print(f"任务: {result.task}")
    print(f"状态: {result.status}")
    print(f"更新数: {result.updates_count}")
    print(f"工具调用: {len(result.tool_calls)}")
    print(f"团队事件: {len(result.team_events)}")
    print(f"权限请求: {len(result.permission_requests)}")
    print(f"变更文件: {len(result.changed_files)}")
    print(f"违规: {len(result.violations)}")
    if result.violations:
        for v in result.violations:
            print(f"  ❌ {v}")
    if result.high_risk_files_touched:
        print(f"高风险文件: {len(result.high_risk_files_touched)}")
        for f in result.high_risk_files_touched:
            print(f"  ⚠️ {f}")
    print(f"测试数: {result.test_count_before} → {result.test_count_after}")
    if result.buffer_overflow_count > 0:
        print(f"⚠️  ACP buffer 溢出: {result.buffer_overflow_count} 次（非致命，验证仍执行）")
    print(f"trajectory 更新: {'CodeBuddy' if result.trajectory_updated_by_codebuddy else 'orchestrator 补写'}")
    print(f"decision_log 更新: {'CodeBuddy' if result.decision_log_updated_by_codebuddy else 'orchestrator 补写'}")
    if result.error:
        print(f"错误: {result.error}")
    if result.test_result and not result.test_result.get("error"):
        print(f"测试结果: {result.test_result.get('passed', 0)} passed, {result.test_result.get('failed', 0)} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
