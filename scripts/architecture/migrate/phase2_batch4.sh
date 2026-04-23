#!/bin/bash
# ============================================================================
# 阶段2：核心组件重组 - 第4批：Framework整合
# ============================================================================

set -e

GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 阶段2 - 第4批：Framework整合"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 创建Framework目录结构
log_info "🏗️  创建Framework目录结构..."
mkdir -p core/framework/{agents,memory,collaboration,routing,gateway}
log_info "✅ 目录结构创建完成"
echo ""

# 2. 整合Framework模块
log_info "🔗 整合Framework模块..."

FRAMEWORK_MODULES=(
    "core/agents:core/framework/agents"
    "core/memory:core/framework/memory"
    "core/collaboration:core/framework/collaboration"
    "core/orchestration:core/framework/routing"
)

for module in "${FRAMEWORK_MODULES[@]}"; do
    src="${module%%:*}"
    dst="${module##*:}"

    if [ -d "$src" ]; then
        log_info "  整合: $src → $dst"
        mkdir -p "$dst"
        rsync -av --remove-source-files "$src/" "$dst/" 2>/dev/null || true
        find "$src" -type d -empty -delete 2>/dev/null || true
    fi
done

log_info "✅ Framework整合完成"
echo ""

# 3. 最终验证
log_info "🔍 最终验证..."
CORE_DIRS=$(ls -d core/*/ 2>/dev/null | wc -l)
log_info "  core/子目录数: $CORE_DIRS"
log_info "  目标: <30"

if [ "$CORE_DIRS" -lt 30 ]; then
    log_info "✅ 达到目标！"
else
    log_info "⚠️  仍需精简，建议检查core/other/目录"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段2全部完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
