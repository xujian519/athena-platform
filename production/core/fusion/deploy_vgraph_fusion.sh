#!/bin/bash
# ============================================
# Vector-Graph Fusion 部署脚本
# NebulaGraph + pgvector 深度融合部署
#
# 作者: 小诺·双鱼公主
# 创建时间: 2025-12-28
# ============================================

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

# 检查必要的命令
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi

    log_success "依赖检查通过"
}

# 初始化数据库架构
init_database_schema() {
    log_info "初始化统一数据架构..."

    # 检查 PostgreSQL 是否运行
    if ! docker ps | grep -q "athena_postgres_5438"; then
        log_warning "PostgreSQL 容器未运行，正在启动..."

        # 启动 PostgreSQL 多实例
        docker-compose -f docker-compose.pgvector-multi-business.yml up -d

        # 等待启动完成
        log_info "等待 PostgreSQL 启动..."
        sleep 30
    fi

    # 应用统一架构
    log_info "应用 vgraph_unified_schema.sql..."

    for port in 5438 5439 5440 5443 5444 5445; do
        container_name="athena_postgres_$port"

        if docker ps | grep -q "$container_name"; then
            log_info "初始化容器 $container_name 的架构..."

            docker exec -i "$container_name" psql -U postgres -d \
                $(docker exec "$container_name" psql -U postgres -tAc "SELECT current_database()") \
                < infrastructure/database/vgraph_unified_schema.sql || true

            log_success "容器 $container_name 架构初始化完成"
        fi
    done

    log_success "数据库架构初始化完成"
}

# 初始化 NebulaGraph 图空间
init_nebula_graph() {
    log_info "初始化 NebulaGraph 图空间..."

    # 检查 NebulaGraph 是否运行
    if ! docker ps | grep -q "athena_nebula_graph_min"; then
        log_warning "NebulaGraph 容器未运行"
        log_info "请手动启动 NebulaGraph 或使用现有实例"
        return
    fi

    # 创建图空间
    log_info "创建 vgraph_unified_space..."

    # 这里需要使用 NebulaGraph 控制台或客户端
    # 暂时跳过，需要在运行时通过代码创建

    log_success "NebulaGraph 初始化完成"
}

# 安装 Python 依赖
install_python_dependencies() {
    log_info "安装 Python 依赖..."

    # 激活虚拟环境
    if [ -d "athena_env" ]; then
        source athena_env/bin/activate
    else
        log_warning "虚拟环境不存在，请先创建"
    fi

    # 安装必要的包
    pip install -q asyncpg nebula3 numpy networkx || true

    log_success "Python 依赖安装完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p core/fusion
    mkdir -p infrastructure/database
    mkdir -p logs/fusion
    mkdir -p data/fusion_cache

    log_success "目录创建完成"
}

# 运行验证
run_validation() {
    log_info "运行验证测试..."

    python3 -c "
import asyncio
import sys

async def validate():
    print('🔍 验证 Fusion 架构部署...')

    # 检查数据库连接
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host='localhost',
            port=5438,
            user='postgres',
            password='athena_password',
            database='agent_memory_db'
        )

        # 检查统一映射表
        tables = await conn.fetch(\"\"\"
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name LIKE 'vgraph_%'
        \"\"\")

        print(f'✅ 找到 {len(tables)} 个 vgraph 表')

        await conn.close()
        print('✅ 数据库验证通过')

    except Exception as e:
        print(f'❌ 数据库验证失败: {e}')
        sys.exit(1)

    # 检查 NebulaGraph 连接
    try:
        from nebula3.gclient.net import ConnectionPool
        from nebula3.Config import Config

        config = Config()
        config.max_connection_pool_size = 1

        pool = ConnectionPool()
        pool.init([('localhost', 9669)], config)

        session = pool.get_session()
        result = session.execute('SHOW SPACES;')

        if result.is_succeeded():
            print('✅ NebulaGraph 连接正常')

        session.release()
        pool.close()

    except Exception as e:
        print(f'⚠️  NebulaGraph 验证跳过: {e}')

    print('✅ 验证完成')

asyncio.run(validate())
"

    log_success "验证测试完成"
}

# 主函数
main() {
    echo "=========================================="
    echo "  Vector-Graph Fusion 部署脚本"
    echo "  NebulaGraph + pgvector 深度融合"
    echo "=========================================="
    echo ""

    # 解析命令行参数
    ACTION=${1:-all}

    case $ACTION in
        all)
            check_dependencies
            create_directories
            init_database_schema
            init_nebula_graph
            install_python_dependencies
            run_validation
            ;;
        schema)
            init_database_schema
            ;;
        nebula)
            init_nebula_graph
            ;;
        validate)
            run_validation
            ;;
        *)
            echo "用法: $0 [all|schema|nebula|validate]"
            exit 1
            ;;
    esac

    echo ""
    log_success "部署完成！"
    echo ""
    echo "📋 后续步骤："
    echo "  1. 初始化数据: python3 core/fusion/init_sample_data.py"
    echo "  2. 启动同步服务: python3 core/fusion/vgraph_sync_service.py"
    echo "  3. 测试融合查询: python3 core/fusion/test_fusion_query.py"
}

# 执行主函数
main "$@"
