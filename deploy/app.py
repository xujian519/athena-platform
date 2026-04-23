#!/usr/bin/env python3
"""
您的AI应用入口
Your AI Application Entry Point
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 导入按需启动系统
try:
    from ready_on_demand_system import ai_system
    print("✅ 按需启动AI系统导入成功")
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("   请确保 core/collaboration/ready_on_demand_system.py 存在")
    sys.exit(1)

async def main():
    """主应用"""
    print("🚀 您的AI应用启动")
    print("-" * 40)

    try:
        # 初始化系统
        print("📝 正在初始化AI系统...")
        await ai_system.initialize()

        # 显示欢迎信息
        welcome = await ai_system.chat("你好，请介绍一下系统功能")
        print(f"🤖 AI: {welcome}")

        # 示例：专利分析
        print("\n📜 示例：专利分析")
        patent_result = await ai_system.patent_analysis("请分析这个专利权利要求的质量")
        print(f"🤖 小娜: {patent_result[:100]}...")

        # 显示系统状态
        status = ai_system.get_status()
        print("\n📊 系统状态:")
        print(f"   运行智能体: {status['running_agents']}/{status['total_agents']}")
        print(f"   内存使用: {status['memory_usage_mb']} MB")
        print(f"   资源效率: {status['resource_efficiency']}")

        # 交互模式
        print("\n💬 进入交互模式 (输入 'exit' 退出)")
        while True:
            try:
                user_input = input("\n👤 您: ").strip()
                if user_input.lower() == 'exit':
                    print("👋 再见！")
                    break
                elif not user_input:
                    continue

                response = await ai_system.chat(user_input)
                print(f"🤖 AI: {response}")

            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except EOFError:
                print("\n👋 再见！")
                break

    except Exception as e:
        print(f"❌ 应用运行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
