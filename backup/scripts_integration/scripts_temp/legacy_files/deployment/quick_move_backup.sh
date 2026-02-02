#!/bin/bash

# 快速移动备份到外接硬盘

SOURCE_DIR="/Users/xujian/Athena工作平台/data/patents/backup/20251209"
EXTERNAL_DRIVE="/Volumes/xujian"  # xujian 外接硬盘

# 检查源目录
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ 源目录不存在: $SOURCE_DIR"
    exit 1
fi

# 计算源目录大小
echo "📊 计算备份大小..."
SOURCE_SIZE=$(du -sh "$SOURCE_DIR" | cut -f1)
echo "源目录大小: $SOURCE_SIZE"

# 检查外接硬盘
if [ ! -d "$EXTERNAL_DRIVE" ]; then
    echo "❌ 外接硬盘未找到: $EXTERNAL_DRIVE"
    echo "请检查外接硬盘是否已连接并更新脚本中的路径"
    exit 1
fi

# 检查可用空间
AVAILABLE_SPACE=$(df -h "$EXTERNAL_DRIVE" | awk 'NR==2 {print $4}')
echo "外接硬盘可用空间: $AVAILABLE_SPACE"

# 创建目标目录
TIMESTAMP=$(date +%Y%m%d)
TARGET_DIR="$EXTERNAL_DRIVE/Patent_Backup_$TIMESTAMP"

echo ""
echo "🚀 准备移动备份..."
echo "源目录: $SOURCE_DIR"
echo "目标目录: $TARGET_DIR"
echo ""

# 确认移动
read -p "确认移动备份到外接硬盘? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "移动已取消"
    exit 0
fi

# 创建目标目录
mkdir -p "$TARGET_DIR"

# 开始复制
echo "📦 开始复制文件..."
START_TIME=$(date +%s)

# 使用rsync复制，显示进度
rsync -avh --progress "$SOURCE_DIR/" "$TARGET_DIR/"

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "✅ 复制完成!"
echo "耗时: $ELAPSED 秒"

# 验证
echo "🔍 验证备份..."
SOURCE_FILES=$(find "$SOURCE_DIR" -type f | wc -l)
TARGET_FILES=$(find "$TARGET_DIR" -type f | wc -l)

echo "源文件数: $SOURCE_FILES"
echo "目标文件数: $TARGET_FILES"

if [ $SOURCE_FILES -eq $TARGET_FILES ]; then
    echo "✅ 验证成功!"

    # 询问是否删除原始备份
    echo ""
    read -p "是否删除原始备份以释放空间? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ 删除原始备份..."
        rm -rf "$SOURCE_DIR"
        echo "✅ 原始备份已删除"

        # 显示释放的空间
        echo "释放空间: $SOURCE_SIZE"
    fi

    # 创建符号链接
    LINK_DIR="/Users/xujian/Athena工作平台/data/patents/backup/external"
    if [ -L "$LINK_DIR" ]; then
        rm "$LINK_DIR"
    fi
    ln -s "$TARGET_DIR" "$LINK_DIR"
    echo "🔗 创建符号链接: $LINK_DIR"
else
    echo "❌ 验证失败!"
    exit 1
fi

echo ""
echo "✅ 备份移动完成!"
echo "您可以通过以下方式访问备份:"
echo "1. 直接访问外接硬盘"
echo "2. 通过符号链接: /Users/xujian/Athena工作平台/data/patents/backup/external"