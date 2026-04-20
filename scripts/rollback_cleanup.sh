#!/bin/bash

################################################################################
# Athena工作平台 - 清理回滚脚本
# 功能：从备份恢复清理脚本删除的文件
# 作者：Claude Code
# 日期：2026-04-20
# 版本：v1.0
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT" || exit 1

################################################################################
# 工具函数
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

confirm() {
    read -p "$(echo -e ${YELLOW}[确认]${NC} $1 (y/N): )" -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Yy]$ ]]
}

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

################################################################################
# 回滚函数
################################################################################

list_backups() {
    print_header "可用的备份列表"

    local backups=($(ls -dt .cleanup_backup_* 2>/dev/null || true))

    if [ ${#backups[@]} -eq 0 ]; then
        log_error "未找到任何备份"
        exit 1
    fi

    log_info "找到 ${#backups[@]} 个备份："
    echo ""

    for i in "${!backups[@]}"; do
        local backup="${backups[$i]}"

        # 检查是目录还是压缩包
        if [ -d "$backup" ]; then
            local size=$(du -sh "$backup" 2>/dev/null | cut -f1 || echo "未知")
            echo "  [$i] $backup (目录, 大小: $size)"
        elif [ -f "${backup}.tar.gz" ]; then
            local size=$(du -sh "${backup}.tar.gz" 2>/dev/null | cut -f1 || echo "未知")
            echo "  [$i] ${backup}.tar.gz (压缩包, 大小: $size)"
        fi
    done

    echo ""
}

select_backup() {
    list_backups

    local backups=($(ls -dt .cleanup_backup_* 2>/dev/null || true))

    while true; do
        read -p "请选择要恢复的备份编号 [0-$((${#backups[@]} - 1))]: " choice

        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 0 ] && [ "$choice" -lt "${#backups[@]}" ]; then
            SELECTED_BACKUP="${backups[$choice]}"

            # 如果选择的是压缩包，先解压
            if [ -f "${SELECTED_BACKUP}.tar.gz" ] && [ ! -d "$SELECTED_BACKUP" ]; then
                log_info "解压备份文件..."
                tar -xzf "${SELECTED_BACKUP}.tar.gz"
                log_success "解压完成"
            fi

            if [ -d "$SELECTED_BACKUP" ]; then
                log_success "已选择备份: $SELECTED_BACKUP"
                return
            else
                log_error "备份目录不存在: $SELECTED_BACKUP"
                exit 1
            fi
        else
            log_error "无效的选择，请输入 $0 到 $((${#backups[@]} - 1)) 之间的数字"
        fi
    done
}

restore_files() {
    print_header "恢复文件"

    local backup_root="$SELECTED_BACKUP"
    local restored_count=0
    local skipped_count=0

    log_info "开始从备份恢复文件..."
    echo ""

    # 遍历备份目录中的所有文件
    find "$backup_root" -type f | while read -r backup_file; do
        # 计算相对路径
        local relative_path="${backup_file#$backup_root/}"

        # 检查目标文件是否已存在
        if [ -f "$relative_path" ]; then
            log_warning "文件已存在，跳过: $relative_path"
            ((skipped_count++))
        else
            # 确保目标目录存在
            local target_dir=$(dirname "$relative_path")
            mkdir -p "$target_dir"

            # 恢复文件
            cp -p "$backup_file" "$relative_path"
            log_success "已恢复: $relative_path"
            ((restored_count++))
        fi
    done

    echo ""
    log_success "恢复完成！"
    log_info "恢复文件数: $restored_count"
    log_info "跳过文件数: $skipped_count"
}

confirm_restore() {
    print_header "回滚确认"

    log_warning "您即将从备份恢复文件，这可能覆盖当前文件。"
    log_warning "建议在执行回滚前先创建当前状态的备份。"

    if ! confirm "确定要执行回滚操作吗？"; then
        log_info "回滚操作已取消"
        exit 0
    fi
}

################################################################################
# 主函数
################################################################################

main() {
    clear
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║     Athena工作平台 - 清理回滚脚本                             ║
║     版本: v1.0                                               ║
║     日期: 2026-04-20                                         ║
╚══════════════════════════════════════════════════════════════╝
EOF

    # 选择备份
    select_backup

    # 确认回滚
    confirm_restore

    # 执行恢复
    restore_files

    # 询问是否删除备份
    echo ""
    if confirm "是否删除已恢复的备份（保留其他备份）？"; then
        rm -rf "$SELECTED_BACKUP"
        if [ -f "${SELECTED_BACKUP}.tar.gz" ]; then
            rm -f "${SELECTED_BACKUP}.tar.gz"
        fi
        log_success "备份已删除"
    fi

    echo ""
    log_success "回滚操作完成！"
}

# 执行主函数
main "$@"
