#!/usr/bin/env python3
"""
智能体记忆系统集成演示

展示统一记忆系统与智能体的集成功能：
1. BaseAgent记忆系统方法
2. 小娜智能体记忆集成
3. 小诺编排者记忆集成
"""

import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.framework.agents.base_agent import BaseAgent
from core.framework.memory.unified_memory_system import MemoryType, MemoryCategory


def demo_base_agent_memory():
    """演示BaseAgent记忆系统功能"""
    print("=" * 60)
    print("演示1: BaseAgent记忆系统功能")
    print("=" * 60)

    # 创建临时项目目录
    temp_dir = tempfile.mkdtemp()
    print(f"\n📁 创建临时项目: {temp_dir}")

    # 创建一个具体的智能体类用于演示
    class DemoAgent(BaseAgent):
        def process(self, input_text: str, **_kwargs  # noqa: ARG001) -> str:
            return f"处理完成: {input_text}"

    try:
        # 创建带记忆的智能体
        agent = DemoAgent(
            name="demo_agent",
            role="演示智能体",
            project_path=temp_dir
        )

        print(f"\n✅ 智能体创建成功")
        print(f"   - 名称: {agent.name}")
        print(f"   - 记忆系统启用: {agent._memory_enabled}")

        # 保存记忆
        print(f"\n💾 保存记忆...")
        agent.save_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "demo_key",
            "# 演示项目\n\n这是一个演示项目。"
        )
        print(f"   ✅ 记忆已保存")

        # 加载记忆
        print(f"\n📖 加载记忆...")
        content = agent.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "demo_key"
        )
        print(f"   ✅ 记忆内容: {content[:50]}...")

        # 保存工作历史
        print(f"\n📝 保存工作历史...")
        agent.save_work_history(
            task="演示任务",
            result="任务完成",
            status="success"
        )
        print(f"   ✅ 工作历史已保存")

        # 搜索记忆
        print(f"\n🔍 搜索记忆...")
        results = agent.search_memory("演示", limit=10)
        print(f"   ✅ 找到 {len(results)} 条相关记忆")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n🧹 清理临时目录")


def demo_xiaona_agent():
    """演示小娜智能体记忆集成"""
    print("\n" + "=" * 60)
    print("演示2: 小娜智能体记忆集成")
    print("=" * 60)

    try:
        from core.framework.agents.xiaona_agent_with_unified_memory import XiaonaAgentWithMemory

        # 创建临时项目目录
        temp_dir = tempfile.mkdtemp()
        print(f"\n📁 创建临时项目: {temp_dir}")

        try:
            # 创建小娜智能体
            xiaona = XiaonaAgentWithMemory(
                name="xiaona",
                role="专利法律专家",
                project_path=temp_dir
            )

            print(f"\n✅ 小娜智能体创建成功")
            print(f"   - 学习历史记录数: {len(xiaona.learning_history)}")

            # 处理任务
            print(f"\n🔬 处理分析任务...")
            result = xiaona.process("分析专利CN123456789A的创造性")
            print(f"   ✅ 分析完成")
            print(f"   - 结果: {result[:100]}...")

            # 更新学习洞察
            print(f"\n🧠 更新学习洞察...")
            xiaona.update_insights(
                insight="创造性分析需要考虑现有技术的差异",
                category="patent_analysis"
            )
            print(f"   ✅ 学习洞察已更新")
            print(f"   - 学习历史记录数: {len(xiaona.learning_history)}")

            # 查看学习摘要
            print(f"\n📊 学习摘要:")
            summary = xiaona.get_learning_summary()
            print(f"   {summary[:200]}...")

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
            print(f"\n🧹 清理临时目录")

    except ImportError as e:
        print(f"\n⚠️ 小娜智能体模块导入失败: {e}")


def demo_xiaonuo_orchestrator():
    """演示小诺编排者记忆集成"""
    print("\n" + "=" * 60)
    print("演示3: 小诺编排者记忆集成")
    print("=" * 60)

    try:
        from core.framework.agents.xiaonuo_orchestrator_with_memory import XiaonuoOrchestratorWithMemory

        # 创建临时项目目录
        temp_dir = tempfile.mkdtemp()
        print(f"\n📁 创建临时项目: {temp_dir}")

        try:
            # 创建小诺编排者
            xiaonuo = XiaonuoOrchestratorWithMemory(
                name="xiaonuo",
                role="智能体编排者",
                project_path=temp_dir
            )

            print(f"\n✅ 小诺编排者创建成功")
            print(f"   - 编排历史记录数: {len(xiaonuo.orchestration_history)}")

            # 处理任务
            print(f"\n🎯 处理编排任务...")
            result = xiaonuo.process("帮我分析专利CN123456789A的创造性")
            print(f"   ✅ 编排完成")
            print(f"   - 结果: {result[:100]}...")

            # 查看编排统计
            print(f"\n📊 编排统计:")
            stats = xiaonuo.get_orchestration_statistics()
            print(f"   - 总次数: {stats['total']}")
            print(f"   - 成功率: {stats['success_rate']}")
            print(f"   - 平均时间: {stats['avg_time']}")

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
            print(f"\n🧹 清理临时目录")

    except ImportError as e:
        print(f"\n⚠️ 小诺编排者模块导入失败: {e}")


def demo_memory_persistence():
    """演示记忆持久化"""
    print("\n" + "=" * 60)
    print("演示4: 记忆持久化")
    print("=" * 60)

    # 创建临时项目目录
    temp_dir = tempfile.mkdtemp()
    print(f"\n📁 创建临时项目: {temp_dir}")

    # 创建一个具体的智能体类用于演示
    class DemoAgent(BaseAgent):
        def process(self, input_text: str, **_kwargs  # noqa: ARG001) -> str:
            return f"处理完成: {input_text}"

    try:
        # 第一个智能体保存记忆
        print(f"\n💾 智能体1保存记忆...")
        agent1 = DemoAgent(
            name="agent1",
            role="第一个智能体",
            project_path=temp_dir
        )
        agent1.save_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "persistent_key",
            "这条记忆应该被持久化"
        )
        print(f"   ✅ 记忆已保存")

        # 第二个智能体加载记忆
        print(f"\n📖 智能体2加载记忆...")
        agent2 = DemoAgent(
            name="agent2",
            role="第二个智能体",
            project_path=temp_dir
        )
        content = agent2.load_memory(
            MemoryType.PROJECT,
            MemoryCategory.PROJECT_CONTEXT,
            "persistent_key"
        )
        print(f"   ✅ 记忆已加载")
        print(f"   - 内容: {content}")

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n🧹 清理临时目录")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("智能体记忆系统集成演示")
    print("=" * 60)

    try:
        # 演示1: BaseAgent记忆系统
        demo_base_agent_memory()

        # 演示2: 小娜智能体
        demo_xiaona_agent()

        # 演示3: 小诺编排者
        demo_xiaonuo_orchestrator()

        # 演示4: 记忆持久化
        demo_memory_persistence()

        print("\n" + "=" * 60)
        print("✅ 所有演示完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
