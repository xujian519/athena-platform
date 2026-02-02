#!/bin/bash
# 系统状态监控脚本

echo "🔍 Athena工作平台系统状态监控"
echo "================================"
echo "监控时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. Docker容器状态
echo "📊 Docker容器状态:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep athena

echo ""
echo "🚀 服务端口测试:"
test_port() {
    local port=$1
    local name=$2
    if curl -s --max-time 2 "http://localhost:$port" > /dev/null 2>&1; then
        echo "  ✅ $name (端口$port): 运行中"
        return 0
    else
        echo "  ❌ $name (端口$port): 无响应"
        return 1
    fi
}

test_port 8000 "主平台服务"
test_port 8020 "API网关"
test_port 9000 "平台管理器"

echo ""
echo "💾 缓存和数据库状态:"
if nc -z localhost 6379 2>/dev/null; then
    echo "  ✅ Redis (端口6379): 正常"
else
    echo "  ❌ Redis (端口6379): 无响应"
fi

if nc -z localhost 6333 2>/dev/null; then
    echo "  ✅ Qdrant (端口6333): 正常"
else
    echo "  ❌ Qdrant (端口6333): 无响应"
fi

if nc -z localhost 5432 2>/dev/null; then
    echo "  ✅ PostgreSQL (端口5432): 正常"
else
    echo "  ❌ PostgreSQL (端口5432): 无响应"
fi

echo ""
echo "📈 系统资源:"
echo "  CPU使用率: $(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')%"
echo "  内存使用: $(top -l 1 -n 0 | grep "PhysMem" | awk '{print $2 "/" $3}' | sed 's/[()]//g')"
echo "  磁盘使用: $(df -h . | tail -1 | awk '{print $3 "/" $4 " (" $5 ")"}')"

echo ""
echo "📋 最新日志文件:"
ls -lt logs/*.log 2>/dev/null | head -5 | awk '{print "  " $9 " (" $5 " " $6 " " $7 ")"}' || echo "  无日志文件"

echo ""
echo "✅ 监控完成"