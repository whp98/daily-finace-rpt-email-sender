# 全球宏观财经每日邮件简报系统设计规范 (Design Spec)

- **日期**：2026-09-23
- **版本**：v1.0.0
- **项目名**：daily-finace-rpt-email-sender
- **状态**：Approved (已评审通过)

---

## 1. 目标与背景

本系统旨在构建一个轻量、稳定、免运维的**全球宏观每日财经邮件简报系统**。系统通过完全免费、免申请 API Key 的公开金融行情通道，采集用户指定的 22 个全球核心资产（涵盖欧美主要股指、亚太核心股指、大宗商品、贵金属、加密货币与恐慌指数）的收盘与盘后行情，按国内证券习惯（红涨绿跌）生成精美自适应 HTML 邮件，并通过 Gmail SMTP 在每个交易日早晚定时推送到用户指定邮箱。

系统核心原则：
1. **零成本与免服务器**：基于 GitHub Actions 自动化工作流与 Gmail 发信，无需独立云服务器；
2. **极速与易开发**：采用 `uv` 作为包管理工具，提供 `setup-env.sh` 与 `local-test.sh` 脚本支持一键环境配置与本地免发信调试；
3. **高容错与多源兜底**：采用东方财富（Eastmoney）+ 新浪财经（Sina）+ 腾讯财经（Tencent）多源互备机制，单个品种休市或接口波动绝不阻塞整封邮件送达。

---

## 2. 监控标的清单与数据源映射

系统监控的 22 个资产划分为 4 大版块，具体代码与数据源映射如下：

| 序号 | 标的名称 | 分类 | 主力数据源 | 备用数据源 | 代码标识 (Symbol/Secid) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 标普500指数 | 欧美核心股指 | 东方财富 / 腾讯 | 新浪 | `100.SPX` / `s_usINX` |
| 2 | 纳斯达克100 | 欧美核心股指 | 东方财富 / 腾讯 | 新浪 | `100.NDX100` / `s_usNDX` |
| 3 | 英国富时100 | 欧美核心股指 | 东方财富 | 新浪 | `100.FTSE` / `int_ftse` |
| 4 | 法国CAC40 | 欧美核心股指 | 东方财富 | 新浪 | `100.FCHI` / `int_cac` |
| 5 | 德国DAX30 | 欧美核心股指 | 东方财富 | 新浪 | `100.GDAXI` / `int_dax` |
| 6 | 上证指数 | 亚太重点股指 | 腾讯 / 新浪 | 东方财富 | `s_sh000001` / `1.000001` |
| 7 | 沪深300 | 亚太重点股指 | 腾讯 / 新浪 | 东方财富 | `s_sh000300` / `0.399300` |
| 8 | 香港恒生指数 | 亚太重点股指 | 腾讯 / 东方财富 | 新浪 | `s_hkHSI` / `100.HSI` |
| 9 | 恒生科技指数 | 亚太重点股指 | 腾讯 / 东方财富 | 新浪 | `s_hkHSTECH` / `124.HSTECH` |
| 10 | 台湾加权指数 | 亚太重点股指 | 东方财富 | 新浪 | `100.TWII` |
| 11 | 日本东证指数 | 亚太重点股指 | 东方财富 | 新浪 / Yahoo | `100.N225` / `int_topix` |
| 12 | 韩国KOSPI | 亚太重点股指 | 东方财富 | 新浪 | `100.KS11` |
| 13 | 印度BSE SENSEX | 亚太重点股指 | 东方财富 | 新浪 | `100.SENSEX` |
| 14 | 越南HNX30 | 亚太重点股指 | 东方财富 | 新浪 | `100.VNINDEX` / `HNX30` |
| 15 | WTI原油 | 大宗商品与贵金属 | 新浪期货 | 东方财富 | `hf_CL` |
| 16 | 布伦特原油现货/美元 | 大宗商品与贵金属 | 新浪期货 | 东方财富 | `hf_OIL` |
| 17 | 黄金/美元 | 大宗商品与贵金属 | 新浪现货 | 东方财富 | `fx_sxauusd` / `hf_GC` |
| 18 | 银/美元 | 大宗商品与贵金属 | 新浪现货 | 东方财富 | `fx_sxagusd` / `hf_SI` |
| 19 | Bitcoin | 数字与恐慌资产 | 新浪现货 / 币安 | 东方财富 | `fx_sbtcusd` / `BTCUSDT` |
| 20 | VIX恐慌指数 | 数字与恐慌资产 | 腾讯美股 | 东方财富 / Yahoo | `s_usVIX` / `107.VIXY` |
| 21 | 俄罗斯市值加权指数 | 数字与恐慌资产 | 东方财富 | 新浪 | `100.RTS` |
| 22 | 沪深300 (复核) | 亚太重点股指 | 腾讯 / 东方财富 | 新浪 | 同上 |

---

## 3. 项目目录结构

```text
daily-finace-rpt-email-sender/
├── .github/
│   └── workflows/
│       └── daily_report.yml    # GitHub Actions 定时工作流 (周一至周五 07:30 / 17:30 BJT)
├── config/
│   └── assets.yaml             # 22 个监控品种元数据与分组配置
├── src/
│   ├── __init__.py
│   ├── config.py               # 环境变量与运行时配置解析
│   ├── models.py               # 统一数据结构定义 (AssetQuote, MarketReport)
│   ├── collectors/             # 多源数据采集适配器
│   │   ├── __init__.py
│   │   ├── base.py             # 抽象基类 BaseCollector
│   │   ├── eastmoney.py        # 东方财富 API 采集适配器
│   │   ├── sina.py             # 新浪财经 API 采集适配器
│   │   ├── tencent.py          # 腾讯财经 API 采集适配器
│   │   └── aggregator.py       # 多源并发调度与容错降级分发器
│   ├── renderer.py             # Jinja2 邮件 HTML 渲染引擎
│   ├── mailer.py               # Gmail SMTP 安全发信模块
│   └── templates/
│       └── report.html.j2      # 邮件模板 (红涨绿跌、自适应移动端、分区表格)
├── main.py                     # CLI 入口脚本 (--type morning|evening, --dry-run)
├── setup-env.sh                # 环境安装与依赖初始化脚本
├── local-test.sh               # 本地调试与测试脚本
├── local.env.example           # 本地环境变量配置样例
├── .gitignore                  # Git 忽略文件 (local.env, .venv 等)
├── pyproject.toml              # uv 项目元数据与依赖定义
└── README.md                   # 部署配置与使用说明
```

---

## 4. 核心组件与数据流设计

### 4.1 数据流
```text
[assets.yaml]
      │
      ▼
[Aggregator] ──(异步并发)──> [Eastmoney Collector] ──> 东方财富 Web API
      │                ──> [Sina Collector]      ──> 新浪财经 HQ API
      │                ──> [Tencent Collector]   ──> 腾讯财经 GTimg API
      ▼
[AssetQuote 数据归一化 & 异常兜底过滤]
      │
      ▼
[Renderer] ──(Jinja2 模板注入 + 红涨绿跌样式计算)──> 生成 HTML 邮件内容
      │
      ├── (若 --dry-run) ──> 终端格式化打印表格 + 保存 test_report.html
      └── (若 发信模式)   ──> [Mailer] ──(Gmail SMTP TLS 587)──> 发送到指定用户邮箱
```

### 4.2 统一行情模型 (`src/models.py`)
```python
from pydantic import BaseModel
from typing import Optional

class AssetQuote(BaseModel):
    name: str                   # 标的中文名称，如 "恒生科技指数"
    symbol: str                 # 标的代码，如 "HSTECH"
    category: str               # 所属板块分类
    latest_price: str           # 最新价/收盘价（格式化字符串）
    prev_close: str             # 昨收盘价
    change_pct: float           # 涨跌幅数值（如 -1.33）
    change_str: str             # 涨跌幅展示字符串（如 "-1.33%"）
    change_val: str             # 涨跌金额（如 "-59.14"）
    volume: str                 # 成交量（如 "977.62M" 或 "-"）
    quote_time: str             # 行情更新时间（如 "15:59:59"）
    color: str                  # 颜色标识："up" (红) | "down" (绿) | "flat" (灰)
    status: str = "normal"      # 状态："normal" | "holiday" | "fallback"
```

### 4.3 采集容错与重试逻辑
1. **异步并发请求**：使用 `httpx.AsyncClient`，批量抓取耗时控制在 1 秒左右；
2. **超时与重试**：单次请求设置 5 秒超时，接口异常时自动重试最多 2 次；
3. **数据兜底策略**：
   - 东方财富与新浪、腾讯互为兜底；
   - 若某品种遇到该市场假期休市，接口返回昨收或停牌标识，系统自动标注 `休市` 并展示最新有效数据，绝不导致程序崩溃或邮件流产。

---

## 5. 邮件渲染与样式规范

### 5.1 视觉风格
- **国内证券惯例**：
  - 上涨（`change_pct > 0`）：文字颜色 `#e53935`（正红），徽章微红背景 `#ffebee`，带前缀 `+`；
  - 下跌（`change_pct < 0`）：文字颜色 `#2e7d32`（正绿），徽章微绿背景 `#e8f5e9`；
  - 平盘（`change_pct == 0`）：文字颜色 `#757575`（中性灰）。
- **表格列排布**：
  1. `标的名称`（加粗显示）
  2. `最新价`
  3. `昨收盘`
  4. `涨跌幅`（高亮徽章）
  5. `成交量`
  6. `行情时间`
- **分区显示**：按 4 大板块拆分为独立卡片表格，版面层次分明。
- **兼容性保障**：使用纯内联样式（Inline CSS），支持 Gmail Web 端、iOS 自带 Mail、Android Gmail 及各种第三方客户端。

### 5.2 早晚报逻辑
- **早报（Morning Report）**：
  - 发送时间：周一至周五 07:30 (UTC+8)
  - 邮件标题：`【全球财经晨报】隔夜欧美大宗复盘与外盘盘点 (YYYY-MM-DD)`
  - 重点摘要：美股三强、黄金原油、Bitcoin、VIX恐慌指数最新动态。
- **晚报（Evening Report）**：
  - 发送时间：周一至周五 17:30 (UTC+8)
  - 邮件标题：`【全球财经晚报】亚太核心股指收盘与欧洲盘初盘点 (YYYY-MM-DD)`
  - 重点摘要：A股、港股、日韩台越收盘表现。

---

## 6. 脚本与环境规范

### 6.1 `setup-env.sh`
- 检测操作系统与 Python 3.12+ 环境；
- 检查 `uv` 是否安装，未安装则自动执行官方推荐安装脚本；
- 执行 `uv venv` 创建虚拟环境；
- 执行 `uv pip install -e .` 或 `uv sync` 安装运行时与测试依赖；
- 检查是否存在 `local.env`，若不存在则从 `local.env.example` 复制，并友好提示配置 Gmail 凭证。

### 6.2 `local-test.sh`
- 自动加载 `local.env` 中的环境变量；
- 默认执行：`./local-test.sh`（即 `uv run python main.py --report-type morning --dry-run`），在终端打印美观表格，并在根目录生成 `test_report.html`；
- 支持参数：
  - `./local-test.sh --send`：触发真实 Gmail 邮件发送测试；
  - `./local-test.sh --type evening`：测试晚报模式；
  - `./local-test.sh --unit`：运行 `uv run pytest` 执行单元测试。

### 6.3 配置文件与安全隔离
- `local.env` 必须在 `.gitignore` 中显式排除；
- `local.env.example` 包含模板字段：
  ```ini
  # Gmail SMTP 配置
  GMAIL_USER=your_email@gmail.com
  GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
  EMAIL_TO=recipient@example.com
  TIMEZONE=Asia/Shanghai
  ```

---

## 7. GitHub Actions 工作流规范 (`daily_report.yml`)

### 7.1 触发时机
- **早报定时**：`cron: '30 23 * * 0-4'`（UTC 时间周日至周四 23:30 = 北京时间周一至周五 07:30）；
- **晚报定时**：`cron: '30 9 * * 1-5'`（UTC 时间周一至周五 09:30 = 北京时间周一至周五 17:30）；
- **手动触发**：`workflow_dispatch`，可在 GitHub Actions 界面选择 `report_type`: `auto` / `morning` / `evening` / `dry-run`。

### 7.2 安全凭证
在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 中配置：
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `EMAIL_TO`

---

## 8. 测试与验证方案

1. **单元测试 (`tests/test_collectors.py`)**：
   - 验证东方财富、新浪、腾讯行情解析器的容错与字段映射；
   - 验证极端格式（成交量缺省、无昨收价、数据缺失）下的解析健壮性。
2. **端到端集成测试 (`local-test.sh`)**：
   - 本地运行 `--dry-run`，验证 22 个品种全部拉取成功并生成合格的 HTML 文件；
   - 本地运行 `--send`，验证 Gmail SMTP 成功将邮件投递至收件箱并呈现预期样式。
3. **工作流语法验证**：
   - 校验 GitHub Actions YAML 语法的合规性与 Cron 时区换算准确性。
