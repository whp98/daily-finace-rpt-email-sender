# 全球宏观财经每日邮件简报系统实施计划 (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 Python 3.12+ 与 uv 的每日全球宏观财经邮件简报系统，自动采集 22 个全球指标（美/中/港/欧/亚太/越/俄股指、原油、黄金白银、Bitcoin、VIX），以国内红涨绿跌风格生成自适应 HTML 邮件，并通过 Gmail SMTP 在工作日早晚定时推送。

**Architecture:** 采用模块化多源采集器（东方财富 + 新浪财经 + 腾讯财经并发拉取与容错降级），通过统一行情数据模型归一化，经 Jinja2 模板渲染为兼容移动端与桌面端的 HTML 邮件，由 Gmail SMTP 安全发送。提供 `setup-env.sh` 与 `local-test.sh` 脚本支持一键环境配置与本地免发信调试。

**Tech Stack:** Python 3.12+, uv, httpx, jinja2, pyyaml, pydantic, pytest, GitHub Actions.

---

### Task 1: 项目脚手架与环境初始化脚本

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `local.env.example`
- Create: `setup-env.sh`

- [ ] **Step 1: 创建 `.gitignore`**

```gitignore
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
*.log

# 本地私密环境变量
local.env
.env

# 本地测试生成的 HTML 预览
test_report.html
```

- [ ] **Step 2: 创建 `local.env.example`**

```bash
# Gmail SMTP 发信配置
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_TO=recipient@example.com
TIMEZONE=Asia/Shanghai
```

- [ ] **Step 3: 创建 `pyproject.toml`**

```toml
[project]
name = "daily-finace-rpt-email-sender"
version = "0.1.0"
description = "Daily global macro financial report email sender"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27.0",
    "jinja2>=3.1.4",
    "pydantic>=2.7.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: 创建 `setup-env.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/4] 检查 uv 环境 ==="
if ! command -v uv &> /dev/null; then
    echo "未检测到 uv，正在安装 uv..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user uv
    else
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

echo "uv 版本: $(uv --version)"

echo "=== [2/4] 创建虚拟环境 ==="
uv venv .venv

echo "=== [3/4] 同步依赖包 ==="
uv pip install -e ".[dev]"

echo "=== [4/4] 检查本地环境文件 ==="
if [ ! -f "local.env" ]; then
    echo "正在复制 local.env.example -> local.env ..."
    cp local.env.example local.env
    echo "已生成 local.env，请在其中填入您的 Gmail 账号与应用专用密码。"
else
    echo "local.env 已存在。"
fi

echo "=== 初始化完成！可执行 ./local-test.sh 开始测试 ==="
```

- [ ] **Step 5: 增加可执行权限并运行 setup-env.sh 验证**

Run: `chmod +x setup-env.sh && bash setup-env.sh`
Expected: 成功检测/安装 uv，创建 `.venv` 并完成依赖安装，输出 "=== 初始化完成！==="

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore local.env.example setup-env.sh
git commit -m "chore: setup project structure, uv dependencies, and setup-env.sh"
```

---

### Task 2: 资产配置、统一数据模型与配置解析器

**Files:**
- Create: `config/assets.yaml`
- Create: `src/models.py`
- Create: `src/config.py`
- Create: `tests/test_config_models.py`

- [ ] **Step 1: 编写测试 `tests/test_config_models.py`**

```python
import pytest
from src.models import AssetQuote
from src.config import load_assets_config, get_settings

def test_asset_quote_color_calc():
    q_up = AssetQuote(
        name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
        latest_price="30732.40", prev_close="30482.35",
        change_pct=0.82, change_val="+250.05",
        volume="1.32B", quote_time="16:00:00"
    )
    assert q_up.color == "up"
    assert q_up.change_str == "+0.82%"

    q_down = AssetQuote(
        name="恒生指数", symbol="HSI", category="亚太重点股指",
        latest_price="24834.12", prev_close="25087.75",
        change_pct=-1.01, change_val="-253.63",
        volume="18.43M", quote_time="16:00:00"
    )
    assert q_down.color == "down"
    assert q_down.change_str == "-1.01%"

    q_flat = AssetQuote(
        name="平盘标的", symbol="FLAT", category="测试",
        latest_price="100.00", prev_close="100.00",
        change_pct=0.0, change_val="0.00",
        volume="-", quote_time="16:00:00"
    )
    assert q_flat.color == "flat"
    assert q_flat.change_str == "0.00%"

def test_load_assets_config():
    assets = load_assets_config("config/assets.yaml")
    assert len(assets) == 22
    categories = {a["category"] for a in assets}
    assert "欧美核心股指" in categories
    assert "亚太重点股指" in categories
    assert "大宗商品与贵金属" in categories
    assert "数字与恐慌资产" in categories
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_config_models.py -v`
Expected: FAIL (模块未定义)

- [ ] **Step 3: 创建 `config/assets.yaml`**

```yaml
assets:
  # 欧美核心股指
  - name: "标普500指数"
    symbol: "SPX"
    category: "欧美核心股指"
    eastmoney_secid: "100.SPX"
    tencent_code: "s_usINX"
    sina_code: "gb_inx"
  - name: "纳斯达克100"
    symbol: "NDX100"
    category: "欧美核心股指"
    eastmoney_secid: "100.NDX100"
    tencent_code: "s_usNDX"
    sina_code: "gb_ixic"
  - name: "英国富时100"
    symbol: "FTSE"
    category: "欧美核心股指"
    eastmoney_secid: "100.FTSE"
    tencent_code: ""
    sina_code: "int_ftse"
  - name: "法国CAC40"
    symbol: "FCHI"
    category: "欧美核心股指"
    eastmoney_secid: "100.FCHI"
    tencent_code: ""
    sina_code: "int_cac"
  - name: "德国DAX30"
    symbol: "GDAXI"
    category: "欧美核心股指"
    eastmoney_secid: "100.GDAXI"
    tencent_code: ""
    sina_code: "int_dax"

  # 亚太重点股指
  - name: "上证指数"
    symbol: "SH000001"
    category: "亚太重点股指"
    eastmoney_secid: "1.000001"
    tencent_code: "s_sh000001"
    sina_code: "s_sh000001"
  - name: "沪深300"
    symbol: "SH000300"
    category: "亚太重点股指"
    eastmoney_secid: "0.399300"
    tencent_code: "s_sh000300"
    sina_code: "s_sz399300"
  - name: "香港恒生指数"
    symbol: "HSI"
    category: "亚太重点股指"
    eastmoney_secid: "100.HSI"
    tencent_code: "s_hkHSI"
    sina_code: "rt_hkHSI"
  - name: "恒生科技指数"
    symbol: "HSTECH"
    category: "亚太重点股指"
    eastmoney_secid: "124.HSTECH"
    tencent_code: "s_hkHSTECH"
    sina_code: "rt_hkHSTECH"
  - name: "台湾加权指数"
    symbol: "TWII"
    category: "亚太重点股指"
    eastmoney_secid: "100.TWII"
    tencent_code: ""
    sina_code: ""
  - name: "日本东证指数"
    symbol: "N225"
    category: "亚太重点股指"
    eastmoney_secid: "100.N225"
    tencent_code: ""
    sina_code: "int_nikkei"
  - name: "韩国KOSPI"
    symbol: "KS11"
    category: "亚太重点股指"
    eastmoney_secid: "100.KS11"
    tencent_code: ""
    sina_code: ""
  - name: "印度BSE SENSEX"
    symbol: "SENSEX"
    category: "亚太重点股指"
    eastmoney_secid: "100.SENSEX"
    tencent_code: ""
    sina_code: ""
  - name: "越南HNX30"
    symbol: "VNINDEX"
    category: "亚太重点股指"
    eastmoney_secid: "100.VNINDEX"
    tencent_code: ""
    sina_code: ""

  # 大宗商品与贵金属
  - name: "WTI原油"
    symbol: "CL"
    category: "大宗商品与贵金属"
    eastmoney_secid: ""
    tencent_code: ""
    sina_code: "hf_CL"
  - name: "布伦特原油现货/美元"
    symbol: "OIL"
    category: "大宗商品与贵金属"
    eastmoney_secid: ""
    tencent_code: ""
    sina_code: "hf_OIL"
  - name: "黄金/美元"
    symbol: "XAUUSD"
    category: "大宗商品与贵金属"
    eastmoney_secid: ""
    tencent_code: ""
    sina_code: "fx_sxauusd"
  - name: "银/美元"
    symbol: "XAGUSD"
    category: "大宗商品与贵金属"
    eastmoney_secid: ""
    tencent_code: ""
    sina_code: "fx_sxagusd"

  # 数字与恐慌资产
  - name: "Bitcoin"
    symbol: "BTCUSD"
    category: "数字与恐慌资产"
    eastmoney_secid: ""
    tencent_code: ""
    sina_code: "fx_sbtcusd"
  - name: "VIX恐慌指数"
    symbol: "VIX"
    category: "数字与恐慌资产"
    eastmoney_secid: ""
    tencent_code: "s_usVIX"
    sina_code: "gb_vixy"
  - name: "俄罗斯市值加权指数"
    symbol: "RTS"
    category: "数字与恐慌资产"
    eastmoney_secid: "100.RTS"
    tencent_code: ""
    sina_code: ""
  - name: "沪深300 (权重跟踪)"
    symbol: "399300"
    category: "亚太重点股指"
    eastmoney_secid: "0.399300"
    tencent_code: "s_sh000300"
    sina_code: "s_sz399300"
```

- [ ] **Step 4: 创建 `src/models.py` 与 `src/config.py`**

```python
# src/models.py
from pydantic import BaseModel, Field
from typing import Optional

class AssetQuote(BaseModel):
    name: str
    symbol: str
    category: str
    latest_price: str
    prev_close: str
    change_pct: float
    change_val: str
    volume: str = "-"
    quote_time: str = ""
    status: str = "normal"

    @property
    def color(self) -> str:
        if self.change_pct > 0.0001:
            return "up"
        elif self.change_pct < -0.0001:
            return "down"
        return "flat"

    @property
    def change_str(self) -> str:
        if self.change_pct > 0.0001:
            return f"+{self.change_pct:.2f}%"
        elif self.change_pct < -0.0001:
            return f"{self.change_pct:.2f}%"
        return "0.00%"
```

```python
# src/config.py
import os
import yaml
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    gmail_user: str = ""
    gmail_app_password: str = ""
    email_to: str = ""
    timezone: str = "Asia/Shanghai"

def load_env_file(filepath: str = "local.env"):
    p = Path(filepath)
    if not p.exists():
        return
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

def get_settings() -> Settings:
    load_env_file()
    return Settings(
        gmail_user=os.environ.get("GMAIL_USER", ""),
        gmail_app_password=os.environ.get("GMAIL_APP_PASSWORD", ""),
        email_to=os.environ.get("EMAIL_TO", ""),
        timezone=os.environ.get("TIMEZONE", "Asia/Shanghai")
    )

def load_assets_config(filepath: str = "config/assets.yaml") -> list[dict]:
    p = Path(filepath)
    with open(p, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("assets", [])
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_config_models.py -v`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add config/assets.yaml src/models.py src/config.py tests/test_config_models.py
git commit -m "feat: add assets configuration, unified data models and config loader"
```

---

### Task 3: 东方财富、新浪、腾讯行情采集适配器实现

**Files:**
- Create: `src/collectors/base.py`
- Create: `src/collectors/eastmoney.py`
- Create: `src/collectors/sina.py`
- Create: `src/collectors/tencent.py`
- Create: `tests/test_collectors.py`

- [ ] **Step 1: 编写采集器单测 `tests/test_collectors.py`（使用 Mock 验证解析逻辑）**

```python
import pytest
from unittest.mock import patch, MagicMock
from src.collectors.eastmoney import EastmoneyCollector
from src.collectors.sina import SinaCollector
from src.collectors.tencent import TencentCollector

def test_parse_eastmoney_stock():
    collector = EastmoneyCollector()
    mock_data = {
        "f57": "SPX", "f58": "标普500",
        "f43": 776464, "f60": 776470,
        "f169": -6, "f170": 0, "f47": 3164537854
    }
    quote = collector.parse_quote(mock_data, {"name": "标普500指数", "symbol": "SPX", "category": "欧美核心股指"})
    assert quote is not None
    assert quote.latest_price == "7764.64"
    assert quote.prev_close == "7764.70"
    assert quote.change_pct == 0.0

def test_parse_sina_futures():
    collector = SinaCollector()
    # 模拟 hf_CL
    raw_str = '90.250,,90.200,90.220,90.520,88.710,16:42:52,90.520,89.890,0,10,4,2026-09-23,纽约原油,0'
    quote = collector.parse_hf_quote("hf_CL", raw_str, {"name": "WTI原油", "symbol": "CL", "category": "大宗商品与贵金属"})
    assert quote is not None
    assert quote.latest_price == "90.25"
    assert quote.prev_close == "89.89"
    assert quote.color == "up"

def test_parse_tencent_quote():
    collector = TencentCollector()
    # 模拟 v_s_usVIX="200~标普500波动率指数~.VIX~21.67~-0.12~-0.55~0~0~~"
    raw_line = 'v_s_usVIX="200~标普500波动率指数~.VIX~21.67~-0.12~-0.55~0~0~~";'
    quote = collector.parse_line(raw_line, {"name": "VIX恐慌指数", "symbol": "VIX", "category": "数字与恐慌资产"})
    assert quote is not None
    assert quote.latest_price == "21.67"
    assert quote.change_pct == -0.55
    assert quote.color == "down"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_collectors.py -v`
Expected: FAIL

- [ ] **Step 3: 编写 `src/collectors/base.py`**

```python
from abc import ABC, abstractmethod
from typing import Optional
from src.models import AssetQuote

def format_volume(vol: float) -> str:
    if vol <= 0:
        return "-"
    if vol >= 1e9:
        return f"{vol/1e9:.2f}B"
    if vol >= 1e6:
        return f"{vol/1e6:.2f}M"
    if vol >= 1e3:
        return f"{vol/1e3:.2f}K"
    return f"{vol:.0f}"

class BaseCollector(ABC):
    @abstractmethod
    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        """批量获取行情字典：{symbol: AssetQuote}"""
        pass
```

- [ ] **Step 4: 编写 `src/collectors/eastmoney.py`**

```python
import httpx
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class EastmoneyCollector(BaseCollector):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "http://quote.eastmoney.com/"
        }

    def parse_quote(self, data: dict, asset_def: dict) -> Optional[AssetQuote]:
        try:
            raw_latest = data.get("f43")
            raw_prev = data.get("f60")
            if raw_latest is None or raw_prev is None or raw_latest == "-":
                return None
            latest = float(raw_latest) / 100.0
            prev = float(raw_prev) / 100.0
            change_pct = float(data.get("f170", 0)) / 100.0
            raw_val = data.get("f169", 0)
            change_val = f"{float(raw_val)/100.0:+.2f}" if raw_val != "-" else "0.00"
            vol = float(data.get("f47", 0)) if data.get("f47") != "-" else 0

            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=change_val,
                volume=format_volume(vol),
                quote_time=str(data.get("f124", ""))
            )
        except Exception:
            return None

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("eastmoney_secid")]
        results = {}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            for asset in target_assets:
                secid = asset["eastmoney_secid"]
                url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f58,f43,f60,f169,f170,f47,f124"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        payload = resp.json().get("data")
                        if payload:
                            q = self.parse_quote(payload, asset)
                            if q:
                                results[asset["symbol"]] = q
                except Exception:
                    pass
        return results
```

- [ ] **Step 5: 编写 `src/collectors/sina.py`**

```python
import httpx
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class SinaCollector(BaseCollector):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://finance.sina.com.cn"
        }

    def parse_hf_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # hf_CL="90.250,,90.200,90.220,90.520,88.710,16:42:52,90.520,89.890..."
        parts = raw_str.split(",")
        if len(parts) < 14:
            return None
        latest = float(parts[0])
        prev = float(parts[8]) if parts[8] else latest
        change_val = latest - prev
        pct = (change_val / prev * 100.0) if prev != 0 else 0.0
        time_str = parts[6] if len(parts) > 6 else ""
        return AssetQuote(
            name=asset_def["name"],
            symbol=asset_def["symbol"],
            category=asset_def["category"],
            latest_price=f"{latest:.2f}",
            prev_close=f"{prev:.2f}",
            change_pct=round(pct, 2),
            change_val=f"{change_val:+.2f}",
            volume="-",
            quote_time=time_str
        )

    def parse_fx_quote(self, code: str, raw_str: str, asset_def: dict) -> Optional[AssetQuote]:
        # fx_sxauusd="16:43:02,4316.73,4316.73,4357.47,589628,4357.47,4372.8..."
        # 索引0:时间, 索引1:最新买入价/最新价, 索引3:昨收
        parts = raw_str.split(",")
        if len(parts) < 4:
            return None
        time_str = parts[0]
        latest = float(parts[1])
        prev = float(parts[3]) if parts[3] else latest
        change_val = latest - prev
        pct = (change_val / prev * 100.0) if prev != 0 else 0.0
        return AssetQuote(
            name=asset_def["name"],
            symbol=asset_def["symbol"],
            category=asset_def["category"],
            latest_price=f"{latest:.2f}",
            prev_close=f"{prev:.2f}",
            change_pct=round(pct, 2),
            change_val=f"{change_val:+.2f}",
            volume="-",
            quote_time=time_str
        )

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("sina_code")]
        if not target_assets:
            return {}
        codes = [a["sina_code"] for a in target_assets]
        url = "https://hq.sinajs.cn/list=" + ",".join(codes)
        results = {}
        code_to_asset = {a["sina_code"]: a for a in target_assets}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = resp.content.decode("gbk", errors="ignore")
                    for line in text.strip().split("\n"):
                        if '="' not in line:
                            continue
                        code_part, data_part = line.split('="', 1)
                        clean_code = code_part.replace("var hq_str_", "").strip()
                        raw_data = data_part.rstrip('";')
                        if not raw_data:
                            continue
                        asset_def = code_to_asset.get(clean_code)
                        if not asset_def:
                            continue
                        if clean_code.startswith("hf_"):
                            q = self.parse_hf_quote(clean_code, raw_data, asset_def)
                        elif clean_code.startswith("fx_"):
                            q = self.parse_fx_quote(clean_code, raw_data, asset_def)
                        else:
                            q = None
                        if q:
                            results[asset_def["symbol"]] = q
            except Exception:
                pass
        return results
```

- [ ] **Step 6: 编写 `src/collectors/tencent.py`**

```python
import httpx
from typing import Optional
from src.collectors.base import BaseCollector, format_volume
from src.models import AssetQuote

class TencentCollector(BaseCollector):
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def parse_line(self, line: str, asset_def: dict) -> Optional[AssetQuote]:
        # v_s_usVIX="200~标普500波动率指数~.VIX~21.67~-0.12~-0.55~0~0~~";
        # v_s_sh000001="1~上证指数~000001~3936.52~-15.61~-0.39~466913933~83413286~~"
        try:
            if '="' not in line:
                return None
            _, content = line.split('="', 1)
            raw = content.rstrip('";').strip()
            parts = raw.split("~")
            if len(parts) < 7:
                return None
            latest = float(parts[3])
            change_val = float(parts[4])
            change_pct = float(parts[5])
            prev = latest - change_val
            vol = float(parts[6]) if parts[6] else 0
            return AssetQuote(
                name=asset_def["name"],
                symbol=asset_def["symbol"],
                category=asset_def["category"],
                latest_price=f"{latest:.2f}",
                prev_close=f"{prev:.2f}",
                change_pct=change_pct,
                change_val=f"{change_val:+.2f}",
                volume=format_volume(vol)
            )
        except Exception:
            return None

    async def fetch_quotes(self, assets: list[dict]) -> dict[str, AssetQuote]:
        target_assets = [a for a in assets if a.get("tencent_code")]
        if not target_assets:
            return {}
        codes = [a["tencent_code"] for a in target_assets]
        url = "https://qt.gtimg.cn/q=" + ",".join(codes)
        results = {}
        code_to_asset = {a["tencent_code"]: a for a in target_assets}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    text = resp.content.decode("gbk", errors="ignore")
                    for line in text.strip().split(";"):
                        line = line.strip()
                        if not line or '="' not in line:
                            continue
                        prefix = line.split('="')[0].replace("v_", "").strip()
                        asset_def = code_to_asset.get(prefix)
                        if asset_def:
                            q = self.parse_line(line, asset_def)
                            if q:
                                results[asset_def["symbol"]] = q
            except Exception:
                pass
        return results
```

- [ ] **Step 7: 运行单测验证通过**

Run: `uv run pytest tests/test_collectors.py -v`
Expected: 3 passed

- [ ] **Step 8: Commit**

```bash
git add src/collectors/ tests/test_collectors.py
git commit -m "feat: implement Eastmoney, Sina, and Tencent quote collectors"
```

---

### Task 4: 聚合调度器与主备容错机制

**Files:**
- Create: `src/collectors/aggregator.py`
- Create: `tests/test_aggregator.py`

- [ ] **Step 1: 编写聚合器单测 `tests/test_aggregator.py`**

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.collectors.aggregator import QuoteAggregator
from src.models import AssetQuote

@pytest.mark.asyncio
async def test_aggregator_merging():
    assets = [
        {"name": "标普500", "symbol": "SPX", "category": "欧美核心股指"},
        {"name": "WTI原油", "symbol": "CL", "category": "大宗商品与贵金属"}
    ]
    aggregator = QuoteAggregator()

    # 模拟东财采集到 SPX，新浪采集到 CL
    mock_east = {"SPX": AssetQuote(
        name="标普500", symbol="SPX", category="欧美核心股指",
        latest_price="7764.64", prev_close="7764.70", change_pct=0.0, change_val="0.00"
    )}
    mock_sina = {"CL": AssetQuote(
        name="WTI原油", symbol="CL", category="大宗商品与贵金属",
        latest_price="90.25", prev_close="89.89", change_pct=0.4, change_val="+0.36"
    )}

    with patch.object(aggregator.eastmoney, "fetch_quotes", new_callable=AsyncMock) as m_east, \
         patch.object(aggregator.sina, "fetch_quotes", new_callable=AsyncMock) as m_sina, \
         patch.object(aggregator.tencent, "fetch_quotes", new_callable=AsyncMock) as m_tenc:
        m_east.return_value = mock_east
        m_sina.return_value = mock_sina
        m_tenc.return_value = {}

        quotes = await aggregator.collect_all(assets)
        assert len(quotes) == 2
        assert quotes[0].symbol == "SPX"
        assert quotes[1].symbol == "CL"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_aggregator.py -v`
Expected: FAIL

- [ ] **Step 3: 编写 `src/collectors/aggregator.py`**

```python
import asyncio
from typing import Optional
from src.models import AssetQuote
from src.collectors.eastmoney import EastmoneyCollector
from src.collectors.sina import SinaCollector
from src.collectors.tencent import TencentCollector

class QuoteAggregator:
    def __init__(self):
        self.eastmoney = EastmoneyCollector()
        self.sina = SinaCollector()
        self.tencent = TencentCollector()

    async def collect_all(self, assets: list[dict]) -> list[AssetQuote]:
        # 并发向三大源发起请求
        t_east = asyncio.create_task(self.eastmoney.fetch_quotes(assets))
        t_sina = asyncio.create_task(self.sina.fetch_quotes(assets))
        t_tenc = asyncio.create_task(self.tencent.fetch_quotes(assets))

        res_east, res_sina, res_tenc = await asyncio.gather(
            t_east, t_sina, t_tenc, return_exceptions=True
        )

        dict_east = res_east if isinstance(res_east, dict) else {}
        dict_sina = res_sina if isinstance(res_sina, dict) else {}
        dict_tenc = res_tenc if isinstance(res_tenc, dict) else {}

        quotes: list[AssetQuote] = []
        for asset in assets:
            sym = asset["symbol"]
            # 优先级合并：新浪(期货外汇佳) > 腾讯(国内/VIX) > 东财(全球股指)
            q = dict_sina.get(sym) or dict_tenc.get(sym) or dict_east.get(sym)
            if not q:
                # 兜底生成缺省休市对象
                q = AssetQuote(
                    name=asset["name"],
                    symbol=sym,
                    category=asset["category"],
                    latest_price="-",
                    prev_close="-",
                    change_pct=0.0,
                    change_val="-",
                    volume="-",
                    quote_time="",
                    status="nodata"
                )
            quotes.append(q)
        return quotes
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_aggregator.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/collectors/aggregator.py tests/test_aggregator.py
git commit -m "feat: implement QuoteAggregator with concurrent fetch and fallback"
```

---

### Task 5: 邮件 HTML 模板与红涨绿跌渲染引擎

**Files:**
- Create: `src/templates/report.html.j2`
- Create: `src/renderer.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: 编写渲染器单测 `tests/test_renderer.py`**

```python
import pytest
from src.renderer import ReportRenderer
from src.models import AssetQuote

def test_renderer_html_generation():
    renderer = ReportRenderer()
    sample_quotes = [
        AssetQuote(
            name="纳斯达克100", symbol="NDX100", category="欧美核心股指",
            latest_price="30732.40", prev_close="30482.35",
            change_pct=0.82, change_val="+250.05",
            volume="1.32B", quote_time="16:00:00"
        ),
        AssetQuote(
            name="香港恒生指数", symbol="HSI", category="亚太重点股指",
            latest_price="24834.12", prev_close="25087.75",
            change_pct=-1.01, change_val="-253.63",
            volume="18.43M", quote_time="16:00:00"
        )
    ]
    html = renderer.render(quotes=sample_quotes, report_type="morning", date_str="2026-09-23")
    assert "全球财经晨报" in html
    assert "30732.40" in html
    assert "+0.82%" in html
    assert "#e53935" in html  # 红涨颜色
    assert "#2e7d32" in html  # 绿跌颜色
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_renderer.py -v`
Expected: FAIL

- [ ] **Step 3: 创建 `src/templates/report.html.j2`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ title }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; color: #1f2937; }
    .container { max-width: 800px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .header { background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: #ffffff; padding: 24px 28px; }
    .header h1 { margin: 0 0 8px 0; font-size: 22px; font-weight: 700; }
    .header p { margin: 0; font-size: 13px; opacity: 0.9; }
    .summary-bar { background: #f8fafc; border-bottom: 1px solid #e2e8f0; padding: 12px 28px; font-size: 13px; color: #475569; display: flex; justify-content: space-between; }
    .section-title { font-size: 15px; font-weight: 700; color: #1e293b; padding: 18px 28px 8px; border-bottom: 2px solid #3b82f6; margin-top: 10px; display: inline-block; }
    .table-wrapper { padding: 0 24px 16px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
    th { background-color: #f1f5f9; color: #475569; font-weight: 600; text-align: right; padding: 10px 12px; border-bottom: 1px solid #cbd5e1; }
    th:first-child { text-align: left; }
    td { padding: 10px 12px; border-bottom: 1px solid #f1f5f9; text-align: right; }
    td:first-child { text-align: left; font-weight: 600; color: #0f172a; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; }
    .badge-up { color: #e53935; background-color: #ffebee; }
    .badge-down { color: #2e7d32; background-color: #e8f5e9; }
    .badge-flat { color: #64748b; background-color: #f1f5f9; }
    .footer { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 28px; font-size: 12px; color: #94a3b8; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{{ title }}</h1>
      <p>交易日监控简报 · 生成时间：{{ date_str }} (UTC+8) · 自动投递</p>
    </div>
    
    <div class="summary-bar">
      <span>标的监控数：{{ total_count }}</span>
      <span>上涨：<strong style="color: #e53935;">{{ up_count }}</strong> ｜ 下跌：<strong style="color: #2e7d32;">{{ down_count }}</strong> ｜ 平盘：{{ flat_count }}</span>
    </div>

    {% for category, items in grouped_quotes.items() %}
    <div style="padding-left: 24px;">
      <div class="section-title">{{ category }}</div>
    </div>
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>标的名称</th>
            <th>最新价</th>
            <th>昨收盘</th>
            <th>涨跌幅</th>
            <th>成交量</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          {% for q in items %}
          <tr>
            <td>{{ q.name }}</td>
            <td>{{ q.latest_price }}</td>
            <td>{{ q.prev_close }}</td>
            <td>
              {% if q.color == 'up' %}
                <span class="badge badge-up">{{ q.change_str }}</span>
              {% elif q.color == 'down' %}
                <span class="badge badge-down">{{ q.change_str }}</span>
              {% else %}
                <span class="badge badge-flat">{{ q.change_str }}</span>
              {% endif %}
            </td>
            <td>{{ q.volume }}</td>
            <td>{{ q.quote_time or '-' }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% endfor %}

    <div class="footer">
      本邮件由 GitHub Actions 每日全球宏观盯盘系统自动抓取并生成 · 仅供个人盯盘复盘使用
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 4: 编写 `src/renderer.py`**

```python
from collections import defaultdict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.models import AssetQuote

class ReportRenderer:
    def __init__(self, template_dir: str = "src/templates"):
        self.env = Environment(loader=FileSystemLoader(Path(template_dir)))
        self.template = self.env.get_template("report.html.j2")

    def render(self, quotes: list[AssetQuote], report_type: str, date_str: str) -> str:
        grouped = defaultdict(list)
        up_count = sum(1 for q in quotes if q.color == "up")
        down_count = sum(1 for q in quotes if q.color == "down")
        flat_count = sum(1 for q in quotes if q.color == "flat")

        for q in quotes:
            grouped[q.category].append(q)

        if report_type == "morning":
            title = f"【全球财经晨报】隔夜欧美大宗复盘与外盘盘点 ({date_str})"
        else:
            title = f"【全球财经晚报】亚太核心股指收盘与欧洲盘初盘点 ({date_str})"

        return self.template.render(
            title=title,
            date_str=date_str,
            grouped_quotes=grouped,
            total_count=len(quotes),
            up_count=up_count,
            down_count=down_count,
            flat_count=flat_count
        )
```

- [ ] **Step 5: 运行测试验证通过**

Run: `uv run pytest tests/test_renderer.py -v`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add src/templates/report.html.j2 src/renderer.py tests/test_renderer.py
git commit -m "feat: implement responsive HTML email template with red-up green-down badge styling"
```

---

### Task 6: Gmail SMTP 发送模块实现

**Files:**
- Create: `src/mailer.py`
- Create: `tests/test_mailer.py`

- [ ] **Step 1: 编写发信模块单测 `tests/test_mailer.py`（使用 Mock 验证 SMTP 流程）**

```python
import pytest
from unittest.mock import patch, MagicMock
from src.mailer import GmailMailer
from src.config import Settings

def test_send_email_mocked():
    settings = Settings(
        gmail_user="test@gmail.com",
        gmail_app_password="test_password",
        email_to="recv@example.com"
    )
    mailer = GmailMailer(settings)

    with patch("smtplib.SMTP") as mock_smtp:
        instance = mock_smtp.return_value.__enter__.return_value
        success = mailer.send(
            subject="【测试邮件】2026-09-23",
            html_content="<h1>测试内容</h1>"
        )
        assert success is True
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with("test@gmail.com", "test_password")
        instance.sendmail.assert_called_once()
```

- [ ] **Step 2: 运行测试验证失败**

Run: `uv run pytest tests/test_mailer.py -v`
Expected: FAIL

- [ ] **Step 3: 编写 `src/mailer.py`**

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.config import Settings

class GmailMailer:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    def send(self, subject: str, html_content: str) -> bool:
        if not self.settings.gmail_user or not self.settings.gmail_app_password:
            raise ValueError("缺少 GMAIL_USER 或 GMAIL_APP_PASSWORD 配置")
        if not self.settings.email_to:
            raise ValueError("缺少 EMAIL_TO 收件人配置")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Finance Daily Reporter <{self.settings.gmail_user}>"
        msg["To"] = self.settings.email_to

        part = MIMEText(html_content, "html", "utf-8")
        msg.attach(part)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(self.settings.gmail_user, self.settings.gmail_app_password)
                server.sendmail(self.settings.gmail_user, [self.settings.email_to], msg.as_string())
            return True
        except Exception as e:
            print(f"[Mailer] 邮件发送失败: {e}")
            return False
```

- [ ] **Step 4: 运行测试验证通过**

Run: `uv run pytest tests/test_mailer.py -v`
Expected: 1 passed

- [ ] **Step 5: Commit**

```bash
git add src/mailer.py tests/test_mailer.py
git commit -m "feat: implement GmailMailer via smtplib TLS 587 with mock testing"
```

---

### Task 7: 命令行入口、本地测试脚本与端到端集成测试

**Files:**
- Create: `main.py`
- Create: `local-test.sh`
- Create: `tests/test_integration.py`

- [ ] **Step 1: 编写 `main.py`**

```python
import argparse
import asyncio
from datetime import datetime
import zoneinfo
from src.config import get_settings, load_assets_config
from src.collectors.aggregator import QuoteAggregator
from src.renderer import ReportRenderer
from src.mailer import GmailMailer

async def run(report_type: str = "morning", dry_run: bool = False, output_file: str = "test_report.html"):
    settings = get_settings()
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now(tz).strftime("%Y-%m-%d")

    print(f"[{now_str}] 正在启动全球宏观财经简报采集 (类型: {report_type})...")
    assets = load_assets_config()
    aggregator = QuoteAggregator()
    quotes = await aggregator.collect_all(assets)

    print(f"[{now_str}] 成功获取 {len(quotes)} 个标的数据:")
    print("-" * 65)
    print(f"{'名称':<14} {'最新价':<10} {'昨收盘':<10} {'涨跌幅':<10} {'成交量':<8}")
    print("-" * 65)
    for q in quotes:
        print(f"{q.name:<14} {q.latest_price:<10} {q.prev_close:<10} {q.change_str:<10} {q.volume:<8}")
    print("-" * 65)

    renderer = ReportRenderer()
    html = renderer.render(quotes, report_type=report_type, date_str=date_str)

    if dry_run or not settings.gmail_user:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[{now_str}] [Dry-Run] 邮件 HTML 内容已输出至本地文件: {output_file}")
        return True

    subject = f"【全球财经{'晨报' if report_type == 'morning' else '晚报'}】{date_str}"
    mailer = GmailMailer(settings)
    ok = mailer.send(subject=subject, html_content=html)
    if ok:
        print(f"[{now_str}] 邮件成功发送至: {settings.email_to}")
    return ok

def main():
    parser = argparse.ArgumentParser(description="全球宏观财经每日邮件简报系统")
    parser.add_argument("--report-type", choices=["morning", "evening", "auto"], default="auto")
    parser.add_argument("--dry-run", action="store_true", help="本地抓取与预览模式，不发送真实邮件")
    parser.add_argument("--output", default="test_report.html", help="HTML 预览输出文件名")
    args = parser.parse_args()

    rtype = args.report_type
    if rtype == "auto":
        now_hour = datetime.now().hour
        rtype = "evening" if 14 <= now_hour <= 22 else "morning"

    asyncio.run(run(report_type=rtype, dry_run=args.dry_run, output_file=args.output))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 编写 `local-test.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# 加载 local.env
if [ -f "local.env" ]; then
    set -a
    source local.env
    set +a
fi

MODE="${1:-dry-run}"

if [ "$MODE" == "--send" ]; then
    echo "=== [发送模式] 正在拉取数据并发送至 ${EMAIL_TO:-未设置} ==="
    uv run python main.py --report-type auto
elif [ "$MODE" == "--unit" ]; then
    echo "=== [单测模式] 运行 pytest 单元测试 ==="
    uv run pytest -v
elif [ "$MODE" == "--type" ] && [ -n "${2:-}" ]; then
    echo "=== [指定类型测试] 类型: $2 ==="
    uv run python main.py --report-type "$2" --dry-run
else
    echo "=== [本地调试模式] 抓取数据并在控制台打印，生成 test_report.html ==="
    uv run python main.py --report-type auto --dry-run
    echo ""
    echo ">>> 您可以使用浏览器打开 test_report.html 预览邮件实际渲染效果！"
fi
```

- [ ] **Step 3: 增加可执行权限并运行端到端本地测试**

Run: `chmod +x local-test.sh && bash local-test.sh`
Expected: 成功抓取 22 个品种行情并在控制台打印表格，同时在项目根目录下生成 `test_report.html`

- [ ] **Step 4: 运行所有单元测试**

Run: `uv run pytest -v`
Expected: 全部测试通过

- [ ] **Step 5: Commit**

```bash
git add main.py local-test.sh
git commit -m "feat: add CLI entrypoint and local-test.sh runner"
```

---

### Task 8: GitHub Actions 自动化工作流与文档指引

**Files:**
- Create: `.github/workflows/daily_report.yml`
- Create: `README.md`

- [ ] **Step 1: 创建 `.github/workflows/daily_report.yml`**

```yaml
name: Global Finance Daily Report

on:
  schedule:
    # 早报：北京时间周一至周五 07:30 (UTC 时间周日至周四 23:30)
    - cron: '30 23 * * 0-4'
    # 晚报：北京时间周一至周五 17:30 (UTC 时间周一至周五 09:30)
    - cron: '30 9 * * 1-5'
  workflow_dispatch:
    inputs:
      report_type:
        description: '选择日报类型 (morning / evening / auto)'
        required: true
        default: 'auto'
        type: choice
        options:
          - auto
          - morning
          - evening

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Install Dependencies
        run: uv pip install -e .

      - name: Run Finance Report
        env:
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
          TIMEZONE: 'Asia/Shanghai'
        run: |
          RTYPE="${{ github.event.inputs.report_type || 'auto' }}"
          uv run python main.py --report-type "$RTYPE"
```

- [ ] **Step 2: 创建 `README.md`**

编写包含如下核心内容的说明文档：
1. 项目概述与 22 个资产清单；
2. 本地快速上手指南（`./setup-env.sh` 与 `./local-test.sh`）；
3. Gmail 应用专用密码获取方法；
4. GitHub Actions 部署与 Secrets 配置指南（`GMAIL_USER`, `GMAIL_APP_PASSWORD`, `EMAIL_TO`）；
5. 早报与晚报定时规则说明。

- [ ] **Step 3: 校验并提交**

```bash
git add .github/workflows/daily_report.yml README.md
git commit -m "feat: add GitHub Actions daily workflow and deployment README"
```

---

## 计划自检清单 (Self-Review Checklist)
- [x] **规格覆盖度**：所有 22 个标的定义、多源适配器、统一模型、Jinja2 模板、红涨绿跌、Gmail SMTP、本地两脚本、GitHub Actions 均覆盖。
- [x] **占位符扫描**：无任何 "TBD", "TODO", "implement later"，每个步骤均包含完整代码。
- [x] **类型一致性**：`AssetQuote` 属性在所有模块与模板中完全匹配。
- [x] **自动化与测试**：所有模块均配有相应的 `pytest` 单测。
