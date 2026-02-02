#!/bin/bash

# Athena工作平台快速备份脚本
# Quick Backup Script for Athena Work Platform

echo "💾 Athena工作平台 - 快速备份"
echo "=================================="

# 检查时间
echo "🕐 备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 备份目录
BACKUP_DIR="/Users/xujian/Athena工作平台/backups"
DATA_DIR="/Users/xujian/Athena工作平台/data"
CONFIG_DIR="/Users/xujian/Athena工作平台/config"
LOGS_DIR="/Users/xujian/Athena工作平台/logs"

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

# 检查各目录大小
echo "📊 目录大小检查:"
if [ -d "$DATA_DIR" ]; then
    data_size=$(du -sh "$DATA_DIR" | cut -f1)
    echo "  📁 数据目录: $data_size"
fi

if [ -d "$CONFIG_DIR" ]; then
    config_size=$(du -sh "$CONFIG_DIR" | cut -f1)
    echo "  ⚙️ 配置目录: $config_size"
fi

if [d "$LOGS_DIR" ]; then
    logs_size=$(du -sh "$LOGS_DIR" | cut -f1)
    echo "  📋 日志目录: $logs_size"
fi

echo ""
echo "💾 备份选项:"
echo "  1. 📦 完整备份 (推荐)"
echo "  2. 📊 仅数据备份"
echo "  3. ⚙️ 仅配置备份"
echo "  4. 📋 仅日志备份"
echo "  5. 📋 列出备份"
echo "  6. 🧹 清理旧备份"
echo "  7. ⚙️ 备份设置"
echo ""

# 读取用户选择
read -p "请选择备份类型 (1-7): " choice

case $choice in
  1)
    echo ""
    echo "📦 开始完整备份..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --backup --backup-type full
    ;;

  2)
    echo ""
    echo "📊 开始数据备份..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --backup --backup-type data
    ;;

  3)
    echo ""
    echo "⚙️ 开始配置备份..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --backup --backup-type config
    ;;

  4)
    echo ""
    echo "📋 开始日志备份..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --backup --backup-type logs
    ;;

  5)
    echo ""
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --list
    ;;

  6)
    echo ""
    echo "🧹 清理30天前的旧备份..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --cleanup 30
    ;;

  7)
    echo ""
    echo "⚙️ 备份统计信息..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/backup_manager.py --stats
    ;;

  *)
    echo ""
    echo "❌ 无效选择，退出"
    exit 1
    ;;
esac

# 检查备份结果
echo ""
echo "📋 备份后检查:"
if [ -d "$BACKUP_DIR" ]; then
    backup_count=$(ls -1 "$BACKUP_DIR"/*.tar.gz 2>/dev/null | wc -l)
    backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    echo "  📦 备份文件数: $backup_count"
    echo "  💾 备份总大小: $backup_size"
else
    echo "  ❌ 备份目录不存在"
fi

echo ""
echo "⚡ 快速操作:"
echo "  🔄 定期备份: python3 scripts/system_operations/backup_manager.py --backup"
echo "  📋 查看备份: python3 scripts/system_operations/backup_manager.py --list"
echo "  📊 备份统计: python3 scripts/system_operations/backup_manager.py --stats"
echo "  🔍 验证备份: python3 scripts/system_operations/backup_manager.py --verify [backup_name]"
echo "  🧹 清理备份: python3 scripts/system_operations/backup_manager.py --cleanup [days]"
echo ""
echo "💡 定期备份建议:"
echo "  📅 每日数据备份: 0 2 * * * python3 scripts/utils/quick_backup.sh"
echo "  📅 每周完整备份: 0 3 * * 0 python3 scripts/utils/quick_backup.sh"
echo "  📅 每月清理: 每月1号执行 python3 scripts/utils/quick_backup.sh (选择6)"

echo ""
echo "✅ 快速备份完成"