#!/usr/bin/env python3
"""
显式规划器测试脚本

测试规划引擎的核心功能:
1. 创建计划
2. 可视化计划
3. 用户批准
4. 执行计划
5. 动态调整

作者: 小诺·双鱼座
创建时间: 2025-01-05
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.planning.explicit_planner import PlanningRequest, Priority, get_explicit_planner
from core.planning.plan_visualizer import get_plan_visualizer


async def test_create_plan():
    """测试1: 创建计划"""
    print("\n" + "=" * 60)
    print("🧪 测试1: 创建计划")
    print("=" * 60)

    planner = get_explicit_planner()

    # 构建规划请求
    request = PlanningRequest(
        title="专利检索与分析",
        description="用户想要查找关于'深度学习在图像识别中的应用'的相关专利,并进行技术分析",
        context={
            "user_id": "test_user_001",
            "query": "深度学习 图像识别 专利",
            "databases": ["CN", "US", "EP", "WO"],
            "time_range": "2015-2024",
        },
        requirements=["检索相关专利至少20篇", "分析技术创新点", "识别主要申请人", "生成分析报告"],
        constraints=["只考虑发明专利", "关注中文和英文专利"],
        priority=Priority.HIGH,
    )

    # 创建计划
    result = await planner.create_plan(request)

    if result.success:
        print("✅ 计划创建成功!")
        print(f"   计划ID: {result.plan_id}")
        print(f"   步骤数: {len(result.steps)}")
        print(f"   置信度: {result.confidence_score:.1%}")
        print(f"   预估时间: {result.estimated_duration.total_seconds() / 60:.1f}分钟")
        return result.plan_id
    else:
        print(f"❌ 计划创建失败: {result.feedback}")
        return None


async def test_visualize_plan(plan_id: str):
    """测试2: 可视化计划"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 可视化计划")
    print("=" * 60)

    planner = get_explicit_planner()
    visualizer = get_plan_visualizer()

    plan = await planner.get_plan(plan_id)
    if not plan:
        print("❌ 计划不存在")
        return

    # 文本格式
    print("\n📄 文本格式:")
    print("-" * 60)
    text_viz = visualizer.to_text(plan)
    print(text_viz)

    # Mermaid格式
    print("\n📊 Mermaid流程图格式:")
    print("-" * 60)
    mermaid_viz = visualizer.to_mermaid(plan)
    print(mermaid_viz)

    # 保存到文件
    output_dir = project_root / "data" / "planning"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存Mermaid图表
    mermaid_file = output_dir / f"plan_{plan_id}_mermaid.mmd"
    with open(mermaid_file, "w", encoding="utf-8") as f:
        f.write(mermaid_viz)
    print(f"✅ Mermaid图表已保存到: {mermaid_file}")

    # 保存HTML报告
    html_viz = visualizer.to_html(plan)
    html_file = output_dir / f"plan_{plan_id}_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_viz)
    print(f"✅ HTML报告已保存到: {html_file}")


async def test_approve_plan(plan_id: str):
    """测试3: 用户批准计划"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 用户批准计划")
    print("=" * 60)

    planner = get_explicit_planner()

    # 模拟用户批准
    approved = True
    comments = "计划合理,批准执行"

    success = await planner.await_user_approval(plan_id, approved, comments)

    if success:
        print("✅ 计划已获批准")
        print(f"   用户评论: {comments}")
    else:
        print("❌ 批准失败")


async def test_execute_plan(plan_id: str):
    """测试4: 执行计划"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 执行计划")
    print("=" * 60)

    planner = get_explicit_planner()

    # 执行计划
    result = await planner.execute_plan(plan_id)

    print("\n执行结果:")
    print(f"   成功: {result['success']}")
    print(f"   完成步骤: {len(result['completed_steps'])}")
    print(f"   失败步骤: {len(result['failed_steps'])}")

    if result["completed_steps"]:
        print("\n✅ 完成的步骤:")
        for step in result["completed_steps"]:
            print(f"   - {step['name']}: {step.get('result', {})}")

    if result["failed_steps"]:
        print("\n❌ 失败的步骤:")
        for step in result["failed_steps"]:
            print(f"   - {step['name']}: {step['error']}")

    if result["final_output"]:
        print("\n📊 最终输出:")
        print(f"   {result['final_output']}")


async def test_get_status(plan_id: str):
    """测试5: 获取执行状态"""
    print("\n" + "=" * 60)
    print("🧪 测试5: 获取执行状态")
    print("=" * 60)

    planner = get_explicit_planner()

    status = await planner.get_plan_status(plan_id)

    print(f"计划ID: {status['plan_id']}")
    print(f"计划名称: {status['plan_name']}")
    print(f"状态: {status['status']}")
    print(f"批准状态: {status['approved']}")
    print(f"进度: {status['progress']:.1%}")

    print("\n步骤状态:")
    for step in status["steps"]:
        print(
            f"   {step['step_number']}. {step['name']}: {step['status']} (置信度: {step['confidence']:.1%})"
        )


async def test_api_service():
    """测试6: 启动API服务"""
    print("\n" + "=" * 60)
    print("🧪 测试6: 启动API服务")
    print("=" * 60)

    from core.planning.planning_api_service import start_planning_api

    print("\n🚀 启动规划引擎API服务...")
    print("   访问 http://localhost:8019 查看API文档")
    print("   按 Ctrl+C 停止服务")

    try:
        start_planning_api(port=8019, log_level="INFO")
    except KeyboardInterrupt:
        print("\n👋 服务已停止")


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("🧪 显式规划器测试套件")
    print("基于《智能体设计模式》标准实现")
    print("=" * 60)

    try:
        # 测试1: 创建计划
        plan_id = await test_create_plan()
        if not plan_id:
            print("\n❌ 测试失败:无法创建计划")
            return

        # 测试2: 可视化计划
        await test_visualize_plan(plan_id)

        # 测试3: 用户批准
        await test_approve_plan(plan_id)

        # 测试4: 执行计划
        await test_execute_plan(plan_id)

        # 测试5: 获取状态
        await test_get_status(plan_id)

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

        # 询问是否启动API服务
        print("\n是否启动API服务? (y/n): ", end="")
        # 在自动化测试中跳过此步骤
        # 如果想测试API服务,取消下面的注释
        # response = input().strip().lower()
        # if response == 'y':
        #     await test_api_service()

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
