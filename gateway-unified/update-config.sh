#!/bin/bash
# Athena Gateway 配置更新脚本
# 用途: 安全地更新配置并重启服务

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

APP_DIR="/opt/athena-gateway"
SERVICE_NAME="athena-gateway"

# 检查参数
if [ $# -lt 1 ]; then
    echo "用法: $0 <config-file> [test]"
    echo ""
    echo "参数:"
    echo "  config-file  要部署的配置文件路径"
    echo "  test         测试模式，只验证不应用"
    echo ""
    echo "示例:"
    echo "  $0 config.yaml"
    echo "  $0 config.yaml test"
    exit 1
fi

CONFIG_FILE="$1"
TEST_MODE="${2:-}"

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}错误: 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi

# 备份当前配置
BACKUP_DIR="${APP_DIR}/backup/config-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  配置更新${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

echo -e "${GREEN}[1/5] 备份当前配置...${NC}"
if [ -f "${APP_DIR}/config/config.yaml" ]; then
    cp "${APP_DIR}/config/config.yaml" "$BACKUP_DIR/"
    echo -e "${GREEN}✓ 配置已备份到: $BACKUP_DIR${NC}"
else
    echo -e "${YELLOW}当前无配置文件${NC}"
fi

# 验证新配置
echo -e "${GREEN}[2/5] 验证新配置...${NC}"

# 检查YAML语法
if command -v yamllint &> /dev/null; then
    if yamllint "$CONFIG_FILE" 2>&1 | grep -q "error"; then
        echo -e "${RED}❌ YAML语法错误，请检查配置文件${NC}"
        yamllint "$CONFIG_FILE"
        exit 1
    fi
elif command -v python3 &> /dev/null; then
    python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null || {
        echo -e "${RED}❌ YAML语法错误，请检查配置文件${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✓ YAML语法验证通过${NC}"

# 复制新配置
echo -e "${GREEN}[3/5] 应用新配置...${NC}"

cp "$CONFIG_FILE" "${APP_DIR}/config/config.yaml.tmp"

# 验证配置文件
if grep -q "CHANGE-THIS" "${APP_DIR}/config/config.yaml"; then
    echo -e "${RED}❌ 检测到默认密钥，请修改后再部署！${NC}"
    rm -f "${APP_DIR}/config/config.yaml.tmp"
    exit 1
fi

mv "${APP_DIR}/config/config.yaml.tmp" "${APP_DIR}/config/config.yaml"

chown athena:athena "${APP_DIR}/config/config.yaml"
chmod 640 "${APP_DIR}/config/config.yaml"

echo -e "${GREEN}✓ 配置文件已更新${NC}"

# 测试模式
if [ "$TEST_MODE" = "test" ]; then
    echo ""
    echo -e "${YELLOW}[测试模式] 只验证配置，不应用${NC}"
    rm -f "${APP_DIR}/config/config.yaml"
    mv "${APP_DIR}/config/config.yaml" "${APP_DIR_DIR}/config/config.yaml"
    echo -e "${GREEN}✓ 配置验证通过，可以部署${NC}"
    exit 0
fi

# 重启服务
echo -e "${GREEN}[4/5] 重启服务...${NC}"

if systemctl is-active --quiet ${SERVICE_NAME}; then
    systemctl reload ${SERVICE_NAME} 2>/dev/null || systemctl restart ${SERVICE_NAME}
    echo -e "${GREEN}✓ 服务已重启${NC}"
else
    systemctl start ${SERVICE_NAME}
    echo -e "${GREEN}✓ 服务已启动${NC}"
fi

sleep 2

# 验证服务状态
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✅ 服务运行正常${NC}"
else
    echo -e "${RED}❌ 服务启动失败！${NC}"
    journalctl -n 50 --unit ${SERVICE_NAME}

    # 回滚配置
    if [ -f "$BACKUP_DIR/config.yaml" ]; then
        echo -e "${YELLOW}正在回滚配置...${NC}"
        cp "$BACKUP_DIR/config.yaml" "${APP_DIR}/config/config.yaml"
        systemctl restart ${SERVICE_NAME}
    fi

    exit 1
fi

echo -e "${GREEN}[5/5] 验证服务...${NC}"

# 健康检查
sleep 2
HEALTH_CHECK=$(curl -s http://localhost:8005/health 2>/dev/null || echo "")

if echo "$HEALTH_CHECK" | grep -q '"status":"UP"' || echo "$HEALTH_CHECK" | grep -q '"status": "UP"'; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  健康检查失败，请检查配置${NC}"
    echo "$HEALTH_CHECK"
fi

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  配置更新完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "备份位置: $BACKUP_DIR"
echo ""
echo -e "${YELLOW}如需回滚，使用:${NC}"
echo "  cp $BACKUP_DIR/config.yaml ${APP_DIR}/config/config.yaml"
echo "  systemctl restart ${SERVICE_NAME}"
echo ""
