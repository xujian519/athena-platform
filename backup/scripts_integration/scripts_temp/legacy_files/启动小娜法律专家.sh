#!/bin/bash
# 官方小娜法律专家启动脚本
# Official Xiaona Legal Expert Startup Script
#
# 小娜 = 知识产权法律专家 (端口: 8001)
# Xiaona = Intellectual Property Legal Expert (Port: 8001)

echo "⚖️ 启动小娜 - 知识产权法律专家"
echo "================================"
echo "📌 身份确认："
echo "   - 姓名：小娜"
echo "   - 拼音：xiǎo nà"
echo "   - 角色：知识产权法律专家"
echo "   - 端口：8001"
echo "   - 身份：天秤女神，专业法律顾问"
echo ""

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查小娜增强版服务文件
XIAONA_PATH="/Users/xujian/Athena工作平台/services/autonomous-control/xiaona_enhanced_integrated.py"
if [ ! -f "$XIAONA_PATH" ]; then
    echo "❌ 找不到小娜增强版服务文件，正在创建..."
    bash scripts/start_xiaona_enhanced.sh
    exit 0
fi

# 检查端口是否被占用
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ 端口8001已被占用，正在停止现有服务..."
    pkill -f "xiaona_enhanced" 2>/dev/null || true
    sleep 2
fi

echo "🚀 启动小娜法律专家..."

# 启动小娜
cd /Users/xujian/Athena工作平台/services/autonomous-control

# 使用nohup在后台运行
nohup python3 xiaona_enhanced_integrated.py > /tmp/xiaona_legal_expert.log 2>&1 &
XIAONA_PID=$!

# 等待服务启动
sleep 3

# 验证服务是否启动成功
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo ""
    echo "✅ 小娜法律专家启动成功！"
    echo "   - 服务地址: http://localhost:8001"
    echo "   - 进程PID: $XIAONA_PID"
    echo "   - 日志文件: /tmp/xiaona_legal_expert.log"
    echo ""
    echo "⚖️ 小娜专长："
    echo "   - 专利申请与保护"
    echo "   - 商标注册与维权"
    echo "   - 版权登记与纠纷"
    echo "   - 法律文书起草"
    echo ""
    echo "🔧 API测试命令："
    echo "   curl http://localhost:8001/"
    echo "   curl -X POST http://localhost:8001/api/v2/analyze/comprehensive \\"
    echo "        -H 'Content-Type: application/json' \\"
    echo "        -d '{\"text\": \"我的人工智能算法如何申请专利保护？\"}'"
else
    echo "❌ 小娜法律专家启动失败！"
    echo "请查看日志文件: /tmp/xiaona_legal_expert.log"
    exit 1
fi

echo ""
echo "💡 重要提示："
echo "   - 这是小娜（xiǎo nà），不是小诺（xiǎo nuò）"
echo "   - 小娜是法律专家（端口8001）"
echo "   - 小诺是平台调度（端口8005）"
echo ""
echo "   如需启动小诺，请使用："
echo "   bash scripts/启动小诺平台调度.sh"