#!/bin/bash
# ============================================================================
# 阶段2补充：清理剩余core模块 - 达成<30目标
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 记录开始时的core子目录数
START_COUNT=$(ls -d core/*/ 2>/dev/null | wc -l | tr -d ' ')

log_section "🧹 阶段2补充：清理剩余core模块"
log_info "开始时core子目录数: $START_COUNT"
log_info "目标: <30"
echo ""

# ============================================================================
# 1. 删除废弃模块
# ============================================================================
log_section "🗑️  步骤1：删除废弃模块"

DEPRECATED_MODULES=(
    "core/deprecated_agents"
    "core/legacy"
)

for module in "${DEPRECATED_MODULES[@]}"; do
    if [ -d "$module" ]; then
        log_info "  删除: $module"
        rm -rf "$module"
    else
        log_warn "  跳过（不存在）: $module"
    fi
done

log_info "✅ 废弃模块已删除"
echo ""

# ============================================================================
# 2. 删除小模块（<=3个文件）
# ============================================================================
log_section "📦 步骤2：删除小模块（空壳或测试模块）"

# 使用Python脚本识别小模块
python3 << 'PYTHON_EOF'
import os
from pathlib import Path

core_path = Path("core")
small_modules = []

for subdir in core_path.iterdir():
    if not subdir.is_dir() or subdir.name.startswith('_'):
        continue

    # 跳过已整合的顶层目录
    if subdir.name in ['ai', 'infrastructure', 'framework']:
        continue

    # 统计非__init__.py的文件数
    files = list(subdir.rglob('*.py'))
    non_init_files = [f for f in files if f.name != '__init__.py']

    if len(non_init_files) <= 3:
        small_modules.append(subdir.name)

# 输出到文件供shell读取
with open('/tmp/small_modules.txt', 'w') as f:
    for module in small_modules:
        f.write(f"{module}\n")

print(f"识别到 {len(small_modules)} 个小模块")
PYTHON_EOF

# 读取并删除小模块
if [ -f /tmp/small_modules.txt ]; then
    SMALL_COUNT=$(wc -l < /tmp/small_modules.txt | tr -d ' ')
    log_info "识别到 $SMALL_COUNT 个小模块"

    while IFS= read -r module; do
        if [ -n "$module" ] && [ -d "core/$module" ]; then
            log_info "  删除小模块: core/$module"
            rm -rf "core/$module"
        fi
    done < /tmp/small_modules.txt

    log_info "✅ 小模块已删除"
else
    log_warn "未找到小模块列表"
fi

echo ""

# ============================================================================
# 3. 移动大模块到合适位置
# ============================================================================
log_section "📦 步骤3：移动大模块到合适位置"

# 3.1 移动 patents -> domains/patents
if [ -d "core/patents" ]; then
    log_info "  移动: core/patents -> domains/patents"
    mkdir -p "domains/patents"
    rsync -av "core/patents/" "domains/patents/"
    rm -rf "core/patents"
    log_info "✅ patents已移动到domains/"
fi

# 3.2 保留 tools 和 search 在core/
log_info "  保留: core/tools (63个文件)"
log_info "  保留: core/search (61个文件)"

echo ""

# ============================================================================
# 4. 整合知识图谱相关模块
# ============================================================================
log_section "🔗 步骤4：整合知识图谱相关模块"

KG_MODULES=(
    "core/kg"
    "core/kg_unified"
    "core/knowledge_graph"
    "core/knowledge"
    "core/knowledge_sync"
)

mkdir -p "core/knowledge_graph_unified"

for module in "${KG_MODULES[@]}"; do
    if [ -d "$module" ]; then
        module_name=$(basename "$module")
        log_info "  整合: $module -> core/knowledge_graph_unified/$module_name"
        mv "$module" "core/knowledge_graph_unified/$module_name" 2>/dev/null || rm -rf "$module"
    fi
done

log_info "✅ 知识图谱模块已整合"
echo ""

# ============================================================================
# 5. 整合法律相关模块
# ============================================================================
log_section "⚖️  步骤5：整合法律相关模块"

LEGAL_MODULES=(
    "core/legal"
    "core/legal_database"
    "core/legal_qa"
    "core/legal_world_model"
)

mkdir -p "domains/legal/core_modules"

for module in "${LEGAL_MODULES[@]}"; do
    if [ -d "$module" ]; then
        module_name=$(basename "$module")
        log_info "  移动: $module -> domains/legal/core_modules/$module_name"
        mv "$module" "domains/legal/core_modules/$module_name"
    fi
done

log_info "✅ 法律模块已整合到domains/legal/"
echo ""

# ============================================================================
# 6. 整合文档相关模块
# ============================================================================
log_section "📄 步骤6：整合文档相关模块"

DOC_MODULES=(
    "core/document_parser"
    "core/document_management"
    "core/document_export"
    "core/plan_documents"
)

mkdir -p "core/document_processing"

for module in "${DOC_MODULES[@]}"; do
    if [ -d "$module" ]; then
        module_name=$(basename "$module")
        log_info "  整合: $module -> core/document_processing/$module_name"
        mv "$module" "core/document_processing/$module_name"
    fi
done

log_info "✅ 文档模块已整合"
echo ""

# ============================================================================
# 7. 清理缓存和临时文件
# ============================================================================
log_section "🧹 步骤7：清理缓存和临时文件"

CACHE_DIRS=(
    "core/__pycache__"
    "core/.ruff_cache"
    "core/.pytest_cache"
)

for cache_dir in "${CACHE_DIRS[@]}"; do
    if [ -d "$cache_dir" ]; then
        log_info "  删除缓存: $cache_dir"
        rm -rf "$cache_dir"
    fi
done

log_info "✅ 缓存已清理"
echo ""

# ============================================================================
# 8. 验证结果
# ============================================================================
log_section "✅ 验证清理结果"

END_COUNT=$(ls -d core/*/ 2>/dev/null | wc -l | tr -d ' ')
REDUCTION=$((START_COUNT - END_COUNT))
PERCENT=$((REDUCTION * 100 / START_COUNT))

echo ""
log_info "📊 清理统计："
echo "  - 开始时: $START_COUNT 个子目录"
echo "  - 结束时: $END_COUNT 个子目录"
echo "  - 减少: $REDUCTION 个 ($PERCENT%)"
echo ""

if [ $END_COUNT -lt 30 ]; then
    log_info "🎉 已达成目标：core子目录数 < 30"
else
    log_warn "⚠️  未完全达成目标：当前 $END_COUNT 个（目标 <30）"
    log_warn "建议：继续检查剩余模块"
fi

echo ""
log_info "📁 保留的主要core模块："
ls -d core/*/ | grep -E "(tools|search|ai|infrastructure|framework|document_processing|knowledge_graph_unified)" | while read dir; do
    count=$(find "$dir" -name '*.py' | wc -l | tr -d ' ')
    echo "  - $(basename $dir): $count 个文件"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段2补充清理完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
