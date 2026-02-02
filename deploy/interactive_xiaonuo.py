#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小诺交互式客户端
Interactive client for Xiaonuo system
"""

import asyncio
import sys
from ready_on_demand_system import ai_system

async def interactive_chat():
    """交互式聊天"""
    print("🤖 小诺交互式客户端已启动")
    print("=" * 50)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'status' 查看系统状态")
    print("输入 'help' 查看可用命令")
    print("=" * 50)

    await ai_system.initialize()

    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 您: ").strip()

            # 处理特殊命令
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 再见！")
                break

            elif user_input.lower() in ['status', '状态']:
                status = ai_system.get_status()
                print(f"\n📊 系统状态:")
                print(f"   运行智能体: {status['running_agents']}/{status['total_agents']}")
                print(f"   运行中: {', '.join(status['running_agent_names'])}")
                print(f"   内存使用: {status['memory_usage_mb']} MB")
                print(f"   总任务数: {status['total_tasks']}")
                print(f"   资源效率: {status['resource_efficiency']}")
                print(f"   节省内存: {status.get('memory_saved_mb', 0)} MB")
                continue

            elif user_input.lower() in ['help', '帮助']:
                print(f"\n📖 可用命令:")
                print(f"   普通对话 - 直接输入消息")
                print(f"   专利分析 - 输入包含'专利'、'权利要求'等关键词")
                print(f"   IP管理 - 输入包含'IP'、'案卷'、'查询'等关键词")
                print(f"   内容创作 - 输入包含'文章'、'写作'、'创作'等关键词")
                print(f"   status - 查看系统状态")
                print(f"   help - 显示帮助")
                print(f"   quit/exit - 退出")
                continue

            elif not user_input:
                continue

            # 发送消息并获取回复
            print("\n🤖 小诺正在思考...")
            response = await ai_system.chat(user_input)
            print(f"\n🤖 小诺: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(interactive_chat())