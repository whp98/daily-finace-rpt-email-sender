#!/usr/bin/env bash
set -euo pipefail

echo "=== [1/4] 检查 uv 环境 ==="
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

if ! command -v uv &> /dev/null; then
    echo "未检测到 uv，正在安装 uv..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user uv 2>/dev/null || pip3 install --break-system-packages --user uv 2>/dev/null || true
    fi
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

echo "uv 版本: $(uv --version)"

echo "=== [2/4] 创建虚拟环境 ==="
uv venv --allow-existing .venv

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
