#!/usr/bin/env python3

"""
小诺任务分解器
Xiaonuo Task Decomposer

功能:
1. 将用户意图分解为可执行的步骤
2. 确定步骤间的依赖关系
3. 分配智能体和资源
4. 设置成功标准和回退策略

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
import time
from typing import Any

from .xiaonuo_planner_engine import ExecutionStep, Intent, IntentType

logger = logging.getLogger(__name__)


# ========== 任务模板配置 ==========


class TaskTemplates:
    """任务模板库"""

    # 专利检索模板
    PATENT_RETRIEVAL = [
        {
            "id": "analyze_query",
            "description": "分析检索需求，构建检索策略",
            "agent": "xiaona",
            "action": "analyze_search_query",
            "estimated_time": 30,
            "dependencies": [],
        },
        {
            "id": "search_database",
            "description": "执行专利数据库检索",
            "agent": "xiaona",
            "action": "search_patents",
            "estimated_time": 60,
            "dependencies": ["analyze_query"],
            "required_resources": ["patent_db", "search_api"],
        },
        {
            "id": "analyze_results",
            "description": "分析和筛选检索结果",
            "agent": "xiaona",
            "action": "analyze_patents",
            "estimated_time": 45,
            "dependencies": ["search_database"],
        },
        {
            "id": "generate_report",
            "description": "生成检索报告",
            "agent": "xiaona",
            "action": "create_report",
            "estimated_time": 30,
            "dependencies": ["analyze_results"],
        },
    ]

    # 数据分析模板
    DATA_ANALYSIS = [
        {
            "id": "collect_data",
            "description": "收集分析所需数据",
            "agent": "xiaonuo",
            "action": "collect_data",
            "estimated_time": 60,
            "dependencies": [],
            "required_resources": ["database"],
        },
        {
            "id": "perform_analysis",
            "description": "执行数据分析",
            "agent": "xiaonuo",
            "action": "analyze_data",
            "estimated_time": 120,
            "dependencies": ["collect_data"],
        },
        {
            "id": "visualize_results",
            "description": "可视化分析结果",
            "agent": "xiaonuo",
            "action": "create_visualization",
            "estimated_time": 45,
            "dependencies": ["perform_analysis"],
        },
    ]

    # 系统优化模板
    SYSTEM_OPTIMIZATION = [
        {
            "id": "diagnose_performance",
            "description": "诊断系统性能瓶颈",
            "agent": "xiaonuo",
            "action": "diagnose_performance",
            "estimated_time": 120,
            "dependencies": [],
            "required_resources": ["monitoring_tools"],
        },
        {
            "id": "design_solution",
            "description": "设计优化方案",
            "agent": "xiaonuo",
            "action": "design_optimization",
            "estimated_time": 60,
            "dependencies": ["diagnose_performance"],
        },
        {
            "id": "implement_optimization",
            "description": "实施优化方案",
            "agent": "xiaonuo",
            "action": "implement_changes",
            "estimated_time": 300,
            "dependencies": ["design_solution"],
            "required_resources": ["development_tools"],
        },
        {
            "id": "verify_improvement",
            "description": "验证优化效果",
            "agent": "xiaonuo",
            "action": "verify_results",
            "estimated_time": 180,
            "dependencies": ["implement_optimization"],
        },
    ]

    # 智能体协调模板
    AGENT_COORDINATION = [
        {
            "id": "identify_agents",
            "description": "识别需要的智能体",
            "agent": "xiaonuo",
            "action": "identify_agents",
            "estimated_time": 10,
            "dependencies": [],
        },
        {
            "id": "distribute_tasks",
            "description": "分配任务给各智能体",
            "agent": "xiaonuo",
            "action": "distribute_tasks",
            "estimated_time": 15,
            "dependencies": ["identify_agents"],
        },
        {
            "id": "monitor_execution",
            "description": "监控执行进度",
            "agent": "xiaonuo",
            "action": "monitor_progress",
            "estimated_time": 60,
            "dependencies": ["distribute_tasks"],
        },
        {
            "id": "integrate_results",
            "description": "整合各智能体的结果",
            "agent": "xiaonuo",
            "action": "integrate_results",
            "estimated_time": 30,
            "dependencies": ["monitor_execution"],
        },
    ]


# ========== 任务分解器 ==========


class TaskDecomposer:
    """
    任务分解器

    核心功能:
    1. 基于意图类型选择模板
    2. 根据实体信息定制步骤
    3. 构建步骤间依赖关系
    4. 分配智能体资源
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates = TaskTemplates()
        self.decomposition_history: list[dict[str, Any] = []

    async def decompose(
        self,
        intent: Intent,
        context: dict[str, Any]]
    ) -> list[ExecutionStep]:
        """
        分解任务为执行步骤

        Args:
            intent: 用户意图
            context: 上下文信息

        Returns:
            List[ExecutionStep]: 执行步骤列表
        """
        self.logger.info(f"📋 开始任务分解: {intent.intent_type.value}")

        # 1. 根据意图类型选择模板
        template = self._select_template(intent)

        # 2. 根据实体信息定制步骤
        steps = self._customize_steps(template, intent, context)

        # 3. 构建依赖关系
        steps = self._build_dependencies(steps)

        # 4. 分配智能体
        steps = self._assign_agents(steps, intent)

        # 5. 生成唯一ID
        timestamp = int(time.time())
        for i, step in enumerate(steps):
            if not step.id or step.id.startswith("template_"):
                step.id = f"step_{timestamp}_{i}"

        # 记录历史
        self.decomposition_history.append({
            "intent": intent,
            "steps_count": len(steps),
            "timestamp": time.time(),
        })

        self.logger.info(f"   ✅ 任务分解完成: {len(steps)} 个步骤")
        return steps

    def _select_template(self, intent: Intent) -> list[dict[str, Any]]:
        """选择任务模板"""
        intent_type = intent.intent_type

        # 根据意图类型选择模板
        if intent_type == IntentType.QUERY:
            if "专利" in str(intent.context) or "patent" in str(intent.context).lower():
                return self.templates.PATENT_RETRIEVAL
            else:
                # 通用查询模板
                return [
                    {
                        "id": "understand_query",
                        "description": "理解查询需求",
                        "agent": "xiaonuo",
                        "action": "understand_query",
                        "estimated_time": 15,
                        "dependencies": [],
                    },
                    {
                        "id": "execute_query",
                        "description": "执行查询",
                        "agent": "xiaonuo",
                        "action": "execute_query",
                        "estimated_time": 30,
                        "dependencies": ["understand_query"],
                    },
                    {
                        "id": "format_results",
                        "description": "格式化查询结果",
                        "agent": "xiaonuo",
                        "action": "format_results",
                        "estimated_time": 15,
                        "dependencies": ["execute_query"],
                    },
                ]

        elif intent_type == IntentType.TASK:
            return [
                {
                    "id": "prepare_task",
                    "description": "准备任务执行环境",
                    "agent": "xiaonuo",
                    "action": "prepare_task",
                    "estimated_time": 20,
                    "dependencies": [],
                },
                {
                    "id": "execute_task",
                    "description": "执行任务",
                    "agent": "xiaonuo",
                    "action": "execute_task",
                    "estimated_time": 120,
                    "dependencies": ["prepare_task"],
                },
                {
                    "id": "verify_result",
                    "description": "验证执行结果",
                    "agent": "xiaonuo",
                    "action": "verify_result",
                    "estimated_time": 30,
                    "dependencies": ["execute_task"],
                },
            ]

        elif intent_type == IntentType.ANALYSIS:
            return self.templates.DATA_ANALYSIS

        elif intent_type == IntentType.OPTIMIZATION:
            return self.templates.SYSTEM_OPTIMIZATION

        elif intent_type == IntentType.COORDINATION:
            return self.templates.AGENT_COORDINATION

        elif intent_type == IntentType.CHAT:
            return [
                {
                    "id": "chat_response",
                    "description": "生成温暖回应",
                    "agent": "xiaonuo",
                    "action": "chat",
                    "estimated_time": 5,
                    "dependencies": [],
                },
            ]

        else:
            # 默认通用模板
            return [
                {
                    "id": "analyze_request",
                    "description": "分析用户请求",
                    "agent": "xiaonuo",
                    "action": "analyze",
                    "estimated_time": 20,
                    "dependencies": [],
                },
                {
                    "id": "process_request",
                    "description": "处理用户请求",
                    "agent": "xiaonuo",
                    "action": "process",
                    "estimated_time": 60,
                    "dependencies": ["analyze_request"],
                },
                {
                    "id": "respond",
                    "description": "返回处理结果",
                    "agent": "xiaonuo",
                    "action": "respond",
                    "estimated_time": 10,
                    "dependencies": ["process_request"],
                },
            ]

    def _customize_steps(
        self,
        template: list[dict[str, Any],
        intent: Intent,
        context: dict[str, Any]]
    ) -> list[ExecutionStep]:
        """定制步骤"""
        steps = []

        for template_step in template:
            # 创建执行步骤
            step = ExecutionStep(
                id=f"template_{template_step['id']}",
                description=template_step["description"],
                agent=template_step["agent"],
                action=template_step["action"],
                parameters={
                    "intent_type": intent.intent_type.value,
                    "primary_goal": intent.primary_goal,
                    "entities": intent.entities,
                },
                dependencies=template_step.get("dependencies", []).copy(),
                estimated_time=template_step.get("estimated_time", 30),
                required_resources=template_step.get("required_resources", []).copy(),
            )

            # 添加回退策略
            step.fallback_strategy = self._generate_fallback_strategy(step)

            steps.append(step)

        return steps

    def _build_dependencies(self, steps: list[ExecutionStep]) -> list[ExecutionStep]:
        """构建依赖关系"""
        # 确保依赖的步骤ID存在
        step_ids = {step.id for step in steps}

        for step in steps:
            valid_deps = []
            for dep in step.dependencies:
                # 检查依赖的步骤是否存在
                if dep in step_ids:
                    valid_deps.append(dep)
                # 如果依赖的步骤不存在，尝试找到相似的步骤ID
                else:
                    # 简单的模糊匹配
                    for step_id in step_ids:
                        if dep in step_id or step_id in dep:
                            valid_deps.append(step_id)
                            break

            step.dependencies = valid_deps

        return steps

    def _assign_agents(
        self,
        steps: list[ExecutionStep],
        intent: Intent
    ) -> list[ExecutionStep]:
        """分配智能体"""
        # 如果实体中指定了智能体，优先使用
        if intent.entities.get("agents"):
            # TODO: 根据用户指定的智能体偏好进行分配
            # 目前保留默认分配，可扩展为根据任务类型选择最优智能体
            pass

        return steps

    def _generate_fallback_strategy(self, step: ExecutionStep) -> str:
        """生成回退策略"""
        if step.action == "search_patents":
            return "如果主数据库检索失败，使用备用数据源"
        elif step.action == "analyze_data":
            return "如果分析失败，返回基础统计信息"
        elif step.action == "implement_changes":
            return "如果实施失败，回滚到原始状态"
        else:
            return "记录错误并通知用户"

    def get_decomposition_stats(self) -> dict[str, Any]:
        """获取分解统计信息"""
        if not self.decomposition_history:
            return {"total_decompositions": 0}

        total_steps = sum(d["steps_count"] for d in self.decomposition_history)

        return {
            "total_decompositions": len(self.decomposition_history),
            "total_steps_generated": total_steps,
            "average_steps_per_decomposition": total_steps / len(self.decomposition_history),
        }

