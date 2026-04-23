#!/bin/bash
# 备份清理脚本 - 提前执行
# 原定清理时间: 2026年4月28日
# 现在执行时间: 2026年4月21日

echo "🧹 开始清理备份目录..."
echo "原定清理时间: 2026年4月28日"
echo "实际执行时间: $(date)"
echo ""

# 统计备份大小
echo "📊 备份统计:"
if [ -d "/Users/xujian/Athena工作平台/core/patent.bak" ]; then
    size=$(du -sh /Users/xujian/Athena工作平台/core/patent.bak 2>/dev/null | cut -f1)
    echo "  core/patent.bak: $size"
fi

echo ""
echo "🗑️  清理备份目录..."

# 清理patent.bak备份
if [ -d "/Users/xujian/Athena工作平台/core/patent.bak" ]; then
    echo "  删除 core/patent.bak..."
    rm -rf /Users/xujian/Athena工作平台/core/patent.bak
    echo "  ✅ 已删除"
fi

# 清理其他.bak目录
find /Users/xujian/Athena工作平台 -type d -name "*.bak" ! -path "*/node_modules/*" ! -path "*/.git/*" 2>/dev/null | while read dir; do
    if [ -d "$dir" ]; then
        echo "  删除 $dir..."
        rm -rf "$dir"
        echo "  ✅ 已删除"
    fi
done

# 清理.nebula_backup文件
echo ""
echo "🗑️  清理备份文件..."
find /Users/xujian/Athena工作平台 -name "*.nebula_backup" ! -path "*/node_modules/*" ! -path "*/.git/*" 2>/dev/null | while read file; do
    if [ -f "$file" ]; then
        echo "  删除 $file..."
        rm -f "$file"
        echo "  ✅ 已删除"
    fi
done

echo ""
echo "✅ 备份清理完成！"
echo ""
echo "📊 清理结果:"
echo "  备份目录已清理"
echo "  磁盘空间已释放"
