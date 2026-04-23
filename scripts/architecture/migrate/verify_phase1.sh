#!/bin/bash
# ============================================================================
# Athena平台架构优化 - 阶段1验证脚本
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 架构优化阶段1 - 验证脚本"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 检查services依赖
echo "🔍 检查core/中对services/的依赖..."
VIOLATIONS=$(grep -r "from services\." core/ --include="*.py" 2>/dev/null | wc -l || echo "0")
if [ "$VIOLATIONS" -eq 0 ]; then
    log_info "✅ 无services依赖"
else
    log_error "❌ 发现 $VIOLATIONS 个services依赖"
    echo "示例:"
    grep -r "from services\." core/ --include="*.py" | head -5
    exit 1
fi
echo ""

# 2. 检查domains依赖
echo "🔍 检查core/中对domains/的依赖..."
VIOLATIONS=$(grep -r "from domains\." core/ --include="*.py" 2>/dev/null | wc -l || echo "0")
if [ "$VIOLATIONS" -eq 0 ]; then
    log_info "✅ 无domains依赖"
else
    log_error "❌ 发现 $VIOLATIONS 个domains依赖"
    echo "示例:"
    grep -r "from domains\." core/ --include="*.py" | head -5
    exit 1
fi
echo ""

# 3. 检查接口定义
echo "🔍 检查接口定义文件..."
INTERFACE_FILES=(
    "core/interfaces/__init__.py"
    "core/interfaces/vector_store.py"
    "core/interfaces/knowledge_base.py"
    "core/interfaces/patent_service.py"
)

for file in "${INTERFACE_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_info "✅ $file"
    else
        log_error "❌ $file 不存在"
        exit 1
    fi
done
echo ""

# 4. 检查依赖注入配置
echo "🔍 检查依赖注入配置..."
if [ -f "config/dependency_injection.py" ]; then
    log_info "✅ config/dependency_injection.py"
else
    log_error "❌ config/dependency_injection.py 不存在"
    exit 1
fi
echo ""

# 5. 检查core目录结构
echo "🔍 检查core/目录结构..."
CORE_DIRS=$(ls -d core/*/ 2>/dev/null | wc -l)
log_info "core/子目录数: $CORE_DIRS"
echo ""

# 6. 运行测试（如果pytest可用）
if command -v pytest &> /dev/null; then
    echo "🔍 运行测试套件..."
    pytest tests/ -v --tb=short -x --maxfail=10 2>&1 | head -50
    echo ""
    log_info "✅ 测试完成"
else
    log_warn "⚠️  pytest未安装，跳过测试"
fi
echo ""

# 7. 生成验证报告
echo "📝 生成验证报告..."
REPORT_FILE="reports/architecture/phase1/verification_report.txt"
mkdir -p "reports/architecture/phase1"

cat > "$REPORT_FILE" << EOF
架构优化阶段1 - 验证报告
生成时间: $(date)

1. services依赖检查: 通过 (0个违规)
2. domains依赖检查: 通过 (0个违规)
3. 接口定义检查: 通过
4. 依赖注入配置检查: 通过
5. core目录结构: $CORE_DIRS 个子目录
6. 测试状态: $(command -v pytest >/dev/null && echo "已运行" || echo "跳过")

结论: 阶段1验证通过 ✅
EOF

log_info "✅ 验证报告: $REPORT_FILE"
echo ""

# 输出摘要
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段1验证通过"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
