#!/usr/bin/env python3
"""
Canvas/Host UI系统演示

展示如何使用Canvas Host创建实时更新的UI界面。
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.canvas.canvas_host import (
    CanvasHost,
    UIComponentFactory,
    UIComponentType,
    UIComponent,
)
from datetime import datetime


async def demo_basic_usage():
    """演示基础使用"""
    print("\n" + "="*60)
    print("演示1: 基础使用")
    print("="*60)

    # 创建Canvas Host
    host = CanvasHost("demo_host")
    await host.start()

    # 创建Canvas
    await host.create_canvas("demo_canvas", "演示仪表板")
    print("✓ Canvas创建成功")

    # 添加文本组件
    text = UIComponentFactory.create_text_component(
        component_id="welcome_text",
        title="欢迎使用",
        text="这是Canvas/Host UI系统的演示！"
    )
    await host.add_component("demo_canvas", text)
    print("✓ 文本组件添加成功")

    # 添加进度条组件
    progress = UIComponentFactory.create_progress_component(
        component_id="demo_progress",
        title="演示进度",
        current=3,
        total=10
    )
    await host.add_component("demo_canvas", progress)
    print("✓ 进度条组件添加成功")

    # 添加指标组件
    metric = UIComponentFactory.create_metric_component(
        component_id="demo_metric",
        title="系统指标",
        metric_name="CPU使用率",
        value=45.6,
        unit="%"
    )
    await host.add_component("demo_canvas", metric)
    print("✓ 指标组件添加成功")

    # 添加图表组件
    chart_data = [
        {"x": "周一", "y": 120},
        {"x": "周二", "y": 200},
        {"x": "周三", "y": 150},
        {"x": "周四", "y": 80},
        {"x": "周五", "y": 70},
        {"x": "周六", "y": 110},
        {"x": "周日", "y": 130},
    ]
    chart = UIComponentFactory.create_chart_component(
        component_id="demo_chart",
        title="本周数据趋势",
        chart_type="line",
        data=chart_data
    )
    await host.add_component("demo_canvas", chart)
    print("✓ 图表组件添加成功")

    # 获取统计信息
    stats = host.get_statistics()
    print(f"\n📊 统计信息:")
    print(f"  - Canvas数量: {stats['total_canvases']}")
    print(f"  - 运行状态: {stats['running']}")

    # 获取Canvas中的所有组件
    components = await host.get_canvas_components("demo_canvas")
    print(f"\n🧩 组件列表 (共{len(components)}个):")
    for comp in components:
        print(f"  - {comp.component_id}: {comp.title} ({comp.component_type})")

    await host.stop()
    print("\n✓ 演示1完成\n")


async def demo_realtime_updates():
    """演示实时更新"""
    print("="*60)
    print("演示2: 实时更新")
    print("="*60)

    host = CanvasHost("realtime_demo")
    await host.start()

    await host.create_canvas("realtime_canvas", "实时更新演示")

    # 添加进度条
    progress = UIComponentFactory.create_progress_component(
        component_id="task_progress",
        title="任务进度",
        current=0,
        total=100
    )
    await host.add_component("realtime_canvas", progress)

    # 添加日志组件
    log_component = UIComponent(
        component_id="task_logs",
        component_type=UIComponentType.LOG,
        title="任务日志",
        data={"entries": []}
    )
    await host.add_component("realtime_canvas", log_component)

    # 模拟任务执行
    tasks = [
        "初始化系统",
        "加载数据",
        "处理分析",
        "生成报告",
        "完成"
    ]

    print("\n⏳ 开始执行任务...")
    for i, task in enumerate(tasks):
        # 更新进度
        progress_value = int((i + 1) / len(tasks) * 100)
        await host.update_component(
            "realtime_canvas",
            "task_progress",
            {"current": progress_value, "total": 100}
        )

        # 添加日志
        logs = log_component.data["entries"]
        logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": "INFO",
            "message": f"正在执行: {task}"
        })
        await host.update_component(
            "realtime_canvas",
            "task_logs",
            {"entries": logs}
        )

        print(f"  [{i+1}/{len(tasks)}] {task}")
        await asyncio.sleep(0.5)  # 模拟处理时间

    # 添加完成指标
    final_metric = UIComponentFactory.create_metric_component(
        component_id="completion_metric",
        title="执行结果",
        metric_name="完成度",
        value=100,
        unit="%"
    )
    await host.add_component("realtime_canvas", final_metric)

    print("\n✓ 所有任务完成！")

    await host.stop()
    print("\n✓ 演示2完成\n")


async def demo_patent_analysis_dashboard():
    """演示专利分析仪表板"""
    print("="*60)
    print("演示3: 专利分析仪表板")
    print("="*60)

    host = CanvasHost("patent_demo")
    await host.start()

    patent_id = "CN123456789A"
    canvas_id = f"patent_analysis_{patent_id}"

    await host.create_canvas(canvas_id, f"专利分析: {patent_id}")
    print(f"✓ 创建专利分析Canvas: {patent_id}")

    # 顶部指标卡片
    metrics = [
        ("相似度得分", "85.6%", "primary"),
        ("权利要求数", "10", "info"),
        ("引用文献", "23", "warning"),
        ("法律状态", "有效", "success"),
    ]

    print("\n📊 添加指标卡片:")
    for i, (title, value, mtype) in enumerate(metrics):
        metric = UIComponent(
            component_id=f"metric_{i}",
            component_type=UIComponentType.METRIC,
            title=title,
            data={
                "metric_name": title,
                "value": value,
                "type": mtype
            },
            position={"row": 0, "col": i}
        )
        await host.add_component(canvas_id, metric)
        print(f"  - {title}: {value}")

    # 相似度对比图表
    chart_data = {
        "labels": ["权利要求1", "权利要求2", "权利要求3", "权利要求4", "权利要求5"],
        "datasets": [{
            "label": "相似度得分",
            "data": [0.85, 0.72, 0.91, 0.68, 0.78],
            "color": "#4CAF50"
        }]
    }

    chart = UIComponentFactory.create_chart_component(
        component_id="similarity_chart",
        title="权利要求相似度分析",
        chart_type="bar",
        data=chart_data
    )
    chart.position = {"row": 1, "col": 0, "colspan": 4}
    await host.add_component(canvas_id, chart)
    print("\n✓ 添加相似度对比图表")

    # 分析结论
    conclusion = UIComponentFactory.create_text_component(
        component_id="conclusion_text",
        title="分析结论",
        text="该专利具有较高的创造性，权利要求1-3的相似度较高但未超出现有技术范围，建议进一步审查。"
    )
    conclusion.position = {"row": 2, "col": 0, "colspan": 4}
    await host.add_component(canvas_id, conclusion)
    print("✓ 添加分析结论")

    # 显示统计
    components = await host.get_canvas_components(canvas_id)
    print(f"\n📈 仪表板统计: {len(components)}个组件")

    await host.stop()
    print("\n✓ 演示3完成\n")


async def demo_websocket_subscription():
    """演示WebSocket订阅"""
    print("="*60)
    print("演示4: WebSocket订阅")
    print("="*60)

    # 模拟WebSocket客户端
    class MockWebSocketClient:
        def __init__(self, client_id: str):
            self.client_id = client_id
            self.received_messages = []

        async def send(self, message: str):
            """接收Canvas更新"""
            import json
            data = json.loads(message)
            self.received_messages.append(data)

            if data["type"] == "canvas_created":
                print(f"  📢 [{self.client_id}] Canvas创建: {data['canvas_id']}")
            elif data["type"] == "component_updated":
                print(f"  📢 [{self.client_id}] 组件更新: {data['component_id']}")
            elif data["type"] == "component_created":
                print(f"  📢 [{self.client_id}] 组件创建: {data['component_id']}")

    host = CanvasHost("websocket_demo")
    await host.start()

    # 创建两个WebSocket客户端
    client1 = MockWebSocketClient("client_001")
    client2 = MockWebSocketClient("client_002")

    # 订阅Canvas更新
    await host.subscribe("client_001", client1)
    await host.subscribe("client_002", client2)
    print("✓ 两个客户端已订阅\n")

    # 创建Canvas（会广播到订阅者）
    await host.create_canvas("broadcast_canvas", "广播测试")

    # 添加组件（会广播）
    component = UIComponentFactory.create_text_component(
        component_id="broadcast_text",
        title="广播消息",
        text="这条消息会发送给所有订阅者"
    )
    await host.add_component("broadcast_canvas", component)

    # 更新组件（会广播）
    await host.update_component(
        "broadcast_canvas",
        "broadcast_text",
        {"text": "消息已更新！所有订阅者都会收到通知。"}
    )

    # 显示客户端接收的消息
    print(f"\n📨 客户端1接收了 {len(client1.received_messages)} 条消息")
    print(f"📨 客户端2接收了 {len(client2.received_messages)} 条消息")

    # 取消订阅
    await host.unsubscribe("client_001")
    print("\n✓ 客户端1已取消订阅")

    # 再次更新（client1不会收到）
    await host.update_component(
        "broadcast_canvas",
        "broadcast_text",
        {"text": "这次只有client_002会收到"}
    )
    print(f"✓ 客户端1接收了 {len(client1.received_messages)} 条消息（无新增）")
    print(f"✓ 客户端2接收了 {len(client2.received_messages)} 条消息（+1条）")

    await host.stop()
    print("\n✓ 演示4完成\n")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("     Canvas/Host UI系统演示")
    print("="*60)

    try:
        # 运行所有演示
        await demo_basic_usage()
        await demo_realtime_updates()
        await demo_patent_analysis_dashboard()
        await demo_websocket_subscription()

        print("="*60)
        print("     所有演示完成！")
        print("="*60)
        print("\n💡 提示:")
        print("  - 查看 docs/guides/CANVAS_HOST_USAGE_GUIDE.md 了解更多")
        print("  - 运行 pytest tests/canvas/test_canvas_host.py 查看测试")
        print("  - 启动Gateway: cd gateway-unified && sudo bash quick-deploy-macos.sh")
        print()

    except Exception as e:
        print(f"\n❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
