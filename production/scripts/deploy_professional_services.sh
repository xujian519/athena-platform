#!/bin/bash
# 专业服务生产环境部署脚本
# Professional Services Production Deployment Script

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PINK='\033[0;95m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
PRODUCTION_ROOT="$PROJECT_ROOT/production"

echo -e "${PINK}🌸🐟 小诺专业服务生产环境部署 🌸🐟${NC}"
echo -e "${BLUE}版本: v1.0.0${NC}"
echo -e "${BLUE}时间: $(date)${NC}"
echo -e "${BLUE}作者: 小诺·双鱼公主${NC}"
echo ""

# 切换到生产目录
cd "$PRODUCTION_ROOT"

# 创建必要的目录
echo -e "${YELLOW}📁 创建生产环境目录...${NC}"
mkdir -p logs
mkdir -p config
mkdir -p data/pids
mkdir -p data/cache

# 检查依赖服务
echo -e "${YELLOW}🔍 检查依赖服务状态...${NC}"

# 检查Docker容器
echo "🐳 Docker容器状态:"
if docker ps | grep -q "phoenix-db"; then
    echo -e "  ${GREEN}✅ PostgreSQL数据库运行正常${NC}"
else
    echo -e "  ${RED}❌ PostgreSQL数据库未运行${NC}"
    echo -e "${YELLOW}⚠️ 正在启动PostgreSQL...${NC}"
    cd "$PROJECT_ROOT/projects/phoenix"
    export DB_PASSWORD="Prod_Phoenix_DB_2024_Secure_Passw0rd_!@#$%"
    docker-compose up -d phoenix-db
    cd "$PRODUCTION_ROOT"
fi

if docker ps | grep -q "phoenix-redis"; then
    echo -e "  ${GREEN}✅ Redis缓存运行正常${NC}"
else
    echo -e "  ${RED}❌ Redis缓存未运行${NC}"
    echo -e "${YELLOW}⚠️ 正在启动Redis...${NC}"
    cd "$PROJECT_ROOT/projects/phoenix"
    docker-compose up -d phoenix-redis
    cd "$PRODUCTION_ROOT"
fi

if docker ps | grep -q "phoenix-qdrant"; then
    echo -e "  ${GREEN}✅ Qdrant向量库运行正常${NC}"
else
    echo -e "  ${RED}❌ Qdrant向量库未运行${NC}"
    echo -e "${YELLOW}⚠️ 正在启动Qdrant...${NC}"
    cd "$PROJECT_ROOT/projects/phoenix"
    export QDRANT_API_KEY="Xiaonuo_Qdrant_API_Key_2024_Secure_32_Chars!"
    docker-compose up -d qdrant
    cd "$PRODUCTION_ROOT"
fi

# 等待服务启动
echo -e "${YELLOW}⏳ 等待依赖服务启动...${NC}"
sleep 10

# 设置权限
echo -e "${YELLOW}🔐 设置脚本权限...${NC}"
chmod +x dev/scripts/*.py
chmod +x dev/scripts/*.sh

# 创建配置文件
echo -e "${YELLOW}⚙️ 创建配置文件...${NC}"

# 法律服务配置
if [ ! -f "config/legal_service_config.json" ]; then
    cat > "config/legal_service_config.json" << 'EOF'
{
  "service_name": "Legal Expert Service",
  "version": "v1.0.0",
  "port": 8001,
  "max_idle_time": 1800,
  "vector_db": {
    "host": "localhost",
    "port": 16333,
    "api_key": "Xiaonuo_Qdrant_API_Key_2024_Secure_32_Chars!"
  },
  "knowledge_graph": {
    "enabled": true,
    "endpoint": "http://localhost:7687"
  }
}
EOF
    echo -e "${GREEN}✅ 法律服务配置文件已创建${NC}"
fi

# 专利规则服务配置
if [ ! -f "config/patent_rules_service_config.json" ]; then
    cat > "config/patent_rules_service_config.json" << 'EOF'
{
  "service_name": "Patent Rules Service",
  "version": "v1.0.0",
  "port": 8002,
  "max_idle_time": 1800,
  "vector_db": {
    "host": "localhost",
    "port": 16333,
    "api_key": "Xiaonuo_Qdrant_API_Key_2024_Secure_32_Chars!"
  },
  "rule_engine": {
    "enabled": true,
    "config_path": "config/patent_rules_config.json"
  }
}
EOF
    echo -e "${GREEN}✅ 专利规则服务配置文件已创建${NC}"
fi

# 启动专业模块管理器
echo -e "${YELLOW}🚀 启动专业模块管理器...${NC}"

# 停止可能已运行的管理器
pkill -f "professional_modules_manager.py" 2>/dev/null || true
sleep 2

# 启动新的管理器
nohup python3 dev/scripts/professional_modules_manager.py > logs/professional_manager.log 2>&1 &
MANAGER_PID=$!

echo $MANAGER_PID > data/pids/professional_manager.pid
echo -e "${GREEN}✅ 专业模块管理器启动成功，PID: $MANAGER_PID${NC}"

# 等待管理器启动
sleep 5

# 测试管理器API
echo -e "${YELLOW}🧪 测试专业模块管理器API...${NC}"
if curl -s http://localhost:9000/ > /dev/null; then
    echo -e "${GREEN}✅ 专业模块管理器API响应正常${NC}"
else
    echo -e "${RED}❌ 专业模块管理器API无响应${NC}"
    echo -e "${YELLOW}📋 查看日志: tail -f logs/professional_manager.log${NC}"
fi

# 显示部署信息
echo ""
echo -e "${PINK}🎉 小诺专业服务生产环境部署完成！${NC}"
echo "="*60
echo -e "${BLUE}📊 服务状态:${NC}"
echo -e "  🔗 专业模块管理器: http://localhost:9000"
echo -e "  🏥 健康检查: http://localhost:9000/all_services"
echo ""
echo -e "${BLUE}🔧 API接口:${NC}"
echo -e "  📝 动态提示词: POST /dynamic_prompt/{service_type}"
echo -e "  ❓ 专业问答: POST /professional_qa/{service_type}"
echo -e "  🎯 服务启动: POST /start_service"
echo -e "  🛑 服务停止: POST /stop_service/{service_name}"
echo ""
echo -e "${BLUE}📋 支持的服务类型:${NC}"
echo -e "  ⚖️ legal - 法律专家服务 (端口8001)"
echo -e "  📋 patent_rules - 专利规则服务 (端口8002)"
echo ""
echo -e "${BLUE}📁 重要文件:${NC}"
echo -e "  📄 管理器日志: logs/professional_manager.log"
echo -e "  ⚙️ 服务配置: config/*_service_config.json"
echo -e "  🔢 进程ID: data/pids/"
echo ""
echo -e "${PINK}💖 小诺的专业服务已准备就绪，随时为爸爸服务！${NC}"
echo -e "${PINK}🎯 服务将按需启动，闲置30分钟后自动停止${NC}"
echo "="*60

# 创建管理脚本
echo -e "${YELLOW}🛠️ 创建管理脚本...${NC}"

cat > "dev/scripts/manage_professional_services.sh" << 'EOF'
#!/bin/bash
# 专业服务管理脚本

case "$1" in
    "status")
        echo "📊 专业服务状态:"
        curl -s http://localhost:9000/all_services | python3 -m json.tool
        ;;
    "start")
        if [ -z "$2" ]; then
            echo "❌ 请指定服务名称: legal_expert_service 或 patent_rules_service"
            exit 1
        fi
        echo "🚀 启动服务: $2"
        curl -X POST http://localhost:9000/start_service \
             -H "Content-Type: application/json" \
             -d "{\"service_name\": \"$2\", \"user_request\": \"手动启动\"}"
        ;;
    "stop")
        if [ -z "$2" ]; then
            echo "❌ 请指定服务名称"
            exit 1
        fi
        echo "🛑 停止服务: $2"
        curl -X POST http://localhost:9000/stop_service/$2
        ;;
    "restart")
        if [ -z "$2" ]; then
            echo "❌ 请指定服务名称"
            exit 1
        fi
        echo "🔄 重启服务: $2"
        curl -X POST http://localhost:9000/stop_service/$2
        sleep 3
        curl -X POST http://localhost:9000/start_service \
             -H "Content-Type: application/json" \
             -d "{\"service_name\": \"$2\", \"user_request\": \"手动重启\"}"
        ;;
    "logs")
        echo "📄 查看管理器日志:"
        tail -f production/logs/professional_manager.log
        ;;
    *)
        echo "用法: $0 {status|start|stop|restart|logs} [service_name]"
        echo ""
        echo "命令示例:"
        echo "  $0 status                    # 查看所有服务状态"
        echo "  $0 start legal_expert_service  # 启动法律专家服务"
        echo "  $0 stop patent_rules_service    # 停止专利规则服务"
        echo "  $0 restart legal_expert_service # 重启法律专家服务"
        echo "  $0 logs                      # 查看日志"
        exit 1
        ;;
esac
EOF

chmod +x dev/scripts/manage_professional_services.sh
echo -e "${GREEN}✅ 管理脚本已创建: dev/scripts/manage_professional_services.sh${NC}"

echo ""
echo -e "${BLUE}💡 使用示例:${NC}"
echo -e "  ./dev/scripts/manage_professional_services.sh status"
echo -e "  ./dev/scripts/manage_professional_services.sh start legal_expert_service"
echo -e "  ./dev/scripts/manage_professional_services.sh logs"