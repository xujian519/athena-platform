#!/bin/bash
# Athena Gateway 健康检查脚本

GATEWAY_URL="http://127.0.0.1:8005"

echo "🔍 Athena Gateway 健康检查..."
echo ""

# 基本健康检查
echo -n "  基本健康: "
if curl -sf "$GATEWAY_URL/health" > /dev/null 2>&1; then
    echo "✅ 正常"
else
    echo "❌ 异常"
    exit 1
fi

# 就绪检查
echo -n "  就绪状态: "
if curl -sf "$GATEWAY_URL/ready" > /dev/null 2>&1; then
    echo "✅ 就绪"
else
    echo "⚠️  未就绪"
fi

# 存活检查
echo -n "  存活状态: "
if curl -sf "$GATEWAY_URL/live" > /dev/null 2>&1; then
    echo "✅ 存活"
else
    echo "❌ 不存活"
    exit 1
fi

# 指标检查
echo -n "  指标端点: "
if curl -sf "$GATEWAY_URL/metrics" > /dev/null 2>&1; then
    echo "✅ 可用"
else
    echo "⚠️  不可用"
fi

# 检查服务管理API
echo -n "  服务管理API: "
if curl -sf "$GATEWAY_URL/api/v1/services/instances" > /dev/null 2>&1; then
    echo "✅ 可用"
else
    echo "⚠️  不可用"
fi

echo ""
echo "✅ 所有检查通过"

# 显示基本信息
echo ""
echo "📊 运行状态:"
curl -s "$GATEWAY_URL/health" | head -5
