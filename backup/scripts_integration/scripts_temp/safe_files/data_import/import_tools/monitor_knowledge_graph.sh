#!/bin/bash
# 知识图谱监控脚本

echo "📊 知识图谱实时监控"
echo "按Ctrl+C停止监控"
echo "========================================"

while true; do
    clear
    echo "📊 知识图谱实时监控 - $(date)"
    echo "========================================"

    # 检查服务状态
    echo "服务状态:"
    if nc -z localhost 8182; then
        echo "  JanusGraph: ✅ 运行中"
    else
        echo "  JanusGraph: ❌ 未运行"
    fi

    if nc -z localhost 6333; then
        echo "  Qdrant: ✅ 运行中"
    else
        echo "  Qdrant: ❌ 未运行"
    fi

    if nc -z localhost 8080; then
        echo "  API服务: ✅ 运行中"
    else
        echo "  API服务: ❌ 未运行"
    fi

    echo ""
    echo "数据统计:"

    # 获取顶点和边数量
    vertex_count=$(echo "g.V().count()" | gremlin.sh - 2>/dev/null | tail -n +2 | head -1)
    edge_count=$(echo "g.E().count()" | gremlin.sh - 2>/dev/null | tail -n +2 | head -1)

    echo "  顶点总数: $vertex_count"
    echo "  边总数: $edge_count"

    # 获取API统计
    if curl -s http://localhost:8080/api/v1/stats > /dev/null; then
        api_stats=$(curl -s http://localhost:8080/api/v1/stats 2>/dev/null)
        echo "  API调用: $(echo "$api_stats" | jq -r '.total_queries // "N/A"')"
    fi

    echo ""
    echo "系统资源:"
    echo "  内存使用: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "  磁盘使用: $(df -h / | awk 'NR==2{print $5}')"
    echo "  CPU负载: $(uptime | awk -F'load average:' '{print $2}')"

    sleep 5
done
