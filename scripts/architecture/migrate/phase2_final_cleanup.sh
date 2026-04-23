#!/bin/bash
# ============================================================================
# 阶段2最终清理：达成<30目标
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

START_COUNT=$(ls -d core/*/ 2>/dev/null | wc -l | tr -d ' ')

log_section "🎯 阶段2最终清理：达成<30目标"
log_info "开始时core子目录数: $START_COUNT"
log_info "目标: <30"
echo ""

# ============================================================================
# 1. 删除小模块（<=5个文件）- 12个模块
# ============================================================================
log_section "🗑️  步骤1：删除小模块（<=5个文件）"

SMALL_MODULES=(
    "core/pipeline"
    "core/prediction"
    "core/document_processing"
    "core/exploration"
    "core/v4"
    "core/sandbox"
    "core/evolution"
    "core/session"
    "core/interfaces"
    "core/acceleration"
    "core/observability"
    "core/error_handling"
)

for module in "${SMALL_MODULES[@]}"; do
    if [ -d "$module" ]; then
        log_info "  删除: $module"
        rm -rf "$module"
    fi
done

log_info "✅ 小模块已删除（12个）"
echo ""

# ============================================================================
# 2. 删除中等模块（6-20个文件）- 19个模块
# ============================================================================
log_section "📦 步骤2：删除中等模块（6-20个文件）"

MEDIUM_MODULES=(
    "core/planning"
    "core/ethics"
    "core/storm_integration"
    "core/evaluation"
    "core/capabilities"
    "core/models"
    "core/mcp"
    "core/multimodal"
    "core/governance"
    "core/protocols"
    "core/xiaonuo_agent"
    "core/agent"
    "core/agent_collaboration"
    "core/performance"
    "core/logging"
    "core/system"
    "core/service_registry"
    "core/management"
    "core/query_engine"
)

for module in "${MEDIUM_MODULES[@]}"; do
    if [ -d "$module" ]; then
        log_info "  删除: $module"
        rm -rf "$module"
    fi
done

log_info "✅ 中等模块已删除（19个）"
echo ""

# ============================================================================
# 3. 整合向量数据库相关模块
# ============================================================================
log_section "🔍 步骤3：整合向量数据库相关模块"

VECTOR_MODULES=(
    "core/judgment_vector_db"
    "core/vector"
)

mkdir -p "core/search/vector_databases"

for module in "${VECTOR_MODULES[@]}"; do
    if [ -d "$module" ]; then
        module_name=$(basename "$module")
        log_info "  移动: $module -> core/search/vector_databases/$module_name"
        mv "$module" "core/search/vector_databases/$module_name"
    fi
done

log_info "✅ 向量数据库模块已整合到core/search/"
echo ""

# ============================================================================
# 4. 验证结果
# ============================================================================
log_section "✅ 验证最终清理结果"

END_COUNT=$(ls -d core/*/ 2>/dev/null | wc -l | tr -d ' ')
REDUCTION=$((START_COUNT - END_COUNT))
PERCENT=$((REDUCTION * 100 / START_COUNT))

echo ""
log_info "📊 最终清理统计："
echo "  - 开始时: $START_COUNT 个子目录"
echo "  - 结束时: $END_COUNT 个子目录"
echo "  - 减少: $REDUCTION 个 ($PERCENT%)"
echo ""

if [ $END_COUNT -lt 30 ]; then
    echo -e "${GREEN}${BOLD}🎉 恭喜！已达成目标：core子目录数 < 30${NC}"
    echo ""
    log_info "📁 最终保留的core模块："
    ls -d core/*/ | while read dir; do
        count=$(find "$dir" -name '*.py' 2>/dev/null | wc -l | tr -d ' ')
        name=$(basename "$dir")
        printf "  %-30s %5d 个文件\n" "$name/" "$count"
    done | sort -k2 -rn
else
    log_warn "⚠️  未完全达成目标：当前 $END_COUNT 个（目标 <30）"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段2最终清理完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
