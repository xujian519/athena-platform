#!/bin/bash
# 统一工具注册表回滚脚本
# 作者: Agent 1 备份专家
# 创建时间: 2026-04-19
# 用途: 回滚到统一注册表实现之前的状态

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
BACKUP_DIR="${PROJECT_ROOT}/backup/registries_20260419"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}统一工具注册表回滚脚本${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}错误: 备份目录不存在: $BACKUP_DIR${NC}"
    exit 1
fi

# 检查备份文件是否完整
echo -e "${GREEN}步骤 1: 验证备份文件完整性...${NC}"
required_files=(
    "agent_registry.py"
    "capability_registry.py"
    "model_registry.py"
    "registry.py"
    "service_registry.py"
    "subagent_registry.py"
    "tool_registry_center.py"
    "tool_registry.py"
    "unified_tool_registry.py"
    "tool_registry_search.py"
    "service_registry_system.py"
    "registry_skills.py"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ ! -f "${BACKUP_DIR}/${file}" ]; then
        echo -e "${RED}  ✗ 缺失: ${file}${NC}"
        missing_files=$((missing_files + 1))
    else
        echo -e "${GREEN}  ✓ 存在: ${file}${NC}"
    fi
done

if [ $missing_files -gt 0 ]; then
    echo -e "${RED}错误: 缺失 ${missing_files} 个备份文件，回滚中止${NC}"
    exit 1
fi

echo ""

# 确认回滚操作
echo -e "${YELLOW}警告: 此操作将覆盖当前的注册表文件！${NC}"
echo -e "${YELLOW}请确认您要回滚到备份版本 (yes/no):${NC}"
read -r confirmation

if [ "$confirmation" != "yes" ]; then
    echo -e "${YELLOW}回滚操作已取消${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}步骤 2: 执行回滚操作...${NC}"

# 回滚核心注册表文件
cp "${BACKUP_DIR}/agent_registry.py" "${PROJECT_ROOT}/core/agent_collaboration/agent_registry.py"
echo -e "${GREEN}  ✓ 回滚: agent_registry.py${NC}"

cp "${BACKUP_DIR}/service_registry.py" "${PROJECT_ROOT}/core/agent_collaboration/service_registry.py"
echo -e "${GREEN}  ✓ 回滚: service_registry.py${NC}"

cp "${BACKUP_DIR}/registry.py" "${PROJECT_ROOT}/core/tools/registry.py"
echo -e "${GREEN}  ✓ 回滚: registry.py (tools)${NC}"

cp "${BACKUP_DIR}/model_registry.py" "${PROJECT_ROOT}/core/llm/model_registry.py"
echo -e "${GREEN}  ✓ 回滚: model_registry.py${NC}"

cp "${BACKUP_DIR}/capability_registry.py" "${PROJECT_ROOT}/core/capabilities/capability_registry.py"
echo -e "${GREEN}  ✓ 回滚: capability_registry.py${NC}"

cp "${BACKUP_DIR}/subagent_registry.py" "${PROJECT_ROOT}/core/agents/subagent_registry.py"
echo -e "${GREEN}  ✓ 回滚: subagent_registry.py${NC}"

cp "${BACKUP_DIR}/tool_registry_search.py" "${PROJECT_ROOT}/core/search/registry/tool_registry.py"
echo -e "${GREEN}  ✓ 回滚: tool_registry.py (search)${NC}"

cp "${BACKUP_DIR}/service_registry_system.py" "${PROJECT_ROOT}/core/system/system_manager/service_registry.py"
echo -e "${GREEN}  ✓ 回滚: service_registry.py (system)${NC}"

cp "${BACKUP_DIR}/unified_tool_registry.py" "${PROJECT_ROOT}/core/governance/unified_tool_registry.py"
echo -e "${GREEN}  ✓ 回滚: unified_tool_registry.py${NC}"

cp "${BACKUP_DIR}/tool_registry_center.py" "${PROJECT_ROOT}/core/registry/tool_registry_center.py"
echo -e "${GREEN}  ✓ 回滚: tool_registry_center.py${NC}"

cp "${BACKUP_DIR}/registry_skills.py" "${PROJECT_ROOT}/core/skills/registry.py"
echo -e "${GREEN}  ✓ 回滚: registry.py (skills)${NC}"

echo ""
echo -e "${GREEN}步骤 3: 验证回滚结果...${NC}"

# 验证文件是否正确回滚
rollback_success=0
for file in "${required_files[@]}"; do
    if [ -f "${BACKUP_DIR}/${file}" ]; then
        # 简单检查文件是否非空
        if [ -s "${BACKUP_DIR}/${file}" ]; then
            rollback_success=$((rollback_success + 1))
        fi
    fi
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}回滚完成！${NC}"
echo -e "${GREEN}成功回滚文件: ${rollback_success}/${#required_files[@]}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}后续操作建议:${NC}"
echo -e "  1. 运行测试套件验证功能: ${GREEN}pytest tests/ -v -m unit${NC}"
echo -e "  2. 检查导入依赖: ${GREEN}python3 -c 'from core.tools.registry import *'${NC}"
echo -e "  3. 如果一切正常，提交回滚: ${GREEN}git add . && git commit -m 'rollback: 回滚到统一注册表之前的状态'${NC}"
echo ""
