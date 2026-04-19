#!/bin/bash
###############################################################################
# 生产环境首次部署引导脚本
# Production Deployment Bootstrap
#
# 功能：首次部署时的准备工作
#   - 创建配置文件
#   - 生成密钥
#   - 初始化数据库
#   - 启动服务
#
# 使用: ./production/scripts/bootstrap.sh
#
# 作者: Athena AI系统
# 创建时间: 2026-04-18
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Athena平台生产环境首次部署引导"
echo "=========================================="
echo ""

# 1. 创建生产环境配置文件
echo "1. 创建生产环境配置..."
if [ ! -f "${PROJECT_ROOT}/.env.production" ]; then
    cp "${PROJECT_ROOT}/.env.production.template" "${PROJECT_ROOT}/.env.production"
    echo -e "${GREEN}✓${NC} 配置文件已创建: .env.production"
    echo -e "${YELLOW}⚠${NC} 请编辑 .env.production 文件，设置正确的配置值"
    echo ""
    read -p "是否现在编辑配置文件? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} "${PROJECT_ROOT}/.env.production"
    fi
else
    echo "配置文件已存在，跳过"
fi

# 2. 生成JWT密钥
echo ""
echo "2. 生成安全密钥..."
if ! grep -q "CHANGE_ME_SUPER_SECRET" "${PROJECT_ROOT}/.env.production" 2>/dev/null; then
    echo "JWT密钥已设置，跳过"
else
    JWT_SECRET=$(openssl rand -hex 32)
    sed -i.bak "s/CHANGE_ME_SUPER_SECRET_JWT_KEY/${JWT_SECRET}/" "${PROJECT_ROOT}/.env.production"
    echo -e "${GREEN}✓${NC} JWT密钥已生成"
fi

# 3. 生成数据库密码
echo ""
echo "3. 生成数据库密码..."
if grep -q "CHANGE_ME.*PASSWORD" "${PROJECT_ROOT}/.env.production" 2>/dev/null; then
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    NEO4J_PASSWORD=$(openssl rand -hex 16)

    sed -i "s/CHANGE_ME_PRODUCTION_PASSWORD/${POSTGRES_PASSWORD}/" "${PROJECT_ROOT}/.env.production"
    sed -i "s/CHANGE_ME_REDIS_PASSWORD/${REDIS_PASSWORD}/" "${PROJECT_ROOT}/.env.production"
    sed -i "s/CHANGE_ME_NEO4J_PASSWORD/${NEO4J_PASSWORD}/" "${PROJECT_ROOT}/.env.production"

    echo -e "${GREEN}✓${NC} 数据库密码已生成"
    echo ""
    echo -e "${YELLOW}⚠${NC} 重要：请保存以下密码信息："
    echo "  PostgreSQL: ${POSTGRES_PASSWORD}"
    echo "  Redis: ${REDIS_PASSWORD}"
    echo "  Neo4j: ${NEO4J_PASSWORD}"
    echo ""
    read -p "是否已保存密码? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "请保存密码后继续..."
        read -p "按回车继续..."
    fi
fi

# 4. 创建必要目录
echo ""
echo "4. 创建目录结构..."
mkdir -p "${PROJECT_ROOT}/logs/production"
mkdir -p "${PROJECT_ROOT}/data/production"
mkdir -p "${PROJECT_ROOT}/backups/production"
mkdir -p "${PROJECT_ROOT}/models"
echo -e "${GREEN}✓${NC} 目录结构已创建"

# 5. 设置权限
echo ""
echo "5. 设置文件权限..."
chmod +x "${PROJECT_ROOT}/production/scripts/deploy_production.sh"
chmod +x "${PROJECT_ROOT}/production/scripts/health_check.sh"
echo -e "${GREEN}✓${NC} 权限已设置"

# 6. 构建镜像
echo ""
echo "6. 构建Docker镜像..."
read -p "是否现在构建Docker镜像? (可能需要10-15分钟) (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "${PROJECT_ROOT}"
    docker build -f docker/Dockerfile.production -t athena-platform:latest .
    echo -e "${GREEN}✓${NC} 镜像构建完成"
fi

# 7. 启动服务
echo ""
echo "7. 启动服务..."
read -p "是否现在启动服务? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "${PROJECT_ROOT}"
    docker-compose -f docker-compose.production.yml up -d
    echo -e "${GREEN}✓${NC} 服务启动完成"
    echo ""
    echo "等待服务就绪..."
    sleep 15

    # 健康检查
    if "${PROJECT_ROOT}/production/scripts/health_check.sh"; then
        echo -e "${GREEN}✓${NC} 所有服务健康检查通过"
    else
        echo -e "${YELLOW}⚠${NC} 部分服务健康检查失败，请查看日志"
    fi
fi

# 8. 完成
echo ""
echo "=========================================="
echo -e "${GREEN}首次部署引导完成！${NC}"
echo "=========================================="
echo ""
echo "下一步操作："
echo "  1. 检查服务状态: docker-compose ps"
echo "  2. 查看日志: docker-compose logs -f"
echo "  3. 健康检查: ./production/scripts/health_check.sh"
echo "  4. 访问Grafana: http://localhost:3000"
echo ""
echo "配置文件位置："
echo "  - 环境配置: .env.production"
echo "  - Docker Compose: docker-compose.production.yml"
echo "  - 部署脚本: production/scripts/deploy_production.sh"
echo ""
