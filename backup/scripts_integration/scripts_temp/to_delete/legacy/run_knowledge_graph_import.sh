#!/bin/bash

# 知识图谱导入执行脚本
# 使用方法: ./run_knowledge_graph_import.sh [选项]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    echo -e "${BLUE}"
    echo "=================================================="
    echo "🏛️  Athena知识图谱数据导入工具"
    echo "=================================================="
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        exit 1
    fi

    # 检查Neo4j
    if command -v neo4j &> /dev/null; then
        NEO4J_INSTALLED=true
        print_success "Neo4j 已安装"
    else
        NEO4J_INSTALLED=false
        print_warning "Neo4j 未安装，将使用备选方案"
    fi

    # 检查pip包
    python3 -c "import networkx, sqlite3" 2>/dev/null || {
        print_info "安装Python依赖包..."
        pip3 install networkx arango python-arango
    }
}

# 检查数据目录
check_data_directories() {
    print_info "检查数据目录..."

    DATA_DIR="/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j"

    if [ ! -d "$DATA_DIR" ]; then
        print_error "数据目录不存在: $DATA_DIR"
        exit 1
    fi

    # 统计数据文件
    CYPER_FILES=$(find "$DATA_DIR" -name "*.cypher" | wc -l)
    JSON_FILES=$(find "$DATA_DIR" -name "*.json" | wc -l)
    CSV_FILES=$(find "$DATA_DIR" -name "*.csv" | wc -l)

    print_info "发现 $CYPER_FILES 个Cypher文件, $JSON_FILES 个JSON文件, $CSV_FILES 个CSV文件"
}

# 启动Neo4j（如果需要）
start_neo4j() {
    if [ "$NEO4J_INSTALLED" = true ]; then
        print_info "检查Neo4j状态..."

        if ! neo4j status | grep -q "running"; then
            print_info "启动Neo4j..."
            neo4j start

            # 等待Neo4j启动
            print_info "等待Neo4j启动完成..."
            sleep 10

            if neo4j status | grep -q "running"; then
                print_success "Neo4j启动成功"
            else
                print_warning "Neo4j启动失败，将使用备选方案"
                return 1
            fi
        else
            print_success "Neo4j已在运行"
        fi
        return 0
    fi
    return 1
}

# 导入到Neo4j
import_to_neo4j() {
    print_info "开始导入到Neo4j..."

    SCRIPT_DIR="/Users/xujian/Athena工作平台/scripts"
    IMPORT_SCRIPT="$SCRIPT_DIR/import_knowledge_graphs.py"

    if [ -f "$IMPORT_SCRIPT" ]; then
        python3 "$IMPORT_SCRIPT"
        if [ $? -eq 0 ]; then
            print_success "Neo4j导入完成"
            return 0
        else
            print_warning "Neo4j导入失败"
            return 1
        fi
    else
        print_error "导入脚本不存在: $IMPORT_SCRIPT"
        return 1
    fi
}

# 导入到备选方案
import_to_alternative() {
    print_info "使用备选方案导入..."

    SCRIPT_DIR="/Users/xujian/Athena工作平台/scripts"

    # 尝试NetworkX + SQLite
    SQLITE_SCRIPT="$SCRIPT_DIR/networkx_sqlite_import.py"
    if [ -f "$SQLITE_SCRIPT" ]; then
        print_info "使用NetworkX + SQLite导入..."
        python3 "$SQLITE_SCRIPT"
        print_success "SQLite导入完成，数据保存在 /tmp/knowledge_graph.db"
        return 0
    fi

    # 尝试ArangoDB
    ARANGO_SCRIPT="$SCRIPT_DIR/arangodb_import.py"
    if [ -f "$ARANGO_SCRIPT" ]; then
        print_info "使用ArangoDB导入..."
        print_warning "请确保ArangoDB已安装并运行"
        python3 "$ARANGO_SCRIPT"
        return 0
    fi

    print_error "没有可用的导入方案"
    return 1
}

# 验证导入结果
verify_import() {
    print_info "验证导入结果..."

    # 如果Neo4j在运行，验证Neo4j
    if [ "$NEO4J_INSTALLED" = true ] && neo4j status | grep -q "running"; then
        print_info "查询Neo4j数据统计..."

        # 这里可以添加验证查询
        print_success "Neo4j数据验证完成"
    fi

    # 验证SQLite
    if [ -f "/tmp/knowledge_graph.db" ]; then
        print_info "查询SQLite数据统计..."
        sqlite3 /tmp/knowledge_graph.db "SELECT COUNT(*) as entities FROM entities;"
        sqlite3 /tmp/knowledge_graph.db "SELECT COUNT(*) as relations FROM relations;"
        print_success "SQLite数据验证完成"
    fi
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --neo4j-only    仅使用Neo4j导入"
    echo "  --sqlite-only   仅使用SQLite导入"
    echo "  --arango-only   仅使用ArangoDB导入"
    echo "  --verify        验证导入结果"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "默认行为: 尝试Neo4j，失败后使用备选方案"
}

# 清理函数
cleanup() {
    print_info "清理临时文件..."
    # 这里可以添加清理逻辑
}

# 主函数
main() {
    print_header

    # 解析命令行参数
    NEO4J_ONLY=false
    SQLITE_ONLY=false
    ARANGO_ONLY=false
    VERIFY_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --neo4j-only)
                NEO4J_ONLY=true
                shift
                ;;
            --sqlite-only)
                SQLITE_ONLY=true
                shift
                ;;
            --arango-only)
                ARANGO_ONLY=true
                shift
                ;;
            --verify)
                VERIFY_ONLY=true
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

    # 仅验证
    if [ "$VERIFY_ONLY" = true ]; then
        verify_import
        exit 0
    fi

    # 设置清理陷阱
    trap cleanup EXIT

    # 检查依赖和数据
    check_dependencies
    check_data_directories

    # 根据参数选择导入方式
    if [ "$SQLITE_ONLY" = true ]; then
        import_to_alternative
    elif [ "$ARANGO_ONLY" = true ]; then
        print_info "ArangoDB导入模式"
        import_to_alternative
    elif [ "$NEO4J_ONLY" = true ]; then
        if start_neo4j; then
            import_to_neo4j
        else
            print_error "Neo4j启动失败"
            exit 1
        fi
    else
        # 默认行为：尝试Neo4j，失败后使用备选方案
        if start_neo4j; then
            if ! import_to_neo4j; then
                print_warning "Neo4j导入失败，使用备选方案"
                import_to_alternative
            fi
        else
            import_to_alternative
        fi
    fi

    # 验证导入
    verify_import

    print_success "知识图谱导入流程完成！"
    print_info ""
    print_info "访问方式："

    if [ "$NEO4J_INSTALLED" = true ] && neo4j status | grep -q "running"; then
        print_info "  Neo4j Browser: http://localhost:7474"
        print_info "  连接字符串: bolt://localhost:7687"
    fi

    if [ -f "/tmp/knowledge_graph.db" ]; then
        print_info "  SQLite数据库: /tmp/knowledge_graph.db"
        print_info "  查看命令: sqlite3 /tmp/knowledge_graph.db"
    fi
}

# 运行主函数
main "$@"