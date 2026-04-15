#!/bin/bash
# ArangoDB本地安装脚本 (macOS)

echo "🚀 开始本地安装ArangoDB..."

# 检查是否已安装
if command -v arangod &> /dev/null; then
    echo "✅ ArangoDB已安装"
    arangod --version
else
    echo "📦 通过Homebrew安装ArangoDB..."
    brew install arangodb

    if [ $? -eq 0 ]; then
        echo "✅ ArangoDB安装成功"
    else
        echo "❌ ArangoDB安装失败"
        exit 1
    fi
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p /Users/xujian/Athena工作平台/data/arangodb
mkdir -p /Users/xujian/Athena工作平台/data/arangodb/databases
mkdir -p /Users/xujian/Athena工作平台/data/arangodb/apps

# 启动ArangoDB
echo "🚀 启动ArangoDB服务..."
brew services start arangodb

# 等待服务启动
sleep 5

# 检查服务状态
if arangosh --server.endpoint http+tcp://127.0.0.1:8529 --server.username root --server.password "" \
   --javascript.execute-string "db._createDatabase('athena_kg')" 2>/dev/null; then
    echo "✅ 数据库创建成功"
else
    echo "ℹ️  数据库可能已存在"
fi

# 安装Python依赖
echo "📦 安装Python依赖..."
pip3 install python-arango

# 测试连接
echo "🔍 测试连接..."
python3 -c "
from arango import ArangoClient
client = ArangoClient('http://localhost:8529')
try:
    sys_db = client.db('_system', username='root', password='')
    if sys_db.has_database('athena_kg'):
        print('✅ 连接成功，数据库已创建')
    else:
        print('❌ 数据库创建失败')
except Exception as e:
    print(f'❌ 连接失败: {e}')
"

echo ""
echo "✅ ArangoDB本地安装完成！"
echo "📊 Web界面: http://localhost:8528"
echo "🔌 API端点: http://localhost:8529/_db/athena_kg/_admin/aardvark/index.html"