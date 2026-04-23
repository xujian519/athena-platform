#!/bin/bash
# ============================================================================
# 阶段3：顶层目录聚合 - 工具脚本整合
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 阶段3：顶层目录聚合"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 创建新的scripts目录结构
log_info "🏗️  创建scripts目录结构..."
mkdir -p scripts/{dev,deploy,admin,automation}
log_info "✅ 目录结构创建完成"
echo ""

# 2. 分析和分类现有脚本
log_info "📊 分析现有脚本..."

# 分析tools/
if [ -d "tools" ]; then
    log_info "  整合 tools/ → scripts/"
    # 开发工具
    find tools/ -name "test*.sh" -o -name "lint*.sh" -o -name "format*.sh" 2>/dev/null | while read file; do
        [ -f "$file" ] && cp "$file" scripts/dev/ 2>/dev/null || true
    done
    # 部署工具
    find tools/ -name "deploy*.sh" -o -name "start*.sh" -o -name "stop*.sh" 2>/dev/null | while read file; do
        [ -f "$file" ] && cp "$file" scripts/deploy/ 2>/dev/null || true
    done
fi

# 分析cli/
if [ -d "cli" ]; then
    log_info "  整合 cli/ → scripts/"
    rsync -av cli/ scripts/automation/ 2>/dev/null || true
fi

# 分析utils/
if [ -d "utils" ]; then
    log_info "  整合 utils/ → scripts/admin/"
    rsync -av utils/ scripts/admin/ 2>/dev/null || true
fi

log_info "✅ 脚本整合完成"
echo ""

# 3. 统计根目录数
log_info "🔍 统计根目录..."
ROOT_DIRS=$(ls -d */ 2>/dev/null | wc -l)
log_info "  根目录数: $ROOT_DIRS (目标: <20)"
echo ""

# 4. 生成报告
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段3完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 下一步:"
echo "  1. 检查scripts/目录结构"
echo "  2. 验证脚本可执行性"
echo "  3. 清理旧目录（如确认无问题）"
echo ""

exit 0
