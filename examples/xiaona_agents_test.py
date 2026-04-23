"""
小娜专业智能体系统测试示例

演示如何使用小诺编排者动态组装小娜专业智能体完成各种任务。
"""

import asyncio
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scenario_detection():
    """测试场景识别"""
    from core.framework.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

    # 创建小诺编排者
    xiaonuo = XiaonuoOrchestrator()

    # 测试不同场景
    test_inputs = [
        "帮我检索关于自动驾驶掉头的专利",
        "分析专利CN123456789A的创造性",
        "根据交底书撰写专利申请文件",
        "审查意见认为权利要求1不具备创造性，请帮助答复",
    ]

    print("\n" + "="*60)
    print("场景识别测试")
    print("="*60)

    for user_input in test_inputs:
        result = await xiaonuo.test_scenario_detection(user_input)
        result_dict = json.loads(result)
        print(f"\n用户输入: {user_input}")
        print(f"识别场景: {result_dict['detected_scenario']}")
        print(f"需要的智能体: {result_dict['required_agents']}")
        print(f"执行模式: {result_dict['execution_mode']}")


async def test_patent_search():
    """测试专利检索任务"""
    from core.framework.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

    print("\n" + "="*60)
    print("专利检索任务测试")
    print("="*60)

    # 创建小诺编排者
    xiaonuo = XiaonuoOrchestrator()

    # 执行专利检索任务
    user_input = "帮我检索关于自动驾驶掉头的专利"
    session_id = "test_session_001"

    result = await xiaonuo.process(user_input, session_id)
    result_dict = json.loads(result)

    print(f"\n任务状态: {result_dict['status']}")
    print(f"识别场景: {result_dict['scenario']}")
    print(f"执行时间: {result_dict['total_time']:.2f}秒")
    print(f"完成步骤: {result_dict['steps_completed']}/{result_dict['steps_total']}")

    if result_dict['status'] == 'success':
        # 输出检索结果
        output = result_dict.get('output', {})
        if 'patents' in output:
            patents = output['patents']
            print(f"\n检索到 {len(patents)} 篇专利")
            for i, patent in enumerate(patents[:5], 1):
                print(f"{i}. {patent.get('title', 'N/A')} ({patent.get('patent_id', 'N/A')})")


async def test_creativity_analysis():
    """测试创造性分析任务"""
    from core.framework.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

    print("\n" + "="*60)
    print("创造性分析任务测试")
    print("="*60)

    # 创建小诺编排者
    xiaonuo = XiaonuoOrchestrator()

    # 执行创造性分析任务
    user_input = "分析专利CN123456789A的创造性"
    session_id = "test_session_002"

    result = await xiaonuo.process(user_input, session_id)
    result_dict = json.loads(result)

    print(f"\n任务状态: {result_dict['status']}")
    print(f"识别场景: {result_dict['scenario']}")
    print(f"执行时间: {result_dict['total_time']:.2f}秒")
    print(f"完成步骤: {result_dict['steps_completed']}/{result_dict['steps_total']}")

    # 输出各步骤详情
    for step_id, step_detail in result_dict.get('step_details', {}).items():
        print(f"  - {step_id}: {step_detail['agent_id']} ({step_detail['status']}) - {step_detail['execution_time']:.2f}秒")


async def test_agent_status():
    """测试智能体状态查询"""
    from core.framework.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

    print("\n" + "="*60)
    print("智能体状态查询")
    print("="*60)

    # 创建小诺编排者
    xiaonuo = XiaonuoOrchestrator()

    # 获取智能体状态
    status = xiaonuo.get_agent_status()

    print("\n统计信息:")
    print(f"  总智能体数: {status['statistics']['total_agents']}")
    print(f"  启用智能体: {status['statistics']['enabled']}")
    print(f"  总能力数: {status['statistics']['total_capabilities']}")
    print(f"  阶段分布: {status['statistics']['phase_distribution']}")

    print("\n智能体详情:")
    for agent_id, agent_info in status['agents'].items():
        print(f"  - {agent_id}:")
        print(f"    类型: {agent_info['type']}")
        print(f"    阶段: {agent_info['phase']}")
        print(f"    状态: {'启用' if agent_info['enabled'] else '禁用'}")
        print(f"    能力: {', '.join(agent_info['capabilities'])}")


async def test_supported_scenarios():
    """测试支持的场景列表"""
    from core.framework.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

    print("\n" + "="*60)
    print("支持的场景列表")
    print("="*60)

    # 创建小诺编排者
    xiaonuo = XiaonuoOrchestrator()

    # 获取支持的场景
    scenarios = xiaonuo.get_supported_scenarios()

    for scenario in scenarios:
        print(f"\n场景: {scenario['name']} ({scenario['scenario']})")
        print(f"  描述: {scenario['description']}")
        print(f"  关键词: {', '.join(scenario['keywords'])}")
        print(f"  需要的智能体: {', '.join(scenario['required_agents'])}")
        print(f"  执行模式: {scenario['execution_mode']}")


async def main():
    """主测试函数"""
    print("\n小娜专业智能体系统测试")
    print("=" * 60)

    # 测试场景识别
    await test_scenario_detection()

    # 测试智能体状态
    await test_agent_status()

    # 测试支持的场景
    await test_supported_scenarios()

    # 测试专利检索（需要实际的专利数据库）
    # await test_patent_search()

    # 测试创造性分析（需要实际的专利数据）
    # await test_creativity_analysis()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
