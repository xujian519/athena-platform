#!/bin/bash
# Athena工作平台临时文件清理脚本
# Cleanup script for temporary files

# 设置项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 记录清理开始时间
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')
CLEANUP_LOG="$PROJECT_ROOT/logs/cleanup_$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

echo "======================================" | tee -a "$CLEANUP_LOG"
echo "Athena工作平台临时文件清理" | tee -a "$CLEANUP_LOG"
echo "开始时间: $START_TIME" | tee -a "$CLEANUP_LOG"
echo "======================================" | tee -a "$CLEANUP_LOG"

# 1. 清理 Python 缓存文件
echo "" | tee -a "$CLEANUP_LOG"
echo "1. 清理 Python 缓存文件..." | tee -a "$CLEANUP_LOG"
PYCACHE_COUNT=0
PYCACHE_SIZE=0

# 删除 __pycache__ 目录
while IFS= read -r dir; do
    if [ -d "$dir" ]; then
        SIZE=$(du -sb "$dir" | cut -f1)
        rm -rf "$dir"
        PYCACHE_COUNT=$((PYCACHE_COUNT + 1))
        PYCACHE_SIZE=$((PYCACHE_SIZE + SIZE))
        echo "  已删除: $dir ($(du -sh "$dir" 2>/dev/null | cut -f1))" | tee -a "$CLEANUP_LOG"
    fi
done < <(find "$PROJECT_ROOT" -type d -name "__pycache__" 2>/dev/null)

# 删除 .pyc 文件
PYC_COUNT=$(find "$PROJECT_ROOT" -name "*.pyc" -type f 2>/dev/null | wc -l)
if [ $PYC_COUNT -gt 0 ]; then
    find "$PROJECT_ROOT" -name "*.pyc" -type f -delete 2>/dev/null
    echo "  已删除 $PYC_COUNT 个 .pyc 文件" | tee -a "$CLEANUP_LOG"
fi

# 删除 .pyo 文件
PYO_COUNT=$(find "$PROJECT_ROOT" -name "*.pyo" -type f 2>/dev/null | wc -l)
if [ $PYO_COUNT -gt 0 ]; then
    find "$PROJECT_ROOT" -name "*.pyo" -type f -delete 2>/dev/null
    echo "  已删除 $PYO_COUNT 个 .pyo 文件" | tee -a "$CLEANUP_LOG"
fi

echo "  Python 缓存清理完成: $PYCACHE_COUNT 个目录, $PYC_COUNT 个 .pyc 文件, $PYO_COUNT 个 .pyo 文件" | tee -a "$CLEANUP_LOG"
echo "  释放空间: $((PYCACHE_SIZE / 1024 / 1024)) MB" | tee -a "$CLEANUP_LOG"

# 2. 清理临时和运行时文件
echo "" | tee -a "$CLEANUP_LOG"
echo "2. 清理临时和运行时文件..." | tee -a "$CLEANUP_LOG"

# 清理 temp 目录
TEMP_DIRS=("temp" "tmp" ".runtime")
for temp_dir in "${TEMP_DIRS[@]}"; do
    if [ -d "$PROJECT_ROOT/$temp_dir" ]; then
        SIZE_BEFORE=$(du -sb "$PROJECT_ROOT/$temp_dir" 2>/dev/null | cut -f1)
        # 删除超过7天的文件
        find "$PROJECT_ROOT/$temp_dir" -type f -mtime +7 -delete 2>/dev/null
        # 清理空的子目录
        find "$PROJECT_ROOT/$temp_dir" -type d -empty -delete 2>/dev/null
        SIZE_AFTER=$(du -sb "$PROJECT_ROOT/$temp_dir" 2>/dev/null | cut -f1)
        FREED=$((SIZE_BEFORE - SIZE_AFTER))
        echo "  清理 $temp_dir/: 释放 $((FREED / 1024 / 1024)) MB" | tee -a "$CLEANUP_LOG"
    fi
done

# 3. 清理日志文件
echo "" | tee -a "$CLEANUP_LOG"
echo "3. 清理过期日志文件..." | tee -a "$CLEANUP_LOG"

# 保留最近30天的日志
if [ -d "$PROJECT_ROOT/logs" ]; then
    LOG_SIZE_BEFORE=$(du -sb "$PROJECT_ROOT/logs" 2>/dev/null | cut -f1)
    find "$PROJECT_ROOT/logs" -name "*.log" -type f -mtime +30 -delete 2>/dev/null
    LOG_SIZE_AFTER=$(du -sb "$PROJECT_ROOT/logs" 2>/dev/null | cut -f1)
    LOG_FREED=$((LOG_SIZE_BEFORE - LOG_SIZE_AFTER))
    echo "  清理过期日志: 释放 $((LOG_FREED / 1024 / 1024)) MB" | tee -a "$CLEANUP_LOG"
fi

# 4. 清理备份文件
echo "" | tee -a "$CLEANUP_LOG"
echo "4. 清理备份文件..." | tee -a "$CLEANUP_LOG"

# 删除编辑器备份文件
find "$PROJECT_ROOT" -name "*.bak" -type f -delete 2>/dev/null
find "$PROJECT_ROOT" -name "*~" -type f -delete 2>/dev/null
find "$PROJECT_ROOT" -name ".#*" -type f -delete 2>/dev/null
find "$PROJECT_ROOT" -name "#*#" -type f -delete 2>/dev/null

# 5. 清理系统文件
echo "" | tee -a "$CLEANUP_LOG"
echo "5. 清理系统文件..." | tee -a "$CLEANUP_LOG"

# 删除 .DS_Store 文件
DSSTORE_COUNT=$(find "$PROJECT_ROOT" -name ".DS_Store" -type f 2>/dev/null | wc -l)
if [ $DSSTORE_COUNT -gt 0 ]; then
    find "$PROJECT_ROOT" -name ".DS_Store" -type f -delete 2>/dev/null
    echo "  已删除 $DSSTORE_COUNT 个 .DS_Store 文件" | tee -a "$CLEANUP_LOG"
fi

# 6. 清理 Docker 临时文件
echo "" | tee -a "$CLEANUP_LOG"
echo "6. 清理 Docker 临时文件..." | tee -a "$CLEANUP_LOG"

# 清理未使用的 Docker 镜像和容器
if command -v docker >/dev/null 2>&1; then
    echo "  清理 Docker 容器..." | tee -a "$CLEANUP_LOG"
    docker container prune -f >/dev/null 2>&1
    echo "  清理 Docker 镜像..." | tee -a "$CLEANUP_LOG"
    docker image prune -f >/dev/null 2>&1
    echo "  Docker 清理完成" | tee -a "$CLEANUP_LOG"
fi

# 7. 统计清理结果
echo "" | tee -a "$CLEANUP_LOG"
echo "======================================" | tee -a "$CLEANUP_LOG"
echo "清理统计" | tee -a "$CLEANUP_LOG"
echo "======================================" | tee -a "$CLEANUP_LOG"

# 计算总释放空间
SIZE_BEFORE=$(du -sb "$PROJECT_ROOT" 2>/dev/null | cut -f1)
sleep 1  # 确保文件系统同步
SIZE_AFTER=$(du -sb "$PROJECT_ROOT" 2>/dev/null | cut -f1)
TOTAL_FREED=$((SIZE_BEFORE - SIZE_AFTER))

echo "总释放空间: $((TOTAL_FREED / 1024 / 1024)) MB" | tee -a "$CLEANUP_LOG"
echo "项目当前大小: $(du -sh "$PROJECT_ROOT" | cut -f1)" | tee -a "$CLEANUP_LOG"

# 8. 更新 .gitignore（如果需要）
GITIGNORE_FILE="$PROJECT_ROOT/.gitignore"
if [ -f "$GITIGNORE_FILE" ]; then
    echo "" | tee -a "$CLEANUP_LOG"
    echo "8. 检查 .gitignore 配置..." | tee -a "$CLEANUP_LOG"
    
    # 检查是否包含了必要的忽略规则
    NEEDED_IGNORE=(
        "__pycache__/"
        "*.py[cod]"
        "*.pyo"
        "*.pyd"
        ".Python"
        ".DS_Store"
        ".env.*"
        "temp/"
        "tmp/"
        ".runtime/"
        "logs/"
        "*.log"
        "*.bak"
        "*~"
    )
    
    for pattern in "${NEEDED_IGNORE[@]}"; do
        if ! grep -q "^$pattern$" "$GITIGNORE_FILE"; then
            echo "$pattern" >> "$GITIGNORE_FILE"
            echo "  添加到 .gitignore: $pattern" | tee -a "$CLEANUP_LOG"
        fi
    done
fi

# 记录清理结束时间
END_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "" | tee -a "$CLEANUP_LOG"
echo "清理完成时间: $END_TIME" | tee -a "$CLEANUP_LOG"
echo "清理日志: $CLEANUP_LOG" | tee -a "$CLEANUP_LOG"
echo "======================================" | tee -a "$CLEANUP_LOG"

# 输出简短摘要
echo ""
echo "✨ 清理完成！"
echo "📊 释放空间: $((TOTAL_FREED / 1024 / 1024)) MB"
echo "📝 详细日志: $CLEANUP_LOG"