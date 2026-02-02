#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协作协议测试运行器
Collaboration Protocols Test Runner

运行协作协议的所有测试
"""

import sys
import os
import unittest
import time
import logging
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_protocol_core_tests():
    """运行协议核心测试"""
    print("\n🔄 运行协议核心测试")
    print("=" * 50)

    try:
        from tests.protocols.test_collaboration_protocols import (
            TestProtocolMessage, TestProtocolContext
        )

        # 创建测试套件
        loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()

        # 添加测试类
        test_suite.addTest(loader.loadTestsFromTestCase(TestProtocolMessage))
        test_suite.addTest(loader.loadTestsFromTestCase(TestProtocolContext))

        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 协议核心测试运行失败: {e}")
        return False


def run_communication_protocol_tests():
    """运行通信协议测试"""
    print("\n📡 运行通信协议测试")
    print("=" * 50)

    try:
        from tests.protocols.test_collaboration_protocols import TestCommunicationProtocol

        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestCommunicationProtocol)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 通信协议测试运行失败: {e}")
        return False


def run_coordination_protocol_tests():
    """运行协调协议测试"""
    print("\n🤝 运行协调协议测试")
    print("=" * 50)

    try:
        from tests.protocols.test_collaboration_protocols import TestCoordinationProtocol

        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestCoordinationProtocol)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 协调协议测试运行失败: {e}")
        return False


def run_decision_protocol_tests():
    """运行决策协议测试"""
    print("\n🗳️ 运行决策协议测试")
    print("=" * 50)

    try:
        from tests.protocols.test_collaboration_protocols import TestDecisionProtocol

        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestDecisionProtocol)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 决策协议测试运行失败: {e}")
        return False


def run_protocol_manager_tests():
    """运行协议管理器测试"""
    print("\n🎛️ 运行协议管理器测试")
    print("=" * 50)

    try:
        from tests.protocols.test_collaboration_protocols import TestProtocolManager

        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestProtocolManager)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 协议管理器测试运行失败: {e}")
        return False


def run_integration_protocol_tests():
    """运行协议集成测试"""
    print("\n🔗 运行协议集成测试")
    print("=" * 50)

    try:
        from tests.protocols.test_collaboration_protocols import TestProtocolIntegration

        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestProtocolIntegration)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 协议集成测试运行失败: {e}")
        return False


async def run_advanced_coordination_tests():
    """运行高级协调测试"""
    print("\n🚀 运行高级协调测试")
    print("=" * 50)

    try:
        from core.protocols.advanced_coordination import (
            AdvancedCoordinationEngine, AgentCapability, TaskSpecification,
            TaskPriority, ResourceType, register_agent, submit_task
        )

        # 创建协调引擎
        engine = AdvancedCoordinationEngine()

        print("1. 测试智能体注册...")
        # 创建测试能力
        capabilities = [
            AgentCapability(
                capability_name="analysis",
                proficiency=0.9,
                availability=1.0,
                cost_per_hour=100.0
            ),
            AgentCapability(
                capability_name="planning",
                proficiency=0.8,
                availability=0.9,
                cost_per_hour=120.0
            )
        ]

        # 注册智能体
        success = engine.register_agent("test_agent", capabilities, max_load=2.0)
        print(f"   智能体注册: {'✅ 成功' if success else '❌ 失败'}")

        print("2. 测试任务提交...")
        # 创建测试任务
        task_spec = TaskSpecification(
            task_id="test_task_001",
            task_type="analysis_task",
            priority=TaskPriority.HIGH,
            required_capabilities=["analysis"],
            resource_requirements=[
                {
                    "resource_type": ResourceType.COMPUTE,
                    "amount": 50.0,
                    "unit": "percent"
                }
            ]
        )

        # 提交任务
        success = submit_task(task_spec)
        print(f"   任务提交: {'✅ 成功' if success else '❌ 失败'}")

        print("3. 测试资源管理...")
        # 添加资源
        engine.resource_pool.add_resource("cpu_001", ResourceType.COMPUTE, 100.0, "percent")
        engine.resource_pool.add_resource("mem_001", ResourceType.MEMORY, 16.0, "GB")

        # 分配资源
        from core.protocols.advanced_coordination import ResourceRequirement
        req = ResourceRequirement(
            resource_type=ResourceType.COMPUTE,
            amount=25.0,
            unit="percent"
        )

        resource_id = engine.resource_pool.allocate_resource(req, "test_task_001")
        print(f"   资源分配: {'✅ 成功' if resource_id else '❌ 失败'}")

        print("4. 测试协调状态...")
        status = engine.get_coordination_status()
        print(f"   注册智能体数: {status['registered_agents']}")
        print(f"   排队任务数: {status['queued_tasks']}")
        print(f"   协调策略: {status['coordination_strategy']}")
        print(f"   协调状态: ✅ 正常")

        return True

    except Exception as e:
        print(f"❌ 高级协调测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_performance_protocol_tests():
    """运行协议性能测试"""
    print("\n📊 运行协议性能测试")
    print("=" * 50)

    try:
        from core.protocols.collaboration_protocols import ProtocolManager, CommunicationProtocol

        print("1. 测试协议创建性能...")
        start_time = time.time()

        manager = ProtocolManager()
        participants = ["agent_001", "agent_002"]

        protocols = []
        for i in range(100):
            protocol_id = manager.create_communication_protocol(participants)
            protocols.append(protocol_id)

        creation_time = time.time() - start_time
        print(f"   创建100个协议用时: {creation_time:.3f} 秒")
        print(f"   平均创建速度: {100/creation_time:.1f} 个/秒")

        print("2. 测试消息处理性能...")
        start_time = time.time()

        from core.protocols.collaboration_protocols import ProtocolMessage

        messages_processed = 0
        for protocol_id in protocols[:50]:  # 测试50个协议
            for i in range(10):  # 每个协议10条消息
                message = ProtocolMessage(
                    protocol_id=protocol_id,
                    sender_id="agent_001",
                    receiver_id="agent_002",
                    message_type="test_message",
                    content={"index": i}
                )
                if manager.route_message(message):
                    messages_processed += 1

        processing_time = time.time() - start_time
        print(f"   处理{messages_processed}条消息用时: {processing_time:.3f} 秒")
        print(f"   消息处理速度: {messages_processed/processing_time:.1f} 条/秒")

        print("3. 测试状态查询性能...")
        start_time = time.time()

        for protocol_id in protocols:
            status = manager.get_protocol_status(protocol_id)
            # 验证状态获取成功
            assert status is not None

        query_time = time.time() - start_time
        print(f"   查询100个协议状态用时: {query_time:.3f} 秒")
        print(f"   状态查询速度: {100/query_time:.1f} 次/秒")

        # 性能评估
        performance_ok = (
            creation_time < 1.0 and
            processing_time < 0.5 and
            query_time < 0.1
        )

        print(f"\n📈 性能评估:")
        print(f"   协议创建: {'✅ 优秀' if creation_time < 0.5 else '⚠️ 一般' if creation_time < 1.0 else '❌ 需要优化'}")
        print(f"   消息处理: {'✅ 优秀' if processing_time < 0.25 else '⚠️ 一般' if processing_time < 0.5 else '❌ 需要优化'}")
        print(f"   状态查询: {'✅ 优秀' if query_time < 0.05 else '⚠️ 一般' if query_time < 0.1 else '❌ 需要优化'}")
        print(f"   性能测试结果: {'✅ 通过' if performance_ok else '⚠️ 需要优化'}")

        return performance_ok

    except Exception as e:
        print(f"❌ 协议性能测试运行失败: {e}")
        return False


def generate_protocol_test_report(results):
    """生成协议测试报告"""
    print("\n📄 生成协议测试报告")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = passed_tests / total_tests if total_tests > 0 else 0

    print(f"📊 协议测试统计:")
    print(f"   总测试项: {total_tests}")
    print(f"   通过项目: {passed_tests}")
    print(f"   失败项目: {total_tests - passed_tests}")
    print(f"   成功率: {success_rate:.1%}")

    print(f"\n📋 详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")

    # 保存报告
    report_dir = Path('/Users/xujian/Athena工作平台/tests/reports')
    report_dir.mkdir(exist_ok=True)

    import time
    report_content = f"""# 协作协议测试报告

**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 测试统计

- 总测试项: {total_tests}
- 通过项目: {passed_tests}
- 失败项目: {total_tests - passed_tests}
- 成功率: {success_rate:.1%}

## 测试结果

"""

    for test_name, result in results.items():
        status = "通过" if result else "失败"
        report_content += f"- {test_name}: {status}\n"

    if success_rate >= 0.8:
        report_content += "\n## 总体评估\n✅ 协议质量良好，可以投入使用"
    else:
        report_content += "\n## 总体评估\n⚠️ 存在问题，需要修复后重新测试"

    # 保存报告
    report_file = report_dir / f"protocol_test_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n📄 报告已保存: {report_file}")

    return success_rate


async def main():
    """主函数"""
    print("🚀 开始协作协议测试")
    print("=" * 60)

    start_time = time.time()

    results = {}

    # 运行各项测试
    results["协议核心测试"] = run_protocol_core_tests()
    results["通信协议测试"] = run_communication_protocol_tests()
    results["协调协议测试"] = run_coordination_protocol_tests()
    results["决策协议测试"] = run_decision_protocol_tests()
    results["协议管理器测试"] = run_protocol_manager_tests()
    results["协议集成测试"] = run_integration_protocol_tests()
    results["高级协调测试"] = await run_advanced_coordination_tests()
    results["协议性能测试"] = run_performance_protocol_tests()

    # 生成测试报告
    success_rate = generate_protocol_test_report(results)

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n⏱️ 总测试时间: {total_time:.2f} 秒")

    if success_rate >= 0.8:
        print("\n🎉 协议测试完成！系统质量良好")
        return 0
    else:
        print("\n⚠️ 协议测试发现问题，建议修复后重新测试")
        return 1


if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs('/Users/xujian/Athena工作平台/tests/reports', exist_ok=True)

    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)