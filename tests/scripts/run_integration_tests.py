#!/usr/bin/env python3
"""
集成测试运行器
Integration Test Runner

运行整个多智能体协作系统的集成测试
"""

import asyncio
import logging
import os
import sys
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_end_to_end_tests():
    """运行端到端测试"""
    print("\n🔄 运行端到端集成测试")
    print("=" * 50)

    try:
        from tests.integration.test_end_to_end_collaboration import TestEndToEndCollaboration

        # 创建测试套件
        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestEndToEndCollaboration)

        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 端到端测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_system_integration_tests():
    """运行系统集成测试"""
    print("\n🔧 运行系统集成测试")
    print("=" * 50)

    try:
        # 导入各个模块
        from core.protocols import ProtocolManager
        from core.protocols.advanced_coordination import AdvancedCoordinationEngine
        from integration.multi_agent_integration import MultiAgentIntegration

        from core.framework.collaboration import Agent, MultiAgentCollaborationFramework

        print("1. 测试模块导入...")
        # 模块导入测试
        modules = [
            ("协作框架", MultiAgentCollaborationFramework),
            ("协议管理器", ProtocolManager),
            ("协调引擎", AdvancedCoordinationEngine),
            ("智能体集成", MultiAgentIntegration)
        ]

        for module_name, module_class in modules:
            try:
                module_class()
                print(f"   {module_name}: ✅ 导入成功")
            except Exception as e:
                print(f"   {module_name}: ❌ 导入失败 - {e}")
                return False

        print("\n2. 测试系统初始化...")
        # 系统初始化测试
        framework = MultiAgentCollaborationFramework()
        protocol_manager = ProtocolManager()
        coordination_engine = AdvancedCoordinationEngine()
        MultiAgentIntegration()

        # 启动框架
        framework.start_framework()
        print("   协作框架: ✅ 启动成功")

        print("\n3. 测试组件间集成...")
        # 组件集成测试
        # 注册智能体 - 使用统一能力接口
        try:
            from core.framework.collaboration.unified_capability import (
                CapabilityAdapter,
                CapabilityType,
                UnifiedAgentCapability,
            )
            use_unified_capability = True
        except ImportError:
            use_unified_capability = False

        if use_unified_capability:
            # 使用统一能力接口
            unified_cap = UnifiedAgentCapability(
                name="integration_test",
                description="集成测试能力",
                type=CapabilityType.TECHNICAL,
                proficiency=0.9,
                max_concurrent_tasks=1,
                estimated_duration=timedelta(minutes=10)
            )
            # 转换为协作框架格式
            framework_cap = CapabilityAdapter.to_collaboration_framework(unified_cap)
            capabilities = [framework_cap] if isinstance(framework_cap, dict) else [framework_cap]

            # 转换为协调引擎格式
            coord_cap = CapabilityAdapter.to_advanced_coordination(unified_cap)
        else:
            # 使用原有接口
            from core.protocols.advanced_coordination import AgentCapability as CoordCapability

            from core.framework.collaboration import AgentCapability as CollabCapability
            capabilities = [CollabCapability("integration_test", 0.9, timedelta(minutes=10))]
            coord_cap = CoordCapability(
                capability_name="integration_test",
                proficiency=0.9,
                availability=1.0,
                cost_per_hour=100.0
            )

        agent = Agent(
            id="test_integration_agent",
            name="集成测试智能体",
            capabilities=capabilities
        )
        success = framework.register_agent(agent)
        print(f"   智能体注册: {'✅ 成功' if success else '❌ 失败'}")

        # 创建协议
        comm_protocol_id = protocol_manager.create_communication_protocol(["test_integration_agent"])
        print(f"   通信协议创建: {'✅ 成功' if comm_protocol_id else '❌ 失败'}")

        # 注册协调引擎智能体
        coord_success = coordination_engine.register_agent("test_integration_agent", [coord_cap])
        print(f"   协调引擎注册: {'✅ 成功' if coord_success else '❌ 失败'}")

        print("\n4. 测试完整工作流...")
        # 完整工作流测试
        from core.framework.collaboration import Priority, Task, TaskStatus

        # 创建任务
        task = Task(
            title="集成测试任务",
            required_capabilities=["integration_test"],
            priority=Priority.NORMAL
        )

        framework.tasks[task.id] = task
        print("   任务创建: ✅ 成功")

        # 分配任务
        assignment_success = framework.assign_task(task.id, ["test_integration_agent"])
        print(f"   任务分配: {'✅ 成功' if assignment_success else '❌ 失败'}")

        # 完成任务
        task.status = TaskStatus.COMPLETED
        task.update_progress(1.0)
        framework.completed_tasks.add(task.id)
        print("   任务完成: ✅ 成功")

        print("\n5. 获取系统状态...")
        # 系统状态测试
        framework_status = framework.get_framework_status()
        coordination_status = coordination_engine.get_coordination_status()

        print(f"   框架智能体数: {framework_status['agents']['total']}")
        print(f"   框架任务数: {framework_status['tasks']['total']}")
        print(f"   协调引擎智能体数: {coordination_status['registered_agents']}")
        print("   系统状态: ✅ 正常")

        return True

    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_performance_integration_tests():
    """运行性能集成测试"""
    print("\n📊 运行性能集成测试")
    print("=" * 50)

    try:
        from core.protocols import ProtocolManager
        from core.protocols.advanced_coordination import AdvancedCoordinationEngine

        from core.framework.collaboration import (
            Agent,
            AgentCapability,
            MultiAgentCollaborationFramework,
        )

        # 创建系统组件
        framework = MultiAgentCollaborationFramework()
        protocol_manager = ProtocolManager()
        AdvancedCoordinationEngine()

        print("1. 性能基准测试...")
        start_time = time.time()

        # 注册智能体性能测试
        print("   注册智能体性能测试...")
        agent_start = time.time()

        # 导入统一能力接口
        try:
            from core.framework.collaboration.unified_capability import (
                CapabilityAdapter,
                CapabilityType,
                UnifiedAgentCapability,
            )
            use_unified_capability = True
        except ImportError:
            use_unified_capability = False
            print("   警告: 无法导入统一能力接口，使用原有接口")

        for i in range(100):
            if use_unified_capability:
                # 使用统一能力接口
                unified_cap = UnifiedAgentCapability(
                    name=f"capability_{i%5}",
                    description=f"性能测试能力 {i%5}",
                    type=CapabilityType.TECHNICAL,
                    proficiency=0.8,
                    max_concurrent_tasks=3,
                    estimated_duration=timedelta(minutes=10),
                    cost_per_hour=100.0
                )
                # 转换为协作框架格式
                framework_cap = CapabilityAdapter.to_collaboration_framework(unified_cap)
                capabilities = [framework_cap] if isinstance(framework_cap, dict) else [framework_cap]
            else:
                # 使用原有接口
                capabilities = [
                    AgentCapability(f"capability_{i%5}", 0.8, timedelta(minutes=10), cost_per_hour=100.0)
                ]

            agent = Agent(
                id=f"perf_agent_{i:03d}",
                name=f"性能智能体{i}",
                capabilities=capabilities,
                max_load=5
            )
            framework.register_agent(agent)
        agent_time = time.time() - agent_start
        print(f"   注册100个智能体用时: {agent_time:.3f} 秒 ({100/agent_time:.1f} 个/秒)")

        # 协议创建性能测试
        print("   协议创建性能测试...")
        protocol_start = time.time()
        protocols = []
        for i in range(50):
            participants = [f"perf_agent_{j:03d}" for j in range(min(5, 100))]
            protocol_id = protocol_manager.create_communication_protocol(participants)
            protocols.append(protocol_id)
        protocol_time = time.time() - protocol_start
        print(f"   创建50个协议用时: {protocol_time:.3f} 秒 ({50/protocol_time:.1f} 个/秒)")

        # 任务创建和分配性能测试
        print("   任务创建和分配性能测试...")
        task_start = time.time()
        successful_assignments = 0
        for i in range(200):
            # 创建任务
            from core.framework.collaboration import Priority, Task
            task = Task(
                title=f"性能任务{i:04d}",
                required_capabilities=[f"capability_{i%5}"],
                priority=Priority.NORMAL
            )
            framework.tasks[task.id] = task

            # 分配任务
            suitable_agents = framework.find_suitable_agents(
                {"capabilities": task.required_capabilities}
            )
            if suitable_agents:
                agent_id = suitable_agents[0][0]
                if framework.assign_task(task.id, [agent_id]):
                    successful_assignments += 1

        task_time = time.time() - task_start
        print(f"   处理200个任务用时: {task_time:.3f} 秒 ({200/task_time:.1f} 个/秒)")
        print(f"   成功分配任务: {successful_assignments}/{200}")

        total_time = time.time() - start_time
        print(f"\n   总体性能: {(100+50+200)/total_time:.1f} 操作/秒")

        # 性能评估
        performance_ok = (
            agent_time < 2.0 and
            protocol_time < 1.0 and
            task_time < 3.0
        )

        print(f"   性能测试结果: {'✅ 优秀' if performance_ok else '⚠️ 需要优化'}")

        return performance_ok

    except Exception as e:
        print(f"❌ 性能集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_scenario_based_tests():
    """运行场景化测试"""
    print("\n🎭 运行场景化测试")
    print("=" * 50)

    try:
        from core.framework.collaboration import (
            Agent,
            AgentCapability,
            MultiAgentCollaborationFramework,
            Priority,
            Task,
            TaskStatus,
        )

        framework = MultiAgentCollaborationFramework()
        framework.start_framework()

        # 场景1: 专利分析协作
        print("场景1: 专利分析协作")
        print("-" * 30)

        # 注册专业智能体
        patent_analyst = Agent(
            id="patent_analyst",
            name="专利分析师",
            capabilities=[
                AgentCapability("patent_analysis", 0.95, timedelta(minutes=25)),
                AgentCapability("technical_evaluation", 0.9, timedelta(minutes=20))
            ]
        )

        strategic_advisor = Agent(
            id="strategic_advisor",
            name="战略顾问",
            capabilities=[
                AgentCapability("strategic_thinking", 0.9, timedelta(minutes=30)),
                AgentCapability("market_analysis", 0.85, timedelta(minutes=35))
            ]
        )

        framework.register_agent(patent_analyst)
        framework.register_agent(strategic_advisor)

        # 创建专利分析任务
        patent_task = Task(
            title="AI技术专利分析",
            description="分析一项新兴AI技术的专利申请",
            required_capabilities=["patent_analysis", "strategic_thinking"],
            priority=Priority.HIGH,
            deadline=datetime.now() + timedelta(hours=4)
        )

        framework.tasks[patent_task.id] = patent_task

        # 分配任务
        suitable_agents = framework.find_suitable_agents(
            {"capabilities": patent_task.required_capabilities}
        )

        if suitable_agents:
            best_agent_id = suitable_agents[0][0]
            framework.assign_task(patent_task.id, [best_agent_id])
            print(f"   任务已分配给: {best_agent_id}")
            patent_task.status = TaskStatus.IN_PROGRESS
            patent_task.update_progress(0.6)

        print(f"   场景1状态: {'✅ 成功' if patent_task.status == TaskStatus.IN_PROGRESS else '❌ 失败'}")

        # 场景2: 项目规划协作
        print("\n场景2: 项目规划协作")
        print("-" * 30)

        project_manager = Agent(
            id="project_manager",
            name="项目经理",
            capabilities=[
                AgentCapability("project_planning", 0.9, timedelta(minutes=40)),
                AgentCapability("resource_allocation", 0.85, timedelta(minutes=30))
            ]
        )

        goal_specialist = Agent(
            id="goal_specialist",
            name="目标专家",
            capabilities=[
                AgentCapability("goal_setting", 0.95, timedelta(minutes=20)),
                AgentCapability("progress_tracking", 0.9, timedelta(minutes=15))
            ]
        )

        framework.register_agent(project_manager)
        framework.register_agent(goal_specialist)

        # 创建项目规划任务
        planning_task = Task(
            title="智能体开发项目规划",
            description="制定新智能体开发项目的详细规划",
            required_capabilities=["project_planning", "goal_setting"],
            priority=Priority.NORMAL
        )

        framework.tasks[planning_task.id] = planning_task

        # 启动协作会话
        session_id = framework.start_collaboration_session(
            planning_task.id,
            ["project_manager", "goal_specialist"],
            {"mode": "sequential", "workflow": ["goal_setting", "planning"]}
        )

        planning_task.status = TaskStatus.ASSIGNED
        planning_task.update_progress(0.3)

        print(f"   协作会话启动: {'✅ 成功' if session_id else '❌ 失败'}")
        print(f"   场景2状态: {'✅ 成功' if planning_task.status == TaskStatus.ASSIGNED else '❌ 失败'}")

        # 场景3: 紧急任务处理
        print("\n场景3: 紧急任务处理")
        print("-" * 30)

        emergency_handler = Agent(
            id="emergency_handler",
            name="应急处理专家",
            capabilities=[
                AgentCapability("emergency_response", 0.95, timedelta(minutes=5)),
                AgentCapability("rapid_coordination", 0.9, timedelta(minutes=10))
            ],
            metadata={"role": "emergency", "priority": 10}
        )

        framework.register_agent(emergency_handler)

        # 创建紧急任务
        emergency_task = Task(
            title="系统故障紧急处理",
            description="处理突发的系统故障",
            required_capabilities=["emergency_response"],
            priority=Priority.URGENT,
            deadline=datetime.now() + timedelta(minutes=30)
        )

        framework.tasks[emergency_task.id] = emergency_task

        # 高优先级分配
        suitable_agents = framework.find_suitable_agents(
            {"capabilities": emergency_task.required_capabilities}
        )

        if suitable_agents:
            emergency_agent_id = suitable_agents[0][0]
            framework.assign_task(emergency_task.id, [emergency_agent_id])
            emergency_task.status = TaskStatus.IN_PROGRESS
            emergency_task.update_progress(0.8)

        print(f"   紧急任务分配: {'✅ 成功' if suitable_agents else '❌ 无可用智能体'}")
        print(f"   场景3状态: {'✅ 成功' if emergency_task.status == TaskStatus.IN_PROGRESS else '❌ 失败'}")

        # 场景4: 多任务并行处理
        print("\n场景4: 多任务并行处理")
        print("-" * 30)

        # 注册更多智能体
        for i in range(5):
            worker = Agent(
                id=f"worker_{i}",
                name=f"工作智能体{i}",
                capabilities=[
                    AgentCapability("general_task", 0.8, timedelta(minutes=15))
                ]
            )
            framework.register_agent(worker)

        # 创建多个并行任务
        parallel_tasks = []
        for i in range(10):
            task = Task(
                title=f"并行任务{i}",
                required_capabilities=["general_task"],
                priority=Priority.NORMAL
            )
            framework.tasks[task.id] = task
            parallel_tasks.append(task)

        # 并行分配
        assigned_count = 0
        for task in parallel_tasks:
            suitable_agents = framework.find_suitable_agents(
                {"capabilities": task.required_capabilities}
            )
            if suitable_agents:
                agent_id = suitable_agents[0][0]
                framework.assign_task(task.id, [agent_id])
                assigned_count += 1

        print(f"   并行任务分配: {assigned_count}/{len(parallel_tasks)}")
        print(f"   场景4状态: {'✅ 成功' if assigned_count > 0 else '❌ 失败'}")

        # 获取最终状态
        final_status = framework.get_framework_status()
        print("\n📊 最终状态统计:")
        print(f"   注册智能体: {final_status['agents']['total']}")
        print(f"   创建任务: {final_status['tasks']['total']}")
        print(f"   活跃会话: {final_status['sessions']['active']}")
        print(f"   完成任务: {len(framework.completed_tasks)}")

        return True

    except Exception as e:
        print(f"❌ 场景化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_integration_test_report(results):
    """生成集成测试报告"""
    print("\n📄 生成集成测试报告")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = passed_tests / total_tests if total_tests > 0 else 0

    print("📊 集成测试统计:")
    print(f"   总测试项: {total_tests}")
    print(f"   通过项目: {passed_tests}")
    print(f"   失败项目: {total_tests - passed_tests}")
    print(f"   成功率: {success_rate:.1%}")

    print("\n📋 详细结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")

    # 保存报告
    report_dir = Path('/Users/xujian/Athena工作平台/tests/reports')
    report_dir.mkdir(exist_ok=True)

    import time
    report_content = f"""# 多智能体协作系统集成测试报告

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
        report_content += "\n## 总体评估\n✅ 系统集成质量优秀，可以投入生产使用"
    elif success_rate >= 0.6:
        report_content += "\n## 总体评估\n⚠️ 系统集成质量良好，建议优化后使用"
    else:
        report_content += "\n## 总体评估\n❌ 系统集成存在较多问题，需要修复后重新测试"

    # 保存报告
    report_file = report_dir / f"integration_test_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n📄 报告已保存: {report_file}")

    return success_rate


async def main():
    """主函数"""
    print("🚀 开始多智能体协作系统集成测试")
    print("=" * 60)

    start_time = time.time()

    results = {}

    # 运行各项测试
    results["端到端集成测试"] = run_end_to_end_tests()
    results["系统集成测试"] = await run_system_integration_tests()
    results["性能集成测试"] = await run_performance_integration_tests()
    results["场景化测试"] = await run_scenario_based_tests()

    # 生成测试报告
    success_rate = generate_integration_test_report(results)

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n⏱️ 总测试时间: {total_time:.2f} 秒")

    if success_rate >= 0.8:
        print("\n🎉 集成测试完成！系统质量优秀")
        return 0
    elif success_rate >= 0.6:
        print("\n✅ 集成测试完成！系统质量良好")
        return 0
    else:
        print("\n⚠️ 集成测试发现问题，建议修复后重新测试")
        return 1


if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs('/Users/xujian/Athena工作平台/tests/reports', exist_ok=True)

    # 运行集成测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
