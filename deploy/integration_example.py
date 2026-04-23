#!/usr/bin/env python3
"""
项目集成示例
Project Integration Example

展示如何将按需启动AI系统集成到您的现有项目
"""

import asyncio

# 导入按需启动AI系统
from ready_on_demand_system import ai_system


class YourProject:
    """您的项目类"""

    def __init__(self):
        self.ai_initialized = False

    async def initialize_ai(self):
        """初始化AI系统"""
        if not self.ai_initialized:
            print("🚀 初始化AI系统...")
            await ai_system.initialize()
            self.ai_initialized = True
            print("✅ AI系统初始化完成")

    async def handle_user_request(self, user_message: str, user_id: str = "default"):
        """处理用户请求"""
        await self.initialize_ai()

        # 智能路由
        if "专利" in user_message or "权利要求" in user_message:
            # 专利相关 - 使用小娜
            result = await ai_system.patent_analysis(user_message)
            return {"agent": "小娜", "response": result}

        elif "案卷" in user_message or "查询" in user_message or "IP" in user_message:
            # IP管理 - 使用云熙
            result = await ai_system.ip_management(user_message)
            return {"agent": "云熙", "response": result}

        elif "写" in user_message or "文章" in user_message or "内容" in user_message:
            # 内容创作 - 使用小宸
            result = await ai_system.content_creation(user_message)
            return {"agent": "小宸", "response": result}

        else:
            # 通用对话 - 使用小诺
            result = await ai_system.chat(user_message)
            return {"agent": "小诺", "response": result}

    async def get_system_status(self):
        """获取系统状态"""
        if self.ai_initialized:
            return ai_system.get_status()
        return {"status": "not_initialized"}

# 集成使用示例
async def integration_demo():
    """集成演示"""
    print("🔗 项目集成演示")
    print("=" * 50)

    # 创建项目实例
    project = YourProject()

    # 处理各种用户请求
    test_requests = [
        "你好，介绍一下功能",
        "请分析这个专利的权利要求质量",
        "查询案卷CASE_001的状态",
        "写一篇关于AI技术的文章",
        "这个技术有创新性吗？"
    ]

    for i, request in enumerate(test_requests, 1):
        print(f"\n{i}. 处理请求: {request}")

        result = await project.handle_user_request(request)
        print(f"   🤖 {result['agent']}: {result['response'][:80]}...")

    # 显示系统状态
    status = await project.get_system_status()
    print("\n📊 系统状态:")
    print(f"   运行智能体: {status.get('running_agents', 'N/A')}")
    print(f"   内存使用: {status.get('memory_usage_mb', 'N/A')} MB")
    print(f"   处理任务: {status.get('total_tasks', 'N/A')}")

# 便捷函数
async def quick_ai_chat(message: str):
    """快速AI对话"""
    return await ai_system.chat(message)

async def quick_patent_analysis(patent_text: str):
    """快速专利分析"""
    return await ai_system.patent_analysis(patent_text)

if __name__ == "__main__":
    print("🎯 立即集成示例")
    print("=" * 50)
    print("1. 运行完整演示")
    print("2. 测试便捷函数")
    print("3. 查看集成代码")
    print()

    choice = input("请选择 (1-3): ").strip()

    if choice == "1":
        asyncio.run(integration_demo())
    elif choice == "2":
        asyncio.run(quick_ai_chat("你好，请介绍一下系统"))
    elif choice == "3":
        print("\n📝 集成代码示例:")
        print("=" * 30)
        print("""
# 简单集成
from ready_on_demand_system import ai_system

async def your_function():
    response = await ai_system.chat("您的消息")
    return response

# 高级集成
class YourApp:
    async def process(self, message):
        if "专利" in message:
            return await ai_system.patent_analysis(message)
        else:
            return await ai_system.chat(message)
        """)
    else:
        print("运行完整演示...")
        asyncio.run(integration_demo())
