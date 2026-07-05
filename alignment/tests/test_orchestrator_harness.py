"""Harness 单元测试 — 覆盖 orchestrator.py 的关键 helper 函数。

测试范围（与 iterations/iteration_6/spec.md §4.6 对应）：
1. parse_pytest_summary() — passed-only / failed / errors / no tests / collect-only
2. has_test_failures() — exit_code/failed/errors/error 各分支
3. get_changed_files() — mock subprocess.run 解析 porcelain
4. count_tests() — mock collect 输出，验证 fallback 解析
5. run_tests() — mock subprocess result
6. save_iteration_snapshot() — 验证 result.json / git_status.txt / gate_status.json / untracked 证据

不启动真实 CodeBuddy、不调用网络、不运行完整 pytest。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# 确保 alignment/ 在 sys.path 上（conftest 已 stub acp）
_ALIGN_DIR = Path(__file__).resolve().parent.parent
if str(_ALIGN_DIR) not in sys.path:
    sys.path.insert(0, str(_ALIGN_DIR))

import orchestrator as orch  # noqa: E402  (conftest 已 stub acp)


# ---------------------------------------------------------------------------
# 1. parse_pytest_summary
# ---------------------------------------------------------------------------


class TestParsePytestSummary:
    def test_passed_only_with_warnings(self):
        r = orch.parse_pytest_summary("562 passed, 103 warnings in 15.70s")
        assert r["passed"] == 562
        assert r["failed"] == 0
        assert r["errors"] == 0
        assert r["warnings"] == 103
        assert "562 passed" in r["summary"]

    def test_passed_and_failed_and_warnings(self):
        r = orch.parse_pytest_summary("562 passed, 5 failed, 103 warnings in 20.1s")
        assert r["passed"] == 562
        assert r["failed"] == 5
        assert r["warnings"] == 103

    def test_error_before_passed(self):
        # pytest 8.x: "1 error, 10 passed in 2.0s"
        r = orch.parse_pytest_summary("1 error, 10 passed in 2.0s")
        assert r["errors"] == 1
        assert r["passed"] == 10
        assert r["failed"] == 0

    def test_no_tests_ran(self):
        r = orch.parse_pytest_summary("no tests ran in 0.01s")
        assert r["passed"] == 0
        assert r["failed"] == 0
        assert r["errors"] == 0
        assert "no tests ran" in r["summary"]

    def test_collect_only_deselected(self):
        # `pytest --collect-only` 末尾: "562/578 tests collected (16 deselected) in 1.63s"
        r = orch.parse_pytest_summary("562/578 tests collected (16 deselected) in 1.63s")
        assert r["collected"] == 562

    def test_empty_output(self):
        r = orch.parse_pytest_summary("")
        assert r["passed"] == 0
        assert r["failed"] == 0
        assert r["errors"] == 0
        assert r["warnings"] == 0
        assert r["summary"] == ""

    def test_warning_singular(self):
        # "1 warning" 单数形式也要解析
        r = orch.parse_pytest_summary("5 passed, 1 warning in 0.5s")
        assert r["passed"] == 5
        assert r["warnings"] == 1

    def test_errors_plural(self):
        r = orch.parse_pytest_summary("2 errors, 3 passed in 1.0s")
        assert r["errors"] == 2
        assert r["passed"] == 3


# ---------------------------------------------------------------------------
# 2. has_test_failures
# ---------------------------------------------------------------------------


class TestHasTestFailures:
    def test_none_is_failure(self):
        assert orch.has_test_failures(None) is True

    def test_error_field_is_failure(self):
        assert orch.has_test_failures({"error": "boom", "exit_code": 0}) is True

    def test_nonzero_exit_code_is_failure(self):
        assert orch.has_test_failures({"exit_code": 1, "failed": 0, "errors": 0}) is True

    def test_failed_positive_is_failure(self):
        assert orch.has_test_failures({"exit_code": 0, "failed": 5, "errors": 0}) is True

    def test_errors_positive_is_failure(self):
        assert orch.has_test_failures({"exit_code": 0, "failed": 0, "errors": 2}) is True

    def test_clean_is_not_failure(self):
        assert orch.has_test_failures({"exit_code": 0, "failed": 0, "errors": 0}) is False

    def test_missing_fields_default_to_failure(self):
        # 缺少 exit_code → 默认 1 → 视为失败
        assert orch.has_test_failures({}) is True


# ---------------------------------------------------------------------------
# 3. get_changed_files (porcelain parsing)
# ---------------------------------------------------------------------------


class _FakeCompletedProcess:
    """模拟 subprocess.run 返回对象。"""

    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class TestGetChangedFiles:
    def test_parses_modified_added_untracked(self, monkeypatch):
        porcelain = (
            " M mytrader/main.py\n"
            "A  alignment/new_module.py\n"
            "?? iterations/iteration_6/spec.md\n"
            " M mytrader/tests/test_x.py\n"
        )
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=porcelain, returncode=0),
        )
        files = orch.get_changed_files()
        assert "mytrader/main.py" in files
        assert "alignment/new_module.py" in files
        assert "iterations/iteration_6/spec.md" in files
        assert "mytrader/tests/test_x.py" in files

    def test_dedupes_same_file(self, monkeypatch):
        # 同一文件 staged + working 均有变更，只出现一次
        porcelain = "MM mytrader/main.py\n"
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=porcelain, returncode=0),
        )
        files = orch.get_changed_files()
        assert files == ["mytrader/main.py"]

    def test_rename_uses_destination(self, monkeypatch):
        porcelain = "R  old_path.py -> new_path.py\n"
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=porcelain, returncode=0),
        )
        files = orch.get_changed_files()
        assert files == ["new_path.py"]

    def test_quoted_path_unwrapped(self, monkeypatch):
        # 路径含空格时 git 包引号
        porcelain = '?? "mytrader/path with space/file.py"\n'
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=porcelain, returncode=0),
        )
        files = orch.get_changed_files()
        assert files == ["mytrader/path with space/file.py"]

    def test_fallback_to_diff_on_failure(self, monkeypatch):
        # git status rc=1 → fallback 到 git diff --name-only HEAD
        def fake_run(cmd, **kwargs):
            if "status" in cmd:
                return _FakeCompletedProcess(returncode=1, stderr="boom")
            # diff fallback
            return _FakeCompletedProcess(stdout="mytrader/fallback.py\n", returncode=0)

        monkeypatch.setattr("orchestrator.subprocess.run", fake_run)
        files = orch.get_changed_files()
        assert files == ["mytrader/fallback.py"]

    def test_all_fail_returns_empty(self, monkeypatch):
        def raising_run(cmd, **kwargs):
            raise RuntimeError("git not found")

        monkeypatch.setattr("orchestrator.subprocess.run", raising_run)
        files = orch.get_changed_files()
        assert files == []


# ---------------------------------------------------------------------------
# 4. count_tests
# ---------------------------------------------------------------------------


class TestCountTests:
    def test_collect_only_summary_parsed(self, monkeypatch):
        output = (
            "tests/test_a.py: 20\n"
            "tests/test_b.py: 14\n"
            "562/578 tests collected (16 deselected) in 1.63s\n"
        )
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=output, returncode=0),
        )
        assert orch.count_tests() == 562

    def test_nodeid_fallback(self, monkeypatch):
        # 无 summary，但有 `::` nodeid 行
        output = (
            "tests/test_a.py::test_one\n"
            "tests/test_a.py::test_two\n"
            "tests/test_b.py::test_three\n"
        )
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=output, returncode=0),
        )
        assert orch.count_tests() == 3

    def test_per_file_count_fallback(self, monkeypatch):
        # pytest 8.x `-q --collect-only` 输出格式
        output = (
            "tests/test_alpaca_broker.py: 20\n"
            "tests/test_strategy.py: 49\n"
            "tests/test_backtest.py: 14\n"
        )
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=output, returncode=0),
        )
        assert orch.count_tests() == 83  # 20 + 49 + 14

    def test_per_file_ignores_site_packages_warnings(self, monkeypatch):
        # stderr 中 site-packages 警告 `__init__.py:6` 不应被计入
        output = (
            "tests/test_a.py: 20\n"
            "tests/test_b.py: 14\n"
        )
        stderr = (
            "/Users/.../miniforge3/envs/py312trade/lib/python3.12/site-packages/"
            "websockets/legacy/__init__.py:6\n"
            "  DeprecationWarning: websockets.legacy is deprecated\n"
        )
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(
                stdout=output, stderr=stderr, returncode=0
            ),
        )
        assert orch.count_tests() == 34  # 20 + 14，不含 site-packages 行

    def test_nonzero_exit_returns_minus_one(self, monkeypatch):
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(returncode=1, stderr="err"),
        )
        assert orch.count_tests() == -1

    def test_subprocess_exception_returns_minus_one(self, monkeypatch):
        def raising_run(cmd, **kwargs):
            raise RuntimeError("timeout")
        monkeypatch.setattr("orchestrator.subprocess.run", raising_run)
        assert orch.count_tests() == -1


# ---------------------------------------------------------------------------
# 5. run_tests
# ---------------------------------------------------------------------------


class TestRunTests:
    def test_parses_typical_success(self, monkeypatch):
        stdout = "................. 562 passed, 103 warnings in 15.70s\n"
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=stdout, returncode=0),
        )
        r = orch.run_tests()
        assert r["passed"] == 562
        assert r["failed"] == 0
        assert r["errors"] == 0
        assert r["warnings"] == 103
        assert r["exit_code"] == 0
        assert "562 passed" in r["summary"]
        assert "command" in r
        assert isinstance(r["command"], list)
        assert r["stdout_tail"] == stdout  # short enough to fit

    def test_parses_failures(self, monkeypatch):
        stdout = "FF... 5 failed, 557 passed, 103 warnings in 20.0s\n"
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=stdout, returncode=1),
        )
        r = orch.run_tests()
        assert r["passed"] == 557
        assert r["failed"] == 5
        assert r["exit_code"] == 1

    def test_exception_returns_error_dict(self, monkeypatch):
        def raising_run(cmd, **kwargs):
            raise RuntimeError("timeout 300s")
        monkeypatch.setattr("orchestrator.subprocess.run", raising_run)
        r = orch.run_tests()
        assert "error" in r
        assert r["exit_code"] == -1
        assert "timeout" in r["error"]
        assert r["passed"] == 0
        assert r["failed"] == 0

    def test_stdout_tail_truncated(self, monkeypatch):
        # 确保 stdout_tail 不会无限增长
        long_stdout = "x" * 5000 + "\n5 passed in 1.0s\n"
        monkeypatch.setattr(
            "orchestrator.subprocess.run",
            lambda *args, **kwargs: _FakeCompletedProcess(stdout=long_stdout, returncode=0),
        )
        r = orch.run_tests()
        assert len(r["stdout_tail"]) <= 2000


# ---------------------------------------------------------------------------
# 6. save_iteration_snapshot
# ---------------------------------------------------------------------------


def _make_result(
    status: str = "passed",
    changed_files: list[str] | None = None,
    test_result: dict | None = None,
) -> orch.IterationResult:
    """构造一个用于测试的 IterationResult。"""
    return orch.IterationResult(
        iteration_id="test123",
        task="harness test",
        start_time=1000.0,
        end_time=1005.0,
        status=status,
        updates_count=0,
        text_responses=["hello"],
        tool_calls=[],
        team_events=[],
        permission_requests=[],
        changed_files=changed_files or [],
        violations=[],
        high_risk_files_touched=[],
        test_result=test_result or {"passed": 5, "failed": 0, "errors": 0, "warnings": 0, "exit_code": 0, "summary": "5 passed"},
        test_count_before=5,
        test_count_after=5,
    )


class TestSaveIterationSnapshot:
    def test_writes_result_json_and_gate_status(self, tmp_path, monkeypatch):
        monkeypatch.setattr(orch, "ITERATIONS_DIR", tmp_path)
        # save_iteration_snapshot 使用 get_next_iteration_number() - 1 作为 iter_num
        # mock 返回 100，则实际 iter_num = 99
        monkeypatch.setattr(orch, "get_next_iteration_number", lambda: 100)
        # git diff HEAD 返回空
        def fake_run(cmd, **kwargs):
            if "diff" in cmd:
                return _FakeCompletedProcess(stdout="(empty)", returncode=0)
            if "status" in cmd:
                return _FakeCompletedProcess(stdout="", returncode=0)
            return _FakeCompletedProcess(stdout="", returncode=0)
        monkeypatch.setattr("orchestrator.subprocess.run", fake_run)

        result = _make_result()
        orch.save_iteration_snapshot(result)

        snap = tmp_path / "iteration_99"
        assert (snap / "result.json").exists()
        assert (snap / "gate_status.json").exists()
        assert (snap / "git_status.txt").exists()
        assert (snap / "prompt_template.md").exists()
        assert (snap / "full_response.md").exists()
        assert (snap / "code_diff.patch").exists()

        # gate_status.json 内容校验
        gate = json.loads((snap / "gate_status.json").read_text())
        assert gate["iteration"] == 99
        assert gate["status"] == "passed"
        assert gate["tests"]["passed"] == 5
        assert gate["tests"]["has_test_failures"] is False
        assert gate["snapshot"]["changed_files_count"] == 0
        assert "compliance" in gate
        assert "timestamp_utc" in gate

        # result.json 内容校验
        rj = json.loads((snap / "result.json").read_text())
        assert rj["iteration_id"] == "test123"
        assert rj["status"] == "passed"

    def test_captures_untracked_files(self, tmp_path, monkeypatch):
        """untracked 新文件必须进入 git_status.txt + untracked_files.json + untracked_diff.patch。"""
        # 准备一个真实的 untracked 文件
        untracked_path = tmp_path.parent / "iteration_test_untracked_sample.py"
        untracked_path.write_text("# untracked sample\nx = 1\n", encoding="utf-8")
        try:
            # 模拟 git status 输出包含该 untracked 文件
            porcelain = f"?? {untracked_path.name}\n"
            monkeypatch.setattr(orch, "ITERATIONS_DIR", tmp_path)
            monkeypatch.setattr(orch, "PROJECT_ROOT", untracked_path.parent)

            def fake_run(cmd, **kwargs):
                if "diff" in cmd:
                    return _FakeCompletedProcess(stdout="(empty)", returncode=0)
                if "status" in cmd:
                    return _FakeCompletedProcess(stdout=porcelain, returncode=0)
                return _FakeCompletedProcess(stdout="", returncode=0)
            monkeypatch.setattr("orchestrator.subprocess.run", fake_run)
            monkeypatch.setattr(orch, "get_next_iteration_number", lambda: 101)

            result = _make_result(changed_files=[untracked_path.name])
            orch.save_iteration_snapshot(result)

            snap = tmp_path / "iteration_100"
            assert (snap / "git_status.txt").exists()
            assert "?? iteration_test_untracked_sample.py" in (
                snap / "git_status.txt"
            ).read_text()

            untracked_json = snap / "untracked_files.json"
            assert untracked_json.exists(), "untracked_files.json 必须存在"
            entries = json.loads(untracked_json.read_text())
            assert len(entries) == 1
            assert entries[0]["path"] == "iteration_test_untracked_sample.py"
            assert entries[0]["sha256"] is not None
            assert entries[0]["sensitive"] is False

            diff_patch = snap / "untracked_diff.patch"
            assert diff_patch.exists(), "untracked_diff.patch 必须存在"
            patch_content = diff_patch.read_text()
            assert "diff --git" in patch_content
            assert "new file mode 100644" in patch_content
            assert "+x = 1" in patch_content
        finally:
            untracked_path.unlink(missing_ok=True)

    def test_skips_sensitive_untracked_files(self, tmp_path, monkeypatch):
        """敏感文件（.env / token / key）只记录路径，不读内容。"""
        sensitive_path = tmp_path / ".env"
        sensitive_path.write_text("SECRET=abc123\n", encoding="utf-8")
        try:
            porcelain = "?? .env\n"
            monkeypatch.setattr(orch, "ITERATIONS_DIR", tmp_path)
            monkeypatch.setattr(orch, "PROJECT_ROOT", tmp_path)

            def fake_run(cmd, **kwargs):
                if "diff" in cmd:
                    return _FakeCompletedProcess(stdout="(empty)", returncode=0)
                if "status" in cmd:
                    return _FakeCompletedProcess(stdout=porcelain, returncode=0)
                return _FakeCompletedProcess(stdout="", returncode=0)
            monkeypatch.setattr("orchestrator.subprocess.run", fake_run)
            monkeypatch.setattr(orch, "get_next_iteration_number", lambda: 102)

            result = _make_result(changed_files=[".env"])
            orch.save_iteration_snapshot(result)

            snap = tmp_path / "iteration_101"
            entries = json.loads((snap / "untracked_files.json").read_text())
            assert len(entries) == 1
            assert entries[0]["sensitive"] is True
            assert entries[0]["sha256"] is None

            # 不应生成 untracked_diff.patch（无内容可写）
            diff_patch = snap / "untracked_diff.patch"
            assert not diff_patch.exists(), "敏感文件不应被写入 patch"
        finally:
            sensitive_path.unlink(missing_ok=True)

    def test_gate_status_reflects_failed_tests(self, tmp_path, monkeypatch):
        """构造 failed>0 → has_test_failures=True，status=failed。"""
        monkeypatch.setattr(orch, "ITERATIONS_DIR", tmp_path)

        def fake_run(cmd, **kwargs):
            if "diff" in cmd:
                return _FakeCompletedProcess(stdout="(empty)", returncode=0)
            if "status" in cmd:
                return _FakeCompletedProcess(stdout="", returncode=0)
            return _FakeCompletedProcess(stdout="", returncode=0)
        monkeypatch.setattr("orchestrator.subprocess.run", fake_run)
        monkeypatch.setattr(orch, "get_next_iteration_number", lambda: 103)

        failed_result = {
            "passed": 557,
            "failed": 5,
            "errors": 0,
            "warnings": 0,
            "exit_code": 1,
            "summary": "5 failed, 557 passed",
        }
        result = _make_result(status="failed", test_result=failed_result)
        orch.save_iteration_snapshot(result)

        snap = tmp_path / "iteration_102"
        gate = json.loads((snap / "gate_status.json").read_text())
        assert gate["status"] == "failed"
        assert gate["tests"]["failed"] == 5
        assert gate["tests"]["exit_code"] == 1
        assert gate["tests"]["has_test_failures"] is True


# ---------------------------------------------------------------------------
# 7. 两份 orchestrator 副本同步检查
# ---------------------------------------------------------------------------


_CB_ACP_DEV_COPY = (
    Path(__file__).resolve().parent.parent.parent
    / ".codebuddy"
    / "skills"
    / "cb-acp-dev"
    / "scripts"
    / "orchestrator.py"
)


class TestOrchestratorSync:
    """验证 alignment/orchestrator.py 与 .codebuddy/skills/cb-acp-dev/scripts/orchestrator.py
    保持同步（spec §5.8）。
    """

    def test_cb_acp_dev_copy_exists(self):
        assert _CB_ACP_DEV_COPY.exists(), f"cb-acp-dev 副本不存在: {_CB_ACP_DEV_COPY}"

    def test_key_helpers_present_in_both(self):
        """两份文件都应包含本轮新增的关键 helper。"""
        required_helpers = [
            "def build_pytest_command(",
            "def parse_pytest_summary(",
            "def has_test_failures(",
            "def count_tests(",
            "def run_tests(",
            "def _collect_untracked_files(",
            "def _build_untracked_diff(",
            "def _write_gate_status(",
        ]
        align_src = orch.__file__
        # alignment 副本
        align_content = Path(align_src).read_text(encoding="utf-8")
        for h in required_helpers:
            assert h in align_content, f"alignment 副本缺少 helper: {h}"

        # cb-acp-dev 副本
        if _CB_ACP_DEV_COPY.exists():
            cb_content = _CB_ACP_DEV_COPY.read_text(encoding="utf-8")
            for h in required_helpers:
                assert h in cb_content, f"cb-acp-dev 副本缺少 helper: {h}"

    def test_two_copies_are_identical(self):
        """两份 orchestrator.py 应字节级一致（marker-based path detection 让它们可同步）。"""
        if not _CB_ACP_DEV_COPY.exists():
            pytest.skip("cb-acp-dev 副本不存在")
        align_content = Path(orch.__file__).read_text(encoding="utf-8")
        cb_content = _CB_ACP_DEV_COPY.read_text(encoding="utf-8")
        assert align_content == cb_content, (
            "alignment/orchestrator.py 与 .codebuddy/skills/cb-acp-dev/scripts/orchestrator.py "
            "内容不一致；请使用 `cp alignment/orchestrator.py "
            ".codebuddy/skills/cb-acp-dev/scripts/orchestrator.py` 同步。"
        )
