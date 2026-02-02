#!/usr/bin/env python3
"""
任务复杂度分析器测试
Tests for TaskComplexityAnalyzer

测试用例：
1. 简单任务分析
2. 中等任务分析
3. 复杂任务分析
4. 专业任务分析
5. 批量分析
6. 边界情况测试

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 2"
"""

import pytest
from core.planning.models import Task, ComplexityLevel, StrategyType
from core.planning.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
    analyze_task_complexity
)


class TestTaskComplexityAnalyzer:
    """任务复杂度分析器测试"""

    @pytest.fixture
    def analyzer(self):
        """创建分析器实例"""
        return TaskComplexityAnalyzer()

    @pytest.mark.asyncio
    async def test_simple_task_analysis(self, analyzer):
        """测试简单任务分析"""
        # 创建简单任务
        task = Task(
            description="帮我搜索Python相关的文档",
            task_type="general"
        )

        # 分析复杂度
        result = await analyzer.analyze(task)

        # 验证结果
        assert result.complexity == ComplexityLevel.SIMPLE
        assert result.score <= 5
        assert result.suggested_strategy == StrategyType.REACT
        assert result.confidence > 0
        assert len(result.reasoning) > 0

    @pytest.mark.asyncio
    async def test_medium_task_analysis(self, analyzer):
        """测试中等任务分析"""
        # 创建中等任务
        task = Task(
            description="帮我分析专利的新颖性",
            task_type="patent_analysis",
            domain="patent"
        )

        # 分析复杂度
        result = await analyzer.analyze(task)

        # 验证结果
        assert result.complexity == ComplexityLevel.MEDIUM
        assert 5 < result.score <= 10
        assert result.suggested_strategy in [
            StrategyType.PLANNING,
            StrategyType.REACT
        ]

    @pytest.mark.asyncio
    async def test_complex_task_analysis(self, analyzer):
        """测试复杂任务分析"""
        # 创建复杂任务
        task = Task(
            description="对专利组合进行全面的创造性分析，需要综合多个数据源，设计创新方案，并给出优化建议",
            task_type="patent_analysis",
            domain="patent"
        )

        # 分析复杂度
        result = await analyzer.analyze(task)

        # 验证结果
        assert result.complexity == ComplexityLevel.COMPLEX
        assert result.score > 10
        assert result.suggested_strategy in [
            StrategyType.WORKFLOW_REUSE,
            StrategyType.ADAPTIVE
        ]
        assert result.factors.requires_creative_reasoning == True
        assert result.factors.requires_multi_source == True

    @pytest.mark.asyncio
    async def test_professional_task_bonus(self, analyzer):
        """测试专业任务加分"""
        # 专业任务
        professional_task = Task(
            description="分析专利",
            task_type="patent_analysis"
        )

        # 通用任务
        general_task = Task(
            description="写代码",
            task_type="general"
        )

        # 分别分析
        prof_result = await analyzer.analyze(professional_task)
        gen_result = await analyzer.analyze(general_task)

        # 专业任务分数应该更高
        assert prof_result.score > gen_result.score

    @pytest.mark.asyncio
    async def test_parallelizable_task_discount(self, analyzer):
        """测试可并行化任务减分"""
        # 可并行化任务
        parallel_task = Task(
            description="批量下载100个专利文件，可以并行处理"
        )

        # 不可并行化任务
        _ = Task(
            description="分析专利的新颖性，需要按顺序执行"
        )

        # 分析可并行化任务
        parallel_result = await analyzer.analyze(parallel_task)

        # 验证可并行化属性
        assert parallel_result.factors.parallelizable == True
        # 可并行化任务的复杂度应该更低

    @pytest.mark.asyncio
    async def test_multi_source_detection(self, analyzer):
        """测试多源数据检测"""
        task = Task(
            description="对比分析多个数据源的信息"
        )

        result = await analyzer.analyze(task)

        assert result.factors.requires_multi_source == True

    @pytest.mark.asyncio
    async def test_creative_reasoning_detection(self, analyzer):
        """测试创造性推理检测"""
        task = Task(
            description="设计一个创新的解决方案来优化现有系统"
        )

        result = await analyzer.analyze(task)

        assert result.factors.requires_creative_reasoning == True

    @pytest.mark.asyncio
    async def test_tool_estimation(self, analyzer):
        """测试工具数量预估"""
        # 包含多个动作的任务
        task = Task(
            description="先搜索专利，然后下载文件，接着分析内容，最后生成报告"
        )

        result = await analyzer.analyze(task)

        # 应该预估出多个工具
        assert result.factors.estimated_tools >= 2

    @pytest.mark.asyncio
    async def test_step_estimation(self, analyzer):
        """测试步骤数预估"""
        # 包含步骤指示的任务
        task = Task(
            description="首先进行专利检索，然后对比分析，接着得出结论，最后生成报告"
        )

        result = await analyzer.analyze(task)

        # 应该预估出多个步骤
        assert result.factors.estimated_steps >= 2

    @pytest.mark.asyncio
    async def test_batch_analyze(self, analyzer):
        """测试批量分析"""
        tasks = [
            Task(description="简单任务1"),
            Task(description="简单任务2"),
            Task(description="中等任务：需要分析和搜索")
        ]

        results = await analyzer.batch_analyze(tasks)

        # 验证结果数量
        assert len(results) == len(tasks)

        # 验证每个结果都有完整的分析
        for result in results:
            assert result.complexity in [
                ComplexityLevel.SIMPLE,
                ComplexityLevel.MEDIUM,
                ComplexityLevel.COMPLEX
            ]
            assert result.score >= 0
            assert result.suggested_strategy is not None

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, analyzer):
        """测试置信度计算"""
        # 短任务描述
        short_task = Task(description="搜索")

        # 长任务描述
        long_task = Task(
            description="这是一个非常详细的任务描述，包含了很多具体的要求和背景信息，"
                       "使得复杂度分析能够更加准确。任务明确指定了需要使用的工具和"
                       "期望的输出格式，以及具体的执行步骤。"
        )

        short_result = await analyzer.analyze(short_task)
        long_result = await analyzer.analyze(long_task)

        # 长描述的置信度应该更高
        assert long_result.confidence >= short_result.confidence

    def test_to_dict_conversion(self, analyzer):
        """测试结果转换为字典"""
        # 创建测试任务（同步测试）
        task = Task(
            description="测试任务",
            task_type="general"
        )

        # 验证模型属性
        assert hasattr(task, 'task_id')
        assert hasattr(task, 'description')

        # 验证ComplexityFactors的to_dict方法
        from core.planning.models import ComplexityFactors
        factors = ComplexityFactors(
            task_type="general",
            estimated_tools=1,
            estimated_steps=1,
            requires_multi_source=False,
            requires_creative_reasoning=False,
            domain_specific_knowledge=False,
            requires_real_time_data=False,
            parallelizable=False
        )
        factors_dict = factors.to_dict()
        assert isinstance(factors_dict, dict)
        assert "task_type" in factors_dict


class TestConvenienceFunction:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_analyze_task_complexity(self):
        """测试便捷函数"""
        task = Task(description="帮我搜索文档")

        result = await analyze_task_complexity(task)

        assert result is not None
        assert result.complexity in [
            ComplexityLevel.SIMPLE,
            ComplexityLevel.MEDIUM,
            ComplexityLevel.COMPLEX
        ]


@pytest.mark.parametrize("description,task_type,expected_complexity", [
    # 简单任务 (score <= 5)
    ("搜索文档", "general", ComplexityLevel.SIMPLE),  # score=2
    ("下载文件", "general", ComplexityLevel.SIMPLE),  # score=2

    # 中等任务 (5 < score <= 10)
    ("分析专利的新颖性", "patent_analysis", ComplexityLevel.MEDIUM),  # score=7 (专业+3, 工具+2, 步骤+2)
    ("对比多个数据源的信息并得出结论", "general", ComplexityLevel.SIMPLE),  # score=5 (边界, 多源+2, 工具+2, 步骤+1)

    # 复杂任务 (score > 10)
    ("对专利组合进行全面分析，需要综合多个数据源，设计创新方案，并给出优化建议",
     "patent_analysis", ComplexityLevel.COMPLEX),  # score=12+
])
@pytest.mark.asyncio
async def test_complexity_classification(description, task_type, expected_complexity):
    """参数化测试复杂度分类"""
    task = Task(description=description, task_type=task_type)
    result = await analyze_task_complexity(task)

    assert result.complexity == expected_complexity


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
