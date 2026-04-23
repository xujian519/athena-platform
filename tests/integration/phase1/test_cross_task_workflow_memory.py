#!/usr/bin/env python3
"""
CrossTaskWorkflowMemory 核心功能测试

测试工作流模式提取、存储、检索和应用功能。

Author: Athena平台团队
Created: 2026-01-20
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.framework.memory.cross_task_workflow_memory import CrossTaskWorkflowMemory
from core.framework.memory.workflow_pattern import (
    StepType,
    TaskDomain,
    TaskTrajectory,
    WorkflowPattern,
    WorkflowStep,
)


@pytest.mark.asyncio
async def test_basic_workflow_pattern():
    """测试基本的WorkflowPattern创建"""

    print("\n" + "="*60)
    print("测试1: 基本WorkflowPattern创建")
    print("="*60)

    # 创建测试步骤
    steps = [
        WorkflowStep(
            step_id="step_1",
            name="分析权利要求",
            step_type=StepType.TOOL_USE,
            description="使用claim_analysis工具分析专利权利要求",
            action="claim_analysis",
            input_schema={"patent_id": "string"},
            output_schema={"claims": "list"}
        ),
        WorkflowStep(
            step_id="step_2",
            name="检索对比文件",
            step_type=StepType.TOOL_USE,
            description="使用patent_search工具检索对比文件",
            action="patent_search",
            input_schema={"keywords": "list"},
            output_schema={"results": "list"},
            dependencies=["step_1"]
        ),
        WorkflowStep(
            step_id="step_3",
            name="评估新颖性",
            step_type=StepType.DECISION,
            description="评估专利的新颖性",
            action="novelty_assessment",
            input_schema={"claims": "list", "results": "list"},
            output_schema={"conclusion": "string"},
            dependencies=["step_1", "step_2"]
        )
    ]

    # 创建模式
    pattern = WorkflowPattern(
        pattern_id="test_patent_novelty_001",
        name="专利新颖性分析模式",
        description="用于专利新颖性分析的workflow模式",
        task_type="PATENT_ANALYSIS",
        domain=TaskDomain.PATENT,
        steps=steps,
        success_rate=0.92,
        usage_count=10,
        total_executions=10,
        successful_executions=9,
        avg_execution_time=45.5,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    print(f"✅ 创建模式: {pattern.name}")
    print(f"   模式ID: {pattern.pattern_id}")
    print(f"   步骤数: {len(pattern.steps)}")
    print(f"   成功率: {pattern.success_rate:.2%}")
    print(f"   置信度: {pattern.get_confidence():.3f}")

    return pattern


@pytest.mark.asyncio
async def test_workflow_extractor():
    """测试WorkflowExtractor"""

    print("\n" + "="*60)
    print("测试2: WorkflowExtractor模式提取")
    print("="*60)

    from core.framework.memory.workflow_extractor import WorkflowExtractor

    # 创建测试任务轨迹 (增加步骤以满足最小模式长度)
    trajectory = TaskTrajectory(
        task_id="test_task_001",
        task_description="分析专利CN202310000000的新颖性",
        task_type="PATENT_ANALYSIS",
        domain=TaskDomain.PATENT,
        steps=[
            WorkflowStep(
                step_id="step_1",
                name="分析权利要求",
                step_type=StepType.TOOL_USE,
                description="分析专利权利要求",
                action="claim_analysis",
                input_schema={},
                output_schema={}
            ),
            WorkflowStep(
                step_id="step_2",
                name="检索对比文件",
                step_type=StepType.TOOL_USE,
                description="检索对比文件",
                action="patent_search",
                input_schema={},
                output_schema={},
                dependencies=["step_1"]
            ),
            WorkflowStep(
                step_id="step_3",
                name="对比分析",
                step_type=StepType.TOOL_USE,
                description="对比分析差异点",
                action="comparison_analysis",
                input_schema={},
                output_schema={},
                dependencies=["step_1", "step_2"]
            )
        ],
        start_time=datetime.now(),
        total_steps=3,
        execution_time=30.5,
        success=True,
        quality_score=0.85
    )

    # 创建测试任务对象
    class MockTask:
        id = "test_task_001"
        description = "分析专利CN202310000000的新颖性"
        type = "PATENT_ANALYSIS"
        domain = TaskDomain.PATENT

    task = MockTask()

    # 提取模式 (使用更小的min_pattern_length)
    extractor = WorkflowExtractor(min_pattern_length=2)
    pattern = await extractor.extract_workflow_pattern(task, trajectory, success=True)

    if pattern:
        print(f"✅ 成功提取模式: {pattern.pattern_id}")
        print(f"   模式名称: {pattern.name}")
        print(f"   步骤数: {len(pattern.steps)}")
        print(f"   描述: {pattern.description[:100]}...")
        return pattern
    else:
        print("❌ 模式提取失败")
        return None


@pytest.mark.asyncio
async def test_workflow_memory():
    """测试CrossTaskWorkflowMemory完整流程"""

    print("\n" + "="*60)
    print("测试3: CrossTaskWorkflowMemory完整流程")
    print("="*60)

    # 初始化记忆系统
    memory = CrossTaskWorkflowMemory(
        storage_path="data/workflow_memory",
        similarity_threshold=0.75
    )

    # 创建测试模式
    pattern = WorkflowPattern(
        pattern_id="test_patent_analysis_001",
        name="专利分析测试模式",
        description="用于测试的专利分析workflow模式",
        task_type="PATENT_ANALYSIS",
        domain=TaskDomain.PATENT,
        steps=[
            WorkflowStep(
                step_id="step_1",
                name="步骤1",
                step_type=StepType.TOOL_USE,
                description="测试步骤1",
                action="test_action",
                input_schema={},
                output_schema={}
            )
        ],
        success_rate=0.90,
        usage_count=5,
        avg_execution_time=30.0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # 存储模式
    await memory.store_pattern(pattern)
    print(f"✅ 模式已存储: {pattern.pattern_id}")

    # 检索相似模式
    class MockTask:
        description = "分析专利的新颖性"
        type = "PATENT_ANALYSIS"
        domain = TaskDomain.PATENT

    task = MockTask()

    results = await memory.retrieve_similar_workflows(task, top_k=3)

    print(f"✅ 检索到{len(results)}个相似模式:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.pattern.pattern_id}")
        print(f"      相似度: {result.similarity:.3f}")
        print(f"      匹配原因: {result.match_reason}")

    # 应用模式
    if results:
        execution_plan = await memory.apply_workflow_pattern(
            results[0].pattern,
            task
        )
        print("\n✅ 模式应用成功:")
        print(f"   模式名称: {execution_plan['pattern_name']}")
        print(f"   步骤数: {len(execution_plan['steps'])}")
        print(f"   预估成功率: {execution_plan['estimated_success_rate']:.2%}")
        print(f"   预估执行时间: {execution_plan['estimated_execution_time']:.1f}秒")

    # 获取统计信息
    stats = await memory.get_pattern_statistics()
    print("\n📊 记忆系统统计:")
    print(f"   总模式数: {stats['total_patterns']}")
    print(f"   平均成功率: {stats['avg_success_rate']:.2%}")
    print(f"   总使用次数: {stats['total_usage']}")

    return memory


async def main():
    """主测试函数"""

    print("\n" + "="*60)
    print("🧪 CrossTaskWorkflowMemory 测试套件")
    print("="*60)

    try:
        # 测试1: 基本模式创建
        await test_basic_workflow_pattern()

        # 测试2: 模式提取
        await test_workflow_extractor()

        # 测试3: 完整流程
        await test_workflow_memory()

        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
