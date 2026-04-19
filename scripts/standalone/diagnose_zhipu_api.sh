#!/bin/bash

# 智谱API密钥详细诊断脚本

echo "========================================"
echo "🔍 智谱API密钥详细诊断工具"
echo "========================================"
echo ""

API_KEY="2b4ab444ad814c5b9ae4b13be4beb887.coYRf2PKuIjkc1bn"

# 1. 检查API密钥格式
echo "📋 1. 检查API密钥格式"
echo "   密钥长度: ${#API_KEY} 字符"
echo "   密钥格式: 检查是否符合智谱格式..."

if [[ "$API_KEY" =~ ^[a-f0-9]{32}\.[A-Za-z0-9]{16}$ ]]; then
    echo "   ✅ 格式正确 (32字符.16字符格式)"
else
    echo "   ⚠️  格式可能不正确"
    echo "   标准格式: 32个十六进制字符.16个字符的ID"
fi

echo ""

# 2. 测试基础认证
echo "📋 2. 测试基础认证"
echo "   尝试调用智谱API..."

FULL_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }' \
  https://open.bigmodel.cn/api/paas/v4/chat/completions)

HTTP_CODE=$(echo "$FULL_RESPONSE" | grep "HTTP_CODE:" | cut -d':' -f2)
RESPONSE_BODY=$(echo "$FULL_RESPONSE" | grep -v "HTTP_CODE:")

echo "   HTTP状态码: $HTTP_CODE"

if [ "$HTTP_CODE" == "200" ]; then
    echo "   ✅ 认证成功"
else
    echo "   ❌ 认证失败"
    echo "   错误详情:"
    echo "$RESPONSE_BODY" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE_BODY"
fi

echo ""

# 3. 检查可能的问题
echo "📋 3. 可能的问题分析"
echo ""
echo "如果认证失败，可能的原因:"
echo "  1. ❌ API密钥已过期或被撤销"
echo "  2. ❌ API密钥没有激活相应的服务权限"
echo "  3. ❌ API密钥账户余额不足"
echo "  4. ❌ API密钥格式错误"
echo ""

# 4. 解决建议
echo "📋 4. 解决建议"
echo ""
echo "请按以下步骤获取有效的API密钥:"
echo ""
echo "  1️⃣ 访问智谱开放平台:"
echo "     https://open.bigmodel.cn/usercenter/proj-mgmt/apikeys"
echo ""
echo "  2️⃣ 登录您的账户"
echo ""
echo "  3️⃣ 检查现有API密钥或创建新密钥"
echo "     - 确保密钥状态为'启用'"
echo "     - 检查账户余额是否充足"
echo "     - 确认密钥具有以下权限:"
echo "       * GLM-4V (视觉模型)"
echo "       * GLM-4-Flash / GLM-4"
echo "       * Web Search API"
echo "       * Web Reader API"
echo ""
echo "  4️⃣ 复制新的API密钥并重新运行此脚本"
echo ""
echo "========================================"
echo "💡 提示"
echo "========================================"
echo ""
echo "如果您确认API密钥正确但仍失败，请:"
echo "  1. 检查智谱账户余额"
echo "  2. 联系智谱技术支持"
echo "  3. 查看智谱服务状态页面"
echo ""
