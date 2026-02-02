#!/bin/bash
# 快速性能监控脚本

echo "🔍 Athena工作平台快速性能监控"
echo "================================"

# 检查容器状态
echo -e "\n📊 容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep athena

# 测试服务响应
echo -e "\n🚀 服务响应测试:"
services=("8000:主平台" "8020:API网关" "9000:平台管理器")
for service in "${services[@]}; do
    port=${service%:*}
    name=${service#*:}
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ $name (端口$port): 正常"
    else
        echo "  ❌ $name (端口$port): 无响应"
    fi
done

# 快速性能测试
echo -e "\n⚡ 性能快速测试:"
python3 << 'EOF' 2>/dev/null
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
    test_vector = np.random.random(1024).tolist()

    # 测试查询
    times = []
    for i in range(5):
        start = time.time()
        results = client.search("legal_clauses", test_vector, limit=10)
        response_time = (time.time() - start) * 1000
        times.append(response_time)
        print(f"  查询 {i+1}: {response_time:.2f}ms")

    avg_time = sum(times) / len(times)
    print(f"\n  📈 平均响应时间: {avg_time:.2f}ms")

    # 缓存统计
    cache_stats = client.get_cache_stats()
    hit_rate = cache_stats.get('hit_rate', '0%')
    print(f"  💾 缓存命中率: $hit_rate")

except Exception as e:
    print(f"  ❌ 测试失败: {str(e)[:50]}")
EOF

# 系统资源
echo -e "\n💻 系统资源:"
echo "  CPU: $(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')%"
echo "  内存: $(top -l 1 -n 0 | grep "PhysMem" | awk '{print $2 "/" $3}')"
echo "  磁盘: $(df -h . | tail -1 | awk '{print $3 "/" $4 " (" $5 ")"}')"

echo -e "\n✅ 监控完成 - $(date '+%H:%M:%S')"