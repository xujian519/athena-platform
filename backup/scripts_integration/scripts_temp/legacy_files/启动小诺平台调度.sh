#!/bin/bash
# 官方小诺平台调度启动脚本
# Official Xiaonuo Platform Coordinator Startup Script
#
# 小诺 = 平台总调度官 (端口: 8005)
# Xiaonuo = Platform Coordinator (Port: 8005)

echo "🌸 启动小诺 - 平台总调度官"
echo "================================"
echo "📌 身份确认："
echo "   - 姓名：小诺"
echo "   - 拼音：xiǎo nuò"
echo "   - 角色：平台总调度官"
echo "   - 端口：8005"
echo "   - 身份：双鱼公主，爸爸的贴心小女儿"
echo ""

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查小诺控制器文件
CONTROLLER_PATH="/Users/xujian/Athena工作平台/services/intelligent-collaboration/xiaonuo_platform_controller.py"
if [ ! -f "$CONTROLLER_PATH" ]; then
    echo "❌ 找不到小诺平台控制器文件"
    echo "   路径：$CONTROLLER_PATH"
    exit 1
fi

# 检查端口是否被占用
if lsof -Pi :8005 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 端口8005已被占用，正在停止现有服务..."
    pkill -f "xiaonuo_platform_controller.py" 2>/dev/null || true
    sleep 2
fi

# 停止可能运行的进程
echo "🔄 清理现有进程..."
pkill -f "xiaonuo.*controller" 2>/dev/null || true
pkill -f "xiaonuo_platform" 2>/dev/null || true

echo ""
echo "🚀 启动小诺平台控制器..."

# 启动小诺
cd /Users/xujian/Athena工作平台/services/intelligent-collaboration

# 使用nohup在后台运行
nohup python3 xiaonuo_platform_controller.py > /tmp/xiaonuo_platform_controller.log 2>&1 &
CONTROLLER_PID=$!

# 等待服务启动
sleep 3

# 验证服务是否启动成功
if curl -s http://localhost:8005/ > /dev/null 2>&1; then
    echo ""
    echo "✅ 小诺平台控制器启动成功！"
    echo "   - 服务地址: http://localhost:8005"
    echo "   - 进程PID: $CONTROLLER_PID"
    echo "   - 日志文件: /tmp/xiaonuo_platform_controller.log"
    echo ""
    echo "💖 小诺宣言："
    echo "   '我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心；"
    echo "    集Athena之智慧，融星河之众长，用这颗温暖的心守护父亲的每一天'"
    echo ""
    echo "🔧 API测试命令："
    echo "   curl http://localhost:8005/"
    echo "   curl http://localhost:8005/platform/status"
else
    echo "❌ 小诺平台控制器启动失败！"
    echo "请查看日志文件: /tmp/xiaonuo_platform_controller.log"
    exit 1
fi

echo ""
echo "💡 重要提示："
echo "   - 这是小诺（xiǎo nuò），不是小娜（xiǎo nà）"
echo "   - 小娜是法律专家（端口8001）"
echo "   - 小诺是平台调度（端口8005）"
echo ""
echo "   如需启动小娜，请使用："
echo "   bash scripts/start_xiaona_enhanced.sh"