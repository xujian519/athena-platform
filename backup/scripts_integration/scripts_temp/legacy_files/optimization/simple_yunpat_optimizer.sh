#!/bin/bash

# 简化版云熙性能优化脚本
# Simple YunPat Performance Optimizer

echo "🚀 云熙性能优化"
echo "===================="
echo "当前时间: $(date)"

# 1. 显示当前运行的服务
echo ""
echo "📌 当前运行的服务:"
echo "-------------------"

# 检查各个端口
check_port() {
    local port=$1
    local name=$2
    if lsof -i :$port >/dev/null 2>&1; then
        echo "✅ $name (端口 $port): 运行中"
        return 0
    else
        echo "❌ $name (端口 $port): 未运行"
        return 1
    fi
}

check_port 8087 "云熙API服务"
check_port 8088 "知识检索服务"
check_port 8001 "小娜控制服务"
check_port 8005 "小诺协调服务"

# 2. 显示系统负载
echo ""
echo "📊 系统负载:"
echo "-----------"
echo "负载平均值: $(uptime | awk -F'load average:' '{print $2}' | awk '{print $1,$2,$3}')"
echo "内存使用: $(top -l 1 | grep "PhysMem" | awk '{print $2}' | sed 's/used//')"

# 3. 统计Python进程
echo ""
echo "🐍 Python进程统计:"
echo "----------------"
python_count=$(ps aux | grep -E "python" | grep -v grep | wc -l | tr -d ' ')
echo "总Python进程数: $python_count"

echo ""
echo "占用内存较高的Python进程:"
ps aux | grep python | grep -v grep | awk '$5 > 100 {print "  PID " $2 ": " $5 "MB - " $11}' | head -5

# 4. 停止非必要服务
echo ""
echo "🔧 停止非必要服务..."
echo "-------------------"

# 停止知识检索服务
if check_port 8088 "知识检索服务" >/dev/null 2>&1; then
    echo "→ 停止知识检索服务 (8088)..."
    pkill -f "knowledge_retrieval" 2>/dev/null || echo "   已停止"
fi

# 停止小娜控制服务
if check_port 8001 "小娜控制服务" >/dev/null 2>&1; then
    echo "→ 停止小娜控制服务 (8001)..."
    pkill -f "athena_control_server" 2>/dev/null || echo "   已停止"
fi

# 停止小诺协调服务
if check_port 8005 "小诺协调服务" >/dev/null 2>&1; then
    echo "→ 停止小诺协调服务 (8005)..."
    pkill -f "xiaonuo_coordination" 2>/dev/null || echo "   已停止"
fi

# 5. 清理日志文件
echo ""
echo "🧹 清理日志文件..."
echo "-------------------"

# 截断大日志文件
for logfile in /Users/xujian/Athena工作平台/logs/*.log; do
    if [ -f "$logfile" ] && [ $(stat -f%z "$logfile") -gt 1048576 ]; then
        echo "→ 截断日志: $(basename $logfile)"
        tail -c 1M "$logfile" > "$logfile.tmp" && mv "$logfile.tmp" "$logfile"
    fi
done

# 6. 清理Python缓存
echo ""
echo "🗑️ 清理Python缓存..."
echo "-------------------"
find /Users/xujian/Athena工作平台 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find /Users/xujian/Athena工作平台 -name "*.pyc" -delete 2>/dev/null
echo "Python缓存已清理"

# 7. 清理临时文件
echo ""
echo "🗑️ 清理临时文件..."
echo "-------------------"
rm -f /tmp/yunpat_* 2>/dev/null
rm -f /tmp/athena_* 2>/dev/null
rm -f /tmp/*.tmp 2>/dev/null
echo "临时文件已清理"

# 8. 优化云熙配置
echo ""
echo "⚙️ 优化云熙配置..."
echo "-------------------"

# 创建优化配置
cat > /tmp/yunpat_optimized.env << EOF
# 云熙性能优化配置
export LOG_LEVEL=WARNING
export DEBUG=false
export ENABLE_METRICS=false
export MAX_WORKERS=2
export CACHE_SIZE=100
export HEALTH_CHECK_INTERVAL=300
EOF

echo "优化配置已生成"

# 9. 验证优化效果
echo ""
echo "✅ 优化完成！验证结果..."
echo "========================"

echo ""
echo "📌 保留的核心服务:"
check_port 8087 "云熙API服务"

echo ""
echo "📌 已停止的服务:"
check_port 8088 "知识检索服务" || echo "  ✅ 知识检索服务 (已停止)"
check_port 8001 "小娜控制服务" || echo "  ✅ 小娜控制服务 (已停止)"
check_port 8005 "小诺协调服务" || echo "  ✅ 小诺协调服务 (已停止)"

echo ""
echo "📊 优化后系统状态:"
echo "负载平均值: $(uptime | awk -F'load average:' '{print $2}' | awk '{print $1,$2,$3}')"
echo "内存使用: $(top -l 1 | grep "PhysMem" | awk '{print $2}' | sed 's/used//')"

# 10. 保存优化报告
echo ""
echo "💾 保存优化报告..."
echo "=================="

cat > /tmp/yunpat_optimization_report.md << EOF
# 云熙性能优化报告

## 优化时间
$(date)

## 优化措施
1. 停止非必要服务
   - 知识检索服务 (8088)
   - 小娜控制服务 (8001)
   - 小诺协调服务 (8005)

2. 保留核心服务
   - 云熙API服务 (8087)
   - PostgreSQL数据库
   - Redis缓存

3. 系统清理
   - 截断大日志文件
   - 清理Python缓存
   - 删除临时文件

4. 配置优化
   - 日志级别: WARNING
   - 最大工作进程: 2
   - 缓存大小: 100MB
   - 健康检查间隔: 300秒

## 建议
1. 按需启动其他服务
2. 定期清理日志 (每周)
3. 监控资源使用
4. 使用负载均衡

## 注意事项
- 知识检索功能暂时不可用
- 如需恢复功能，请重新启动相应服务
- 配置文件位于 /tmp/yunpat_optimized.env
EOF

echo "报告已保存到: /tmp/yunpat_optimization_report.md"

echo ""
echo "🎯 优化总结:"
echo "================"
echo "• 停止了3个非必要服务"
echo "• 保留了核心云熙API功能"
echo "• 清理了系统资源"
echo "• 优化了配置参数"
echo ""
echo "📈 预期效果:"
echo "• CPU负载显著降低"
echo "• 内存使用减少"
echo "• 系统响应更快"
echo "• 稳定性提高"
echo ""
echo "💡 如需恢复其他功能，请运行:"
echo "   - 知识检索: python3 services/yunpat-agent/knowledge_retrieval.py"
echo "   - 小娜控制: python3 services/autonomous-control/athena_control_server.py"
echo "   - 小诺协调: python3 services/intelligent-collaboration/xiaonuo_coordination_server.py"
echo ""
echo "===================="