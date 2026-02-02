#!/bin/bash

# Athena工作平台快速配置检查脚本
# Quick Configuration Check for Athena Work Platform

echo "⚙️ Athena工作平台 - 快速配置检查"
echo "=================================="

# 检查时间
echo "🕐 检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 配置文件目录
CONFIG_DIR="/Users/xujian/Athena工作平台/config"
DEV_CONFIG="$CONFIG_DIR/environments/development/config.yaml"
PROD_CONFIG="$CONFIG_DIR/environments/production/config.yaml"

# 检查配置文件存在性
echo "📁 配置文件检查:"
if [ -f "$DEV_CONFIG" ]; then
    echo "  ✅ 开发环境配置: $DEV_CONFIG"
    dev_size=$(stat -f%z "$DEV_CONFIG" 2>/dev/null || stat -c%s "$DEV_CONFIG" 2>/dev/null)
    echo "     文件大小: $dev_size bytes"
else
    echo "  ❌ 开发环境配置: 文件不存在"
fi

if [ -f "$PROD_CONFIG" ]; then
    echo "  ✅ 生产环境配置: $PROD_CONFIG"
    prod_size=$(stat -f%z "$PROD_CONFIG" 2>/dev/null || stat -c%s "$PROD_CONFIG" 2>/dev/null)
    echo "     文件大小: $prod_size bytes"
else
    echo "  ❌ 生产环境配置: 文件不存在"
fi

echo ""

# 检查环境变量
echo "🌍 环境变量检查:"

# 数据库环境变量
db_vars=("DATABASE_HOST" "DATABASE_PORT" "DATABASE_NAME" "DATABASE_USER" "DATABASE_PASSWORD")
echo "  🗄️ 数据库配置:"
for var in "${db_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "    ✅ $var: ${!var}"
    else
        echo "    ❌ $var: 未设置"
    fi
done

# Redis环境变量
redis_vars=("REDIS_HOST" "REDIS_PORT" "REDIS_PASSWORD")
echo "  💾 Redis配置:"
for var in "${redis_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "    ✅ $var: ${!var}"
    else
        echo "    ❌ $var: 未设置"
    fi
done

# 服务端口环境变量
port_vars=("ATHENA_PORT" "ATHENA_MEMORY_PORT" "XIAONUO_MEMORY_PORT")
echo "  🔌 服务端口:"
for var in "${port_vars[@]}"; do
    if [ -n "${!var}" ]; then
        echo "    ✅ $var: ${!var}"
    else
        echo "    ❌ $var: 未设置 (使用默认值)"
    fi
done

echo ""

# 检查当前运行的服务
echo "🏃 当前运行服务:"
if command -v lsof >/dev/null 2>&1; then
    ports=(8000 8008 8083 8010 8011)
    for port in "${ports[@]}"; do
        if lsof -i :$port >/dev/null 2>&1; then
            echo "  ✅ 端口 $port: 运行中"
        else
            echo "  ❌ 端口 $port: 未运行"
        fi
    done
else
    echo "  ⚠️ lsof 命令不可用，无法检查端口状态"
fi

echo ""

# 配置验证
echo "✅ 配置验证:"
if [ -f "/Users/xujian/Athena工作平台/scripts/system_operations/config_manager.py" ]; then
    echo "  🔍 运行配置验证..."
    python3 /Users/xujian/Athena工作平台/scripts/system_operations/config_manager.py --validate 2>/dev/null | grep -E "(✅|❌|📊)" || echo "  ⚠️ 配置验证工具执行失败"
else
    echo "  ❌ 配置管理工具不存在"
fi

echo ""

# 快速操作提示
echo "⚡ 快速操作:"
echo "  🔄 验证所有配置: python3 scripts/system_operations/config_manager.py --validate"
echo "  📊 比较环境配置: python3 scripts/system_operations/config_manager.py --compare development production"
echo "  📋 生成统一配置: python3 scripts/system_operations/config_manager.py --unified"
echo "  📄 配置摘要: python3 scripts/system_operations/config_manager.py --summary"

echo ""
echo "✅ 配置检查完成"