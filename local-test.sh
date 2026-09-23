#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# 加载 local.env (如果存在)
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
    echo "=========================================================================="
    echo ">>> 成功！您可以使用浏览器打开 test_report.html 预览邮件实际渲染效果！"
    echo "=========================================================================="
fi
