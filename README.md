# Global Finance Daily Report Email Sender (全球宏观财经每日邮件简报系统)

自动化采集全球 22 个核心指标（美/中/港/欧/亚太/越/俄股指、原油、黄金白银、Bitcoin、VIX），以国内**红涨绿跌**风格生成自适应 HTML 邮件，通过 Gmail SMTP 在工作日早晚定时推送。

## 功能特性

- **多源采集**：东方财富 + 新浪财经 + 腾讯财经并发拉取与容错降级
- **22 个全球标的**：覆盖欧美核心股指、亚太重点股指、大宗商品与贵金属、数字与恐慌资产
- **红涨绿跌**：符合国内阅读习惯的涨跌配色
- **HTML 邮件**：响应式设计，兼容桌面端与移动端
- **定时推送**：GitHub Actions 工作日早晚自动触发
- **本地调试**：一键预览 HTML 邮件效果

## 监控标的

| 分类 | 标的 |
|------|------|
| 欧美核心股指 | 标普500、纳斯达克100、英国富时100、法国CAC40、德国DAX30 |
| 亚太重点股指 | 上证指数、沪深300、恒生指数、恒生科技、台湾加权、日经225、韩国KOSPI、印度SENSEX、越南VN30 |
| 大宗商品与贵金属 | WTI原油、布伦特原油、黄金、白银 |
| 数字与恐慌资产 | Bitcoin、VIX恐慌指数、俄罗斯RTS |

## 快速上手

### 1. 环境初始化

```bash
./setup-env.sh
```

自动完成：检测/安装 uv、创建虚拟环境、安装依赖、生成 `local.env` 配置文件。

### 2. 配置 Gmail 凭据

编辑 `local.env`，填入以下信息：

```bash
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=recipient@example.com
TIMEZONE=Asia/Shanghai
```

> **获取 Gmail 应用专用密码：**
> 1. 访问 [Google 账号安全设置](https://myaccount.google.com/security)
> 2. 确保已开启两步验证
> 3. 进入"两步验证" → "应用专用密码"，生成新密码
> 4. 将生成的 16 位密码填入 `GMAIL_APP_PASSWORD`

### 3. 本地测试

```bash
# 默认 dry-run 模式：抓取数据 + 生成 HTML 预览
./local-test.sh

# 运行单元测试
./local-test.sh --unit

# 指定晨报类型
./local-test.sh --type morning

# 真实发送邮件（需已配置 Gmail 凭据）
./local-test.sh --send
```

生成的 `test_report.html` 可用浏览器直接打开预览。

## GitHub Actions 部署

### 配置 Secrets

在 GitHub 仓库 → Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 说明 |
|-------------|------|
| `GMAIL_USER` | Gmail 邮箱地址 |
| `GMAIL_APP_PASSWORD` | Gmail 应用专用密码 |
| `EMAIL_TO` | 收件人邮箱地址 |

### 定时规则

| 类型 | 北京时间 | UTC 时间 | Cron 表达式 |
|------|---------|---------|-------------|
| 早报 | 周一至周五 07:30 | 周日至周四 23:30 | `30 23 * * 0-4` |
| 晚报 | 周一至周五 17:30 | 周一至周五 09:30 | `30 9 * * 1-5` |

### 手动触发

在 GitHub Actions 页面点击 "Run workflow"，可选择 `auto` / `morning` / `evening` 类型。

## 项目结构

```
daily-finace-rpt-email-sender/
├── config/assets.yaml          # 22 个资产配置定义
├── src/
│   ├── models.py               # AssetQuote 统一数据模型
│   ├── config.py               # 配置加载器
│   ├── renderer.py             # Jinja2 HTML 渲染器
│   ├── mailer.py               # Gmail SMTP 发送模块
│   ├── collectors/
│   │   ├── base.py             # 采集器基类
│   │   ├── eastmoney.py        # 东方财富采集器
│   │   ├── sina.py             # 新浪财经采集器
│   │   ├── tencent.py          # 腾讯财经采集器
│   │   └── aggregator.py       # 多源聚合调度器
│   └── templates/
│       └── report.html.j2      # 邮件 HTML 模板
├── tests/                      # 单元测试
├── main.py                     # CLI 入口
├── setup-env.sh                # 环境初始化脚本
├── local-test.sh               # 本地测试脚本
└── .github/workflows/
    └── daily_report.yml        # GitHub Actions 工作流
```

## 技术栈

- Python 3.12+
- uv (包管理)
- httpx (异步 HTTP)
- Jinja2 (模板引擎)
- Pydantic (数据验证)
- PyYAML (配置解析)
- pytest (测试框架)
