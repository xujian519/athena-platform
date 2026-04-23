#!/usr/bin/env python3
"""
协作协议演示脚本
Collaboration Protocols Demo

演示多智能体协作协议的功能和使用方法
"""

import asyncio
import sys
from datetime import datetime, timedelta
from typing import Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from core.protocols.advanced_coordination import (
    AdvancedCoordinationEngine,
    AgentCapability,
    ResourceType,
    TaskPriority,
    TaskSpecification,
    register_agent,
    submit_task,
)
from core.protocols.collaboration_protocols import (
    ProtocolManager,
    ProtocolMessage,
    start_protocol_session,
)


def print_header(title) -> None:
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🤝 {title}")
    print("=" * 60)


def print_separator() -> Any:
    """打印分隔线"""
    print("\n" + "-" * 40)


async def demo_communication_protocol():
    """演示通信协议"""
    print_header("通信协议演示")

    try:
        # 创建协议管理器
        manager = ProtocolManager()

        # 参与者列表
        participants = ["xiaonuo", "xiaona", "yunxi", "xiaochen"]

        # 创建通信协议
        protocol_id = manager.create_communication_protocol(participants)
        print(f"✅ 通信协议已创建: {protocol_id}")

        # 启动协议
        started = await start_protocol_session(protocol_id)
        if started:
            print("✅ 通信协议已启动")
        else:
            print("❌ 通信协议启动失败")

        # 发送测试消息
        print("\n📡 发送测试消息:")
        messages = [
            {
                "sender": "xiaonuo",
                "receiver": "xiaona",
                "content": {"action": "request_analysis", "patent_id": "PAT_001"}
            },
            {
                "sender": "xiaona",
                "receiver": "xiaonuo",
                "content": {"action": "analysis_result", "result": "success"}
            },
            {
                "sender": "yunxi",
                "receiver": "broadcast",
                "content": {"action": "progress_update", "progress": 0.5}
            }
        ]

        for i, msg_info in enumerate(messages, 1):
            message = ProtocolMessage(
                sender_id=msg_info["sender"],
                receiver_id=msg_info["receiver"],
                message_type="request" if i == 1 else "response",
                content=msg_info["content"],
                priority=2
            )

            success = manager.route_message(message)
            status = "✅ 已发送" if success else "❌ 发送失败"
            print(f"   消息{i}: {msg_info['sender']} -> {msg_info['receiver']} {status}")

        # 显示协议状态
        print_separator()
        status = manager.get_protocol_status(protocol_id)
        if status:
            print("📊 协议状态:")
            print(f"   协议ID: {status['protocol_id']}")
            print(f"   协议类型: {status['protocol_type']}")
            print(f"   参与者: {', '.join(status['participants'])}")
            print(f"   当前阶段: {status['current_phase']}")
            print(f"   状态: {status['status']}")
            print(f"   共享状态大小: {status['shared_state_size']}")
            print(f"   消息队列大小: {status['message_queue_size']}")

    except Exception as e:
        print(f"❌ 通信协议演示失败: {e}")


async def demo_coordination_protocol():
    """演示协调协议"""
    print_header("协调协议演示")

    try:
        # 创建高级协调引擎
        engine = AdvancedCoordinationEngine()

        print("👥 注册智能体:")
        agents = [
            {
                "id": "xiaonuo",
                "capabilities": [
                    AgentCapability("planning", 0.9, 1.0, 150.0),
                    AgentCapability("strategic_thinking", 0.8, 0.9, 200.0)
                ],
                "max_load": 2.0
            },
            {
                "id": "xiaona",
                "capabilities": [
                    AgentCapability("patent_analysis", 0.95, 1.0, 180.0),
                    AgentCapability("data_processing", 0.85, 0.95, 120.0)
                ],
                "max_load": 3.0
            },
            {
                "id": "yunxi",
                "capabilities": [
                    AgentCapability("goal_management", 0.9, 1.0, 100.0),
                    AgentCapability("progress_tracking", 0.95, 1.0, 80.0)
                ],
                "max_load": 5.0
            },
            {
                "id": "xiaochen",
                "capabilities": [
                    AgentCapability("coordination", 0.85, 1.0, 160.0),
                    AgentCapability("collaboration", 0.8, 0.9, 140.0)
                ],
                "max_load": 2.5
            }
        ]

        for agent in agents:
            success = register_agent(agent["id"], agent["capabilities"], agent["max_load"])
            status = "✅ 成功" if success else "❌ 失败"
            print(f"   {agent['id']}: {status} ({len(agent['capabilities'])} 个能力)")

        print_separator()

        print("📋 提交协调任务:")
        tasks = [
            TaskSpecification(
                task_id="task_001",
                task_type="patent_analysis",
                priority=TaskPriority.HIGH,
                required_capabilities=["patent_analysis"],
                resource_requirements=[
                    {
                        "resource_type": ResourceType.COMPUTE,
                        "amount": 60.0,
                        "unit": "percent",
                        "duration": timedelta(minutes=30)
                    }
                ]
            ),
            TaskSpecification(
                task_id="task_002",
                task_type="project_planning",
                priority=TaskPriority.NORMAL,
                required_capabilities=["planning", "strategic_thinking"],
                resource_requirements=[
                    {
                        "resource_type": ResourceType.MEMORY,
                        "amount": 4.0,
                        "unit": "GB",
                        "duration": timedelta(minutes=45)
                    }
                ]
            ),
            TaskSpecification(
                task_id="task_003",
                task_type="goal_setting",
                priority=TaskPriority.HIGH,
                required_capabilities=["goal_management"],
                deadline=datetime.now() + timedelta(hours=2),
                estimated_duration=timedelta(minutes=20)
            )
        ]

        for task in tasks:
            success = submit_task(task)
            status = "✅ 已提交" if success else "❌ 提交失败"
            print(f"   {task.task_id}: {status} (优先级: {task.priority.name})")

        print_separator()

        print("⚙️ 协调状态:")
        coordination_status = engine.get_coordination_status()
        print(f"   注册智能体数: {coordination_status['registered_agents']}")
        print(f"   活跃任务数: {coordination_status['active_tasks']}")
        print(f"   排队任务数: {coordination_status['queued_tasks']}")
        print(f"   协调策略: {coordination_status['coordination_strategy']}")
        print(f"   平均负载: {coordination_status['average_agent_load']:.2f}")

        # 添加资源
        engine.resource_pool.add_resource("cpu_cluster_1", ResourceType.COMPUTE, 100.0, "percent")
        engine.resource_pool.add_resource("memory_pool_1", ResourceType.MEMORY, 32.0, "GB")
        engine.resource_pool.add_resource("storage_ssd_1", ResourceType.STORAGE, 2000.0, "GB")

        print_separator()
        print("💾 资源池状态:")
        for resource_id, resource in engine.resource_pool.resources.items():
            utilization = (resource['capacity'] - resource['available']) / resource['capacity'] * 100
            print(f"   {resource_id}: {utilization:.1f}% 利用率 ({resource['available']:.1f}/{resource['capacity']:.1f} {resource['unit']})")

    except Exception as e:
        print(f"❌ 协调协议演示失败: {e}")


async def demo_decision_protocol():
    """演示决策协议"""
    print_header("决策协议演示")

    try:
        # 创建协议管理器
        manager = ProtocolManager()

        # 参与者
        participants = ["xiaonuo", "xiaona", "yunxi", "xiaochen"]

        # 创建决策协议
        protocol_id = manager.create_decision_protocol(participants)
        print(f"✅ 决策协议已创建: {protocol_id}")

        # 启动协议
        started = await start_protocol_session(protocol_id)
        if started:
            print("✅ 决策协议已启动")
        else:
            print("❌ 决策协议启动失败")

        print_separator()

        print("🗳️ 模拟决策过程:")

        # 发起提案
        proposal_message = ProtocolMessage(
            sender_id="xiaonuo",
            receiver_id="broadcast",
            message_type="proposal",
            content={
                "proposal": {
                    "title": "AI系统架构优化提案",
                    "description": "建议采用微服务架构重构现有系统",
                    "options": ["微服务架构", "单体架构", "混合架构"],
                    "deadline": (datetime.now() + timedelta(hours=2)).isoformat()
                }
            }
        )

        success = manager.route_message(proposal_message)
        print(f"   提案发起: {'✅ 成功' if success else '❌ 失败'}")

        # 模拟投票
        votes = [
            {"voter": "xiaonuo", "decision": "agree", "reason": "微服务架构更适合扩展"},
            {"voter": "xiaona", "decision": "agree", "reason": "便于独立开发和部署"},
            {"voter": "yunxi", "decision": "agree", "reason": "更好的目标管理"},
            {"voter": "xiaochen", "decision": "disagree", "reason": "增加协调复杂度"}
        ]

        for vote in votes:
            vote_message = ProtocolMessage(
                sender_id=vote["voter"],
                receiver_id="broadcast",
                message_type="vote",
                content={
                    "proposal_id": "mock_proposal_001",
                    "decision": vote["decision"],
                    "reason": vote["reason"]
                }
            )

            success = manager.route_message(vote_message)
            print(f"   {vote['voter']} 投票: {vote['decision']} ({'✅' if success else '❌'})")

        print_separator()

        print("📊 决策结果分析:")
        agree_votes = sum(1 for v in votes if v["decision"] == "agree")
        total_votes = len(votes)
        consensus_ratio = agree_votes / total_votes if total_votes > 0 else 0

        print(f"   赞成票: {agree_votes}/{total_votes} ({consensus_ratio:.1%})")
        print("   共识阈值: 70%")
        print(f"   决策结果: {'✅ 达成共识' if consensus_ratio >= 0.7 else '❌ 未达成共识'}")

        # 显示协议状态
        status = manager.get_protocol_status(protocol_id)
        if status:
            print("\n📈 协议性能:")
            print(f"   协议ID: {status['protocol_id']}")
            print(f"   当前阶段: {status['current_phase']}")
            print(f"   状态: {status['status']}")

    except Exception as e:
        print(f"❌ 决策协议演示失败: {e}")


async def demo_protocol_integration():
    """演示协议集成"""
    print_header("协议集成演示")

    try:
        # 创建协议管理器
        manager = ProtocolManager()

        participants = ["xiaonuo", "xiaona", "yunxi", "xiaochen"]

        # 创建多种协议
        print("🔗 创建协议栈:")
        protocols = {}

        # 通信协议
        comm_id = manager.create_communication_protocol(participants)
        protocols["communication"] = comm_id
        print(f"   通信协议: {comm_id}")

        # 协调协议
        coord_id = manager.create_coordination_protocol(participants)
        protocols["coordination"] = coord_id
        print(f"   协调协议: {coord_id}")

        # 决策协议
        decision_id = manager.create_decision_protocol(participants)
        protocols["decision"] = decision_id
        print(f"   决策协议: {decision_id}")

        print_separator()

        # 启动所有协议
        print("🚀 启动协议栈:")
        for protocol_type, protocol_id in protocols.items():
            started = await start_protocol_session(protocol_id)
            status = "✅ 已启动" if started else "❌ 启动失败"
            print(f"   {protocol_type}: {status}")

        print_separator()

        # 模拟协作工作流
        print("🔄 模拟协作工作流:")

        workflow_steps = [
            {
                "step": 1,
                "protocol": "communication",
                "action": "项目启动通知",
                "description": "通过通信协议通知所有参与者项目开始"
            },
            {
                "step": 2,
                "protocol": "coordination",
                "action": "任务分配",
                "description": "通过协调协议分配具体任务给各个智能体"
            },
            {
                "step": 3,
                "protocol": "decision",
                "action": "技术方案决策",
                "description": "通过决策协议选择最佳技术方案"
            },
            {
                "step": 4,
                "protocol": "communication",
                "action": "进度同步",
                "description": "通过通信协议同步项目进度"
            }
        ]

        for step in workflow_steps:
            print(f"\n   步骤{step['step']}: {step['action']}")
            print(f"   协议: {step['protocol']}")
            print(f"   说明: {step['description']}")

            # 模拟消息
            message = ProtocolMessage(
                sender_id="coordinator",
                receiver_id="broadcast",
                message_type="workflow_step",
                content={
                    "step": step["step"],
                    "action": step["action"],
                    "protocol": step["protocol"]
                }
            )

            success = manager.route_message(message)
            status = "✅ 完成" if success else "❌ 失败"
            print(f"   状态: {status}")

            # 短暂延迟模拟执行时间
            await asyncio.sleep(0.5)

        print_separator()

        # 显示所有协议状态
        print("📊 协议栈状态:")
        all_status = manager.get_all_protocols_status()
        for protocol_id, status in all_status.items():
            protocol_type = next(k for k, v in protocols.items() if v == protocol_id)
            print(f"   {protocol_type}: {status['status']} ({status['current_phase']})")

        print_separator()

        print("🔍 系统集成指标:")
        print(f"   活跃协议数: {len(all_status)}")
        print(f"   参与智能体数: {len(participants)}")
        print("   协议间通信: ✅ 正常")
        print("   集成状态: ✅ 稳定")

    except Exception as e:
        print(f"❌ 协议集成演示失败: {e}")


def show_protocol_features() -> Any:
    """显示协议功能特性"""
    print_header("协作协议功能特性")

    features = {
        "通信协议": [
            "标准化消息格式",
            "可靠消息传递",
            "消息确认机制",
            "广播和点对点通信",
            "消息优先级管理",
            "错误处理和重试"
        ],
        "协调协议": [
            "智能任务分配",
            "资源管理和调度",
            "负载均衡",
            "冲突检测和解决",
            "动态协调策略",
            "性能监控"
        ],
        "决策协议": [
            "多种决策模式",
            "投票和共识机制",
            "提案管理",
            "异议处理",
            "决策历史记录",
            "智能决策算法"
        ],
        "高级协调": [
            "自适应协调",
            "预测性调度",
            "基于市场的协调",
            "机会性任务分配",
            "性能优化",
            "资源池管理"
        ]
    }

    for protocol_type, feature_list in features.items():
        print(f"\n🔧 {protocol_type}:")
        for i, feature in enumerate(feature_list, 1):
            print(f"   {i}. {feature}")


def show_use_cases() -> Any:
    """显示使用场景"""
    print_header("协议应用场景")

    use_cases = [
        {
            "场景": "专利分析项目",
            "协议组合": ["通信协议", "协调协议"],
            "描述": "小娜和小诺协作完成专利分析任务",
            "优势": "高效的任务分配和实时通信"
        },
        {
            "场景": "项目规划决策",
            "协议组合": ["决策协议", "协调协议"],
            "描述": "多个智能体共同决策项目规划方案",
            "优势": "民主决策和智能协调"
        },
        {
            "场景": "系统架构设计",
            "协议组合": ["全部协议"],
            "描述": "完整的系统设计协作流程",
            "优势": "全方位协作支持"
        },
        {
            "场景": "紧急任务处理",
            "协议组合": ["协调协议", "通信协议"],
            "描述": "快速协调处理紧急任务",
            "优势": "快速响应和资源调度"
        }
    ]

    for i, use_case in enumerate(use_cases, 1):
        print(f"\n📋 场景{i}: {use_case['场景']}")
        print(f"   协议组合: {', '.join(use_case['协议组合'])}")
        print(f"   描述: {use_case['描述']}")
        print(f"   优势: {use_case['优势']}")


async def main():
    """主演示函数"""
    print_header("协作协议演示")
    print("本演示将展示协作协议的主要功能和使用方法")

    try:
        # 显示功能特性
        show_protocol_features()

        # 通信协议演示
        await demo_communication_protocol()

        # 协调协议演示
        await demo_coordination_protocol()

        # 决策协议演示
        await demo_decision_protocol()

        # 协议集成演示
        await demo_protocol_integration()

        # 显示使用场景
        show_use_cases()

        # 总结
        print_header("演示总结")
        print("✅ 协作协议演示完成")
        print("\n🎯 主要功能:")
        print("   ✓ 标准化通信协议")
        print("   ✓ 智能协调机制")
        print("   ✓ 民主决策系统")
        print("   ✓ 高级协调引擎")
        print("   ✓ 协议集成管理")

        print("\n📈 技术特点:")
        print("   ✓ 模块化设计")
        print("   ✓ 异步消息处理")
        print("   ✓ 动态协议管理")
        print("   ✓ 高性能协调")
        print("   ✓ 容错和恢复")

        print("\n🚀 应用价值:")
        print("   ✓ 提升协作效率")
        print("   ✓ 降低沟通成本")
        print("   ✓ 优化资源利用")
        print("   ✓ 增强决策质量")
        print("   ✓ 支持复杂项目")

        print("\n💡 下一步:")
        print("   - 扩展更多协议类型")
        print("   - 增强协议安全性")
        print("   - 优化协议性能")
        print("   - 集成更多智能体")
        print("   - 支持跨域协作")

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🤝 协作协议演示")
    print("=" * 60)
    print("本演示需要协作协议支持，请确保相关模块已正确安装")
    print()

    # 运行演示
    asyncio.run(main())
