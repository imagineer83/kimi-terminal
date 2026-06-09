# Kimi Terminal — 设计文档

**日期**：2026-06-09  
**状态**：待实现  
**作者**：Kimi Code (Brainstorming)  
**版本**：v1.0

---

## 1. 产品概述

Kimi Terminal（命令 `kmt`）是一款面向中国大陆 A 股与香港股市的终端风格 TUI（Text User Interface）金融数据工具。它基于 `plugin-kimi-datasource` 提供的 `stock_finance_data` 数据源能力，在 Linux/macOS 终端内提供类似 Bloomberg Terminal 的行情、财务、技术分析与公告查询体验。

### 1.1 目标用户

- 个人投资者、量化研究员、财经爱好者
- 习惯终端工作流、追求低资源占用与快速键盘操作的用户

### 1.2 成功标准

- 启动 `kmt` 后 3 秒内进入主界面并展示自选股行情
- 所有核心操作可通过键盘完成（无需鼠标）
- 行情数据刷新延迟 ≤ 35 秒（受 API 限制）
- 个股详情页可在 2 秒内加载历史走势与技术指标
- 财务数据支持按报告期切换、按指标维度筛选

---

## 2. 范围与限制

### 2.1 本次 MVP 范围

| 模块 | 内容 | 优先级 |
|---|---|---|
| Dashboard | 自选股实时行情表格 | P0 |
| Quote | 个股详情 + 历史 K 线 + 实时技术指标 | P0 |
| Financials | 财报三表 + 六大财务指标 | P0 |
| Announcements | A 股公告列表与标题搜索 | P1 |
| Screener | 智能选股器（多维度条件） | P1 |
| 命令栏 | Bloomberg 风格命令输入 | P0 |

### 2.2 明确不做的内容

- 通用实时新闻（数据源未提供）
- 交易下单功能
- 美股行情展示（数据源支持但本次聚焦 A 股/港股）
- Web/移动端界面
- 用户账户系统

### 2.3 数据源能力边界

- **实时行情**：每次请求最多 3 个 ticker；A 股全天可用，港股仅在交易时段提供当日盘中数据
- **技术指标（realtime_tech）**：仅 A 股主板，不支持港股、ETF、科创板 688xxx
- **公告/业绩预告**：仅 A 股
- **历史价格**：最多 10 个 ticker，时间跨度 ≤ 3 年
- **财报/财务指标**：A 股与港股均支持，需指定报告期

---

## 3. 技术栈

- **语言**：Python 3.11+
- **TUI 框架**：Textual 0.x
- **数据请求**：`httpx`（异步 HTTP）
- **数据解析/缓存**：`pydantic` + `sqlite3`
- **图表**：`textual-plotext` 或自定义 Sparkline（ASCII 折线图）
- **配置**：YAML（`PyYAML`）
- **CLI 入口**：`click` 或 `typer`

---

## 4. 架构设计

采用**单体式 Textual TUI**方案：所有 UI、业务逻辑、数据访问封装在一个 Python 包内，直接调用 Kimi API。

```
kimi_terminal/
├── __init__.py
├── cli.py                      # 入口：kmt 命令解析
├── app.py                      # Textual App：路由、全局快捷键、主题
├── config.py                   # 配置读取与 watchlist 管理
├── models/
│   ├── __init__.py
│   ├── ticker.py               # Ticker 解析与校验
│   ├── quote.py                # 实时行情数据模型
│   ├── candle.py               # K 线数据模型
│   ├── financial.py            # 财报与财务指标模型
│   └── announcement.py         # 公告模型
├── services/
│   ├── __init__.py
│   ├── api_client.py           # Kimi API 调用封装
│   ├── cache.py                # SQLite 缓存层
│   └── watchlist_service.py    # 自选股 CRUD
├── screens/
│   ├── __init__.py
│   ├── dashboard_screen.py     # 自选股 Dashboard
│   ├── quote_screen.py         # 个股详情
│   ├── financial_screen.py     # 财务报表
│   ├── announcement_screen.py  # 公告列表
│   └── screener_screen.py      # 智能选股
├── widgets/
│   ├── __init__.py
│   ├── header.py               # 顶部状态条
│   ├── footer.py               # 底部命令栏/状态栏
│   ├── quote_table.py          # 行情表格
│   ├── sparkline.py            # ASCII 迷你走势图
│   ├── command_input.py        # 命令输入弹窗
│   └── loading.py              # 加载指示器
└── utils/
    ├── __init__.py
    ├── format.py               # 数字/百分比格式化
    └── async_helpers.py        # 异步工具
```

### 4.1 模块职责

| 模块 | 职责 | 依赖 |
|---|---|---|
| `cli.py` | 解析命令行参数，启动 App | `app.py` |
| `app.py` | Textual 应用主类，管理屏幕栈、全局事件（`:EQ`、`:FA` 等命令） | `screens/*`、`widgets/*` |
| `config.py` | 读取 `~/.config/kimi-terminal/config.yaml`，维护 `watchlist.yaml` | 标准库 |
| `services/api_client.py` | 读取 Kimi Code credentials，构造 HTTP 请求，解析返回的 CSV/JSON，处理超时与重试 | `httpx`、本地文件 |
| `services/cache.py` | 基于 SQLite 的 TTL 缓存，缓存解析后的结构化数据（非原始 CSV） | `sqlite3` |
| `screens/*` | 每个屏幕负责自己的布局、数据加载、用户交互 | `services/*`、`widgets/*` |
| `widgets/*` | 可复用的视觉组件，不直接调用 API | `models/*`、`utils/*` |

---

## 5. 核心数据流

### 5.1 启动流程

1. 用户执行 `kmt`
2. `cli.py` 初始化配置目录 `~/.config/kimi-terminal/`，如不存在则创建默认 `config.yaml` 与 `watchlist.yaml`
3. `app.py` 挂载 `DashboardScreen` 为默认屏幕
4. `DashboardScreen` 从 `watchlist.yaml` 读取自选股列表
5. 分批调用 `stock_finance_data_get_stock_realtime_price` 加载实时行情
6. 渲染 `QuoteTable`

### 5.2 行情刷新流程

```
DashboardScreen.on_mount()
  → 启动 Interval 定时器（30 秒）
  → WatchlistService.get_tickers()
  → 按每批 3 个分组
  → ApiClient.get_realtime_price(batch)
    → Cache.get(...) 若命中且 TTL 内则返回
    → 否则读取 ~/.kimi-code/credentials/kimi-code.json
    → POST https://api.kimi.com/coding/v1/tools
    → Cache.set(...)
  → 合并结果 → QuoteTable.update_rows()
```

### 5.3 个股详情流程

1. 用户在 Dashboard 选中股票按 Enter，或命令栏输入 `:EQ 600519.SH`
2. `App` 派发 `PushScreen("quote", ticker=...)`
3. `QuoteScreen` 并行发起三个请求：
   - `get_stock_info`（公司基本信息）
   - `get_price`（近 90 日日线，用于 K 线）
   - `get_stock_realtime_price(type=realtime_tech)`（技术指标，仅 A 股）
4. 左侧展示 info，右侧上方 Sparkline 展示收盘价走势，下方 DataTable 展示技术指标
5. 港股跳过技术指标请求，仅展示价格走势

### 5.4 财报流程

1. 命令 `:FA 600519.SH` 进入 `FinancialScreen`
2. 默认展示最近年报的资产负债表
3. 顶部提供 Tab 切换：`资产负债表 | 利润表 | 现金流量 | 财务指标`
4. 若选择财务指标，再提供子维度：`盈利能力 | 成长能力 | 偿债能力 | 营运能力 | 流动性 | 现金流覆盖`
5. 切换时优先读取缓存，过期则调用对应 API

---

## 6. 命令栏设计

底部固定命令栏，按 `:` 激活输入，回车执行，`Esc` 取消。

| 命令 | 含义 | 示例 |
|---|---|---|
| `:EQ <ticker>` | 打开个股详情 | `:EQ 600519.SH` |
| `:FA <ticker>` | 打开财务报表 | `:FA 0700.HK` |
| `:ANN <ticker>` | 打开公告 | `:ANN 000001.SZ` |
| `:SCR [query]` | 打开选股器 | `:SCR 人工智能 PE小于30` |
| `:ADD <ticker>` | 加入自选股 | `:ADD 0700.HK` |
| `:DEL <ticker>` | 删除自选股 | `:DEL 0700.HK` |
| `:HOME` / `:D` | 返回 Dashboard | `:D` |
| `:Q` | 退出程序 | `:Q` |

全局快捷键：
- `F1` / `d` → Dashboard
- `F2` / `e` → 输入 `:EQ`
- `F3` / `f` → 输入 `:FA`
- `F4` / `a` → 输入 `:ANN`
- `F5` / `s` → 打开 Screener
- `q` / `Ctrl+C` → 退出

---

## 7. 缓存策略

使用本地 SQLite（`~/.cache/kimi-terminal/cache.db`），按数据类型设置 TTL：

| 数据类型 | TTL | 说明 |
|---|---|---|
| `stock_info` | 7 天 | 公司基本面变化不频繁 |
| `realtime_price` | 25 秒 | 略短于自动刷新周期 |
| `close_summary` | 1 天 | 日线收盘后固定 |
| `historical_price` | 1 天 | 日线历史数据 |
| `financial_statements` | 7 天 | 财报按季度发布 |
| `financial_index` | 7 天 | 财务指标 |
| `announcement` | 1 小时 | 公告可能随时更新 |
| `screener_result` | 10 分钟 | 选股结果日内相对有效 |

缓存键包含 ticker + API 参数哈希。

---

## 8. 错误处理

- **API 调用失败**：捕获 `httpx.HTTPStatusError`、`TimeoutException`、Kimi API 返回的 `is_success=false`，在 `Footer` 状态栏显示简短错误信息，不弹窗阻塞
- **凭证缺失**：若 `~/.kimi-code/credentials/kimi-code.json` 不存在，提示用户运行 Kimi Code `/login`
- **Ticker 格式错误**：校验 A 股（6 位 + .SH/.SZ/.BJ）、港股（4 位 + .HK），非法格式在命令栏即时提示
- **数据源不支持**：港股请求技术指标、A 股外请求公告时，在内容区展示 `该市场暂不支持此功能`
- **离线模式**：若 API 完全不可用，使用缓存数据并显示 `离线模式 - 数据可能不是最新`

---

## 9. 配置与自选股

配置文件目录：`~/.config/kimi-terminal/`

`config.yaml`：
```yaml
theme: "dark"
refresh_interval_seconds: 30
price_precision: 2
cache_db_path: "~/.cache/kimi-terminal/cache.db"
```

`watchlist.yaml`：
```yaml
watchlist:
  - code: "600519.SH"
    name: "贵州茅台"
    hold_cost: 1500.0
    hold_quantity: 100
  - code: "0700.HK"
    name: "腾讯控股"
```

首次启动时，若文件不存在，自动生成包含 2-3 只示例股票的默认 watchlist。

---

## 10. 测试策略

| 测试层级 | 内容 |
|---|---|
| 单元测试 | `models/` 中 ticker 解析、格式化函数；`services/cache.py` 读写；`utils/format.py` |
| 集成测试 | 使用 `respx` mock Kimi API，验证 `api_client.py` 的请求构造、缓存命中、错误处理 |
| UI 测试 | Textual 的 `Pilot` 测试：屏幕切换、按键事件、命令栏输入 |
| 端到端 | 本地启动 `kmt`，人工走查 Dashboard → Quote → Financials → 命令栏 |

---

## 11. 交付物

- `kimi_terminal/` Python 包
- `pyproject.toml`（ Poetry 或 hatchling）
- `README.md`：安装、配置、快捷键说明
- `Makefile`：install / test / run
- 可选：GitHub Actions 运行 pytest

---

## 12. 风险与依赖

| 风险 | 缓解措施 |
|---|---|
| Kimi API 调用频率/配额限制 | 缓存 + 25-30 秒刷新周期；用户可配置刷新间隔 |
| API 返回字段变更 | Pydantic 模型使用 `extra="ignore"`，关键字段缺失时展示占位符 |
| 港股实时数据在非交易时段为空 | 自动回退到 `close_summary` 展示最近收盘数据 |
| Textual 在部分终端渲染异常 | 默认使用 256 色主题，提供 `simple` 模式（减少边框/颜色） |

---

## 13. 后续迭代方向

- 美股行情支持（`yahoo_finance` 数据源）
- 自定义指标公式与回测
- 导出数据为 CSV/Excel
- 多 watchlist 组合管理
- 插件化图表（接入 `textual-plotext` 绘制更专业的 K 线图）
