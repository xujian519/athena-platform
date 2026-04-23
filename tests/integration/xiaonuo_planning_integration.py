"""
小诺规划集成测试模块
Xiaonuo Planning Integration Test Module

提供测试用的小诺规划集成功能
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PlanningStatus(Enum):
    """规划状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PlanStep:
    """规划步骤"""
    step_id: str
    description: str
    status: PlanningStatus = PlanningStatus.PENDING
    dependencies: list[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class IntegrationPlan:
    """集成规划"""
    plan_id: str
    steps: list[PlanStep]
    current_step: str | None = None
    status: PlanningStatus = PlanningStatus.PENDING

class XiaonuoPlanningIntegration:
    """小诺规划集成"""

    def __init__(self):
        self.plans: dict[str, IntegrationPlan] = {}

    async def create_plan(self, tasks: list[dict[str, Any]) -> IntegrationPlan:
        """创建规划"""
        plan_id = f"plan_{len(self.plans) + 1}"
        steps = [
            PlanStep(
                step_id=f"step_{i}",
                description=task.get("description", ""),
                dependencies=task.get("dependencies", [])
            )
            for i, task in enumerate(tasks)
        ]
        plan = IntegrationPlan(plan_id=plan_id, steps=steps)
        self.plans[plan_id] = plan
        return plan

    async def execute_plan(self, plan_id: str) -> bool:
        """执行规划"""
        if plan_id not in self.plans:
            return False

        plan = self.plans[plan_id]
        plan.status = PlanningStatus.IN_PROGRESS

        # TODO: 实现实际的执行逻辑
        plan.status = PlanningStatus.COMPLETED
        return True

    def get_plan_status(self, plan_id: str) -> PlanningStatus | None:
        """获取规划状态"""
        if plan_id in self.plans:
            return self.plans[plan_id].status
        return None

__all__ = [
    'XiaonuoPlanningIntegration',
    'IntegrationPlan',
    'PlanStep',
    'PlanningStatus'
]

# 添加别名,使测试能够导入
XiaonuoEnhancedAgent = XiaonuoPlanningIntegration
__all__.append('XiaonuoEnhancedAgent')
