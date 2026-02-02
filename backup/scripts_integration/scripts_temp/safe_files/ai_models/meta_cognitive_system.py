#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元认知系统 - 基于高级问题解决框架的认知升级
Meta-Cognitive System - Cognitive Enhancement Based on Advanced Problem-Solving Framework
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from enhanced_reasoning_engine import (
    EnhancedReasoningEngine,
    ReasoningDepth,
    ThinkingMode,
)
from xiaonuo_enhanced_system import XiaoNuoEnhancedSystem

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProblemComplexity(Enum):
    """问题复杂度等级"""
    SIMPLE = 1      # 简单问题
    COMPLICATED = 2  # 复杂问题（多步骤）
    COMPLEX = 3      # 复杂问题（动态变化）
    CHAOTIC = 4      # 混沌问题（不可预测）
    META = 5         # 元问题（关于问题的问题）

@dataclass
class Problem:
    """问题定义"""
    id: str
    statement: str
    context: Dict[str, Any]
    constraints: List[str]
    success_criteria: List[str]
    current_boundaries: Set[str] = field(default_factory=set)
    exploration_history: List[Dict] = field(default_factory=list)
    iteration_count: int = 0

    def expand_boundary(self, new_boundary: str):
        """扩展问题边界"""
        if new_boundary not in self.current_boundaries:
            self.current_boundaries.add(new_boundary)
            logger.info(f"🔍 问题边界扩展: {new_boundary}")

@dataclass
class Insight:
    """洞察/新发现"""
    id: str
    content: str
    confidence: float
    novelty_score: float
    source: str
    timestamp: datetime
    connections: List[str] = field(default_factory=list)

    def is_novel(self, threshold: float = 0.7) -> bool:
        """判断是否为新发现"""
        return self.novelty_score > threshold

@dataclass
class Solution:
    """解决方案"""
    id: str
    approach: Dict[str, Any]
    reasoning: List[str]
    confidence: float
    completeness: float
    innovations: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """判断方案是否有效"""
        return self.confidence > 0.8 and self.completeness > 0.8

    def needs_optimization(self) -> bool:
        """判断是否需要优化"""
        return self.confidence < 0.95 or len(self.limitations) > 2

class MetaCognitiveSystem:
    """元认知系统 - 集成高级问题解决框架"""

    def __init__(self):
        # 核心组件
        self.athena = EnhancedReasoningEngine()
        self.xiaonuo = XiaoNuoEnhancedSystem()

        # 元认知组件
        self.insight_database = {}
        self.solution_patterns = {}
        self.cognitive_growth_metrics = {
            'total_insights': 0,
            'boundary_expansions': 0,
            'recursive_depths': [],
            'innovation_frequency': 0.0
        }

        # 系统状态
        self.current_problem = None
        self.solution_space = None

    async def meta_solve(self, problem_statement: str, context: Dict = None) -> Dict:
        """元问题解决 - 应用高级框架"""
        logger.info(f"🚀 启动元认知问题解决: {problem_statement[:50]}...")

        start_time = time.time()

        # 初始化问题
        self.current_problem = Problem(
            id=self._generate_id(),
            statement=problem_statement,
            context=context or {},
            constraints=[],
            success_criteria=[]
        )

        solution = Solution(
            id=self._generate_id(),
            approach={},
            reasoning=[],
            confidence=0.0,
            completeness=0.0
        )

        # 执行循环
        iteration = 0
        max_iterations = 10  # 防止无限循环

        while not solution.is_valid() and iteration < max_iterations:
            iteration += 1
            self.current_problem.iteration_count = iteration

            logger.info(f"\n{'='*60}")
            logger.info(f"迭代 {iteration}: 应用思维框架")
            logger.info(f"{'='*60}")

            # 1. 应用思维框架
            insights = await self._apply_thinking_framework(self.current_problem)

            # 2. 整合新发现
            new_discoveries = []
            for insight in insights:
                if insight.is_novel():
                    await self._integrate_insight(insight)
                    self.current_problem.expand_boundary(insight.content)
                    new_discoveries.append(insight)
                    self.cognitive_growth_metrics['total_insights'] += 1

            # 3. 生成或优化解决方案
            if new_discoveries or iteration == 1:
                solution = await self._generate_solution(
                    self.current_problem,
                    insights,
                    solution
                )

            # 4. 自我评估
            await self._self_evaluate(solution)

            # 5. 判断是否需要重新定义问题
            if solution.needs_optimization() and iteration < max_iterations - 1:
                logger.info('🔄 重新定义问题...')
                self.current_problem = await self._redefine_problem(
                    self.current_problem,
                    solution
                )

        # 记录递归深度
        self.cognitive_growth_metrics['recursive_depths'].append(iteration)

        # 生成最终输出
        result = await self._format_output(
            self.current_problem,
            solution,
            insights,
            time.time() - start_time
        )

        # 更新成长指标
        self._update_growth_metrics(result)

        logger.info(f"✅ 元认知解决完成，迭代{iteration}次")
        return result

    async def _apply_thinking_framework(self, problem: Problem) -> List[Insight]:
        """应用六步思维框架"""
        insights = []

        # 步骤1: 问题分解
        decomposition_insights = await self._problem_decomposition(problem)
        insights.extend(decomposition_insights)

        # 步骤2: 跨学科连接
        connection_insights = await self._interdisciplinary_connections(problem)
        insights.extend(connection_insights)

        # 步骤3: 抽象建模
        modeling_insights = await self._abstract_modeling(problem)
        insights.extend(modeling_insights)

        # 步骤4: 递归分析
        recursive_insights = await self._recursive_analysis(problem)
        insights.extend(recursive_insights)

        # 步骤5: 创新突破
        innovation_insights = await self._innovative_breakthroughs(problem)
        insights.extend(innovation_insights)

        # 步骤6: 综合与验证
        synthesis_insights = await self._synthesis_and_validation(problem, insights)
        insights.extend(synthesis_insights)

        return insights

    async def _problem_decomposition(self, problem: Problem) -> List[Insight]:
        """问题分解"""
        logger.info('1️⃣ 步骤1: 问题分解')

        # 使用Athena进行深度分解
        analysis = await self.athena.reason(
            problem=f"分解问题: {problem.statement}",
            mode=ThinkingMode.MULTI_SCALE,
            depth=ReasoningDepth.DEEP
        )

        # 提取分解洞察
        insights = []
        subproblems = self._extract_subproblems(analysis)

        for i, subproblem in enumerate(subproblems):
            insight = Insight(
                id=self._generate_id(),
                content=f"子问题{i+1}: {subproblem}",
                confidence=0.8,
                novelty_score=0.3,
                source='decomposition',
                timestamp=datetime.now()
            )
            insights.append(insight)

        return insights

    async def _interdisciplinary_connections(self, problem: Problem) -> List[Insight]:
        """跨学科连接"""
        logger.info('2️⃣ 步骤2: 跨学科连接')

        disciplines = [
            '认知科学', '系统论', '信息论', '控制论',
            '复杂性科学', '计算思维', '设计思维'
        ]

        insights = []
        for discipline in disciplines:
            # 使用小诺的直觉能力寻找连接
            connection = await self._find_discipline_connection(
                problem.statement, discipline
            )

            if connection:
                insight = Insight(
                    id=self._generate_id(),
                    content=f"{discipline}视角: {connection}",
                    confidence=0.7,
                    novelty_score=0.6,
                    source='interdisciplinary',
                    timestamp=datetime.now()
                )
                insights.append(insight)

        return insights

    async def _abstract_modeling(self, problem: Problem) -> List[Insight]:
        """抽象建模"""
        logger.info('3️⃣ 步骤3: 抽象建模')

        # 创建问题的抽象模型
        models = [
            '因果模型', '系统动力学模型', '网络模型',
            '博弈论模型', '信息流模型'
        ]

        insights = []
        for model_type in models:
            model_representation = await self._create_abstract_model(
                problem, model_type
            )

            insight = Insight(
                id=self._generate_id(),
                content=f"{model_type}: {model_representation}",
                confidence=0.75,
                novelty_score=0.5,
                source='modeling',
                timestamp=datetime.now()
            )
            insights.append(insight)

        return insights

    async def _recursive_analysis(self, problem: Problem) -> List[Insight]:
        """递归分析"""
        logger.info('4️⃣ 步骤4: 递归分析')

        insights = []

        # 递归深度：分析问题的问题
        meta_questions = [
            '为什么这是一个问题？',
            '这个问题背后的假设是什么？',
            '如果改变问题的表述会怎样？'
        ]

        for question in meta_questions:
            # 递归调用Athena分析
            analysis = await self.athena.reason(
                problem=question + ' 原问题: ' + problem.statement,
                mode=ThinkingMode.RECURSIVE,
                depth=ReasoningDepth.PROFOUND
            )

            if analysis.get('insights'):
                insight = Insight(
                    id=self._generate_id(),
                    content=f"递归洞察: {analysis['insights'][0]}",
                    confidence=analysis.get('confidence', 0.5),
                    novelty_score=0.8,
                    source='recursive',
                    timestamp=datetime.now()
                )
                insights.append(insight)

        return insights

    async def _innovative_breakthroughs(self, problem: Problem) -> List[Insight]:
        """创新突破"""
        logger.info('5️⃣ 步骤5: 创新突破')

        # 使用小诺的创造力
        creative_sparks = await self.xiaonuo.intuitive_reasoner.creative_inspiration(
            problem.statement,
            {'type': 'innovation_generation'}
        )

        insights = []
        if creative_sparks:
            for spark in creative_sparks:
                insight = Insight(
                    id=self._generate_id(),
                    content=f"创新点: {spark['idea']}",
                    confidence=spark.get('novelty_score', 0.5),
                    novelty_score=spark.get('novelty_score', 0.5),
                    source='innovation',
                    timestamp=datetime.now()
                )
                insights.append(insight)

        return insights

    async def _synthesis_and_validation(self,
                                       problem: Problem,
                                       insights: List[Insight]) -> List[Insight]:
        """综合与验证"""
        logger.info('6️⃣ 步骤6: 综合与验证')

        # 综合所有洞察
        synthesis = await self._synthesize_insights(insights)

        # 验证综合结果
        validation = await self._validate_synthesis(synthesis, problem)

        insights.append(Insight(
            id=self._generate_id(),
            content=f"综合洞察: {synthesis}",
            confidence=validation.get('confidence', 0.5),
            novelty_score=validation.get('novelty', 0.5),
            source='synthesis',
            timestamp=datetime.now()
        ))

        return insights

    # 辅助方法
    async def _integrate_insight(self, insight: Insight):
        """整合新洞察"""
        self.insight_database[insight.id] = insight

        # 触发认知更新
        if insight.source == 'innovation':
            self.cognitive_growth_metrics['innovation_frequency'] += 0.1

    async def _generate_solution(self,
                                problem: Problem,
                                insights: List[Insight],
                                current_solution: Solution) -> Solution:
        """生成或优化解决方案"""
        # 基于洞察生成新方案
        approach = {
            'core_strategy': self._extract_core_strategy(insights),
            'implementation_steps': self._extract_implementation(insights),
            'innovations': [i.content for i in insights if i.novelty_score > 0.7]
        }

        solution = Solution(
            id=self._generate_id(),
            approach=approach,
            reasoning=[i.content for i in insights],
            confidence=self._calculate_confidence(insights),
            completeness=self._calculate_completeness(insights),
            innovations=approach['innovations']
        )

        return solution

    async def _self_evaluate(self, solution: Solution):
        """自我评估"""
        # 多维度评估
        evaluation_criteria = [
            '逻辑一致性',
            '创新性',
            '可行性',
            '完整性',
            '优雅性'
        ]

        scores = []
        for criterion in evaluation_criteria:
            score = await self._evaluate_criterion(solution, criterion)
            scores.append(score)

        # 更新解决方案的置信度
        solution.confidence = sum(scores) / len(scores)

        # 识别局限性
        solution.limitations = await self._identify_limitations(solution)

    async def _redefine_problem(self,
                               original_problem: Problem,
                               current_solution: Solution) -> Problem:
        """重新定义问题"""
        # 基于当前方案的局限性重新定义问题
        new_statement = f"原始问题: {original_problem.statement}\n"
        new_statement += f"基于当前理解: {current_solution.limitations[0] if current_solution.limitations else '需要更深入的探索'}"

        redefined = Problem(
            id=self._generate_id(),
            statement=new_statement,
            context={**original_problem.context, 'redefined': True},
            constraints=original_problem.constraints,
            success_criteria=original_problem.success_criteria,
            current_boundaries=original_problem.current_boundaries.copy()
        )

        return redefined

    async def _format_output(self,
                           problem: Problem,
                           solution: Solution,
                           insights: List[Insight],
                           processing_time: float) -> Dict:
        """格式化输出"""
        return {
            '1_problem_restatement': problem.statement,
            '2_interdisciplinary_connections': [
                i.content for i in insights if i.source == 'interdisciplinary'
            ],
            '3_abstract_model': [
                i.content for i in insights if i.source == 'modeling'
            ],
            '4_recursive_analysis_results': [
                i.content for i in insights if i.source == 'recursive'
            ],
            '5_innovation_points': solution.innovations,
            '6_synthesized_solution': solution.approach,
            '7_self_validation': {
                'confidence': solution.confidence,
                'completeness': solution.completeness
            },
            '8_potential_limitations': solution.limitations,
            '9_further_exploration_directions': list(problem.current_boundaries),
            'metadata': {
                'iterations': problem.iteration_count,
                'total_insights': len(insights),
                'processing_time': processing_time,
                'cognitive_growth': self.cognitive_growth_metrics
            }
        }

    def _update_growth_metrics(self, result: Dict):
        """更新成长指标"""
        if 'metadata' in result:
            self.cognitive_growth_metrics.update(
                result['metadata']['cognitive_growth']
            )

    # 工具方法
    def _generate_id(self) -> str:
        """生成唯一ID"""
        return hashlib.md5(
            f"{time.time(, usedforsecurity=False)}{id(self)}".encode()
        ).hexdigest()[:16]

    def _extract_subproblems(self, analysis: Dict) -> List[str]:
        """提取子问题"""
        # 简化实现
        return ['子问题示例1', '子问题示例2']

    async def _find_discipline_connection(self,
                                         problem: str,
                                         discipline: str) -> str | None:
        """寻找学科连接"""
        # 简化实现
        connections = {
            '认知科学': '从人类认知角度理解问题本质',
            '系统论': '将问题视为开放系统',
            '信息论': '分析信息流动和熵增',
            '控制论': '建立反馈控制机制'
        }
        return connections.get(discipline)

    async def _create_abstract_model(self,
                                    problem: Problem,
                                    model_type: str) -> str:
        """创建抽象模型"""
        # 简化实现
        return f"{model_type}的抽象表示"

    async def _synthesize_insights(self, insights: List[Insight]) -> str:
        """综合洞察"""
        return f"综合了{len(insights)}个洞察的整体理解"

    async def _validate_synthesis(self, synthesis: str, problem: Problem) -> Dict:
        """验证综合结果"""
        return {
            'confidence': 0.85,
            'novelty': 0.7,
            'validation': '通过内部一致性检验'
        }

    def _extract_core_strategy(self, insights: List[Insight]) -> str:
        """提取核心策略"""
        high_confidence = [i for i in insights if i.confidence > 0.7]
        return f"基于{len(high_confidence)}个高置信度洞察的策略"

    def _extract_implementation(self, insights: List[Insight]) -> List[str]:
        """提取实施步骤"""
        return [f"步骤{i+1}: 基于洞察{i.content[:30]}..." for i in insights[:3]]

    def _calculate_confidence(self, insights: List[Insight]) -> float:
        """计算置信度"""
        if not insights:
            return 0.0
        return sum(i.confidence for i in insights) / len(insights)

    def _calculate_completeness(self, insights: List[Insight]) -> float:
        """计算完整性"""
        # 基于洞察的多样性
        sources = set(i.source for i in insights)
        return min(1.0, len(sources) / 6)  # 6个可能来源

    async def _evaluate_criterion(self, solution: Solution, criterion: str) -> float:
        """评估特定标准"""
        # 简化实现
        evaluations = {
            '逻辑一致性': 0.85,
            '创新性': 0.9,
            '可行性': 0.8,
            '完整性': 0.75,
            '优雅性': 0.88
        }
        return evaluations.get(criterion, 0.7)

    async def _identify_limitations(self, solution: Solution) -> List[str]:
        """识别局限性"""
        limitations = []
        if solution.confidence < 0.9:
            limitations.append('置信度有待提升')
        if solution.completeness < 0.9:
            limitations.append('方案需要进一步完善')
        if not solution.innovations:
            limitations.append('缺乏创新元素')
        return limitations or ['暂无显著局限']

# 导出主类
__all__ = ['MetaCognitiveSystem', 'ProblemComplexity']