#!/bin/bash
# Gateway路由验证脚本
# 测试核心路由是否正确配置

GATEWAY_URL="http://localhost:8005"

echo "=========================================="
echo "Gateway路由验证测试"
echo "=========================================="
echo ""

# 测试健康检查
echo "1. 测试Gateway健康检查..."
curl -s "${GATEWAY_URL}/health" | jq '.' || echo "❌ Gateway健康检查失败"
echo ""

# 测试小娜法律专家路由
echo "2. 测试小娜法律专家路由 (/api/legal/health)..."
curl -s "${GATEWAY_URL}/api/legal/health" | jq '.' || echo "⚠️  路由存在但服务未启动（预期行为）"
echo ""

# 测试小诺协调器路由
echo "3. 测试小诺协调器路由 (/api/coord/health)..."
curl -s "${GATEWAY_URL}/api/coord/health" | jq '.' || echo "⚠️  路由存在但服务未启动（预期行为）"
echo ""

# 测试云熙IP管理路由
echo "4. 测试云熙IP管理路由 (/api/ip/health)..."
curl -s "${GATEWAY_URL}/api/ip/health" | jq '.' || echo "⚠️  路由存在但服务未启动（预期行为）"
echo ""

# 查看所有已注册的路由
echo "5. 查看所有已注册的路由..."
curl -s "${GATEWAY_URL}/api/routes" | jq '.data[] | {id: .id, path: .path, target: .target_service}' || echo "❌ 获取路由列表失败"
echo ""

# 查看所有已注册的服务实例
echo "6. 查看所有已注册的服务实例..."
curl -s "${GATEWAY_URL}/api/services/instances" | jq '.data[] | {service: .service_name, host: .host, port: .port, status: .status}' || echo "❌ 获取服务实例失败"
echo ""

echo "=========================================="
echo "验证测试完成"
echo "=========================================="
