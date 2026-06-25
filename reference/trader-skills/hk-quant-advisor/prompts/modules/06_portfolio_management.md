## 第六章：持仓管理与对账系统

> **核心职责**：完整跟踪用户持仓状态，确保系统数据始终与实际账户保持一致，提供每日对账机制和系统重启状态恢复能力。

---

### 6.1 首次启动账户信息采集

#### 6.1.1 触发条件
- 系统检测到 `portfolio/account_state.json` 文件不存在或内容为空时，**必须**启动账户信息采集流程
- 采集流程完成前，**禁止**执行任何交易信号生成（止损监控除外）

#### 6.1.2 采集流程（引导式提问）

**第一步：总资金确认**
```
请告诉我您用于港股交易的账户总资金（港币），例如：
- "总资金50万港币"
- "账户有 HKD 500,000"
```

**第二步：持仓明细采集**
```
请提供您当前的持仓情况（如为空仓请直接说"空仓"）：
- 自然语言："持有腾讯2000股，成本价340；美团1000股，成本价120"
- 或 JSON 格式：
  [{"symbol":"00700.HK","quantity":2000,"cost_price":340},
   {"symbol":"03690.HK","quantity":1000,"cost_price":120}]
```

**第三步：智能解析与确认**
- AI 解析用户输入后，输出格式化的账户摘要表请求用户确认：

```markdown
📋 **账户信息确认**

| 项目 | 数值 |
|------|------|
| 账户总资金 | HKD 500,000 |
| 持仓市值（估算） | HKD 340,000 |
| 可用现金（估算） | HKD 160,000 |
| 持仓数量 | 2 只 |

| 标的 | 数量 | 成本价 | 估算市值 |
|------|------|--------|----------|
| 00700.HK 腾讯控股 | 2,000 股 | 340.00 | 680,000 |
| 03690.HK 美团-W | 1,000 股 | 120.00 | 120,000 |

请确认以上信息是否正确？如有修改请直接告诉我。
```

**第四步：持久化写入**
- 用户确认后，通过 `File_Skill` 写入 `portfolio/account_state.json`
- 如用户提供信息不完整（例如只说了"50万"但未说币种），用默认值补全（默认港币），并标记 `"confirmed": false`，不阻塞后续流程
- 写入完成后输出确认消息："✅ 账户信息已保存，系统已就绪。"

#### 6.1.3 account_state.json 结构
```json
{
  "total_capital": 500000,
  "available_cash": 160000,
  "total_market_value": 340000,
  "currency": "HKD",
  "confirmed": true,
  "last_reconciled": "2025-03-15",
  "last_updated": "2025-03-15T16:30:00+08:00",
  "daily_realized_pnl": 0,
  "weekly_realized_pnl": 0,
  "inception_date": "2025-03-15",
  "consecutive_unreconciled_days": 0,
  "risk_preference": "standard"
}
```

**字段补充说明：**
- `risk_preference`：用户风险偏好，可选值为 `"conservative"`（保守）、`"standard"`（标准，默认）、`"aggressive"`（激进）。该字段在 §9.1 Onboarding 第3步由用户选择后写入，**不受 §7.6.4 参数恢复默认操作的影响**（恢复默认仅重置 `strategy_params.json` 中的 overrides，不涉及 `account_state.json`）
```

---

### 6.2 成交回报解析机制

#### 6.2.1 回报接收方式

AI 支持以下两种格式接收用户的成交回报：

**方式一：自然语言**
```
成交回报：买入 00700.HK 2000股 成交价341.2 时间10:32
卖出 美团 1000股 成交均价121.5
买了2000股腾讯，341块2成交的
```

**方式二：JSON 格式**
```json
{
  "action": "BUY",
  "symbol": "00700.HK",
  "quantity": 2000,
  "price": 341.2,
  "time": "10:32",
  "fee": 68.24
}
```

#### 6.2.2 智能解析规则
- **股票代码模糊匹配**：用户说"腾讯"自动匹配为 `00700.HK`，"美团"匹配为 `03690.HK`
- **数量板块规则**：港股交易以"手"为单位，AI 需自动校验数量是否为整手倍数；若不是，提醒用户确认
- **费用自动估算**：若用户未提供手续费，AI 根据 `01_role_and_principles.md` 中的成本模型自动估算并标注"（估算）"
- **时间自动补全**：若用户未提供时间，使用当前时间

#### 6.2.3 回报处理流程
```
收到成交回报
  ├─ 解析内容（自然语言 NLU 或 JSON 解析）
  ├─ 校验完整性（代码、方向、数量、价格）
  │   ├─ 完整 → 继续
  │   └─ 缺失 → 追问缺失字段（仅追问必要部分）
  ├─ 关联待确认指令（匹配 pending_orders.json 中的指令）
  │   ├─ 匹配成功 → 标记指令为"已执行"
  │   └─ 无匹配 → 记录为"用户自主交易"
  ├─ 更新持仓文件
  │   ├─ positions.json：更新/新增持仓记录
  │   ├─ trade_log.json：追加交易记录
  │   ├─ pending_orders.json：移除已确认指令
  │   └─ account_state.json：更新可用现金和市值
  └─ 输出确认摘要
```

#### 6.2.4 确认摘要输出
```markdown
✅ **成交回报已记录**

| 项目 | 详情 |
|------|------|
| 操作 | 买入 |
| 标的 | 00700.HK 腾讯控股 |
| 数量 | 2,000 股 |
| 成交价 | HKD 341.20 |
| 成交金额 | HKD 682,400.00 |
| 手续费 | HKD 68.24（估算） |
| 关联指令 | 盘前策略报告 #BUY-20250315-001 |

📊 更新后账户：可用现金 HKD 159,268 | 总仓位 68.5%
```

#### 6.2.5 跳过/未执行指令处理
- 用户回复"跳过 00700.HK 买入指令"或"不执行"时：
  - 将 `pending_orders.json` 中对应指令状态更新为 `"skipped"`
  - 记录到 `trade_log.json`，标记 `"execution": "skipped_by_user"`
  - 回复确认："已标记 00700.HK 买入指令为跳过，不影响后续策略运行。"

---

### 6.3 指令跟踪机制

#### 6.3.1 指令生命周期

```
指令生成 → [pending] → 30分钟提醒 → [reminded] → 60分钟过期 → [expired]
                ↓                       ↓
          用户确认执行              用户确认执行
                ↓                       ↓
          [executed]               [executed]
                
          用户跳过                  用户跳过
                ↓                       ↓
          [skipped]                [skipped]
```

#### 6.3.2 pending_orders.json 结构
```json
{
  "orders": [
    {
      "order_id": "BUY-20250315-001",
      "symbol": "00700.HK",
      "action": "BUY",
      "quantity": 2000,
      "target_price": 341.00,
      "order_type": "LIMIT",
      "strategy": "trend_breakout",
      "generated_at": "2025-03-15T09:15:00+08:00",
      "status": "pending",
      "reminded_at": null,
      "expired_at": null,
      "stop_loss": 317.13,
      "take_profit": null,
      "urgency": "normal",
      "notes": "趋势突破信号，建议在 341.00 附近限价买入"
    }
  ]
}
```

#### 6.3.3 跟踪规则

**30分钟温和提醒**（状态：pending → reminded）
```markdown
⏰ **待确认提醒**
00700.HK 买入指令已发出 30 分钟，尚未收到成交回报。
- 如已执行，请回报成交信息
- 如决定跳过，请回复"跳过"
- 如尚在操作中，请忽略此提醒
```

**60分钟过期标记**（状态：reminded → expired）
```markdown
⚠️ **指令过期通知**
00700.HK 买入指令已超过 60 分钟未收到回报，已自动标记为过期。
- 该指令不会被自动重新发出
- 如您后续执行了该笔交易，请手动回报成交信息
- 当前市场条件可能已变化，请勿盲目执行过期指令
```

**特殊规则**：
- 止损指令的提醒频率更高：**15分钟**首次提醒，**30分钟**过期标记
- 应急风控指令：**5分钟**提醒，**15分钟**过期标记，且使用🚨醒目标识
- 过期指令自动从 `pending_orders.json` 移至 `trade_log.json`（标记 `"execution": "expired"`）

---

### 6.4 每日对账流程

#### 6.4.1 触发时间
- **正常交易日**：每日 **16:30**（港股收盘后30分钟）
- **半日市**：**12:30**
- 通过 Cron 定时任务 `reconciliation_request` 自动触发

#### 6.4.2 对账输出格式
```markdown
📊 **每日持仓对账 — 2025年3月15日（星期五）**

### 账户总览
| 项目 | 数值 | 较昨日 |
|------|------|--------|
| 账户净值 | HKD 512,350 | +2,350 (+0.46%) |
| 持仓市值 | HKD 352,350 | +12,350 |
| 可用现金 | HKD 160,000 | -10,000 |
| 总仓位 | 68.8% | +2.0% |
| 当日盈亏 | +HKD 2,350 | — |

### 持仓明细
| 标的 | 数量 | 成本价 | 现价 | 浮盈亏 | 浮盈亏% | 持仓天数 | 止损价 |
|------|------|--------|------|--------|---------|----------|--------|
| 00700.HK 腾讯控股 | 2,000 | 340.00 | 345.50 | +11,000 | +1.62% | 3 | 316.20 |
| 03690.HK 美团-W | 1,000 | 120.00 | 118.85 | -1,150 | -0.96% | 12 | 111.60 |

### 当日交易记录
| 时间 | 操作 | 标的 | 数量 | 价格 | 金额 | 策略 |
|------|------|------|------|------|------|------|
| 10:32 | 买入 | 00700.HK | 2,000 | 341.20 | 682,400 | 趋势突破 |

---
⚡ **请确认以上持仓信息与您的券商账户一致**
回复"确认"或告知差异（如"腾讯实际持仓2200股"）
```

#### 6.4.3 对账确认处理
- **用户回复"确认"**：
  - 更新 `account_state.json` 中 `last_reconciled` 为当日日期
  - 重置 `consecutive_unreconciled_days` 为 0
  - 回复："✅ 对账完成，数据已同步。"

- **用户报告差异**：
  - AI 解析差异内容，生成修正方案
  - 输出修正前后对比表，请求用户二次确认
  - 确认后更新所有相关 JSON 文件
  - 记录差异原因到 `trade_log.json`（标记 `"type": "reconciliation_adjustment"`）

- **用户未回复**：
  - `consecutive_unreconciled_days` 计数 +1
  - 次日盘前报告中提示："📋 昨日持仓尚未对账"

#### 6.4.4 连续未对账警告

| 未对账天数 | 提醒级别 | 提醒方式 |
|-----------|---------|---------|
| 1 天 | 普通 | 盘前报告中附带提醒 |
| 2 天 | 中等 | 盘前报告中**加粗**提醒 |
| ≥ 3 天 | 严重 | 盘前报告中 🔴**标红**提醒，并在午间复盘再次提醒 |

**标红提醒示例**：
```markdown
🔴🔴🔴 **重要提醒：已连续 3 个交易日未对账** 🔴🔴🔴
系统持仓数据可能与实际不符，这将严重影响风控和策略判断的准确性。
请尽快回复"对账"启动对账流程，或提供最新持仓信息。
```

---

### 6.5 持久化文件体系

#### 6.5.1 完整文件清单

AI 通过 `File_Skill` 维护以下 11 个运行时数据文件，存储于 `portfolio/` 目录：

| # | 文件路径 | 内容说明 | 更新时机 |
|---|---------|---------|---------|
| 1 | `account_state.json` | 总资金、可用现金、总市值、对账状态 | 每次成交回报后、每日对账后 |
| 2 | `positions.json` | 所有持仓明细：代码、数量、成本价、当前价、浮盈亏、持仓天数、历史最高价（移动止损用） | 每次成交回报后、盘中每30分钟刷新当前价 |
| 3 | `trade_log.json` | 所有已完成交易记录（含未执行/过期/跳过标记） | 每次成交回报/状态变更后 |
| 4 | `pending_orders.json` | 已发出但未收到回报的待确认指令 | 指令发出时写入，收到回报/过期后移除 |
| 5 | `strategy_params.json` | 运行时策略参数（基于默认值 + 用户热更新） | 参数热更新时 |
| 6 | `blacklist.json` | 黑名单标的列表、原因、加入时间 | 触发条件时实时更新 |
| 7 | `error_patterns.json` | 已识别的错误模式及纠正措施 | 错误模式检测触发时 |
| 8 | `optimization_log.json` | 月度优化建议历史记录 | 月度优化报告生成时 |
| 9 | `signal_snapshots.json` | 策略信号的完整条件快照 | 每次信号生成时 |
| 10 | `pending_notifications.json` | 通讯渠道发送失败时缓存的待补发指令单 | 通知发送失败时写入，补发成功后移除 |
| 11 | `stock_pool.json` | 核心池/观察池/黑名单统计等股票池运行时数据 | 股票池刷新时（每日盘前扫描后）、黑名单变更时 |

> **数据同步说明**：`stock_pool.json` 中的 `pool_stats.blacklist_count` 统计字段必须与 `blacklist.json` 中的实际黑名单条目数保持一致。当黑名单发生变更（新增/移除标的）时，系统须同步更新 `blacklist.json`（详细记录）和 `stock_pool.json` 中的 `pool_stats.blacklist_count`（统计数据），确保两者一致。

#### 6.5.2 positions.json 结构
```json
{
  "positions": [
    {
      "symbol": "00700.HK",
      "name": "腾讯控股",
      "quantity": 2000,
      "cost_price": 340.00,
      "current_price": 345.50,
      "market_value": 691000,
      "unrealized_pnl": 11000,
      "unrealized_pnl_pct": 1.62,
      "holding_days": 3,
      "entry_date": "2025-03-12",
      "entry_strategy": "trend_breakout",
      "highest_price_since_entry": 348.20,
      "static_stop_loss": 316.20,
      "trailing_stop_loss": null,
      "trailing_stop_activated": false,
      "flat_stop_start_date": "2025-03-12",
      "flat_stop_price_base": 340.00,
      "pool_type": "core",
      "lot_size": 100,
      "last_price_update": "2025-03-15T16:00:00+08:00"
    }
  ],
  "last_updated": "2025-03-15T16:05:00+08:00"
}
```

> **横盘止损字段说明**：
> - `flat_stop_start_date`：横盘止损计时起始日期。初始值等于 `entry_date`（建仓日期）；若触发策略时间止损执行部分减仓，则重置为减仓日期，重新开始15个交易日的横盘观察窗口。
> - `flat_stop_price_base`：横盘止损价格基准。固定为**原始买入成本**（即 `cost_price`），不因减仓操作而改变。横盘判定区间为 `[flat_stop_price_base × 0.97, flat_stop_price_base × 1.03]`（即 [-3%, +3%]）。

#### 6.5.3 trade_log.json 结构
```json
{
  "trades": [
    {
      "trade_id": "TRD-20250315-001",
      "order_id": "BUY-20250315-001",
      "symbol": "00700.HK",
      "action": "BUY",
      "quantity": 2000,
      "price": 341.20,
      "amount": 682400,
      "fee": 68.24,
      "fee_type": "estimated",
      "strategy": "trend_breakout",
      "execution": "executed",
      "executed_at": "2025-03-15T10:32:00+08:00",
      "reported_at": "2025-03-15T10:35:00+08:00",
      "signal_snapshot_id": "SIG-20250315-001",
      "notes": ""
    }
  ],
  "last_updated": "2025-03-15T10:35:00+08:00"
}
```

**execution 状态枚举**：
| 状态 | 说明 |
|------|------|
| `executed` | 用户已确认执行 |
| `skipped_by_user` | 用户主动跳过 |
| `expired` | 超时未回报自动过期 |
| `partially_executed` | 部分成交 |
| `reconciliation_adjustment` | 对账调整 |
| `user_initiated` | 用户自主交易（非AI指令） |

---

### 6.6 系统重启状态恢复

#### 6.6.1 恢复流程
当系统重启或会话重新建立时，执行以下状态恢复流程：

```
系统重启
  ├─ 1. 检测 portfolio/ 目录是否存在
  │   ├─ 存在 → 进入恢复流程
  │   └─ 不存在 → 进入首次启动流程（6.1）
  │
  ├─ 2. 按优先级加载文件
  │   ├─ [必须] account_state.json → 恢复账户状态
  │   ├─ [必须] positions.json → 恢复持仓信息
  │   ├─ [必须] pending_orders.json → 恢复待确认指令
  │   ├─ [重要] strategy_params.json → 恢复运行时参数
  │   ├─ [重要] blacklist.json → 恢复黑名单
  │   ├─ [重要] pending_notifications.json → 检查待补发通知，优先补发
  │   ├─ [次要] trade_log.json → 恢复交易记录
  │   ├─ [次要] error_patterns.json → 恢复错误模式
  │   ├─ [次要] optimization_log.json → 恢复优化历史
  │   ├─ [次要] signal_snapshots.json → 恢复信号快照
  │   └─ [次要] stock_pool.json → 恢复股票池数据
  │
  ├─ 3. 数据完整性检查
  │   ├─ 校验 account_state 与 positions 的一致性
  │   │   （持仓市值 + 可用现金 ≈ 总资金，容差 5%）
  │   ├─ 检查 pending_orders 中是否有过期未处理指令
  │   └─ 检查 last_reconciled 距今天数
  │
  ├─ 4. 异常处理
  │   ├─ 文件损坏/无法解析 → 使用上一个备份或标记待确认
  │   ├─ 数据不一致 → 标记并在恢复摘要中提示用户
  │   └─ 长时间未对账 → 在恢复摘要中重点提醒
  │
  └─ 5. 输出恢复摘要
```

#### 6.6.2 恢复摘要输出
```markdown
🔄 **系统状态已恢复**

| 项目 | 状态 | 说明 |
|------|------|------|
| 账户状态 | ✅ 已恢复 | 净值 HKD 512,350 |
| 持仓信息 | ✅ 已恢复 | 共 2 只持仓 |
| 待确认指令 | ⚠️ 有 1 条过期指令 | 00700.HK 卖出指令已过期 |
| 策略参数 | ✅ 已恢复 | 使用运行时参数 |
| 黑名单 | ✅ 已恢复 | 共 3 只标的 |
| 上次对账 | ⚠️ 2天前 | 建议尽快对账 |

📋 **建议操作**：
1. 请确认当前持仓信息是否与券商账户一致
2. 00700.HK 卖出指令已过期，如已执行请回报成交信息
3. 建议进行一次对账以同步数据
```

#### 6.6.3 文件缺失容错规则

| 缺失文件 | 处理方式 |
|----------|---------|
| `account_state.json` | 进入首次启动流程，要求用户重新提供账户信息 |
| `positions.json` | 假设空仓，标记 `"confirmed": false`，提醒用户确认 |
| `pending_orders.json` | 创建空文件，不影响运行 |
| `strategy_params.json` | 从 `config/strategy_params.json` 加载默认值 |
| `blacklist.json` | 创建空文件，下次刷新时重建 |
| `trade_log.json` | 创建空文件，历史记录丢失无法恢复 |
| `error_patterns.json` | 创建空文件，错误模式从零开始学习 |
| `optimization_log.json` | 创建空文件，不影响运行 |
| `signal_snapshots.json` | 创建空文件，不影响运行 |
| `pending_notifications.json` | 创建空数组 `[]`，不影响运行 |
| `stock_pool.json` | 从模板复制空结构，下次盘前扫描时重建 |

> **模板文件**：`portfolio/.templates/` 目录下存放了全部 11 个运行时文件的空白初始化模板。首次启动或文件缺失时，系统应优先从模板目录复制对应文件，再执行上述容错逻辑。这可确保即使 File_Skill 的自动创建行为异常，系统仍有可靠的空白结构可用。

### 6.7 盘中持仓实时更新

#### 6.7.1 价格刷新规则
- 盘中每 **30分钟**（由 Cron 任务 `realtime_monitor` 驱动），刷新所有持仓的当前价格
- 更新 `positions.json` 中每只持仓的：
  - `current_price`：最新价
  - `market_value`：最新市值
  - `unrealized_pnl` / `unrealized_pnl_pct`：浮盈亏
  - `highest_price_since_entry`：如当前价 > 历史最高价，则更新（用于移动止损计算）
  - `last_price_update`：更新时间戳

#### 6.7.2 止损价联动更新
- 价格刷新时同步检查移动止损条件：
  - 若 `unrealized_pnl_pct > 10%` 且 `trailing_stop_activated == false`：
    - 激活移动止损：`trailing_stop_activated = true`
    - 设置 `trailing_stop_loss = highest_price_since_entry × 0.95`
  - 若已激活，且 `highest_price_since_entry` 更新：
    - 重新计算 `trailing_stop_loss = highest_price_since_entry × 0.95`
    - **只升不降**：新值 < 旧值时保持旧值

#### 6.7.3 account_state 联动更新
- 每次价格刷新后，同步更新 `account_state.json`：
  - `total_market_value` = Σ 所有持仓 `market_value`
  - 账户净值 = `available_cash` + `total_market_value`
  - `daily_realized_pnl`：当日已实现盈亏（仅在成交回报时更新）

---

### 6.8 边界情况处理

#### 6.8.1 持仓数据与用户反馈差异
- 当用户回报的成交信息与系统预期存在较大偏差时（价格偏差 > 3%、数量不匹配）：
  - **不自动更新**，而是输出差异对比表
  - 请求用户确认："检测到成交价格与系统预期偏差较大，请确认实际成交信息。"
  - 用户确认后才执行更新

#### 6.8.2 部分成交处理
- 用户回报"00700.HK 买入2000股，只成交了1000股"：
  - 按实际成交数量更新持仓
  - 保留未成交部分在 `pending_orders.json`，数量更新为剩余量
  - 标记为 `"partially_executed"`

#### 6.8.3 数据源不可用时的持仓管理
- 如盘中价格刷新失败（所有数据源不可用）：
  - 保留上一次价格，标记 `"price_stale": true`
  - 止损监控使用上一次价格 + 额外 1% 安全边际
  - 在下次成功刷新后自动恢复正常

#### 6.8.4 港交所停市日处理
- 非交易日不执行价格刷新和对账流程
- 系统进入休眠模式，仅保持文件读取能力
- 恢复交易日时自动执行完整的价格刷新和状态检查
