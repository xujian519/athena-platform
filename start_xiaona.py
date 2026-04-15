#!/usr/bin/env python3
"""小娜专业版启动脚本 - 修复版"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.agents.xiaona_professional import XiaonaProfessionalAgent


async def main():
    print("🌟 启动小娜·天秤女神...")

    # 初始化小娜 - 不需要额外参数
    agent = XiaonaProfessionalAgent()

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
