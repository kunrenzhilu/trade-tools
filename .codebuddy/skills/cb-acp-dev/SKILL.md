---
name: cb-acp-dev
description: "Orchestrator skill for driving another CodeBuddy instance to develop code via the ACP (Agent Client Protocol). This skill should be used when the user wants to delegate development tasks to CodeBuddy as the primary developer while the current session (GLM) acts as a monitor/supervisor — ensuring ai_constitution compliance, tracking iteration progress, and optionally triggering Agent Teams for parallel research. Triggers include phrases like '让 codebuddy 开发', '启动迭代', '监控 codebuddy', '用 acp 调用 codebuddy', 'agent teams 并行调研', 'orchestrator', or any request to run a supervised development loop on the mytrader project."
---

# cb-acp-dev — CodeBuddy ACP Orchestrator

## Overview

Drive a separate CodeBuddy instance (via `codebuddy --acp`) to perform development iterations on the mytrader project, while the current session monitors its behavior, validates outputs against `ai_constitution.md`, and logs results to `iteration_trajectory.md`.

## Architecture

```
GLM (this session, Orchestrator/Monitor)
  │
  ├── Load ai_constitution.md → extract rules (forbidden actions, risk levels)
  ├── Define iteration task
  │
  ├── ACP (JSON-RPC over stdio)
  │   └── spawn_agent_process("codebuddy", "--acp", "--permission-mode", "bypassPermissions")
  │       ├── conn.initialize() → protocol handshake
  │       ├── conn.new_session() → create work session
  │       ├── conn.prompt() → send task + constitution rules
  │       └── session_update callback → real-time events:
  │             ├── text responses
  │             ├── tool calls (codebuddy.ai/toolName)
  │             ├── team events (codebuddy.ai/teamUpdate, codebuddy.ai/memberEvent)
  │             └── agent phase (codebuddy.ai/agentPhase)
  │
  ├── Post-iteration validation
  │   ├── git diff → check for forbidden code patterns
  │   ├── pytest → verify test count and pass rate
  │   └── compliance check → Constitution violations
  │
  └── Logging
      ├── alignment/iteration_trajectory.md
      └── alignment/decision_log.md
```

## When To Use

- User wants CodeBuddy to perform a development task on mytrader (code changes, new features, refactoring)
- User wants to run a supervised iteration loop with Constitution compliance checking
- User wants parallel research via Agent Teams (multiple CodeBuddy members investigating different modules)
- User asks to "let CodeBuddy do it" or "start an iteration"

## Workflow

### Step 1: Load Context

Read the following files to establish context:

1. `alignment/ai_constitution.md` — extract forbidden actions, high/low risk change categories, validation pipeline requirements
2. `alignment/iteration_trajectory.md` — get the last iteration number and lessons learned
3. `.codebuddy/CODEBUDDY.md` — current project state and phase progress

### Step 2: Define Iteration Task

Determine the specific task for this iteration. Tasks should be:
- **Scoped**: One clear deliverable (e.g., "implement AlpacaBroker auto mode", not "build Phase 6")
- **Verifiable**: Has a clear pass/fail criteria (tests pass, code compiles, file exists)
- **Risk-classified**: Low risk (auto-deploy) or high risk (needs user approval per Constitution L8)

### Step 3: Run Orchestrator

Execute the orchestrator script with the task:

```bash
# Short task (< 30 min): run directly
/Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py \
    --task "具体任务描述" \
    --max-turns 50 \
    --timeout 1800

# Long task (> 30 min): run in background
nohup /Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py \
    --task "具体任务描述" \
    --max-turns 100 \
    --timeout 86400 \
    > /tmp/orchestrator.log 2>&1 &

# With parallel Agent Teams research
/Users/rickouyang/miniforge3/envs/py312trade/bin/python alignment/orchestrator.py \
    --task "重构信号过滤器" \
    --team-research \
    --timeout 3600
```

Key parameters:
- `--task`: The development task description (required)
- `--max-turns`: Max agent turns (default 50, increase for complex tasks)
- `--timeout`: Max runtime in seconds (default 300, increase for long tasks)
- `--team-research`: Trigger CodeBuddy to create an Agent Team for parallel research

### Step 4: Monitor

During execution, the orchestrator captures all `session_update` events:
- **Text responses**: CodeBuddy's outputs and explanations
- **Tool calls**: Which tools CodeBuddy invoked (Read, Write, Bash, etc.)
- **Team events**: If Agent Teams are used, track `teamUpdate` and `memberEvent`
- **Permission requests**: Tools that needed permission (auto-approved in bypassPermissions mode)

For long-running background tasks, periodically check the log:
```bash
tail -50 /tmp/orchestrator.log
```

### Step 5: Post-Iteration Validation

After the iteration completes, verify:

1. **Test suite**: Run `pytest` in `mytrader/` — test count should not decrease, all tests should pass
2. **Git diff compliance**: Check changed files for forbidden patterns (RL imports, black-box strategies, DD threshold changes)
3. **Documentation sync**: Verify `CODEBUDDY.md` and design docs are updated if architecture changed
4. **Trajectory log**: Verify `alignment/iteration_trajectory.md` has a new entry

### Step 6: Report

Summarize results to the user:
- Iteration status (passed / failed / partial)
- What CodeBuddy produced (files changed, tests added)
- Any Constitution violations detected
- Recommendation for next iteration

## Agent Teams

CodeBuddy can autonomously create Agent Teams when instructed via the prompt. The orchestrator's `--team-research` flag appends a team creation instruction.

**Verified behavior** (tested 2026-06-30):
- CodeBuddy calls `TeamCreate` via `DeferExecuteTool`
- Creates team with named members (e.g., `backtest-explorer`, `signal-explorer`)
- Members work in parallel, communicate via `send_message`
- Team events are pushed through `_meta['codebuddy.ai/teamUpdate']` and `_meta['codebuddy.ai/memberEvent']`
- CodeBuddy sends `shutdown_request` to members when done, waits for `shutdown_response`

**Requirement**: Must use `--permission-mode bypassPermissions`, otherwise `TeamCreate` permission is denied.

## Key Technical Details

### ACP Communication

- **Protocol**: JSON-RPC 2.0 over stdio (ndJSON stream, one JSON object per line)
- **SDK**: `agent-client-protocol` Python package (v0.10.1)
- **Connection**: `spawn_agent_process()` starts a new `codebuddy --acp` subprocess
- **Each run is a fresh CodeBuddy instance**: No cross-iteration context; state is passed via files (`iteration_trajectory.md`, code itself)

### Permission Handling

The ACP client must return the correct permission response format:

```python
# ❌ Wrong (causes deny)
return {"outcome": {"outcome": "approved"}}

# ✅ Correct (select an allow option from the options list)
for opt in options:
    if 'allow' in opt.kind:
        return {"outcome": {"outcome": "selected", "optionId": opt.optionId}}
```

Or simply use `--permission-mode bypassPermissions` to skip permission prompts entirely.

### Constitution Compliance Rules

Extracted from `ai_constitution.md`:

**Forbidden (12 items)**:
1. Break max drawdown 20% constraint
2. Deploy strategies without full validation pipeline
3. Merge code when tests fail
4. Produce unexplainable trading decisions (black box)
5. Over-engineer for uncertain future requirements
6. Major architecture changes without re-interview
7. Introduce unsafe third-party dependencies
8. Silently execute major decisions (must notify via Telegram Bot)
9. Decrease test coverage
10. Leave stale code/tests uncleaned
11. Documentation out of sync with code
12. Introduce RL in production (not in early/mid stage)

**Validation Pipeline**: Backtest (≥5 years) → Walk-Forward (4 rounds) → Paper Trade (≥1 month) → Live

**High-risk changes** (require user approval): risk param changes, execution logic, validation thresholds, new Alpha sources, major refactors, cash/leverage changes

## Resources

### scripts/
- `orchestrator.py` — Main orchestrator script. Run via `python alignment/orchestrator.py --task "..."`. Requires `agent-client-protocol` package installed.

### references/
- `orchestrator_design.md` — Full design document with architecture diagrams, ACP protocol details, and compliance check rules.
