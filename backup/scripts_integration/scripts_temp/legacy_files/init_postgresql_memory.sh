#!/bin/bash
# 初始化PostgreSQL记忆系统数据库

echo "🗄️ 初始化PostgreSQL记忆系统数据库..."

# 设置路径
POSTGRES_HOME=/opt/homebrew/var/postgresql@17
DATA_DIR=~/postgres_memory_data
CONFIG_DIR=/Users/xujian/Athena工作平台/configs
PORT=5438

# 检查是否已有数据
if [ -f "$DATA_DIR/PG_VERSION" ]; then
    echo "⚠️ 数据目录已存在，跳过初始化"
else
    echo "📦 初始化新的PostgreSQL数据目录..."

    # 使用/opt/homebrew/Cellar/postgresql@17/17.7/bin/initdb初始化数据库
    /opt/homebrew/Cellar/postgresql@17/17.7/bin/initdb -D $DATA_DIR --encoding=UTF8 --locale=C

    # 复制配置文件
    cp $CONFIG_DIR/postgresql_memory.conf $DATA_DIR/

    # 创建pg_log目录
    mkdir -p $DATA_DIR/pg_log

    echo "✅ 数据库初始化完成"
fi

# 启动PostgreSQL（如果未运行）
if /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_isready -h localhost -p $PORT >/dev/null 2>&1; then
    echo "✅ PostgreSQL已在端口$PORT运行"
else
    echo "🚀 启动PostgreSQL在端口$PORT..."

    # 启动PostgreSQL
    /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_ctl -D $DATA_DIR -l $DATA_DIR/pg_log/startup.log start -o "-c port=$PORT"

    # 等待启动
    sleep 3

    # 检查是否成功
    if /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_isready -h localhost -p $PORT >/dev/null 2>&1; then
        echo "✅ PostgreSQL启动成功"
    else
        echo "❌ PostgreSQL启动失败"
        tail $DATA_DIR/pg_log/startup.log
        exit 1
    fi
fi

# 创建记忆系统数据库
echo "📝 创建记忆系统数据库..."
/opt/homebrew/Cellar/postgresql@17/17.7/bin/createdb -h localhost -p $PORT memory_module 2>/dev/null || echo "数据库已存在"

# 初始化记忆表结构
echo "🏗️ 初始化记忆表结构..."
/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql -h localhost -p $PORT -d memory_module -f scripts/memory/init_memory_tables.sql 2>/dev/null || echo "表可能已存在"

echo ""
echo "🎉 PostgreSQL记忆系统配置完成！"
echo "   - 端口: $PORT"
echo "   - 数据库: memory_module"
echo "   - 数据目录: $DATA_DIR"
echo ""
echo "📋 常用命令："
echo "   - 启动: /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_ctl -D $DATA_DIR -l $DATA_DIR/pg_log/startup.log start -o \"-c port=$PORT\""
echo "   - 停止: /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_ctl -D $DATA_DIR stop"
echo "   - 重启: /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_ctl -D $DATA_DIR restart -o \"-c port=$PORT\""
echo "   - 连接: /opt/homebrew/Cellar/postgresql@17/17.7/bin/psql -h localhost -p $PORT -d memory_module"