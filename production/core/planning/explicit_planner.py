#!/usr/bin/env python3
"""
显式规划器 - Explicit Planner
按照《智能体设计模式》书中的标准实现规划模式

实现功能:
1. 任务分解为清晰的执行步骤
2. 生成类似Google DeepResearch的计划清单
3. 等待用户确认后执行
4. 支持动态调整

作者: 小诺·双鱼座
版本: v1.0.0 "显式规划"
创建时间: 2025-01-05
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# 导入LLM客户端
try:
    from core.llm.glm47_client import get_glm47_client
except ImportError:
    # 兼容性处理: 如果GLM客户端不可用，使用None
    get_glm47_client = None  # type: ignore
    logger.warning("GLM-47客户端不可用，部分功能可能受限")

from .unified_planning_interface import (
    BasePlanner,
    PlannerType,
    PlanningRequest,
    PlanningResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class PlanStepStatus(Enum):
    """规划步骤状态"""

    PENDING = "pending"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """规划步骤"""

    step_id: str = field(default_factory=lambda: str(uuid4()))
    step_number: int = 0
    name: str = ""
    description: str = ""
    tool: str | None = None
    tool_parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    confidence: float = 0.8
    estimated_duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    status: PlanStepStatus = PlanStepStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """执行计划"""

    plan_id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str = ""
    name: str = ""
    description: str = ""
    steps: list[PlanStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    total_confidence: float = 0.0
    total_duration: timedelta = field(default_factory=lambda: timedelta())
    requires_approval: bool = True
    approved: bool = False
    approval_comments: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    parallel_groups: list[list[int]] = field(default_factory=list)  # 并行任务组
    execution_mode: str = "sequential"  # sequential, parallel, mixed


# 规划生成的提示词模板
PLAN_GENERATION_PROMPT = """
你是一个专业的任务规划专家。你的职责是将用户的复杂任务分解为清晰、可执行的步骤。

## 用户任务
{task_description}

## 任务上下文
{context}

## 可用工具
{available_tools}

## 要求
1. 将任务分解为 3-10 个具体、可执行的步骤
2. 每个步骤必须明确要做什么
3. 标注每个步骤需要使用的工具
4. 识别步骤之间的依赖关系
5. 评估每个步骤的成功概率(0-1之间)
6. 预估每个步骤的执行时间(分钟)
7. 确保步骤之间的逻辑顺序合理

## 输出格式
请严格按照以下JSON格式输出:

```json
{{
  "plan_name": "执行计划的简短名称",
  "plan_description": "计划的总体描述",
  "steps": [
    {{
      "step_number": 1,
      "name": "步骤名称",
      "description": "详细描述该步骤要做什么",
      "tool": "工具名称(从可用工具列表中选择)",
      "tool_parameters": {{
        "param1": "value1"
      }},
      "dependencies": [],
      "confidence": 0.9,
      "estimated_duration_minutes": 5
    }}
  ]
}}
```

## 注意事项
- 第一个步骤不应该有依赖
- 如果某个工具不在可用工具列表中,请选择最接近的工具或标记为"manual"
- 置信度应该基于任务的复杂度和信息的完整度
- 总执行时间应该合理(通常不超过2小时)
"""


class ExplicitPlanner(BasePlanner):
    """
    显式规划器

    实现书中描述的规划模式:
    1. 首先生成详细的执行计划
    2. 向用户展示计划并等待确认
    3. 用户批准后按计划执行
    4. 执行过程中支持动态调整
    """

    def __init__(self, name: str = "显式规划器", use_llm: bool = True):
        super().__init__(name, PlannerType.TASK_PLANNER)
        self.plans: dict[str, ExecutionPlan] = {}
        self.available_tools = self._register_available_tools()

        # 初始化LLM客户端
        self.use_llm = use_llm
        if use_llm:
            self.llm_client = get_glm47_client()
            logger.info(f"🤖 LLM客户端已启用: {self.llm_client.get_model_info()}")
        else:
            self.llm_client = None
            logger.info("📝 使用模拟模式(LLM未启用)")

        # 保存最后一次请求(供LLM使用)
        self.last_request = None

    def _register_available_tools(self) -> dict[str, Any]:
        """注册可用的工具"""
        return {
            "patent_search": {
                "name": "专利检索",
                "description": "根据关键词检索专利数据",
                "parameters": ["query", "limit", "database"],
            },
            "patent_analysis": {
                "name": "专利分析",
                "description": "分析专利的技术特征和创新点",
                "parameters": ["patent_id", "analysis_type"],
            },
            "vector_search": {
                "name": "向量搜索",
                "description": "基于语义相似度的向量检索",
                "parameters": ["query", "top_k", "filter"],
            },
            "knowledge_graph": {
                "name": "知识图谱",
                "description": "查询专利知识图谱中的实体关系",
                "parameters": ["entity", "relation_type", "depth"],
            },
            "web_search": {
                "name": "网络搜索",
                "description": "在互联网上搜索相关信息",
                "parameters": ["query", "num_results"],
            },
            "document_analysis": {
                "name": "文档分析",
                "description": "分析和提取文档中的关键信息",
                "parameters": ["document_id", "extract_fields"],
            },
            "data_synthesis": {
                "name": "数据综合",
                "description": "综合多个来源的数据生成报告",
                "parameters": ["sources", "output_format"],
            },
            "manual": {
                "name": "人工操作",
                "description": "需要人工介入的操作",
                "parameters": ["instruction"],
            },
        }

    async def create_plan(self, request: PlanningRequest) -> PlanningResult:
        """
        第一步:创建执行计划

        使用LLM将复杂任务分解为清晰的步骤
        """
        logger.info(f"📋 开始创建计划: {request.title}")

        # 保存请求供LLM使用
        self.last_request = request

        try:
            # 1. 准备提示词
            prompt = self._prepare_planning_prompt(request)

            # 2. 调用LLM生成计划
            # 注意:这里需要集成实际的LLM调用
            # 暂时使用模拟数据
            plan_json = await self._generate_plan_with_llm(prompt)

            # 3. 构建ExecutionPlan对象
            execution_plan = self._build_execution_plan(request.id, plan_json)

            # 4. 保存计划
            self.plans[execution_plan.plan_id] = execution_plan

            # 5. 返回规划结果
            return PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=True,
                plan_id=execution_plan.plan_id,
                steps=[self._step_to_dict(s) for s in execution_plan.steps],
                timeline={
                    "total_duration_minutes": execution_plan.total_duration.total_seconds() / 60,
                    "created_at": execution_plan.created_at.isoformat(),
                },
                confidence_score=execution_plan.total_confidence,
                estimated_duration=execution_plan.total_duration,
                status=TaskStatus.PENDING,
                feedback="计划已创建,等待用户确认",
            )

        except Exception as e:
            return PlanningResult(
                request_id=request.id,
                planner_type=self.planner_type,
                success=False,
                feedback=f"创建计划失败: {e!s}",
            )

    def _prepare_planning_prompt(self, request: PlanningRequest) -> str:
        """准备规划提示词"""
        # 格式化可用工具
        tools_str = "\n".join(
            [f"- {name}: {info.get('description')}" for name, info in self.available_tools.items()]
        )

        # 格式化上下文
        context_str = json.dumps(request.context, ensure_ascii=False, indent=2)

        # 填充提示词模板
        return PLAN_GENERATION_PROMPT.format(
            task_description=request.description, context=context_str, available_tools=tools_str
        )

    async def _generate_plan_with_llm(self, prompt: str) -> dict[str, Any]:
        """
        使用LLM生成计划

        集成GLM-4.7进行智能规划
        """
        if self.use_llm and self.llm_client:
            try:
                # 准备工具列表
                tools_list = [
                    {"name": name, "description": info.get("description")}
                    for name, info in self.available_tools.items()
                ]

                # 使用LLM客户端生成计划
                plan_json = await self.llm_client.generate_plan(
                    task_description=self.last_request.description,
                    context=self.last_request.context,
                    available_tools=tools_list,
                    requirements=self.last_request.requirements,
                    constraints=self.last_request.constraints,
                )

                logger.info("✅ GLM-4.7计划生成成功")
                return plan_json

            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)
                # 继续使用模拟模式
                pass

        # 模拟LLM返回的计划(降级方案)

        mock_plan = {
            "plan_name": "专利检索与分析计划",
            "plan_description": "根据用户需求进行专利检索,并对检索结果进行深度分析",
            "steps": [
                {
                    "step_number": 1,
                    "name": "理解用户需求",
                    "description": "分析用户的查询意图,提取关键信息",
                    "tool": "manual",
                    "tool_parameters": {"instruction": "理解用户查询的真实意图"},
                    "dependencies": [],
                    "confidence": 0.95,
                    "estimated_duration_minutes": 2,
                },
                {
                    "step_number": 2,
                    "name": "执行专利检索",
                    "description": "根据提取的关键词进行专利数据库检索",
                    "tool": "patent_search",
                    "tool_parameters": {
                        "query": "根据用户需求生成检索式",
                        "limit": 20,
                        "database": "all",
                    },
                    "dependencies": [1],
                    "confidence": 0.85,
                    "estimated_duration_minutes": 3,
                },
                {
                    "step_number": 3,
                    "name": "向量语义检索",
                    "description": "使用向量搜索找到语义相似的专利",
                    "tool": "vector_search",
                    "tool_parameters": {"query": "用户的查询", "top_k": 10, "filter": {}},
                    "dependencies": [1],
                    "confidence": 0.80,
                    "estimated_duration_minutes": 2,
                },
                {
                    "step_number": 4,
                    "name": "知识图谱关联分析",
                    "description": "查询知识图谱中的相关实体和关系",
                    "tool": "knowledge_graph",
                    "tool_parameters": {
                        "entity": "从查询中提取的实体",
                        "relation_type": "all",
                        "depth": 2,
                    },
                    "dependencies": [1],
                    "confidence": 0.75,
                    "estimated_duration_minutes": 2,
                },
                {
                    "step_number": 5,
                    "name": "专利深度分析",
                    "description": "对检索到的专利进行技术分析和创新点识别",
                    "tool": "patent_analysis",
                    "tool_parameters": {
                        "patent_id": "从前述步骤获得",
                        "analysis_type": "comprehensive",
                    },
                    "dependencies": [2, 3, 4],
                    "confidence": 0.90,
                    "estimated_duration_minutes": 10,
                },
                {
                    "step_number": 6,
                    "name": "综合生成报告",
                    "description": "整合所有分析结果,生成最终报告",
                    "tool": "data_synthesis",
                    "tool_parameters": {
                        "sources": ["检索结果", "分析结果", "图谱数据"],
                        "output_format": "structured_report",
                    },
                    "dependencies": [5],
                    "confidence": 0.92,
                    "estimated_duration_minutes": 5,
                },
            ],
        }

        logger.info("✅ 使用模拟LLM生成了计划(实际实现中需要集成真实的LLM)")
        return mock_plan

    def _build_execution_plan(self, request_id: str, plan_json: dict[str, Any]) -> ExecutionPlan:
        """构建ExecutionPlan对象"""
        steps = []
        total_duration = timedelta()
        total_confidence = 0.0

        for step_data in plan_json.get("steps", []):
            step = PlanStep(
                step_number=step_data.get("step_number"),
                name=step_data.get("name"),
                description=step_data.get("description"),
                tool=step_data.get("tool", "manual"),
                tool_parameters=step_data.get("tool_parameters", {}),
                dependencies=step_data.get("dependencies", []),
                confidence=step_data.get("confidence", 0.8),
                estimated_duration=timedelta(
                    minutes=step_data.get("estimated_duration_minutes", 5)
                ),
            )
            steps.append(step)
            total_duration += step.estimated_duration
            total_confidence += step.confidence

        # 计算平均置信度
        avg_confidence = total_confidence / len(steps) if steps else 0.0

        return ExecutionPlan(
            request_id=request_id,
            name=plan_json.get("plan_name", "未命名计划"),
            description=plan_json.get("plan_description", ""),
            steps=steps,
            total_confidence=avg_confidence,
            total_duration=total_duration,
            requires_approval=True,
        )

    def _step_to_dict(self, step: PlanStep) -> dict[str, Any]:
        """将PlanStep转换为字典"""
        return {
            "step_id": step.step_id,
            "step_number": step.step_number,
            "name": step.name,
            "description": step.description,
            "tool": step.tool,
            "tool_parameters": step.tool_parameters,
            "dependencies": step.dependencies,
            "confidence": step.confidence,
            "estimated_duration_minutes": step.estimated_duration.total_seconds() / 60,
            "status": step.status.value,
            "result": step.result,
            "error": step.error,
            "metadata": step.metadata,
        }

    async def get_plan(self, plan_id: str) -> ExecutionPlan | None:
        """获取计划详情"""
        return self.plans.get(plan_id)

    async def await_user_approval(self, plan_id: str, approved: bool, comments: str = "") -> bool:
        """
        第二步:等待并处理用户确认

        用户可以:
        - 批准计划:继续执行
        - 拒绝计划:取消执行
        - 修改计划:调整步骤后重新确认
        """
        plan = self.plans.get(plan_id)
        if not plan:
            logger.error(f"计划不存在: {plan_id}")
            return False

        plan.approved = approved
        plan.approval_comments = comments

        if approved:
            plan.status = TaskStatus.IN_PROGRESS
            logger.info(f"✅ 计划已获用户批准: {plan_id}")
            return True
        else:
            plan.status = TaskStatus.CANCELLED
            logger.info(f"❌ 计划被用户拒绝: {plan_id}")
            return False

    async def execute_plan(self, plan_id: str) -> dict[str, Any]:
        """
        第三步:执行计划

        按步骤顺序执行,支持动态调整
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return {"success": False, "error": "计划不存在"}

        if not plan.approved:
            return {"success": False, "error": "计划尚未获得批准"}

        logger.info(f"🚀 开始执行计划: {plan.name}")

        execution_results = {
            "plan_id": plan_id,
            "success": True,
            "completed_steps": [],
            "failed_steps": [],
            "total_duration": 0,
            "final_output": None,
        }

        try:
            # 按顺序执行每个步骤
            for step in plan.steps:
                if step.status == PlanStepStatus.SKIPPED:
                    continue

                # 检查依赖是否完成
                if not await self._check_dependencies(step, plan):
                    logger.warning(f"步骤 {step.name} 的依赖未满足,跳过")
                    step.status = PlanStepStatus.SKIPPED
                    continue

                # 执行步骤
                logger.info(f"⚙️ 执行步骤 {step.step_number}: {step.name}")
                step.status = PlanStepStatus.IN_PROGRESS

                try:
                    result = await self._execute_step(step, plan)
                    step.result = result
                    step.status = PlanStepStatus.COMPLETED
                    execution_results.get("completed_steps").append(
                        {"step_number": step.step_number, "name": step.name, "result": result}
                    )

                except Exception as e:
                    step.status = PlanStepStatus.FAILED
                    step.error = str(e)
                    execution_results.get("failed_steps").append(
                        {"step_number": step.step_number, "name": step.name, "error": str(e)}
                    )

                    # 尝试动态调整
                    adjustment = await self._adjust_plan(plan_id, step, str(e))
                    if not adjustment:
                        # 无法调整,终止执行
                        execution_results["success"] = False
                        break

            # 更新最终状态
            plan.status = (
                TaskStatus.COMPLETED if execution_results.get("success") else TaskStatus.FAILED
            )
            execution_results["final_output"] = await self._generate_final_output(plan)

            return execution_results

        except Exception as e:
            return {"success": False, "error": str(e), "plan_id": plan_id}

    async def _check_dependencies(self, step: PlanStep, plan: ExecutionPlan) -> bool:
        """检查步骤的依赖是否满足"""
        if not step.dependencies:
            return True

        for dep_step_num in step.dependencies:
            dep_step = next((s for s in plan.steps if s.step_number == dep_step_num), None)
            if not dep_step or dep_step.status != PlanStepStatus.COMPLETED:
                return False

        return True

    async def _execute_step(self, step: PlanStep, plan: ExecutionPlan) -> dict[str, Any]:
        """
        执行单个步骤

        TODO: 集成实际的工具调用
        这里使用模拟执行
        """
        # 模拟执行时间
        await asyncio.sleep(0.5)

        # 根据工具类型返回模拟结果
        if step.tool == "patent_search":
            return {
                "success": True,
                "results_count": 15,
                "patents": ["CN123456", "US789012", "EP345678"],
            }
        elif step.tool == "vector_search":
            return {
                "success": True,
                "results_count": 8,
                "similar_documents": ["doc1", "doc2", "doc3"],
            }
        elif step.tool == "knowledge_graph":
            return {"success": True, "entities_found": 5, "relations": 12}
        elif step.tool == "patent_analysis":
            return {
                "success": True,
                "analysis": {"innovations": ["创新点1", "创新点2"], "claims": 3, "citations": 5},
            }
        else:
            return {"success": True, "message": f"步骤 {step.name} 执行完成"}

    async def _adjust_plan(self, plan_id: str, failed_step: PlanStep, error: str) -> bool:
        """
        动态调整计划

        当某步失败时:
        1. 分析失败原因
        2. 尝试生成替代方案
        3. 询问用户是否继续
        """
        logger.info(f"🔄 尝试调整计划,失败的步骤: {failed_step.name}")

        plan = self.plans.get(plan_id)
        if not plan:
            return False

        # 使用LLM生成调整建议
        if self.use_llm and self.llm_client:
            try:
                adjustment = await self.llm_client.suggest_adjustment(
                    failed_step={
                        "step_number": failed_step.step_number,
                        "name": failed_step.name,
                        "description": failed_step.description,
                        "tool": failed_step.tool,
                        "tool_parameters": failed_step.tool_parameters,
                    },
                    error_message=error,
                    plan_context={"plan_name": plan.name, "total_steps": len(plan.steps)},
                )

                logger.info(f"🤖 GLM-4.7调整建议: {adjustment.get('adjustment_type')}")

                # 根据建议调整计划
                if adjustment.get("alternative_steps"):
                    for alt_step_data in adjustment["alternative_steps"]:
                        alt_step = PlanStep(
                            step_number=alt_step_data.get("step_number"),
                            name=alt_step_data.get("name"),
                            description=alt_step_data.get("description", ""),
                            tool=alt_step_data.get("tool", "manual"),
                            confidence=alt_step_data.get("confidence", 0.6),
                            estimated_duration=timedelta(
                                minutes=alt_step_data.get("estimated_duration_minutes", 3)
                            ),
                        )
                        # 插入到步骤列表
                        failed_index = plan.steps.index(failed_step)
                        plan.steps.insert(failed_index + 1, alt_step)
                        logger.info(f"✅ 已添加GLM-4.7建议的替代步骤: {alt_step.name}")

                    return True

            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)

        # 降级到简单调整(如果没有LLM或LLM失败)
        # 生成替代步骤
        alternative_step = PlanStep(
            step_number=failed_step.step_number + 0.5,  # 插入到失败步骤之后
            name=f"替代方案: {failed_step.name}",
            description=f"由于原步骤失败({error}),尝试使用替代方法",
            tool="manual",
            confidence=0.6,
            estimated_duration=timedelta(minutes=3),
        )

        # 插入到步骤列表
        failed_index = plan.steps.index(failed_step)
        plan.steps.insert(failed_index + 1, alternative_step)

        logger.info(f"✅ 已添加替代步骤: {alternative_step.name}")
        return True

    async def identify_parallel_tasks(self, plan_id: str) -> list[list[int]]:
        """
        识别可以并行执行的任务

        Args:
            plan_id: 计划ID

        Returns:
            并行任务组列表
        """
        plan = self.plans.get(plan_id)
        if not plan:
            logger.warning(f"计划不存在: {plan_id}")
            return []

        logger.info(f"🔍 识别并行任务: {plan.name}")

        # 使用LLM识别并行任务
        if self.use_llm and self.llm_client:
            try:
                # 构建计划数据
                plan_data = {
                    "plan_name": plan.name,
                    "steps": [
                        {
                            "step_number": s.step_number,
                            "name": s.name,
                            "dependencies": s.dependencies,
                        }
                        for s in plan.steps
                    ],
                }

                parallel_groups = await self.llm_client.identify_parallel_tasks(plan_data)

                if parallel_groups:
                    plan.parallel_groups = parallel_groups
                    if len(parallel_groups) > 0:
                        plan.execution_mode = "mixed"
                        logger.info(f"✅ 识别到 {len(parallel_groups)} 组并行任务")
                        for i, group in enumerate(parallel_groups):
                            logger.info(f"   组{i+1}: 步骤 {group}")
                else:
                    plan.execution_mode = "sequential"
                    logger.info("ℹ️ 未发现可并行的任务")

                return parallel_groups

            except Exception as e:
                logger.error(f"捕获异常: {e}", exc_info=True)

        # 降级到简单的并行性分析
        parallel_groups = []
        processed_steps = set()

        for step in plan.steps:
            if step.step_number in processed_steps:
                continue

            # 找出与当前步骤没有依赖关系的其他步骤
            current_deps = set(step.dependencies)
            parallel_group = [step.step_number]

            for other_step in plan.steps:
                if (
                    other_step.step_number != step.step_number
                    and other_step.step_number not in processed_steps
                    and other_step.step_number not in current_deps
                    and step.step_number not in set(other_step.dependencies)
                ):

                    parallel_group.append(other_step.step_number)
                    processed_steps.add(other_step.step_number)

            if len(parallel_group) > 1:
                parallel_groups.append(parallel_group)

            processed_steps.add(step.step_number)

        if parallel_groups:
            plan.parallel_groups = parallel_groups
            plan.execution_mode = "mixed" if len(parallel_groups) > 0 else "sequential"
            logger.info(f"✅ 识别到 {len(parallel_groups)} 组并行任务(降级模式)")
        else:
            plan.execution_mode = "sequential"
            logger.info("ℹ️ 未发现可并行的任务")

        return parallel_groups

    async def _generate_final_output(self, plan: ExecutionPlan) -> dict[str, Any]:
        """生成最终输出"""
        successful_steps = [s for s in plan.steps if s.status == PlanStepStatus.COMPLETED]

        return {
            "plan_name": plan.name,
            "total_steps": len(plan.steps),
            "completed_steps": len(successful_steps),
            "success_rate": len(successful_steps) / len(plan.steps) if plan.steps else 0,
            "execution_time": plan.total_duration.total_seconds() / 60,
            "summary": f"计划 {plan.name} 执行完成,{len(successful_steps)}/{len(plan.steps)} 步骤成功",
        }

    async def get_plan_status(self, plan_id: str) -> dict[str, Any]:
        """获取计划执行状态"""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"error": "计划不存在"}

        return {
            "plan_id": plan_id,
            "plan_name": plan.name,
            "status": plan.status.value,
            "approved": plan.approved,
            "steps": [
                {
                    "step_number": s.step_number,
                    "name": s.name,
                    "status": s.status.value,
                    "confidence": s.confidence,
                }
                for s in plan.steps
            ],
            "progress": (
                len([s for s in plan.steps if s.status == PlanStepStatus.COMPLETED])
                / len(plan.steps)
                if plan.steps
                else 0
            ),
        }

    async def update_plan(self, plan_id: str, updates: dict[str, Any]) -> bool:
        """更新计划"""
        plan = self.plans.get(plan_id)
        if not plan:
            return False

        # 更新计划属性
        if "name" in updates:
            plan.name = updates["name"]
        if "description" in updates:
            plan.description = updates["description"]
        if "metadata" in updates:
            plan.metadata.update(updates["metadata"])

        logger.info(f"✅ 计划已更新: {plan_id}")
        return True


# 全局实例
explicit_planner = None


def get_explicit_planner() -> ExplicitPlanner:
    """获取显式规划器单例"""
    global explicit_planner
    if explicit_planner is None:
        explicit_planner = ExplicitPlanner()
    return explicit_planner
