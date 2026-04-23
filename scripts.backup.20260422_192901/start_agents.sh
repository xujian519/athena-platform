#!/bin/bash
# Athena智能体生产环境启动脚本
# 启动小诺和小娜智能体

set -e

PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

echo "======================================================"
echo "🚀 Athena智能体 - 生产环境启动"
echo "======================================================"
echo ""

# 设置环境变量
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export ENVIRONMENT=production
export DEBUG=false

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/data"

# 检查Gateway是否运行
if ! curl -s http://localhost:8005/health > /dev/null 2>&1; then
    echo "⚠️ Gateway未运行，正在启动..."
    cd gateway-unified
    ./gateway > "$PROJECT_ROOT/logs/gateway.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/data/gateway.pid"
    sleep 3
    cd "$PROJECT_ROOT"
    echo "✅ Gateway已启动"
else
    echo "✅ Gateway已运行"
fi

echo ""
echo "📟 启动感知模块..."

# 启动感知模块
cd core/perception
if [ -f "perception_manager.py" ]; then
    nohup python3 perception_manager.py > "$PROJECT_ROOT/logs/perception.log" 2>&1 &
    PERCEPTION_PID=$!
    echo $PERCEPTION_PID > "$PROJECT_ROOT/data/perception.pid"
    cd "$PROJECT_ROOT"
    echo "✅ 感知模块已启动 (PID: $PERCEPTION_PID)"
else
    cd "$PROJECT_ROOT"
    echo "⚠️  感知模块未找到，跳过"
fi

echo ""
echo "📟 启动小诺·双鱼公主..."

# 启动小诺智能体
cd services/intelligent-collaboration
nohup python3 xiaonuo_main.py > "$PROJECT_ROOT/logs/xiaonuo.log" 2>&1 &
XIAONUO_PID=$!
echo $XIAONUO_PID > "$PROJECT_ROOT/data/xiaonuo.pid"
cd "$PROJECT_ROOT"

echo "✅ 小诺已启动 (PID: $XIAONUO_PID)"

# 等待小诺启动
sleep 3

echo ""
echo "📟 启动小娜·天秤女神..."

# 创建小娜启动脚本
cat > "$PROJECT_ROOT/start_xiaona.py" << 'PYEOF'
#!/usr/bin/env python3
"""小娜专业版启动脚本"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.agents.xiaona_professional import XiaonaProfessionalAgent
from core.llm.unified_llm_manager import UnifiedLLMManager
from core.memory.tiered_memory_system import TieredMemorySystem

async def main():
    print("🌟 启动小娜·天秤女神...")
    
    # 初始化小娜
    agent = XiaonaProfessionalAgent(
        name="小娜",
        role="专利法律专家",
        version="4.1.0"
    )
    
    await agent.initialize()
    
    print("✅ 小娜已启动")
    print("📱 小娜服务就绪")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 小娜正在关闭...")
        await agent.shutdown()
        print("✅ 小娜已关闭")

if __name__ == "__main__":
    asyncio.run(main())
PYEOF

# 启动小娜
nohup python3 "$PROJECT_ROOT/start_xiaona.py" > "$PROJECT_ROOT/logs/xiaona.log" 2>&1 &
XIAONA_PID=$!
echo $XIAONA_PID > "$PROJECT_ROOT/data/xiaona.pid"

echo "✅ 小娜已启动 (PID: $XIAONA_PID)"

echo ""
echo "======================================================"
echo "🎉 智能体启动完成！"
echo "======================================================"
echo ""
echo "📱 服务状态:"
echo "  • Gateway:   http://localhost:8005"
echo "  • 感知模块:  ${PERCEPTION_PID:-未启动}"
echo "  • 小诺:      PID $XIAONUO_PID"
echo "  • 小娜:      PID $XIAONA_PID"
echo ""
echo "📋 日志文件:"
echo "  • Gateway:   tail -f $PROJECT_ROOT/logs/gateway.log"
echo "  • 感知模块:  tail -f $PROJECT_ROOT/logs/perception.log"
echo "  • 小诺:      tail -f $PROJECT_ROOT/logs/xiaonuo.log"
echo "  • 小娜:      tail -f $PROJECT_ROOT/logs/xiaona.log"
echo ""
echo "🛑 停止服务:"
if [ -n "$PERCEPTION_PID" ]; then
    echo "  • kill $PERCEPTION_PID  # 停止感知模块"
fi
echo "  • kill $XIAONUO_PID  # 停止小诺"
echo "  • kill $XIAONA_PID   # 停止小娜"
echo "  • kill \$(cat $PROJECT_ROOT/data/gateway.pid)  # 停止Gateway"
echo ""
