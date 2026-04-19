#!/bin/bash

# 专业数据快速重建脚本
# Professional Data Quick Rebuild Script

set -e  # 遇到错误立即退出

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

# 标题
print_header() {
    echo -e "${BLUE}"
    echo "========================================"
    echo "   专业数据高质量重建系统"
    echo "   Professional Data Rebuild System"
    echo "========================================"
    echo -e "${NC}"
}

# 检查系统环境
check_environment() {
    log_info "检查系统环境..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装"
        exit 1
    fi

    # 检查必要的Python包
    log_info "检查Python依赖包..."
    python3 -c "import aiohttp, json, asyncio, hashlib, uuid" 2>/dev/null || {
        log_warning "缺少必要的Python包，正在安装..."
        pip3 install aiohttp asyncio
    }

    # 检查目录
    if [ ! -d "/Users/xujian/Athena工作平台/production" ]; then
        log_error "生产目录不存在"
        exit 1
    fi

    # 检查服务
    log_info "检查运行服务..."

    # 检查NLP服务
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        log_success "NLP服务运行正常"
    else
        log_warning "NLP服务未运行，正在启动..."
        ./start_nlp_service.sh &
        sleep 5
    fi

    # 检查LLM服务
    if curl -s http://localhost:8002/api/tags > /dev/null 2>&1; then
        log_success "LLM服务运行正常"
    else
        log_warning "LLM服务未运行，请手动启动"
    fi

    # 检查Docker服务
    if docker ps | grep -q qdrant; then
        log_success "Qdrant服务运行正常"
    else
        log_warning "Qdrant服务未运行"
    fi

    if docker ps | grep -q nebula; then
        log_success "NebulaGraph服务运行正常"
    else
        log_warning "NebulaGraph服务未运行"
    fi

    log_success "环境检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p /Users/xujian/Athena工作平台/production/data/vector_db
    mkdir -p /Users/xujian/Athena工作平台/production/data/knowledge_graph
    mkdir -p /Users/xujian/Athena工作平台/production/data/patent_data
    mkdir -p /Users/xujian/Athena工作平台/production/logs

    log_success "目录创建完成"
}

# 清理旧数据
clean_old_data() {
    log_info "清理旧数据..."

    read -p "是否要清理旧数据? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf /Users/xujian/Athena工作平台/production/data/vector_db/*
        rm -rf /Users/xujian/Athena工作平台/production/data/knowledge_graph/*
        log_success "旧数据清理完成"
    else
        log_info "跳过数据清理"
    fi
}

# 执行重建
execute_rebuild() {
    log_info "开始执行重建..."

    # 切换到生产目录
    cd /Users/xujian/Athena工作平台/production

    # 创建日志文件
    LOG_FILE="logs/rebuild_$(date +%Y%m%d_%H%M%S).log"

    # 执行重建脚本
    log_info "执行重建脚本..."
    python3 dev/scripts/rebuild_all_professional_data.py 2>&1 | tee "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log_success "重建完成！"
    else
        log_error "重建失败，请查看日志: $LOG_FILE"
        exit 1
    fi
}

# 导入数据到数据库
import_data() {
    log_info "准备导入数据到数据库..."

    # 检查是否有导入脚本
    if [ -f "dev/scripts/import_to_qdrant.sh" ]; then
        read -p "是否导入向量数据到Qdrant? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ./dev/scripts/import_to_qdrant.sh
        fi
    fi

    if [ -f "dev/scripts/import_to_nebula.sh" ]; then
        read -p "是否导入知识图谱到NebulaGraph? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ./dev/scripts/import_to_nebula.sh
        fi
    fi

    log_info "如需手动导入，请参考文档: docs/professional_data_rebuild_guide.md"
}

# 显示报告
show_report() {
    log_info "查看重建报告..."

    REPORT_FILE="rebuild_report.json"
    if [ -f "$REPORT_FILE" ]; then
        echo
        log_success "重建报告摘要:"
        python3 -c "
import json
with open('$REPORT_FILE', 'r') as f:
    report = json.load(f)

print('  开始时间:', report['rebuild_summary']['start_time'])
print('  完成任务:', report['rebuild_summary']['completed_tasks'])
print('  失败任务:', report['rebuild_summary']['failed_tasks'])
print('  总向量数:', report['quality_metrics']['total_vectors'])
print('  总实体数:', report['quality_metrics']['total_entities'])
print('  总关系数:', report['quality_metrics']['total_relations'])
"
        echo
        log_info "完整报告: $REPORT_FILE"
    else
        log_warning "未找到重建报告"
    fi
}

# 主函数
main() {
    print_header

    # 确认执行
    read -p "确定要重建所有专业数据吗? 这个过程可能需要几个小时 (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi

    # 执行步骤
    check_environment
    create_directories
    clean_old_data
    execute_rebuild
    import_data
    show_report

    log_success "所有操作完成！"
    echo
    log_info "下一步:"
    echo "  1. 查看重建报告了解详情"
    echo "  2. 导入数据到生产数据库"
    echo "  3. 测试系统功能"
    echo "  4. 更新应用配置"
    echo
    log_info "如有问题，请查看日志或联系技术支持"
}

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -c, --check    仅检查环境"
    echo "  -q, --quick    快速重建（跳过确认）"
    echo
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--check)
            check_environment
            exit 0
            ;;
        -q|--quick)
            QUICK_MODE=1
            shift
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 设置快速模式
if [ "$QUICK_MODE" = "1" ]; then
    log_warning "快速重建模式：跳过确认"
    main
else
    main
fi