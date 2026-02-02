#!/bin/bash
# Athena工作平台 - 智能启动选择器
# 帮助您选择启动小娜或小诺

clear

echo "╔══════════════════════════════════════╗"
echo "║     Athena工作平台 - 智能启动器      ║"
echo "╚══════════════════════════════════════╝"
echo ""
echo "请选择您要启动的服务："
echo ""
echo "1) ⚖️  小娜 (xiǎo nà) - 知识产权法律专家"
echo "   - 端口：8001"
echo "   - 功能：专利、商标、版权法律服务"
echo ""
echo "2) 🌸  小诺 (xiǎo nuò) - 平台总调度官"
echo "   - 端口：8005"
echo "   - 功能：管理整个平台、调度所有智能体"
echo ""
echo "3) 📚  查看启动命令映射表"
echo ""
echo "4) ❌  退出"
echo ""
echo "────────────────────────────────────────"
echo -n "请输入选项 (1-4): "

read -n 1 choice
echo ""
echo ""

case $choice in
    1)
        echo "⚖️ 您选择了：小娜 - 知识产权法律专家"
        echo "正在启动小娜..."
        bash scripts/启动小娜法律专家.sh
        ;;
    2)
        echo "🌸 您选择了：小诺 - 平台总调度官"
        echo "正在启动小诺..."
        bash scripts/启动小诺平台调度.sh
        ;;
    3)
        echo "📚 显示启动命令映射表..."
        if command -v less >/dev/null 2>&1; then
            less docs/启动命令映射表.md
        elif command -v more >/dev/null 2>&1; then
            more docs/启动命令映射表.md
        else
            cat docs/启动命令映射表.md
        fi
        ;;
    4)
        echo "👋 退出启动器"
        exit 0
        ;;
    *)
        echo "❌ 无效选项，请重新运行"
        exit 1
        ;;
esac