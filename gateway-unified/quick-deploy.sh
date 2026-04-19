#!/bin/bash
# Athena Gateway 一键部署脚本
# 用途: 自动完成部署和安全检查
# 使用: sudo bash quick-deploy.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Athena Gateway 一键部署${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root权限运行此脚本${NC}"
    echo "使用: sudo bash quick-deploy.sh"
    exit 1
fi

# 第一步: 执行部署
echo -e "${GREEN}[1/3] 执行部署...${NC}"
chmod +x "${SCRIPT_DIR}/deploy.sh"
chmod +x "${SCRIPT_DIR}/uninstall.sh"
chmod +x "${SCRIPT_DIR}/security-check.sh"

"${SCRIPT_DIR}/deploy.sh"

# 第二步: 运行安全检查
echo ""
echo -e "${GREEN}[2/3] 运行安全检查...${NC}"
chmod +x "${SCRIPT_DIR}/security-check.sh"

"${SCRIPT_DIR}/security-check.sh" || {
    echo ""
    echo -e "${RED}❌ 安全检查失败，请修复上述问题后重新部署${NC}"
    exit 1
}

# 第三步: 启动服务
echo ""
echo -e "${GREEN}[3/3] 启动服务...${NC}"
APP_DIR="/opt/athena-gateway"

# 启动服务
systemctl start athena-gateway

# 等待启动
sleep 3

# 检查服务状态
if systemctl is-active --quiet athena-gateway; then
    echo -e "${GREEN}✅ 服务启动成功！${NC}"
else
    echo -e "${RED}❌ 服务启动失败，查看日志：${NC}"
    echo "journalctl -u athena-gateway -n 50"
    exit 1
fi

# 显示状态
systemctl status athena-gateway --no-pager

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}服务信息:${NC}"
echo "  状态: $(systemctl is-active athena-gateway)"
echo "  地址: http://localhost:8005"
echo "  健康检查: curl http://localhost:8005/health"
echo ""
echo -e "${YELLOW}管理命令:${NC}"
echo "  启动: systemctl start athena-gateway"
echo "  停止: systemctl stop athena-gateway"
echo "  重启: systemctl restart athena-gateway"
echo "  状态: systemctl status athena-gateway"
echo "  日志: journalctl -u athena-gateway -f"
echo ""
echo -e "${YELLOW}配置文件:${NC}"
echo "  主配置: vi ${APP_DIR}/config/config.yaml"
echo "  认证: vi ${APP_DIR}/config/auth.yaml"
echo "  环境变量: vi ${APP_DIR}/config/env"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo "  1. 修改认证密钥: vi ${APP_DIR}/config/auth.yaml"
echo "  2. 配置SSL证书 (生产环境必须)"
echo "  3. 配置防火墙和IP白名单"
echo "  4. 设置监控告警"
echo ""
