#!/bin/bash
# OpenTelemetry 追踪环境启动脚本
# 用于Athena平台的分布式追踪系统
#
# 使用方法:
#   ./scripts/start_tracing.sh
#   ./scripts/start_tracing.sh --verify  # 启动后自动验证

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Athena OpenTelemetry 追踪环境启动${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查Docker是否运行
echo -e "${YELLOW}🔍 检查Docker状态...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请先启动Docker${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker运行正常${NC}"
echo ""

# 检查配置文件
echo -e "${YELLOW}🔍 检查配置文件...${NC}"
CONFIG_FILES=(
    "docker-compose.tracing.yml"
    "config/otel-collector-config.yaml"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ 配置文件不存在: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ $file${NC}"
done
echo ""

# 检查端口占用
echo -e "${YELLOW}🔍 检查端口占用...${NC}"
PORTS=(4317 4318 13133 16686 14268 14250 6831 6832 9200 3001)
OCCUPIED=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        OCCUPIED+=($port)
        echo -e "${YELLOW}⚠️  端口 $port 已被占用${NC}"
    fi
done

if [ ${#OCCUPIED[@]} -gt 0 ]; then
    echo -e "${RED}❌ 以下端口已被占用: ${OCCUPIED[*]}${NC}"
    echo -e "${YELLOW}提示: 使用 'docker-compose -f docker-compose.tracing.yml ps' 检查现有服务${NC}"
    read -p "是否继续启动? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ 所有端口可用${NC}"
fi
echo ""

# 创建Grafana配置目录
echo -e "${YELLOW}📁 创建Grafana配置目录...${NC}"
mkdir -p config/grafana/provisioning/datasources
mkdir -p config/grafana/provisioning/dashboards
echo -e "${GREEN}✅ 目录创建完成${NC}"
echo ""

# 启动追踪服务
echo -e "${BLUE}🚀 启动OpenTelemetry追踪服务...${NC}"
docker-compose -f docker-compose.tracing.yml up -d
echo ""

# 等待服务就绪
echo -e "${YELLOW}⏳ 等待服务启动 (最多30秒)...${NC}"
MAX_WAIT=30
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    sleep 2
    WAITED=$((WAITED + 2))

    # 检查Collector
    if curl -s http://localhost:13133 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OTEL Collector 就绪${NC}"
        break
    fi

    if [ $WAITED -eq $MAX_WAIT ]; then
        echo -e "${YELLOW}⚠️  服务未完全就绪，请稍后手动验证${NC}"
    fi
done
echo ""

# 显示服务状态
echo -e "${BLUE}📊 服务状态:${NC}"
docker-compose -f docker-compose.tracing.yml ps
echo ""

# 显示访问地址
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ 追踪环境启动成功！${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "📋 服务访问地址:"
echo -e "   • Jaeger UI:       ${BLUE}http://localhost:16686${NC}"
echo -e "   • Grafana:         ${BLUE}http://localhost:3001${NC} (admin/admin)"
echo -e "   • Elasticsearch:   ${BLUE}http://localhost:9200${NC}"
echo ""
echo -e "📡 数据接收端点:"
echo -e "   • OTLP gRPC:       ${BLUE}localhost:4317${NC}"
echo -e "   • OTLP HTTP:       ${BLUE}localhost:4318${NC}"
echo -e "   • Jaeger gRPC:     ${BLUE}localhost:14250${NC}"
echo -e "   • Jaeger HTTP:     ${BLUE}localhost:14268${NC}"
echo ""
echo -e "🔧 管理命令:"
echo -e "   • 查看日志:        ${YELLOW}docker-compose -f docker-compose.tracing.yml logs -f${NC}"
echo -e "   • 停止服务:        ${YELLOW}./scripts/stop_tracing.sh${NC}"
echo -e "   • 验证服务:        ${YELLOW}./scripts/verify_tracing.sh${NC}"
echo ""

# 自动验证（如果指定了--verify参数）
if [[ "$1" == "--verify" ]]; then
    echo -e "${YELLOW}🔍 运行自动验证...${NC}"
    sleep 3
    ./scripts/verify_tracing.sh
fi
