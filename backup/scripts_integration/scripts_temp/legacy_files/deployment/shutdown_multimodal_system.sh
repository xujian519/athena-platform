#!/bin/bash
# Athena多模态文件系统停止脚本

echo "🛑 停止Athena多模态文件系统..."

PID_DIR="/tmp/athena_pids"

# 停止统一API
if [ -f "$PID_DIR/unified_multimodal_api.pid" ]; then
    kill $(cat "$PID_DIR/unified_multimodal_api.pid") 2>/dev/null || true
    rm -f "$PID_DIR/unified_multimodal_api.pid"
    echo "✅ 统一API服务已停止"
fi

# 停止GLM视觉服务
if [ -f "$PID_DIR/glm_vision.pid" ]; then
    kill $(cat "$PID_DIR/glm_vision.pid") 2>/dev/null || true
    rm -f "$PID_DIR/glm_vision.pid"
    echo "✅ GLM视觉服务已停止"
fi

echo "🎉 多模态文件系统已停止"
