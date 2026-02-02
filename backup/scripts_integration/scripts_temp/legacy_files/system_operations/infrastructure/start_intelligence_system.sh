#!/bin/bash
# Athena和小诺智能系统启动脚本

echo "🚀 启动Athena和小诺智能系统..."

# 设置Python路径
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 初始化智能引擎
python3 -c "
import asyncio
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.intent_engine import IntentRecognitionEngine
from core.tool_auto_executor import ToolAutoExecutionEngine, initialize_tool_executor

async def start_intelligence():
    print('🧠 初始化意图识别引擎...')
    intent_engine = IntentRecognitionEngine()

    print('🛠️ 初始化工具执行引擎...')
    await initialize_tool_executor()

    print('✅ 智能系统启动完成')
    print('🎯 Athena和小诺已准备就绪！')

asyncio.run(start_intelligence())
"

echo "🎉 启动完成！"
