#!/usr/bin/env python3
"""
小诺网关规划引擎集成模块
Xiaonuo Gateway Planning Integration

将规划引擎集成到小诺统一网关,实现:
1. 自动规划请求识别
2. 计划-执行-反馈闭环
3. 动态调整支持
4. 并行任务优化

作者: 小诺·双鱼座
版本: v1.0.0 "网关集成"
创建时间: 2025-01-05
"""

from __future__ import annotations
import logging

# 添加项目路径
import sys
from pathlib import Path
from typing import Any

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.llm.glm47_client import get_glm47_client
from core.planning.explicit_planner import get_explicit_planner
from core.planning.plan_visualizer import get_plan_visualizer

logger = logging.getLogger(__name__)


class PlanningGatewayIntegration:
    """
    规划引擎网关集成

    处理小诺网关中的规划相关请求
    """

    def __init__(self):
        """初始化集成模块"""
        self.planner = get_explicit_planner()
        self.visualizer = get_plan_visualizer()
        self.llm_client = get_glm47_client()

        # 规划相关的意图关键词
        self.planning_keywords = [
            "检索",
            "搜索",
            "分析",
            "生成报告",
            "查找",
            "对比",
            "总结",
            "调研",
            "计划",
            "方案",
            "步骤",
            "流程",
        ]

        logger.info("🔗 规划引擎网关集成模块初始化完成")

    def should_use_planning(self, user_message: str, confidence: float = 0.0) -> tuple[bool, str]:
        """
        判断是否需要使用规划引擎

        Args:
            user_message: 用户消息
            confidence: 意图分类置信度

        Returns:
            (是否使用规划, 原因)
        """
        # 如果置信度较低,使用规划模式
        if confidence < 0.7:
            return True, "低置信度复杂任务,建议使用规划模式"

        # 检查是否包含规划关键词
        has_keyword = any(keyword in user_message for keyword in self.planning_keywords)
        if has_keyword:
            return (
                True,
                f"检测到规划关键词: {[k for k in self.planning_keywords if k in user_message]}",
            )

        # 检查消息长度(复杂任务通常较长)
        if len(user_message) > 50:
            return True, "复杂任务(消息长度>50字符),建议使用规划模式"

        return False, "简单任务,直接执行"

    async def process_with_planning(
        self, user_message: str, context: dict[str, Any]  | None = None, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        使用规划引擎处理用户请求

        Args:
            user_message: 用户消息
            context: 上下文信息
            session_id: 会话ID

        Returns:
            处理结果
        """
        logger.info(f"📋 使用规划引擎处理: {user_message[:50]}...")

        try:
            # 1. 创建计划
            from core.planning.unified_planning_interface import PlanningRequest, Priority

            plan_request = PlanningRequest(
                title=f"会话{session_id}的规划任务",
                description=user_message,
                context=context or {},
                requirements=["准确理解用户需求", "提供详细的执行结果", "确保结果质量"],
                constraints=[],
                priority=Priority.HIGH,
            )

            plan_result = await self.planner.create_plan(plan_request)

            if not plan_result.success:
                return {
                    "success": False,
                    "error": f"计划创建失败: {plan_result.feedback}",
                    "mode": "planning_failed",
                }

            plan_id = plan_result.plan_id

            # 2. 获取计划详情
            plan = await self.planner.get_plan(plan_id)

            # 3. 生成计划可视化
            plan_viz = self.visualizer.to_text(plan)

            # 4. 自动批准(网关模式下)
            await self.planner.await_user_approval(plan_id, approved=True, comments="网关自动批准")

            # 5. 识别并行任务
            parallel_groups = await self.planner.identify_parallel_tasks(plan_id)

            # 6. 执行计划
            execution_result = await self.planner.execute_plan(plan_id)

            # 7. 生成最终响应
            if execution_result["success"]:
                final_output = execution_result.get("final_output", {})

                response = f"""
✅ 规划任务执行完成!

📋 执行计划:{plan.name}
━━━━━━━━━━━━━━━━━━━━━━━━

{plan_viz}

━━━━━━━━━━━━━━━━━━━━━━━━
📊 执行结果:
- 总步骤:{final_output.get('total_steps', 0)}
- 完成步骤:{final_output.get('completed_steps', 0)}
- 成功率:{final_output.get('success_rate', 0):.1%}
- 执行时间:{final_output.get('execution_time', 0):.1f}分钟

{final_output.get('summary', '')}

并行任务:{'已识别' if parallel_groups else '未发现'}
"""

                return {
                    "success": True,
                    "response": response,
                    "mode": "planning",
                    "plan_id": plan_id,
                    "execution_result": execution_result,
                    "parallel_groups": parallel_groups,
                }
            else:
                return {
                    "success": False,
                    "error": execution_result.get("error", "执行失败"),
                    "mode": "planning",
                    "plan_id": plan_id,
                    "failed_steps": execution_result.get("failed_steps", []),
                }

        except Exception as e:
            logger.error(f"❌ 规划引擎处理失败: {e}", exc_info=True)
            return {"success": False, "error": str(e), "mode": "planning_error"}

    async def suggest_parallel_execution(self, plan_id: str) -> dict[str, Any]:
        """
        建议并行执行方案

        Args:
            plan_id: 计划ID

        Returns:
            并行执行建议
        """
        logger.info(f"🔍 分析并行执行方案: {plan_id}")

        try:
            plan = await self.planner.get_plan(plan_id)
            if not plan:
                return {"error": "计划不存在"}

            # 识别并行任务
            parallel_groups = await self.planner.identify_parallel_tasks(plan_id)

            if not parallel_groups:
                return {
                    "plan_id": plan_id,
                    "has_parallel_tasks": False,
                    "message": "未发现可并行的任务",
                    "optimization_suggestion": "当前任务需要顺序执行",
                }

            # 生成优化建议
            time_saved = 0
            for group in parallel_groups:
                # 假设每组任务可以节省最长时间步骤的时间
                group_steps = [s for s in plan.steps if s.step_number in group]
                if group_steps:
                    max_duration = max(
                        s.estimated_duration.total_seconds() / 60 for s in group_steps
                    )
                    time_saved += max_duration * (len(group) - 1)

            return {
                "plan_id": plan_id,
                "has_parallel_tasks": True,
                "parallel_groups": parallel_groups,
                "total_groups": len(parallel_groups),
                "estimated_time_saved_minutes": round(time_saved, 1),
                "optimization_suggestion": f"通过并行执行可以节省约{time_saved/60:.1f}小时",
                "execution_plan": self._generate_parallel_execution_plan(plan, parallel_groups),
            }

        except Exception as e:
            logger.error(f"❌ 并行执行分析失败: {e}", exc_info=True)
            return {"error": str(e)}

    def _generate_parallel_execution_plan(self, plan, parallel_groups: list) -> dict[str, Any]:
        """生成并行执行计划"""
        stages = []

        # 构建执行阶段
        processed_steps = set()
        stage_num = 1

        while len(processed_steps) < len(plan.steps):
            current_stage_steps = []

            # 找出当前阶段可以执行的步骤
            for step in plan.steps:
                if step.step_number in processed_steps:
                    continue

                # 检查依赖是否满足
                deps_satisfied = all(dep in processed_steps for dep in step.dependencies)

                if deps_satisfied:
                    current_stage_steps.append(step.step_number)

            # 找出可以并行的步骤组
            stage_parallel_groups = []
            for group in parallel_groups:
                if all(s in current_stage_steps for s in group):
                    stage_parallel_groups.append(group)

            if stage_parallel_groups:
                stages.append(
                    {
                        "stage": stage_num,
                        "type": "parallel",
                        "groups": stage_parallel_groups,
                        "steps": current_stage_steps,
                    }
                )
            else:
                stages.append(
                    {"stage": stage_num, "type": "sequential", "steps": current_stage_steps}
                )

            processed_steps.update(current_stage_steps)
            stage_num += 1

        return {"total_stages": len(stages), "stages": stages}


# 全局实例
planning_gateway_integration = None


def get_planning_gateway_integration() -> PlanningGatewayIntegration:
    """获取规划网关集成单例"""
    global planning_gateway_integration
    if planning_gateway_integration is None:
        planning_gateway_integration = PlanningGatewayIntegration()
    return planning_gateway_integration
