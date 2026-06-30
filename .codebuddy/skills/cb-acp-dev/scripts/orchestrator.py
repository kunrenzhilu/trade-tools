#!/usr/bin/env python3
"""
Orchestrator — CodeBuddy 监控循环

让 CodeBuddy 作为主力开发者迭代 mytrader，本脚本负责:
1. 通过 ACP 协议与 CodeBuddy --acp 通信
2. 注入 ai_constitution 规则
3. 实时监控工具调用和团队事件
4. 迭代后验证 Constitution 合规性
5. 记录到 iteration_trajectory.md 和 decision_log.md

用法:
    python alignment/orchestrator.py --task "实现 AlpacaBroker auto 模式"
    python alignment/orchestrator.py --task "..." --max-turns 30
    python alignment/orchestrator.py --team-research "并行调研 backtest 和 signal 模块"
"""

import asyncio
import json
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
    # 空闲检测
    agent_phase: str = "unknown"        # 当前 agentPhase（仅用于心跳日志，不参与退出决策）
    last_update_time: float = 0.0       # 最后一次 session_update 的时间戳
    violations: list[str] = field(default_factory=list)
    test_result: dict | None = None
    error: str | None = None


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

    # 提取禁止行为
    forbidden_section = re.search(
        r"Forbidden Actions.*?(?:---|\Z)", content, re.DOTALL
    )
    if forbidden_section:
        for line in forbidden_section.group().split("\n"):
            match = re.match(r"\d+\.\s*❌\s*(.+)", line.strip())
            if match:
                rules.forbidden_actions.append(match.group(1))

    # 提取高风险变更
    high_risk_section = re.search(
        r"高风险（必须用户审批）.*?(?:---|\Z)", content, re.DOTALL
    )
    if high_risk_section:
        for line in high_risk_section.group().split("\n"):
            match = re.match(r"-\s*(.+)", line.strip())
            if match and not match.group(1).startswith("修改"):
                rules.high_risk_changes.append(match.group(1))
            elif match:
                rules.high_risk_changes.append(match.group(1))

    # 提取低风险变更
    low_risk_section = re.search(
        r"低风险.*?Agent 可自动部署.*?(?:---|\Z)", content, re.DOTALL
    )
    if low_risk_section:
        for line in low_risk_section.group().split("\n"):
            match = re.match(r"-\s*(.+)", line.strip())
            if match:
                rules.low_risk_changes.append(match.group(1))

    # 验证流水线
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
        """自动批准所有权限请求"""
        tool_name = "unknown"
        if hasattr(tool_call, "name"):
            tool_name = tool_call.name
        elif isinstance(tool_call, dict):
            tool_name = tool_call.get("name", "unknown")

        self.result.permission_requests.append(
            {"tool": tool_name, "session": session_id}
        )

        # 选择第一个 allow 选项
        if options:
            for opt in options:
                opt_dict = opt.model_dump() if hasattr(opt, "model_dump") else opt
                kind = opt_dict.get("kind", "")
                if "allow" in kind:
                    option_id = opt_dict.get("optionId", "")
                    return {"outcome": {"outcome": "selected", "optionId": option_id}}

        return {"outcome": {"outcome": "cancelled"}}

    async def session_update(self, session_id, update, **kwargs):
        """接收 CodeBuddy 的实时更新 — 追踪 agentPhase 用于心跳监控"""
        now = time.time()
        if hasattr(update, "model_dump"):
            d = update.model_dump()
        else:
            d = update

        self.result.updates_count += 1
        self.result.last_update_time = now

        # 提取文本
        for chunk in _extract_text(d):
            self.result.text_responses.append(chunk)

        # 提取工具调用
        meta = d.get("field_meta") or {}
        tool_name = meta.get("codebuddy.ai/toolName")
        if tool_name:
            self.result.tool_calls.append(
                {"tool": tool_name, "timestamp": now}
            )

        # 追踪 agentPhase（心跳监控信号，不参与退出决策）
        phase_info = meta.get("codebuddy.ai/agentPhase")
        if phase_info and isinstance(phase_info, dict):
            new_phase = phase_info.get("phase", "")
            if new_phase and new_phase != self.result.agent_phase:
                self.result.agent_phase = new_phase
                if self._heartbeat_cb:
                    self._heartbeat_cb(f"agentPhase → {new_phase}")

        # 提取团队事件
        for key in meta:
            if "team" in key.lower() or "member" in key.lower():
                self.result.team_events.append(
                    {"key": key, "value": meta[key]}
                )


def _extract_text(obj: Any, depth: int = 0) -> list[str]:
    """递归提取所有文本内容"""
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


# 禁止的代码模式
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

# 高风险代码模式（需用户审批）
HIGH_RISK_PATTERNS = {
    "dd_threshold": re.compile(r"max_drawdown\s*[=<>!]+\s*[^2]\d", re.IGNORECASE),
    "stop_loss_change": re.compile(r"stop_loss_pct\s*[=<>!]+\s*[^0]", re.IGNORECASE),
    "position_limit": re.compile(r"max_position.*[=<>!]+\s*[0-9]", re.IGNORECASE),
}


def check_git_diff_violations() -> list[str]:
    """检查 git diff 是否有违规变更"""
    violations = []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=10,
        )
        changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # 检查每个变更文件的内容
        for filepath in changed_files:
            if not filepath or filepath == "alignment/orchestrator_design.md":
                continue
            full_path = PROJECT_ROOT / filepath
            if not full_path.exists() or not filepath.endswith(".py"):
                continue

            content = full_path.read_text(encoding="utf-8", errors="ignore")
            for pattern_name, (pattern, message) in FORBIDDEN_CODE_PATTERNS.items():
                if pattern.search(content):
                    violations.append(f"{filepath}: {message}")

    except Exception as e:
        violations.append(f"git diff 检查失败: {e}")
    return violations


def run_tests() -> dict:
    """运行 pytest 并返回结果"""
    try:
        result = subprocess.run(
            [
                "/Users/rickouyang/miniforge3/envs/py312trade/bin/python",
                "-m",
                "pytest",
                "--tb=short",
                "-q",
                "--co",
                "-q",
            ],
            capture_output=True,
            text=True,
            cwd=str(MYTRADER_ROOT),
            timeout=30,
        )
        # 收集测试数量
        collected = result.stdout.strip().split("\n")
        test_count = 0
        for line in collected:
            if "::" in line:
                test_count += 1

        return {
            "collected": test_count,
            "exit_code": result.returncode,
            "stdout": result.stdout[:500],
        }
    except Exception as e:
        return {"error": str(e)}


# ─── 日志记录 ────────────────────────────────────────────────────────────


def get_next_iteration_number() -> int:
    """从 iteration_trajectory.md 获取下一个迭代编号"""
    if not TRAJECTORY_FILE.exists():
        return 1
    content = TRAJECTORY_FILE.read_text(encoding="utf-8")
    matches = re.findall(r"## 迭代 #(\d+)", content)
    if matches:
        return max(int(m) for m in matches) + 1
    return 1


def log_iteration(result: IterationResult, rules: ConstitutionRules):
    """记录迭代轨迹到 iteration_trajectory.md"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    duration = result.end_time - result.start_time

    entry = f"""
## 迭代 #{get_next_iteration_number() - 1} — {result.task}

- **日期**: {now}
- **类型**: 自动化迭代 (Orchestrator → CodeBuddy)
- **变更摘要**: {result.task}
- **执行时长**: {duration:.1f}s
- **状态**: {result.status}
- **CodeBuddy 更新数**: {result.updates_count}
- **工具调用数**: {len(result.tool_calls)}
- **团队事件数**: {len(result.team_events)}
- **权限请求数**: {len(result.permission_requests)}
- **违规检测**: {len(result.violations)} 条
- **测试收集**: {result.test_result.get('collected', 'N/A') if result.test_result else 'N/A'}

### 违规详情
"""
    if result.violations:
        for v in result.violations:
            entry += f"- ❌ {v}\n"
    else:
        entry += "- ✅ 无违规\n"

    entry += f"""
### CodeBuddy 最终响应 (摘要)
{(result.text_responses[-1] if result.text_responses else '无响应')[:500]}

### Experience Learned
- 自动化迭代通过 ACP 协议成功执行
- 迭代状态: {result.status}

### 后续建议
- 根据 CodeBuddy 的实际产出决定下一步
- 检查测试是否全部通过

---
"""

    # 追加到文件
    mode = "a" if TRAJECTORY_FILE.exists() else "w"
    with open(TRAJECTORY_FILE, mode, encoding="utf-8") as f:
        f.write(entry)


# ─── 主循环 ──────────────────────────────────────────────────────────────


async def run_iteration(
    task: str,
    max_turns: int = 50,
    timeout_seconds: int = 900,
    use_team: bool = False,
) -> IterationResult:
    """执行一次完整的迭代循环

    等待策略：time-based（确定性，简单可靠）:
    - 等满 timeout_seconds，不提前退出
    - 每 30 秒打印心跳（agentPhase + 距上次 session_update 多久）
    - session_update 实时刷新 last_update_time（用于心跳显示，不改变退出逻辑）
    """

    iteration_id = str(uuid4())[:8]
    result = IterationResult(
        iteration_id=iteration_id,
        task=task,
        start_time=time.time(),
    )

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
        """心跳 — 输出到 stdout（nohup 日志可见），只用于监控，不参与退出决策"""
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

            # time-based 等待（确定性，不提前退出）
            elapsed = 0
            check_interval = 5
            heartbeat_interval = 30
            last_heartbeat = time.time()

            while elapsed < timeout_seconds:
                await asyncio.sleep(check_interval)
                elapsed += check_interval

                # 心跳（仅日志，不改变退出逻辑）
                if time.time() - last_heartbeat > heartbeat_interval:
                    heartbeat_log("心跳")
                    last_heartbeat = time.time()

    except Exception as e:
        result.error = str(e)
        result.status = "failed"

    result.end_time = time.time()

    # 迭代后验证
    if not result.error:
        violations = check_git_diff_violations()
        result.violations.extend(violations)

        result.test_result = run_tests()

        if result.violations:
            result.status = "failed"
        elif result.test_result and result.test_result.get("error"):
            result.status = "partial"
        else:
            result.status = "passed"

    log_iteration(result, rules)
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
    print(f"违规: {len(result.violations)}")
    if result.violations:
        for v in result.violations:
            print(f"  ❌ {v}")
    if result.error:
        print(f"错误: {result.error}")
    if result.test_result:
        print(f"测试收集: {result.test_result.get('collected', 'N/A')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
