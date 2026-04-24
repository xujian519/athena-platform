#!/bin/bash
# OpenTelemetry 追踪环境停止脚本
# 停止并清理追踪服务
#
# 使用方法:
#   ./scripts/stop_tracing.sh          # 停止服务
#   ./scripts/stop_tracing.sh --clean  # 停止并删除数据卷

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Athena 追踪环境停止${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查是否有运行的服务
echo -e "${YELLOW}🔍 检查运行中的服务...${NC}"
RUNNING=$(docker-compose -f docker-compose.tracing.yml ps -q 2>/dev/null | wc -l)

if [ "$RUNNING" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  没有运行中的追踪服务${NC}"
    exit 0
fi

echo -e "发现 $RUNNING 个运行中的容器"
echo ""

# 停止服务
if [[ "$1" == "--clean" ]]; then
    echo -e "${RED}🗑️  停止并删除所有数据...${NC}"
    docker-compose -f docker-compose.tracing.yml down -v
    echo ""

    # 删除数据卷
    echo -e "${YELLOW}删除数据卷...${NC}"
    docker volume rm athena-tracing_es-data 2>/dev/null || true
    docker volume rm athena-tracing_grafana-data 2>/dev/null || true
    echo -e "${GREEN}✅ 数据卷已删除${NC}"
else
    echo -e "${YELLOW}🛑 停止服务...${NC}"
    docker-compose -f docker-compose.tracing.yml down
    echo -e "${GREEN}✅ 服务已停止${NC}"
fi
echo ""

# 检查端口是否释放
echo -e "${YELLOW}🔍 验证端口释放...${NC}"
PORTS=(4317 4318 13133 16686 14268 14250 6831 6832 9200 3001)
STILL_OCCUPIED=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        STILL_OCCUPIED+=($port)
    fi
done

if [ ${#STILL_OCCUPIED[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  以下端口仍被占用: ${STILL_OCCUPIED[*]}${NC}"
    echo -e "提示: 可能有其他服务正在使用这些端口"
else
    echo -e "${GREEN}✅ 所有端口已释放${NC}"
fi
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  ✅ 追踪环境已停止${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "重新启动: ${YELLOW}./scripts/start_tracing.sh${NC}"
