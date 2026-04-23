#!/bin/bash

# 最小化服务启动脚本
# 只启动必要的核心服务

echo "🚀 启动Athena最小化服务集..."

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查必要的系统服务
echo ""
echo "📋 检查基础服务..."

# 1. PostgreSQL
if pg_isready -q; then
    echo -e "${GREEN}✅ PostgreSQL: 运行中${NC}"
else
    echo -e "${RED}❌ PostgreSQL: 未运行${NC}"
    echo "启动PostgreSQL..."
    brew services start postgresql@17
fi

# 2. Redis
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis: 运行中${NC}"
else
    echo -e "${RED}❌ Redis: 未运行${NC}"
    echo "启动Redis..."
    brew services start redis
fi

# 清理残留进程
echo ""
echo "🧹 清理残留进程..."
pkill -f "api_service.py" 2>/dev/null
pkill -f "client_capability" 2>/dev/null
pkill -f "xiaonuo_memory" 2>/dev/null

# 显示当前状态
echo ""
echo "📊 当前服务状态："
echo "------------------------"

# 基础数据库服务
echo -e "\n${YELLOW}📦 基础服务：${NC}"
echo "  • PostgreSQL: $(pg_isready -q && echo "运行中" || echo "已停止")"
echo "  • Redis: $(redis-cli ping 2>/dev/null || echo "已停止")"

# 可选服务（根据需要启动）
echo -e "\n${YELLOW}⚡ 可选服务（按需启动）：${NC}"
echo ""
echo "1. YunPat核心服务（端口8087）"
echo "   用途：专利检索、基础API"
echo "   启动: cd services/yunpat-agent && python3 api_service.py"
echo ""
echo "2. 客户端能力服务（端口8090）"
echo "   用途：分布式AI任务调度"
echo "   启动: cd services/yunpat-agent/client_integration && python3 client_capability_service.py"
echo ""
echo "3. Qdrant向量数据库（端口6333）"
echo "   用途：语义搜索、向量检索"
echo "   启动: docker start qdrant"
echo ""

# 系统资源
echo -e "\n${YELLOW}💻 系统资源：${NC}"
echo "  • 负载: $(uptime | awk -F'load average:' '{print $2}')"
echo "  • 内存: $(top -l 1 | grep "PhysMem" | awk '{print $2}' | sed 's/used//')"
echo "  • 磁盘: $(df -h / | tail -1 | awk '{print $4}') 可用"

echo ""
echo -e "${GREEN}✅ 最小化服务配置完成！${NC}"
echo ""
echo "💡 提示："
echo "  - 只运行了必要的数据库服务"
echo "  - 其他服务按需启动，避免资源浪费"
echo "  - 如需完整功能，请运行上述可选服务"