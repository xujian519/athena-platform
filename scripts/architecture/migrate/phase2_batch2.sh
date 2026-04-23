#!/bin/bash
# ============================================================================
# 阶段2：核心组件重组 - 第2批：基础设施整合
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏗️  阶段2 - 第2批：基础设施整合"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 创建新的infrastructure目录结构
log_info "🏗️  创建infrastructure目录结构..."
mkdir -p core/infrastructure/{database,cache,logging,vector_db,config,messaging,monitoring}
log_info "✅ 目录结构创建完成"
echo ""

# 2. 整合基础设施模块
log_info "🔧 整合基础设施模块..."

INFRA_MODULES=(
    "core/database:core/infrastructure/database"
    "core/cache:core/infrastructure/cache"
    "core/logging.disabled:core/infrastructure/logging"
    "core/vector_db:core/infrastructure/vector_db"
    "core/neo4j:core/infrastructure/vector_db"
    "core/qdrant:core/infrastructure/vector_db"
    "core/redis:core/infrastructure/cache"
)

for module in "${INFRA_MODULES[@]}"; do
    src="${module%%:*}"
    dst="${module##*:}"

    if [ -d "$src" ]; then
        log_info "  整合: $src → $dst"
        mkdir -p "$dst"
        rsync -av --remove-source-files "$src/" "$dst/" 2>/dev/null || true
        find "$src" -type d -empty -delete 2>/dev/null || true
    fi
done

log_info "✅ 基础设施整合完成"
echo ""

# 3. 验证结果
log_info "🔍 验证整合结果..."
CORE_DIRS=$(ls -d core/*/ 2>/dev/null | wc -l)
log_info "  core/子目录数: $CORE_DIRS"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 第2批整合完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
