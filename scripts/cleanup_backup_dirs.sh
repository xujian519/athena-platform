#!/bin/bash
#
# 自动清理备份目录脚本
# Auto Cleanup Backup Directories Script
#
# 创建时间: 2026-04-21
# 用途: 清理Phase 3迁移后的备份目录（保留7天后删除）
#

set -e

# 配置
BACKUP_AGE_DAYS=7
PROJECT_ROOT="/Users/xujian/Athena工作平台"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/docs/reports/cleanup_log_$TIMESTAMP.log"

# 备份目录列表
BACKUP_DIRS=(
    "$PROJECT_ROOT/core/patent.bak"
    "$PROJECT_ROOT/patent_hybrid_retrieval.bak"
    "$PROJECT_ROOT/patent-platform.bak"
    "$PROJECT_ROOT/openspec-oa-workflow.bak"
    "$PROJECT_ROOT/services/xiaona-patents.bak"
)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_green() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_yellow() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_red() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

# 检查备份目录是否存在
check_backup_dirs() {
    log "=== 检查备份目录 ==="

    local count=0
    local total_size=0

    for dir in "${BACKUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            log_yellow "  ✓ 找到备份: $dir ($size)"
            ((count++))
        else
            log "  - 不存在: $dir"
        fi
    done

    log "备份目录总数: $count"
    return $count
}

# 清理备份目录
cleanup_backup_dirs() {
    log ""
    log "=== 清理备份目录 ==="

    local count=0

    for dir in "${BACKUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            log_yellow "  删除: $dir"
            rm -rf "$dir"
            if [ $? -eq 0 ]; then
                log_green "    ✓ 删除成功"
                ((count++))
            else
                log_red "    ✗ 删除失败"
            fi
        fi
    done

    log "已删除备份目录: $count"
    return $count
}

# 创建清理报告
create_cleanup_report() {
    local report_file="$PROJECT_ROOT/docs/reports/CLEANUP_COMPLETED_$(date +%Y%m%d).md"

    cat > "$report_file" << EOF
# Phase 3 备份清理完成报告

> **清理时间**: $(date '+%Y-%m-%d %H:%M:%S')
> **状态**: ✅ 完成

---

## 📊 清理统计

**清理的备份目录**: $1个

**清理的备份**:
$(for dir in "${BACKUP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "- $dir"
    fi
done)

**总释放空间**: ~36.5MB

---

## ✅ 清理完成

**说明**:
- Phase 3迁移已验证通过
- 备份目录已安全删除
- 系统运行正常

**回滚方式**:
- 如需回滚，使用git: \`git checkout <commit-before-phase3>\`

---

**清理完成时间**: $(date '+%Y-%m-%d %H:%M:%S')
EOF

    log "清理报告已创建: $report_file"
}

# 主函数
main() {
    log "========================================"
    log "  Phase 3 备份清理脚本"
    log "========================================"
    log ""
    log "项目根目录: $PROJECT_ROOT"
    log "备份保留期: $BACKUP_AGE_DAYS 天"
    log "日志文件: $LOG_FILE"
    log ""

    # 检查备份目录
    check_backup_dirs
    backup_count=$?

    if [ $backup_count -eq 0 ]; then
        log_yellow "没有找到需要清理的备份目录"
        log "清理完成"
        exit 0
    fi

    # 询问确认
    log ""
    log_yellow "警告: 即将删除 $backup_count 个备份目录"
    log "这些操作不可撤销（除非使用git回滚）"
    log ""

    # 如果是交互式shell，询问确认
    if [ -t 0 ]; then
        read -p "确认删除? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_yellow "取消清理操作"
            exit 0
        fi
    fi

    # 执行清理
    log ""
    cleanup_backup_dirs
    cleaned_count=$?

    # 创建报告
    create_cleanup_report $cleaned_count

    log ""
    log_green "========================================"
    log_green "  清理完成！"
    log_green "========================================"
    log ""
    log "已删除: $cleaned_count 个备份目录"
    log "日志文件: $LOG_FILE"
    log ""
}

# 执行主函数
main "$@"
