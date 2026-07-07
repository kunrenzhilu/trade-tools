"""迭代 #1 — 通过 ACP 驱动 CodeBuddy 对 mytrader 进行完整迭代"""
import asyncio
import json
import time
from pathlib import Path
from uuid import uuid4

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.interfaces import Client

PROJECT_ROOT = Path("/Users/rickouyang/Github/trade-tools")
MYTRADER_ROOT = PROJECT_ROOT / "mytrader"
TEMPLATE_FILE = PROJECT_ROOT / "tmp" / "iteration_template.md"


class IterationClient(Client):
    def __init__(self):
        self.all_updates = []
        self.text_chunks = []
        self.tool_calls = []
        self.team_events = []
        self.errors = []

    async def request_permission(self, options, session_id, tool_call, **kwargs):
        tool_name = "unknown"
        if hasattr(tool_call, "name"):
            tool_name = tool_call.name
        elif isinstance(tool_call, dict):
            tool_name = tool_call.get("name", "unknown")
        print(f"  [权限] 批准: {tool_name}")

        if options:
            for opt in options:
                d = opt.model_dump() if hasattr(opt, "model_dump") else opt
                if "allow" in d.get("kind", ""):
                    return {"outcome": {"outcome": "selected", "optionId": d.get("optionId", "")}}
        return {"outcome": {"outcome": "cancelled"}}

    async def session_update(self, session_id, update, **kwargs):
        if hasattr(update, "model_dump"):
            d = update.model_dump()
        else:
            d = update
        self.all_updates.append(d)

        # 提取文本
        for chunk in self._extract_text(d):
            self.text_chunks.append(chunk)
            # 实时打印较长的文本片段
            if len(chunk) > 20:
                print(f"  [text] {chunk[:200]}")

        # 提取工具调用
        meta = d.get("field_meta") or {}
        tool_name = meta.get("codebuddy.ai/toolName")
        if tool_name:
            self.tool_calls.append({"tool": tool_name, "time": time.time()})
            print(f"  [tool] {tool_name}")

        # 提取团队事件
        for key in meta:
            if "team" in key.lower() or "member" in key.lower():
                self.team_events.append({"key": key, "value": meta[key]})
                print(f"  [team] {key}: {json.dumps(meta[key], ensure_ascii=False)[:200]}")

        # 检查错误
        if "error" in str(d).lower()[:200]:
            phase = meta.get("codebuddy.ai/agentPhase", {}).get("phase", "")
            if phase == "error" or "error" in str(d)[:100].lower():
                self.errors.append(str(d)[:500])

    @staticmethod
    def _extract_text(obj, depth=0):
        if depth > 6:
            return
        if isinstance(obj, dict):
            if obj.get("type") in ("text", "text_delta"):
                if obj.get("text"):
                    yield obj["text"]
            for v in obj.values():
                yield from IterationClient._extract_text(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                yield from IterationClient._extract_text(item, depth + 1)


async def main():
    # 读取模板
    template = TEMPLATE_FILE.read_text(encoding="utf-8")

    print("=" * 60)
    print("迭代 #1 — mytrader 系统迭代")
    print(f"Prompt 长度: {len(template)} 字符")
    print("=" * 60)

    client = IterationClient()

    try:
        async with spawn_agent_process(
            client,
            "codebuddy",
            "--acp",
            "--permission-mode", "bypassPermissions",
            "--max-turns", "80",
            cwd=str(MYTRADER_ROOT),
        ) as (conn, proc):
            print(f"\n[启动] CodeBuddy PID={proc.pid}")

            # 初始化
            result = await conn.initialize(protocol_version=PROTOCOL_VERSION)
            print(f"[初始化] 协议版本={result.protocol_version}")

            # 创建会话
            session = await conn.new_session(
                cwd=str(MYTRADER_ROOT),
                mcp_servers=[],
            )
            print(f"[会话] {session.session_id}")

            # 发送完整迭代任务
            print(f"\n[发送] 迭代任务 prompt...")
            await conn.prompt(
                session_id=session.session_id,
                prompt=[text_block(template)],
                message_id=str(uuid4()),
            )
            print(f"[发送完成] 等待 CodeBuddy 执行...\n")

            # 等待执行（最多 30 分钟）
            timeout = 1800
            elapsed = 0
            last_update_count = 0
            while elapsed < timeout:
                await asyncio.sleep(10)
                elapsed += 10

                # 打印进度
                if len(client.all_updates) != last_update_count:
                    last_update_count = len(client.all_updates)
                    tools_so_far = len(client.tool_calls)
                    texts_so_far = len(client.text_chunks)
                    print(f"  [{elapsed//60}m{elapsed%60:02d}s] 更新:{last_update_count} 工具:{tools_so_far} 文本块:{texts_so_far}")

                # 如果 2 分钟没有新更新，认为可能已完成
                if elapsed % 120 == 0 and elapsed > 0:
                    recent = len(client.all_updates) - last_update_count
                    if recent == 0 and elapsed > 300:
                        print(f"  [{elapsed//60}m] 2分钟无新更新，可能已完成")
                        break

    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()

    # 结果汇总
    print("\n" + "=" * 60)
    print("迭代 #1 结果汇总")
    print("=" * 60)
    print(f"总更新数: {len(client.all_updates)}")
    print(f"工具调用数: {len(client.tool_calls)}")
    print(f"文本块数: {len(client.text_chunks)}")
    print(f"团队事件数: {len(client.team_events)}")
    print(f"错误数: {len(client.errors)}")

    # 打印工具调用列表
    if client.tool_calls:
        print(f"\n工具调用列表:")
        for i, tc in enumerate(client.tool_calls):
            print(f"  [{i+1}] {tc['tool']}")

    # 打印完整文本响应（最后 2000 字符）
    full_text = "".join(client.text_chunks)
    print(f"\n完整响应 (最后 2000 字符):")
    print(f"...{full_text[-2000:]}")

    # 保存完整响应到文件
    output_file = PROJECT_ROOT / "tmp" / "iteration_1_response.md"
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(full_text, encoding="utf-8")
    print(f"\n完整响应已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
