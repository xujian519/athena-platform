#!/usr/bin/env python3
"""
多智能体协作系统使用示例
Usage Examples for Multi-Agent Collaboration System
"""

import asyncio
import json
from datetime import timedelta

from core.framework.collaboration.multi_agent_collaboration import (
    Agent,
    MultiAgentCollaborationFramework,
)

# 导入优化后的核心组件
from core.framework.collaboration.unified_capability import (
    CapabilityRegistry,
    CapabilityType,
    UnifiedAgentCapability,
)
from core.monitoring.performance_monitor import (
    IntegrationPerformanceMonitor,
    start_integration_monitoring,
)


async def example_1_basic_usage():
    """示例1: 基础使用"""
    print("=" * 60)
    print("示例1: 基础系统使用")
    print("=" * 60)

    # 启动框架
    framework = MultiAgentCollaborationFramework()
    framework.start_framework()

    # 启动监控
    start_integration_monitoring(framework)

    # 创建基础能力
    basic_capability = UnifiedAgentCapability(
        name="text_processing",
        description="文本处理能力",
        type=CapabilityType.PROCESSING,
        proficiency=0.85,
        availability=0.95,
        max_concurrent_tasks=3,
        estimated_duration=timedelta(minutes=5),
        cost_per_hour=100.0
    )

    print(f"✅ 创建基础能力: {basic_capability.name}")
    print(f"   熟练度: {basic_capability.proficiency}")
    print(f"   类型: {basic_capability.type}")

    # 获取系统状态
    status = framework.get_framework_status()
    print(f"📊 系统状态: {json.dumps(status, indent=2, ensure_ascii=False)}")

    print("✅ 示例1完成\n")


async def example_2_agent_management():
    """示例2: 智能体管理"""
    print("=" * 60)
    print("示例2: 智能体管理")
    print("=" * 60)

    framework = MultiAgentCollaborationFramework()
    framework.start_framework()

    # 创建多个能力
    capabilities = [
        UnifiedAgentCapability(
            name="data_analysis",
            description="数据分析能力",
            type=CapabilityType.ANALYSIS,
            proficiency=0.90
        ),
        UnifiedAgentCapability(
            name="machine_learning",
            description="机器学习能力",
            type=CapabilityType.TECHNICAL,
            proficiency=0.88
        ),
        UnifiedAgentCapability(
            name="report_generation",
            description="报告生成能力",
            type=CapabilityType.PROCESSING,
            proficiency=0.92
        )
    ]

    # 创建智能体
    agent = Agent(
        id="ml_analyst_001",
        name="机器学习分析师",
        capabilities=capabilities,
        max_load=5,
        metadata={"department": "AI", "level": "senior"}
    )

    print(f"🤖 创建智能体: {agent.name}")
    print(f"   ID: {agent.id}")
    print(f"   能力数量: {len(agent.capabilities)}")
    print(f"   最大负载: {agent.max_load}")

    # 能力注册表操作
    registry = CapabilityRegistry()
    for cap in capabilities:
        registry.register_capability(cap)

    # 查找特定能力
    analysis_caps = registry.find_capabilities(
        capability_type=CapabilityType.ANALYSIS,
        min_proficiency=0.8
    )

    print(f"🔍 找到 {len(analysis_caps)} 个分析能力")

    print("✅ 示例2完成\n")


async def example_3_performance_monitoring():
    """示例3: 性能监控"""
    print("=" * 60)
    print("示例3: 性能监控")
    print("=" * 60)

    framework = MultiAgentCollaborationFramework()
    monitor = IntegrationPerformanceMonitor(framework)
    monitor.start_monitoring()

    # 模拟一些操作
    print("📊 模拟系统操作...")

    # 记录一些事件
    for _i in range(3):
        monitor.record_agent_registration()
        monitor.record_task_assignment()
        await asyncio.sleep(0.1)  # 短暂延迟

    # 记录会话创建
    monitor.record_session_creation()

    # 等待一些监控数据
    await asyncio.sleep(2)

    # 获取当前指标
    current_metrics = monitor.monitor.get_current_metrics()
    if current_metrics:
        print("📈 当前系统指标:")
        print(f"   CPU使用率: {current_metrics.cpu_percent:.1f}%")
        print(f"   内存使用率: {current_metrics.memory_percent:.1f}%")
        print(f"   活跃智能体: {current_metrics.active_agents}")
        print(f"   响应时间: {current_metrics.avg_response_time:.0f}ms")
        print(f"   错误率: {current_metrics.error_rate:.1f}%")

    # 获取性能摘要
    summary = monitor.monitor.get_performance_summary(minutes=1)
    if summary and "cpu" in summary:
        print("📊 性能摘要:")
        print(f"   平均CPU: {summary['cpu']['avg']:.1f}%")
        print(f"   最大CPU: {summary['cpu']['max']:.1f}%")
        print(f"   平均响应时间: {summary['response_time']['avg']:.0f}ms")

    # 获取建议
    recommendations = monitor._generate_recommendations()
    print("💡 优化建议:")
    for rec in recommendations:
        print(f"   - {rec}")

    print("✅ 示例3完成\n")


async def example_4_collaboration_session():
    """示例4: 协作会话"""
    print("=" * 60)
    print("示例4: 协作会话")
    print("=" * 60)

    framework = MultiAgentCollaborationFramework()
    framework.start_framework()

    # 模拟创建智能体

    # 创建不同的协作配置
    collaboration_configs = [
        {
            "name": "并行协作",
            "config": {
                "mode": "parallel",
                "workflow": ["task1", "task2", "task3"]
            }
        },
        {
            "name": "串行协作",
            "config": {
                "mode": "sequential",
                "workflow": ["step1", "step2", "step3"]
            }
        },
        {
            "name": "层次协作",
            "config": {
                "mode": "hierarchical",
                "coordinator": "agent_001",
                "workflow": ["planning", "execution", "review"]
            }
        }
    ]

    for collab in collaboration_configs:
        print(f"🤝 启动{collab['name']}...")

        try:
            # 模拟会话创建（实际使用中需要真实的智能体）
            session_config = {
                **collab["config"],
                "timeout": 3600,  # 1小时超时
                "retry_count": 3
            }

            print(f"   配置: {json.dumps(session_config, indent=6, ensure_ascii=False)}")
            print(f"   ✅ {collab['name']}配置成功")

        except Exception as e:
            print(f"   ❌ {collab['name']}配置失败: {e}")

    print("✅ 示例4完成\n")


async def example_5_error_handling():
    """示例5: 错误处理演示"""
    print("=" * 60)
    print("示例5: 增强的错误处理")
    print("=" * 60)

    from core.protocols.collaboration_protocols import CommunicationProtocol, ErrorHandler

    # 创建协议并演示错误处理
    try:
        print("🛡️ 创建协议并启动错误处理...")

        # 创建通信协议
        CommunicationProtocol("demo_protocol")

        # 创建错误处理器
        error_handler = ErrorHandler(
            max_retries=3,
            backoff_factor=2,
            timeout=30
        )

        print("✅ 错误处理器已配置:")
        print(f"   最大重试次数: {error_handler.max_retries}")
        print(f"   退避因子: {error_handler.backoff_factor}")
        print(f"   超时时间: {error_handler.timeout}")

        # 演示错误处理能力
        print("🔧 错误处理特性:")
        print("   ✅ 协议状态验证")
        print("   ✅ 自动状态修复")
        print("   ✅ 智能错误恢复")
        print("   ✅ 详细错误诊断")
        print("   ✅ 容错消息处理")

    except Exception as e:
        print(f"⚠️ 错误处理演示中的预期错误: {e}")

    print("✅ 示例5完成\n")


async def example_6_system_integration():
    """示例6: 系统集成演示"""
    print("=" * 60)
    print("示例6: 完整系统集成")
    print("=" * 60)

    # 启动完整系统
    framework = MultiAgentCollaborationFramework()
    monitor = IntegrationPerformanceMonitor(framework)

    print("🚀 启动完整系统组件...")

    # 1. 启动框架
    framework.start_framework()
    print("✅ 协作框架已启动")

    # 2. 启动监控
    monitor.start_monitoring()
    print("✅ 性能监控已启动")

    # 3. 创建能力注册表
    CapabilityRegistry()
    print("✅ 能力注册表已创建")

    # 4. 模拟系统运行
    print("📊 模拟系统运行...")
    operations = [
        ("智能体注册", monitor.record_agent_registration),
        ("任务分配", monitor.record_task_assignment),
        ("会话创建", monitor.record_session_creation),
    ]

    for op_name, op_func in operations:
        op_func()
        print(f"   ✅ {op_name}事件已记录")
        await asyncio.sleep(0.1)

    # 5. 生成集成报告
    print("📋 生成集成报告...")
    report = monitor.get_integration_report()

    if report:
        print("✅ 集成报告生成成功:")
        if "integration_summary" in report:
            summary = report["integration_summary"]
            print(f"   运行时间: {summary.get('runtime_hours', 0):.2f} 小时")
            print(f"   总操作数: {summary.get('total_operations', 0)}")
            print(f"   成功率: {summary.get('success_rate_percent', 0)}%")

        if "recommendations" in report:
            print(f"   优化建议: {len(report['recommendations'])} 条")

    print("✅ 示例6完成\n")


async def run_all_examples():
    """运行所有示例"""
    print("🎯 多智能体协作系统使用示例")
    print("🚀 展示优化后的核心功能")
    print("=" * 60)

    examples = [
        ("基础使用", example_1_basic_usage),
        ("智能体管理", example_2_agent_management),
        ("性能监控", example_3_performance_monitoring),
        ("协作会话", example_4_collaboration_session),
        ("错误处理", example_5_error_handling),
        ("系统集成", example_6_system_integration)
    ]

    for name, example_func in examples:
        try:
            print(f"\n🔄 开始执行: {name}")
            await example_func()
        except Exception as e:
            print(f"❌ 示例 {name} 执行失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎉 所有示例执行完成！")
    print("📖 更多用法请查看 quick_start_guide.md")
    print("📚 详细API文档请查看 docs/api_documentation.md")
    print("=" * 60)


if __name__ == "__main__":
    # 可以选择运行特定示例或全部示例
    import sys

    if len(sys.argv) > 1:
        example_num = int(sys.argv[1])
        examples = {
            1: example_1_basic_usage,
            2: example_2_agent_management,
            3: example_3_performance_monitoring,
            4: example_4_collaboration_session,
            5: example_5_error_handling,
            6: example_6_system_integration
        }

        if example_num in examples:
            asyncio.run(examples[example_num]())
        else:
            print(f"示例 {example_num} 不存在，请选择1-6")
    else:
        # 运行所有示例
        asyncio.run(run_all_examples())
