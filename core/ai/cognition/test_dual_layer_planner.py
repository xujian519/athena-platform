#!/usr/bin/env python3

"""
双层规划系统测试脚本
演示如何使用 Markdown Plan + 执行引擎
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.cognition.dual_layer_planner import (
    MarkdownPlanManager,
    PlanStep,
    TaskExecutionEngine,
)


async def main():
    print("=" * 60)
    print("🚀 双层规划系统测试")
    print("=" * 60)
    print()

    # 1. 创建管理器
    print("📋 初始化管理器...")
    plan_manager = MarkdownPlanManager(storage_path=Path("plans"))
    execution_engine = TaskExecutionEngine(plan_manager)

    # 2. 创建一个示例任务计划
    task_id = "demo_task_001"
    title = "专利检索与分析任务"
    description = """
    这是一个示例任务，演示双层规划系统的功能。

    用户可以编辑生成的 Markdown Plan 文档来调整执行步骤，
    系统会自动解析并执行更新后的计划。
    """

    steps = [
        PlanStep(
            id="step_1",
            name="理解用户需求",
            description="分析用户的专利检索需求",
            agent="xiaonuo",
            estimated_time=30,
        ),
        PlanStep(
            id="step_2",
            name="执行专利检索",
            description="从专利数据库中检索相关专利",
            agent="xiaona",
            dependencies=["step_1"],
            estimated_time=120,
        ),
        PlanStep(
            id="step_3",
            name="分析检索结果",
            description="对检索到的专利进行分析和评估",
            agent="xiaona",
            dependencies=["step_2"],
            estimated_time=180,
        ),
        PlanStep(
            id="step_4",
            name="生成分析报告",
            description="生成最终的分析报告",
            agent="xiaonuo",
            dependencies=["step_3"],
            estimated_time=60,
        ),
    ]

    print(f"✅ 任务计划创建完成: {task_id}")
    print()

    # 3. 启动任务（创建 Markdown Plan 文档）
    print("📝 创建 Markdown Plan 文档...")
    plan_file = await execution_engine.start_task(
        task_id=task_id,
        title=title,
        description=description,
        steps=steps,
    )

    print(f"✅ Plan 文档已创建: {plan_file}")
    print()

    # 4. 显示生成的 Markdown 内容
    print("=" * 60)
    print("📄 生成的 Markdown Plan 内容:")
    print("=" * 60)
    with open(plan_file, encoding="utf-8") as f:
        content = f.read()
    print(content)
    print("=" * 60)
    print()

    # 5. 模拟执行步骤
    print("🔄 开始执行任务...")
    print()

    # 执行第一个步骤
    print("执行步骤 1: 理解用户需求")
    result1 = await execution_engine.execute_step(task_id, "step_1")
    print(f"  结果: {'成功' if result1['success'] else '失败'}")
    print()

    # 执行第二个步骤
    print("执行步骤 2: 执行专利检索")
    result2 = await execution_engine.execute_step(task_id, "step_2")
    print(f"  结果: {'成功' if result2['success'] else '失败'}")
    print()

    # 6. 重新加载并查看更新后的 Plan
    print("📄 查看更新后的 Plan 文档:")
    print("=" * 60)

    await execution_engine.reload_plan_from_disk(task_id)
    updated_plan = execution_engine.active_tasks.get(task_id)

    if updated_plan:
        progress = updated_plan.get_progress()
        print(f"进度: {progress['progress_percent']}%")
        print(f"已完成: {progress['completed']}/{progress['total']}")
        print()

        # 重新生成并显示更新后的内容
        with open(plan_file, encoding="utf-8") as f:
            updated_content = f.read()

        # 只显示执行步骤部分
        lines = updated_content.split("\n")
        in_steps = False
        for line in lines:
            if line.startswith("## 🎯 执行步骤"):
                in_steps = True
            if in_steps:
                print(line)
                if line.startswith("---") and in_steps:
                    break
    print("=" * 60)
    print()

    # 7. 演示从文件加载
    print("📂 演示从文件加载任务...")
    loaded_plan = await plan_manager.load_plan(task_id)

    if loaded_plan:
        print(f"✅ 任务加载成功: {loaded_plan.title}")
        print(f"   步骤数: {len(loaded_plan.steps)}")
        print(f"   状态: {loaded_plan.status.value}")
    print()

    # 8. 演示用户修改场景
    print("💡 演示用户修改场景:")
    print("   假设用户在 Markdown 文件中添加了备注")
    print()

    # 重新加载并添加用户备注
    await execution_engine.reload_plan_from_disk(task_id)
    modified_plan = execution_engine.active_tasks.get(task_id)

    if modified_plan:
        # 模拟用户修改：给步骤3添加备注
        step3 = modified_plan.get_step_by_id("step_3")
        if step3:
            step3.user_notes = "用户备注：请重点关注专利的新颖性分析"

        # 同步回文件
        await plan_manager.sync_plan(modified_plan)

        print("✅ 用户备注已同步到 Plan 文档")
        print()

    # 9. 完成所有步骤
    print("🚀 执行剩余所有步骤...")
    final_result = await execution_engine.execute_all_pending(task_id)

    print(f"  结果: {'成功' if final_result['success'] else '失败'}")
    if 'progress' in final_result:
        print(f"  最终进度: {final_result['progress']['progress_percent']}%")
    print()

    print("=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)
    print()
    print("📁 生成的文件:")
    print(f"   - {plan_file}")
    print()
    print("💡 提示:")
    print("   1. 您可以手动编辑 Markdown Plan 文件")
    print("   2. 修改步骤顺序、添加备注、调整状态")
    print("   3. 系统会自动解析并执行更新后的计划")


if __name__ == "__main__":
    asyncio.run(main())

