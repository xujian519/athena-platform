#!/usr/bin/env python3
"""
多智能体协作测试运行器
Multi-Agent Collaboration Test Runner

运行多智能体协作框架的所有测试
"""

import logging
import os
import sys
import time
import unittest
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_basic_collaboration_tests():
    """运行基础协作测试"""
    print("\n🔄 运行基础协作测试")
    print("=" * 50)

    try:
        from tests.collaboration.test_multi_agent_collaboration import (
            TestAgent,
            TestAgentCapability,
            TestMessage,
            TestTask,
        )

        # 创建测试套件
        loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()

        # 添加测试类
        test_suite.addTest(loader.loadTestsFromTestCase(TestAgentCapability))
        test_suite.addTest(loader.loadTestsFromTestCase(TestAgent))
        test_suite.addTest(loader.loadTestsFromTestCase(TestTask))
        test_suite.addTest(loader.loadTestsFromTestCase(TestMessage))

        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 基础协作测试运行失败: {e}")
        return False


def run_framework_tests():
    """运行框架测试"""
    print("\n🏗️ 运行框架测试")
    print("=" * 50)

    try:
        from tests.collaboration.test_multi_agent_collaboration import (
            TestMultiAgentCollaborationFramework,
        )

        loader = unittest.TestLoader()
        test_suite = loader.loadTestsFromTestCase(TestMultiAgentCollaborationFramework)

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 框架测试运行失败: {e}")
        return False


def run_pattern_tests():
    """运行协作模式测试"""
    print("\n🎭 运行协作模式测试")
    print("=" * 50)

    try:
        from tests.collaboration.test_multi_agent_collaboration import (
            TestConsensusCollaborationPattern,
            TestHierarchicalCollaborationPattern,
            TestParallelCollaborationPattern,
            TestSequentialCollaborationPattern,
        )

        loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()

        test_suite.addTest(loader.loadTestsFromTestCase(TestSequentialCollaborationPattern))
        test_suite.addTest(loader.loadTestsFromTestCase(TestParallelCollaborationPattern))
        test_suite.addTest(loader.loadTestsFromTestCase(TestHierarchicalCollaborationPattern))
        test_suite.addTest(loader.loadTestsFromTestCase(TestConsensusCollaborationPattern))

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(test_suite)

        return result.wasSuccessful()

    except Exception as e:
        print(f"❌ 协作模式测试运行失败: {e}")
        return False


def run_integration_collaboration_tests():
    """运行集成协作测试"""
    print("\n🔗 运行集成协作测试")
    print("=" * 50)

    try:
        # 导入多智能体集成
        from integration.multi_agent_integration import MultiAgentIntegration

        # 创建集成实例
        integration = MultiAgentIntegration()

        # 测试集成初始化
        print("1. 测试集成初始化...")
        init_result = integration.initialize_integrations()
        print(f"   集成初始化: {'✅ 成功' if init_result else '❌ 失败'}")

        # 测试协作启动
        print("2. 测试协作启动...")
        import asyncio

        async def test_collaboration():
            session_id = await integration.start_collaboration(
                'comprehensive_collaboration',
                '测试综合协作任务',
                {'test_mode': True}
            )
            return session_id is not None

        try:
            collaboration_result = asyncio.run(test_collaboration())
            print(f"   协作启动: {'✅ 成功' if collaboration_result else '❌ 失败'}")
        except Exception as e:
            print(f"   协作启动: ❌ 失败 ({e})")
            collaboration_result = False

        # 测试状态获取
        print("3. 测试状态获取...")
        try:
            framework_status = integration.get_framework_status()
            agent_status = integration.get_agent_status('xiaonuo')
            print("   框架状态: ✅ 成功获取")
            print("   智能体状态: ✅ 成功获取" if agent_status else "⚠️ 智能体状态获取失败")
        except Exception as e:
            print(f"   状态获取: ❌ 失败 ({e})")
            framework_status = None

        return init_result and collaboration_result and framework_status is not None

    except Exception as e:
        print(f"❌ 集成协作测试运行失败: {e}")
        return False


def run_performance_collaboration_tests():
    """运行协作性能测试"""
    print("\n📊 运行协作性能测试")
    print("=" * 50)

    try:
        from core.framework.collaboration import (
            Agent,
            AgentCapability,
            MultiAgentCollaborationFramework,
            create_task,
        )

        # 创建框架
        framework = MultiAgentCollaborationFramework()

        # 性能测试：注册多个智能体
        print("1. 测试智能体注册性能...")
        start_time = time.time()

        agents = []
        for i in range(20):
            agent = Agent(
                id=f"perf_agent_{i:03d}",
                name=f"性能测试智能体{i}",
                capabilities=[
                    AgentCapability(
                        name=f"capability_{i % 5}",
                        description=f"测试能力{i % 5}"
                    )
                ]
            )
            agents.append(agent)
            framework.register_agent(agent)

        registration_time = time.time() - start_time
        print(f"   注册20个智能体用时: {registration_time:.3f} 秒")

        # 性能测试：创建多个任务
        print("2. 测试任务创建性能...")
        start_time = time.time()

        tasks = []
        for i in range(50):
            task = create_task(
                title=f"性能测试任务{i}",
                required_capabilities=[f"capability_{i % 5}"]
            )
            tasks.append(task)
            framework.tasks[task.id] = task

        task_creation_time = time.time() - start_time
        print(f"   创建50个任务用时: {task_creation_time:.3f} 秒")

        # 性能测试：任务分配
        print("3. 测试任务分配性能...")
        start_time = time.time()

        successful_assignments = 0
        for task in tasks[:20]:  # 只测试前20个任务
            suitable_agents = framework.find_suitable_agents(
                {"capabilities": task.required_capabilities}
            )
            if suitable_agents:
                agent_id = suitable_agents[0][0]
                if framework.assign_task(task.id, [agent_id]):
                    successful_assignments += 1

        assignment_time = time.time() - start_time
        print(f"   分配{successful_assignments}个任务用时: {assignment_time:.3f} 秒")

        # 性能评估
        print("\n📈 性能评估:")
        print(f"   智能体注册速度: {20/registration_time:.1f} 个/秒")
        print(f"   任务创建速度: {50/task_creation_time:.1f} 个/秒")
        print(f"   任务分配速度: {successful_assignments/assignment_time:.1f} 个/秒")

        # 性能阈值检查
        performance_ok = (
            registration_time < 1.0 and
            task_creation_time < 0.5 and
            assignment_time < 2.0
        )

        print(f"   性能测试结果: {'✅ 通过' if performance_ok else '⚠️ 需要优化'}")

        return performance_ok

    except Exception as e:
        print(f"❌ 协作性能测试运行失败: {e}")
        return False


def generate_collaboration_test_report(results):
    """生成协作测试报告"""
    print("\n📄 生成协作测试报告")
    print("=" * 50)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    success_rate = passed_tests / total_tests if total_tests > 0 else 0

    print("📊 协作测试统计:")
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
    report_content = f"""# 多智能体协作框架测试报告

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
        report_content += "\n## 总体评估\n✅ 协作框架质量良好，可以投入使用"
    else:
        report_content += "\n## 总体评估\n⚠️ 存在问题，需要修复后重新测试"

    # 保存报告
    report_file = report_dir / f"collaboration_test_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n📄 报告已保存: {report_file}")

    return success_rate


def main():
    """主函数"""
    print("🚀 开始多智能体协作框架测试")
    print("=" * 60)

    start_time = time.time()

    results = {}

    # 运行各项测试
    results["基础协作测试"] = run_basic_collaboration_tests()
    results["框架测试"] = run_framework_tests()
    results["协作模式测试"] = run_pattern_tests()
    results["集成协作测试"] = run_integration_collaboration_tests()
    results["协作性能测试"] = run_performance_collaboration_tests()

    # 生成测试报告
    success_rate = generate_collaboration_test_report(results)

    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n⏱️ 总测试时间: {total_time:.2f} 秒")

    if success_rate >= 0.8:
        print("\n🎉 协作框架测试完成！系统质量良好")
        return 0
    else:
        print("\n⚠️ 协作框架测试发现问题，建议修复后重新测试")
        return 1


if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs('/Users/xujian/Athena工作平台/tests/reports', exist_ok=True)

    # 运行测试
    exit_code = main()
    sys.exit(exit_code)
