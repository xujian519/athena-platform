#!/bin/bash
################################################################################
# Athena平台 - Docs目录自动整理脚本
# Auto Cleanup Script for docs/ Directory
#
# 功能：
#   1. 自动分类根目录的204个MD文件
#   2. 归档临时报告到对应月份
#   3. 移动过时文档到archive
#   4. 统一文档结构
#
# 使用方法：
#   ./scripts/docs_cleanup.sh [--dry-run] [--force]
#
# 选项：
#   --dry-run   预览模式，不实际移动文件
#   --force     强制执行，不询问确认
#
# 作者: 徐健 (xujian519@gmail.com)
# 创建: 2026-04-22
################################################################################

# set -e  # 注释掉，遇到错误继续执行

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
DOCS_DIR="$PROJECT_ROOT/docs"

# 模式
DRY_RUN=false
FORCE=false

# 统计变量
MOVED_COUNT=0
SKIPPED_COUNT=0
ERROR_COUNT=0

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_action() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}[DRY-RUN]${NC} $1"
    else
        echo -e "${GREEN}[MOVE]${NC} $1"
    fi
}

# 创建目录
ensure_dir() {
    local dir=$1
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  mkdir -p $dir"
    else
        mkdir -p "$dir" 2>/dev/null || true
    fi
}

# 移动文件
move_file() {
    local src=$1
    local dst=$2

    if [[ ! -f "$src" ]]; then
        return
    fi

    local filename=$(basename "$src")
    local target_dir=$(dirname "$dst")

    # 检查目标文件是否已存在
    if [[ -f "$dst" ]]; then
        log_warning "目标已存在，跳过: $filename"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        return
    fi

    # 执行移动
    ensure_dir "$target_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_action "$src → $dst"
    else
        mv "$src" "$dst" 2>/dev/null && {
            log_action "$filename → $dst"
            MOVED_COUNT=$((MOVED_COUNT + 1))
        } || {
            log_error "移动失败: $filename"
            ERROR_COUNT=$((ERROR_COUNT + 1))
        }
    fi
}

# 归档临时报告
archive_temp_reports() {
    log_info "📦 归档临时报告..."

    # 2026年1月的报告
    for file in "$DOCS_DIR"/*_report_202601*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/2026-01/$(basename "$file")"
    done

    # 2026年2月的报告
    for file in "$DOCS_DIR"/*_report_202602*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/2026-02/$(basename "$file")"
    done

    # 2026年3月的报告
    for file in "$DOCS_DIR"/*_report_202603*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/2026-03/$(basename "$file")"
    done

    # 2026年4月的报告
    for file in "$DOCS_DIR"/*_report_202604*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/2026-04/$(basename "$file")"
    done

    # 其他报告（按前缀分类）
    for file in "$DOCS_DIR"/*_REPORT.md "$DOCS_DIR"/*_Report.md "$DOCS_DIR"/*report*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/temp-reports/$(basename "$file")"
    done
}

# 归档过时文档
archive_legacy_docs() {
    log_info "🗄️ 归档过时文档..."

    # 2025年优化相关文档
    for file in "$DOCS_DIR"/xiaona_optimization*.md \
                "$DOCS_DIR"/xiaonuo_optimization*.md \
                "$DOCS_DIR"/*三阶段优化*.md \
                "$DOCS_DIR"/Xiaona增强系统使用指南.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/legacy-2025/$(basename "$file")"
    done

    # Istio相关（已废弃）
    for file in "$DOCS_DIR"/Istio*.md \
                "$DOCS_DIR"/*Istio*.md \
                "$DOCS_DIR"/*vs_Istio*.md \
                "$DOCS_DIR"/*vs_Linkerd*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/archive/legacy-istio/$(basename "$file")"
    done

    # 技术栈选择文档
    for file in "$DOCS_DIR"/*_TECH_STACK_SELECTION.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/reference/technical-stack/$(basename "$file")"
    done
}

# 整理API文档
organize_api_docs() {
    log_info "📚 整理API文档..."

    for file in "$DOCS_DIR"/API*.md \
                "$DOCS_DIR"/api_*.md \
                "$DOCS_DIR"/*_api_*.md \
                "$DOCS_DIR"/*API*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/api/$(basename "$file")"
    done
}

# 整理架构文档
organize_architecture_docs() {
    log_info "🏗️ 整理架构文档..."

    # 系统架构
    for file in "$DOCS_DIR"/*_architecture*.md \
                "$DOCS_DIR"/*_ARCHITECTURE*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/$(basename "$file")"
    done

    # 企业级架构
    for file in "$DOCS_DIR"/enterprise-multi-agent-*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/enterprise/$(basename "$file")"
    done

    # 网关相关
    for file in "$DOCS_DIR"/gateway_*.md \
                "$DOCS_DIR"/athena-api-gateway-*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/gateway/$(basename "$file")"
    done

    # 数据库架构
    for file in "$DOCS_DIR"/database-*.md \
                "$DOCS_DIR"/DATABASE_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/database/$(basename "$file")"
    done
}

# 整理智能体文档
organize_agent_docs() {
    log_info "🤖 整理智能体文档..."

    # 小娜相关
    for file in "$DOCS_DIR"/xiaona*.md \
                "$DOCS_DIR"/Xiaona*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/agents/xiaona/$(basename "$file")"
    done

    # 小诺相关
    for file in "$DOCS_DIR"/xiaonuo*.md \
                "$DOCS_DIR"/Xiaonuo*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/agents/xiaonuo/$(basename "$file")"
    done

    # 智能体架构
    for file in "$DOCS_DIR"/*multi-agent*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/architecture/agents/$(basename "$file")"
    done
}

# 整理专利文档
organize_patent_docs() {
    log_info "📋 整理专利文档..."

    # 中文专利文档
    for file in "$DOCS_DIR"/专利*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/projects/patents/$(basename "$file")"
    done

    # 专利检索报告
    for file in "$DOCS_DIR"/patent*.md \
                "$DOCS_DIR"/PATENT*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/projects/patents/$(basename "$file")"
    done

    # 专利分析报告
    for file in "$DOCS_DIR"/*个*专利*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/projects/patents/reports/$(basename "$file")"
    done
}

# 整理指南文档
organize_guides() {
    log_info "📖 整理指南文档..."

    # 快速开始
    for file in "$DOCS_DIR"/QUICK_*.md \
                "$DOCS_DIR"/Quick_*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/guides/quick-start/$(basename "$file")"
    done

    # 用户指南
    for file in "$DOCS_DIR"/*_guide*.md \
                "$DOCS_DIR"/*_GUIDE*.md \
                "$DOCS_DIR"/user_guide*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/guides/$(basename "$file")"
    done

    # 操作手册
    for file in "$DOCS_DIR"/*_MANUAL.md \
                "$DOCS_DIR"/*_OPS_MANUAL.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/guides/manuals/$(basename "$file")"
    done
}

# 整理部署文档
organize_deployment() {
    log_info "🚀 整理部署文档..."

    # 部署相关
    for file in "$DOCS_DIR"/deployment*.md \
                "$DOCS_DIR"/*_deployment*.md \
                "$DOCS_DIR"/DEPLOYMENT*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/deployment/$(basename "$file")"
    done

    # 迁移相关
    for file in "$DOCS_DIR"/*_migration*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/deployment/migration/$(basename "$file")"
    done

    # Docker相关
    for file in "$DOCS_DIR"/*docker*.md \
                "$DOCS_DIR"/*DOCKER*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/deployment/docker/$(basename "$file")"
    done
}

# 整理配置文档
organize_config() {
    log_info "⚙️ 整理配置文档..."

    for file in "$DOCS_DIR"/*_CONFIG*.md \
                "$DOCS_DIR"/config*.md \
                "$DOCS_DIR"/*ENV*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/reference/configuration/$(basename "$file")"
    done
}

# 整理安全文档
organize_security() {
    log_info "🔒 整理安全文档..."

    for file in "$DOCS_DIR"/security*.md \
                "$DOCS_DIR"/SECURITY*.md \
                "$DOCS_DIR"/*_security*.md \
                "$DOCS_DIR"/*_SECURITY*.md; do
        [[ -f "$file" ]] && move_file "$file" "$DOCS_DIR/security/$(basename "$file")"
    done
}

# 生成整理报告
generate_report() {
    local report_file="$DOCS_DIR/DOCS_CLEANUP_REPORT_$(date +%Y%m%d_%H%M%S).md"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "📋 预览模式 - 不会生成报告文件"
        echo ""
        echo "=========================================="
        echo "整理预览完成"
        echo "=========================================="
        echo "预计移动: $MOVED_COUNT 个文件"
        echo "预计跳过: $SKIPPED_COUNT 个文件"
        echo "预计错误: $ERROR_COUNT 个文件"
        echo ""
        echo "执行实际整理，运行："
        echo "  bash scripts/docs_cleanup.sh"
        return
    fi

    cat > "$report_file" << EOF
# Docs目录整理报告

> **生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
> **执行脚本**: scripts/docs_cleanup.sh

---

## 📊 整理统计

| 项目 | 数量 |
|-----|------|
| 已移动文件 | $MOVED_COUNT |
| 跳过文件 | $SKIPPED_COUNT |
| 错误文件 | $ERROR_COUNT |
| 总计处理 | $((MOVED_COUNT + SKIPPED_COUNT + ERROR_COUNT)) |

---

## 🗂️ 整理详情

### 1. 临时报告归档
- \`*_report_202601*.md\` → \`archive/temp-reports/2026-01/\`
- \`*_report_202602*.md\` → \`archive/temp-reports/2026-02/\`
- \`*_report_202603*.md\` → \`archive/temp-reports/2026-03/\`
- \`*_report_202604*.md\` → \`archive/temp-reports/2026-04/\`

### 2. 过时文档归档
- 2025年优化文档 → \`archive/legacy-2025/\`
- Istio相关文档 → \`archive/legacy-istio/\`

### 3. API文档
- API相关文档 → \`api/\`

### 4. 架构文档
- 系统架构 → \`architecture/\`
- 企业级架构 → \`architecture/enterprise/\`
- 网关架构 → \`architecture/gateway/\`
- 数据库架构 → \`architecture/database/\`

### 5. 智能体文档
- 小娜相关 → \`agents/xiaona/\`
- 小诺相关 → \`agents/xiaonuo/\`
- 多智能体架构 → \`architecture/agents/\`

### 6. 专利文档
- 中文专利文档 → \`projects/patents/\`
- 专利检索报告 → \`projects/patents/\`

### 7. 指南文档
- 快速开始 → \`guides/quick-start/\`
- 用户指南 → \`guides/\`
- 操作手册 → \`guides/manuals/\`

### 8. 部署文档
- 部署相关 → \`deployment/\`
- 迁移相关 → \`deployment/migration/\`
- Docker相关 → \`deployment/docker/\`

### 9. 配置文档
- 配置相关 → \`reference/configuration/\`

### 10. 安全文档
- 安全相关 → \`security/\`

---

## ✅ 下一步

1. **检查整理结果**
   \`\`\`bash
   ls -lh docs/
   ls -lh docs/archive/
   \`\`\`

2. **更新文档索引**
   - 更新 \`docs/README.md\`
   - 更新 \`docs/INDEX.md\`

3. **建立维护规范**
   - 新文档按分类存放
   - 定期归档临时报告
   - 保持根目录整洁

---

**脚本版本**: 1.0.0
**执行者**: $(whoami)
**主机**: $(hostname)
EOF

    log_success "📋 整理报告已生成: $report_file"
}

# 显示帮助
show_help() {
    cat << EOF
Athena平台 - Docs目录自动整理脚本

用法:
    $0 [选项]

选项:
    --dry-run   预览模式，不实际移动文件
    --force     强制执行，不询问确认
    --help      显示帮助信息

功能:
    1. 归档临时报告（按月份）
    2. 归档过时文档（2025年、Istio等）
    3. 整理API文档
    4. 整理架构文档
    5. 整理智能体文档
    6. 整理专利文档
    7. 整理指南文档
    8. 整理部署文档
    9. 整理配置文档
    10. 整理安全文档

示例:
    $0 --dry-run          # 预览整理计划
    $0                    # 执行整理
    $0 --force            # 强制执行

EOF
}

# 主函数
main() {
    echo "=========================================="
    echo "  Athena平台 - Docs目录自动整理"
    echo "=========================================="
    echo ""

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                log_info "🔍 预览模式已启用"
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 确认执行
    if [[ "$FORCE" != "true" && "$DRY_RUN" != "true" ]]; then
        echo "即将整理 docs/ 目录，移动约 $(ls "$DOCS_DIR"/*.md 2>/dev/null | wc -l) 个文件"
        echo ""
        read -p "确认继续? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "已取消"
            exit 0
        fi
    fi

    # 执行整理
    echo ""
    log_info "🚀 开始整理..."
    echo ""

    archive_temp_reports
    archive_legacy_docs
    organize_api_docs
    organize_architecture_docs
    organize_agent_docs
    organize_patent_docs
    organize_guides
    organize_deployment
    organize_config
    organize_security

    echo ""
    log_success "✅ 整理完成！"
    echo ""

    # 生成报告
    generate_report

    # 显示最终状态
    echo ""
    echo "=========================================="
    echo "  整理后状态"
    echo "=========================================="
    echo ""
    echo "根目录剩余文件数: $(ls "$DOCS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')"
    echo ""
    echo "查看详细报告: $DOCS_DIR/DOCS_CLEANUP_REPORT_*.md"
}

# 执行主函数
main "$@"
