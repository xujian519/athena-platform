#!/bin/bash
# ============================================================================
# 批量更新import路径
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 批量更新import路径"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建备份
log_info "📦 创建备份..."
BACKUP_DIR="backups/import-update-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份关键文件
files_to_backup=(
    "core/framework/agents/legacy-athena/athena_enhanced.py"
    "domains/legal/core_modules/legal_qa/legal_world_qa_system.py"
    "scripts/migration/migrate.py"
    "scripts/xiaonuo/xiaonuo_simpler_launcher.py"
    "scripts/xiaonuo/xiaonuo_systems_launcher.py"
    "services/scripts/enhanced_perception_service.py"
    "tests/collaboration/test_multi_agent_collaboration.py"
    "tests/core/agents/test_scratchpad_agent_standalone.py"
    "tests/core/collaboration/test_collaboration_init.py"
    "tests/core/perception/test_factory.py"
    "tests/core/perception/test_integration.py"
    "tests/core/perception/test_integration_extended.py"
    "tests/core/perception/test_processor_performance.py"
    "tests/core/perception/test_text_processor.py"
    "tests/core/test_edge_cases.py"
)

for file in "${files_to_backup[@]}"; do
    if [ -f "$file" ]; then
        mkdir -p "$BACKUP_DIR/$(dirname $file)"
        cp "$file" "$BACKUP_DIR/$file"
    fi
done

log_info "✅ 备份完成: $BACKUP_DIR"
echo ""

# 执行批量替换
log_info "🔄 执行批量替换..."

# 1. core.collaboration → core.framework.collaboration
find . -name "*.py" -type f -exec sed -i '' 's/from core\.collaboration/from core.framework.collaboration/g' {} \;
log_info "✅ core.collaboration → core.framework.collaboration"

# 2. core.database → core.infrastructure.database
find . -name "*.py" -type f -exec sed -i '' 's/from core\.database/from core.infrastructure.database/g' {} \;
log_info "✅ core.database → core.infrastructure.database"

# 3. core.memory → core.framework.memory
find . -name "*.py" -type f -exec sed -i '' 's/from core\.memory/from core.framework.memory/g' {} \;
log_info "✅ core.memory → core.framework.memory"

# 4. core.perception → core.ai.perception
find . -name "*.py" -type f -exec sed -i '' 's/from core\.perception/from core.ai.perception/g' {} \;
log_info "✅ core.perception → core.ai.perception"

# 5. core.agents → core.framework.agents
find . -name "*.py" -type f -exec sed -i '' 's/from core\.agents/from core.framework.agents/g' {} \;
find . -name "*.py" -type f -exec sed -i '' 's/import core\.agents\.base_agent/import core.framework.agents.base_agent/g' {} \;
log_info "✅ core.agents → core.framework.agents"

echo ""

# 验证结果
log_info "🔍 验证结果..."
REMAINING=$(python3 scripts/architecture/verify_imports.py | grep "发现需要更新的文件" | awk '{print $2}')

if [ "$REMAINING" = "0" ] || [ "$REMAINING" = "" ]; then
    log_info "✅ 所有import路径已更新完成！"
else
    log_warn "⚠️  还有 $REMAINING 个文件需要手动检查"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Import路径更新完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 如需回滚，恢复备份："
echo "   cp -r $BACKUP_DIR/* ."
echo ""

exit 0
