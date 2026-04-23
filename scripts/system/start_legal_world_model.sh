#!/bin/bash
# ============================================================================
# Athena法律世界模型 - 三库联动启动脚本
# Legal World Model - Triple Database Startup Script
#
# 功能：启动PostgreSQL + Neo4j + Qdrant，确保使用持久化数据
# 作者：Athena平台团队
# 版本：v1.0.0
# ============================================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查系统环境
check_environment() {
    log_step "检查系统环境..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        return 1
    fi

    # 启动Docker Desktop（如果未运行）
    if ! docker info &> /dev/null; then
        log_info "正在启动Docker..."
        open -a Docker
        sleep 5
        # 等待Docker启动
        local max_wait=60
        local waited=0
        while ! docker info &> /dev/null && [ $waited -lt $max_wait ]; do
            sleep 2
            waited=$((waited + 2))
        done

        if ! docker info &> /dev/null; then
            log_error "Docker启动超时"
            return 1
        fi
    fi

    log_info "✅ Docker环境正常"
    return 0
}

# 显示数据持久化状态
show_data_status() {
    log_step "数据持久化状态..."

    echo ""
    echo "📊 三库数据状态："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # PostgreSQL
    if psql -h localhost -U postgres -d postgres -c "SELECT 1" &> /dev/null; then
        local pg_size=$(psql -h localhost -U postgres -d postgres -t -c "
            SELECT pg_size_pretty(pg_database_size('postgres')) as size
        " 2>/dev/null | xargs)
        echo "✅ PostgreSQL: $pg_size (运行中)"
    else
        echo "⚠️  PostgreSQL: 未运行 (通过Homebrew持久化)"
    fi

    # Neo4j
    if curl -s http://localhost:7474 | grep -q "neo4j"; then
        local nodes=$(curl -s http://localhost:7474/db/neo4j/tx/commit \
            -H "Content-Type: application/json" \
            -d '{"statements":[{"statement":"MATCH (n) RETURN count(n) as count"}]}' \
            2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); print(data['results'][0]['data'][0]['row'][0])" 2>/dev/null || echo "N/A")
        echo "✅ Neo4j: $nodes 节点 (运行中)"
    else
        local neo4j_size=$(du -sh /opt/homebrew/var/neo4j/data 2>/dev/null | cut -f1)
        echo "⚠️  Neo4j: 未运行 (数据: $neo4j_size)"
    fi

    # Qdrant
    if curl -s http://localhost:6333 | grep -q "qdrant"; then
        local collections=$(curl -s http://localhost:6333/collections \
            | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('result',{}).get('collections',[])))" 2>/dev/null || echo "0")
        echo "✅ Qdrant: $collections 集合 (运行中)"
    else
        local qdrant_size=$(du -sh "$PROJECT_ROOT/data/qdrant/storage" 2>/dev/null | cut -f1)
        echo "⚠️  Qdrant: 未运行 (数据: $qdrant_size)"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# 启动PostgreSQL（Homebrew安装的版本）
start_postgresql() {
    log_step "启动PostgreSQL..."

    # 检查PostgreSQL是否已运行（尝试多个版本）
    for pg_ver in "postgresql@17" "postgresql@15" "postgresql"; do
        if brew services list | grep -q "$pg_ver.*started"; then
            if psql -h localhost -U postgres -d postgres -c "SELECT 1" &> /dev/null; then
                log_info "✅ PostgreSQL已在运行 ($pg_ver)"
                return 0
            fi
        fi
    done

    # 尝试启动PostgreSQL
    log_info "正在启动PostgreSQL..."
    if brew services start postgresql@17 2>/dev/null || \
       brew services start postgresql@15 2>/dev/null || \
       brew services start postgresql 2>/dev/null; then
        sleep 3
        if psql -h localhost -U postgres -d postgres -c "SELECT 1" &> /dev/null; then
            log_info "✅ PostgreSQL启动成功"
            return 0
        fi
    fi

    log_error "PostgreSQL启动失败"
    return 1
}

# 启动Neo4j
start_neo4j() {
    log_step "启动Neo4j..."

    # 检查Neo4j是否已运行
    if curl -s http://localhost:7474 | grep -q "neo4j"; then
        log_info "✅ Neo4j已在运行"
        return 0
    fi

    # 启动Neo4j
    log_info "正在启动Neo4j..."
    if neo4j start 2>&1 | head -5; then
        sleep 5

        if curl -s http://localhost:7474 | grep -q "neo4j"; then
            log_info "✅ Neo4j启动成功 (http://localhost:7474)"
            return 0
        fi
    fi

    log_error "Neo4j启动失败"
    return 1
}

# 启动Qdrant（使用持久化数据）
start_qdrant() {
    log_step "启动Qdrant向量数据库..."

    # 检查是否已有Qdrant容器在运行
    if curl -s http://localhost:6333 | grep -q "qdrant"; then
        log_info "✅ Qdrant已在运行"
        return 0
    fi

    # 停止可能存在的旧容器
    docker stop athena-qdrant athena-qdrant-new 2>/dev/null || true
    docker rm athena-qdrant athena-qdrant-new 2>/dev/null || true

    # 使用持久化存储启动Qdrant
    log_info "正在启动Qdrant（使用持久化数据）..."

    docker run -d --name athena-qdrant-new \
        -p 6333:6333 -p 6334:6334 \
        -v "$PROJECT_ROOT/data/qdrant/storage:/qdrant/storage:z" \
        -e QDRANT__SERVICE__HTTP_PORT=6333 \
        -e QDRANT__SERVICE__GRPC_PORT=6334 \
        -e QDRANT__LOG_LEVEL=INFO \
        --restart unless-stopped \
        qdrant/qdrant:latest > /dev/null

    sleep 8

    if curl -s http://localhost:6333 | grep -q "qdrant"; then
        log_info "✅ Qdrant启动成功 (http://localhost:6333)"
        return 0
    fi

    log_error "Qdrant启动失败"
    return 1
}

# 验证三库连接
verify_connections() {
    log_step "验证三库连接..."

    local all_ok=true

    # 检查PostgreSQL
    if psql -h localhost -U postgres -d postgres -c "SELECT 1" &> /dev/null; then
        echo "  ✅ PostgreSQL连接正常"
    else
        echo "  ❌ PostgreSQL连接失败"
        all_ok=false
    fi

    # 检查Neo4j
    if curl -s http://localhost:7474 | grep -q "neo4j"; then
        echo "  ✅ Neo4j连接正常"
    else
        echo "  ❌ Neo4j连接失败"
        all_ok=false
    fi

    # 检查Qdrant
    if curl -s http://localhost:6333 | grep -q "qdrant"; then
        echo "  ✅ Qdrant连接正常"
    else
        echo "  ❌ Qdrant连接失败"
        all_ok=false
    fi

    return $([ "$all_ok" = true ])
}

# 显示数据统计
show_data_statistics() {
    log_step "数据统计..."

    echo ""
    echo "📊 数据库详细统计："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # PostgreSQL统计
    echo ""
    echo "🔹 PostgreSQL (postgres数据库):"
    python3 << 'EOF'
import psycopg2
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='athena_dev_password_2024_secure',
        database='postgres'
    )
    cur = conn.cursor()

    # 数据库大小
    cur.execute("""
        SELECT
            datname,
            pg_size_pretty(pg_database_size(datname)) as size
        FROM pg_database
        WHERE datistemplate = false
        ORDER BY pg_database_size(datname) DESC
        LIMIT 5
    """)
    print("  数据库:")
    for row in cur.fetchall():
        print(f"    - {row[0]:30} {row[1]:15}")

    # 主要表大小
    cur.execute("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 5
    """)
    print("  主要表:")
    for row in cur.fetchall():
        print(f"    - {row[1]:40} {row[2]:15}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"    查询失败: {e}")
EOF

    # Neo4j统计
    echo ""
    echo "🔗 Neo4j图数据库:"
    python3 << 'EOF'
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'athena_neo4j_2024'))
    with driver.session() as session:
        # 节点统计
        result = session.run('MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC LIMIT 5')
        print("  节点类型:")
        for record in result:
            print(f"    - {record['label']:30} {record['count']:10,}")

        # 关系统计
        result = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC LIMIT 5')
        print("  关系类型:")
        for record in result:
            print(f"    - {record['type']:30} {record['count']:10,}")

    driver.close()
except Exception as e:
    print(f"    查询失败: {e}")
EOF

    # Qdrant统计
    echo ""
    echo "🔍 Qdrant向量数据库:"
    python3 << 'EOF'
import requests
try:
    response = requests.get('http://localhost:6333/collections')
    data = response.json()
    if 'result' in data and 'collections' in data['result']:
        collections = data['result']['collections']
        total_points = sum(c.get('points_count', 0) for c in collections)
        total_vectors = sum(c.get('indexed_vectors_count', 0) for c in collections)
        print(f"  总集合数: {len(collections)}")
        print(f"  总点数: {total_points:,}")
        print(f"  总向量数: {total_vectors:,}")
        print("  主要集合:")
        for col in sorted(collections, key=lambda x: x.get('points_count', 0), reverse=True)[:5]:
            name = col['name']
            points = col.get('points_count', 0)
            vectors = col.get('indexed_vectors_count', 0)
            if points > 0 or vectors > 0:
                print(f"    - {name:35} 点:{points:>8,} 向量:{vectors:>8,}")
except Exception as e:
    print(f"    查询失败: {e}")
EOF

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "🌐 服务访问地址："
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  PostgreSQL:"
    echo "    - 主机: localhost:5432"
    echo "    - 数据库: postgres (8GB+)"
    echo "    - 用户: postgres"
    echo ""
    echo "  Neo4j:"
    echo "    - HTTP: http://localhost:7474"
    echo "    - Bolt: bolt://localhost:7687"
    echo "    - 用户: neo4j"
    echo "    - 数据: 295,753+ 节点"
    echo ""
    echo "  Qdrant:"
    echo "    - HTTP: http://localhost:6333"
    echo "    - Dashboard: http://localhost:6333/dashboard"
    echo "    - 数据: 130,000+ 向量"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# 主函数
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  🏛️ Athena法律世界模型 - 三库联动启动系统                 ║"
    echo "║     Legal World Model - Triple Database Startup            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # 检查环境
    if ! check_environment; then
        log_error "环境检查失败"
        exit 1
    fi

    # 显示当前数据状态
    show_data_status

    # 启动三库
    if ! start_postgresql; then
        log_error "PostgreSQL启动失败"
        exit 1
    fi

    if ! start_neo4j; then
        log_warn "Neo4j启动失败，继续..."
    fi

    if ! start_qdrant; then
        log_warn "Qdrant启动失败，继续..."
    fi

    # 验证连接
    echo ""
    if verify_connections; then
        log_info "✅ 所有数据库启动成功！"
    else
        log_warn "⚠️  部分数据库启动失败，请检查日志"
    fi

    # 显示数据统计
    show_data_statistics

    # 显示访问信息
    show_access_info

    echo ""
    log_info "🎉 三库联动系统启动完成！"
    echo ""
}

# 运行主函数
main "$@"
