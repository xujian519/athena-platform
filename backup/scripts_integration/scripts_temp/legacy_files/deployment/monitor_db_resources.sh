#!/bin/bash
# 数据库资源监控脚本

echo "📊 数据库资源占用监控"
echo "===================="
echo ""

# 获取当前时间
timestamp=$(date "+%Y-%m-%d %H:%M:%S")
echo "⏰ 时间: $timestamp"
echo ""

# 检查磁盘使用
echo "💾 磁盘使用情况:"
df -h | grep -E "(文件系统|/var|/usr|/opt)" | head -5
echo ""

# 检查内存使用
echo "🧠 内存使用情况:"
free -h
echo ""

# 检查数据库进程
echo "🗄️ 数据库进程:"
echo "PostgreSQL:"
ps aux | grep postgres | grep -v grep | awk '{print "  PID:", $2, " CPU:", $3"%", " MEM:", $4"%", " CMD:", $11}' | head -3
echo ""
echo "ArangoDB:"
ps aux | grep arangod | grep -v grep | awk '{print "  PID:", $2, " CPU:", $3"%", " MEM:", $4"%"}' || echo "  未运行"
echo ""
echo "Milvus:"
ps aux | grep -E "(milvus|pulsar|minio)" | grep -v grep | awk '{print "  PID:", $2, " CPU:", $3"%", " MEM:", $4"%", " CMD:", $11}' | head -5

# 检查端口占用
echo ""
echo "🔌 端口占用:"
echo "PostgreSQL (5432):"
lsof -i :5432 | grep LISTEN | awk '{print "  " $1 " PID:" $2}' || echo "  未监听"
echo ""
echo "ArangoDB (8529):"
lsof -i :8529 | grep LISTEN | awk '{print "  " $1 " PID:" $2}' || echo "  未监听"
echo ""
echo "Milvus (19530):"
lsof -i :19530 | grep LISTEN | awk '{print "  " $1 " PID:" $2}' || echo "  未监听"

# 总资源使用
echo ""
echo "📈 总资源使用:"
echo "CPU: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')%"
echo "内存: $(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//' | awk '{printf "%.1f GB\n", $1*4096/1024/1024/1024}') 可用"
echo "磁盘: $(df -h / | awk 'NR==2{print $4}') 可用"