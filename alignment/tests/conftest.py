"""pytest 配置：为 alignment/tests 下的测试 stub 掉可选的 acp 依赖。

orchestrator.py 在 import 时会 `from acp import ...`，但 harness 单元测试不依赖 ACP
运行时。本 conftest 在 pytest 收集前注入 acp 的 stub，使 orchestrator 可被直接 import。
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock


def _ensure_acp_stub() -> None:
    if "acp" in sys.modules:
        return
    acp_mod = types.ModuleType("acp")
    acp_mod.PROTOCOL_VERSION = "1.0"  # type: ignore[attr-defined]
    acp_mod.spawn_agent_process = MagicMock(return_value=None)  # type: ignore[attr-defined]
    acp_mod.text_block = lambda x: x  # type: ignore[attr-defined]
    sys.modules["acp"] = acp_mod

    iface_mod = types.ModuleType("acp.interfaces")
    iface_mod.Client = object  # type: ignore[attr-defined]
    sys.modules["acp.interfaces"] = iface_mod


_ensure_acp_stub()
