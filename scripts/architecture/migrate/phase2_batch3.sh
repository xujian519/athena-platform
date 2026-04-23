#!/bin/bash
# ============================================================================
# 阶段2：核心组件重组 - 第3批：AI模块整合
# ============================================================================

set -e

GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 阶段2 - 第3批：AI模块整合"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 创建AI目录结构
log_info "🏗️  创建AI目录结构..."
mkdir -p core/ai/{llm,embedding,prompts,intelligence,cognition,nlp,perception}
log_info "✅ 目录结构创建完成"
echo ""

# 2. 整合AI模块
log_info "🤖 整合AI模块..."

AI_MODULES=(
    "core/llm:core/ai/llm"
    "core/embedding:core/ai/embedding"
    "core/prompts:core/ai/prompts"
    "core/intelligence:core/ai/intelligence"
    "core/cognition:core/ai/cognition"
    "core/nlp:core/ai/nlp"
    "core/perception:core/ai/perception"
)

for module in "${AI_MODULES[@]}"; do
    src="${module%%:*}"
    dst="${module##*:}"

    if [ -d "$src" ]; then
        log_info "  整合: $src → $dst"
        mkdir -p "$dst"
        rsync -av --remove-source-files "$src/" "$dst/" 2>/dev/null || true
        find "$src" -type d -empty -delete 2>/dev/null || true
    fi
done

log_info "✅ AI模块整合完成"
echo ""

# 3. 验证结果
log_info "🔍 验证整合结果..."
CORE_DIRS=$(ls -d core/*/ 2>/dev/null | wc -l)
log_info "  core/子目录数: $CORE_DIRS"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 第3批整合完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
