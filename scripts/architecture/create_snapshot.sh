#!/bin/bash
# ============================================================================
# Athena平台架构优化 - 代码快照系统
# ============================================================================
# 功能：
#   1. 完整代码库tar.gz打包
#   2. Git tag标记
#   3. 文件清单生成
#   4. MD5校验和
# ============================================================================

set -e  # 遇到错误立即退出

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
SNAPSHOT_DIR="$PROJECT_ROOT/backups/architecture-snapshots"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_NAME="snapshot-${TIMESTAMP}"
SNAPSHOT_PATH="$SNAPSHOT_DIR/$SNAPSHOT_NAME.tar.gz"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 创建备份目录
mkdir -p "$SNAPSHOT_DIR"

# 1. 创建快照
log_info "📦 创建代码快照..."
cd "$PROJECT_ROOT"

# 排除不需要备份的目录
EXCLUDE_DIRS=(
    "--exclude=*.pyc"
    "--exclude=__pycache__"
    "--exclude=.pytest_cache"
    "--exclude=htmlcov"
    "--exclude=.git"
    "--exclude=node_modules"
    "--exclude=models/*"
    "--exclude=data/*.db"
    "--exclude=*.log"
    "--exclude=backups"
)

tar -czf "$SNAPSHOT_PATH" "${EXCLUDE_DIRS[@]}" . 2>/dev/null || {
    log_error "快照创建失败"
    exit 1
}

log_info "✅ 快照已创建: $SNAPSHOT_PATH"

# 2. 计算文件大小
SIZE=$(du -h "$SNAPSHOT_PATH" | cut -f1)
log_info "📊 快照大小: $SIZE"

# 3. 生成文件清单
log_info "📝 生成文件清单..."
MANIFEST_PATH="$SNAPSHOT_DIR/${SNAPSHOT_NAME}.manifest"
tar -tzf "$SNAPSHOT_PATH" > "$MANIFEST_PATH"
FILE_COUNT=$(wc -l < "$MANIFEST_PATH")
log_info "✅ 文件清单: $MANIFEST_PATH ($FILE_COUNT 个文件)"

# 4. 计算MD5校验和
log_info "🔐 计算MD5校验和..."
MD5_PATH="$SNAPSHOT_DIR/${SNAPSHOT_NAME}.md5"
if command -v md5 &> /dev/null; then
    # macOS
    md5 -q "$SNAPSHOT_PATH" > "$MD5_PATH"
else
    # Linux
    md5sum "$SNAPSHOT_PATH" > "$MD5_PATH"
fi
MD5_HASH=$(cat "$MD5_PATH")
log_info "✅ MD5: $MD5_HASH"

# 5. 创建Git tag
log_info "🏷️  创建Git tag..."
TAG_NAME="architecture-snapshot-${TIMESTAMP}"
cd "$PROJECT_ROOT"
if git rev-parse --git-dir > /dev/null 2>&1; then
    git tag -a "$TAG_NAME" -m "Architecture snapshot before phase ${1:-none}" 2>/dev/null || true
    log_info "✅ Git tag: $TAG_NAME"
else
    log_warn "不是Git仓库，跳过tag创建"
fi

# 6. 生成快照元数据
META_PATH="$SNAPSHOT_DIR/${SNAPSHOT_NAME}.meta"
cat > "$META_PATH" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "snapshot_name": "$SNAPSHOT_NAME",
  "snapshot_path": "$SNAPSHOT_PATH",
  "size": "$SIZE",
  "file_count": $FILE_COUNT,
  "md5": "$MD5_HASH",
  "git_tag": "$TAG_NAME",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'N/A')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
}
EOF

log_info "✅ 元数据: $META_PATH"

# 7. 清理旧快照（保留最近10个）
log_info "🧹 清理旧快照..."
cd "$SNAPSHOT_DIR"
ls -t snapshot-*.tar.gz | tail -n +11 | xargs -r rm -f
ls -t snapshot-*.manifest | tail -n +11 | xargs -r rm -f
ls -t snapshot-*.md5 | tail -n +11 | xargs -r rm -f
ls -t snapshot-*.meta | tail -n +11 | xargs -r rm -f
log_info "✅ 旧快照已清理（保留最近10个）"

# 8. 输出摘要
echo ""
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "📦 快照创建完成！"
log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  快照文件: $SNAPSHOT_PATH"
echo "  文件清单: $MANIFEST_PATH"
echo "  MD5校验: $MD5_PATH"
echo "  元数据: $META_PATH"
echo "  Git Tag: $TAG_NAME"
echo ""
log_info "💾 使用以下命令恢复："
echo "  tar -xzf $SNAPSHOT_PATH -C /path/to/restore"
echo ""

# 9. 验证快照完整性
log_info "🔍 验证快照完整性..."
if tar -tzf "$SNAPSHOT_PATH" > /dev/null 2>&1; then
    log_info "✅ 快照验证通过"
else
    log_error "快照验证失败"
    exit 1
fi

exit 0
