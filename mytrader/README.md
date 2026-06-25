# MyTrader — 全自动量化交易系统

> 面向美股（S&P 500 + Nasdaq 100），每日扫描 515 只标的，数据驱动选出 Top-5 信号，纸面/半自动/全自动执行。

---

## 架构概览

```
离线回测层（每月 Walk-Forward）
  MarketDataStore → MatrixBacktest(N策略×6组×参数网格) → strategy_weights.json

在线交易层（每日 16 次扫描）
  DataSyncService → MarketDataStore → UniverseManager(515只分组)
    → StrategyMatrixRunner(信号有效期3bar)
    → SignalRanker(Top-2K候选)
    → CandidateSelector(5级约束递补选Top-5)
    → SignalFilter → RiskManager → AlpacaBroker/PaperBroker
```

---

## 环境要求

- **Python 3.12+**（pandas-ta 兼容性要求）
- **操作系统**：macOS / Linux
- **包管理器**：conda（推荐 miniforge）或 venv
- **约 100MB 磁盘空间**（数据库 + 代码 + 依赖）

---

## 快速开始（从零部署）

### 1. 克隆代码

```bash
git clone <your-repo-url> mytrader
cd mytrader
```

### 2. 创建 Python 环境

```bash
conda create -n py312trade python=3.12 -y
conda activate py312trade
pip install -e ".[dev,brokers,dashboard]"
```

或者用已有环境只装依赖：

```bash
pip install -e ".[dev,brokers,dashboard]"
```

### 3. 配置 .env

```bash
cp .env.example .env
# 编辑 .env，填入你的 Alpaca API Key 和 Telegram Bot Token
```

必需的环境变量：

```bash
# Alpaca 美股 API（去 https://alpaca.markets 注册 Paper Trading 账号）
ALPACA__API_KEY=PKXXXXXXXXXX
ALPACA__SECRET_KEY=xxxxxxxxxx
ALPACA__PAPER=true

# 执行模式
EXECUTION__MODE=semi_auto     # paper | semi_auto | auto

# Telegram 通知（可选但 semi_auto 模式强烈建议）
NOTIFICATION__TELEGRAM_ENABLED=true
NOTIFICATION__TELEGRAM_BOT_TOKEN=xxxxx
NOTIFICATION__TELEGRAM_CHAT_ID=xxxxx
```

### 4. 首次初始化（约 10 分钟）

```bash
# 4a. 回填 5 年历史数据（515 只 × 5 年，约 5-10 分钟，需网络）
python main.py --backfill

# 4b. 矩阵回测产出策略权重
python main.py --reoptimize
```

### 5. 验证

```bash
# 干跑检查（确认配置 + API 连接）
python main.py --mode semi_auto --dry-run

# 立即执行一次扫描（验证信号链路）
python main.py --mode paper --scan-now morning
```

---

## 日常操作

### 半自动模式（推荐先用这个）

信号触发后会通过 Telegram 推送给你确认，不下单：

```bash
python main.py --mode semi_auto
```

### Paper 模式（仅模拟成交，不连 Alpaca）

```bash
python main.py --mode paper
```

### 全自动模式（信号直连 Alpaca 下单）

```bash
# 确保 --mode semi_auto 观察一周行为正常后再切
python main.py --mode auto
```

### 调试命令

```bash
# 立即执行一次盘前扫描（不启动调度器）
python main.py --mode paper --scan-now morning

# 盘中扫描
python main.py --mode paper --scan-now intraday

# 只检查配置
python main.py --mode paper --dry-run

# 手动重优化策略权重
python main.py --reoptimize
```

### 运行测试

```bash
# 全部单元测试
python -m pytest --ignore=tests/test_integration_live.py

# 端到端干跑验证（不真实下单）
python examples/phase5_e2e.py
```

---

## 调度任务（ET 时区）

系统启动后自动注册以下定时任务：

| 时间 | 任务 | 说明 |
|------|------|------|
| 09:35 | 盘前扫描 | 生成当日信号并下单 |
| 10:00-14:59 每30min | 盘中扫描 | 更新信号 |
| 15:45 | 收盘前检查 | 检查止损/止盈 |
| 16:30 | 盘后对账 + 数据同步 | 更新本地库 |
| 每月首个交易日 00:00 | Walk-Forward 重优化 | 更新策略权重 |

---

## 目录结构

```
mytrader/
├── main.py                  # 启动入口
├── pyproject.toml           # 依赖声明
├── config/
│   ├── default.yaml         # 默认配置（可提交 Git）
│   ├── strategy_weights.json # 矩阵回测产出（每月更新）
│   └── universe.csv         # S&P 500 + Nasdaq 100 成分股
├── .env                     # 敏感配置（不提交 Git）
├── mytrader/                # 源码
│   ├── data/store/          # MarketDataStore + DataSyncService
│   ├── universe/            # UniverseManager（成分股+分组）
│   ├── strategy/            # 策略引擎 + MatrixRunner
│   ├── signal/              # SignalFilter + SignalRanker
│   ├── risk/                # RiskManager + CandidateSelector
│   ├── backtest/            # BacktestRunner + MatrixBacktest
│   ├── execution/           # alpaca_broker + ibkr_broker
│   ├── portfolio/           # PortfolioTracker + Reconciliation
│   ├── infra/               # Config / Container / Scheduler
│   └── monitor/             # 健康检查 + Streamlit Dashboard
├── tests/                   # 单元测试（457 个）
├── designs/design_v2/       # 设计文档（当前版本 v2.1）
├── doc/                     # 开发总结（phase1-5）
└── examples/
    └── phase5_e2e.py        # 端到端干跑脚本
```

**数据文件**（不提交 Git，自动生成）：

| 文件 | 说明 |
|------|------|
| `~/.mytrader/market_data.db` | 本地时序库（515只×5年日线，~80MB） |
| `~/.mytrader/cache/` | 旧版 Parquet 缓存（v1 遗留） |

---

## 迁移到新服务器

```bash
# 1. 新环境安装
git clone <repo> && cd mytrader
conda create -n py312trade python=3.12 -y && conda activate py312trade
pip install -e ".[dev,brokers,dashboard]"

# 2. 复制配置
# 从旧服务器复制 .env 文件（含 API Key），或新建
scp old-server:~/mytrader/.env .

# 3. 复制数据文件（可选，也可以重新 --backfill）
scp old-server:~/.mytrader/market_data.db ~/.mytrader/
scp old-server:~/mytrader/config/strategy_weights.json config/
scp old-server:~/mytrader/config/universe.csv config/

# 4. 验证
python main.py --mode semi_auto --dry-run
```

---

## 常见问题

### .env 中的 API Key 没有被读取？

确认 `.env` 在项目根目录（与 `main.py` 同级），且格式为 `PREFIX__FIELD=VALUE`（双下划线）。

### 0 signals 是不是坏了？

不一定。双均线等趋势策略的信号频率很低（几个月才交叉一次）。可以先跑这一行确认数据链路正常：

```bash
python main.py --mode paper --scan-now morning
```

看到 `Phase5 Scan done: 515 symbols → N raw signals` 就说明链路正常。N 每天不同。

### 矩阵回测太慢？

515 只 × 4 策略 × 参数网格，离线运行约 5-10 分钟，因为是每月一次，完全可接受。

### 想减少扫描标的？

编辑 `config/universe.csv`，只保留你感兴趣的标的。或通过环境变量指定：
```bash
WATCHLIST__SYMBOLS='["AAPL","TSLA","NVDA"]'
```
但这样就降级到 Phase 4 的单策略模式了。

---

## 开发

```bash
# 运行测试
python -m pytest --ignore=tests/test_integration_live.py

# 代码格式化
ruff format .

# 设计文档
open designs/design_v2/00-overview.md
```

开发原则见 `.codebuddy/notes/experience.md`。
