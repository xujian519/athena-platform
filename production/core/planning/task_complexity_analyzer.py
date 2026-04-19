#!/usr/bin/env python3
"""
任务复杂度分析器
Task Complexity Analyzer

根据多个维度分析任务复杂度,为策略选择提供依据。

分析维度:
1. 任务类型 (专业任务更复杂)
2. 涉及的工具数量
3. 预估步骤数
4. 是否需要多源数据
5. 是否需要创造性推理
6. 是否需要领域知识
7. 是否需要实时数据
8. 是否可并行化

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 2"
"""

from __future__ import annotations
import logging

from .models import ComplexityAnalysis, ComplexityFactors, ComplexityLevel, StrategyType, Task

logger = logging.getLogger(__name__)


class TaskComplexityAnalyzer:
    """
    任务复杂度分析器

    根据任务的特征分析其复杂度,为自适应策略选择提供依据。

    复杂度评分规则:
    - simple: 分数 <= 5
    - medium: 5 < 分数 <= 10
    - complex: 分数 > 10

    各维度权重:
    - 任务类型: 3分 (专业任务)
    - 工具数量: 最多5分
    - 步骤数: 最多5分
    - 多源数据: 2分
    - 创造性推理: 3分
    - 领域知识: 2分
    - 实时数据: 1分
    - 可并行化: -2分 (降低复杂度)
    """

    # 复杂度阈值常量
    SIMPLE_THRESHOLD = 5
    MEDIUM_THRESHOLD = 10

    # 工具数量范围常量
    MIN_TOOLS = 1
    MAX_TOOLS = 5

    # 描述长度阈值常量
    LONG_DESCRIPTION_THRESHOLD = 200
    VERY_LONG_DESCRIPTION_THRESHOLD = 500

    # 步骤数范围常量
    MIN_STEPS = 1
    MAX_STEPS = 10

    # 分数权重常量
    PROFESSIONAL_TASK_SCORE = 3
    MULTI_SOURCE_DATA_SCORE = 2
    CREATIVE_REASONING_SCORE = 3
    DOMAIN_KNOWLEDGE_SCORE = 2
    REALTIME_DATA_SCORE = 1
    PARALLELIZABLE_SCORE = -2

    # 专业任务类型关键词
    PROFESSIONAL_TASK_TYPES = {
        "patent_analysis",
        "legal_research",
        "patent_search",
        "novelty_assessment",
        "inventive_step_analysis",
        "claim_analysis",
        "patent_mapping",
    }

    # 需要多源数据的关键词
    MULTI_SOURCE_KEYWORDS = [
        "对比",
        "综合",
        "多方",
        "多个数据源",
        "cross-source",
        "多源",
        "综合分析",
        "对比分析",
        "关联",
        "跨域",
    ]

    # 需要创造性推理的关键词
    CREATIVE_KEYWORDS = [
        "设计",
        "创新",
        "创意",
        "优化",
        "改进",
        "建议",
        "方案",
        "策略",
        "design",
        "innovate",
        "creative",
        "optimize",
    ]

    # 需要实时数据的关键词
    REALTIME_KEYWORDS = ["实时", "最新", "当前", "现在", "today", "current", "latest", "real-time"]

    # 可并行化的关键词
    PARALLEL_KEYWORDS = ["批量", "并行", "同时", "独立", "batch", "parallel", "simultaneous"]

    def __init__(self, use_llm: bool = False):
        """
        初始化复杂度分析器

        Args:
            use_llm: 是否使用LLM辅助分析 (默认False,使用规则)
        """
        self.use_llm = use_llm

        # 工具预估关键词映射
        self.tool_keywords = {
            "search": ["搜索", "检索", "查询", "search", "find", "query"],
            "analyze": ["分析", "研究", "analyze", "study", "research"],
            "download": ["下载", "获取", "download", "fetch", "get"],
            "compare": ["对比", "比较", "compare", "contrast"],
            "summarize": ["总结", "概括", "summarize", "abstract"],
            "validate": ["验证", "检查", "validate", "verify", "check"],
            "generate": ["生成", "创建", "generate", "create"],
            "transform": ["转换", "变换", "transform", "convert"],
        }

        logger.info("🧠 任务复杂度分析器初始化完成")
        logger.info(f"   LLM辅助: {'启用' if use_llm else '禁用'}")

    async def analyze(self, task: Task) -> ComplexityAnalysis:
        """
        分析任务复杂度

        Args:
            task: 任务对象

        Returns:
            ComplexityAnalysis: 复杂度分析结果
        """
        logger.info(f"🔍 开始分析任务复杂度: {task.task_id}")
        logger.info(f"   任务描述: {task.description[:100]}...")

        # 1. 分析复杂度因素
        factors = await self._analyze_factors(task)

        # 2. 计算复杂度分数
        score = self._calculate_score(factors)

        # 3. 确定复杂度级别
        complexity = self._determine_level(score)

        # 4. 确定建议策略
        strategy = self._suggest_strategy(complexity, factors)

        # 5. 生成分析理由
        reasoning = self._generate_reasoning(factors, score, complexity, strategy)

        # 6. 计算置信度
        confidence = self._calculate_confidence(task)

        result = ComplexityAnalysis(
            task_id=task.task_id,
            complexity=complexity,
            score=score,
            confidence=confidence,
            factors=factors,
            reasoning=reasoning,
            suggested_strategy=strategy,
        )

        logger.info(f"✅ 复杂度分析完成: {complexity.value} (分数: {score:.1f})")
        logger.info(f"   建议策略: {strategy.value}")
        logger.info(f"   置信度: {confidence:.2%}")

        return result

    async def _analyze_factors(self, task: Task) -> ComplexityFactors:
        """分析复杂度因素"""
        description_lower = task.description.lower()

        # 1. 任务类型
        task_type = task.task_type
        is_professional = task_type in self.PROFESSIONAL_TASK_TYPES

        # 2. 预估工具数量
        estimated_tools = self._estimate_tools(task.description)

        # 3. 预估步骤数
        estimated_steps = self._estimate_steps(task.description)

        # 4. 是否需要多源数据
        requires_multi_source = any(kw in description_lower for kw in self.MULTI_SOURCE_KEYWORDS)

        # 5. 是否需要创造性推理
        requires_creative = any(kw in description_lower for kw in self.CREATIVE_KEYWORDS)

        # 6. 是否需要领域知识
        domain_specific = is_professional

        # 7. 是否需要实时数据
        requires_realtime = any(kw in description_lower for kw in self.REALTIME_KEYWORDS)

        # 8. 是否可并行化
        parallelizable = any(kw in description_lower for kw in self.PARALLEL_KEYWORDS)

        return ComplexityFactors(
            task_type=task_type,
            estimated_tools=estimated_tools,
            estimated_steps=estimated_steps,
            requires_multi_source=requires_multi_source,
            requires_creative_reasoning=requires_creative,
            domain_specific_knowledge=domain_specific,
            requires_real_time_data=requires_realtime,
            parallelizable=parallelizable,
        )

    def _estimate_tools(self, description: str) -> int:
        """
        预估需要的工具数量

        基于任务描述中识别的动作关键词
        """
        description_lower = description.lower()
        tools_found = set()

        for tool_type, keywords in self.tool_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    tools_found.add(tool_type)
                    break

        # 基础工具数量
        count = len(tools_found)

        # 根据任务长度调整
        if len(description) > self.LONG_DESCRIPTION_THRESHOLD:
            count += 1
        if len(description) > self.VERY_LONG_DESCRIPTION_THRESHOLD:
            count += 1

        # 最少MIN_TOOLS个工具,最多MAX_TOOLS个
        return max(self.MIN_TOOLS, min(count, self.MAX_TOOLS))

    def _estimate_steps(self, description: str) -> int:
        """
        预估步骤数

        基于任务描述的复杂度和长度
        """
        # 基础步骤
        steps = self.MIN_STEPS

        # 检测步骤关键词
        step_indicators = [
            "然后",
            "接着",
            "之后",
            "最后",
            "首先",
            "then",
            "next",
            "after",
            "finally",
            "first",
            "步骤",
            "step",
        ]

        for indicator in step_indicators:
            if indicator in description.lower():
                steps += 1

        # 根据描述长度调整
        if len(description) > 100:
            steps += 1
        if len(description) > 300:
            steps += 1
        if len(description) > self.VERY_LONG_DESCRIPTION_THRESHOLD:
            steps += 1

        # 最少MIN_STEPS步,最多MAX_STEPS步
        return max(self.MIN_STEPS, min(steps, self.MAX_STEPS))

    def _calculate_score(self, factors: ComplexityFactors) -> float:
        """
        计算复杂度分数

        评分规则:
        - 任务类型: 专业任务 +PROFESSIONAL_TASK_SCORE
        - 工具数量: 每个工具 +1 (最多+MAX_TOOLS)
        - 步骤数: 每步 +1 (最多+MAX_STEPS)
        - 多源数据: +MULTI_SOURCE_DATA_SCORE
        - 创造性推理: +CREATIVE_REASONING_SCORE
        - 领域知识: +DOMAIN_KNOWLEDGE_SCORE
        - 实时数据: +REALTIME_DATA_SCORE
        - 可并行化: +PARALLELIZABLE_SCORE (降低复杂度)
        """
        score = 0.0

        # 任务类型
        if factors.task_type in self.PROFESSIONAL_TASK_TYPES:
            score += self.PROFESSIONAL_TASK_SCORE

        # 工具数量
        score += min(factors.estimated_tools, self.MAX_TOOLS)

        # 步骤数
        score += min(factors.estimated_steps, self.MAX_STEPS)

        # 多源数据
        if factors.requires_multi_source:
            score += self.MULTI_SOURCE_DATA_SCORE

        # 创造性推理
        if factors.requires_creative_reasoning:
            score += self.CREATIVE_REASONING_SCORE

        # 领域知识
        if factors.domain_specific_knowledge:
            score += self.DOMAIN_KNOWLEDGE_SCORE

        # 实时数据
        if factors.requires_real_time_data:
            score += self.REALTIME_DATA_SCORE

        # 可并行化 (降低复杂度)
        if factors.parallelizable:
            score += self.PARALLELIZABLE_SCORE

        # 确保分数非负
        return max(0.0, score)

    def _determine_level(self, score: float) -> ComplexityLevel:
        """根据分数确定复杂度级别"""
        if score <= self.SIMPLE_THRESHOLD:
            return ComplexityLevel.SIMPLE
        elif score <= self.MEDIUM_THRESHOLD:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.COMPLEX

    def _suggest_strategy(
        self, complexity: ComplexityLevel, factors: ComplexityFactors
    ) -> StrategyType:
        """
        建议执行策略

        策略选择逻辑:
        - simple: ReAct (快速响应)
        - medium: Planning (显式规划)
        - complex: MLMP (多层级规划)
        """
        if complexity == ComplexityLevel.SIMPLE:
            # 简单任务用ReAct
            return StrategyType.REACT
        elif complexity == ComplexityLevel.MEDIUM:
            # 中等任务用Planning
            return StrategyType.PLANNING
        else:
            # 复杂任务需要更复杂的策略
            if factors.domain_specific_knowledge:
                return StrategyType.WORKFLOW_REUSE
            else:
                return StrategyType.ADAPTIVE

    def _generate_reasoning(
        self,
        factors: ComplexityFactors,
        score: float,
        complexity: ComplexityLevel,
        strategy: StrategyType,
    ) -> str:
        """生成分析理由"""
        reasons = []

        # 任务类型
        if factors.task_type in self.PROFESSIONAL_TASK_TYPES:
            reasons.append(f"专业任务类型({factors.task_type}) +3")

        # 工具和步骤
        reasons.append(f"预估需要{factors.estimated_tools}个工具 +{factors.estimated_tools}")
        reasons.append(f"预估{factors.estimated_steps}个步骤 +{factors.estimated_steps}")

        # 特殊需求
        if factors.requires_multi_source:
            reasons.append("需要多源数据 +2")
        if factors.requires_creative_reasoning:
            reasons.append("需要创造性推理 +3")
        if factors.domain_specific_knowledge:
            reasons.append("需要领域知识 +2")
        if factors.requires_real_time_data:
            reasons.append("需要实时数据 +1")
        if factors.parallelizable:
            reasons.append("可并行化 -2")

        # 总结
        reasoning = f"复杂度分析: {', '.join(reasons)} = {score:.1f}分\n"
        reasoning += f"判定为{complexity.value}级别,建议使用{strategy.value}策略"

        return reasoning

    def _calculate_confidence(self, task: Task) -> float:
        """
        计算分析置信度

        置信度影响因素:
        - 任务描述长度 (越长越准确)
        - 是否有明确的任务类型
        - 是否有领域信息
        """
        confidence = 0.7  # 基础置信度

        # 任务描述长度
        if len(task.description) > 100:
            confidence += 0.1
        if len(task.description) > 300:
            confidence += 0.1

        # 明确的任务类型
        if task.task_type and task.task_type != "general":
            confidence += 0.05

        # 有领域信息
        if task.domain:
            confidence += 0.05

        return min(confidence, 1.0)

    async def batch_analyze(self, tasks: list[Task]) -> list[ComplexityAnalysis]:
        """批量分析任务复杂度"""
        results = []
        for task in tasks:
            result = await self.analyze(task)
            results.append(result)
        return results


# 便捷函数
async def analyze_task_complexity(task: Task) -> ComplexityAnalysis:
    """
    便捷的任务复杂度分析函数

    Args:
        task: 任务对象

    Returns:
        ComplexityAnalysis: 复杂度分析结果

    Example:
        >>> from core.planning.models import Task
        >>> result = await analyze_task_complexity(
        ...     Task(description="分析专利的新颖性")
        ... )
        >>> print(result.complexity)
        ComplexityLevel.MEDIUM
    """
    analyzer = TaskComplexityAnalyzer()
    return await analyzer.analyze(task)


__all__ = ["TaskComplexityAnalyzer", "analyze_task_complexity"]
