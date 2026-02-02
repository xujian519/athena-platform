#!/bin/bash
# Athena工作平台性能监控脚本
# 持续跟踪优化后的性能表现

set -e

# 配置
MONITOR_INTERVAL=60  # 监控间隔（秒）
LOG_FILE="logs/performance_monitor_$(date +%Y%m%d).log"
REPORT_FILE="reports/performance_report_$(date +%Y%m%d_%H%M%S).md"
ALERT_THRESHOLD=100  # 响应时间告警阈值（毫秒）
MAX_LOG_LINES=1000

# 创建必要的目录
mkdir -p logs reports

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 获取服务状态
get_service_status() {
    local service_name=$1
    local port=$2
    local url="http://localhost:$port/health"

    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $service_name (端口$port): 运行正常"
        return 0
    else
        echo "❌ $service_name (端口$port): 无法访问"
        return 1
    fi
}

# 测试查询性能
test_query_performance() {
    echo "🔍 测试向量查询性能..."

    # 使用Python脚本测试性能
    python3 << 'EOF'
import sys
import time
import numpy as np
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.vector_db.optimized_qdrant_client import OptimizedQdrantClient

    client = OptimizedQdrantClient()

    # 测试向量
    test_vector = np.random.random(1024).tolist()

    # 测试legal_clauses分片查询
    print("\nLegal Clauses分片查询测试:")
    times = []
    for i in range(10):
        start = time.time()
        results = client.search("legal_clauses", test_vector, limit=20)
        response_time = (time.time() - start) * 1000
        times.append(response_time)
        print(f"  查询 {i+1:2d}: {len(results)} 条结果, {response_time:.2f}ms")

    avg_time = sum(times) / len(times)
    print(f"\n平均响应时间: {avg_time:.2f}ms")

    # 测试其他集合
    print("\n其他集合查询测试:")
    collections = ["ai_technical_terms_1024", "legal_documents"]
    for collection in collections:
        try:
            start = time.time()
            results = client.search(collection, test_vector, limit=10)
            response_time = (time.time() - start) * 1000
            print(f"  {collection}: {len(results)} 条结果, {response_time:.2f}ms")
        except Exception as e:
            print(f"  {collection}: 错误 - {str(e)[:50]}")

    # 获取缓存统计
    cache_stats = client.get_cache_stats()
    print("\n缓存统计:")
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")

    # 返回性能数据
    performance_data = {
        "avg_legal_clauses_time": avg_time,
        "cache_stats": cache_stats,
        "timestamp": time.time()
    }

    print("\nPERFORMANCE_DATA:" + json.dumps(performance_data))

except Exception as e:
    print(f"ERROR: {str(e)}")
    print("PERFORMANCE_DATA:{}")
EOF
}

# 获取Redis缓存信息
get_redis_info() {
    echo "📊 Redis缓存信息:"
    if redis-cli -p 6379 ping > /dev/null 2>&1; then
        redis_info=$(redis-cli -p 6379 info memory 2>/dev/null)
        if [ "$redis_info" ]; then
            used_memory=$(echo "$redis_info" | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
            echo "  内存使用: $used_memory"
        fi

        # 获取缓存大小
        cache_size=$(redis-cli -p 6379 dbsize 2>/dev/null || echo "N/A")
        echo "  缓存条目: $cache_size"

        # 获取命中率（如果可用）
        hit_rate=$(redis-cli -p 6379 info stats 2>/dev/null | grep "keyspace" | wc -l)
        echo "  活跃数据库: $hit_rate"
    else
        echo "  ❌ Redis未连接"
    fi
}

# 获取Qdrant统计
get_qdrant_info() {
    echo "🗃️ Qdrant向量数据库信息:"
    if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
        # 获取集合列表
        collections=$(curl -s http://localhost:6333/collections 2>/dev/null | jq -r '.result.collections[] | .name' 2>/dev/null)

        total_vectors=0
        for collection in $collections; do
            count=$(curl -s "http://localhost:6333/collections/$collection" | jq -r '.result.vectors_count' 2>/dev/null || echo "0")
            total_vectors=$((total_vectors + count))
            echo "  $collection: $count 向量"
        done

        echo "  总向量数: $total_vectors"
    else
        echo "  ❌ Qdrant未连接"
    fi
}

# 获取Docker容器状态
get_docker_status() {
    echo "🐳 Docker容器状态:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | while read line; do
        if [[ $line == *"health"* ]]; then
            echo "$line"
        elif [[ $line == *"Up"* ]]; then
            echo "$line"
        fi
    done
}

# 检查系统资源
check_system_resources() {
    echo "💻 系统资源状态:"

    # CPU使用率
    cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    echo "  CPU使用率: ${cpu_usage}%"

    # 内存使用
    memory_pressure=$(top -l 1 -n 0 | grep "PhysMem" | awk '{print $2 "/" $3}')
    echo "  内存使用: $memory_pressure"

    # 磁盘使用
    disk_usage=$(df -h . | tail -1 | awk '{print $3 "/" $4 " (" $5 ")"}')
    echo "  磁盘使用: $disk_usage"
}

# 生成性能报告
generate_report() {
    local report_content="$1"
    echo "📝 生成性能报告..."

    cat > "$REPORT_FILE" << EOF
# Athena工作平台性能监控报告

**生成时间**: $(date '+%Y-%m-%d %H:%M:%S')
**监控间隔**: ${MONITOR_INTERVAL}秒

---

## 📊 实时性能数据

$report_content

---

## 🎯 性能指标

| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| Legal Clauses查询响应时间 | 待更新 | <10ms | ⏳ |
| 缓存命中率 | 待更新 | >70% | ⏳ |
| 系统可用性 | 待更新 | 99% | ⏳ |

---

## 📈 历史趋势

[此处可添加图表或历史数据]

---

## 💡 优化建议

1. **缓存优化**
   - 监控缓存命中率，目标70%+
   - 调整TTL参数

2. **查询优化**
   - Legal Clauses分片已实现
   - 继续监控分片查询性能

3. **资源优化**
   - 监控内存和CPU使用
   - 考虑自动扩展

---

*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF

    echo "✅ 报告已生成: $REPORT_FILE"
}

# 主监控循环
main() {
    log "🚀 启动Athena工作平台性能监控..."
    log "监控间隔: ${MONITOR_INTERVAL}秒"

    # 初始检查
    log "\n===== 初始状态检查 ====="
    get_docker_status
    echo
    get_service_status "Athena主平台" 8000
    get_service_status "API网关" 8020
    echo
    get_redis_info
    echo
    get_qdrant_info
    echo
    check_system_resources

    # 性能测试
    echo
    performance_data=$(test_query_performance)

    # 生成初始报告
    generate_report "初始数据收集完成"

    log "✅ 初始检查完成"

    # 持续监控
    log "\n===== 开始持续监控 ====="
    while true; do
        sleep $MONITOR_INTERVAL

        log "\n===== $(date '+%H:%M:%S') 监控检查 ====="

        # 获取性能数据
        performance_data=$(test_query_performance 2>/dev/null || echo "")

        # 检查关键指标
        if echo "$performance_data" | grep -q "avg_legal_clauses_time"; then
            avg_time=$(echo "$performance_data" | grep "avg_legal_clauses_time" | cut -d'"' -f4)
            log "📊 Legal Clauses平均响应时间: ${avg_time}ms"

            # 检查是否需要告警
            if (( $(echo "$avg_time > $ALERT_THRESHOLD" | bc -l 2>/dev/null || echo "0"))); then
                log "⚠️ 告警: 响应时间超过阈值 ($ALERT_THRESHOLD ms)!"
            fi
        fi

        # 每小时生成一次报告
        current_min=$(date +%M)
        if [ "$current_min" = "00" ]; then
            log "📝 生成小时报告..."
            generate_report "$(date '+%H:%M:%S')的性能数据"
        fi

        # 保持日志文件大小
        if [ $(wc -l < "$LOG_FILE" | cut -d' ' -f1) -gt $MAX_LOG_LINES ]; then
            tail -n $((MAX_LOG_LINES/2)) "$LOG_FILE" > "${LOG_FILE}.tmp"
            mv "${LOG_FILE}.tmp" "$LOG_FILE"
        fi
    done
}

# 信号处理
trap 'log "\n🛑 监控已停止"; exit 0' INT TERM

# 执行监控
main "$@"