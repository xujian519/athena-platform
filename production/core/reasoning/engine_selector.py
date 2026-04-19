#!/usr/bin/env python3
"""
推理引擎自动选择器
Reasoning Engine Auto Selector

基于任务类型、复杂度、领域等因素,自动选择最合适的推理引擎。

作者: 小诺·双鱼座 💖
创建: 2025-12-31
版本: v1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskDomain(Enum):
    """任务领域"""

    GENERAL = "general"  # 通用任务
    PATENT_LAW = "patent_law"  # 专利法律
    LEGAL = "legal"  # 法律
    TECHNICAL = "technical"  # 技术分析
    BUSINESS = "business"  # 商业决策
    CREATIVE = "creative"  # 创意生成
    RESEARCH = "research"  # 研究分析
    COMPLIANCE = "compliance"  # 合规检查
    STRATEGY = "strategy"  # 策略规划


class TaskComplexity(Enum):
    """任务复杂度"""

    SIMPLE = "simple"  # 简单任务
    MODERATE = "moderate"  # 中等复杂
    COMPLEX = "complex"  # 复杂任务
    VERY_COMPLEX = "very_complex"  # 非常复杂
    EXPERT = "expert"  # 专家级


class TaskType(Enum):
    """任务类型"""

    ANALYSIS = "analysis"  # 分析任务
    REASONING = "reasoning"  # 推理任务
    DECISION = "decision"  # 决策任务
    GENERATION = "generation"  # 生成任务
    EVALUATION = "evaluation"  # 评估任务
    COMPARISON = "comparison"  # 比较任务
    VALIDATION = "validation"  # 验证任务
    PLANNING = "planning"  # 规划任务
    DRAFT_PREPARATION = "draft_preparation"  # 起草任务
    RESEARCH = "research"  # 研究任务


class UrgencyLevel(Enum):
    """紧急程度"""

    IMMEDIATE = "immediate"  # 立即处理
    URGENT = "urgent"  # 紧急
    NORMAL = "normal"  # 正常
    LOW = "low"  # 不急


@dataclass
class TaskProfile:
    """任务画像"""

    domain: TaskDomain  # 任务领域
    complexity: TaskComplexity  # 复杂度
    task_type: TaskType  # 任务类型
    urgency: UrgencyLevel  # 紧急程度
    requires_accuracy: bool  # 是否要求高准确度
    requires_creativity: bool  # 是否要求创意
    requires_evidence: bool  # 是否要求证据支持
    requires_speed: bool  # 是否要求速度
    context: dict[str, Any] = field(default_factory=dict)  # 额外上下文


@dataclass
class EngineRecommendation:
    """引擎推荐结果"""

    engine_name: str  # 引擎名称
    confidence: float  # 推荐置信度 (0-1)
    reason: str  # 推荐理由
    alternative_engines: list[tuple[str, str]] = field(
        default_factory=list
    )  # 备选引擎 (名称, 理由)


class ReasoningEngineSelector:
    """推理引擎选择器"""

    def __init__(self):
        self._build_selection_rules()
        self._build_engine_capabilities()

    def _build_engine_capabilities(self) -> Any:
        """构建各引擎的能力矩阵"""
        self.engine_capabilities = {
            # === 核心框架 ===
            "six_step": {
                "domains": [TaskDomain.GENERAL, TaskDomain.TECHNICAL, TaskDomain.RESEARCH],
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.REASONING],
                "strengths": ["深度分析", "问题分解", "跨学科连接"],
                "weaknesses": ["速度较慢", "需要多步推理"],
                "speed": "slow",
                "accuracy": "high",
            },
            "seven_step": {
                "domains": [TaskDomain.GENERAL, TaskDomain.BUSINESS, TaskDomain.STRATEGY],
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.DECISION, TaskType.PLANNING],
                "strengths": ["系统化思维", "假设验证", "错误修正"],
                "weaknesses": ["计算密集", "需要多轮迭代"],
                "speed": "slow",
                "accuracy": "very_high",
            },
            # === 32模式超级推理 ===
            "32modes": {
                "domains": [TaskDomain.GENERAL, TaskDomain.RESEARCH, TaskDomain.TECHNICAL],
                "complexity": [
                    TaskComplexity.MODERATE,
                    TaskComplexity.COMPLEX,
                    TaskComplexity.VERY_COMPLEX,
                ],
                "task_types": [TaskType.ANALYSIS, TaskType.REASONING, TaskType.EVALUATION],
                "strengths": ["32种推理模式", "智能策略选择", "多维度分析"],
                "weaknesses": ["资源消耗大", "配置复杂"],
                "speed": "medium",
                "accuracy": "very_high",
            },
            # === 统一与高级推理 ===
            "unified": {
                "domains": [TaskDomain.GENERAL],
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "task_types": [TaskType.ANALYSIS, TaskType.REASONING, TaskType.VALIDATION],
                "strengths": ["多模式支持", "统一接口", "灵活配置"],
                "weaknesses": ["每种模式深度有限"],
                "speed": "medium",
                "accuracy": "medium",
            },
            "dual_system": {
                "domains": [TaskDomain.GENERAL, TaskDomain.BUSINESS],
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "task_types": [TaskType.DECISION, TaskType.EVALUATION, TaskType.COMPARISON],
                "strengths": ["直觉+分析双系统", "快速决策", "认知偏误控制"],
                "weaknesses": ["可能产生冲突结论"],
                "speed": "fast",
                "accuracy": "medium",
            },
            # === 多模式推理系统 ===
            "multimodal": {
                "domains": [
                    TaskDomain.GENERAL,
                    TaskDomain.BUSINESS,
                    TaskDomain.STRATEGY,
                    TaskDomain.RESEARCH,
                ],
                "complexity": [
                    TaskComplexity.COMPLEX,
                    TaskComplexity.VERY_COMPLEX,
                    TaskComplexity.EXPERT,
                ],
                "task_types": [
                    TaskType.ANALYSIS,
                    TaskType.PLANNING,
                    TaskType.DECISION,
                    TaskType.GENERATION,
                ],
                "strengths": ["AI团队协作", "三层递进推理", "专家级分析"],
                "weaknesses": ["计算资源需求大", "处理时间较长"],
                "speed": "slow",
                "accuracy": "very_high",
            },
            # === 专利/法律推理 ===
            "semantic": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.LEGAL],
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "task_types": [TaskType.ANALYSIS, TaskType.VALIDATION],
                "strengths": ["语义理解", "规则推理", "案例匹配"],
                "weaknesses": ["依赖向量模型"],
                "speed": "medium",
                "accuracy": "high",
            },
            "semantic_v4": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.LEGAL],
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.VALIDATION, TaskType.EVALUATION],
                "strengths": ["维特根斯坦原则", "精确推理", "证据导向"],
                "weaknesses": ["处理较慢"],
                "speed": "slow",
                "accuracy": "very_high",
            },
            "legal": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.LEGAL],
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.DECISION, TaskType.DRAFT_PREPARATION],
                "strengths": ["法律专家", "六步+七步推理", "专业判断"],
                "weaknesses": ["仅限法律领域"],
                "speed": "medium",
                "accuracy": "very_high",
            },
            "enhanced_legal": {
                "domains": [TaskDomain.PATENT_LAW],
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.EVALUATION],
                "strengths": ["新颖性分析", "创造性分析", "对比推理"],
                "weaknesses": ["仅专利领域"],
                "speed": "medium",
                "accuracy": "very_high",
            },
            "compliance": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.COMPLIANCE],
                "complexity": [TaskComplexity.MODERATE],
                "task_types": [TaskType.VALIDATION, TaskType.EVALUATION],
                "strengths": ["合规检查", "规则审查", "专家系统"],
                "weaknesses": ["仅合规领域"],
                "speed": "fast",
                "accuracy": "high",
            },
            "expert_rule": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.COMPLIANCE],
                "complexity": [TaskComplexity.SIMPLE, TaskComplexity.MODERATE],
                "task_types": [TaskType.VALIDATION, TaskType.EVALUATION],
                "strengths": ["规则推理", "知识图谱", "快速判断"],
                "weaknesses": ["仅支持已有规则"],
                "speed": "very_fast",
                "accuracy": "medium",
            },
            "patent_rule": {
                "domains": [TaskDomain.PATENT_LAW],
                "complexity": [TaskComplexity.MODERATE],
                "task_types": [TaskType.VALIDATION, TaskType.ANALYSIS],
                "strengths": ["规则链推理", "专利要素分析"],
                "weaknesses": ["仅专利领域"],
                "speed": "fast",
                "accuracy": "high",
            },
            "prior_art": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.RESEARCH, TaskDomain.TECHNICAL],
                "complexity": [TaskComplexity.COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.COMPARISON],
                "strengths": ["现有技术分析", "技术图谱", "关系挖掘"],
                "weaknesses": ["需要大量数据"],
                "speed": "slow",
                "accuracy": "high",
            },
            "roadmap": {
                "domains": [TaskDomain.BUSINESS, TaskDomain.STRATEGY, TaskDomain.RESEARCH],
                "complexity": [TaskComplexity.VERY_COMPLEX, TaskComplexity.EXPERT],
                "task_types": [TaskType.PLANNING, TaskType.GENERATION],
                "strengths": ["技术路线图", "趋势分析", "战略规划"],
                "weaknesses": ["需要历史数据"],
                "speed": "slow",
                "accuracy": "medium",
            },
            "llm_judgment": {
                "domains": [TaskDomain.PATENT_LAW, TaskDomain.BUSINESS, TaskDomain.TECHNICAL],
                "complexity": [TaskComplexity.MODERATE, TaskComplexity.COMPLEX],
                "task_types": [TaskType.EVALUATION, TaskType.DECISION, TaskType.ANALYSIS],
                "strengths": ["LLM增强", "专家判断", "多维度评估"],
                "weaknesses": ["依赖LLM服务"],
                "speed": "medium",
                "accuracy": "high",
            },
            "ai_invalidity": {
                "domains": [TaskDomain.PATENT_LAW],
                "complexity": [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX],
                "task_types": [TaskType.ANALYSIS, TaskType.REASONING],
                "strengths": ["RAG系统", "专利无效分析", "智能问答"],
                "weaknesses": ["仅无效宣告领域"],
                "speed": "medium",
                "accuracy": "high",
            },
        }

    def _build_selection_rules(self) -> Any:
        """构建选择规则"""
        self.rules = [
            # === 紧急规则 (最高优先级) ===
            {
                "name": "紧急任务优先",
                "condition": lambda p: p.urgency == UrgencyLevel.IMMEDIATE and p.requires_speed,
                "action": lambda p: ["expert_rule", "compliance", "dual_system"],
                "reason": "紧急且需要速度,选择快速推理引擎",
            },
            # === 领域规则 ===
            {
                "name": "专利法律领域",
                "condition": lambda p: p.domain == TaskDomain.PATENT_LAW,
                "action": self._select_patent_law_engine,
                "reason": "专利法律任务,根据具体类型选择专业引擎",
            },
            {
                "name": "一般法律领域",
                "condition": lambda p: p.domain == TaskDomain.LEGAL,
                "action": lambda p: ["legal", "semantic_v4"],
                "reason": "法律任务,使用法律推理引擎",
            },
            {
                "name": "创意生成领域",
                "condition": lambda p: p.domain == TaskDomain.CREATIVE or p.requires_creativity,
                "action": lambda p: ["multimodal", "32modes", "seven_step"],
                "reason": "创意任务,使用支持创新的推理引擎",
            },
            {
                "name": "战略规划领域",
                "condition": lambda p: p.domain == TaskDomain.STRATEGY,
                "action": lambda p: ["multimodal", "roadmap", "seven_step"],
                "reason": "战略规划,使用系统化推理引擎",
            },
            # === 复杂度规则 ===
            {
                "name": "专家级复杂度",
                "condition": lambda p: p.complexity == TaskComplexity.EXPERT,
                "action": lambda p: ["multimodal", "32modes", "seven_step"],
                "reason": "专家级复杂度,使用最强大的推理引擎",
            },
            {
                "name": "非常复杂任务",
                "condition": lambda p: p.complexity == TaskComplexity.VERY_COMPLEX,
                "action": lambda p: ["32modes", "seven_step", "multimodal"],
                "reason": "非常复杂,使用32模式或七步推理",
            },
            {
                "name": "简单任务",
                "condition": lambda p: p.complexity == TaskComplexity.SIMPLE,
                "action": lambda p: ["unified", "expert_rule", "dual_system"],
                "reason": "简单任务,使用轻量级推理引擎",
            },
            # === 准确度规则 ===
            {
                "name": "高准确度要求",
                "condition": lambda p: p.requires_accuracy,
                "action": lambda p: ["semantic_v4", "seven_step", "32modes", "enhanced_legal"],
                "reason": "要求高准确度,使用最精确的推理引擎",
            },
            # === 证据支持规则 ===
            {
                "name": "需要证据支持",
                "condition": lambda p: p.requires_evidence,
                "action": lambda p: ["semantic_v4", "seven_step", "legal"],
                "reason": "需要证据支持,使用证据导向的推理引擎",
            },
            # === 任务类型规则 ===
            {
                "name": "分析任务",
                "condition": lambda p: p.task_type == TaskType.ANALYSIS,
                "action": lambda p: self._select_analysis_engine(p),
                "reason": "分析任务,根据领域选择分析引擎",
            },
            {
                "name": "决策任务",
                "condition": lambda p: p.task_type == TaskType.DECISION,
                "action": lambda p: ["dual_system", "seven_step", "multimodal"],
                "reason": "决策任务,使用支持决策的推理引擎",
            },
            {
                "name": "规划任务",
                "condition": lambda p: p.task_type == TaskType.PLANNING,
                "action": lambda p: ["roadmap", "seven_step", "multimodal"],
                "reason": "规划任务,使用支持规划的推理引擎",
            },
            {
                "name": "验证任务",
                "condition": lambda p: p.task_type == TaskType.VALIDATION,
                "action": lambda p: ["compliance", "semantic_v4", "expert_rule"],
                "reason": "验证任务,使用验证导向的推理引擎",
            },
            # === 默认规则 ===
            {
                "name": "默认推理引擎",
                "condition": lambda p: True,
                "action": lambda p: ["seven_step", "32modes", "unified"],
                "reason": "默认使用七步推理引擎",
            },
        ]

    def _select_patent_law_engine(self, profile: TaskProfile) -> list[str]:
        """选择专利法律推理引擎"""
        # 根据具体任务类型细化
        if profile.task_type == TaskType.VALIDATION:
            return ["compliance", "expert_rule", "patent_rule"]
        elif profile.task_type == TaskType.EVALUATION:
            return ["enhanced_legal", "semantic_v4", "legal"]
        elif profile.urgency == UrgencyLevel.IMMEDIATE:
            return ["expert_rule", "compliance"]
        elif profile.complexity == TaskComplexity.VERY_COMPLEX:
            return ["legal", "ai_invalidity", "enhanced_legal"]
        else:
            return ["semantic_v4", "enhanced_legal", "legal"]

    def _select_analysis_engine(self, profile: TaskProfile) -> list[str]:
        """选择分析引擎"""
        if profile.domain == TaskDomain.PATENT_LAW:
            return ["enhanced_legal", "semantic_v4", "prior_art"]
        elif profile.domain == TaskDomain.RESEARCH:
            return ["32modes", "six_step", "seven_step"]
        elif profile.complexity == TaskComplexity.EXPERT:
            return ["multimodal", "32modes"]
        else:
            return ["seven_step", "six_step", "unified"]

    def analyze_task(self, task_description: str, **kwargs) -> TaskProfile:
        """分析任务并生成任务画像

        Args:
            task_description: 任务描述
            **kwargs: 额外参数
                - domain: 任务领域
                - complexity: 复杂度
                - task_type: 任务类型
                - urgency: 紧急程度
                - requires_accuracy: 是否要求准确度
                - requires_creativity: 是否要求创意
                - requires_evidence: 是否要求证据
                - requires_speed: 是否要求速度

        Returns:
            TaskProfile: 任务画像
        """
        # 从参数中提取或推断任务特征
        domain = kwargs.get("domain", self._infer_domain(task_description))
        complexity = kwargs.get("complexity", self._infer_complexity(task_description))
        task_type = kwargs.get("task_type", self._infer_task_type(task_description))
        urgency = kwargs.get("urgency", UrgencyLevel.NORMAL)

        requires_accuracy = kwargs.get("requires_accuracy", False)
        requires_creativity = kwargs.get("requires_creativity", False)
        requires_evidence = kwargs.get("requires_evidence", False)
        requires_speed = kwargs.get("requires_speed", urgency == UrgencyLevel.IMMEDIATE)

        return TaskProfile(
            domain=domain,
            complexity=complexity,
            task_type=task_type,
            urgency=urgency,
            requires_accuracy=requires_accuracy,
            requires_creativity=requires_creativity,
            requires_evidence=requires_evidence,
            requires_speed=requires_speed,
            context=kwargs.get("context", {}),
        )

    def _infer_domain(self, description: str) -> TaskDomain:
        """从描述中推断任务领域"""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["专利", "patent", "无效", "新颖性", "创造性"]):
            return TaskDomain.PATENT_LAW
        elif any(kw in desc_lower for kw in ["法律", "legal", "法规", "合规"]):
            return TaskDomain.LEGAL
        elif any(kw in desc_lower for kw in ["技术", "研发", "技术分析"]):
            return TaskDomain.TECHNICAL
        elif any(kw in desc_lower for kw in ["商业", "business", "市场"]):
            return TaskDomain.BUSINESS
        elif any(kw in desc_lower for kw in ["创意", "创新", "设计", "创造"]):
            return TaskDomain.CREATIVE
        elif any(kw in desc_lower for kw in ["研究", "分析", "调研"]):
            return TaskDomain.RESEARCH
        elif any(kw in desc_lower for kw in ["战略", "策略", "规划"]):
            return TaskDomain.STRATEGY
        elif any(kw in desc_lower for kw in ["合规", "审查", "检查"]):
            return TaskDomain.COMPLIANCE
        else:
            return TaskDomain.GENERAL

    def _infer_complexity(self, description: str) -> TaskComplexity:
        """从描述中推断任务复杂度"""
        desc_lower = description.lower()

        # 关键词权重
        expert_keywords = ["专家", "expert", "深度", "综合", "系统", "架构", "多维度"]
        complex_keywords = ["复杂", "complex", "分析", "多个", "综合", "整合"]
        moderate_keywords = ["评估", "判断", "选择", "比较"]
        simple_keywords = ["查询", "检查", "简单", "快速"]

        if any(kw in desc_lower for kw in expert_keywords):
            return TaskComplexity.EXPERT
        elif any(kw in desc_lower for kw in complex_keywords):
            return TaskComplexity.COMPLEX
        elif any(kw in desc_lower for kw in moderate_keywords):
            return TaskComplexity.MODERATE
        elif any(kw in desc_lower for kw in simple_keywords):
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.MODERATE

    def _infer_task_type(self, description: str) -> TaskType:
        """从描述中推断任务类型"""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["分析", "analyze", "研究", "探索"]):
            return TaskType.ANALYSIS
        elif any(kw in desc_lower for kw in ["决定", "决策", "choose", "select"]):
            return TaskType.DECISION
        elif any(kw in desc_lower for kw in ["生成", "create", "create", "设计"]):
            return TaskType.GENERATION
        elif any(kw in desc_lower for kw in ["规划", "plan", "路线图"]):
            return TaskType.PLANNING
        elif any(kw in desc_lower for kw in ["验证", "check", "validate", "审查"]):
            return TaskType.VALIDATION
        elif any(kw in desc_lower for kw in ["比较", "对比", "差异"]):
            return TaskType.COMPARISON
        elif any(kw in desc_lower for kw in ["评估", "evaluate"]):
            return TaskType.EVALUATION
        else:
            return TaskType.REASONING

    def select_engine(self, task_profile: TaskProfile) -> EngineRecommendation:
        """选择最合适的推理引擎

        Args:
            task_profile: 任务画像

        Returns:
            EngineRecommendation: 引擎推荐结果
        """
        # 遍历规则,找到第一个匹配的规则
        for rule in self.rules:
            if rule["condition"](task_profile):
                engine_candidates = rule["action"](task_profile)
                primary_engine = engine_candidates[0]
                alternatives = [
                    (e, self._get_engine_reason(e, task_profile)) for e in engine_candidates[1:4]
                ]

                return EngineRecommendation(
                    engine_name=primary_engine,
                    confidence=self._calculate_confidence(primary_engine, task_profile),
                    reason=rule["reason"],
                    alternative_engines=alternatives,
                )

        # 默认返回
        return EngineRecommendation(engine_name="seven_step", confidence=0.5, reason="默认推荐")

    def _get_engine_reason(self, engine_name: str, profile: TaskProfile) -> str:
        """获取选择某个引擎的理由"""
        caps = self.engine_capabilities.get(engine_name, {})
        strengths = caps.get("strengths", [])
        if strengths:
            return f"优势: {', '.join(strengths[:2])}"
        return "备选方案"

    def _calculate_confidence(self, engine_name: str, profile: TaskProfile) -> float:
        """计算推荐置信度"""
        caps = self.engine_capabilities.get(engine_name, {})

        confidence = 0.5  # 基础置信度

        # 检查领域匹配
        if profile.domain in caps.get("domains", []):
            confidence += 0.2

        # 检查复杂度匹配
        if profile.complexity in caps.get("complexity", []):
            confidence += 0.15

        # 检查任务类型匹配
        if profile.task_type in caps.get("task_types", []):
            confidence += 0.1

        # 检查特殊需求匹配
        if profile.requires_accuracy and caps.get("accuracy") in ["high", "very_high"]:
            confidence += 0.05

        if profile.requires_speed and caps.get("speed") in ["fast", "very_fast"]:
            confidence += 0.05

        return min(confidence, 1.0)

    def recommend(self, task_description: str, **kwargs) -> EngineRecommendation:
        """便捷方法:直接从任务描述推荐引擎

        Args:
            task_description: 任务描述
            **kwargs: 额外参数

        Returns:
            EngineRecommendation: 引擎推荐结果
        """
        profile = self.analyze_task(task_description, **kwargs)
        return self.select_engine(profile)


# 全局单例
_selector_instance = None


def get_selector() -> ReasoningEngineSelector:
    """获取推理引擎选择器单例"""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = ReasoningEngineSelector()
    return _selector_instance


def select_reasoning_engine(task_description: str, **kwargs) -> str:
    """选择推理引擎的便捷函数

    Args:
        task_description: 任务描述
        **kwargs: 额外参数

    Returns:
        str: 推荐的引擎名称
    """
    selector = get_selector()
    recommendation = selector.recommend(task_description, **kwargs)
    return recommendation.engine_name


# 导出
__all__ = [
    "EngineRecommendation",
    "ReasoningEngineSelector",
    "TaskComplexity",
    "TaskDomain",
    "TaskProfile",
    "TaskType",
    "UrgencyLevel",
    "get_selector",
    "select_reasoning_engine",
]
