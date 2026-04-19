#!/usr/bin/env python3
from __future__ import annotations
"""
赋能的总体设计部
Empowered General Design Department

基于钱学森系统工程思想,建立具有决策权威的总体设计部:
- 协调者:统筹智能体工作
- 综合者:集成多方意见
- 决策者:做出权威判断

作者: 小诺·双鱼公主
创建时间: 2025-12-27
版本: v2.0.0 "赋能版"
"""

import asyncio
import logging

# 添加项目路径
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.decision.conflict_resolver import ConflictResolver
from core.decision.integrated_decision_engine import (
    AgentOpinion,
    Decision,
    get_decision_engine,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class TaskType(Enum):
    """任务类型分类"""

    PATENT_ANALYSIS = "patent_analysis"
    LEGAL_RESEARCH = "legal_research"
    IP_MANAGEMENT = "ip_management"
    MEDIA_OPERATION = "media_operation"
    GENERAL_QUERY = "general_query"
    DECISION_SUPPORT = "decision_support"
    COORDINATION = "coordination"


class Priority(Enum):
    """任务优先级"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class AgentRole(Enum):
    """智能体角色"""

    XIAONUO = "小诺"
    XIANA = "小娜"
    XIAOCHEN = "小宸"


@dataclass
class Task:
    """任务对象"""

    task_id: str
    task_type: TaskType
    description: str
    requester: str
    priority: Priority = Priority.MEDIUM
    context: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    assigned_to: list[AgentRole] = field(default_factory=list)
    status: str = "pending"
    decision: Decision | None = None


@dataclass
class TaskExecutionResult:
    """任务执行结果"""

    task_id: str
    success: bool
    decision: Decision
    execution_summary: str
    next_actions: list[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EmpoweredGeneralDesignDepartment:
    """
    赋能的总体设计部

    具有协调、综合、决策三位一体职能
    """

    def __init__(self):
        """初始化赋能的总体设计部"""
        self.name = "Athena赋能总体设计部"
        self.version = "v2.0.0"

        # 核心组件
        self.decision_engine = get_decision_engine()
        self.conflict_resolver = ConflictResolver()

        # 任务管理
        self.task_queue: list[Task] = []
        self.completed_tasks: list[Task] = []
        self.decision_history: list[Decision] = []

        # 任务路由规则
        self.routing_rules = self._init_routing_rules()

        # 决策权限配置
        self.decision_authority = self._init_decision_authority()

        logger.info(f"🏛️ {self.name} ({self.version}) 初始化完成")
        logger.info("   ✅ 协调职能: 就绪")
        logger.info("   ✅ 综合职能: 就绪")
        logger.info("   ✅ 决策职能: 就绪")

    def _init_routing_rules(self) -> dict[TaskType, list[AgentRole]]:
        """初始化任务路由规则"""
        return {
            TaskType.PATENT_ANALYSIS: [AgentRole.XIANA],
            TaskType.LEGAL_RESEARCH: [AgentRole.XIANA],
            TaskType.IP_MANAGEMENT: [AgentRole.XIANA],
            TaskType.MEDIA_OPERATION: [AgentRole.XIAOCHEN],
            TaskType.GENERAL_QUERY: [AgentRole.XIAONUO],
            TaskType.DECISION_SUPPORT: [AgentRole.XIANA, AgentRole.XIAONUO],
            TaskType.COORDINATION: [AgentRole.XIAONUO],
        }

    def _init_decision_authority(self) -> dict[str, Any]:
        """初始化决策权限配置"""
        return {
            "can_arbitrate_conflicts": True,  # 可以仲裁冲突
            "can_make_final_decision": True,  # 可以做最终决策
            "can_allocate_resources": True,  # 可以调配资源
            "can_require_quality": True,  # 可以要求质量
            "consult_threshold": 0.7,  # 低于此阈值需征求爸爸意见
            "override_conditions": [  # 必须请示爸爸的情况
                "涉及重大资源分配",
                "存在不可调和的根本分歧",
                "超出专业领域",
            ],
        }

    async def submit_task(
        self,
        description: str,
        task_type: TaskType = TaskType.GENERAL_QUERY,
        requester: str = "徐健",
        priority: Priority = Priority.MEDIUM,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        提交任务到总体设计部

        Args:
            description: 任务描述
            task_type: 任务类型
            requester: 请求者
            priority: 优先级
            context: 上下文信息

        Returns:
            任务ID
        """
        task_id = f"task_{int(datetime.now().timestamp())}"
        task = Task(
            task_id=task_id,
            task_type=task_type,
            description=description,
            requester=requester,
            priority=priority,
            context=context or {},
        )

        # 确定执行智能体
        task.assigned_to = self.routing_rules.get(task_type, [AgentRole.XIAONUO])

        self.task_queue.append(task)

        logger.info(f"📥 任务已提交: {task_id}")
        logger.info(f"   描述: {description}")
        logger.info(f"   类型: {task_type.value}")
        logger.info(f"   分配给: {[a.value for a in task.assigned_to]}")

        return task_id

    async def process_task(self, task: Task) -> TaskExecutionResult:
        """
        处理任务(赋能版)

        不再只是简单转发,而是:
        1. 收集智能体意见
        2. 启动综合集成决策
        3. 如有冲突进行仲裁
        4. 形成权威决策
        5. 给出执行建议

        Args:
            task: 任务对象

        Returns:
            TaskExecutionResult: 任务执行结果
        """
        task.status = "processing"
        logger.info(f"\n{'='*70}")
        logger.info(f"⚙️ 开始处理任务: {task.task_id}")
        logger.info(f"{'='*70}")

        # 第1步:收集智能体意见
        logger.info("\n[第1步]收集智能体意见...")
        agent_opinions = await self._collect_agent_opinions(task)

        # 第2步:检测冲突

        logger.info("\n[第2步]检测意见冲突...")
        conflict_analysis = await self.decision_engine._detect_conflicts(agent_opinions)

        # 第3步:如果有冲突,启动仲裁
        if conflict_analysis.has_conflict:
            logger.info("\n[第3步]启动冲突仲裁...")
            arbitration = await self.conflict_resolver.resolve(agent_opinions, conflict_analysis)
            logger.info(f"   仲裁结果: {arbitration.result.value}")
            # 使用仲裁后的意见
            agent_opinions = arbitration.adjusted_opinions

        # 第4步:综合集成决策
        logger.info("\n[第4步]启动综合集成决策...")
        decision = await self.decision_engine.make_decision(
            task_id=task.task_id,
            task_description=task.description,
            agent_opinions=agent_opinions,
            context=task.context,
        )

        # 第5步:评估决策质量,判断是否需要请示爸爸
        logger.info("\n[第5步]评估决策质量...")
        needs_consultation = await self._evaluate_decision_quality(decision)

        if needs_consultation:
            logger.warning("   ⚠️ 决策置信度较低或涉及重大问题,建议征求爸爸意见")
            decision.final_conclusion += (
                "\n\n[小诺提示]:此决策置信度较低或涉及重大问题,建议爸爸最终把关。"
            )

        # 第6步:生成执行建议
        logger.info("\n[第6步]生成执行建议...")
        execution_summary, next_actions = await self._generate_execution_plan(decision)

        # 更新任务状态
        task.status = "completed"
        task.decision = decision
        self.completed_tasks.append(task)
        self.task_queue.remove(task)

        logger.info(f"\n{'='*70}")
        logger.info(f"✅ 任务处理完成: {task.task_id}")
        logger.info(f"{'='*70}\n")

        return TaskExecutionResult(
            task_id=task.task_id,
            success=decision.final_confidence > 0.5,
            decision=decision,
            execution_summary=execution_summary,
            next_actions=next_actions,
        )

    async def _collect_agent_opinions(self, task: Task) -> list[AgentOpinion]:
        """
        收集智能体意见

        实际实现中会调用各智能体的API
        这里做模拟
        """
        opinions = []

        for agent_role in task.assigned_to:
            # 模拟调用智能体
            opinion = await self._call_agent_simulation(agent_role, task)
            opinions.append(opinion)

        return opinions

    async def _call_agent_simulation(self, agent_role: AgentRole, task: Task) -> AgentOpinion:
        """
        模拟调用智能体(实际应该调用真实API)

        这里提供模拟实现,实际应该:
        1. 调用智能体API
        2. 获取真实意见
        3. 返回AgentOpinion
        """
        # 模拟不同智能体的意见
        if agent_role == AgentRole.XIANA:
            return AgentOpinion(
                agent_name="小娜",
                opinion=f"从法律角度分析,'{task.description}'涉及专利法相关规定。",
                confidence=0.85,
                evidence=["专利法第25条", "审查指南相关规定"],
                reasoning="基于专利法律专业知识进行分析",
            )
        elif agent_role == AgentRole.XIAOCHEN:
            return AgentOpinion(
                agent_name="小宸",
                opinion=f"从运营角度,'{task.description}'需要考虑内容呈现和用户体验。",
                confidence=0.80,
                evidence=["用户反馈", "运营数据"],
                reasoning="基于自媒体运营经验进行分析",
            )
        else:  # XIAONUO
            return AgentOpinion(
                agent_name="小诺",
                opinion=f"作为总调度官,我综合各维度分析'{task.description}'。",
                confidence=0.90,
                evidence=["系统整体情况", "各智能体专业意见"],
                reasoning="基于平台整体视角进行综合判断",
            )

    async def _evaluate_decision_quality(self, decision: Decision) -> bool:
        """
        评估决策质量

        判断是否需要征求爸爸意见

        Returns:
            bool: True表示需要请示
        """
        # 检查置信度
        if decision.final_confidence < self.decision_authority["consult_threshold"]:
            return True

        # 检查是否涉及重大问题
        task_desc_lower = decision.task_description.lower()
        for condition in self.decision_authority["override_conditions"]:
            if condition.lower() in task_desc_lower:
                return True

        # 检查是否有根本分歧
        if decision.integration_iterations:
            final_iteration = decision.integration_iterations[-1]
            if final_iteration.remaining_divergences:
                return True

        return False

    async def _generate_execution_plan(self, decision: Decision) -> tuple[str, list[str]]:
        """
        生成执行计划

        Returns:
            (执行摘要, 下一步行动列表)
        """
        execution_summary = f"""
[总体设计部决策]

任务: {decision.task_description}
定性方向: {decision.qualitative_direction.direction.value}

参与智能体: {', '.join([op.agent_name for op in decision.agent_opinions])}

综合集成过程: {len(decision.integration_iterations)}轮迭代
最终共识: {decision.integration_iterations[-1].consensus_level.value if decision.integration_iterations else '无'}

[决策结论]
{decision.final_conclusion}

[决策依据]
置信度: {decision.final_confidence:.1%}
决策方法: {decision.decision_methodology}
"""

        next_actions = []
        if decision.final_confidence >= 0.8:
            next_actions.append("✅ 决策置信度高,建议直接执行")
        elif decision.final_confidence >= 0.6:
            next_actions.append("⚠️ 决策置信度中等,建议谨慎执行并持续关注")
        else:
            next_actions.append("❌ 决策置信度较低,建议征求爸爸意见或补充信息")

        # 根据智能体意见生成具体行动
        for opinion in decision.agent_opinions:
            if "建议" in opinion.opinion:
                next_actions.append(f"• 参考{opinion.agent_name}的建议")

        return execution_summary, next_actions

    async def batch_process_tasks(self, task_ids: list[str]) -> list[TaskExecutionResult]:
        """批量处理任务"""
        results = []
        for task_id in task_ids:
            task = next((t for t in self.task_queue if t.task_id == task_id), None)
            if task:
                result = await self.process_task(task)
                results.append(result)
        return results

    def get_status(self) -> dict[str, Any]:
        """获取总体设计部状态"""
        pending_count = len(self.task_queue)
        completed_count = len(self.completed_tasks)

        decision_stats = self.decision_engine.get_decision_statistics()

        return {
            "name": self.name,
            "version": self.version,
            "pending_tasks": pending_count,
            "completed_tasks": completed_count,
            "decision_authority": self.decision_authority,
            "decision_statistics": decision_stats,
        }

    def get_decision_history(self, limit: int = 10) -> list[Decision]:
        """获取决策历史"""
        return self.decision_history[-limit:]


# 全局实例
_department: EmpoweredGeneralDesignDepartment | None = None


def get_empowered_department() -> EmpoweredGeneralDesignDepartment:
    """获取赋能总体设计部单例"""
    global _department
    if _department is None:
        _department = EmpoweredGeneralDesignDepartment()
    return _department


# 便捷函数
async def submit_and_process(
    description: str,
    task_type: TaskType = TaskType.GENERAL_QUERY,
    requester: str = "徐健",
    priority: Priority = Priority.MEDIUM,
) -> TaskExecutionResult:
    """便捷函数:提交并处理任务"""
    department = get_empowered_department()
    task_id = await department.submit_task(description, task_type, requester, priority)
    task = next(t for t in department.task_queue if t.task_id == task_id)
    return await department.process_task(task)


if __name__ == "__main__":

    async def test():
        """测试赋能的总体设计部"""
        print("🧪 测试赋能的总体设计部")
        print("=" * 70)

        department = get_empowered_department()

        # 测试1:提交并处理单个任务
        print("\n📋 测试1: 单任务处理")
        result = await submit_and_process(
            description="选择专利检索系统的向量数据库方案", task_type=TaskType.DECISION_SUPPORT
        )

        print("\n✅ 任务处理结果:")
        print(f"成功: {result.success}")
        print(f"\n{result.execution_summary}")
        print("\n下一步行动:")
        for action in result.next_actions:
            print(f"  {action}")

        # 测试2:查看状态
        print("\n📊 测试2: 系统状态")
        status = department.get_status()
        print(f"待处理任务: {status['pending_tasks']}")
        print(f"已完成任务: {status['completed_tasks']}")

        # 测试3:决策历史
        print("\n📜 测试3: 决策历史")
        history = department.get_decision_history(limit=3)
        for i, decision in enumerate(history, 1):
            print(f"\n决策{i}: {decision.task_description[:50]}...")
            print(f"  置信度: {decision.final_confidence:.2%}")

    asyncio.run(test())
