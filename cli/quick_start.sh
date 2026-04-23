#!/bin/bash
# Athena CLI MVP 快速启动脚本

echo "🌸 Athena CLI MVP - 快速启动"
echo "=================================="
echo ""

cd "$(dirname "$0")"

echo "Step 1: 安装依赖..."
poetry install

echo ""
echo "Step 2: 运行测试..."
poetry run pytest tests/ -v

echo ""
echo "Step 3: 测试基本命令..."
poetry run python -m athena_cli.main hello

echo ""
echo "✅ MVP环境已准备就绪！"
echo ""
echo "试试这些命令:"
echo "  poetry run python -m athena_cli.main status"
echo "  poetry run python -m athena_cli.main search patent \"AI专利\" -n 5"
echo "  poetry run python -m athena_cli.main analyze 201921401279.9"
