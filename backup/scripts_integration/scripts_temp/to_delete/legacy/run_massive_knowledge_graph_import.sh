#!/bin/bash

# Athena大规模知识图谱导入执行脚本
# 专门用于导入/private/tmp中的44GB知识图谱数据

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}"
    echo "=================================================="
    echo "🚀  Athena大规模知识图谱导入工具"
    echo "=================================================="
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}🔄 $1${NC}"
}

# 检查系统依赖
check_dependencies() {
    print_step "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi
    print_success "Python3: $(python3 --version)"

    # 检查Neo4j
    if command -v neo4j &> /dev/null; then
        if neo4j status | grep -q "running"; then
            print_success "Neo4j 正在运行"
        else
            print_warning "Neo4j 未运行，正在启动..."
            neo4j start
            sleep 10
            if neo4j status | grep -q "running"; then
                print_success "Neo4j 启动成功"
            else
                print_error "Neo4j 启动失败"
                exit 1
            fi
        fi
    else
        print_error "Neo4j 未安装"
        exit 1
    fi

    # 检查cypher-shell
    if ! command -v cypher-shell &> /dev/null; then
        print_error "cypher-shell 未安装"
        exit 1
    fi
    print_success "cypher-shell 可用"

    # 检查数据目录
    DATA_DIR="/private/tmp"
    if [ ! -d "$DATA_DIR" ]; then
        print_error "数据目录不存在: $DATA_DIR"
        exit 1
    fi

    # 统计数据大小
    TOTAL_SIZE=$(du -sh "$DATA_DIR" | cut -f1)
    print_info "数据目录大小: $TOTAL_SIZE"

    # 检查具体数据目录
    PATENT_LAYERED_DIR="$DATA_DIR/patent_full_layered_output"
    PATENT_OUTPUT_DIR="$DATA_DIR/patent_full_output"
    LEGAL_VECTORS_DIR="$DATA_DIR/legal_vectors_storage"

    if [ -d "$PATENT_LAYERED_DIR" ]; then
        PATENT_LAYERED_SIZE=$(du -sh "$PATENT_LAYERED_DIR" | cut -f1)
        PATENT_LAYERED_FILES=$(find "$PATENT_LAYERED_DIR" -name "*.json" | wc -l)
        print_info "专利分层数据: $PATENT_LAYERED_SIZE ($PATENT_LAYERED_FILES 个文件)"
    fi

    if [ -d "$PATENT_OUTPUT_DIR" ]; then
        PATENT_OUTPUT_SIZE=$(du -sh "$PATENT_OUTPUT_DIR" | cut -f1)
        PATENT_OUTPUT_FILES=$(find "$PATENT_OUTPUT_DIR" -name "*.json" | wc -l)
        print_info "专利输出数据: $PATENT_OUTPUT_SIZE ($PATENT_OUTPUT_FILES 个文件)"
    fi

    if [ -d "$LEGAL_VECTORS_DIR" ]; then
        LEGAL_VECTORS_SIZE=$(du -sh "$LEGAL_VECTORS_DIR" | cut -f1)
        print_info "法律向量数据: $LEGAL_VECTORS_SIZE"
    fi
}

# 检查Neo4j数据库状态
check_neo4j_database() {
    print_step "检查Neo4j数据库状态..."

    # 检查现有数据
    echo "RETURN count(n) as node_count;" | cypher-shell -u neo4j -p password --non-interactive --format plain 2>/dev/null | tail -1 | while read count; do
        if [ "$count" = "0" ]; then
            print_info "Neo4j数据库为空，可以开始导入"
        else
            print_warning "Neo4j数据库已存在 $count 个节点"
            read -p "是否清空现有数据？(y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_info "清空现有数据..."
                echo "MATCH (n) DETACH DELETE n;" | cypher-shell -u neo4j -p password --non-interactive
                print_success "数据清空完成"
            fi
        fi
    done
}

# 检查磁盘空间
check_disk_space() {
    print_step "检查磁盘空间..."

    # 检查Neo4j数据目录所在分区的空间
    NEO4J_DIR="/opt/homebrew/var/neo4j"
    if [ -d "$NEO4J_DIR" ]; then
        AVAILABLE_SPACE=$(df -h "$NEO4J_DIR" | awk 'NR==2 {print $4}')
        print_info "Neo4j数据目录可用空间: $AVAILABLE_SPACE"
    fi

    # 检查临时目录空间
    TEMP_AVAILABLE=$(df -h "/tmp" | awk 'NR==2 {print $4}')
    print_info "临时目录可用空间: $TEMP_AVAILABLE"
}

# 运行导入前测试
run_pre_import_test() {
    print_step "运行导入前连接测试..."

    # 测试Neo4j连接
    TEST_RESULT=$(echo "RETURN 1 as test;" | cypher-shell -u neo4j -p password --non-interactive --format plain 2>/dev/null | tail -1)
    if [ "$TEST_RESULT" = "1" ]; then
        print_success "Neo4j连接测试成功"
    else
        print_error "Neo4j连接测试失败"
        exit 1
    fi
}

# 启动导入
start_import() {
    print_step "开始大规模知识图谱导入..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    IMPORT_SCRIPT="$SCRIPT_DIR/massive_knowledge_graph_importer.py"

    if [ ! -f "$IMPORT_SCRIPT" ]; then
        print_error "导入脚本不存在: $IMPORT_SCRIPT"
        exit 1
    fi

    print_info "使用导入脚本: $IMPORT_SCRIPT"

    # 创建日志目录
    mkdir -p /tmp/athena_import_logs
    LOG_FILE="/tmp/athena_import_documentation/logs/import_$(date +%Y%m%d_%H%M%S).log"

    print_info "日志文件: $LOG_FILE"

    # 启动导入进程
    print_info "启动导入进程，这可能需要几个小时..."
    print_warning "按 Ctrl+C 可以安全中断导入，进度会被保存"

    python3 "$IMPORT_SCRIPT" 2>&1 | tee "$LOG_FILE"

    IMPORT_EXIT_CODE=${PIPESTATUS[0]}

    if [ $IMPORT_EXIT_CODE -eq 0 ]; then
        print_success "导入完成！"
    else
        print_error "导入失败，退出码: $IMPORT_EXIT_CODE"
        print_info "请检查日志文件: $LOG_FILE"
    fi
}

# 显示导入后统计
show_post_import_stats() {
    print_step "生成导入后统计报告..."

    # 获取节点和关系数量
    NODE_COUNT=$(echo "MATCH (n) RETURN count(n) as count;" | cypher-shell -u neo4j -p password --non-interactive --format plain 2>/dev/null | tail -1)
    RELATION_COUNT=$(echo "MATCH ()-[r]->() RETURN count(r) as count;" | cypher-shell -u neo4j -p password --non-interactive --format plain 2>/dev/null | tail -1)

    echo
    print_header
    print_info "导入统计报告"
    echo "总节点数: $NODE_COUNT"
    echo "总关系数: $RELATION_COUNT"

    # 获取数据库大小
    if [ -d "/opt/homebrew/var/neo4j" ]; then
        DB_SIZE=$(du -sh "/opt/homebrew/var/neo4j" | cut -f1)
        echo "数据库大小: $DB_SIZE"
    fi

    echo
    print_info "访问方式："
    echo "  Neo4j Browser: http://localhost:7474"
    echo "  连接字符串: bolt://localhost:7687"
    echo "  用户名: neo4j"
    echo "  密码: password"
}

# 清理函数
cleanup() {
    print_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --test-only     仅运行测试，不执行导入"
    echo "  --stats-only    仅显示统计信息"
    echo "  --skip-checks   跳过依赖检查"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "默认行为: 执行完整的大规模知识图谱导入流程"
    echo ""
    echo "注意: 导入可能需要几个小时，建议在后台运行"
    echo "      nohup $0 > import.log 2>&1 &"
}

# 主函数
main() {
    print_header

    # 解析命令行参数
    TEST_ONLY=false
    STATS_ONLY=false
    SKIP_CHECKS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --test-only)
                TEST_ONLY=true
                shift
                ;;
            --stats-only)
                STATS_ONLY=true
                shift
                ;;
            --skip-checks)
                SKIP_CHECKS=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 仅显示统计信息
    if [ "$STATS_ONLY" = true ]; then
        show_post_import_stats
        exit 0
    fi

    # 设置清理陷阱
    trap cleanup EXIT

    # 运行检查（除非跳过）
    if [ "$SKIP_CHECKS" = false ]; then
        check_dependencies
        check_disk_space
        check_neo4j_database
        run_pre_import_test
    fi

    # 仅测试模式
    if [ "$TEST_ONLY" = true ]; then
        print_success "所有测试通过！"
        exit 0
    fi

    # 确认开始导入
    echo
    print_warning "即将开始大规模知识图谱导入"
    print_warning "这可能需要几个小时的时间"
    read -p "确认开始导入？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "导入已取消"
        exit 0
    fi

    # 开始导入
    start_time=$(date +%s)
    start_import
    end_time=$(date +%s)

    # 计算总耗时
    duration=$((end_time - start_time))
    hours=$((duration / 3600))
    minutes=$(((duration % 3600) / 60))
    seconds=$((duration % 60))

    echo
    print_success "导入总耗时: ${hours}小时${minutes}分钟${seconds}秒"

    # 显示最终统计
    show_post_import_stats

    print_success "大规模知识图谱导入流程完成！"
}

# 运行主函数
main "$@"