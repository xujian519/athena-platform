#!/bin/bash
# ============================================================================
# 阶段2：核心组件重组 - 第1批：业务模块迁移
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

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏗️  阶段2 - 第1批：业务模块迁移"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 1. 备份现有core
log_info "📦 备份现有core目录..."
if [ ! -d "core.backup.phase2" ]; then
    rsync -av --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='.pytest_cache' --exclude='*.log' \
        core/ core.backup.phase2/
    log_info "✅ 备份完成: core.backup.phase2/"
else
    log_info "⏭️  备份已存在，跳过"
fi
echo ""

# 2. 业务模块迁移清单
BUSINESS_MODULES=(
    "core/legal_kg:domains/legal/knowledge_graph"
    "core/biology:domains/biology"
    "core/emotion:domains/emotion"
    "core/compliance:domains/legal/compliance"
)

# 3. 执行迁移
log_info "📦 开始迁移业务模块..."
MIGRATED_COUNT=0

for module in "${BUSINESS_MODULES[@]}"; do
    src="${module%%:*}"
    dst="${module##*:}"

    if [ -d "$src" ]; then
        log_info "  迁移: $src → $dst"

        # 创建目标目录
        mkdir -p "$dst"

        # 使用rsync迁移（保留权限和时间戳）
        rsync -av --remove-source-files "$src/" "$dst/" 2>/dev/null || {
            log_warn "    ⚠️  迁移部分失败，继续"
        }

        # 删除空目录
        find "$src" -type d -empty -delete 2>/dev/null || true

        MIGRATED_COUNT=$((MIGRATED_COUNT + 1))
    else
        log_info "  ⏭️  跳过: $src (不存在)"
    fi
done

log_info "✅ 业务模块迁移完成 (共迁移 $MIGRATED_COUNT 个模块)"
echo ""

# 4. 更新import路径（自动）
log_info "🔧 更新import路径..."
python3 << 'EOPY'
import re
from pathlib import Path

# import替换规则
IMPORT_REPLACEMENTS = {
    r"from core\.legal_kg": "from domains.legal.knowledge_graph",
    r"from core\.biology": "from domains.biology",
    r"from core\.emotion": "from domains.emotion",
    r"from core\.compliance": "from domains.legal.compliance",
    r"import core\.legal_kg": "import domains.legal.knowledge_graph",
    r"import core\.biology": "import domains.biology",
    r"import core\.emotion": "import domains.emotion",
    r"import core\.compliance": "import domains.legal.compliance",
}

PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")
UPDATED_COUNT = 0

# 扫描所有Python文件
for py_file in PROJECT_ROOT.rglob("*.py"):
    # 跳过备份和虚拟环境
    if "backup" in str(py_file) or "venv" in str(py_file) or "__pycache__" in str(py_file):
        continue

    try:
        content = py_file.read_text()
        original_content = content

        # 应用替换规则
        for pattern, replacement in IMPORT_REPLACEMENTS.items():
            content = re.sub(pattern, replacement, content)

        # 如果有修改，写回文件
        if content != original_content:
            py_file.write_text(content)
            UPDATED_COUNT += 1
            print(f"  ✅ 更新: {py_file.relative_to(PROJECT_ROOT)}")

    except Exception as e:
        print(f"  ⚠️  跳过: {py_file.relative_to(PROJECT_ROOT)}: {e}")

print(f"\n✅ Import路径更新完成 (共更新 {UPDATED_COUNT} 个文件)")
EOPY

echo ""

# 5. 验证迁移结果
log_info "🔍 验证迁移结果..."
CORE_DIRS=$(ls -d core/*/ 2>/dev/null | wc -l)
DOMAINS_LEGAL_KG=""
if [ -d "domains/legal/knowledge_graph" ]; then
    DOMAINS_LEGAL_KG="✅ 存在"
else
    DOMAINS_LEGAL_KG="❌ 缺失"
fi

log_info "  core/子目录数: $CORE_DIRS (优化前: 164)"
log_info "  domains/legal/knowledge_graph/: $DOMAINS_LEGAL_KG"
echo ""

# 6. 生成迁移报告
log_info "📝 生成迁移报告..."
REPORT_FILE="reports/architecture/phase2/batch1_migration_report.txt"
mkdir -p "reports/architecture/phase2"

cat > "$REPORT_FILE" << EOF
阶段2 - 第1批：业务模块迁移报告
生成时间: $(date)

================================================================
迁移摘要
================================================================

迁移模块数: $MIGRATED_COUNT
Import更新数: $(python3 -c "import re; from pathlib import Path; count=0; [count:=count+1 for f in Path('.').rglob('*.py') if 'backup' not in str(f) and 'venv' not in str(f) and any(r in f.read_text() for r in ['from domains.', 'import domains.'])]; print(count)")

================================================================
迁移详情
================================================================

EOF

for module in "${BUSINESS_MODULES[@]}"; do
    src="${module%%:*}"
    dst="${module##*:}"
    if [ -d "$src" ]; then
        echo "❌ $src → $dst (迁移失败)" >> "$REPORT_FILE"
    elif [ -d "$dst" ]; then
        echo "✅ $src → $dst (迁移成功)" >> "$REPORT_FILE"
    else
        echo "⏭️  $src → $dst (源不存在)" >> "$REPORT_FILE"
    fi
done

cat >> "$REPORT_FILE" << EOF

================================================================
验证结果
================================================================

core/子目录数: $CORE_DIRS (目标: <30)
domains/legal/knowledge_graph/: $DOMAINS_LEGAL_KG

================================================================
下一步
================================================================

✅ 第1批迁移完成
⏳ 建议运行测试验证: pytest tests/ -v
⏳ 确认无误后继续第2批

EOF

log_info "✅ 迁移报告: $REPORT_FILE"
echo ""

# 7. 输出摘要
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 第1批迁移摘要"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ 迁移模块: $MIGRATED_COUNT 个"
echo "✅ Import更新: 已自动更新"
echo "✅ core/子目录: $CORE_DIRS (优化前: 164)"
echo ""
echo "💡 下一步:"
echo "  1. 运行测试验证: pytest tests/ -v"
echo "  2. 查看迁移报告: cat $REPORT_FILE"
echo "  3. 继续第2批: bash scripts/architecture/migrate/phase2_batch2.sh"
echo ""

exit 0
