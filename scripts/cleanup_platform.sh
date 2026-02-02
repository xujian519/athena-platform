#!/bin/bash
# -*- coding: utf-8 -*-
# 平台文件清理脚本
# Platform File Cleanup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 统计信息
DELETED_COUNT=0
FREED_SPACE=0

# 显示帮助信息
show_help() {
    echo "平台文件清理脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --dry-run     预览模式，不实际删除文件"
    echo "  --all         执行所有清理操作"
    echo "  --empty-dirs  只清理空目录"
    echo "  --test-files  清理测试文件（需要确认）"
    echo "  --demo-files  清理demo文件（需要确认）"
    echo "  --backup-files 清理备份文件"
    echo "  --help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --dry-run              # 预览所有可删除的文件"
    echo "  $0 --backup-files         # 只删除备份文件"
    echo "  $0 --empty-dirs           # 只清理空目录"
    echo "  $0 --all                  # 执行所有清理"
}

# 删除文件或目录（支持dry-run）
delete_item() {
    local item="$1"
    local dry_run="$2"

    if [ "$dry_run" = "true" ]; then
        echo "  [预览] 将删除: $item"
    else
        if [ -d "$item" ]; then
            size=$(du -sk "$item" 2>/dev/null | cut -f1 || echo 0)
            rm -rf "$item" 2>/dev/null || log_warning "删除失败: $item"
        else
            size=$(du -sk "$item" 2>/dev/null | cut -f1 || echo 0)
            rm -f "$item" 2>/dev/null || log_warning "删除失败: $item"
        fi

        DELETED_COUNT=$((DELETED_COUNT + 1))
        FREED_SPACE=$((FREED_SPACE + size))
        log_success "已删除: $item"
    fi
}

# 清理备份文件
cleanup_backup_files() {
    local dry_run="$1"

    log_info "清理备份文件..."

    # 查找备份文件
    find . -type f \( \
        -name "*.bak" -o \
        -name "*.backup" -o \
        -name "*.old" -o \
        -name "*~" -o \
        -name "*.tmp" -o \
        -name "*.temp" -o \
        -name "*.orig" \
        \) -not \( \
        -path "./.git/*" -o \
        -path "./venv/*" -o \
        -path "./storage-system/venv/*" -o \
        -path "./backup/*" -o \
        -path "*/__pycache__/*" \
        \) | while read file; do
        delete_item "$file" "$dry_run"
    done
}

# 清理空目录
cleanup_empty_dirs() {
    local dry_run="$1"

    log_info "清理空目录..."

    # 查找空目录
    find . -type d -empty -not \( \
        -path "./.git/*" -o \
        -path "./venv/*" -o \
        -path "./storage-system/venv/*" -o \
        -path "./node_modules/*" \
        \) | while read dir; do
        delete_item "$dir" "$dry_run"
    done
}

# 清理测试文件
cleanup_test_files() {
    local dry_run="$1"
    local confirm="${2:-false}"

    if [ "$confirm" = "false" ] && [ "$dry_run" = "false" ]; then
        echo -n "⚠️  确定要删除测试文件吗？(y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "跳过测试文件清理"
            return
        fi
    fi

    log_info "清理测试文件..."

    # 查找测试文件
    find . -type f \( \
        -name "test_*.py" -o \
        -name "*_test.py" -o \
        -name "*_spec.py" -o \
        -name "conftest.py" \
        \) -not \( \
        -path "./.git/*" -o \
        -path "./venv/*" -o \
        -path "./storage-system/venv/*" -o \
        -path "./tests/*" -o \
        -path "*/__pycache__/*" \
        \) | while read file; do

        # 检查是否是真正的测试文件
        if grep -q "import unittest\|import pytest\|def test_\|class Test\|@pytest" "$file" 2>/dev/null; then
            delete_item "$file" "$dry_run"
        fi
    done
}

# 清理demo文件
cleanup_demo_files() {
    local dry_run="$1"
    local confirm="${2:-false}"

    if [ "$confirm" = "false" ] && [ "$dry_run" = "false" ]; then
        echo -n "⚠️  确定要删除demo文件吗？(y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "跳过demo文件清理"
            return
        fi
    fi

    log_info "清理demo文件..."

    # 查找demo文件
    find . -type f \( \
        -name "*demo*.py" -o \
        -name "*Demo*.py" -o \
        -name "*example*.py" -o \
        -name "*Example*.py" \
        \) -not \( \
        -path "./.git/*" -o \
        -path "./venv/*" -o \
        -path "./storage-system/venv/*" -o \
        -path "*/__pycache__/*" \
        \) | while read file; do

        # 检查是否是简单的demo
        if [ $(wc -l < "$file") -lt 100 ]; then
            delete_item "$file" "$dry_run"
        fi
    done
}

# 清理simple文件
cleanup_simple_files() {
    local dry_run="$1"

    log_info "清理simple文件..."

    # 查找simple文件
    find . -type f \( \
        -name "*simple*.py" -o \
        -name "*Simple*.py" -o \
        -name "*basic*.py" -o \
        -name "*Basic*.py" \
        \) -not \( \
        -path "./.git/*" -o \
        -path "./venv/*" -o \
        -path "./storage-system/venv/*" -o \
        -path "*/__pycache__/*" \
        \) | while read file; do

        # 检查文件内容
        if grep -q "教程\|Tutorial\|示例\|Example\|简单\|Simple\|快速开始\|Quick Start" "$file" 2>/dev/null; then
            if [ $(wc -l < "$file") -lt 50 ]; then
                delete_item "$file" "$dry_run"
            fi
        fi
    done
}

# 生成统计报告
generate_report() {
    log_info "生成清理报告..."

    REPORT_FILE="cleanup_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "平台文件清理报告"
        echo "================="
        echo "清理时间: $(date)"
        echo "删除文件数: $DELETED_COUNT"
        echo "释放空间: $((FREED_SPACE / 1024)) MB"
        echo ""
        echo "建议后续操作:"
        echo "1. 运行 git status 查看变更"
        echo "2. 检查是否有重要文件被误删"
        echo "3. 提交清理后的变更"
    } > "$REPORT_FILE"

    log_success "报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    local dry_run="false"
    local cleanup_backup="false"
    local cleanup_empty="false"
    local cleanup_test="false"
    local cleanup_demo="false"
    local cleanup_simple="false"
    local run_all="false"

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run="true"
                shift
                ;;
            --all)
                run_all="true"
                shift
                ;;
            --empty-dirs)
                cleanup_empty="true"
                shift
                ;;
            --test-files)
                cleanup_test="true"
                shift
                ;;
            --demo-files)
                cleanup_demo="true"
                shift
                ;;
            --backup-files)
                cleanup_backup="true"
                shift
                ;;
            --simple-files)
                cleanup_simple="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 显示警告
    if [ "$dry_run" = "false" ]; then
        echo ""
        log_warning "⚠️  警告: 这将永久删除文件！"
        echo ""
    fi

    # 执行清理
    echo "🔧 开始平台文件清理..."
    echo "======================"

    if [ "$run_all" = "true" ]; then
        cleanup_backup_files "$dry_run"
        cleanup_empty_dirs "$dry_run"
        cleanup_test_files "$dry_run"
        cleanup_demo_files "$dry_run"
        cleanup_simple_files "$dry_run"
    else
        [ "$cleanup_backup" = "true" ] && cleanup_backup_files "$dry_run"
        [ "$cleanup_empty" = "true" ] && cleanup_empty_dirs "$dry_run"
        [ "$cleanup_test" = "true" ] && cleanup_test_files "$dry_run" "true"
        [ "$cleanup_demo" = "true" ] && cleanup_demo_files "$dry_run" "true"
        [ "$cleanup_simple" = "true" ] && cleanup_simple_files "$dry_run"
    fi

    # 显示统计
    echo ""
    echo "📊 清理统计:"
    echo "==========="
    echo "删除文件/目录数: $DELETED_COUNT"
    echo "释放空间: $((FREED_SPACE / 1024)) MB"

    if [ "$dry_run" = "true" ]; then
        echo ""
        log_info "预览模式完成，没有实际删除文件"
        echo "要执行实际删除，请运行: $0 --all"
    else
        generate_report
        echo ""
        log_success "清理完成！"
    fi
}

# 运行主函数
main "$@"