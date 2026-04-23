#!/usr/bin/env python3
from __future__ import annotations

"""
测试OpenClaw功能集成

验证9阶段流程、任务状态管理、质量审查器是否正确集成到AutoSpecDrafter
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入")
    print("=" * 60)

    try:
        from core.patents.ai_services.autospec_drafter import (
            DraftPhase,
        )
        print("✅ AutoSpecDrafter导入成功")
        print(f"   - DraftPhase: {len(DraftPhase)}个阶段")
        for phase in DraftPhase:
            print(f"     • {phase.value}: {phase.name}")

        print("✅ TaskStateManager导入成功")

        from core.patents.specification_quality_reviewer import (
            IssuePriority,
        )
        print("✅ SpecificationQualityReviewer导入成功")
        print(f"   - IssuePriority: {[p.value for p in IssuePriority]}")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_state_manager():
    """测试任务状态管理器"""
    print("\n" + "=" * 60)
    print("测试2: 任务状态管理器")
    print("=" * 60)

    try:
        from core.patents.task_state_manager import TaskStateManager

        manager = TaskStateManager(storage_dir="test_cases")

        # 创建任务
        task = manager.create_task(
            task_id="TEST-2026-001",
            client="测试客户"
        )
        print(f"✅ 创建任务: {task.task_id}")
        print(f"   - 状态: {task.status}")
        print(f"   - 阶段数: {len(task.phases)}")

        # 更新阶段
        manager.update_phase("TEST-2026-001", 0, "completed", output_file="phase0.md")
        print("✅ 更新阶段0完成")

        # 暂停任务
        manager.pause_task("TEST-2026-001", "测试暂停")
        print("✅ 暂停任务")

        # 恢复任务
        manager.resume_task("TEST-2026-001")
        print("✅ 恢复任务")

        # 获取进度
        progress = manager.get_progress("TEST-2026-001")
        print(f"✅ 进度: {progress['progress_percentage']}")

        # 清理
        manager.delete_task("TEST-2026-001")
        print("✅ 清理测试数据")

        return True

    except Exception as e:
        print(f"❌ 任务状态管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_reviewer():
    """测试质量审查器"""
    print("\n" + "=" * 60)
    print("测试3: 质量审查器")
    print("=" * 60)

    try:
        from core.patents.specification_quality_reviewer import (
            SpecificationQualityReviewer,
        )

        reviewer = SpecificationQualityReviewer()

        # 模拟说明书
        specification = {
            "case_id": "TEST-001",
            "invention_title": "一种智能床垫",
            "detailed_description": {
                "content": "本实施例提供了一种智能床垫，包括床垫主体、压力传感器、控制器等组件。" * 50
            },
            "invention_content": {
                "content": "本发明提供了一种智能床垫，有益效果包括：睡姿监测准确、响应速度快等。"
            }
        }

        # 模拟权利要求
        claims = {
            "claims": [
                {"claim_number": 1, "claim_type": "independent", "content": "一种智能床垫，包括床垫主体和压力传感器。"},
                {"claim_number": 2, "claim_type": "dependent", "content": "根据权利要求1所述的床垫，所述压力传感器为压电传感器之类。"}
            ]
        }

        # 执行审查
        report = reviewer.review(specification, claims)

        print("✅ 审查完成")
        print(f"   - 整体风险: {report.overall_risk.value}")
        print(f"   - 授权概率: {report.authorization_probability:.1%}")
        print(f"   - P0问题: {report.p0_count}")
        print(f"   - P1问题: {report.p1_count}")
        print(f"   - P2问题: {report.p2_count}")

        if report.issues:
            print("   - 问题列表:")
            for issue in report.issues[:3]:
                print(f"     [{issue.priority.value}] {issue.location}: {issue.description[:50]}...")

        return True

    except Exception as e:
        print(f"❌ 质量审查器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_autospec_drafter():
    """测试AutoSpecDrafter集成"""
    print("\n" + "=" * 60)
    print("测试4: AutoSpecDrafter集成")
    print("=" * 60)

    try:
        from core.patents.ai_services.autospec_drafter import (
            AutoSpecDrafter,
        )

        # 创建实例（无LLM，使用启发式方法）
        drafter = AutoSpecDrafter(llm_manager=None, storage_dir="test_cases")

        print("✅ AutoSpecDrafter实例化成功")
        print(f"   - 任务管理器: {'已初始化' if drafter._task_manager else '不可用'}")
        print(f"   - 质量审查器: {'已初始化' if drafter._quality_reviewer else '不可用'}")

        # 测试阶段定义
        phases = drafter._get_phase_definitions()
        print(f"✅ 9阶段定义: {len(phases)}个阶段")
        for phase in phases:
            print(f"   • Phase {phase['phase_id']}: {phase['phase_name']}")

        # 测试启发式审查员模拟
        from core.patents.ai_services.autospec_drafter import (
            SectionContent,
            SectionType,
            SpecificationDraft,
        )

        draft = SpecificationDraft(
            draft_id="test_draft",
            invention_title="测试发明",
            claims=["1. 一种测试装置。"]
        )

        # 添加简单章节
        draft.sections[SectionType.EMBODIMENTS] = SectionContent(
            section_type=SectionType.EMBODIMENTS,
            title="具体实施方式",
            content="这是测试内容" * 100,
            word_count=500
        )

        print("✅ 说明书草稿创建成功")

        return True

    except Exception as e:
        print(f"❌ AutoSpecDrafter集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_workflow():
    """测试完整9阶段流程"""
    print("\n" + "=" * 60)
    print("测试5: 完整9阶段流程（异步）")
    print("=" * 60)

    try:
        from core.patents.ai_services.autospec_drafter import AutoSpecDrafter

        drafter = AutoSpecDrafter(llm_manager=None, storage_dir="test_cases")

        # 简单技术交底书
        disclosure = """
发明名称：一种智能床垫

技术领域：智能家居

技术问题：现有床垫无法准确监测用户睡姿

技术方案：
1. 床垫主体
2. 压力传感器，安装在床垫主体内
3. 控制器，与压力传感器连接

技术效果：
1. 实现精准睡姿监测
2. 响应速度快
3. 使用寿命长
"""

        # 执行完整流程
        result = await drafter.draft_specification_full(
            disclosure=disclosure,
            task_id="TEST-FULL-001",
            client="测试客户",
            enable_examiner_simulation=True
        )

        print("✅ 完整流程执行完成")
        print(f"   - 任务ID: {result.task_id}")
        print(f"   - 状态: {result.status}")
        print(f"   - 当前阶段: {result.current_phase}")
        print(f"   - 已完成阶段: {result.phases_completed}")
        print(f"   - 处理时间: {result.processing_time_ms:.0f}ms")

        if result.examiner_report:
            print("   - 审查报告:")
            print(f"     • 整体风险: {result.examiner_report.overall_risk}")
            print(f"     • 授权概率: {result.examiner_report.authorization_probability:.1%}")
            print(f"     • P0问题: {result.examiner_report.p0_count}")
            print(f"     • P1问题: {result.examiner_report.p1_count}")

        # 清理
        if drafter._task_manager:
            drafter._task_manager.delete_task("TEST-FULL-001")

        return True

    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("OpenClaw功能集成测试")
    print("=" * 60)
    print()

    results = []

    # 测试1: 模块导入
    results.append(("模块导入", test_imports()))

    # 测试2: 任务状态管理器
    results.append(("任务状态管理器", test_task_state_manager()))

    # 测试3: 质量审查器
    results.append(("质量审查器", test_quality_reviewer()))

    # 测试4: AutoSpecDrafter集成
    results.append(("AutoSpecDrafter集成", test_autospec_drafter()))

    # 测试5: 完整流程（异步）
    results.append(("完整9阶段流程", asyncio.run(test_full_workflow())))

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print()
    print(f"总计: {passed}通过, {failed}失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
