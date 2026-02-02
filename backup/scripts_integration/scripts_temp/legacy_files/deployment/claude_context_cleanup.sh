#!/bin/bash
# Claude Code上下文清理脚本

echo "🧹 Claude Code上下文清理工具"
echo "================================"

# 1. 显示当前状态
echo ""
echo "📊 当前状态："
echo "历史记录大小: $(du -sh ~/.claude/history.jsonl | cut -f1)"
echo "Debug目录大小: $(du -sh ~/.claude/debug 2>/dev/null | cut -f1)"
echo "Todos数量: $(find ~/.claude/todos -name "*.json" 2>/dev/null | wc -l)"

# 2. 清理选项
echo ""
echo "🔧 清理选项："
echo "1) 清理历史记录（保留最近500条）"
echo "2) 清理debug目录"
echo "3) 清理完成的todos"
echo "4) 全面清理"
echo "5) 仅查看状态"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🔄 清理历史记录..."
        cp ~/.claude/history.jsonl ~/.claude/history.jsonl.backup
        tail -500 ~/.claude/history.jsonl.backup > ~/.claude/history.jsonl
        echo "✅ 历史记录已清理（保留最近500条）"
        ;;
    2)
        echo ""
        echo "🗑️ 清理debug目录..."
        rm -rf ~/.claude/debug/*
        echo "✅ Debug目录已清理"
        ;;
    3)
        echo ""
        echo "📝 清理完成的todos..."
        find ~/.claude/todos -name "*.json" -exec grep -l '"status":"completed"' {} \; | while read file; do
            rm "$file"
        done
        echo "✅ 已完成的todos已清理"
        ;;
    4)
        echo ""
        echo "🚀 全面清理..."
        # 清理历史记录
        cp ~/.claude/history.jsonl ~/.claude/history.jsonl.backup
        tail -500 ~/.claude/history.jsonl.backup > ~/.claude/history.jsonl

        # 清理debug
        rm -rf ~/.claude/debug/*

        # 清理完成的todos
        find ~/.claude/todos -name "*.json" -exec grep -l '"status":"completed"' {} \; | while read file; do
            rm "$file"
        done

        echo "✅ 全面清理完成"
        ;;
    5)
        echo ""
        echo "📋 当前状态："
        echo "历史记录大小: $(du -sh ~/.claude/history.jsonl | cut -f1)"
        echo "Debug目录大小: $(du -sh ~/.claude/debug 2>/dev/null | cut -f1)"
        echo "Todos数量: $(find ~/.claude/todos -name "*.json" 2>/dev/null | wc -l)"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 3. 显示清理后状态
echo ""
echo "📊 清理后状态："
echo "历史记录大小: $(du -sh ~/.claude/history.jsonl | cut -f1)"
echo "Debug目录大小: $(du -sh ~/.claude/debug 2>/dev/null | cut -f1)"
echo "Todos数量: $(find ~/.claude/todos -name "*.json" 2>/dev/null | wc -l)"

echo ""
echo "💡 建议：定期运行此脚本以保持Claude Code性能"
echo "📚 查看指南: cat /Users/xujian/Athena工作平台/documentation/claude_context_management_guide.md"