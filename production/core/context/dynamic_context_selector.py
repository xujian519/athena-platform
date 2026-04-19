#!/usr/bin/env python3
"""
动态上下文选择器 - 智能上下文管理
Dynamic Context Selector - Intelligent Context Management

基于任务复杂度和类型,动态选择最优的提示词层和上下文内容:
- 根据任务复杂度选择L1-L4层
- 评分上下文部分的重要性
- 实现分层上下文选择策略
- 提供缓存机制提升性能

目标: 减少不必要的Token使用,提升响应速度

作者: 小诺·双鱼公主
创建时间: 2026-01-07
版本: v1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TaskComplexity(Enum):
    """任务复杂度"""

    SIMPLE = "simple"  # 简单任务: 只需L1 + 部分L3
    MODERATE = "moderate"  # 中等任务: L1 + L2 + L3 + 部分L4
    COMPLEX = "complex"  # 复杂任务: 完整L1-L4
    CRITICAL = "critical"  # 关键任务: 完整L1-L4 + 强化版


class TaskType(Enum):
    """任务类型"""

    PLATFORM_MANAGEMENT = "platform_management"
    PATENT_LEGAL = "patent_legal"
    IP_MANAGEMENT = "ip_management"
    DATA_PROCESSING = "data_processing"
    DEVELOPMENT_ASSISTANCE = "development_assistance"
    FAMILY_EMOTION = "family_emotion"
    GENERAL_QUERY = "general_query"


@dataclass
class ContextLayer:
    """上下文层"""

    name: str  # L1, L2, L3, L4
    description: str  # 描述
    content: str  # 内容
    token_count: int = 0  # Token数
    importance: float = 1.0  # 重要性权重
    enabled: bool = True  # 是否启用


@dataclass
class ContextSelection:
    """上下文选择结果"""

    task_complexity: TaskComplexity
    task_type: TaskType
    selected_layers: list[str]  # 选择的层 (如 ["L1", "L3"])
    filtered_content: str  # 过滤后的内容
    total_tokens: int
    estimated_time_savings: float  # 预计节省的时间(秒)
    reasoning: str  # 选择理由


class DynamicContextSelector:
    """
    动态上下文选择器

    核心功能:
    1. 评估任务复杂度
    2. 评分上下文重要性
    3. 选择最优提示词层
    4. 智能过滤上下文内容
    """

    def __init__(self, prompts_base_path: str = "prompts"):
        """
        初始化动态上下文选择器

        Args:
            prompts_base_path: 提示词基础路径
        """
        self.prompts_base_path = Path(prompts_base_path)
        self.context_cache: dict[str, Any] = {}
        self.cache_ttl = 3600  # 缓存1小时

        # 复杂度关键词字典
        self.complexity_keywords = {
            TaskComplexity.SIMPLE: [
                "查询",
                "状态",
                "简单",
                "快速",
                "简要",
                "是什么",
                "怎么样",
                "列表",
                "清单",
            ],
            TaskComplexity.MODERATE: [
                "分析",
                "对比",
                "评估",
                "检索",
                "搜索",
                "理解",
                "解释",
                "说明",
                "比较",
            ],
            TaskComplexity.COMPLEX: [
                "深度分析",
                "综合",
                "多步骤",
                "系统",
                "完整",
                "全面",
                "详细",
                "深入研究",
            ],
            TaskComplexity.CRITICAL: [
                "答复",
                "撰写",
                "无效",
                "审查意见",
                "申请",
                "文件",
                "正式",
                "决策",
            ],
        }

        # 任务类型关键词字典
        self.task_type_keywords = {
            TaskType.PLATFORM_MANAGEMENT: [
                "服务",
                "启动",
                "停止",
                "监控",
                "部署",
                "容器",
                "进程",
                "健康检查",
            ],
            TaskType.PATENT_LEGAL: [
                "专利",
                "法律",
                "审查",
                "答复",
                "撰写",
                "无效",
                "新颖性",
                "创造性",
                "权利要求",
            ],
            TaskType.IP_MANAGEMENT: [
                "管理",
                "费用",
                "期限",
                "年费",
                "流程",
                "申请号",
                "专利号",
                "法律状态",
            ],
            TaskType.DATA_PROCESSING: [
                "数据",
                "检索",
                "查询",
                "统计",
                "分析",
                "数据库",
                "向量",
                "图谱",
            ],
            TaskType.DEVELOPMENT_ASSISTANCE: [
                "代码",
                "开发",
                "API",
                "测试",
                "调试",
                "部署",
                "架构",
                "设计",
            ],
            TaskType.FAMILY_EMOTION: [
                "陪伴",
                "关心",
                "情感",
                "心情",
                "温暖",
                "爸爸",
                "女儿",
                "家人",
            ],
        }

        logger.info("动态上下文选择器初始化完成")

    async def select_context(
        self,
        task: str,
        available_layers: dict[str, ContextLayer],
        force_complexity: TaskComplexity | None = None,
    ) -> ContextSelection:
        """
        选择最优上下文

        Args:
            task: 任务描述
            available_layers: 可用的上下文层
            force_complexity: 强制指定的复杂度

        Returns:
            ContextSelection: 上下文选择结果
        """
        # 1. 评估任务复杂度和类型
        if force_complexity:
            complexity = force_complexity
        else:
            complexity = await self.evaluate_task_complexity(task)

        task_type = await self.classify_task_type(task)

        # 2. 根据策略选择层
        selected_layer_names = self._select_layers_by_strategy(
            complexity, task_type, available_layers
        )

        # 过滤掉不存在的层
        selected_layer_names = [name for name in selected_layer_names if name in available_layers]

        # 3. 过滤和整合内容
        filtered_content = self._filter_and_merge_content(
            selected_layer_names, available_layers, task
        )

        # 4. 计算Token和节省时间
        total_tokens = sum(available_layers[name].token_count for name in selected_layer_names)

        all_tokens = sum(layer.token_count for layer in available_layers.values())
        estimated_time_savings = (all_tokens - total_tokens) * 0.0005  # 粗略估算

        # 5. 生成选择理由
        reasoning = self._generate_selection_reasoning(complexity, task_type, selected_layer_names)

        selection = ContextSelection(
            task_complexity=complexity,
            task_type=task_type,
            selected_layers=selected_layer_names,
            filtered_content=filtered_content,
            total_tokens=total_tokens,
            estimated_time_savings=estimated_time_savings,
            reasoning=reasoning,
        )

        logger.info(f"上下文选择完成: {complexity.value} -> {selected_layer_names}")

        return selection

    async def evaluate_task_complexity(self, task: str) -> TaskComplexity:
        """
        评估任务复杂度

        评估维度:
        1. 关键词匹配
        2. 任务长度
        3. 是否包含多个子任务
        4. 是否需要HITL
        """
        scores = {}

        # 1. 关键词匹配评分
        for complexity, keywords in self.complexity_keywords.items():
            score = sum(1 for kw in keywords if kw in task)
            scores[complexity] = score

        # 2. 任务长度评分
        task_length = len(task)
        if task_length < 50:
            scores[TaskComplexity.SIMPLE] += 2
        elif task_length > 200:
            scores[TaskComplexity.COMPLEX] += 2
        elif task_length > 500:
            scores[TaskComplexity.CRITICAL] += 3

        # 3. 子任务检测
        subtask_indicators = ["然后", "接着", "之后", "还要", "以及", "另外"]
        subtask_count = sum(1 for ind in subtask_indicators if ind in task)
        if subtask_count >= 3:
            scores[TaskComplexity.COMPLEX] += 3
        elif subtask_count >= 1:
            scores[TaskComplexity.MODERATE] += 1

        # 4. HITL任务检测
        hitl_keywords = ["审查意见", "答复", "无效宣告", "专利撰写"]
        if any(kw in task for kw in hitl_keywords):
            scores[TaskComplexity.CRITICAL] += 5

        # 选择得分最高的复杂度
        max_complexity = max(scores, key=scores.get)

        logger.info(f"任务复杂度评估: {task[:50]}... -> {max_complexity.value}")

        return max_complexity

    async def classify_task_type(self, task: str) -> TaskType:
        """
        分类任务类型

        Returns:
            TaskType: 任务类型
        """
        scores = {}

        # 关键词匹配评分
        for task_type, keywords in self.task_type_keywords.items():
            score = sum(1 for kw in keywords if kw in task)
            scores[task_type] = score

        # 选择得分最高的类型
        max_type = max(scores, key=scores.get)

        # 如果所有得分都是0,返回通用查询
        if scores[max_type] == 0:
            max_type = TaskType.GENERAL_QUERY

        logger.info(f"任务类型分类: {task[:50]}... -> {max_type.value}")

        return max_type

    def _select_layers_by_strategy(
        self,
        complexity: TaskComplexity,
        task_type: TaskType,
        available_layers: dict[str, ContextLayer],
    ) -> list[str]:
        """
        根据策略选择层

        策略:
        - SIMPLE: L1 + 相关L3能力
        - MODERATE: L1 + L2 + L3 + 相关L4场景
        - COMPLEX: 完整L1-L4
        - CRITICAL: 完整L1-L4 + 强化版
        """
        if complexity == TaskComplexity.SIMPLE:
            # 简单任务: L1 + 部分L3
            return ["L1", "L3"]

        elif complexity == TaskComplexity.MODERATE:
            # 中等任务: L1 + L2 + L3 + 部分L4
            return ["L1", "L2", "L3", "L4"]

        elif complexity == TaskComplexity.COMPLEX:
            # 复杂任务: 完整L1-L4
            return ["L1", "L2", "L3", "L4"]

        else:  # CRITICAL
            # 关键任务: 完整L1-L4 + 强化版
            return ["L1", "L2", "L3", "L4", "L4_ENHANCED"]

    def _filter_and_merge_content(
        self, selected_layers: list[str], available_layers: dict[str, ContextLayer], task: str
    ) -> str:
        """
        过滤和整合内容

        Args:
            selected_layers: 选择的层名称列表
            available_layers: 可用的层
            task: 任务描述(用于内容过滤)

        Returns:
            str: 整合后的内容
        """
        parts = []

        for layer_name in selected_layers:
            if layer_name not in available_layers:
                continue

            layer = available_layers[layer_name]

            # 智能过滤: 只保留与任务相关的内容
            filtered_content = self._filter_content_by_task(layer.content, task, layer_name)

            parts.append(f"## {layer.description}\n{filtered_content}\n")

        return "\n---\n".join(parts)

    def _filter_content_by_task(self, content: str, task: str, layer_name: str) -> str:
        """
        根据任务过滤内容

        策略:
        - L1: 总是保留完整内容
        - L2: 根据任务类型选择数据源
        - L3: 根据任务选择相关能力
        - L4: 根据任务选择相关场景
        """
        if layer_name == "L1":
            # 基础层总是保留
            return content

        elif layer_name == "L2":
            # 数据层: 根据任务类型过滤
            return self._filter_l2_content(content, task)

        elif layer_name == "L3":
            # 能力层: 根据任务选择相关能力
            return self._filter_l3_content(content, task)

        elif layer_name == "L4":
            # 业务层: 根据任务选择相关场景
            return self._filter_l4_content(content, task)

        else:
            # 默认返回完整内容
            return content

    def _filter_l2_content(self, content: str, task: str) -> str:
        """过滤L2数据层内容"""
        # 保留与任务相关的数据源部分
        lines = content.split("\n")
        filtered_lines = []

        for line in lines:
            # 保留标题和关键部分
            if line.startswith("#") or line.startswith("##") or any(kw in line for kw in ["数据源", "优先级", "决策"]):
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _filter_l3_content(self, content: str, task: str) -> str:
        """过滤L3能力层内容"""
        # 提取任务相关的能力
        lines = content.split("\n")
        filtered_lines = []
        keep_capability = False

        for line in lines:
            # 检测能力标题
            if line.startswith("###") or line.startswith("####"):
                # 检查是否与任务相关
                keep_capability = self._is_capability_relevant(line, task)
                if keep_capability:
                    filtered_lines.append(line)
            elif keep_capability:
                # 保留相关能力的详细说明
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _is_capability_relevant(self, capability_line: str, task: str) -> bool:
        """判断能力是否与任务相关"""
        # 简单实现: 检查能力名称中的关键词是否在任务中
        capability_keywords = capability_line.split()[1:]  # 跳过###标题标记
        return any(kw in task for kw in capability_keywords if len(kw) > 2)

    def _filter_l4_content(self, content: str, task: str) -> str:
        """过滤L4业务层内容"""
        # 提取任务相关的业务场景
        lines = content.split("\n")
        filtered_lines = []
        keep_scenario = False

        for line in lines:
            # 检测场景标题
            if line.startswith("###") or line.startswith("场景"):
                keep_scenario = self._is_scenario_relevant(line, task)
                if keep_scenario:
                    filtered_lines.append(line)
            elif keep_scenario:
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    def _is_scenario_relevant(self, scenario_line: str, task: str) -> bool:
        """判断场景是否与任务相关"""
        scenario_keywords = scenario_line.split()[1:]  # 跳过标题标记
        return any(kw in task for kw in scenario_keywords if len(kw) > 2)

    def _generate_selection_reasoning(
        self, complexity: TaskComplexity, task_type: TaskType, selected_layers: list[str]
    ) -> str:
        """生成选择理由"""
        reasoning_parts = [
            f"任务复杂度: {complexity.value}",
            f"任务类型: {task_type.value}",
            f"选择层级: {', '.join(selected_layers)}",
        ]

        return " | ".join(reasoning_parts)

    def score_context_importance(self, context_part: str, task: str, layer_name: str) -> float:
        """
        评分上下文部分的重要性

        Args:
            context_part: 上下文部分内容
            task: 任务描述
            layer_name: 层名称

        Returns:
            float: 重要性分数 (0-1)
        """
        score = 0.0

        # 1. 关键词匹配 (40%)
        task_keywords = set(task.split())
        context_keywords = set(context_part.split())
        overlap = len(task_keywords & context_keywords)
        keyword_score = min(1.0, overlap / len(task_keywords)) if task_keywords else 0
        score += keyword_score * 0.4

        # 2. 层重要性 (30%)
        layer_importance = {
            "L1": 1.0,  # 基础层最重要
            "L2": 0.8,  # 数据层次之
            "L3": 0.7,  # 能力层
            "L4": 0.6,  # 业务层
            "L4_ENHANCED": 0.5,
        }
        score += layer_importance.get(layer_name, 0.5) * 0.3

        # 3. 内容长度 (20%)
        length_score = min(1.0, len(context_part) / 500)
        score += length_score * 0.2

        # 4. 结构完整性 (10%)
        has_structure = any(marker in context_part for marker in ["#", "##", "###", "-"])
        structure_score = 1.0 if has_structure else 0.5
        score += structure_score * 0.1

        return min(1.0, score)


# ============================================================================
# 便捷函数
# ============================================================================

_selector_instance: DynamicContextSelector | None = None


def get_dynamic_context_selector() -> DynamicContextSelector:
    """获取动态上下文选择器单例"""
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = DynamicContextSelector()
    return _selector_instance


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "ContextLayer",
    "ContextSelection",
    "DynamicContextSelector",
    "TaskComplexity",
    "TaskType",
    "get_dynamic_context_selector",
]
