#!/usr/bin/env python3

"""
双层规划系统增强版测试
演示所有新功能：超时处理、并行执行、执行历史等
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.cognition.dual_layer_planner_v2 import (
    ExecutionMode,
    MarkdownPlanManager,
    PlanStep,
    TaskExecutionEngine,
)


# 模拟智能体响应
class MockResponse:
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data or {}
        self.error = error


# 模拟智能体
class MockAgent:
    """模拟智能体"""

    def __init__(self, name: str, delay: float = 1.0):
        self.name = name
        self.delay = delay

    async def process(self, request):
        """模拟处理请求"""
        await asyncio.sleep(self.delay)
        return MockResponse(
            success=True,
            data={
                "agent": self.name,
                "action": request.action,
                "result": f"由 {self.name} 处理完成",
            },
        )


async def main():
    print("=" * 70)
    print("🚀 双层规划系统增强版 v2.0 - 功能演示")
    print("=" * 70)
    print()

    # 1. 创建管理器和执行引擎
    print("📋 初始化系统...")
    plan_manager = MarkdownPlanManager(storage_path=Path("plans"))
    execution_engine = TaskExecutionEngine(plan_manager)

    # 注册模拟智能体
    xiaonuo = MockAgent("xiaonuo", delay=0.5)
    xiaona = MockAgent("xiaona", delay=1.0)

    execution_engine.register_agent("xiaonuo", xiaonuo)
    execution_engine.register_agent("xiaona", xiaona)

    print("✅ 系统初始化完成")
    print()

    # 2. 创建测试任务（包含并行步骤）
    task_id = "enhanced_demo_001"
    title = "专利分析增强任务"
    description = """
    演示双层规划系统的增强功能：
    1. 并行执行多个独立步骤
    2. 超时处理
    3. 执行历史记录
    4. 自动重试
    """

    steps = [
        # 步骤1：准备工作
        PlanStep(
            id="step_1",
            name="收集需求信息",
            description="收集用户的专利分析需求",
            agent="xiaonuo",
            action="collect",
            estimated_time=30,
            can_parallel=False,
        ),
        # 步骤2-4：可以并行的检索任务
        PlanStep(
            id="step_2a",
            name="检索中文专利",
            description="从中文数据库检索相关专利",
            agent="xiaona",
            action="search_cn",
            estimated_time=60,
            dependencies=["step_1"],
            can_parallel=True,
        ),
        PlanStep(
            id="step_2b",
            name="检索英文专利",
            description="从英文数据库检索相关专利",
            agent="xiaona",
            action="search_en",
            estimated_time=60,
            dependencies=["step_1"],
            can_parallel=True,
        ),
        PlanStep(
            id="step_2c",
            name="检索专利家族",
            description="检索专利家族信息",
            agent="xiaona",
            action="search_family",
            estimated_time=45,
            dependencies=["step_1"],
            can_parallel=True,
        ),
        # 步骤5：合并结果
        PlanStep(
            id="step_3",
            name="合并检索结果",
            description="合并来自不同来源的检索结果",
            agent="xiaonuo",
            action="merge",
            estimated_time=30,
            dependencies=["step_2a", "step_2b", "step_2c"],
        ),
        # 步骤6：最终分析
        PlanStep(
            id="step_4",
            name="生成分析报告",
            description="生成最终的分析报告",
            agent="xiaona",
            action="report",
            estimated_time=60,
            dependencies=["step_3"],
        ),
    ]

    print(f"✅ 任务计划创建完成: {task_id}")
    print(f"   - 总步骤数: {len(steps)}")
    print("   - 可并行步骤: 3个 (步骤2a, 2b, 2c)")
    print()

    # 3. 创建任务
    print("📝 创建 Markdown Plan 文档...")
    plan_file = await execution_engine.start_task(
        task_id=task_id,
        title=title,
        description=description,
        steps=steps,
        execution_mode=ExecutionMode.PARALLEL,
    )

    print(f"✅ Plan 文档已创建: {plan_file}")
    print()

    # 4. 显示原始计划
    print("=" * 70)
    print("📄 原始计划内容:")
    print("=" * 70)
    with open(plan_file, encoding="utf-8") as f:
        content = f.read()
    # 只显示关键部分
    lines = content.split("\n")
    in_relevant_section = False
    for line in lines:
        if line.startswith("# 📋") or line.startswith("**任务ID**") or \
           line.startswith("**状态**") or line.startswith("**执行模式**"):
            in_relevant_section = True
        if line.startswith("## 🎯 执行步骤"):
            in_relevant_section = True
        if in_relevant_section:
            print(line)
        if line.startswith("---") and "执行步骤" in str(lines):
            if lines[lines.index(line) - 1].startswith("## 🎯"):
                continue
            in_relevant_section = False
    print("=" * 70)
    print()

    # 5. 演示功能
    print("🎯 功能演示:")
    print()

    # 功能1：单步执行
    print("1️⃣  单步执行演示:")
    print("-" * 40)

    result = await execution_engine.execute_step(task_id, "step_1")
    print(f"   步骤1执行结果: {'✅ 成功' if result['success'] else '❌ 失败'}")
    if result.get('success'):
        print(f"   耗时: {result.get('duration', 0):.2f}秒")
    print()

    # 功能2：并行执行
    print("2️⃣  并行执行演示:")
    print("-" * 40)
    print("   并行执行步骤 2a, 2b, 2c...")

    parallel_steps = ["step_2a", "step_2b", "step_2c"]
    start_time = asyncio.get_event_loop().time()

    # 并行执行
    tasks = [execution_engine.execute_step(task_id, sid) for sid in parallel_steps]
    results = await asyncio.gather(*tasks)

    elapsed = asyncio.get_event_loop().time() - start_time

    success_count = sum(1 for r in results if r['success'])
    print(f"   并行执行完成: {success_count}/{len(results)} 成功")
    print(f"   总耗时: {elapsed:.2f}秒 (顺序执行约需 {3 * 1.0:.2f}秒)")
    print()

    # 功能3：查看执行历史
    print("3️⃣  执行历史演示:")
    print("-" * 40)

    await execution_engine.reload_plan_from_disk(task_id)
    plan = execution_engine.active_tasks.get(task_id)

    if plan and plan.execution_history:
        print(f"   执行记录数: {len(plan.execution_history)}")
        print()
        print("   最近执行记录:")
        for record in plan.execution_history[-5:]:
            status_value = record.status.value if hasattr(record.status, 'value') else record.status
            status_icon = {
                "completed": "✅",
                "failed": "❌",
                "in_progress": "🔄",
            }.get(status_value, "⏸️")

            print(f"   {status_icon} {record.step_name}")
            print(f"      状态: {status_value}")
            print(f"      耗时: {record.duration:.2f}秒")
            if record.result:
                print(f"      结果: {record.result[:50]}...")
    print()

    # 功能4：完成剩余步骤
    print("4️⃣  完成剩余步骤:")
    print("-" * 40)

    result = await execution_engine.execute_all_pending(task_id, stop_on_error=False)

    progress = result.get('progress', {})
    print(f"   任务完成: {progress.get('progress_percent', 0)}%")
    print(f"   成功: {progress.get('completed', 0)}/{progress.get('total', 0)}")
    print(f"   失败: {progress.get('failed', 0)}")
    print()

    # 5. 显示最终计划
    print("=" * 70)
    print("📄 最终计划状态:")
    print("=" * 70)

    await execution_engine.reload_plan_from_disk(task_id)
    final_plan = execution_engine.active_tasks.get(task_id)

    if final_plan:
        with open(plan_file, encoding="utf-8") as f:
            final_content = f.read()

        # 显示进度表
        lines = final_content.split("\n")
        in_progress_section = False
        for line in lines:
            if line.startswith("## 📊 执行进度"):
                in_progress_section = True
            if in_progress_section:
                print(line)
                if line.startswith("---"):
                    break
    print()

    # 6. 功能列表总结
    print("=" * 70)
    print("🎉 双层规划系统增强版功能总结")
    print("=" * 70)
    print()
    print("✅ 已实现功能:")
    print("   1. Markdown Plan 文档生成和解析")
    print("   2. 步骤状态追踪 (7种状态)")
    print("   3. 依赖关系管理")
    print("   4. 并行执行支持")
    print("   5. 超时处理")
    print("   6. 自动重试机制")
    print("   7. 执行历史记录")
    print("   8. 进度回调")
    print("   9. 真实智能体集成")
    print("   10. 用户可编辑 Plan 文档")
    print()
    print("📁 生成文件:")
    print(f"   - {plan_file}")
    print(f"   - {plan_file.replace('.md', '_history.json')}")
    print()
    print("💡 使用提示:")
    print("   1. 可以直接编辑 .md 文件来修改计划")
    print("   2. 系统会自动解析并执行更新后的计划")
    print("   3. 执行历史保存在 _history.json 文件中")
    print("   4. 支持通过 API 控制任务执行")


if __name__ == "__main__":
    asyncio.run(main())

