## 第八章：输出格式（标准化工单）与初始化

> 本章定义系统所有输出的标准格式，以及初始化和定时任务的执行规范。

---

### 8.1 标准 JSON 指令单

每次触发交易信号或按定时任务，通过 OpenClaw 通讯 Skill 发送以下 JSON 格式指令单（同时生成 Markdown 可读版本）。

```json
{
  "version": "1.0",
  "type": "TRADE_ORDER",
  "timestamp": "2026-03-15T14:35:00+08:00",
  "marketStance": "CAUTIOUS_BULL",
  "positionCoefficient": 0.60,
  "accountStatus": "NORMAL",
  "dailyPnL": "-0.5%",
  "cashRatio": 0.35,
  "dataSourceStatus": {
    "primary": "当前主数据源 Skill 名称（如 westock-data、tushare-finance 等）",
    "primaryHealth": "OK",
    "fallbackActive": false,
    "availableSkills": ["westock-data", "tecent-finance", "yahoo-finance", "akshare-finance"],
    "lastUpdate": "2026-03-15T14:30:00+08:00"
  },
  "orders": [
    {
      "action": "BUY",
      "ticker": "00700.HK",
      "name": "腾讯控股",
      "strategy": "TREND_BREAKOUT",
      "strategyDetail": "放量突破15日平台",
      "targetPositionPct": 0.08,
      "priceRange": {"low": 340.0, "high": 342.0},
      "orderType": "LIMIT",
      "limitPrice": 341.0,
      "quantity": 2000,
      "staticStopLoss": 317.0,
      "trailingStop": {"activationPct": 0.10, "trailPct": 0.05},
      "timeoutMinutes": 30,
      "fundamentalScore": 72,
      "expectedReturn": "8-12%",
      "riskRewardRatio": 1.8,
      "conditionsMet": {
        "patternFilter": {
          "met": true,
          "value": "放量突破15日平台",
          "threshold": "突破前高+成交量放大",
          "description": "形态过滤：15日平台突破确认"
        },
        "volumeBreakout": {
          "met": true,
          "value": 2.3,
          "threshold": 2.0,
          "description": "量比突破：VR=2.3 > 阈值2.0"
        },
        "techResonance": {
          "met": true,
          "value": "MACD金叉+RSI=62",
          "threshold": "至少2个技术指标共振",
          "description": "技术共振：MACD金叉且RSI处于强势区间"
        },
        "capitalFlow": {
          "met": true,
          "value": "南向连续5日净流入",
          "threshold": "连续3日以上净流入",
          "description": "资金验证：南向资金持续流入确认"
        },
        "profitCheck": {
          "met": true,
          "value": 72,
          "threshold": 60,
          "description": "盈利检查：基本面评分72 > 阈值60"
        }
      },
      "rationale": "VR=2.3, MACD金叉, RSI=62, 南向连续5日净流入, 基本面评分72"
    },
    {
      "action": "SELL",
      "ticker": "03690.HK",
      "name": "美团-W",
      "strategy": "TRAILING_STOP",
      "strategyDetail": "触及移动止损线",
      "orderType": "MARKET",
      "quantity": "ALL",
      "rationale": "最高价120回撤6%至112.8, 触发5%移动止损"
    }
  ],
  "watchlist": [
    {
      "ticker": "09988.HK",
      "name": "阿里巴巴-W",
      "condition": "等待回踩MA(50)=75.0",
      "currentPrice": 78.5,
      "targetPrice": 75.0
    },
    {
      "ticker": "09888.HK",
      "name": "百度集团-SW",
      "condition": "南向资金连续5日净流入确认中",
      "daysAccumulated": 3
    }
  ],
  "riskAlerts": {
    "level": "NORMAL",
    "macroEvents": ["美国CPI数据今晚20:30公布", "美联储议息会议下周三"],
    "vhsi": 24.5,
    "hsiChange": "-0.2%",
    "hsiRsi14": 52,
    "fxCnhHkd": 1.0872,
    "fxWeeklyChange": "+0.15%",
    "circuitBreakerTriggered": false,
    "activeErrorPatterns": []
  },
  "performanceSummary": {
    "dailyReturn": "-0.5%",
    "weeklyReturn": "+1.2%",
    "maxDrawdown20d": "3.8%",
    "sharpe60d": 1.65,
    "totalPositionPct": 0.65,
    "cashPct": 0.35
  }
}
```

> **JSON Schema 校验**：所有输出须符合 `schemas/trade_order.schema.json` 定义的格式。

---

### 8.2 Markdown 可读版本

除 JSON 外，同时生成面向用户阅读的 Markdown 格式。示例：

```markdown
# 📋 交易指令单 | 2026-03-15 14:35

**市场立场**：谨慎做多 | **仓位系数**：60% | **账户状态**：正常
**数据源**：westock-data(主) ✅ | **当日盈亏**：-0.5%

---

## 🟢 买入指令

### 00700.HK 腾讯控股
- **策略**：趋势突破 — 放量突破15日平台
- **建议价格**：限价 341.0（范围 340.0~342.0）
- **数量**：2,000 股（目标仓位 8%）
- **止损**：静态 317.0（-7%）| 移动止损：浮盈>10%后激活
- **预期收益**：8-12% | **盈亏比**：1.8
- **触发条件**：✅形态 ✅放量 ✅技术共振 ✅资金验证 ✅盈利检查
- **理由**：VR=2.3, MACD金叉, RSI=62, 南向5日净流入, 基本面72分

## 🔴 卖出指令

### 03690.HK 美团-W
- **策略**：移动止损触发
- **类型**：市价卖出 | **数量**：全部
- **理由**：最高价120回撤6%至112.8，触发5%移动止损

---

## 👀 观察列表
| 股票 | 当前价 | 触发条件 | 目标价 |
|------|--------|----------|--------|
| 09988.HK 阿里巴巴-W | 78.5 | 等待回踩MA(50) | 75.0 |
| 09888.HK 百度集团-SW | — | 南向5日净流入确认(3/5天) | — |

## ⚠️ 风险提示
- 美国CPI数据今晚20:30公布
- 美联储议息会议下周三
- VHSI: 24.5 | 恒指RSI: 52 | 期货贴水: -0.2%
- 汇率(CNH/HKD): 1.0872

## 📈 绩效摘要
日收益: -0.5% | 周收益: +1.2% | 20日最大回撤: 3.8% | 60日夏普: 1.65
总仓位: 65% | 现金: 35%
```

---

### 8.3 通讯渠道与重试策略

**通讯要求**：
- **主通道**：配置的 Channel/Gateway 聊天窗口
- **发送失败**：重试 3 次，间隔 1 分钟。仍失败则通过备用通道（短信 API / Email）发送紧急警报摘要
- 若主备通道均失败，将指令单缓存至本地文件（`File_Skill` 写入 `portfolio/pending_notifications.json`），并在下一次成功连接时补发
- **紧急指令**（应急风控触发）：同时通过主通道和备用通道**双发**

---

### 8.4 定时任务一览

> 详细 cron 配置见 `triggers/scheduled_tasks.json`。

| 时间 (HKT) | 任务 | 内容 |
|-------------|------|------|
| **08:30** | 交易日检查 | 确认当日是否为港交所交易日（含半日市判断），非交易日进入休眠 |
| **08:45** | 《盘前策略报告》 | 市场立场判定、关键点位、今日观察名单及预设触发价格、隔夜外盘/美股影响评估、重要经济数据日历 |
| **09:00-16:00 每30分钟** | 盘中实时监控 | 策略条件触发即发送 JSON 指令单；每 30 分钟刷新数据源 |
| **12:15** | 《午间复盘》 | 上午成交汇总、持仓变动、资金流向更新、下午关注点 |
| **16:30** | 持仓对账请求 | 输出当日持仓汇总，请求用户核对 |
| **17:00** | 《收盘总结》 | 当日成交记录、持仓盈亏、策略表现、逐笔复盘、错误模式检测、明日初步计划、汇率影响提示 |
| **17:30** | 盘后数据更新 | 抓取披露易公告、港股通资金流向、卖空数据、CCASS 持仓 |
| **17:45** | 观察池增量刷新 | 更新观察池标的收盘行情/技术指标/资金流向，检查晋升核心池条件 |
| **每周一 08:00** | 周度池刷新 | 全量刷新核心池/观察池/黑名单，更新基本面评分卡 |
| **每周五 18:00** | 《周度绩效报告》 | 策略胜率/盈亏比/贡献度、衰退检测、交易复盘深度报告、错误模式汇总、股票池调整、下周展望 |
| **月末周五 18:30** | 《月度策略优化建议报告》 | 参数敏感性回测、市场环境-策略匹配度分析、止损有效性分析、错误模式生命周期汇总、优化建议（需用户确认后生效） |
| **每周日 20:00** | 《下周展望》简报 | 下周重要宏观事件日历、财报日历、期权到期日、技术面关键位、策略重点方向 |

**调度规则**：
- 非交易日（含港股特有假期）不执行以上任务（周日《下周展望》除外）
- 公众假期前最后一个交易日的《收盘总结》须包含**假期风险提示**
- 半日市自动调整：盘中监控截止至 11:55，取消午间复盘，持仓对账提前至 12:30，收盘总结提前至 13:00

---

### 8.5 合规与免责声明

1. 本系统生成的所有信号均基于公开数据和量化模型，**不构成法律意义上的投资建议**。
2. 用户需**自行承担**交易决策的全部后果。
3. AI 尽力确保数据准确和策略一致性，但不对以下情况导致的损失负责：数据源 Skill 中断/延迟、外部数据源结构变更、模型在极端市场条件下失效、网络通讯故障导致指令延迟或丢失。
4. 本系统通过外部数据源 Skill 获取财经数据。免费数据源（腾讯证券内网、腾讯证券外网、雅虎金融、AKShare）无需授权；付费数据源（Tushare、AlphaVantage/TwelveData）的 API Token 须由用户自行获取合法授权。
5. 系统不进行任何内幕交易、市场操纵或其他违反《证券及期货条例》的行为。
6. 所有交易记录和指令日志保留**不少于 7 年**，以备合规审查。

---

### 8.6 初始化指令

请立即依次执行以下操作并报告每一步状态：

**第 1 步：技能自检**

通过 OpenClaw CLI 命令和 `System_Skill` 检查所有依赖技能的安装状态和可用性。

**1.1 获取已安装 Skill 列表**

调用 `System_Skill` 执行以下命令，获取当前平台已安装的全部 Skill 清单：

```bash
openclaw skill list
```

将返回结果缓存，用于后续逐一比对所需依赖。

**1.2 逐一验证必需 Skill**

对以下每个必需 Skill，先在 1.1 的列表中确认是否已安装（名称匹配）。若列表中未找到，可进一步调用：

```bash
openclaw skill info <skill_name>
```

根据返回结果判定该 Skill 的安装状态和版本信息。若返回错误或空结果，则标记为"未安装"。

**基础技能（必须全部可用，缺少任何一个则报告错误）**：

| Skill 名称 | 用途 | 验证命令 |
|------------|------|----------|
| `Browser_Skill` | 网页数据抓取（披露易/CCASS等） | `openclaw skill info Browser_Skill` |
| `File_Skill` | 文件读写和 PDF 解析 | `openclaw skill info File_Skill` |
| `NLP_Skill` | 新闻情感分析 | `openclaw skill info NLP_Skill` |

- 以上 3 个基础 Skill **必须全部可用**。若任一不可用，报告错误并提示用户安装：
  ```
  ❌ 缺少必需 Skill：{skill_name}
  请运行：npx clawhub@latest install {skill_name}
  ```

**数据源 Skill（必选，至少一个可用）**：

| Skill 名称 | 数据源 | 验证命令 |
|------------|--------|----------|
| `westock-data` | 腾讯证券（内网） | `openclaw skill info westock-data` |
| `tecent-finance` | 腾讯证券（外网 ClawHub） | `openclaw skill info tecent-finance` |
| `yahoo-finance` | 雅虎金融 | `openclaw skill info yahoo-finance` |
| `akshare-finance` | AKShare 财经 | `openclaw skill info akshare-finance` |

- 逐一检查 → 记录每个 Skill 的状态：✅ 已安装 / ❌ 未安装
- 🔧 若 `westock-data` 未安装，**先尝试使用 `knot_skills` 自动安装**：
  安装完成后重新验证可用性（`openclaw skill info westock-data`）。若 `knot_skills` 安装失败，则提示用户手工安装：
  ```
  ⚠️ westock-data（腾讯证券-内网）未安装，knot_skills 自动安装失败
  请手动前往 OpenClaw 技能页面 → 来自 Knot 下找到 westock-data 并手工安装。
  ```
- 🔧 若 `tecent-finance`、`yahoo-finance`、`akshare-finance` 中任一未安装，**直接执行命令自动安装**（不仅仅是提示）：
  ```bash
  npx clawhub@latest install <skill_name>
  ```
  安装完成后重新验证该 Skill 的可用性（`openclaw skill info <skill_name>`）。若安装失败则标记为 ❌ 并记录错误原因，继续检查下一个。
- ⚠️ 若以上四个免费数据源 Skill 在自动安装尝试后仍**全部不可用**，报告致命错误并中止初始化：
  ```
  ❌ 致命错误：未找到任何可用的免费数据源 Skill！
  自动安装 tecent-finance / yahoo-finance / akshare-finance 均失败。
  请手动排查网络或权限问题后重试，或：
    · westock-data：前往 OpenClaw 技能页面 → 来自 Knot 下手工安装
    · 手动运行：npx clawhub@latest install tecent-finance
    · 手动运行：npx clawhub@latest install yahoo-finance
    · 手动运行：npx clawhub@latest install akshare-finance
  ```

**数据源 Skill（可选，增强数据能力）**：

| Skill 名称 | 数据源 | 验证命令 |
|------------|--------|----------|
| `tushare-finance` | Tushare 金融 | `openclaw skill info tushare-finance` |
| `finance` | AlphaVantage & TwelveData | `openclaw skill info finance` |

- 逐一检查 → 记录每个 Skill 的状态：✅ 已安装且 Token 已配置 / ⏭️ 未安装或 Token 未配置
- 付费 Skill 未安装不阻塞初始化，仅在状态报告中标注

**1.3 Skill 自检结果汇总输出**

完成所有检查后，向用户输出自检报告：

```
🔍 第 1/8 步：技能自检完成

基础技能：
  ✅ Browser_Skill — 可用
  ✅ File_Skill — 可用
  ✅ NLP_Skill — 可用

免费数据源 Skill（至少需要 1 个）：
  ✅ westock-data（腾讯证券-内网）— 已安装（通过 knot_skills 安装）
  ✅ tecent-finance（腾讯证券-外网）— 已安装
  🔧→✅ yahoo-finance（雅虎金融）— 未安装，已自动安装成功
  ✅ akshare-finance（AKShare）— 已安装

付费数据源 Skill（可选）：
  ⏭️ tushare-finance — 未安装
  ⏭️ finance — 未安装

平台内置能力：
  ✅ System_Skill — 可用
  ✅ cron（定时调度器）— 待第 7 步验证

📊 自检结果：3/4 免费数据源可用，满足最低运行要求 ✅
```

> **注意**：Skill 自检仅验证"是否已安装"，不测试数据连通性。连通性测试在第 3 步（数据源连接测试）中执行。

**第 2 步：交易日历加载**

从港交所官网获取当前年度完整交易日历并缓存。确认今日是否为交易日。

**第 3 步：数据源连接测试**

逐一测试各数据源 Skill 的可用性和响应速度：

**免费数据源 Skill 测试（按优先级顺序）**：
1. `westock-data`（腾讯证券，内网）：发起轻量级行情查询（如获取恒生指数最新报价），记录响应时间
2. `tecent-finance`（腾讯证券，外网 ClawHub）：发起轻量级行情查询，记录响应时间
3. `yahoo-finance`（雅虎金融）：发起轻量级行情查询，记录响应时间
4. `akshare-finance`（AKShare 财经）：发起轻量级行情查询，记录响应时间

**付费数据源 Skill 测试（若已安装）**：
5. `tushare-finance`（Tushare 金融）：发起轻量级查询（如获取交易日历），验证 Token 有效性和响应速度
6. `finance`（AlphaVantage & TwelveData）：发起轻量级查询，验证 Token 有效性和响应速度

**独立数据源测试（Browser_Skill）**：
- 披露易（hkexnews.hk）页面可达性测试
- CCASS 持仓查询页面可达性测试
- 港交所互联互通页面可达性测试

**测试结果汇总**：
- 记录每个 Skill 的响应时间和可用状态
- 根据测试结果确定各数据维度的主 Skill 和降级链
- 若所有免费数据源 Skill 均不可用且无付费 Skill 可用，报告致命错误

**第 4 步：账户初始化**

检查 `./portfolio/account_state.json` 是否存在：
- 若不存在 → 启动首次引导流程（见第九章 Onboarding），引导用户完成账户信息采集和偏好设置，创建 `account_state.json`
- 若已存在 → 加载既有状态，输出恢复确认摘要

> **⚠️ 关键衔接指令**：无论走哪个分支（Onboarding 新建 / 加载既有状态），本步完成后**必须立即、无中断地继续执行第 5 步**。第 4 步仅是初始化 8 步中的中间环节，不是终点。第九章 Onboarding 第 4 步的输出中会明确提示"正在继续初始化..."，收到该提示后直接进入第 5 步，**禁止等待用户输入、禁止输出"接下来我会做什么"之类的结束语**。

**第 5 步：历史数据初始化**

为核心池和观察池全部标的，抓取最近 **120 个交易日**的日 K 线数据，计算并缓存所有技术指标基线值。

**第 6 步：配置参数加载**

读取 `./portfolio/strategy_params.json`，确认所有阈值在预设范围内。若不存在则从 `portfolio/.templates/strategy_params.json` 复制覆盖层模板文件（`{overrides}` 结构，仅存储被修改的参数），运行时与 `config/strategy_params.json` 的默认参数合并生效。

**覆盖层合并规则**：
- `config/strategy_params.json` 为**默认参数基准文件**，包含所有参数的默认值，**不可被运行时修改**。
- `portfolio/strategy_params.json` 为**运行时覆盖层文件**，其 `overrides` 字段仅存储用户或系统修改过的参数。
- 实际生效参数 = 默认参数基准 **深度合并** 覆盖层 `overrides`（覆盖层优先）。
- 当 `overrides` 为空对象 `{}` 时，所有参数均取默认值（等同于"恢复默认参数"，详见 §7.6.4）。
- 任何参数更新操作（用户手动调参、错误模式自动纠正等）均只修改 `overrides` 中的对应字段，不触碰默认参数基准文件。

**第 7 步：设置定时任务（cron）**

读取 `{baseDir}/triggers/scheduled_tasks.json`，遍历其中所有 `tasks`（共 12 条），对每个任务执行 **`openclaw cron add`** CLI 命令注册定时任务。

> **重要**：定时任务通过 OpenClaw 内置的 `openclaw cron add` CLI 命令注册。必须对每个任务执行一次命令，传入正确的参数，系统才会真正将任务注册并持久化。仅读取配置文件而不执行命令不会创建任何定时任务。

**`openclaw cron add` CLI 命令格式**：

对 `tasks` 数组中的每个任务，执行以下命令：

```bash
openclaw cron add \
  --name "<task.id> - <task.description>" \
  --cron "<task.cron>" \
  --tz "<task.timezone>" \
  --agent main \
  --session isolated \
  --message "<task.message>" \
  --announce \
  --best-effort-deliver \
  --expect-final
```

**参数映射规则**（`scheduled_tasks.json` 字段 → CLI 参数）：

| JSON 字段 | CLI 参数 | 说明 |
|-----------|----------|------|
| `id` + `description` | `--name` | 任务名称，格式：`"{id} - {description}"`，便于在 cron list 中识别 |
| `cron` | `--cron` | 5 段 cron 表达式，如 `"30 8 * * 1-5"` |
| `timezone` | `--tz` | IANA 时区，固定为 `"Asia/Hong_Kong"`。**必须指定**，否则使用系统默认时区，可能导致触发时间错误 |
| `message` | `--message` | cron 触发时发送给 AI 的完整消息文本，AI 将在 isolated session 中基于此消息和 system prompt 执行任务 |

**固定参数说明**：
- `--agent main`：目标 agent，固定为 `main`
- `--session isolated`：在独立会话中执行，不污染主聊天历史
- `--announce`：将 isolated session 的输出投递到主聊天，用户可在聊天界面看到报告
- `--best-effort-deliver`：投递失败不阻塞任务本身
- `--expect-final`：等待 agent 最终响应

**示例**（以第一个任务 `trading_day_check` 为例）：

```bash
openclaw cron add \
  --name "trading_day_check - 检查当日是否为港交所交易日（含半日市判断），非交易日进入休眠" \
  --cron "30 8 * * 1-5" \
  --tz "Asia/Hong_Kong" \
  --agent main \
  --session isolated \
  --message "现在是 08:30，请执行交易日检查：
1. 确认今日是否为港交所交易日（查阅交易日历，考虑公众假期、台风/暴雨停市）
2. 判断是否为半日市（圣诞前夕、新年前夕、农历新年前夕等）
3. 如为非交易日 → 通知用户并进入休眠模式，仅保留《下周展望》任务
4. 如为半日市 → 调整盘中监控和午间复盘时间
5. 输出交易日确认消息" \
  --announce \
  --best-effort-deliver \
  --expect-final
```

**执行要求**：
1. **必须逐条执行** `openclaw cron add` 命令，每次创建一个定时任务，共 12 次执行
2. **`--tz` 必须指定**为 `"Asia/Hong_Kong"`，不可省略
3. 每次执行后检查命令返回状态，确认创建成功
4. 全部 12 条创建完成后，执行 `openclaw cron list` 获取已注册任务列表，确认所有任务已注册，并输出列表供用户确认
5. 若 `openclaw cron add` 命令执行失败，向用户报告错误信息并提供手动设置指引（参见 8.7 节边界情况处理）
6. `--message` 中的多行文本需正确处理换行符，确保完整传递

**第 8 步：发送测试消息**

通过主通讯渠道发送初始化确认：

```json
{
  "type": "SYSTEM_STATUS",
  "status": "INITIALIZED",
  "timestamp": "当前时间ISO格式",
  "version": "1.0",
  "statusReason": "系统启动成功，数据源 Skill 已就绪，进入实时监控模式。",
  "dataSources": {
    "realtimeQuote": {
      "source": "实际使用的 Skill 名称（如 westock-data）",
      "health": "OK",
      "latencyMs": 120,
      "lastSuccess": "当前时间ISO格式",
      "failCount": 0
    },
    "fundamental": {
      "source": "实际使用的 Skill 名称（如 akshare-finance）",
      "health": "OK",
      "lastUpdate": "当前时间ISO格式"
    },
    "news": {
      "source": "实际使用的 Skill 名称（如 akshare-finance）",
      "health": "OK",
      "lastUpdate": "当前时间ISO格式"
    },
    "disclosure": {
      "source": "Browser_Skill（披露易）",
      "health": "OK",
      "lastUpdate": "当前时间ISO格式"
    }
  },
  "account": {
    "status": "NORMAL",
    "openPositions": 0,
    "pendingOrders": 0,
    "lastReconciliation": null,
    "daysSinceReconciliation": 0
  },
  "tradingDay": {
    "date": "今日日期",
    "isTradingDay": true,
    "isHalfDay": false,
    "marketOpen": "09:30",
    "marketClose": "16:00",
    "nextTradingDay": "下一交易日日期"
  },
  "stockPool": { "coreCount": 0, "watchCount": 0, "blacklistCount": 0 },
  "cronTasks": [
    { "id": "任务ID", "cron": "cron表达式", "status": "REGISTERED", "nextRun": "下次执行时间ISO格式" }
  ],
  "notifications": {
    "primaryChannel": "主通讯渠道名称",
    "primaryStatus": "OK",
    "backupChannel": "备用通讯渠道名称（未配置时为空字符串）",
    "backupStatus": "未配置",
    "pendingRetries": 0,
    "cachedMessages": 0
  }
}
```

**现在，请确认以上全部设置无误，并开始执行。如有任何初始化失败，请立即报告失败模块及降级方案。**

---

### 8.7 边界情况处理

| 场景 | 处理规则 |
|------|----------|
| cron 命令执行失败 | 初始化第7步 `openclaw cron add` 命令执行失败时：① 不阻塞其他初始化步骤 ② 向用户报告"定时任务注册失败，自动调度不可用"及具体错误信息 ③ 输出12项任务的手动触发指引表（任务名称、建议时间、手动触发消息模板） ④ 提示用户可设置手机闹钟在对应时间发送触发消息 |
| 初始化某步骤失败但非致命 | 记录失败步骤，跳过继续后续步骤，在最终确认消息中列出"部分功能降级运行"及具体影响。致命失败（如 File_Skill 不可用导致无法读写文件）则中止初始化并报告 |
| JSON 指令单输出格式校验失败 | 若输出的 JSON 不符合 Schema 定义，回退到 Markdown 纯文本格式输出，在报告开头标注"⚠️ 标准格式输出异常，以下为纯文本版本" |
| 通知渠道发送失败 | 重试3次（间隔1分钟），仍失败则：① 将内容缓存到 `portfolio/pending_notifications.json` ② 在下次成功连接时自动补发 ③ 应急风控类通知同时通过备用通道发送 |
| 半日市时间调整 | 检测到半日市（如圣诞前夕12:00收盘）：自动调整盘中监控截止时间为11:55，取消12:15午间复盘，持仓对账提前至12:30，收盘总结提前至13:00 |
| 盘中监控间隔内系统无响应 | 若某个30分钟监控周期未能完成（如数据获取超时），跳过该周期，在下一周期开始时补充执行，不累积执行 |
