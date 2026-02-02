#!/bin/bash
# 集成记忆系统到平台

PROJECT_ROOT="/Users/xujian/Athena工作平台"

echo "🔄 集成记忆系统到平台..."

# 1. 更新智能体启动脚本
for agent in athena xiaona xiaonuo yunxi xiaochen; do
    agent_script="${PROJECT_ROOT}/scripts/start_${agent}.sh"
    if [ -f "$agent_script" ]; then
        # 在启动脚本中添加记忆系统初始化
        if ! grep -q "unified_memory" "$agent_script"; then
            sed -i '' '/python3/i\
# 初始化统一记忆系统\
export MEMORY_SYSTEM_CONFIG="'$PROJECT_ROOT'/config/memory_system_config.json"\
' "$agent_script"
        fi
        echo "✅ 更新 $agent 启动脚本"
    fi
done

# 2. 创建环境变量配置
cat > "${PROJECT_ROOT}/.env.memory" << EOL
# 记忆系统环境变量
MEMORY_SYSTEM_CONFIG=${PROJECT_ROOT}/config/memory_system_config.json
POSTGRES_HOST=localhost
POSTGRES_PORT=5438
POSTGRES_DB=memory_module
QDRANT_HOST=localhost
QDRANT_PORT=6333
KG_HOST=localhost
KG_PORT=8002
MEMORY_SERVICE_PORT=8003
EOL

echo "✅ 创建环境变量配置"

# 3. 更新主启动脚本
main_script="${PROJECT_ROOT}/start.sh"
if [ -f "$main_script" ]; then
    if ! grep -q "memory_service" "$main_script"; then
        # 在启动脚本中添加记忆系统服务
        sed -i '' '/# Start core services/a\
# 启动记忆系统服务\
echo "启动记忆系统服务..."\
bash "${PROJECT_ROOT}"/scripts/start_memory_service.sh &\
MEMORY_PID=$!\
echo "记忆系统服务 PID: $MEMORY_PID"\
' "$main_script"
    fi
    echo "✅ 更新主启动脚本"
fi

echo "🎉 记忆系统集成完成！"
