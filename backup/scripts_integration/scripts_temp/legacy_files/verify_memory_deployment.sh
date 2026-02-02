#!/bin/bash
# 验证记忆系统部署

PROJECT_ROOT="/Users/xujian/Athena工作平台"
MEMORY_SERVICE_PORT="8003"

echo "🔍 验证记忆系统部署..."

# 1. 检查配置文件
if [ -f "${PROJECT_ROOT}/config/memory_system_config.json" ]; then
    echo "✅ 配置文件存在"
else
    echo "❌ 配置文件不存在"
    exit 1
fi

# 2. 检查记忆系统服务
if curl -s http://localhost:${MEMORY_SERVICE_PORT}/api/health > /dev/null; then
    echo "✅ 记忆系统API服务运行正常"
else
    echo "❌ 记忆系统API服务未运行"
    echo "请执行: bash ${PROJECT_ROOT}/scripts/start_memory_service.sh"
fi

# 3. 检查数据库连接
if /opt/homebrew/Cellar/postgresql@17/17.7/bin/psql -h localhost -p 5438 -d memory_module -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ PostgreSQL连接正常"
    memory_count=$(/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql -h localhost -p 5438 -d memory_module -t -c "SELECT COUNT(*) FROM memory_items;")
    echo "   当前记忆数: ${memory_count//[[:space:]]/}"
else
    echo "❌ PostgreSQL连接失败"
fi

# 4. 检查Qdrant
if curl -s http://localhost:6333/health > /dev/null; then
    echo "✅ Qdrant服务正常"
else
    echo "❌ Qdrant服务未运行"
fi

echo "🎉 验证完成！"
