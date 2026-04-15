#!/bin/bash
# 存储系统快速状态查看脚本

echo "📊 Athena平台存储系统状态"
echo "============================"

# PostgreSQL
echo -e "\n🗄️ PostgreSQL数据库:"
if lsof -i :5432 | grep -q postgres; then
    echo "  ✅ 运行中 (端口5432)"
    # 检查数据库
    if psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw athena_kg; then
        echo "  ✅ athena_kg数据库存在"
    else
        echo "  ❌ athena_kg数据库不存在"
    fi
else
    echo "  ❌ 未运行"
fi

# Qdrant
echo -e "\n🔍 Qdrant向量数据库:"
if lsof -i :6333 | grep -q 6333; then
    echo "  ✅ 运行中 (端口6333)"
    # 尝试API测试
    if curl -s http://localhost:6333/ > /dev/null; then
        echo "  ✅ API响应正常"
    else
        echo "  ⚠️ API无响应"
    fi
else
    echo "  ❌ 未运行"
fi

# Redis
echo -e "\n💾 Redis缓存:"
if lsof -i :6379 | grep -q 6379; then
    echo "  ✅ 运行中 (端口6379)"
else
    echo "  ❌ 未运行"
fi

# 外部存储
echo -e "\n📁 外部存储:"
if [ -L "../external_storage" ]; then
    echo "  ✅ 已挂载"
else
    echo "  ❌ 未挂载"
fi

echo -e "\n💖 存储系统检查完成！"