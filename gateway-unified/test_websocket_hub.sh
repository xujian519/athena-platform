#!/bin/bash

# WebSocket Hub 测试脚本
# 用于测试Athena Gateway的WebSocket Hub功能

set -e

GATEWAY_URL="ws://localhost:8005/ws/hub"
SESSION_ID="test_session_$(date +%s)"

echo "🌸 Athena Gateway WebSocket Hub 测试"
echo "======================================"
echo ""
echo "📡 测试参数:"
echo "  - Gateway URL: $GATEWAY_URL"
echo "  - Session ID: $SESSION_ID"
echo ""

# 检查wscat是否安装
if ! command -v wscat &> /dev/null; then
    echo "❌ wscat未安装，请先安装:"
    echo "   npm install -g wscat"
    exit 1
fi

echo "✅ wscat已安装"
echo ""

# 测试1: 基本连接
echo "🧪 测试1: 基本连接测试"
echo "--------------------------------------"
timeout 5 wscat -c "$GATEWAY_URL?session_id=$SESSION_ID" <<EOF || true
{"type":"ping","session_id":"$SESSION_ID","timestamp":"$(date -u +%Y-%m-%dT%H:%M:%SZ)","payload":{}}
EOF
echo ""

# 测试2: 发送任务创建消息
echo "🧪 测试2: 发送任务创建消息"
echo "--------------------------------------"
TASK_ID="task_$(date +%s)"
timeout 5 wscat -c "$GATEWAY_URL?session_id=$SESSION_ID" <<EOF || true
{
  "type": "task_create",
  "session_id": "$SESSION_ID",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "payload": {
    "task_id": "$TASK_ID",
    "task_type": "patent_search",
    "user_input": "检索自动驾驶相关专利",
    "priority": "medium"
  }
}
EOF
echo ""

# 测试3: 检查Hub统计API
echo "🧪 测试3: 检查Hub统计API"
echo "--------------------------------------"
curl -s http://localhost:8005/api/hub/stats | python3 -m json.tool || echo "❌ 无法获取统计信息"
echo ""

echo "✅ 测试完成！"
echo ""
echo "📋 更多测试方法:"
echo "  1. 使用HTML测试页面: file://$PWD/test_websocket_hub.html"
echo "  2. 使用wscat交互式测试: wscat -c \"$GATEWAY_URL?session_id=$SESSION_ID\""
echo "  3. 查看Hub统计: curl http://localhost:8005/api/hub/stats"
