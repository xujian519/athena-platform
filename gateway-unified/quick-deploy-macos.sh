#!/bin/bash
# Athena Gateway macOS 一键部署脚本
# 用途: 自动完成部署和安全检查
# 使用: sudo bash quick-deploy-macos.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Athena Gateway 一键部署 (macOS)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root权限运行此脚本${NC}"
    echo "使用: sudo bash quick-deploy-macos.sh"
    exit 1
fi

# 第一步: 执行部署
echo -e "${GREEN}[1/2] 执行部署...${NC}"
chmod +x "${SCRIPT_DIR}/deploy-macos.sh"
chmod +x "${SCRIPT_DIR}/uninstall-macos.sh"
chmod +x "${SCRIPT_DIR}/security-check-macos.sh"

"${SCRIPT_DIR}/deploy-macos.sh"

# 第二步: 运行安全检查
echo ""
echo -e "${GREEN}[2/2] 运行安全检查...${NC}"
chmod +x "${SCRIPT_DIR}/security-check-macos.sh"

"${SCRIPT_DIR}/security-check-macos.sh" || {
    echo ""
    echo -e "${RED}❌ 安全检查失败，请修复上述问题后重新部署${NC}"
    exit 1
}

# 显示状态
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}服务信息:${NC}"
echo "  安装目录: /usr/local/athena-gateway"
echo "  服务名称: com.athena.gateway"
echo "  HTTP端口: 8005"
echo "  HTTPS端口: 8443"
echo "  监控端口: 9090"
echo ""
echo -e "${YELLOW}管理命令:${NC}"
echo "  启动服务: sudo /usr/local/athena-gateway/start.sh"
echo "  停止服务: sudo /usr/local/athena-gateway/stop.sh"
echo "  查看状态: sudo /usr/local/athena-gateway/status.sh"
echo "  查看日志: sudo /usr/local/athena-gateway/logs.sh"
echo ""
echo -e "${YELLOW}launchd直接命令:${NC}"
echo "  启动: sudo launchctl load -w /Library/LaunchDaemons/com.athena.gateway.plist"
echo "  停止: sudo launchctl unload -w /Library/LaunchDaemons/com.athena.gateway.plist"
echo "  重启: sudo launchctl kickstart -k gui/$(id -u)/com.athena.gateway"
echo "  查看列表: launchctl list | grep com.athena.gateway"
echo ""
echo -e "${YELLOW}配置文件:${NC}"
echo "  主配置: sudo vi /usr/local/athena-gateway/config/config.yaml"
echo "  认证: sudo vi /usr/local/athena-gateway/config/auth.yaml"
echo "  环境: sudo vi /usr/local/athena-gateway/config/env"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo "  1. 修改认证密钥: sudo vi /usr/local/athena-gateway/config/auth.yaml"
echo "  2. 配置SSL证书（如需要）"
echo "  3. 配置防火墙规则"
echo "  4. 启动服务: sudo /usr/local/athena-gateway/start.sh"
echo "  5. 验证服务: curl http://localhost:8005/health"
echo ""
