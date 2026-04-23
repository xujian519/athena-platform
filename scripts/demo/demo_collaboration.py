#!/usr/bin/env python3
"""
多智能体协作演示脚本
Multi-Agent Collaboration Demo

演示多智能体协作框架的基本功能和使用方法
"""

import asyncio
import sys
from datetime import datetime
from typing import Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from integration.multi_agent_integration import (
    get_agent_status,
    get_collaboration_status,
    get_system_status,
    initialize_multi_agent_system,
    start_collaboration,
)


def print_header(title) -> Any:
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"🤖 {title}")
    print("=" * 60)


def print_separator() -> Any:
    """打印分隔线"""
    print("\n" + "-" * 40)


def show_system_status() -> Any:
    """显示系统状态"""
    print_header("系统状态概览")

    try:
        status = get_system_status()

        print("📊 智能体状态:")
        agents_info = status.get('agents', {})
        print(f"   总智能体数: {agents_info.get('total', 0)}")
        print(f"   活跃智能体: {agents_info.get('active', 0)}")

        print("\n📋 任务状态:")
        tasks_info = status.get('tasks', {})
        print(f"   总任务数: {tasks_info.get('total', 0)}")
        print(f"   已完成任务: {tasks_info.get('completed', 0)}")
        print(f"   进行中任务: {tasks_info.get('in_progress', 0)}")

        print("\n🔄 协作会话:")
        sessions_info = status.get('sessions', {})
        print(f"   活跃会话: {sessions_info.get('active', 0)}")
        print(f"   总会话数: {sessions_info.get('total', 0)}")

        print("\n💾 资源状态:")
        resources_info = status.get('resources', {})
        print(f"   总资源: {resources_info.get('total_resources', 0)}")
        print(f"   可用资源: {resources_info.get('available_resources', 0)}")
        print(f"   利用率: {resources_info.get('utilization_rate', 0):.1%}")

    except Exception as e:
        print(f"❌ 获取系统状态失败: {e}")


def show_agent_status() -> Any:
    """显示智能体状态"""
    print_header("智能体详细状态")

    agents = ['xiaonuo', 'xiaona', 'yunxi', 'xiaochen']

    for agent_name in agents:
        print(f"\n🤖 {agent_name.upper()} 智能体:")
        try:
            status = get_agent_status(agent_name)
            if status:
                print(f"   状态: {status['status']}")
                print(f"   当前负载: {status['current_load']}/{status['max_load']}")
                print(f"   能力: {', '.join(status['capabilities'])}")
            else:
                print("   状态: 不可用")
        except Exception as e:
            print(f"   ❌ 获取状态失败: {e}")


async def demo_collaboration_scenarios():
    """演示协作场景"""
    print_header("协作场景演示")

    scenarios = [
        {
            'type': 'patent_analysis_collaboration',
            'description': '专利分析协作 - 小娜主导，小诺辅助',
            'task': '分析一项新的AI技术专利，包括技术评估、市场前景分析'
        },
        {
            'type': 'project_planning_collaboration',
            'description': '项目规划协作 - 云熙目标设定，小诺战略规划',
            'task': '制定一个新的智能体开发项目计划'
        },
        {
            'type': 'comprehensive_collaboration',
            'description': '综合协作 - 全体智能体参与，小宸协调',
            'task': '设计并规划一个完整的企业级AI解决方案'
        }
    ]

    collaboration_sessions = []

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 场景 {i}: {scenario['description']}")
        print(f"   任务: {scenario['task']}")

        try:
            print("   🚀 启动协作...")
            session_id = await start_collaboration(
                scenario['type'],
                scenario['task'],
                {'demo_mode': True, 'timestamp': datetime.now().isoformat()}
            )

            if session_id:
                print(f"   ✅ 协作已启动，会话ID: {session_id}")
                collaboration_sessions.append({
                    'session_id': session_id,
                    'type': scenario['type'],
                    'description': scenario['description']
                })
            else:
                print("   ❌ 协作启动失败")

        except Exception as e:
            print(f"   ❌ 协作启动异常: {e}")

        print_separator()

    # 等待一段时间后检查协作状态
    print("\n⏱️ 等待协作执行...")
    await asyncio.sleep(2)

    # 显示协作状态
    for session in collaboration_sessions:
        print(f"\n📊 协作状态 - {session['description']}:")
        try:
            status = get_collaboration_status(session['session_id'])
            if status:
                print(f"   会话ID: {status['session_id']}")
                print(f"   状态: {status['status']}")
                print(f"   参与者: {', '.join(status['participants'])}")
                print(f"   任务状态: {status['task_status']}")
                print(f"   进度: {status.get('task_progress', 0):.1%}")
            else:
                print("   状态: 不可用")
        except Exception as e:
            print(f"   ❌ 获取状态失败: {e}")


def show_available_templates() -> Any:
    """显示可用的协作模板"""
    print_header("可用的协作模板")

    templates = {
        'patent_analysis_collaboration': {
            'name': '专利分析协作',
            'pattern': '层次协作',
            'participants': ['小娜', '小诺'],
            'coordinator': '小娜',
            'duration': '60分钟',
            'best_for': '专利技术分析、知识产权评估'
        },
        'project_planning_collaboration': {
            'name': '项目规划协作',
            'pattern': '串行协作',
            'participants': ['云熙', '小诺'],
            'coordinator': '云熙',
            'duration': '55分钟',
            'best_for': '项目计划制定、目标管理'
        },
        'comprehensive_collaboration': {
            'name': '综合协作',
            'pattern': '并行协作',
            'participants': ['小诺', '小娜', '云熙', '小宸'],
            'coordinator': '小宸',
            'duration': '50分钟',
            'best_for': '复杂项目、综合性任务'
        }
    }

    for _template_id, template_info in templates.items():
        print(f"\n📋 {template_info['name']}:")
        print(f"   协作模式: {template_info['pattern']}")
        print(f"   参与智能体: {', '.join(template_info['participants'])}")
        print(f"   协调者: {template_info['coordinator']}")
        print(f"   预估时长: {template_info['duration']}")
        print(f"   适用场景: {template_info['best_for']}")


def show_collaboration_patterns() -> Any:
    """显示协作模式说明"""
    print_header("协作模式说明")

    patterns = [
        {
            'name': '串行协作 (Sequential)',
            'description': '智能体按顺序依次完成任务，适用于有明确依赖关系的任务',
            'advantages': ['简单易控', '逻辑清晰', '质量保证'],
            'disadvantages': ['执行时间较长', '并行度低'],
            'example': '专利分析中的初步分析→战略规划→详细分析'
        },
        {
            'name': '并行协作 (Parallel)',
            'description': '多个智能体同时处理任务的不同部分，适用于可分解的独立任务',
            'advantages': ['执行速度快', '资源利用率高', '效率高'],
            'disadvantages': ['协调复杂', '可能存在资源竞争'],
            'example': '不同领域的专利分析同时进行'
        },
        {
            'name': '层次协作 (Hierarchical)',
            'description': '基于主从关系的协作，有明确的协调者和执行者角色',
            'advantages': ['管理清晰', '决策统一', '易于协调'],
            'disadvantages': ['协调者负载大', '单点风险'],
            'example': '项目管理者制定计划，执行者完成任务'
        },
        {
            'name': '共识协作 (Consensus)',
            'description': '基于投票和共识的决策协作，确保所有参与者同意',
            'advantages': ['决策质量高', '参与度高', '风险低'],
            'disadvantages': ['决策时间长', '可能无法达成一致'],
            'example': '重要决策的制定，技术方案的选择'
        }
    ]

    for pattern in patterns:
        print(f"\n🎭 {pattern['name']}:")
        print(f"   描述: {pattern['description']}")
        print(f"   优势: {', '.join(pattern['advantages'])}")
        print(f"   劣势: {', '.join(pattern['disadvantages'])}")
        print(f"   示例: {pattern['example']}")


async def main():
    """主演示函数"""
    print_header("多智能体协作框架演示")
    print("本演示将展示多智能体协作框架的主要功能和使用方法")

    try:
        # 1. 初始化系统
        print("\n🚀 正在初始化多智能体系统...")
        init_result = await initialize_multi_agent_system()
        if init_result:
            print("✅ 系统初始化成功")
        else:
            print("❌ 系统初始化失败")
            return

        # 2. 显示系统状态
        show_system_status()

        # 3. 显示智能体状态
        show_agent_status()

        # 4. 显示协作模式
        show_collaboration_patterns()

        # 5. 显示可用模板
        show_available_templates()

        # 6. 演示协作场景
        await demo_collaboration_scenarios()

        # 7. 最终状态
        print_header("演示总结")
        print("✅ 多智能体协作框架演示完成")
        print("\n🎯 主要功能:")
        print("   ✓ 智能体注册和管理")
        print("   ✓ 多种协作模式")
        print("   ✓ 任务分配和协调")
        print("   ✓ 冲突检测和解决")
        print("   ✓ 性能监控和优化")

        print("\n📈 性能特点:")
        print("   ✓ 高并发支持")
        print("   ✓ 智能资源调度")
        print("   ✓ 灵活的协作策略")
        print("   ✓ 完善的错误处理")

        print("\n🚀 应用场景:")
        print("   ✓ 专利分析项目")
        print("   ✓ 产品规划任务")
        print("   ✓ 综合研究项目")
        print("   ✓ 决策支持系统")

        print("\n💡 下一步:")
        print("   - 实施更高级的协作协议")
        print("   - 增加更多协作模式")
        print("   - 优化性能和用户体验")
        print("   - 扩展应用场景")

    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🤖 多智能体协作框架演示")
    print("=" * 60)
    print("本演示需要多智能体集成支持，请确保相关模块已正确安装")
    print()

    # 运行演示
    asyncio.run(main())
