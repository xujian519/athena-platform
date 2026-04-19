#!/bin/bash
################################################################################
# 专利检索工具清理脚本
#
# 删除所有不使用有效检索渠道的无效工具
#
# 有效渠道:
#   1. 本地PostgreSQL patent_db数据库
#   2. Google Patents在线检索
#   3. Google Patents PDF下载
#
# 创建日期: 2026-04-19
################################################################################

set -e  # 遇到错误立即退出

PROJECT_ROOT="/Users/xujian/Athena工作平台"
BACKUP_DIR="/backup/patent_tools_cleanup_$(date +%Y%m%d_%H%M%S)"
INVALID_TOOLS_LOG="/tmp/invalid_tools_cleanup.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

################################################################################
# 函数定义
################################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

create_backup() {
    log_info "📦 创建备份..."

    # 创建备份目录
    mkdir -p "$BACKUP_DIR"

    # 备份将要删除的文件
    for file in "${INVALID_RETRIEVAL_TOOLS[@]}" "${INVALID_DOWNLOAD_TOOLS[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            mkdir -p "$BACKUP_DIR/$(dirname $file)"
            cp "$PROJECT_ROOT/$file" "$BACKUP_DIR/$file"
            log_info "  备份: $file"
        fi
    done

    log_info "✅ 备份完成: $BACKUP_DIR"
}

delete_invalid_tools() {
    log_info "🗑️  删除无效工具..."

    cd "$PROJECT_ROOT"

    # 删除无效检索工具
    log_info "  删除无效检索工具（6个）..."
    for file in "${INVALID_RETRIEVAL_TOOLS[@]}"; do
        if [ -f "$file" ]; then
            rm -v "$file" | tee -a "$INVALID_TOOLS_LOG"
        else
            log_warn "  文件不存在: $file"
        fi
    done

    # 删除无效下载工具
    log_info "  删除无效下载工具（5个）..."
    for file in "${INVALID_DOWNLOAD_TOOLS[@]}"; do
        if [ -f "$file" ]; then
            rm -v "$file" | tee -a "$INVALID_TOOLS_LOG"
        else
            log_warn "  文件不存在: $file"
        fi
    done

    log_info "✅ 删除完成！"
}

verify_cleanup() {
    log_info "🔍 验证清理结果..."

    cd "$PROJECT_ROOT"

    # 检查是否还有无效工具
    remaining_count=0

    for file in "${INVALID_RETRIEVAL_TOOLS[@]}" "${INVALID_DOWNLOAD_TOOLS[@]}"; do
        if [ -f "$file" ]; then
            log_error "  文件仍然存在: $file"
            remaining_count=$((remaining_count + 1))
        fi
    done

    if [ $remaining_count -eq 0 ]; then
        log_info "✅ 所有无效工具已成功删除"
    else
        log_error "❌ 仍有 $remaining_count 个文件未删除"
        return 1
    fi

    # 检查有效工具是否保留
    log_info "  检查有效工具是否保留..."

    # 检查PostgreSQL检索工具
    if [ -f "patent_hybrid_retrieval/real_patent_hybrid_retrieval.py" ]; then
        log_info "  ✅ PostgreSQL检索工具保留"
    else
        log_error "  ❌ PostgreSQL检索工具缺失"
    fi

    # 检查Google Patents检索工具
    if [ -f "patent-platform/core/core_programs/google_patents_retriever.py" ]; then
        log_info "  ✅ Google Patents检索工具保留"
    else
        log_error "  ❌ Google Patents检索工具缺失"
    fi

    # 检查Google Patents下载工具
    if [ -f "tools/google_patents_downloader.py" ]; then
        log_info "  ✅ Google Patents下载工具保留"
    else
        log_error "  ❌ Google Patents下载工具缺失"
    fi
}

generate_report() {
    log_info "📊 生成清理报告..."

    REPORT_FILE="$BACKUP_DIR/cleanup_report.txt"

    cat > "$REPORT_FILE" <<EOF
专利检索工具清理报告
=====================

清理日期: $(date)
项目路径: $PROJECT_ROOT
备份目录: $BACKUP_DIR

删除的文件列表:
----------------

无效检索工具（6个）:
EOF

    for file in "${INVALID_RETRIEVAL_TOOLS[@]}"; do
        echo "  - $file" >> "$REPORT_FILE"
    done

    cat >> "$REPORT_FILE" <<EOF

无效下载工具（5个）:
EOF

    for file in "${INVALID_DOWNLOAD_TOOLS[@]}"; do
        echo "  - $file" >> "$REPORT_FILE"
    done

    cat >> "$REPORT_FILE" <<EOF

统计:
------
总删除文件数: $(( ${#INVALID_RETRIEVAL_TOOLS[@]} + ${#INVALID_DOWNLOAD_TOOLS[@]} ))

备份位置:
--------
$BACKUP_DIR

如需恢复，执行:
-----------
cd $PROJECT_ROOT
cp -r $BACKUP_DIR/* .

EOF

    log_info "✅ 报告已生成: $REPORT_FILE"
    cat "$REPORT_FILE"
}

################################################################################
# 主程序
################################################################################

main() {
    echo "╔════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                        ║"
    echo "║           专利检索工具清理脚本                                        ║"
    echo "║                                                                        ║"
    echo "║  删除所有不使用有效检索渠道的无效工具                                  ║"
    echo "║                                                                        ║"
    echo "╚════════════════════════════════════════════════════════════════════════╝"
    echo ""

    # 定义无效工具列表
    declare -a INVALID_RETRIEVAL_TOOLS=(
        "tools/search/athena_search_platform.py"
        "tools/search/external_search_platform.py"
        "tools/patent_search_schemes_flexible.py"
        "tools/patent_search_schemes_analyzer.py"
        "patent-platform/core/core_programs/deepseek_direct_patent_search.py"
        "patent_hybrid_retrieval/hybrid_retrieval_system.py"
    )

    declare -a INVALID_DOWNLOAD_TOOLS=(
        "tools/download/download_cn_patents.py"
        "tools/download/download_cn_patents_cnipa.py"
        "tools/download/download_cn_patents_final.py"
        "tools/download/download_daqi_patents.py"
        "tools/download/download_daqi_patents_pdf.py"
    )

    log_info "📋 清理计划:"
    log_info "  - 无效检索工具: ${#INVALID_RETRIEVAL_TOOLS[@]} 个"
    log_info "  - 无效下载工具: ${#INVALID_DOWNLOAD_TOOLS[@]} 个"
    log_info "  - 总计: $(( ${#INVALID_RETRIEVAL_TOOLS[@]} + ${#INVALID_DOWNLOAD_TOOLS[@]} )) 个文件"
    echo ""

    # 确认操作
    read -p "是否继续清理？(yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_warn "❌ 取消清理操作"
        exit 0
    fi

    echo ""
    log_info "🚀 开始清理..."
    echo ""

    # 执行清理
    create_backup
    echo ""
    delete_invalid_tools
    echo ""
    verify_cleanup
    echo ""
    generate_report
    echo ""

    log_info "✅ 清理完成！"
    echo ""
    log_info "📝 下一步:"
    log_info "  1. 检查清理报告: $REPORT_FILE"
    log_info "  2. 创建统一检索接口: core/tools/patent_retrieval.py"
    log_info "  3. 创建统一下载接口: core/tools/patent_download.py"
    log_info "  4. 注册到工具系统: core/tools/auto_register.py"
    echo ""
    log_warn "⚠️  如需恢复，执行: cp -r $BACKUP_DIR/* $PROJECT_ROOT/"
}

# 运行主程序
main "$@"
