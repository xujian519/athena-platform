#!/bin/bash
# 存储空间快速清理脚本
# 快速释放不必要的存储空间

echo "🧹 开始存储空间清理..."
echo "时间: $(date)"
echo "=================================="

# 1. 清理Docker相关文件
echo "🐳 清理Docker文件..."
docker system prune -a -f
docker volume prune -f

# 2. 清理日志文件
echo "📝 清理系统日志..."
sudo rm -rf /var/log/*.log.old
sudo rm -rf /var/log/journal/*
find ~/Library/Logs -name "*.log" -mtime +30 -delete

# 3. 清理临时文件
echo "🗂️ 清理临时文件..."
rm -rf /tmp/*
rm -rf ~/Downloads/*.dmg
rm -rf ~/Downloads/*.pkg
find ~/Downloads -name "*.zip" -mtime +7 -delete

# 4. 清理Athena平台缓存文件
echo "🚀 清理Athena缓存..."
find /Users/xujian/Athena工作平台 -name "*.pyc" -delete
find /Users/xujian/Athena工作平台 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find /Users/xujian/Athena工作平台 -name ".DS_Store" -delete

# 5. 压缩大文件
echo "📦 压缩历史数据..."
# 压缩日志文件
find /Users/xujian/Athena工作平台 -name "*.log" -mtime +7 -exec gzip {} \;
# 压缩历史数据文件
find /Users/xujian/Athena工作平台/data -name "*.json" -mtime +30 -exec gzip {} \;

# 6. 移动大文件到外置硬盘
EXTERNAL_DISK="/Volumes/xujian"
if [ -d "$EXTERNAL_DISK" ]; then
    echo "💾 移动文件到外置硬盘..."

    # 创建归档目录
    mkdir -p "$EXTERNAL_DISK/archive/patents"
    mkdir -p "$EXTERNAL_DISK/archive/models"
    mkdir -p "$EXTERNAL_DISK/archive/data"

    # 移动归档文件
    if [ -d "/Users/xujian/Athena工作平台/archive" ]; then
        mv /Users/xujian/Athena工作平台/archive/* "$EXTERNAL_DISK/archive/patents/" 2>/dev/null
    fi

    # 移动旧的模型文件
    find /Users/xujian/Athena工作平台/models -name "*.old" -exec mv {} "$EXTERNAL_DISK/archive/models/" \; 2>/dev/null

    # 移动大型数据集
    find /Users/xujian/Athena工作平台/data -name "*.backup" -exec mv {} "$EXTERNAL_DISK/archive/data/" \; 2>/dev/null
fi

# 7. 显示清理结果
echo ""
echo "📊 清理结果统计:"
echo "=================================="

# 显示磁盘使用情况
echo "💾 磁盘使用情况:"
df -h | grep -E "(Filesystem|/dev|Data)"

# 显示Athena平台空间使用
echo ""
echo "🚀 Athena平台空间使用:"
du -sh /Users/xujian/Athena工作平台/* 2>/dev/null | sort -hr | head -10

echo ""
echo "✅ 存储清理完成!"
echo "建议下一步:"
echo "1. 购买4TB外置硬盘 (约¥800)"
echo "2. 设置云存储备份 (阿里云OSS/腾讯云COS)"
echo "3. 考虑NAS家庭存储 (群晖DS220+)"
echo ""
echo "当前时间: $(date)"