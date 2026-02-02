#!/usr/bin/env python3
"""
思考模式选择器
Thinking Mode Selector - 自动选择最适合的思考模式

支持5种思考模式(来自JoyAgent):
1. ReAct: Reasoning + Acting - 交替进行推理和行动
2. Plan: 先制定详细计划再执行
3. SOPPlan: 基于标准作业程序的规划
4. Executor: 直接执行,适用于简单任务
5. TreeOfThought: 树状推理,探索多个可能的路径

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ThinkingMode(Enum):
    """思考模式"""

    REACT = "ReAct"  # 推理-行动循环
    PLAN = "Plan"  # 先规划后执行
    SOPPLAN = "SOPPlan"  # 标准作业程序
    EXECUTOR = "Executor"  # 直接执行
    TREE_OF_THOUGHT = "TreeOfThought"  # 树状推理


@dataclass
class ModeCharacteristics:
    """模式特征"""

    name: str
    description: str
    best_for: list[str]  # 最适用的任务类型
    complexity: str  # 复杂度: low/medium/high
    planning_required: bool  # 是否需要规划
    reasoning_depth: int  # 推理深度 (1-5)
    branching_factor: int  # 分支因子 (1-5)


class ThinkingModeSelector:
    """思考模式选择器"""

    # 模式特征定义
    MODE_CHARACTERISTICS: dict[ThinkingMode, ModeCharacteristics] = {
        ThinkingMode.REACT: ModeCharacteristics(
            name="ReAct",
            description="推理-行动循环模式",
            best_for=["探索性任务", "信息收集", "逐步推理"],
            complexity="medium",
            planning_required=False,
            reasoning_depth=3,
            branching_factor=1,
        ),
        ThinkingMode.PLAN: ModeCharacteristics(
            name="Plan",
            description="先规划后执行模式",
            best_for=["复杂任务", "多步骤任务", "需要明确计划的任务"],
            complexity="high",
            planning_required=True,
            reasoning_depth=4,
            branching_factor=1,
        ),
        ThinkingMode.SOPPLAN: ModeCharacteristics(
            name="SOPPlan",
            description="标准作业程序模式",
            best_for=["专业任务", "重复性任务", "有规范的任务"],
            complexity="medium",
            planning_required=True,
            reasoning_depth=3,
            branching_factor=1,
        ),
        ThinkingMode.EXECUTOR: ModeCharacteristics(
            name="Executor",
            description="直接执行模式",
            best_for=["简单任务", "单步任务", "明确指令任务"],
            complexity="low",
            planning_required=False,
            reasoning_depth=1,
            branching_factor=1,
        ),
        ThinkingMode.TREE_OF_THOUGHT: ModeCharacteristics(
            name="TreeOfThought",
            description="树状推理模式",
            best_for=["创造性任务", "多方案任务", "需要探索的任务"],
            complexity="high",
            planning_required=True,
            reasoning_depth=5,
            branching_factor=3,
        ),
    }

    def __init__(self):
        """初始化思考模式选择器"""
        logger.info("🧠 思考模式选择器初始化")

    async def select_mode(
        self,
        task_description: str,
        task_type: str = "general",
        complexity: str | None = None,
        domain: str | None = None,
        user_preference: ThinkingMode | None = None,
    ) -> ThinkingMode:
        """
        选择最适合的思考模式

        Args:
            task_description: 任务描述
            task_type: 任务类型 (professional/general)
            complexity: 任务复杂度 (low/medium/high)
            domain: 任务领域
            user_preference: 用户偏好模式(优先级最高)

        Returns:
            ThinkingMode: 选定的思考模式
        """
        logger.info(f"🧠 选择思考模式: {task_description[:50]}...")

        # 如果有用户偏好,直接使用
        if user_preference:
            logger.info(f"✅ 使用用户偏好模式: {user_preference.value}")
            return user_preference

        # 分析任务特征
        task_complexity = complexity or self._estimate_complexity(task_description)
        task_keywords = self._extract_keywords(task_description)

        # 根据任务类型选择模式
        if task_type == "professional":
            # 专业任务:优先使用SOPPlan或Plan模式
            if self._has_sop(task_keywords, domain):
                selected = ThinkingMode.SOPPLAN
            elif task_complexity == "high":
                selected = ThinkingMode.PLAN
            else:
                selected = ThinkingMode.REACT
        else:
            # 通用任务:根据复杂度选择
            if task_complexity == "low":
                selected = ThinkingMode.EXECUTOR
            elif task_complexity == "high":
                # 判断是否需要多方案探索
                if self._needs_exploration(task_description):
                    selected = ThinkingMode.TREE_OF_THOUGHT
                else:
                    selected = ThinkingMode.PLAN
            else:
                selected = ThinkingMode.REACT

        mode_info = self.MODE_CHARACTERISTICS[selected]
        logger.info(f"✅ 选择模式: {mode_info.name} - {mode_info.description}")

        return selected

    def _estimate_complexity(self, task_description: str) -> str:
        """
        估算任务复杂度

        Args:
            task_description: 任务描述

        Returns:
            str: 复杂度 (low/medium/high)
        """
        # 简单启发式规则
        low_complexity_keywords = ["查询", "搜索", "获取", "简单", "快速"]
        high_complexity_keywords = ["分析", "设计", "开发", "复杂", "综合", "多步骤"]

        task_lower = task_description.lower()

        if any(kw in task_lower for kw in low_complexity_keywords):
            return "low"
        elif any(kw in task_lower for kw in high_complexity_keywords):
            return "high"
        else:
            return "medium"

    def _extract_keywords(self, task_description: str) -> list[str]:
        """
        提取任务关键词

        Args:
            task_description: 任务描述

        Returns:
            list[str]: 关键词列表
        """
        # 简单的关键词提取
        # TODO: 实际实现中可以使用NLP工具
        import re

        words = re.findall(r"\w+", task_description.lower())
        # 过滤停用词
        stopwords = {"的", "是", "在", "和", "与", "或", "了", "要", "我", "你"}
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        return keywords[:10]  # 返回前10个关键词

    def _has_sop(self, keywords: list[str], domain: str) -> bool:
        """
        判断是否有标准作业程序

        Args:
            keywords: 任务关键词
            domain: 任务领域

        Returns:
            bool: 是否有SOP
        """
        # 专业领域通常有SOP
        sop_domains = ["patent", "legal", "trademark", "copyright"]
        return domain in sop_domains

    def _needs_exploration(self, task_description: str) -> bool:
        """
        判断是否需要多方案探索

        Args:
            task_description: 任务描述

        Returns:
            bool: 是否需要探索
        """
        exploration_keywords = ["设计", "创意", "方案", "优化", "改进", "创新"]
        task_lower = task_description.lower()
        return any(kw in task_lower for kw in exploration_keywords)

    def get_mode_info(self, mode: ThinkingMode) -> ModeCharacteristics:
        """
        获取模式信息

        Args:
            mode: 思考模式

        Returns:
            ModeCharacteristics: 模式特征
        """
        return self.MODE_CHARACTERISTICS[mode]

    def list_all_modes(self) -> dict[ThinkingMode, ModeCharacteristics]:
        """
        列出所有模式

        Returns:
            Dict: 所有模式
        """
        return self.MODE_CHARACTERISTICS.copy()


class ThinkingModeExecutor:
    """思考模式执行器"""

    def __init__(self):
        """初始化执行器"""
        self.selector = ThinkingModeSelector()
        logger.info("⚙️ 思考模式执行器初始化")

    async def execute_with_mode(
        self,
        task_description: str,
        task_type: str = "general",
        mode: ThinkingMode | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        使用指定或自动选择的模式执行任务

        Args:
            task_description: 任务描述
            task_type: 任务类型
            mode: 思考模式(None则自动选择)
            context: 执行上下文

        Returns:
            Dict: 执行结果
        """
        # 选择模式
        if mode is None:
            mode = await self.selector.select_mode(task_description, task_type)

        mode_info = self.selector.get_mode_info(mode)

        logger.info(f"🚀 使用 {mode_info.name} 模式执行任务")

        # 根据模式执行
        if mode == ThinkingMode.REACT:
            return await self._execute_react(task_description, context)
        elif mode == ThinkingMode.PLAN:
            return await self._execute_plan(task_description, context)
        elif mode == ThinkingMode.SOPPLAN:
            return await self._execute_sopplan(task_description, context)
        elif mode == ThinkingMode.EXECUTOR:
            return await self._execute_executor(task_description, context)
        elif mode == ThinkingMode.TREE_OF_THOUGHT:
            return await self._execute_tree_of_thought(task_description, context)
        else:
            raise ValueError(f"未知的思考模式: {mode}")

    async def _execute_react(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行ReAct模式"""
        # TODO: 实际实现ReAct循环
        return {
            "mode": "ReAct",
            "task": task_description,
            "steps": ["推理", "行动", "观察", "推理"],
            "result": "ReAct模式执行完成",
        }

    async def _execute_plan(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行Plan模式"""
        # TODO: 实际实现Plan模式
        return {
            "mode": "Plan",
            "task": task_description,
            "steps": ["制定计划", "执行计划", "验证结果"],
            "result": "Plan模式执行完成",
        }

    async def _execute_sopplan(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行SOPPlan模式"""
        # TODO: 实际实现SOPPlan模式
        return {
            "mode": "SOPPlan",
            "task": task_description,
            "steps": ["加载SOP", "执行SOP步骤", "记录结果"],
            "result": "SOPPlan模式执行完成",
        }

    async def _execute_executor(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行Executor模式"""
        # TODO: 实际实现Executor模式
        return {
            "mode": "Executor",
            "task": task_description,
            "steps": ["直接执行"],
            "result": "Executor模式执行完成",
        }

    async def _execute_tree_of_thought(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """执行TreeOfThought模式"""
        # TODO: 实际实现TreeOfThought模式
        return {
            "mode": "TreeOfThought",
            "task": task_description,
            "steps": ["生成方案A", "生成方案B", "生成方案C", "评估选择最佳方案"],
            "result": "TreeOfThought模式执行完成",
        }


# 便捷函数
async def select_thinking_mode(task_description: str, task_type: str = "general") -> ThinkingMode:
    """
    便捷的思考模式选择函数

    Args:
        task_description: 任务描述
        task_type: 任务类型

    Returns:
        ThinkingMode: 选定的思考模式
    """
    selector = ThinkingModeSelector()
    return await selector.select_mode(task_description, task_type)


async def execute_with_best_mode(
    task_description: str, task_type: str = "general"
) -> dict[str, Any]:
    """
    便捷的任务执行函数(自动选择最佳模式)

    Args:
        task_description: 任务描述
        task_type: 任务类型

    Returns:
        Dict: 执行结果
    """
    executor = ThinkingModeExecutor()
    return await executor.execute_with_mode(task_description, task_type)


__all__ = [
    "ModeCharacteristics",
    "ThinkingMode",
    "ThinkingModeExecutor",
    "ThinkingModeSelector",
    "execute_with_best_mode",
    "select_thinking_mode",
]
