#!/bin/bash
# ============================================================================
# 批量修复剩余的import路径问题
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 批量修复剩余import路径问题"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建备份
BACKUP_DIR="backups/import-fix-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
log_info "📦 备份当前代码到: $BACKUP_DIR"
cp -r core tests "$BACKUP_DIR/" 2>/dev/null || true
echo ""

# 1. 修复 core.llm → core.ai.llm
log_info "🔄 修复 core.llm → core.ai.llm ..."
find . -name "*.py" -type f -exec sed -i '' 's/from core\.llm\./from core.ai.llm./g' {} \;
find . -name "*.py" -type f -exec sed -i '' 's/import core\.llm\./import core.ai.llm./g' {} \;
log_info "✅ core.llm → core.ai.llm"
echo ""

# 2. 修复 core.agent → core.framework.agents
log_info "🔄 修复 core.agent → core.framework.agents ..."
find . -name "*.py" -type f -exec sed -i '' 's/from core\.agent\./from core.framework.agents./g' {} \;
find . -name "*.py" -type f -exec sed -i '' 's/import core\.agent\./import core.framework.agents./g' {} \;
log_info "✅ core.agent → core.framework.agents"
echo ""

# 3. 修复 core.embedding → core.ai.embedding
log_info "🔄 修复 core.embedding → core.ai.embedding ..."
find . -name "*.py" -type f -exec sed -i '' 's/from core\.embedding\./from core.ai.embedding./g' {} \;
log_info "✅ core.embedding → core.ai.embedding"
echo ""

# 4. 修复 core.nlp → core.ai.nlp
log_info "🔄 修复 core.nlp → core.ai.nlp ..."
find . -name "*.py" -type f -exec sed -i '' 's/from core\.nlp\./from core.ai.nlp./g' {} \;
log_info "✅ core.nlp → core.ai.nlp"
echo ""

# 5. 修复 core.prompts → core.ai.prompts
log_info "🔄 修复 core.prompts → core.ai.prompts ..."
find . -name "*.py" -type f -exec sed -i '' 's/from core\.prompts\./from core.ai.prompts./g' {} \;
log_info "✅ core.prompts → core.ai.prompts"
echo ""

# 6. 修复 tests/core/agent → tests/core/framework/agents (目录重命名)
if [ -d "tests/core/agent" ] && [ ! -d "tests/core/framework/agents" ]; then
    log_info "🔄 重命名测试目录: tests/core/agent → tests/core/framework/agents"
    mkdir -p tests/core/framework
    mv tests/core/agent tests/core/framework/agents
    log_info "✅ 测试目录已重命名"
else
    log_info "ℹ️  测试目录重命名已跳过（可能已存在）"
fi
echo ""

# 7. 修复 tests/core/agents → tests/core/framework/agents (如果需要)
if [ -d "tests/core/agents" ] && [ ! -d "tests/core/framework/agents" ]; then
    log_info "🔄 重命名测试目录: tests/core/agents → tests/core/framework/agents"
    mkdir -p tests/core/framework
    mv tests/core/agents tests/core/framework/agents
    log_info "✅ 测试目录已重命名"
fi
echo ""

# 8. 修复Python 3.9的类型注解问题 (str | None → Optional[str])
log_info "🔄 修复Python 3.9类型注解兼容性..."
find tests/ -name "*.py" -type f -exec sed -i '' 's/\([a-zA-Z_][a-zA-Z0-9_]*\) | None/Optional[\1]/g' {} \;
find tests/ -name "*.py" -type f -exec sed -i '' 's/\([a-zA-Z_][a-zA-Z0-9_]*\) \| None/Optional[\1]/g' {} \;

# 确保导入Optional
for file in $(find tests/ -name "*.py" -type f); do
    if grep -q "Optional\[" "$file" && ! grep -q "from typing import.*Optional" "$file"; then
        # 添加Optional到typing导入
        sed -i '' 's/from typing import \([^)]*\)/from typing import \1, Optional/' "$file" || true
    fi
done
log_info "✅ Python 3.9类型注解已修复"
echo ""

# 验证
log_info "🔍 验证修复结果..."
REMAINING=$(python3 scripts/architecture/verify_imports.py 2>/dev/null | grep "发现需要更新的文件" | awk '{print $2}')

if [ "$REMAINING" = "0" ] || [ "$REMAINING" = "" ]; then
    log_info "✅ Import路径修复完成！"
else
    log_info "ℹ️  还有 $REMAINING 个文件需要检查（可能需要手动修复）"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Import路径批量修复完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 如需回滚，恢复备份："
echo "   cp -r $BACKUP_DIR/* ."
echo ""

exit 0
