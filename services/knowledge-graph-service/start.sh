#!/bin/bash
# 知识图谱混合搜索服务启动脚本

echo "🚀 启动Athena知识图谱混合搜索服务"
echo "================================================="

# 检查依赖
echo "🔍 检查系统依赖..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi
echo "✅ Python3已安装"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3未安装"
    exit 1
fi
echo "✅ pip3已安装"

# 创建虚拟环境
VENV_PATH="./venv_kg_service"
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv $VENV_PATH
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source $VENV_PATH/bin/activate

# 安装依赖
echo "📦 安装Python依赖..."
pip install -r requirements.txt

# 检查服务配置
echo "⚙️ 检查服务配置..."

# 检查端口占用
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -tPID > /dev/null ; then
        echo "⚠️  端口 $1 已被占用"
        return 1
    else
        echo "✅ 端口 $1 可用"
        return 0
    fi
}

check_port 8080 || { echo "💡 请停止占用端口8080的服务或修改配置"; exit 1; }
check_port 6333 || { echo "💡 请确保Qdrant服务运行在端口6333"; exit 1; }
check_port 8182 || { echo "💡 请确保JanusGraph服务运行在端口8182"; exit 1; }

# 创建配置文件
echo "📝 创建配置文件..."

# 环境配置
cat > .env << EOF
# 服务配置
PORT=8080
HOST=0.0.0.0

# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333

# JanusGraph配置
JANUSGRAPH_HOST=localhost
JANUSGRAPH_PORT=8182

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/knowledge-graph.log
EOF

# 创建日志目录
mkdir -p logs

# 创建nginx配置
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream knowledge_graph_api {
        server knowledge-graph-api:8080;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://knowledge_graph_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /docs {
            proxy_pass http://knowledge_graph_api;
        }

        location /redoc {
            proxy_pass http://knowledge_graph_api;
        }
    }
}
EOF

# 启动方式选择
echo ""
echo "🎯 选择启动方式:"
echo "1) 直接启动 (开发模式)"
echo "2) Docker启动 (推荐生产环境)"
echo "3) 仅检查服务状态"
echo ""

read -p "请选择 (1-3): " choice

case $choice in
    1)
        echo "🔧 直接启动服务..."

        # 健止现有进程
        pkill -f "api_server.py" 2>/dev/null || true

        # 启动服务
        python api_server.py &

        sleep 3

        # 检查服务状态
        if curl -s http://localhost:8080/health > /dev/null; then
            echo "✅ 服务启动成功!"
            echo ""
            echo "📡 API地址: http://localhost:8080"
            echo "📖 API文档: http://localhost:8080/docs"
            echo "🔍 ReDoc文档: http://localhost:8080/redoc"
            echo ""
            echo "💡 使用Ctrl+C停止服务"
        else
            echo "❌ 服务启动失败，请检查日志"
            tail -20 logs/knowledge-graph.log
        fi
        ;;

    2)
        echo "🐳 Docker启动服务..."

        # 检查Docker
        if ! command -v docker &> /dev/null; then
            echo "❌ Docker未安装"
            exit 1
        fi

        # 启动服务
        docker-compose -f docker-compose.unified.yml --profile dev up -d

        echo "✅ Docker服务启动中..."
        echo ""
        echo "📡 API地址: http://localhost:8080"
        echo "📖 API文档: http://localhost:8080/docs"
        echo ""
        echo "💡 查看日志: docker-compose -f docker-compose.unified.yml --profile dev logs -f knowledge-graph-api"
        echo "💡 停止服务: docker-compose -f docker-compose.unified.yml --profile dev down"
        ;;

    3)
        echo "🔍 检查服务状态..."

        # 检查API服务
        if curl -s http://localhost:8080/health > /dev/null; then
            echo "✅ API服务运行正常"
            curl -s http://localhost:8080/health | python3 -m json.tool
        else
            echo "❌ API服务未运行"
        fi

        # 检查Qdrant
        if curl -s http://localhost:6333/health > /dev/null; then
            echo "✅ Qdrant服务运行正常"
        else
            echo "❌ Qdrant服务未运行"
        fi

        # 检查JanusGraph
        if nc -z localhost 8182; then
            echo "✅ JanusGraph服务运行正常"
        else
            echo "❌ JanusGraph服务未运行"
        fi
        ;;

    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 操作完成！"