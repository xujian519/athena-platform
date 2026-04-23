#!/bin/bash

################################################################################
# Athena工作平台 - 项目清理脚本
# 功能：清理废弃、冗余、过期文件和文档
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

# 备份目录
BACKUP_DIR="$PROJECT_ROOT/.cleanup_backup_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$PROJECT_ROOT/cleanup_log_$(date +%Y%m%d_%H%M%S).log"

# 统计变量
TOTAL_FILES=0
TOTAL_SPACE=0

################################################################################
# 工具函数
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo ""
    echo "========================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
}

confirm() {
    read -p "$(echo -e ${YELLOW}[确认]${NC} $1 (y/N): )" -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Yy]$ ]]
}

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log_info "备份目录已创建: $BACKUP_DIR"
}

backup_file() {
    local file="$1"
    local backup_path="$BACKUP_DIR/$(dirname "$file")"

    if [ -e "$file" ]; then
        mkdir -p "$backup_path"
        cp -p "$file" "$backup_path/"
        log_info "已备份: $file"
    fi
}

get_file_size() {
    if [ -e "$1" ]; then
        du -h "$1" | cut -f1
    else
        echo "0"
    fi
}

################################################################################
# 清理函数
################################################################################

# 优先级1: 清理备份文件
cleanup_backup_files() {
    print_header "步骤 1/6: 清理备份文件"

    local backup_files=(
        "requirements_backup.txt"
        "core/llm/response_cache.py.backup"
        "core/patent/infringement/infringement_determiner.py.bak"
        "core/agents/xiaona_legal.py.bak"
        "core/search/enhanced_hybrid_search.py.backup"
    )

    for file in "${backup_files[@]}"; do
        if [ -f "$file" ]; then
            backup_file "$file"
            local size=$(get_file_size "$file")
            rm -f "$file"
            log_success "已删除: $file (大小: $size)"
            ((TOTAL_FILES++))
        else
            log_warning "文件不存在，跳过: $file"
        fi
    done
}

# 优先级1: 清理.backup目录
cleanup_backup_directory() {
    print_header "步骤 2/6: 清理.backup目录"

    if [ -d ".backup" ]; then
        backup_file ".backup"
        local size=$(du -sh .backup | cut -f1)
        rm -rf .backup
        log_success "已删除: .backup/ (大小: $size)"
        ((TOTAL_FILES++))
    else
        log_warning "目录不存在，跳过: .backup/"
    fi
}

# 优先级1: 清理PID文件
cleanup_pid_files() {
    print_header "步骤 3/6: 清理PID文件"

    log_warning "正在检查进程状态..."

    local pids_running=false
    local pid_files=(
        "pids/memory_system.pid"
        "pids/knowledge_graph.pid"
        "pids/xiaonuo.pid"
        "pids/xiaona.pid"
    )

    for pid_file in "${pid_files[@]}"; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file" 2>/dev/null || echo "")
            if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
                log_warning "进程仍在运行: $pid_file (PID: $pid)"
                pids_running=true
            fi
        fi
    done

    if $pids_running; then
        if ! confirm "检测到运行中的进程，仍要清理PID文件吗？"; then
            log_warning "跳过PID文件清理"
            return
        fi
    fi

    for pid_file in "${pid_files[@]}"; do
        if [ -f "$pid_file" ]; then
            backup_file "$pid_file"
            rm -f "$pid_file"
            log_success "已删除PID文件: $pid_file"
            ((TOTAL_FILES++))
        fi
    done

    # 清理tasks目录下的pid文件
    find tasks/ -name "*.pid" -type f 2>/dev/null | while read -r pid_file; do
        backup_file "$pid_file"
        rm -f "$pid_file"
        log_success "已删除PID文件: $pid_file"
        ((TOTAL_FILES++))
    done
}

# 优先级2: 清理临时数据文件
cleanup_temp_files() {
    print_header "步骤 4/6: 清理临时数据文件"

    local temp_dirs=(
        "data/trademark_rules/temp"
    )

    for temp_dir in "${temp_dirs[@]}"; do
        if [ -d "$temp_dir" ]; then
            backup_file "$temp_dir"
            local size=$(du -sh "$temp_dir" 2>/dev/null | cut -f1 || echo "未知")
            rm -rf "$temp_dir"
            log_success "已删除临时目录: $temp_dir/ (大小: $size)"
            ((TOTAL_FILES++))
        else
            log_warning "目录不存在，跳过: $temp_dir/"
        fi
    done
}

# 优先级2: 清理历史测试报告（保留最近3个月）
cleanup_old_test_reports() {
    print_header "步骤 5/6: 清理历史测试报告"

    if [ ! -d "tests/results" ]; then
        log_warning "测试报告目录不存在: tests/results/"
        return
    fi

    log_info "查找3个月前的测试报告..."

    # 查找并删除90天前的测试报告
    find tests/results/ -name "*.json" -type f -mtime +90 2>/dev/null | while read -r report; do
        backup_file "$report"
        local size=$(get_file_size "$report")
        rm -f "$report"
        log_success "已删除旧测试报告: $report (大小: $size)"
        ((TOTAL_FILES++))
    done

    # 显示保留的报告
    local remaining=$(find tests/results/ -name "*.json" -type f -mtime -90 2>/dev/null | wc -l)
    log_info "保留了 $remaining 个最近的测试报告"
}

# 优先级3: 清理Python缓存
cleanup_python_cache() {
    print_header "步骤 6/6: 清理Python缓存"

    log_info "查找__pycache__目录..."

    local cache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
    log_info "找到 $cache_count 个__pycache__目录"

    if confirm "是否清理所有Python缓存文件？"; then
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        find . -type f -name "*.pyo" -delete 2>/dev/null || true
        log_success "Python缓存已清理"
    else
        log_warning "跳过Python缓存清理"
    fi
}

# 修复Git状态
fix_git_status() {
    print_header "修复Git状态"

    log_info "检查Git状态..."

    # 显示已删除但未暂存的文件
    local deleted_files=$(git status | grep "deleted:" | awk '{print $2}' || echo "")

    if [ -z "$deleted_files" ]; then
        log_info "没有需要修复的Git文件"
        return
    fi

    log_warning "发现以下已删除但未暂存的文件："
    echo "$deleted_files"

    if confirm "是否将这些文件从Git中移除？"; then
        echo "$deleted_files" | while read -r file; do
            [ -n "$file" ] && git rm "$file"
        done
        log_success "Git状态已修复"
    else
        log_warning "跳过Git状态修复"
    fi
}

# 生成清理建议
generate_recommendations() {
    print_header "清理建议和后续操作"

    cat << 'EOF' | tee -a "$LOG_FILE"

📋 清理建议和后续操作
========================

1. Docker配置文件合并
   - 发现多个docker-compose.yml文件
   - 建议合并到主配置文件，使用profile区分环境
   - 位置: docker-compose.yml

2. .gitignore优化
   建议添加以下规则：
   - __pycache__/
   - *.py[cod]
   - *.bak
   - *.backup
   - .backup/
   - pids/*.pid
   - data/trademark_rules/temp/
   - tests/results/*.json
   - .cleanup_backup_*/

3. 定期清理任务
   - 建议每月执行一次此清理脚本
   - 可添加到crontab:
     0 0 1 * * /Users/xujian/Athena工作平台/scripts/cleanup_project.sh

4. 配置文件管理
   - 统一requirements.txt管理
   - 使用环境变量区分不同配置
   - 避免硬编码配置值

5. 文档更新
   - 检查docs/目录下的过期文档
   - 更新CLAUDE.md中的项目结构说明
   - 同步README.md中的启动命令

EOF
}

# 生成统计报告
generate_report() {
    print_header "清理统计报告"

    local backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "未知")

    cat << EOF | tee -a "$LOG_FILE"

📊 清理统计
============
- 清理文件总数: $TOTAL_FILES
- 备份位置: $BACKUP_DIR
- 备份大小: $backup_size
- 日志文件: $LOG_FILE

✅ 清理完成！
如需回滚，请运行:
  tar -xzf "$BACKUP_DIR".tar.gz -C /

EOF
}

# 压缩备份
compress_backup() {
    if [ -d "$BACKUP_DIR" ]; then
        log_info "正在压缩备份文件..."
        tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
        log_success "备份已压缩: ${BACKUP_DIR}.tar.gz"

        # 询问是否删除未压缩的备份
        if confirm "是否删除未压缩的备份目录（已保留压缩包）？"; then
            rm -rf "$BACKUP_DIR"
            log_success "已删除未压缩的备份目录"
        fi
    fi
}

################################################################################
# 主函数
################################################################################

main() {
    clear
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║     Athena工作平台 - 项目清理脚本                             ║
║     版本: v1.0                                               ║
║     日期: 2026-04-20                                         ║
╚══════════════════════════════════════════════════════════════╝
EOF

    log_info "脚本开始执行: $(date)"
    log_info "项目路径: $PROJECT_ROOT"

    # 创建备份目录
    create_backup_dir

    # 执行清理步骤
    cleanup_backup_files
    cleanup_backup_directory
    cleanup_pid_files
    cleanup_temp_files
    cleanup_old_test_reports
    cleanup_python_cache

    # 修复Git状态
    if confirm "是否修复Git状态（删除已移除的文件）？"; then
        fix_git_status
    fi

    # 压缩备份
    compress_backup

    # 生成报告和建议
    generate_report
    generate_recommendations

    log_success "脚本执行完成: $(date)"
}

# 执行主函数
main "$@"
