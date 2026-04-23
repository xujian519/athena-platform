#!/usr/bin/env python3
from __future__ import annotations
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
from typing import Any

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
        complexity: Optional[str] = None,
        domain: Optional[str] = None,
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
        context: Optional[dict[str, Any]] = None,
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
        """
        执行ReAct模式

        ReAct = Reasoning + Acting
        循环: 思考 -> 行动 -> 观察 -> 思考...
        """
        steps = []
        max_iterations = 5
        iteration = 0
        current_thought = task_description

        while iteration < max_iterations:
            iteration += 1

            # 思考阶段
            thought = f"思考#{iteration}: 分析 '{current_thought[:50]}...'"
            steps.append(thought)

            # 行动阶段 (这里简化为生成行动描述)
            action = f"行动#{iteration}: 基于 {thought}"
            steps.append(action)

            # 观察阶段 (模拟观察结果)
            observation = f"观察#{iteration}: 行动已完成"
            steps.append(observation)

            # 简单的终止条件
            if iteration >= 3:
                break

        return {
            "mode": "ReAct",
            "task": task_description,
            "steps": steps,
            "iterations": iteration,
            "result": f"ReAct模式执行完成 (共{iteration}轮)",
        }

    async def _execute_plan(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行Plan模式

        Plan模式: 先制定详细计划,再按计划执行
        1. 分析任务,分解步骤
        2. 制定执行计划
        3. 按顺序执行各步骤
        4. 验证结果
        """
        # 步骤1: 任务分解
        task_analysis = f"分析任务: {task_description}"
        steps = [task_analysis]

        # 步骤2: 制定计划 (根据任务复杂度分解)
        plan_steps = self._generate_plan_steps(task_description)
        steps.append(f"制定计划: 共{len(plan_steps)}个步骤")

        # 步骤3: 执行计划
        for i, step in enumerate(plan_steps, 1):
            steps.append(f"执行步骤{i}: {step}")

        # 步骤4: 验证结果
        steps.append("验证结果: 计划执行完成")

        return {
            "mode": "Plan",
            "task": task_description,
            "plan": plan_steps,
            "steps": steps,
            "result": "Plan模式执行完成",
        }

    def _generate_plan_steps(self, task_description: str) -> list[str]:
        """根据任务描述生成计划步骤"""
        # 简单的计划生成逻辑
        if "分析" in task_description:
            return ["收集数据", "分析数据", "生成报告", "审核结果"]
        elif "开发" in task_description or "实现" in task_description:
            return ["需求分析", "设计方案", "编码实现", "测试验证"]
        elif "检索" in task_description or "搜索" in task_description:
            return ["确定检索策略", "执行检索", "筛选结果", "整理输出"]
        else:
            return ["理解任务", "制定方案", "执行操作", "确认结果"]

    async def _execute_sopplan(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行SOPPlan模式

        SOPPlan = Standard Operating Procedure Plan
        基于标准作业程序的规划执行:
        1. 识别适用的SOP
        2. 加载SOP步骤
        3. 按SOP执行
        4. 记录执行日志
        """
        steps = []

        # 步骤1: 识别SOP
        sop_id = self._identify_sop(task_description, context)
        steps.append(f"识别SOP: {sop_id}")

        # 步骤2: 加载SOP
        sop_steps = self._load_sop(sop_id)
        steps.append(f"加载SOP: 共{len(sop_steps)}个标准步骤")

        # 步骤3: 按SOP执行
        execution_log = []
        for i, sop_step in enumerate(sop_steps, 1):
            steps.append(f"执行SOP步骤{i}: {sop_step}")
            execution_log.append({"step": i, "action": sop_step, "status": "completed"})

        # 步骤4: 记录结果
        steps.append("记录执行日志: SOP执行完成")

        return {
            "mode": "SOPPlan",
            "task": task_description,
            "sop_id": sop_id,
            "sop_steps": sop_steps,
            "steps": steps,
            "execution_log": execution_log,
            "result": "SOPPlan模式执行完成",
        }

    def _identify_sop(self, task_description: str, context: dict[str, Any]) -> str:
        """识别适用的SOP"""
        # 简单的SOP识别逻辑
        if "专利" in task_description or "patent" in task_description.lower():
            return "SOP-PATENT-001"
        elif "商标" in task_description or "trademark" in task_description.lower():
            return "SOP-TM-001"
        elif "侵权" in task_description:
            return "SOP-INFRINGE-001"
        else:
            return "SOP-GEN-001"

    def _load_sop(self, sop_id: str) -> list[str]:
        """加载SOP步骤"""
        # SOP库 (简化版)
        sop_library = {
            "SOP-PATENT-001": [
                "接收技术交底书",
                "检索现有技术",
                "分析技术特征",
                "撰写权利要求",
                "撰写说明书",
                "审核质量",
            ],
            "SOP-TM-001": [
                "确认商标信息",
                "查询近似商标",
                "评估注册风险",
                "准备申请材料",
                "提交申请",
            ],
            "SOP-INFRINGE-001": [
                "收集证据",
                "分析侵权要素",
                "比对技术特征",
                "评估侵权风险",
                "制定应对策略",
            ],
            "SOP-GEN-001": ["理解需求", "制定方案", "执行操作", "验证结果"],
        }
        return sop_library.get(sop_id, ["执行标准流程"])

    async def _execute_executor(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行Executor模式

        Executor模式: 直接执行,适用于简单任务
        - 不需要规划或推理
        - 直接调用相应的工具或服务
        - 快速返回结果
        """
        import time

        start_time = time.time()

        # 直接执行 (简化实现)
        steps = ["直接执行任务"]
        execution_time = time.time() - start_time

        # 根据任务类型选择执行方式
        if "查询" in task_description or "搜索" in task_description:
            result = "查询结果已返回"
        elif "获取" in task_description or "读取" in task_description:
            result = "数据已获取"
        else:
            result = "任务执行完成"

        return {
            "mode": "Executor",
            "task": task_description,
            "steps": steps,
            "execution_time_ms": round(execution_time * 1000, 2),
            "result": result,
        }

    async def _execute_tree_of_thought(
        self, task_description: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        执行TreeOfThought模式

        TreeOfThought = 树状推理
        1. 生成多个候选方案
        2. 评估每个方案
        3. 选择最佳路径
        4. 执行选定的方案
        """
        steps = []

        # 步骤1: 生成多个候选方案
        steps.append("🌳 生成思维树分支...")
        branches = self._generate_thought_branches(task_description, num_branches=3)
        for i, branch in enumerate(branches, 1):
            steps.append(f"  分支{i}: {branch['name']}")

        # 步骤2: 评估每个分支
        steps.append("📊 评估各分支...")
        evaluations = []
        for i, branch in enumerate(branches, 1):
            score = self._evaluate_thought_branch(branch, task_description)
            evaluations.append({"branch": i, "score": score, "name": branch["name"]})
            steps.append(f"  分支{i}评分: {score}/10")

        # 步骤3: 选择最佳分支
        best_branch = max(evaluations, key=lambda x: x["score"])
        steps.append(f"✅ 选择最佳分支: {best_branch['name']} (评分: {best_branch['score']})")

        # 步骤4: 执行选定分支
        steps.append(f"🚀 执行分支: {best_branch['name']}")
        execution_result = await self._execute_selected_branch(
            branches[best_branch["branch"] - 1], task_description
        )
        steps.append(f"✨ 执行完成: {execution_result}")

        return {
            "mode": "TreeOfThought",
            "task": task_description,
            "branches": branches,
            "evaluations": evaluations,
            "selected_branch": best_branch,
            "steps": steps,
            "result": f"TreeOfThought模式执行完成 - 选择了'{best_branch['name']}'方案",
        }

    def _generate_thought_branches(
        self, task_description: str, num_branches: int = 3
    ) -> list[dict[str, Any]]:
        """生成思维树的分支(候选方案)"""
        # 简单的分支生成逻辑
        base_branches = [
            {"name": "方案A-保守方案", "approach": "稳健", "risk": "low"},
            {"name": "方案B-平衡方案", "approach": "平衡", "risk": "medium"},
            {"name": "方案C-创新方案", "approach": "创新", "risk": "high"},
        ]
        return base_branches[:num_branches]

    def _evaluate_thought_branch(
        self, branch: dict[str, Any], task_description: str
    ) -> int:
        """评估分支得分 (1-10)"""
        # 简单的评分逻辑
        base_score = 5
        if "保守" in branch["name"]:
            base_score += 2  # 保守方案更稳妥
        if "创新" in task_description:
            base_score += 1  # 创新任务偏好创新方案
        if "专利" in task_description:
            base_score += 1  # 专利任务需要创新
        return min(base_score, 10)

    async def _execute_selected_branch(
        self, branch: dict[str, Any], task_description: str
    ) -> str:
        """执行选定的分支"""
        # 简化的执行逻辑
        return f"已执行{branch['name']}, 采用{branch['approach']}方法"


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
