#!/bin/bash
# 启动所有智能体服务（带身份展示）
# Start All Agents with Identity Display

echo "🚀 启动Athena平台所有智能体..."
echo "================================"

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 1. 启动小诺（如果还没启动）
if ! curl -s http://localhost:8005/ > /dev/null 2>&1; then
    echo "🌸 启动小诺 - 平台总调度官..."
    cd services/intelligent-collaboration
    nohup python3 xiaonuo_platform_controller.py > /tmp/xiaonuo.log 2>&1 &
    echo "✅ 小诺启动中 (端口:8005)"
    cd ../..
else
    echo "✅ 小诺已在运行 (端口:8005)"
fi

# 2. 启动小娜
if ! curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "⚖️ 启动小娜 - 知识产权法律专家..."
    bash scripts/启动小娜法律专家.sh > /tmp/xiaona_startup.log 2>&1 &
    sleep 2
    echo "✅ 小娜启动中 (端口:8001)"
else
    echo "✅ 小娜已在运行 (端口:8001)"
fi

# 3. 启动小宸
echo "🏹 启动小宸 - 自媒体运营专家..."
cd services/xiaochen-media
nohup python3 xiaochen_media_api.py > /tmp/xiaochen.log 2>&1 &
echo "✅ 小宸启动中 (端口:8006)"
cd ../..

# 4. 启动云熙
echo "✨ 启动云熙 - IP管理专家..."
cd services/yunxi-ip
nohup python3 yunxi_ip_management_api.py > /tmp/yunxi.log 2>&1 &
echo "✅ 云熙启动中 (端口:8007)"
cd ../..

# 5. 启动记忆系统（如果还没启动）
if ! curl -s http://localhost:8003/api/health > /dev/null 2>&1; then
    echo "🧠 启动记忆系统..."
    bash scripts/start_complete_memory_system.sh > /tmp/memory_system.log 2>&1 &
    sleep 3
    echo "✅ 记忆系统启动中 (端口:8003)"
else
    echo "✅ 记忆系统已在运行 (端口:8003)"
fi

# 等待所有服务启动
echo ""
echo "⏳ 等待所有服务启动完成..."
sleep 5

# 检查所有服务状态
echo ""
echo "📊 智能体服务状态检查："
echo "============================"

# 小诺
if curl -s http://localhost:8005/ > /dev/null 2>&1; then
    echo "✅ 小诺 (8005) - 平台总调度官"
    curl -s http://localhost:8005/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   {d.get(\"message\", \"\")[:50]}')" 2>/dev/null
else
    echo "❌ 小诺 (8005) - 启动失败"
fi

# 小娜
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "✅ 小娜 (8001) - 知识产权法律专家"
    curl -s http://localhost:8001/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   {d.get(\"message\", \"\")[:50]}')" 2>/dev/null
else
    echo "❌ 小娜 (8001) - 启动失败"
fi

# 小宸
if curl -s http://localhost:8006/ > /dev/null 2>&1; then
    echo "✅ 小宸 (8006) - 自媒体运营专家"
    curl -s http://localhost:8006/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   {d.get(\"message\", \"\")[:50]}')" 2>/dev/null
else
    echo "❌ 小宸 (8006) - 启动失败"
fi

# 云熙
if curl -s http://localhost:8007/ > /dev/null 2>&1; then
    echo "✅ 云熙 (8007) - IP管理专家"
    curl -s http://localhost:8007/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   {d.get(\"message\", \"\")[:50]}')" 2>/dev/null
else
    echo "❌ 云熙 (8007) - 启动失败"
fi

# 记忆系统
if curl -s http://localhost:8003/api/health > /dev/null 2>&1; then
    echo "✅ 记忆系统 (8003) - 智能记忆管家"
    curl -s http://localhost:8003/ | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   {d.get(\"message\", \"\")[:50]}')" 2>/dev/null
else
    echo "❌ 记忆系统 (8003) - 启动失败"
fi

echo ""
echo "🎯 所有智能体身份展示功能已激活！"
echo ""
echo "💡 访问地址："
echo "   小诺: http://localhost:8005/"
echo "   小娜: http://localhost:8001/"
echo "   小宸: http://localhost:8006/"
echo "   云熙: http://localhost:8007/"
echo "   记忆系统: http://localhost:8003/"