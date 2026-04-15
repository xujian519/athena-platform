#!/bin/bash
# Athena Gateway 卸载脚本
# 用途: 从生产环境卸载网关
# 使用: sudo bash uninstall.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="athena-gateway"
APP_USER="athena"
APP_DIR="/opt/${APP_NAME}"
SERVICE_NAME="${APP_NAME}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Athena Gateway 卸载程序${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用root权限运行此脚本 (sudo ./uninstall.sh)${NC}"
    exit 1
fi

# 确认卸载
echo -e "${RED}警告: 此操作将卸载 Athena Gateway！${NC}"
echo -n "确定要继续吗? (yes/no): "
read -r response
if [ "$response" != "yes" ]; then
    echo "取消卸载"
    exit 0
fi

# 第一步: 停止服务
echo -e "${GREEN}[1/5] 停止服务...${NC}"

if systemctl is-active --quiet ${SERVICE_NAME}; then
    systemctl stop ${SERVICE_NAME}
    echo -e "${GREEN}✓ 服务已停止${NC}"
else
    echo -e "${YELLOW}服务未运行${NC}"
fi

# 第二步: 禁用服务
echo -e "${GREEN}[2/5] 禁用自动启动...${NC}"

if systemctl is-enabled ${SERVICE_NAME} 2>/dev/null; then
    systemctl disable ${SERVICE_NAME}
    echo -e "${GREEN}✓ 已禁用自动启动${NC}"
else
    echo -e "${YELLOW}服务未启用${NC}"
fi

# 第三步: 备份配置
echo -e "${GREEN}[3/5] 备份配置...${NC}"

BACKUP_DIR="/tmp/athena-gateway-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -d "$APP_DIR" ]; then
    cp -r "$APP_DIR/config" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$APP_DIR/certs" "$BACKUP_DIR/" 2>/dev/null || true
    echo -e "${GREEN}✓ 配置已备份到: $BACKUP_DIR${NC}"
fi

# 第四步: 删除应用文件
echo -e "${GREEN}[4/5] 删除应用文件...${NC}"

rm -rf "$APP_DIR"
echo -e "${GREEN}✓ 应用目录已删除${NC}"

# 第五步: 删除用户
echo -e "${GREEN}[5/5] 删除应用用户...${NC}"

if id "$APP_USER" &>/dev/null; then
    userdel "$APP_USER"
    echo -e "${GREEN}✓ 用户 ${APP_USER} 已删除${NC}"
else
    echo -e "${YELLOW}用户 ${APP_USER} 不存在${NC}"
fi

# 删除systemd服务文件
rm -f /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
echo -e "${GREEN}✓ 系统服务配置已删除${NC}"

# 删除logrotate配置
rm -f /etc/logrotate.d/${APP_NAME}
echo -e "${GREEN}✓ Logrotate配置已删除${NC}"

# 删除防火墙规则
if command -v ufw &> /dev/null; then
    ufw delete allow 8005/tcp 2>/dev/null || true
    ufw delete allow 8443/tcp 2>/dev/null || true
    ufw delete allow 9090/tcp 2>/dev/null || true
    echo -e "${GREEN}✓ UFW规则已删除${NC}"
fi

if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --remove-port=8005/tcp 2>/dev/null || true
    firewall-cmd --permanent --remove-port=8443/tcp 2>/dev/null || true
    firewall-cmd --permanent --remove-port=9090/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo -e "${GREEN}✓ firewalld规则已删除${NC}"
fi

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  卸载完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "备份位置: $BACKUP_DIR"
echo ""
