"""
Python WebSocket Agent适配器使用示例

演示如何使用Agent适配器与Gateway通信。
"""

import asyncio
import logging

from core.framework.agents.websocket_adapter import (
    WebSocketClient,
    create_xiaona_agent,
    create_xiaonuo_agent,
    create_yunxi_agent,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_1_basic_usage():
    """示例1: 基本使用 - 创建并启动小娜Agent"""
    print("\n=== 示例1: 基本使用 ===\n")

    # 创建并启动小娜Agent
    xiaona = await create_xiaona_agent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    print("✅ 小娜Agent已启动")
    print(f"   Session ID: {xiaona.session_id}")
    print(f"   连接状态: {xiaona.is_connected}")

    # 保持运行一段时间
    await asyncio.sleep(5)

    # 停止Agent
    await xiaona.stop()
    print("✅ 小娜Agent已停止")


async def example_2_direct_client():
    """示例2: 直接使用WebSocket客户端"""
    print("\n=== 示例2: 直接使用WebSocket客户端 ===\n")

    # 创建WebSocket客户端
    client = WebSocketClient(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    # 连接到Gateway
    if await client.connect():
        print("✅ 已连接到Gateway")
        print(f"   Session ID: {client.session_id}")

        # 发送任务
        task_id = await client.send_task(
            task_type="patent_analysis",
            target_agent="xiaona",
            parameters={
                "patent_id": "CN123456789A",
                "analysis_type": "creativity"
            }
        )
        print(f"✅ 任务已发送: {task_id}")

        # 发送查询
        query_id = await client.send_query(
            query_type="agent_status",
            parameters={}
        )
        print(f"✅ 查询已发送: {query_id}")

        # 断开连接
        await client.disconnect()
        print("✅ 已断开连接")


async def example_3_multiple_agents():
    """示例3: 多Agent协作"""
    print("\n=== 示例3: 多Agent协作 ===\n")

    # 创建多个Agent
    agents = []

    # 小娜 - 法律专家
    xiaona = await create_xiaona_agent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )
    agents.append(("小娜", xiaona))
    print("✅ 小娜Agent已启动")

    # 小诺 - 调度官
    xiaonuo = await create_xiaonuo_agent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )
    agents.append(("小诺", xiaonuo))
    print("✅ 小诺Agent已启动")

    # 云希 - IP管理
    yunxi = await create_yunxi_agent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )
    agents.append(("云希", yunxi))
    print("✅ 云希Agent已启动")

    # 保持运行
    await asyncio.sleep(5)

    # 停止所有Agent
    for name, agent in agents:
        await agent.stop()
        print(f"✅ {name}Agent已停止")


async def example_4_task_with_progress():
    """示例4: 带进度的任务处理"""
    print("\n=== 示例4: 带进度的任务处理 ===\n")

    # 创建小娜Agent
    xiaona = await create_xiaona_agent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    # 模拟进度回调
    async def progress_callback(progress, status, current_step="", total_steps=0):
        print(f"📊 进度: {progress}% - {status}")
        if current_step:
            print(f"   当前步骤: {current_step}/{total_steps}")

    # 处理专利分析任务
    result = await xiaona.handle_task(
        task_type="patent_analysis",
        parameters={
            "patent_id": "CN123456789A",
            "analysis_type": "comprehensive"
        },
        progress_callback=progress_callback
    )

    print("\n✅ 任务完成")
    print(f"   创造性评分: {result['creativity']['score']}")
    print(f"   创造性等级: {result['creativity']['level']}")

    await xiaona.stop()


async def example_5_custom_message_handler():
    """示例5: 自定义消息处理器"""
    print("\n=== 示例5: 自定义消息处理器 ===\n")

    # 创建WebSocket客户端
    client = WebSocketClient(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    # 注册自定义消息处理器
    def handle_progress(message):
        """处理进度消息"""
        progress = message.data.get("progress", 0)
        status = message.data.get("status", "")
        print(f"📊 收到进度更新: {progress}% - {status}")

    def handle_response(message):
        """处理响应消息"""
        success = message.data.get("success", False)
        result = message.data.get("result", {})
        print(f"✅ 收到响应: success={success}")
        print(f"   结果: {result}")

    def handle_error(message):
        """处理错误消息"""
        error_code = message.data.get("error_code", "")
        error_msg = message.data.get("error_msg", "")
        print(f"❌ 收到错误: [{error_code}] {error_msg}")

    # 注册处理器
    client.register_handler("progress", handle_progress)
    client.register_handler("response", handle_response)
    client.register_handler("error", handle_error)

    # 连接并发送任务
    if await client.connect():
        print("✅ 已连接到Gateway")

        # 发送任务
        await client.send_task(
            task_type="patent_search",
            target_agent="xiaona",
            parameters={
                "query": "人工智能",
                "limit": 5
            }
        )

        # 等待接收消息
        await asyncio.sleep(5)

        await client.disconnect()


async def main():
    """主函数"""
    print("=" * 60)
    print("Athena Gateway Python Agent适配器使用示例")
    print("=" * 60)

    try:
        # 运行示例
        await example_1_basic_usage()
        await example_2_direct_client()
        # await example_3_multiple_agents()  # 可选
        # await example_4_task_with_progress()  # 可选
        # await example_5_custom_message_handler()  # 可选

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被中断")

    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
