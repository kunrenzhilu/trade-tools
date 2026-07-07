# Iteration #6 Spec — Harness Reliability & Live Test Isolation

> 日期：2026-07-04  
> Meta-Agent：GLM  
> 输入依据：`iterations/iteration_5/summary.md`、`tmp/gpt_explore.md`、`alignment/iteration_trajectory.md`、`.codebuddy/notes/experience.md`、`alignment/orchestrator.py` 当前实现  
> 风险等级：低到中（只修改开发/验证 harness 与测试隔离；不得修改交易策略、风控阈值、下单逻辑）  
> 核心目标：让 orchestrator 不再产生“假 passed”，让测试统计、默认 pytest、快照留痕可作为后续策略/生产迭代的可信证据。

---

## 1. 背景

Iteration #5 已修复 paper trading 链路中的关键一致性问题，系统距离 paper 稳定性验证更近。但 Iteration #5 的 `result.json` 仍暴露 harness 层问题：

- `status=partial` / `test_result.exit_code=1`，失败原因来自默认 pytest 触发 live IBKR 测试。
- `test_count_before=0`、`test_count_after=0`，而项目实际默认测试数为 562+。
- 早期迭代中 `status=passed` 曾与 `test_result.exit_code=1` 不一致，存在“假 passed”风险。
- `code_diff.patch` 只用 `git diff HEAD`，不会包含 untracked 新文件内容；迭代复现证据不完整。
- `alignment/orchestrator.py` 与 `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py` 存在双副本，修复必须同步。

根据 `.codebuddy/notes/experience.md`：单元测试无法替代集成测试；但默认测试也不能误触真实 broker / Telegram / TWS。live 测试必须显式 opt-in。

---

## 2. Problem Statement

### P0-A：默认 pytest 未隔离 live 集成测试

`mytrader/tests/test_integration_live.py` 直接访问 Alpaca / IBKR / Telegram / TWS，默认 `pytest` 会收集并运行，导致：

- 本地未启动 TWS 时必然失败。
- 可能发送真实 Telegram 测试消息。
- Orchestrator 验证结果被 pre-existing live failure 污染。

### P0-B：orchestrator 状态判定没有严格使用 pytest exit code

当前状态判定只检查 `result.test_result.get("error")`，没有将以下情况判为失败/partial：

- `exit_code != 0`
- `failed > 0`
- `errors > 0`

这会导致“测试失败但迭代 passed/partial 语义不清”。

### P0-C：测试数量统计不可靠

`count_tests()` 通过解析 `pytest --co -q` 中包含 `::` 的行计数，在当前项目记录为 0，无法支撑 Constitution “测试覆盖率不得下降”。

### P0-D：快照与变更文件遗漏 untracked 新文件

`get_changed_files()` / `code_diff.patch` 只基于 `git diff`，遗漏：

- 新增但未 `git add` 的文件
- 新增文件完整内容

导致 `iterations/iteration_N/` 证据不完整。

### P1：缺少机器可读 gate/harness 健康状态

目前 gate 状态主要写在 markdown summary，不能被后续程序稳定读取。至少需要本轮输出一个 `gate_status.json` 或 `harness_health.json`，记录测试隔离、pytest 状态、快照完整性等验证结果。

---

## 3. Scope

### 本次要做

1. 隔离 live 测试：默认 `pytest` 不运行 `tests/test_integration_live.py`，live 测试需显式 `-m live` 或指定文件运行。
2. 修复 `alignment/orchestrator.py` 的状态判定：测试失败不能被记录为 passed。
3. 修复 `count_tests()`：默认统计非 live 测试数量，必须返回真实数量（目标 ≥ 562，具体以当前收集为准）。
4. 修复 `run_tests()`：默认运行非 live 测试，解析 pytest summary 可靠，保存 stdout/stderr tail。
5. 修复变更文件与 snapshot：包含 untracked 文件；新增文件内容必须进入快照证据。
6. 同步修复 `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`。
7. 如修改 monitor git 统计逻辑，同步 `alignment/monitor.py` 与 `.codebuddy/skills/meta-agent/scripts/monitor.py`。
8. 增加 harness 单元测试，覆盖 parser/status/snapshot 边界。
9. 更新 `alignment/iteration_trajectory.md`、`alignment/decision_log.md`（如有模糊决策）、`.codebuddy/CODEBUDDY.md` 与必要设计/说明文档。

### 本次不做

1. 不修改策略逻辑、参数网格、SignalRanker scoring、PortfolioBacktester 交易逻辑。
2. 不修改 DD 20% 阈值、仓位上限、止损止盈、任何风控参数。
3. 不触发真实 Alpaca/IBKR 下单；不要求 live 测试通过。
4. 不做 paper 自动部署；本轮只修 harness 可信度。
5. 不新增第三方依赖。

---

## 4. Detailed Design

## 4.1 live 测试隔离

### 修改文件

- `mytrader/pyproject.toml`
- `mytrader/tests/test_integration_live.py`

### 设计要求

在 `pyproject.toml` 的 `[tool.pytest.ini_options]` 中新增：

```toml
markers = [
    "live: tests that call real broker/notification/network services; skipped by default",
]
addopts = "-q -m 'not live'"
```

注意：如果引号在 TOML 中不兼容，请使用合法 TOML 字符串语法；必须保证运行：

```bash
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest --collect-only -q
/Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -q
```

默认不收集或不运行 live tests。

在 `test_integration_live.py` 顶部（import pytest 后）添加：

```python
pytestmark = pytest.mark.live
```

并更新文件 docstring：默认 pytest 会跳过 live；显式运行方式为：

```bash
python -m pytest tests/test_integration_live.py -m live -v -s
```

### 验收

- `python -m pytest -q` 不运行 IBKR live tests，不发送 Telegram 测试消息。
- `python -m pytest tests/test_integration_live.py -m live -q` 仍可显式运行（可以失败，但必须是显式命令）。

---

## 4.2 pytest summary 解析与测试统计

### 修改文件

- `alignment/orchestrator.py`
- `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`
- 新增或修改 harness 测试文件，例如：`alignment/tests/test_orchestrator_harness.py`

### 新增/修改函数建议

#### `build_pytest_command(*, collect_only: bool = False) -> list[str]`

返回统一 pytest 命令：

```python
def build_pytest_command(*, collect_only: bool = False) -> list[str]:
    cmd = [PYTHON_BIN, "-m", "pytest"]
    if collect_only:
        cmd += ["--collect-only", "-q"]
    else:
        cmd += ["--tb=short", "-q"]
    return cmd
```

默认由 `pyproject.toml` 的 `addopts=-m 'not live'` 隔离 live。也可以在命令中显式加入 `-m`, `not live`，但不能与 pyproject 重复冲突。

#### `parse_pytest_summary(output: str) -> dict[str, int | str]`

必须可靠解析以下格式：

- `562 passed, 103 warnings in 15.70s`
- `562 passed, 5 failed, 103 warnings in 20.1s`
- `1 error, 10 passed in 2.0s`
- `no tests ran in 0.01s`
- pytest stdout 为空但 stderr 有错误

返回至少：

```python
{
    "passed": int,
    "failed": int,
    "errors": int,
    "warnings": int,
    "summary": str,
}
```

注意同时支持 `error` / `errors`、`warning` / `warnings`。

#### `count_tests() -> int`

建议实现顺序：

1. 执行 collect-only 命令。
2. 优先从 stdout/stderr 的 `N tests collected` 或 `N collected` / `N items collected` 解析。
3. 如果 summary 解析不到，再 fallback 统计包含 `::` 的 nodeid 行。
4. 如果命令 exit code 非 0，返回 `-1` 并在调用方记录 error/warning（不要假装 0）。

验收：当前默认收集数必须为真实值，预期 ≥ 562；不能再是 0。

#### `run_tests() -> dict`

返回结构保持兼容，但增强字段：

```python
{
    "passed": int,
    "failed": int,
    "errors": int,
    "warnings": int,
    "exit_code": int,
    "summary": str,
    "stdout_tail": str,
    "stderr_tail": str,
    "command": list[str],
}
```

如果 `subprocess.run` timeout 或异常：

```python
{"error": str(e), "exit_code": -1, "command": cmd}
```

---

## 4.3 状态判定修复

### 修改文件

- `alignment/orchestrator.py`
- `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`

### 新增 helper

```python
def has_test_failures(test_result: dict | None) -> bool:
    if not test_result:
        return True
    if test_result.get("error"):
        return True
    if int(test_result.get("exit_code", 1)) != 0:
        return True
    if int(test_result.get("failed", 0)) > 0:
        return True
    if int(test_result.get("errors", 0)) > 0:
        return True
    return False
```

状态判定顺序建议：

1. `result.error` 已在外层处理为 failed。
2. `result.violations` → `failed`
3. `has_test_failures(result.test_result)` → `failed`
4. 测试数下降且 before > 0 → `failed`
5. `high_risk_files_touched` → `partial`
6. `buffer_overflow_count > 0` → `partial`
7. 其他 → `passed`

验收：构造 `exit_code=1, failed=5` 时状态不能是 `passed`。

---

## 4.4 changed files 与 snapshot 完整性

### 修改文件

- `alignment/orchestrator.py`
- `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`

### `get_changed_files()`

改为基于：

```bash
git status --porcelain
```

解析 tracked modified + untracked，例如：

- ` M mytrader/main.py`
- `A  new.py`
- `?? iterations/iteration_6/spec.md`

返回去重后的相对路径 list。

保留兼容：如果 `git status --porcelain` 失败，fallback 到 `git diff --name-only HEAD`。

### `save_iteration_snapshot()`

保留 `code_diff.patch`，但必须新增至少一个证据文件：

1. `git_status.txt`：完整 `git status --porcelain=v1` 输出。
2. `untracked_files.json`：untracked 文件路径、大小、sha256（或至少路径+大小）。
3. `untracked_files/`：对文本型 untracked 文件保存内容副本，或生成 `untracked_diff.patch`，格式类似：

```diff
diff --git a/path b/path
new file mode 100644
--- /dev/null
+++ b/path
@@
<file content>
```

实现要求：

- 只保存项目内文本文件。
- 跳过 `.codebuddy/teams/`、`__pycache__/`、`.pyc`、大于 1MB 的文件。
- 不保存敏感文件：`.env`、包含 `secret` / `token` / `key` 的文件名。
- 不删除或清理 `.codebuddy/`。

### 监控脚本可选同步

如果 `alignment/monitor.py::_git_info()` 仍只看 `git diff --stat`，可改为 `git status --porcelain` 统计 changed_files，使 monitor 与 orchestrator 一致。若修改，也同步 `.codebuddy/skills/meta-agent/scripts/monitor.py`。

---

## 4.5 gate/harness health JSON

### 修改文件

- `alignment/orchestrator.py`
- `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`

在 `save_iteration_snapshot()` 或新函数中写出：

```text
iterations/iteration_N/gate_status.json
```

本轮至少包含 harness/gate 证据：

```json
{
  "iteration": N,
  "timestamp_utc": "...",
  "status": "passed|failed|partial",
  "tests": {
    "count_before": 562,
    "count_after": 562,
    "passed": 562,
    "failed": 0,
    "errors": 0,
    "exit_code": 0,
    "summary": "562 passed, ..."
  },
  "snapshot": {
    "changed_files_count": 0,
    "includes_untracked": true,
    "git_status_file": "git_status.txt"
  },
  "compliance": {
    "violations": [],
    "high_risk_files_touched": []
  }
}
```

目的：让后续 Meta-Agent 不只依赖 markdown summary。

---

## 4.6 测试计划

新增 `alignment/tests/test_orchestrator_harness.py`（或等价位置），使用 monkeypatch/mock，不启动真实 CodeBuddy、不调用网络、不运行完整 pytest。

至少覆盖：

1. `parse_pytest_summary()`：passed-only / failed / errors / no tests / warnings。
2. `has_test_failures()`：exit_code=1、failed>0、errors>0、error 字段均为 True；exit_code=0 且 failed/errors=0 为 False。
3. `get_changed_files()`：mock `subprocess.run` 返回 porcelain，能解析 `M/A/??`。
4. `count_tests()`：mock collect stdout 的 collected summary，返回真实数量；collect 失败返回 -1。
5. `run_tests()`：mock subprocess result，返回 stdout/stderr tail、command、exit_code。
6. `save_iteration_snapshot()`：在临时 git repo 或 monkeypatch subprocess 输出，验证会写 `result.json`、`git_status.txt`、`gate_status.json`，且 untracked 文件证据存在。

同步副本测试策略：至少对 `alignment/orchestrator.py` 测；再增加一个轻量测试/脚本断言关键 helper 在 `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py` 中存在，或直接对两份模块分别 import 测试。

---

## 5. Success Criteria

1. 默认测试隔离：`python -m pytest -q` 不运行 live tests，且不触发真实 Telegram/IBKR/TWS。
2. 默认 pytest 通过：当前非 live 测试全部通过，预期 `562 passed` 或更多，`exit_code=0`。
3. `count_tests()` 返回真实非 live 测试数，必须 > 0，预期 ≥ 562。
4. 构造 pytest failure 时 orchestrator 状态判定为 `failed`，不能 `passed`。
5. `changed_files` 和 snapshot 包含 untracked 新文件证据。
6. `iterations/iteration_6/result.json` 中测试结果与真实 pytest 一致，不能出现 `exit_code=1` 但 `status=passed`。
7. `iterations/iteration_6/gate_status.json` 生成且包含 tests/snapshot/compliance 字段。
8. 两份 orchestrator 副本保持同步：`alignment/orchestrator.py` 与 `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py` 都包含相同 harness 修复。
9. 更新 `alignment/iteration_trajectory.md`、`.codebuddy/CODEBUDDY.md`；如新增目录/测试文件，文档要反映。

---

## 6. Implementation Order

1. 先读本 spec、`.codebuddy/notes/experience.md`、`alignment/orchestrator.py`、`.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`、`mytrader/pyproject.toml`、`mytrader/tests/test_integration_live.py`。
2. 实现 live 测试隔离，并先跑 collect/default pytest 验证不会触发 live。
3. 在 `alignment/orchestrator.py` 中实现 pytest parser、test failure 判定、changed files、snapshot、gate_status。
4. 将相同修复同步到 `.codebuddy/skills/cb-acp-dev/scripts/orchestrator.py`。
5. 如修改 monitor git 统计，同步两份 monitor。
6. 添加 harness 单元测试。
7. 运行 targeted tests：
   ```bash
   /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest alignment/tests/test_orchestrator_harness.py -q
   ```
8. 运行默认 mytrader tests：
   ```bash
   cd /Users/rickouyang/Github/trade-tools/mytrader
   /Users/rickouyang/miniforge3/envs/py312trade/bin/python -m pytest -q
   ```
9. 运行 orchestrator 自检函数（可用短脚本 import `alignment.orchestrator`，打印 `count_tests()` 和 `run_tests()` summary）。
10. 更新 trajectory / CODEBUDDY / 必要设计文档。

---

## 7. Risk Classification

- **低风险**：测试配置、harness parser、snapshot 留痕、文档更新。
- **中风险**：修改 orchestrator 自身可能影响后续自动迭代，但不影响交易系统运行。
- **禁止越界**：不得修改 `mytrader/mytrader/risk/`、`mytrader/mytrader/execution/` 下交易逻辑；不得触发真实下单；不得删除 `.codebuddy/`。

本轮变更的业务价值不是直接提高收益，而是提高后续所有收益/风险判断的可信度。没有可信 harness，就无法判断策略优化或 paper 结果是否真实。
