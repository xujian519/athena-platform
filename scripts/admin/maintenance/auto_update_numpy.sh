#!/bin/bash
# -*- coding: utf-8 -*-
# Numpy自动更新和维护脚本
# Auto-update script for Numpy management

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

# 检查Python和Numpy版本
check_versions() {
    log_info "检查当前环境版本..."

    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "未安装")

    echo "Python版本: $PYTHON_VERSION"
    echo "Numpy版本: $NUMPY_VERSION"

    # 检查兼容性
    python3 tools/manage_numpy_versions.py --check
}

# 运行兼容性测试
run_compatibility_tests() {
    log_info "运行兼容性测试..."

    # 基础兼容性测试
    if python3 test_numpy_compatibility.py; then
        log_success "基础兼容性测试通过"
    else
        log_error "基础兼容性测试失败"
        return 1
    fi

    # 创建并运行版本特定测试
    python3 tools/manage_numpy_versions.py --create-test
    if [ -f "test_numpy_version_compatibility.py" ]; then
        log_info "运行版本兼容性测试..."
        if python3 test_numpy_version_compatibility.py; then
            log_success "版本兼容性测试通过"
        else
            log_warning "版本兼容性测试有警告，但可以继续"
        fi
    fi
}

# 更新numpy（如果需要）
update_numpy() {
    log_info "检查numpy更新..."

    # 获取升级建议
    RECOMMEND_OUTPUT=$(python3 tools/manage_numpy_versions.py --recommend 2>&1)

    if echo "$RECOMMEND_OUTPUT" | grep -q "需要升级: 是"; then
        log_warning "检测到需要升级numpy"

        # 提取升级命令
        UPGRADE_CMD=$(echo "$RECOMMEND_OUTPUT" | grep "升级命令:" | cut -d' ' -f4-)

        if [ -n "$UPGRADE_CMD" ]; then
            log_info "执行升级命令: $UPGRADE_CMD"
            eval "$UPGRADE_CMD"

            # 验证升级
            NEW_VERSION=$(python3 -c "import numpy; print(numpy.__version__)")
            log_success "numpy已升级到: $NEW_VERSION"
        else
            log_error "无法获取升级命令"
            return 1
        fi
    else
        log_success "numpy版本已是最新或无需升级"
    fi
}

# 更新requirements文件
update_requirements() {
    log_info "更新requirements文件..."

    # 预览更新
    python3 tools/manage_numpy_versions.py --update-requirements --dry-run

    # 询问是否应用更新
    echo -n "\n是否应用这些更新？(y/N): "
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        python3 tools/manage_numpy_versions.py --update-requirements
        log_success "requirements文件已更新"
    else
        log_info "跳过requirements更新"
    fi
}

# 检查项目兼容性
check_project_compatibility() {
    log_info "检查项目兼容性..."

    # 分析项目
    python3 tools/unify_numpy_stack.py --output project_analysis.json

    # 显示简要统计
    if [ -f "project_analysis.json" ]; then
        NUMPY_FILES=$(python3 -c "
import json
with open('project_analysis.json') as f:
    data = json.load(f)
print(data['summary']['numpy_files_count'])
")
        echo "发现 $NUMPY_FILES 个文件使用numpy"

        # 检查是否需要修复
        ISSUES=$(python3 tools/fix_numpy_compatibility.py --directory . --dry-run 2>&1 | grep "修复文件数:" | awk '{print $3}')
        if [ "$ISSUES" -gt 0 ]; then
            log_warning "发现 $ISSUES 个文件需要修复"
        else
            log_success "所有文件兼容性良好"
        fi
    fi
}

# 生成报告
generate_report() {
    log_info "生成兼容性报告..."

    REPORT_DIR="reports/numpy_compatibility"
    mkdir -p "$REPORT_DIR"

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    REPORT_FILE="$REPORT_DIR/compatibility_report_$TIMESTAMP.md"

    cat > "$REPORT_FILE" << EOF
# Numpy兼容性报告

**生成时间**: $(date)
**Python版本**: $(python3 --version)
**Numpy版本**: $(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "未安装")

## 兼容性检查

\`\`\`
$(python3 tools/manage_numpy_versions.py --check)
\`\`\`

## 项目统计

- 使用numpy的文件数: $(python3 -c "
import json
with open('project_analysis.json', 'r') as f:
    data = json.load(f)
    print(data['summary']['numpy_files_count'])
" 2>/dev/null || echo "未知")

## 测试结果

### 基础兼容性测试
\`\`\`
$(python3 test_numpy_compatibility.py 2>&1 || echo "测试失败")
\`\`\`

### 性能测试
\`\`\`
$(python3 m4_optimization_success.py 2>&1 | head -20)
\`\`\`

## 建议

1. 定期运行此脚本检查兼容性
2. 保持numpy版本更新
3. 在开发新功能时使用统一的导入方式
4. 运行CI/CD检查确保持续兼容

---
*报告由 auto_update_numpy.sh 自动生成*
EOF

    log_success "报告已生成: $REPORT_FILE"
}

# 主函数
main() {
    echo "========================================"
    echo "Numpy自动更新和维护脚本"
    echo "========================================"

    # 创建报告目录
    mkdir -p reports

    # 执行检查和更新流程
    check_versions
    echo ""

    run_compatibility_tests
    echo ""

    update_numpy
    echo ""

    update_requirements
    echo ""

    check_project_compatibility
    echo ""

    generate_report

    echo ""
    log_success "Numpy维护流程完成！"
}

# 处理命令行参数
case "${1:-}" in
    --check-only)
        check_versions
        run_compatibility_tests
        ;;
    --update-only)
        update_numpy
        update_requirements
        ;;
    --test-only)
        run_compatibility_tests
        ;;
    --help)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --check-only   仅检查版本和兼容性"
        echo "  --update-only  仅更新numpy和requirements"
        echo "  --test-only    仅运行测试"
        echo "  --help         显示此帮助信息"
        echo ""
        echo "默认: 执行完整的维护流程"
        exit 0
        ;;
    *)
        main
        ;;
esac