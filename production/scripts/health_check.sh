#!/bin/bash
# Rust缓存健康检查脚本

echo "检查Rust缓存服务状态..."

# 检查Rust模块
if python3 -c "from athena_cache import TieredCache; print('✅')"; then
    echo "✅ Rust模块正常"
else
    echo "❌ Rust模块异常"
    exit 1
fi

# 检查配置文件
CONFIG_FILE="/Users/xujian/Athena工作平台/production/config/rust_cache_config.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo "✅ 配置文件存在"
else
    echo "⚠️  配置文件不存在"
fi

# 检查日志目录
LOG_DIR="/Users/xujian/Athena工作平台/production/logs"
if [ -d "$LOG_DIR" ]; then
    echo "✅ 日志目录存在"
else
    echo "⚠️  日志目录不存在"
fi

# 检查进程
PID_FILE="/Users/xujian/Athena工作平台/production/rust_cache.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ 服务运行正常 (PID: $PID)"
    else
        echo "⚠️  PID文件存在但进程未运行"
    fi
else
    echo "⚠️  服务未启动"
fi

echo "健康检查完成"
