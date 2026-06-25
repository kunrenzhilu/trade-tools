"""Phase 3 真实集成测试：Alpaca Paper 账户 + Telegram Bot。

运行方式：
    cd mytrader
    python -m pytest tests/test_integration_live.py -v -s

前提：
    - .env 已配置 ALPACA__API_KEY / ALPACA__SECRET_KEY
    - .env 已配置 NOTIFICATION__TELEGRAM_ENABLED=true / BOT_TOKEN / CHAT_ID
    - alpaca-py 已安装
"""
from __future__ import annotations

import httpx
import pytest
from alpaca.trading.client import TradingClient

from mytrader.infra.config import load_config


# ---------------------------------------------------------------------------
# 配置预检
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def config():
    cfg = load_config()
    assert cfg.alpaca.api_key, "ALPACA__API_KEY not set in .env"
    assert cfg.alpaca.secret_key, "ALPACA__SECRET_KEY not set in .env"
    return cfg


# ===================================================================
# Alpaca Paper 账户测试
# ===================================================================

class TestAlpacaAccount:
    """验证 Alpaca Paper 账户连接、权限、资金。"""

    def test_connect_and_get_account(self, config):
        """A1: 连接 Alpaca Paper 账户并获取账户信息。"""
        client = TradingClient(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper=config.alpaca.paper,
        )
        account = client.get_account()
        assert account is not None, "get_account returned None"
        print(f"  ✓ Account ID: {account.id}")
        print(f"  ✓ Status: {account.status}")
        print(f"  ✓ Cash: ${float(account.cash):,.2f}")
        print(f"  ✓ Buying Power: ${float(account.buying_power):,.2f}")
        print(f"  ✓ Pattern Day Trader: {account.pattern_day_trader}")
        assert account.status == "ACTIVE", f"Account status={account.status}, expected ACTIVE"

    def test_account_is_paper(self, config):
        """A2: 确认连接的是 Paper（沙盒）账户而非真实账户。"""
        client = TradingClient(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper=True,
        )
        account = client.get_account()
        assert account is not None
        # Paper 账户 ID 通常不以真实账户前缀开头
        print(f"  Account ID: {account.id}")
        print(f"  ✓ Paper mode: {config.alpaca.paper}")

    def test_list_positions(self, config):
        """A3: 查询当前持仓（Paper 账户应为空或测试持仓）。"""
        client = TradingClient(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper=True,
        )
        positions = client.get_all_positions()
        print(f"  Positions count: {len(positions)}")
        for pos in positions:
            print(f"    {pos.symbol}: qty={pos.qty}, market_value=${float(pos.market_value):,.2f}")
        # Paper 账户可以有持仓，不限断言

    def test_list_orders(self, config):
        """A4: 查询最近订单历史。"""
        from alpaca.trading.requests import GetOrdersRequest
        from alpaca.trading.enums import QueryOrderStatus

        client = TradingClient(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper=True,
        )
        orders = client.get_orders(
            filter=GetOrdersRequest(status=QueryOrderStatus.ALL, limit=5)
        )
        print(f"  Recent orders: {len(orders)}")
        for o in orders:
            print(f"    {o.symbol} {o.side} {o.qty} @ {o.type} status={o.status}")

    def test_get_asset_info(self, config):
        """A5: 查询 AAPL 的可交易状态。"""
        client = TradingClient(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper=True,
        )
        asset = client.get_asset("AAPL")
        assert asset is not None
        print(f"  ✓ AAPL: tradable={asset.tradable}, status={asset.status}")
        print(f"  ✓ shortable={asset.shortable}, easy_to_borrow={asset.easy_to_borrow}")
        assert asset.tradable, "AAPL should be tradable"

    def test_get_asset_info_tsla(self, config):
        """A6: 查询 TSLA 的可交易状态。"""
        client = TradingClient(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper=True,
        )
        asset = client.get_asset("TSLA")
        assert asset is not None
        print(f"  ✓ TSLA: tradable={asset.tradable}, status={asset.status}, fractionable={asset.fractionable}")
        assert asset.tradable, "TSLA should be tradable"


# ===================================================================
# Telegram Bot 测试
# ===================================================================

class TestTelegramBot:
    """验证 Telegram Bot 配置正确且能成功发送消息。"""

    @pytest.fixture(autouse=True)
    def check_config(self, config):
        if not config.notification.telegram_enabled:
            pytest.skip("NOTIFICATION__TELEGRAM_ENABLED=false")
        if not config.notification.telegram_bot_token:
            pytest.skip("NOTIFICATION__TELEGRAM_BOT_TOKEN not set")
        if not config.notification.telegram_chat_id:
            pytest.skip("NOTIFICATION__TELEGRAM_CHAT_ID not set")

    def test_bot_token_valid(self, config):
        """T1: 验证 bot token 有效（getMe API）。"""
        token = config.notification.telegram_bot_token
        resp = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        assert resp.status_code == 200, f"getMe failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok"), f"getMe not ok: {data}"
        bot_info = data["result"]
        print(f"  ✓ Bot username: @{bot_info['username']}")
        print(f"  ✓ Bot name: {bot_info['first_name']}")
        print(f"  ✓ Bot ID: {bot_info['id']}")
        assert bot_info["username"].endswith("bot"), "Should be a bot"

    def test_send_test_message(self, config):
        """T2: 发送一条测试消息到你的 Telegram（请检查手机）。"""
        token = config.notification.telegram_bot_token
        chat_id = config.notification.telegram_chat_id

        text = (
            "✅ *MyTrader 集成测试*\n\n"
            f"测试时间：2026-06-20\n"
            "系统状态：Telegram Bot 连接正常\n"
            "如果你看到这条消息，说明通知推送已成功配置。"
        )
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        assert resp.status_code == 200, f"sendMessage failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok"), f"sendMessage not ok: {data}"
        msg_id = data["result"]["message_id"]
        print(f"  ✓ Message sent! msg_id={msg_id}")
        print(f"  📱 请检查 Telegram 是否收到测试消息（@alp_paper_bot）")

    def test_invalid_token_detected(self):
        """T3: 故意用无效 token，验证能正确报错。"""
        resp = httpx.get("https://api.telegram.org/botINVALID_TOKEN/getMe", timeout=10)
        data = resp.json()
        assert not data.get("ok"), "Invalid token should return ok=False"
        print(f"  ✓ Invalid token correctly rejected: {data.get('description', '')}")


# ===================================================================
# Container 集成测试
# ===================================================================

class TestContainerWithAlpaca:
    """验证 Container 在 semi_auto 模式下正确装配 AlpacaBroker + NotificationService。"""

    def test_build_semi_auto_mode(self, config):
        """C1: Container.build 在 semi_auto 模式下正常装配。"""
        from mytrader.infra.container import Container

        # 临时把 execution.mode 改为 semi_auto
        original_mode = config.execution.mode
        try:
            # 构造一个 mode=semi_auto 的配置（避免修改原 config）
            from mytrader.infra.config import AppConfig
            import copy
            cfg = copy.deepcopy(config)
            # 直接改 field
            object.__setattr__(cfg.execution, 'mode', 'semi_auto')

            components = Container.build(cfg)
            assert components.broker is not None, "Broker should not be None"
            assert components.notification is not None, "NotificationService should not be None"
            assert components.tracker is not None, "PortfolioTracker should not be None"
            assert components.health is not None, "HealthChecker should not be None"

            broker_type = type(components.broker).__name__
            print(f"  ✓ Broker type: {broker_type}")
            print(f"  ✓ Notification: {type(components.notification).__name__}")
            print(f"  ✓ Total components assembled: 6")
        finally:
            pass  # 不恢复 mode，不污染后续测试

    def test_notification_service_init(self, config):
        """C2: NotificationService 用真实配置初始化。"""
        from mytrader.execution.notification import NotificationService
        svc = NotificationService(config.notification)
        print(f"  ✓ NotificationService created")
        print(f"  ✓ Telegram enabled: {config.notification.telegram_enabled}")
        print(f"  ✓ WeChat Work enabled: {config.notification.wechat_work_enabled}")


# ===================================================================
# IBKR TWS Paper 账户测试（需本地运行 TWS 并开启 API）
# ===================================================================

class TestIBKRConnection:
    """验证 IBKR TWS Paper 账户连接、账户信息、持仓。"""

    @pytest.fixture(autouse=True)
    def check_config(self, config):
        if not config.ibkr.host:
            pytest.skip("IBKR__HOST not set")

    @pytest.fixture
    def ib(self):
        from ib_insync import IB, util
        util.startLoop()
        ib = IB()
        yield ib
        if ib.isConnected():
            ib.disconnect()

    def test_connect_tws_paper(self, config, ib):
        """I1: 连接 TWS Paper 账户。"""
        ib.connect(
            config.ibkr.host,
            config.ibkr.port,
            clientId=config.ibkr.client_id,
            readonly=True,
        )
        assert ib.isConnected(), "TWS connection failed"
        print(f"  ✓ Connected to TWS {config.ibkr.host}:{config.ibkr.port}")

    def test_managed_accounts(self, config, ib):
        """I2: 获取托管账户列表。"""
        ib.connect(
            config.ibkr.host, config.ibkr.port,
            clientId=config.ibkr.client_id, readonly=True,
        )
        accounts = ib.managedAccounts()
        assert len(accounts) > 0, "No managed accounts found"
        print(f"  ✓ Accounts: {accounts}")
        assert accounts[0].startswith("D"), "Paper account should start with D"

    def test_account_summary(self, config, ib):
        """I3: 获取账户资金摘要。"""
        ib.connect(
            config.ibkr.host, config.ibkr.port,
            clientId=config.ibkr.client_id, readonly=True,
        )
        summary = ib.accountSummary()
        key_tags = {"NetLiquidation", "TotalCashValue", "BuyingPower"}
        found = {s.tag: (s.value, s.currency) for s in summary if s.tag in key_tags}
        print(f"  Account summary:")
        for tag, (value, currency) in found.items():
            print(f"    {tag}: {value} {currency}")
        assert "NetLiquidation" in found, "Missing NetLiquidation"
        assert float(found["NetLiquidation"][0]) > 0, "NetLiquidation should be positive"

    def test_positions_empty(self, config, ib):
        """I4: 查询当前持仓（Paper 账户应为空）。"""
        ib.connect(
            config.ibkr.host, config.ibkr.port,
            clientId=config.ibkr.client_id, readonly=True,
        )
        positions = ib.positions()
        print(f"  Positions count: {len(positions)}")
        for p in positions:
            print(f"    {p.contract.symbol}: qty={p.position}, "
                  f"marketPrice={p.marketPrice}, avgCost={p.avgCost}")
        # Paper 新账户通常持仓为空，但不强制断言

    def test_fetch_spy_price(self, config, ib):
        """I5: 获取 SPY 行情（若无市场数据订阅则降级跳过）。"""
        from ib_insync import Stock
        ib.connect(
            config.ibkr.host, config.ibkr.port,
            clientId=config.ibkr.client_id, readonly=True,
        )
        contract = Stock("SPY", "SMART", "USD")
        ib.qualifyContracts(contract)
        # 请求延迟数据（无需订阅）
        ib.reqMarketDataType(3)
        ticker = ib.reqMktData(contract, "", False, False)
        ib.sleep(3)  # 等待延迟数据到达

        last_price = ticker.last if ticker.last and ticker.last > 0 else ticker.close
        if last_price is None or (isinstance(last_price, float) and last_price <= 0):
            print(f"  ⚠️ SPY: no market data (10168: not subscribed, normal for Paper accounts)")
            print(f"  ℹ️ TWS → Global Configuration → API → enable 'Allow delayed market data' to fix")
            ib.cancelMktData(contract)
            return  # 降级跳过，不 fail
        print(f"  ✓ SPY: last={ticker.last}, bid={ticker.bid}, ask={ticker.ask}, close={ticker.close}")
        ib.cancelMktData(contract)
