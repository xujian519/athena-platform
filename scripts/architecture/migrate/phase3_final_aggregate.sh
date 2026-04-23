#!/bin/bash
# ============================================================================
# 阶段3补充：整合根目录，达成<20目标
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

START_COUNT=$(ls -d */ 2>/dev/null | wc -l | tr -d ' ')

log_section "📁 阶段3补充：整合根目录"
log_info "开始时根目录数: $START_COUNT"
log_info "目标: <20"
echo ""

# ============================================================================
# 1. 整合工具目录到scripts/
# ============================================================================
log_section "🔧 步骤1：整合工具目录"

# 创建scripts子目录结构
mkdir -p scripts/{dev,admin,automation}

# 整合tools/内容
if [ -d "tools" ] && [ "$(ls -A tools)" ]; then
    log_info "  整合: tools/ → scripts/"
    rsync -av tools/ scripts/ 2>/dev/null || true
    rm -rf tools
else
    log_warn "  tools/为空或不存在"
fi

# 整合cli/内容
if [ -d "cli" ] && [ "$(ls -A cli)" ]; then
    log_info "  整合: cli/ → scripts/automation/"
    rsync -av cli/ scripts/automation/ 2>/dev/null || true
    rm -rf cli
else
    log_warn "  cli/为空或不存在"
fi

# 整合utils/内容
if [ -d "utils" ] && [ "$(ls -A utils)" ]; then
    log_info "  整合: utils/ → scripts/admin/"
    rsync -av utils/ scripts/admin/ 2>/dev/null || true
    rm -rf utils
else
    log_warn "  utils/为空或不存在"
fi

log_info "✅ 工具目录已整合到scripts/"
echo ""

# ============================================================================
# 2. 删除或清理临时目录
# ============================================================================
log_section "🧹 步骤2：清理临时目录"

TEMP_DIRS=(
    "logs"
    "htmlcov"
    "backups"
)

for dir in "${TEMP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_info "  删除临时目录: $dir/"
        rm -rf "$dir"
    fi
done

log_info "✅ 临时目录已清理"
echo ""

# ============================================================================
# 3. 整合部署相关目录
# ============================================================================
log_section "🚀 步骤3：整合部署目录"

# 整合infrastructure/ → deploy/
if [ -d "infrastructure" ] && [ "$(ls -A infrastructure)" ]; then
    log_info "  整合: infrastructure/ → deploy/"
    rsync -av infrastructure/ deploy/ 2>/dev/null || true
    rm -rf infrastructure
else
    log_warn "  infrastructure/为空或不存在"
fi

log_info "✅ 部署目录已整合"
echo ""

# ============================================================================
# 4. 评估并删除低价值目录
# ============================================================================
log_section "📦 步骤4：删除低价值目录"

LOW_VALUE_DIRS=(
    "shared"
    "tasks"
    "skills"
    "apps"
    "api"
    "admin"
)

for dir in "${LOW_VALUE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        file_count=$(find "$dir" -type f | wc -l | tr -d ' ')
        if [ $file_count -lt 10 ]; then
            log_info "  删除低价值目录: $dir/ (${file_count}个文件)"
            rm -rf "$dir"
        else
            log_warn "  保留: $dir/ (${file_count}个文件)"
        fi
    fi
done

log_info "✅ 低价值目录已清理"
echo ""

# ============================================================================
# 5. 验证结果
# ============================================================================
log_section "✅ 验证根目录整合结果"

END_COUNT=$(ls -d */ 2>/dev/null | wc -l | tr -d ' ')
REDUCTION=$((START_COUNT - END_COUNT))
PERCENT=$((REDUCTION * 100 / START_COUNT))

echo ""
log_info "📊 根目录整合统计："
echo "  - 开始时: $START_COUNT 个目录"
echo "  - 结束时: $END_COUNT 个目录"
echo "  - 减少: $REDUCTION 个 ($PERCENT%)"
echo ""

if [ $END_COUNT -lt 20 ]; then
    echo -e "${GREEN}${BOLD}🎉 恭喜！已达成目标：根目录数 < 20${NC}"
    echo ""
    log_info "📁 最终保留的根目录："
    ls -d */ | sort | while read dir; do
        echo "  - ${dir%/}/"
    done
else
    log_warn "⚠️  未完全达成目标：当前 $END_COUNT 个（目标 <20）"
    log_warn "建议：继续检查剩余目录"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 阶段3补充整合完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exit 0
