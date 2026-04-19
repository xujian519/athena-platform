#!/bin/bash
###############################################################################
# 查看生产环境服务状态
###############################################################################

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          生产环境服务状态                                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 检查执行引擎
echo "📊 执行引擎状态:"
if [ -f "production/pids/execution_engine.pid" ]; then
    PID=$(cat production/pids/execution_engine.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "  状态: ✅ 运行中"
        echo "  PID: $PID"
        echo "  运行时间: $(ps -p $PID -o etime= | tr -d ' ')"
        echo "  内存使用: $(ps -p $PID -o rss= | awk '{printf "%.1fMB", $1/1024}')"
        echo "  CPU使用: $(ps -p $PID -o %cpu=)%"
    else
        echo "  状态: ❌ PID文件存在但进程未运行"
        echo "  建议: 运行 bash production/scripts/stop.sh 清理"
    fi
else
    echo "  状态: ❌ 未启动"
    echo "  建议: 运行 bash production/scripts/deploy.sh 部署"
fi

echo ""
echo "📁 日志文件:"
if [ -f "production/logs/execution_engine.log" ]; then
    SIZE=$(du -h production/logs/execution_engine.log | cut -f1)
    LINES=$(wc -l < production/logs/execution_engine.log)
    echo "  执行引擎: $SIZE ($LINES 行)"
    echo "  最新日志:"
    tail -3 production/logs/execution_engine.log | sed 's/^/    /'
else
    echo "  执行引擎: (不存在)"
fi

echo ""
echo "📂 输出目录:"
if [ -d "production/output" ]; then
    FILES=$(find production/output -type f | wc -l)
    SIZE=$(du -sh production/output 2>/dev/null | cut -f1)
    echo "  文件数: $FILES"
    echo "  总大小: $SIZE"
else
    echo "  (不存在)"
fi

echo ""
echo "⚙️  配置文件:"
echo "  执行引擎: production/config/execution_config.json"
echo "  CAP02: production/config/cap02_config.json"

echo ""
echo "💾 备份目录:"
if [ -d "production/backups" ]; then
    BACKUPS=$(ls -1t production/backups | head -5)
    echo "  最近备份:"
    echo "$BACKUPS" | sed 's/^/    /'
else
    echo "  (无备份)"
fi
