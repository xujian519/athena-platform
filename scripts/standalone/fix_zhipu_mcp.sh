#!/bin/bash

# 智谱MCP服务配置修复脚本
# 解决 HTTP 401 认证失败问题

echo "========================================"
echo "🔧 智谱MCP服务配置修复工具"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查配置文件
CONFIG_FILE="$HOME/.config/opencode/opencode.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 当前问题诊断:${NC}"
echo "错误信息: HTTP 401 - Authentication Failed"
echo "原因: API密钥可能已失效或过期"
echo ""

# 显示当前密钥（脱敏）
CURRENT_KEY=$(cat "$CONFIG_FILE" | grep -o 'Z_AI_API_KEY": "[^"]*' | cut -d'"' -f4)
if [ -n "$CURRENT_KEY" ]; then
    MASKED_KEY="${CURRENT_KEY:0:8}...${CURRENT_KEY: -8}"
    echo -e "${YELLOW}当前API密钥: $MASKED_KEY${NC}"
    echo ""
fi

# 提示用户输入新密钥
echo -e "${GREEN}请按以下步骤获取新的API密钥:${NC}"
echo "1. 访问: https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys"
echo "2. 登录智谱开放平台账号"
echo "3. 创建或复制API密钥"
echo ""
echo -e "${YELLOW}注意: 请确保API密钥具有以下权限:${NC}"
echo "  - GLM-4V (视觉模型) - 用于图像分析"
echo "  - Web Search - 用于网络搜索"
echo "  - Web Reader - 用于网页读取"
echo ""

read -p "请输入新的智谱API密钥: " NEW_API_KEY

# 验证密钥格式
if [ -z "$NEW_API_KEY" ]; then
    echo -e "${RED}❌ 密钥不能为空${NC}"
    exit 1
fi

if [ ${#NEW_API_KEY} -lt 20 ]; then
    echo -e "${RED}❌ 密钥格式不正确（太短）${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ 密钥格式验证通过${NC}"
echo ""

# 备份原配置文件
BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ 已备份原配置文件到:${NC}"
echo "   $BACKUP_FILE"
echo ""

# 更新配置文件
echo -e "${YELLOW}🔄 正在更新配置...${NC}"

# 使用sed替换所有智谱API密钥
# 1. 更新 zai-mcp-server 的环境变量
sed -i.tmp "s/\"Z_AI_API_KEY\": \"[^\"]*\"/\"Z_AI_API_KEY\": \"$NEW_API_KEY\"/g" "$CONFIG_FILE"

# 2. 更新所有远程服务的 Authorization header
sed -i.tmp "s/\"Authorization\": \"Bearer [^\"]*\"/\"Authorization\": \"Bearer $NEW_API_KEY\"/g" "$CONFIG_FILE"

# 3. 更新 provider 配置中的 apiKey
sed -i.tmp "s/\"apiKey\": \"[^\"]*\\.0mYTotbC7aRmoNCe\"/\"apiKey\": \"$NEW_API_KEY\"/g" "$CONFIG_FILE"

# 清理临时文件
rm -f "${CONFIG_FILE}.tmp"

echo -e "${GREEN}✅ 配置文件已更新${NC}"
echo ""

# 验证更新
echo -e "${YELLOW}🔍 验证配置更新...${NC}"

# 检查4个智谱MCP服务
SERVICES=(
    "zai-mcp-server"
    "web-search-prime"
    "web-reader"
    "zread"
)

echo ""
echo -e "${GREEN}已更新的智谱MCP服务:${NC}"
for service in "${SERVICES[@]}"; do
    if grep -q "\"$service\"" "$CONFIG_FILE"; then
        echo -e "  ${GREEN}✅${NC} $service"
    else
        echo -e "  ${RED}❌${NC} $service (未找到)"
    fi
done

echo ""
echo -e "${GREEN}========================================"
echo "✅ 智谱MCP服务配置修复完成！"
echo "========================================${NC}"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo "1. 重启 Claude Code"
echo "2. 测试图像分析功能"
echo "3. 如果仍有问题，请检查:"
echo "   - API密钥是否有GLM-4V权限"
echo "   - 网络连接是否正常"
echo "   - 智谱服务是否在线"
echo ""
echo -e "${GREEN}测试命令:${NC}"
echo "  在Claude Code中输入: '分析这张图片的内容'"
echo ""

# 可选：测试API密钥
read -p "是否要测试API密钥是否有效? (y/n): " TEST_KEY
if [ "$TEST_KEY" = "y" ] || [ "$TEST_KEY" = "Y" ]; then
    echo ""
    echo -e "${YELLOW}🔍 测试API密钥...${NC}"

    # 测试智谱API
    RESPONSE=$(curl -s -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
        -H "Authorization: Bearer $NEW_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "model": "glm-4",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }' 2>&1)

    if echo "$RESPONSE" | grep -q '"choices"'; then
        echo -e "${GREEN}✅ API密钥有效！${NC}"
    elif echo "$RESPONSE" | grep -q 'Authentication Failed'; then
        echo -e "${RED}❌ API密钥无效或无权限${NC}"
        echo "请检查密钥是否正确"
    else
        echo -e "${YELLOW}⚠️ 无法验证密钥（可能是网络问题）${NC}"
        echo "响应: $RESPONSE"
    fi
fi

echo ""
echo -e "${GREEN}修复脚本执行完毕${NC}"
