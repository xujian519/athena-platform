#!/bin/bash
# ============================================================================
# 阶段4：数据治理 - 数据去重
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 阶段4：数据治理"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 创建assets目录
log_info "🏗️  创建assets目录..."
mkdir -p assets/{legal-knowledge,patent-data,models}
log_info "✅ 目录结构创建完成"
echo ""

# 2. 对比和去重
log_info "🔍 对比data/和domains/数据..."

if [ -d "data/legal-docs" ] && [ -d "domains/legal-knowledge" ]; then
    log_info "  发现重复数据: data/legal-docs 和 domains/legal-knowledge"

    # 对比
    if diff -rq "data/legal-docs" "domains/legal-knowledge" >/dev/null 2>&1; then
        log_info "  ✅ 数据完全一致，执行去重"

        # 备份domains下的数据
        mv "domains/legal-knowledge" "domains/legal-knowledge.backup"

        # 迁移data到assets
        mv "data/legal-docs" "assets/legal-knowledge"

        log_info "✅ 数据去重完成"
    else
        log_warn "  ⚠️  数据不完全一致，需人工检查"
    fi
fi

echo ""

# 3. 完善.gitignore
log_info "📝 完善.gitignore..."

GITIGNORE_ADDITIONS="
# 运行时数据
*.db
*.sqlite
*.log
*.pid

# 报告和临时文件
*_report.json
*_report.md
build/reports/
htmlcov/
.pytest_cache/

# 备份目录
scripts.backup.*
*.backup
*.bak

# 模型文件（大文件）
models/*.bin
models/*.safetensors
*.gguf

# 数据文件（运行时生成）
data/cache/
data/temp/
data/logs/

# 架构优化临时文件
core.backup.*
domains/*.backup
"

if [ -f ".gitignore" ]; then
    echo "$GITIGNORE_ADDITIONS" >> .gitignore
    log_info "✅ .gitignore已更新"
else
    echo "$GITIGNORE_ADDITIONS" > .gitignore
    log_info "✅ .gitignore已创建"
fi

echo ""

# 4. 清理历史备份
log_info "🧹 清理历史备份..."
find . -maxdepth 1 -type d -name "*.backup*" -exec rm -rf {} + 2>/dev/null || true
find . -maxdepth 1 -type d -name "*_backup" -exec rm -rf {} + 2>/dev/null || true
log_info "✅ 历史备份已清理"
echo ""

# 5. 验证结果
log_info "🔍 验证数据治理结果..."

if [ -d "assets/legal-knowledge" ]; then
    ASSETS_SIZE=$(du -sh assets/legal-knowledge | cut -f1)
    log_info "  assets/legal-knowledge/: $ASSETS_SIZE"
fi

if [ -d "data/legal-docs" ]; then
    log_warn "  ⚠️  data/legal-docs/ 仍存在"
else
    log_info "  ✅ data/legal-docs/ 已清理"
fi

if [ -d "domains/legal-knowledge" ]; then
    log_warn "  ⚠️  domains/legal-knowledge/ 仍存在"
else
    log_info "  ✅ domains/legal-knowledge/ 已清理"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段4完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
