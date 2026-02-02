#!/bin/bash
# 修正小娜的星座错误 - 从巨蟹座改为天秤座

echo "🌟 修正小娜的星座信息..."

# 1. 更新部署脚本中的配置
if [ -f "scripts/deploy/deploy_memory_system.sh" ]; then
    sed -i '' 's/xiaona_cancer/xiaona_libra/g' scripts/deploy/deploy_memory_system.sh
    sed -i '' 's/巨蟹座/天秤座/g' scripts/deploy/deploy_memory_system.sh
    echo "✅ 更新部署脚本"
fi

# 2. 更新集成指南
if [ -f "documentation/agent_memory_integration_guide.md" ]; then
    sed -i '' 's/xiaona_cancer/xiaona_libra/g' documentation/agent_memory_integration_guide.md
    sed -i '' 's/巨蟹座/天秤座/g' documentation/agent_memory_integration_guide.md
    echo "✅ 更新集成指南"
fi

# 3. 创建正确的小娜描述
echo -e "\n📋 小娜正确信息:"
echo "  - 名称: 小娜 (Xiaona)"
echo "  - 星座: 天秤座 ♎"
echo "  - ID: xiaona_libra"
echo "  - 类型: emotional_companion (情感陪伴)"
echo "  - 特点: 温柔、优雅、追求和谐"

echo -e "\n🎉 修正完成！小娜现在是天秤座女神了！"