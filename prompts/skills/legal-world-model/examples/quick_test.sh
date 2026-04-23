#!/bin/bash
# 法律世界模型技能快速测试脚本
# Quick Test Script for Legal World Model Skill

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== 法律世界模型技能测试 ==="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查服务状态
echo -e "${YELLOW}[1/4] 检查法律世界模型服务状态...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 服务运行中${NC}"
else
    echo -e "${RED}✗ 服务未启动${NC}"
    echo ""
    echo "启动提示:"
    echo "  python3 core/legal_qa/legal_world_qa_system.py"
    echo ""
    exit 1
fi

# 测试CLI帮助
echo ""
echo -e "${YELLOW}[2/4] 测试CLI工具...${NC}"
if python3 "$SCRIPT_DIR/scripts/legal_qa_cli.py" --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓ CLI工具可用${NC}"
else
    echo -e "${RED}✗ CLI工具异常${NC}"
    exit 1
fi

# 检查技能文件
echo ""
echo -e "${YELLOW}[3/4] 检查技能文件...${NC}"
SKILL_MD="$SCRIPT_DIR/SKILL.md"
if [ -f "$SKILL_MD" ]; then
    echo -e "${GREEN}✓ SKILL.md 存在${NC}"
    echo "  技能名称: $(grep '^name:' "$SKILL_MD" | cut -d: -f2)"
    echo "  版本号: $(grep '^version:' "$SKILL_MD" | cut -d: -f2)"
else
    echo -e "${RED}✗ SKILL.md 不存在${NC}"
    exit 1
fi

# 检查能力配置
echo ""
echo -e "${YELLOW}[4/4] 检查智能体能力配置...${NC}"
CAPABILITIES_JSON="$PROJECT_ROOT/data/identity_personas_storage/athena/athena_capabilities.json"
if [ -f "$CAPABILITIES_JSON" ]; then
    echo -e "${GREEN}✓ 能力配置文件存在${NC}"
    python3 -c "
import json
with open('$CAPABILITIES_JSON') as f:
    config = json.load(f)
    legal_world = config['capabilities']['legal_world_model']
    print(f\"  技能ID: {legal_world['id']}\")
    print(f\"  API地址: {legal_world['api_endpoint']}\")
    print(f\"  启用状态: {legal_world['enabled']}\")
    print(f\"\\n  已配置的智能体:\")
    for agent_name, agent_config in config['agent_mappings'].items():
        if 'legal_world_model' in agent_config.get('capabilities', []):
            print(f\"    - {agent_config['name']} ({agent_name})\")
" 2>&1
else
    echo -e "${YELLOW}⚠ 能力配置文件不存在 (首次运行)${NC}"
fi

echo ""
echo -e "${GREEN}=== 测试完成 ===${NC}"
echo ""
echo "下一步:"
echo "  1. 启动法律世界模型服务:"
echo "     python3 core/legal_qa/legal_world_qa_system.py"
echo ""
echo "  2. 使用CLI工具提问:"
echo "     python3 $SCRIPT_DIR/scripts/legal_qa_cli.py \"什么是专利侵权？\""
echo ""
echo "  3. 查看完整文档:"
echo "     cat $SCRIPT_DIR/README.md"
echo ""
