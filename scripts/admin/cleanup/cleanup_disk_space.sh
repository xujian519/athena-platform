#!/bin/bash
# Athena 工作平台磁盘清理脚本
# 生成时间: 2026-02-07
# 预期节省空间: ~3.7GB

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

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

# 获取目录大小函数
get_size() {
    du -sh "$1" 2>/dev/null | awk '{print $1}'
}

# 显示当前项目大小
show_current_size() {
    log_info "当前项目大小: $(get_size "$PROJECT_ROOT")"
}

# 创建备份
create_backup() {
    local backup_name=$1
    local source_dir=$2

    log_info "创建备份: $backup_name"
    tar -czf "$backup_name" -C "$source_dir" . 2>/dev/null || true
    log_success "备份完成: $backup_name ($(get_size "$backup_name"))"
}

# ==================== 主要清理函数 ====================

# 1. 清理虚拟环境
cleanup_venv() {
    log_info "=== 清理虚拟环境 ==="

    # 计算清理前大小
    local before_size=$(du -sk . | awk '{sum+=$1} END {print sum}')

    # 移动主虚拟环境到项目外
    if [ -d "athena_env" ] && [ ! -L "athena_env" ]; then
        log_info "移动主虚拟环境到用户主目录..."
        if [ ! -d "$HOME/athena_venv" ]; then
            mv athena_env "$HOME/athena_venv"
            ln -s "$HOME/athena_venv" athena_env
            log_success "主虚拟环境已移动并创建符号链接"
        else
            log_warning "目标目录已存在，跳过移动"
        fi
    fi

    # 删除不需要的虚拟环境
    log_info "删除重复/不必要的虚拟环境..."

    local venvs_to_delete=(
        "modules/storage/storage-system/venv"
        "modules/storage/storage-system/athena_env"
        "services/yunpat_agent/venv"
        "services/multimodal/venv"
        "services/knowledge-graph-service/venv"
        "dev/scripts/venv"
        "apps/xiaonuo/venv"
        "infrastructure/deploy/venv"
    )

    for venv in "${venvs_to_delete[@]}"; do
        if [ -d "$venv" ]; then
            log_info "删除: $venv ($(get_size "$venv"))"
            rm -rf "$venv"
        fi
    done

    # 更新 .gitignore
    if ! grep -q "^athena_env/$" .gitignore 2>/dev/null; then
        log_info "更新 .gitignore..."
        {
            echo ""
            echo "# 虚拟环境"
            echo "athena_env/"
            echo "athena_env_py311/"
            echo "**/venv/"
            echo "**/.venv/"
        } >> .gitignore
        log_success ".gitignore 已更新"
    fi

    local after_size=$(du -sk . | awk '{sum+=$1} END {print sum}')
    local saved=$((before_size - after_size))
    log_success "虚拟环境清理完成，节省: $((saved / 1024)) MB"
}

# 2. 归档日志文件
archive_logs() {
    log_info "=== 归档日志文件 ==="

    local archive_date=$(date +%Y%m)
    local archive_dir="logs/archive/$archive_date"
    local prod_archive_dir="production/logs/archive/$archive_date"

    # 创建归档目录
    mkdir -p "$archive_dir" "$prod_archive_dir"

    # 归档大型日志文件
    local large_logs=(
        "logs/xiaonuo_gateway.log"
        "logs/prompt-system-api.stderr.log"
        "production/logs/unified_memory.stderr.log"
        "production/logs/unified_memory_service.log"
        "production/logs/unified_memory_api.log"
        "production/logs/collaboration-hub.log"
        "production/logs/unified-identity.log"
    )

    for log_file in "${large_logs[@]}"; do
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            local filename=$(basename "$log_file")
            local dest_dir="production/logs"[[ "$log_file" == production/* ]] && echo "$prod_archive_dir" || echo "$archive_dir"

            log_info "归档: $log_file ($(get_size "$log_file"))"
            mv "$log_file" "$dest_dir/"
        fi
    done

    # 压缩归档
    log_info "压缩日志归档..."
    find logs/archive -type f -name "*.log" -exec gzip {} \; 2>/dev/null || true
    find production/logs/archive -type f -name "*.log" -exec gzip {} \; 2>/dev/null || true

    log_success "日志归档完成"
}

# 3. 清理旧模型版本
cleanup_old_models() {
    log_info "=== 清理旧模型版本 ==="

    # 删除带时间戳的旧意图分类器模型，保留最新版本
    log_info "清理旧意图分类器模型..."

    find core -name "*enhanced_intent_classifier*.pkl" ! -name "latest_*.pkl" -type f -print -delete 2>/dev/null || true
    find core -name "*tool_selector*.pkl" ! -name "latest_*.pkl" -type f -print -delete 2>/dev/null || true
    find production -name "*enhanced_intent_classifier*.pkl" ! -name "latest_*.pkl" -type f -print -delete 2>/dev/null || true
    find production -name "*tool_selector*.pkl" ! -name "latest_*.pkl" -type f -print -delete 2>/dev/null || true

    # 删除临时转换文件
    log_info "删除临时模型转换文件..."
    rm -rf models/converted/DeepSeek-R1/._____temp 2>/dev/null || true

    log_success "旧模型版本清理完成"
}

# 4. 清理 Python 缓存
cleanup_pycache() {
    log_info "=== 清理 Python 缓存 ==="

    local pycache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
    log_info "找到 $pycache_count 个 __pycache__ 目录"

    # 只清理生产环境的缓存
    find production -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # 删除 .pyc 文件
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true

    log_success "Python 缓存清理完成"
}

# 5. 清理重复数据库文件
cleanup_duplicate_db() {
    log_info "=== 清理重复数据库文件 ==="

    # 删除重复的 yunpat.db
    if [ -f "services/yunpat_agent/data/yunpat.db" ]; then
        log_info "删除重复的 yunpat.db"
        rm -f services/yunpat_agent/data/yunpat.db
    fi

    # 删除备份目录中的 grafana.db
    if [ -d "backups/deployments" ]; then
        log_info "删除备份目录中的 grafana.db 副本"
        find backups/deployments -path "*/config/docker/data/grafana/grafana.db" -delete 2>/dev/null || true
    fi

    log_success "重复数据库清理完成"
}

# 6. 清理临时文件
cleanup_temp_files() {
    log_info "=== 清理临时文件 ==="

    # 删除临时文件
    find . -name "*.tmp" -type f -delete 2>/dev/null || true
    find . -name ".DS_Store" -type f -delete 2>/dev/null || true

    # 删除空的 ._* 文件（macOS 资源分支）
    find . -name "._*" -type f -size 0 -delete 2>/dev/null || true

    log_success "临时文件清理完成"
}

# 7. 压缩备份目录
compress_backups() {
    log_info "=== 压缩备份目录 ==="

    if [ -d "backups" ] && [ "$(ls -A backups 2>/dev/null)" ]; then
        local backup_file="backups_archived_$(date +%Y%m%d).tar.gz"
        log_info "压缩 backups/ 目录..."
        tar -czf "$backup_file" backups/ 2>/dev/null || true
        log_success "备份已压缩: $backup_file ($(get_size "$backup_file"))"

        # 询问是否删除原始目录
        read -p "是否删除原始 backups/ 目录? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf backups/
            log_success "原始备份目录已删除"
        fi
    fi

    if [ -d "backup" ] && [ "$(ls -A backup 2>/dev/null)" ]; then
        local backup_file2="backup_archived_$(date +%Y%m%d).tar.gz"
        log_info "压缩 backup/ 目录..."
        tar -czf "$backup_file2" backup/ 2>/dev/null || true
        log_success "备份已压缩: $backup_file2 ($(get_size "$backup_file2"))"

        read -p "是否删除原始 backup/ 目录? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf backup/
            log_success "原始备份目录已删除"
        fi
    fi
}

# 8. Git 仓库优化
optimize_git() {
    log_info "=== 优化 Git 仓库 ==="

    # 检查是否在 Git 仓库中
    if [ -d ".git" ]; then
        log_info "运行 git gc --aggressive..."
        git gc --aggressive --prune=now 2>/dev/null || true
        log_success "Git 仓库优化完成"
    else
        log_warning "不是 Git 仓库，跳过"
    fi
}

# ==================== 主函数 ====================

main() {
    echo ""
    echo "=========================================="
    echo "  Athena 工作平台磁盘清理工具"
    echo "=========================================="
    echo ""

    # 显示当前状态
    show_current_size
    echo ""

    # 询问是否创建备份
    read -p "是否在清理前创建数据库备份? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        mkdir -p .cleanup_backup
        create_backup ".cleanup_backup/db_backup_$(date +%Y%m%d_%H%M%S).tar.gz" "data"
    fi

    echo ""
    read -p "开始执行清理? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        log_info "清理已取消"
        exit 0
    fi

    echo ""
    log_info "开始清理..."
    echo ""

    # 执行清理
    cleanup_venv
    echo ""
    archive_logs
    echo ""
    cleanup_old_models
    echo ""
    cleanup_pycache
    echo ""
    cleanup_duplicate_db
    echo ""
    cleanup_temp_files
    echo ""

    # 询问是否压缩备份目录
    read -p "是否压缩备份目录? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        compress_backups
        echo ""
    fi

    # 询问是否优化 Git 仓库
    read -p "是否优化 Git 仓库 (可能需要几分钟)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        optimize_git
        echo ""
    fi

    # 显示结果
    echo ""
    echo "=========================================="
    log_success "清理完成!"
    echo "=========================================="
    echo ""
    show_current_size
    echo ""

    log_info "详细报告: docs/reports/ATHENA_DISK_CLEANUP_REPORT.md"
    echo ""

    # 建议后续操作
    log_info "建议后续操作:"
    echo "  1. 运行测试验证功能正常: pytest tests/ -v"
    echo "  2. 配置日志轮转防止日志文件无限增长"
    echo "  3. 定期执行此脚本 (建议每月一次)"
    echo ""
}

# 执行主函数
main "$@"
