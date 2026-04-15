#!/bin/bash

# DeepSeek API测试脚本
# 使用curl直接测试DeepSeek API连接

API_KEY="sk-7f0fa1165de249d0a30b62a2584bd4c5"
API_URL="https://api.deepseek.com/v1/chat/completions"

echo "🔍 测试DeepSeek API连接..."
echo "API地址: $API_URL"
echo ""

# 发送测试请求
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "deepseek-coder",
    "messages": [
      {
        "role": "user",
        "content": "请用Python写一个简单的Hello World程序，包含注释说明"
      }
    ],
    "max_tokens": 200,
    "temperature": 0.1
  }' \
  --connect-timeout 30 \
  --max-time 60

echo ""
echo ""
echo "✅ 测试完成"