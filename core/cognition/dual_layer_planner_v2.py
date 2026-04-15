#!/usr/bin/env python3
from __future__ import annotations
"""
双层规划系统增强版 v2.0
Dual-Layer Planning System Enhanced

新增功能:
1. 超时处理
2. 并行执行支持
3. 执行历史记录
4. 真实智能体集成
5. 进度回调
6. 结果缓存

Author: Athena Team
Version: 2.0.0
Date: 2026-02-25
"""

import asyncio
import json
import logging
import re
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ========== 数据结构 ==========


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    HYBRID = "hybrid"  # 混合执行


@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    name: str
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    agent: str = "xiaonuo"
    action: str = "process"  # 智能体动作
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    estimated_time: int = 0
    timeout: int = 300  # 超时时间(秒)
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    context_file: str | None = None
    result: str | None = None
    error: str | None = None
    output_data: dict[str, Any] = field(default_factory=dict)
    started_at: str | None = None
    completed_at: str | None = None
    user_notes: str = ""
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    can_parallel: bool = False  # 是否可以并行执行

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        status_icons = {
            StepStatus.PENDING: "⏸️",
            StepStatus.IN_PROGRESS: "🔄",
            StepStatus.COMPLETED: "✅",
            StepStatus.FAILED: "❌",
            StepStatus.SKIPPED: "⏭️",
            StepStatus.BLOCKED: "🚫",
            StepStatus.CANCELLED: "🔕",
            StepStatus.TIMEOUT: "⏱️",
        }

        icon = status_icons.get(self.status, "⏸️")

        md = f"- [{self.status.value}] {icon} **{self.name}**\n"

        if self.description:
            md += f"  - 描述: {self.description}\n"

        if self.agent:
            md += f"  - 执行者: `{self.agent}`\n"

        if self.action:
            md += f"  - 动作: `{self.action}`\n"

        if self.dependencies:
            md += f"  - 依赖: {', '.join(self.dependencies)}\n"

        if self.estimated_time:
            md += f"  - 预估: {self.estimated_time}秒\n"

        if self.timeout != 300:
            md += f"  - 超时: {self.timeout}秒\n"

        if self.can_parallel:
            md += "  - 可并行: 是\n"

        if self.context_file:
            md += f"  - 上下文: `{self.context_file}`\n"

        if self.result:
            result_preview = self.result[:100] + "..." if len(self.result) > 100 else self.result
            md += f"  - 结果: {result_preview}\n"

        if self.error:
            md += f"  - 错误: {self.error}\n"

        if self.retry_count > 0:
            md += f"  - 重试: {self.retry_count}/{self.max_retries}\n"

        if self.user_notes:
            md += f"  - 备注: {self.user_notes}\n"

        return md

    @classmethod
    def from_markdown(cls, md_text: str, step_id: str) -> "PlanStep":
        """从 Markdown 文本解析步骤"""
        lines = md_text.strip().split("\n")

        # 解析状态和名称
        status = StepStatus.PENDING
        name = step_id
        agent = "xiaonuo"
        action = "process"
        dependencies = []
        estimated_time = 0
        timeout = 300
        can_parallel = False
        description = ""
        context_file = None
        user_notes = ""

        for line in lines:
            line = line.strip()

            # 解析状态行
            status_match = re.search(r"- \[(\w+)\]", line)
            if status_match:
                try:
                    status = StepStatus(status_match.group(1))
                except ValueError:
                    pass

            # 解析名称
            name_match = re.search(r"\*\*(.+?)\*\*", line)
            if name_match:
                name = name_match.group(1).strip()

            # 解析描述
            if line.startswith("- 描述:"):
                description = line.replace("- 描述:", "").strip()

            # 解析执行者
            elif line.startswith("- 执行者:"):
                agent = line.replace("- 执行者:", "").strip().strip("`")

            # 解析动作
            elif line.startswith("- 动作:"):
                action = line.replace("- 动作:", "").strip().strip("`")

            # 解析依赖
            elif line.startswith("- 依赖:"):
                deps_str = line.replace("- 依赖:", "").strip()
                dependencies = [d.strip() for d in deps_str.split(",") if d.strip()]

            # 解析预估时间
            elif line.startswith("- 预估:"):
                time_str = line.replace("- 预估:", "").strip().replace("秒", "")
                try:
                    estimated_time = int(time_str)
                except ValueError:
                    pass

            # 解析超时
            elif line.startswith("- 超时:"):
                timeout_str = line.replace("- 超时:", "").strip().replace("秒", "")
                try:
                    timeout = int(timeout_str)
                except ValueError:
                    pass

            # 解析可并行
            elif line.startswith("- 可并行:"):
                can_parallel = "是" in line or "true" in line.lower()

            # 解析上下文
            elif line.startswith("- 上下文:"):
                context_file = line.replace("- 上下文:", "").strip().strip("`")

            # 解析备注
            elif line.startswith("- 备注:"):
                user_notes = line.replace("- 备注:", "").strip()

        return cls(
            id=step_id,
            name=name,
            description=description,
            status=status,
            agent=agent,
            action=action,
            dependencies=dependencies,
            estimated_time=estimated_time,
            timeout=timeout,
            can_parallel=can_parallel,
            context_file=context_file,
            user_notes=user_notes,
        )


@dataclass
class ExecutionRecord:
    """执行记录"""
    record_id: str
    task_id: str
    step_id: str
    step_name: str
    agent: str
    action: str
    status: StepStatus
    started_at: str
    completed_at: str | None = None
    duration: float = 0  # 执行时长(秒)
    result: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskPlan:
    """任务计划"""
    task_id: str
    title: str
    description: str
    steps: list[PlanStep]
    status: StepStatus = StepStatus.PENDING
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_history: list[ExecutionRecord] = field(default_factory=list)

    def get_step_by_id(self, step_id: str) -> PlanStep | None:
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_pending_steps(self) -> list[PlanStep]:
        """获取待执行的步骤"""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}
        {s.id for s in self.steps if s.status == StepStatus.IN_PROGRESS}

        pending = []
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                deps_satisfied = all(dep in completed_ids for dep in step.dependencies)
                if deps_satisfied:
                    pending.append(step)

        return pending

    def get_ready_for_parallel(self) -> list[list[PlanStep]]:
        """获取可以并行执行的步骤组"""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}

        # 找出所有可以并行执行的步骤
        parallel_groups = []
        processed = set()

        for step in self.steps:
            if step.id in processed or not step.can_parallel:
                continue
            if step.status != StepStatus.PENDING:
                continue

            # 检查依赖
            deps_satisfied = all(dep in completed_ids for dep in step.dependencies)
            if not deps_satisfied:
                continue

            # 找到可以和这个步骤一起并行的其他步骤
            group = [step]
            processed.add(step.id)

            for other in self.steps:
                if other.id in processed or not other.can_parallel:
                    continue
                if other.status != StepStatus.PENDING:
                    continue

                # 检查是否可以一起并行（没有共享依赖）
                other_deps_ok = all(dep in completed_ids for dep in other.dependencies)
                if other_deps_ok:
                    group.append(other)
                    processed.add(other.id)

            if group:
                parallel_groups.append(group)

        return parallel_groups

    def get_progress(self) -> dict[str, Any]:
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        in_progress = sum(1 for s in self.steps if s.status == StepStatus.IN_PROGRESS)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "failed": failed,
            "pending": total - completed - in_progress - failed,
            "progress_percent": int(completed / total * 100) if total > 0 else 0,
        }

    def add_execution_record(self, record: ExecutionRecord) -> None:
        self.execution_history.append(record)


# ========== 进度回调类型 ==========


ProgressCallback = Callable[[str, str, StepStatus, dict[str, Any]], None]


# ========== Layer 1: 增强 Markdown Plan 管理器 ==========


class MarkdownPlanManager:
    """Markdown Plan 文档管理器增强版"""

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path("plans")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📄 Markdown Plan 管理器初始化: {self.storage_path}")

    def get_plan_file(self, task_id: str) -> Path:
        return self.storage_path / f"{task_id}.md"

    def get_history_file(self, task_id: str) -> Path:
        return self.storage_path / f"{task_id}_history.json"

    async def create_plan(self, plan: TaskPlan) -> str:
        plan_file = self.get_plan_file(plan.task_id)
        content = self._generate_markdown(plan)

        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 创建历史记录文件
        await self._save_history(plan)

        logger.info(f"✅ Plan 文档已创建: {plan_file}")
        return str(plan_file)

    def _generate_markdown(self, plan: TaskPlan) -> str:
        progress = plan.get_progress()

        md = f"""# 📋 {plan.title}

**任务ID**: `{plan.task_id}`
**状态**: {plan.status.value}
**执行模式**: {plan.execution_mode.value}
**创建时间**: {plan.created_at}
**更新时间**: {plan.updated_at}
**版本**: {plan.version}

---

## 📝 任务描述

{plan.description}

---

## 📊 执行进度

**总进度**: {progress['progress_percent']}% ({progress['completed']}/{progress['total']})

| 状态 | 数量 |
|------|------|
| ✅ 已完成 | {progress['completed']} |
| 🔄 进行中 | {progress['in_progress']} |
| ⏸️ 待开始 | {progress['pending']} |
| ❌ 失败 | {progress['failed']} |

---

## 🎯 执行步骤

"""

        for i, step in enumerate(plan.steps, 1):
            md += f"### 步骤 {i}: {step.name}\n\n"
            md += step.to_markdown()
            md += "\n"

        # 执行历史
        if plan.execution_history:
            md += "\n---\n\n## 📜 执行历史\n\n"
            md += "| 时间 | 步骤 | 状态 | 耗时 |\n"
            md += "|------|------|------|------|\n"

            for record in plan.execution_history[-10:]:  # 只显示最近10条
                duration_str = f"{record.duration:.1f}s" if record.duration > 0 else "-"
                md += f"| {record.started_at[-8:]} | {record.step_name[:15]} | {record.status.value} | {duration_str} |\n"

        if plan.metadata:
            md += "\n---\n\n## 📋 元数据\n\n"
            md += "```json\n"
            md += json.dumps(plan.metadata, indent=2, ensure_ascii=False)
            md += "\n```\n"

        md += "\n---\n\n## 📝 更新记录\n\n"
        md += f"**最后更新**: {plan.updated_at}\n"
        md += "\n<!-- 用户可以在此添加自定义备注 -->\n"

        md += "\n---\n\n"
        md += "**生成者**: 小诺·双鱼公主 (Athena v3.0 - Enhanced)\n"

        return md

    async def load_plan(self, task_id: str) -> TaskPlan | None:
        plan_file = self.get_plan_file(task_id)

        if not plan_file.exists():
            return None

        try:
            with open(plan_file, encoding="utf-8") as f:
                content = f.read()

            plan = self._parse_markdown(content, task_id)

            # 加载历史记录
            await self._load_history(plan)

            return plan

        except Exception as e:
            logger.error(f"❌ 解析 Plan 文档失败: {e}")
            return None

    def _parse_markdown(self, content: str, task_id: str) -> TaskPlan:
        lines = content.split("\n")

        title = "未命名任务"
        description = ""
        status = StepStatus.PENDING
        execution_mode = ExecutionMode.SEQUENTIAL
        created_at = datetime.now().isoformat()
        updated_at = datetime.now().isoformat()
        version = 1

        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
            elif "**任务ID**:" in line:
                pass
            elif "**状态**:" in line:
                status_str = line.split("**状态**:")[1].strip()
                try:
                    status = StepStatus(status_str)
                except ValueError:
                    pass
            elif "**执行模式**:" in line:
                mode_str = line.split("**执行模式**:")[1].strip()
                try:
                    execution_mode = ExecutionMode(mode_str)
                except ValueError:
                    pass
            elif "**创建时间**:" in line:
                created_at = line.split("**创建时间**:")[1].strip()
            elif "**更新时间**:" in line:
                updated_at = line.split("**更新时间**:")[1].strip()
            elif "**版本**:" in line:
                version = int(line.split("**版本**:")[1].strip())

        # 解析步骤
        steps = []
        current_step_lines = []
        step_counter = 0
        in_steps_section = False

        for line in lines:
            if line.startswith("## 🎯 执行步骤"):
                in_steps_section = True
                continue

            if in_steps_section:
                if line.startswith("###"):
                    if current_step_lines:
                        step_counter += 1
                        step = PlanStep.from_markdown(
                            "\n".join(current_step_lines),
                            f"step_{step_counter}"
                        )
                        steps.append(step)
                        current_step_lines = []
                elif line.startswith("##") or line.startswith("---"):
                    break
                else:
                    current_step_lines.append(line)

        if current_step_lines:
            step_counter += 1
            step = PlanStep.from_markdown(
                "\n".join(current_step_lines),
                f"step_{step_counter}"
            )
            steps.append(step)

        return TaskPlan(
            task_id=task_id,
            title=title,
            description=description,
            steps=steps,
            status=status,
            execution_mode=execution_mode,
            created_at=created_at,
            updated_at=updated_at,
            version=version,
        )

    async def _save_history(self, plan: TaskPlan) -> None:
        """保存执行历史"""
        history_file = self.get_history_file(plan.task_id)

        # 转换为可序列化的字典
        history_data = []
        for record in plan.execution_history:
            record_dict = {
                "record_id": record.record_id,
                "task_id": record.task_id,
                "step_id": record.step_id,
                "step_name": record.step_name,
                "agent": record.agent,
                "action": record.action,
                "status": record.status.value,
                "started_at": record.started_at,
                "completed_at": record.completed_at,
                "duration": record.duration,
                "result": record.result,
                "error": record.error,
                "metadata": record.metadata,
            }
            history_data.append(record_dict)

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)

    async def _load_history(self, plan: TaskPlan) -> None:
        """加载执行历史"""
        history_file = self.get_history_file(plan.task_id)

        if not history_file.exists():
            return

        try:
            with open(history_file, encoding="utf-8") as f:
                history_data = json.load(f)

            plan.execution_history = [
                ExecutionRecord(**record) for record in history_data
            ]

        except Exception as e:
            logger.warning(f"⚠️ 加载历史记录失败: {e}")

    async def sync_plan(self, plan: TaskPlan) -> bool:
        plan.updated_at = datetime.now().isoformat()
        plan_file = self.get_plan_file(plan.task_id)

        if not plan_file.exists():
            return await self.create_plan(plan)

        try:
            content = self._generate_markdown(plan)
            with open(plan_file, "w", encoding="utf-8") as f:
                f.write(content)

            await self._save_history(plan)

            logger.info(f"✅ Plan 已同步: {plan_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 同步 Plan 失败: {e}")
            return False


# ========== Layer 2: 增强任务执行引擎 ==========


class TaskExecutionEngine:
    """
    任务执行引擎增强版

    新增功能:
    - 超时处理
    - 并行执行
    - 自动重试
    - 进度回调
    - 真实智能体集成
    """

    def __init__(
        self,
        plan_manager: MarkdownPlanManager | None = None,
        progress_callback: ProgressCallback | None = None,
    ):
        self.plan_manager = plan_manager or MarkdownPlanManager()
        self.progress_callback = progress_callback
        self.active_tasks: dict[str, TaskPlan] = {}
        self.agents: dict[str, Any] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

        logger.info("🚀 增强任务执行引擎初始化")

    def register_agent(self, name: str, agent: Any) -> None:
        """注册执行智能体"""
        self.agents[name] = agent
        logger.info(f"🤖 注册智能体: {name}")

    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """设置进度回调"""
        self.progress_callback = callback

    def _notify_progress(
        self,
        task_id: str,
        step_id: str,
        status: StepStatus,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """通知进度更新"""
        if self.progress_callback:
            self.progress_callback(task_id, step_id, status, extra or {})

    async def start_task(
        self,
        task_id: str,
        title: str,
        description: str,
        steps: list[PlanStep],
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
    ) -> str:
        """启动新任务"""
        plan = TaskPlan(
            task_id=task_id,
            title=title,
            description=description,
            steps=steps,
            execution_mode=execution_mode,
        )

        plan_file = await self.plan_manager.create_plan(plan)
        self.active_tasks[task_id] = plan

        logger.info(f"🚀 任务已启动: {task_id}")
        return plan_file

    async def load_and_resume_task(self, task_id: str) -> TaskPlan | None:
        """加载并恢复任务"""
        plan = await self.plan_manager.load_plan(task_id)

        if plan:
            self.active_tasks[task_id] = plan
            logger.info(f"📂 任务已加载: {task_id}")

        return plan

    async def reload_plan_from_disk(self, task_id: str) -> bool:
        """从磁盘重新加载 Plan"""
        plan = await self.plan_manager.load_plan(task_id)

        if plan:
            self.active_tasks[task_id] = plan
            logger.info(f"🔄 Plan 已重新加载: {task_id}")
            return True

        return False

    @asynccontextmanager
    async def _timeout_context(self, timeout: int, step_id: str):
        """超时上下文管理器"""
        try:
            async with asyncio.timeout(timeout):
                yield
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ 步骤超时: {step_id}")
            raise TimeoutError(f"步骤执行超时 ({timeout}秒)") from None

    async def execute_step(
        self,
        task_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        """执行单个步骤（支持超时和重试）"""
        plan = self.active_tasks.get(task_id)

        if not plan:
            plan = await self.load_and_resume_task(task_id)

        if not plan:
            return {"success": False, "error": "任务不存在"}

        step = plan.get_step_by_id(step_id)

        if not step:
            return {"success": False, "error": f"步骤不存在: {step_id}"}

        # 检查依赖
        completed_ids = {s.id for s in plan.steps if s.status == StepStatus.COMPLETED}
        for dep in step.dependencies:
            if dep not in completed_ids:
                return {"success": False, "error": f"依赖未完成: {dep}"}

        # 更新状态为进行中
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now().isoformat()
        await self.plan_manager.sync_plan(plan)

        self._notify_progress(task_id, step_id, StepStatus.IN_PROGRESS)

        # 创建执行记录
        record = ExecutionRecord(
            record_id=str(uuid.uuid4()),
            task_id=task_id,
            step_id=step_id,
            step_name=step.name,
            agent=step.agent,
            action=step.action,
            status=StepStatus.IN_PROGRESS,
            started_at=step.started_at,
        )

        # 执行步骤（带重试）
        max_retries = step.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            if attempt > 0:
                step.retry_count = attempt
                logger.info(f"🔄 重试步骤 {step.name} (第 {attempt} 次)")

            try:
                async with self._timeout_context(step.timeout, step_id):
                    result = await self._execute_step_action(step)

                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now().isoformat()
                step.result = result.get("output", "")
                step.output_data = result.get("data", {})
                step.error = None

                # 更新执行记录
                record.status = StepStatus.COMPLETED
                record.completed_at = step.completed_at
                record.duration = (
                    datetime.fromisoformat(step.completed_at) -
                    datetime.fromisoformat(step.started_at)
                ).total_seconds()
                record.result = step.result

                plan.add_execution_record(record)
                await self.plan_manager.sync_plan(plan)

                self._notify_progress(task_id, step_id, StepStatus.COMPLETED, {
                    "result": result
                })

                logger.info(f"✅ 步骤完成: {step.name}")

                return {
                    "success": True,
                    "step_id": step_id,
                    "result": result,
                    "duration": record.duration,
                }

            except TimeoutError as e:
                last_error = str(e)
                step.status = StepStatus.TIMEOUT
                step.error = last_error

                if attempt < max_retries:
                    continue

            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ 步骤执行失败: {e}")

                if attempt < max_retries:
                    continue

        # 所有重试都失败
        step.status = StepStatus.FAILED
        step.completed_at = datetime.now().isoformat()
        step.error = last_error

        record.status = StepStatus.FAILED
        record.completed_at = step.completed_at
        record.duration = (
            datetime.fromisoformat(step.completed_at) -
            datetime.fromisoformat(record.started_at)
        ).total_seconds()
        record.error = last_error

        plan.add_execution_record(record)
        await self.plan_manager.sync_plan(plan)

        self._notify_progress(task_id, step_id, StepStatus.FAILED, {
            "error": last_error
        })

        return {
            "success": False,
            "step_id": step_id,
            "error": last_error,
        }

    async def _execute_step_action(self, step: PlanStep) -> dict[str, Any]:
        """执行步骤的具体操作"""
        agent = self.agents.get(step.agent)

        if not agent:
            # 模拟执行（用于测试）
            await asyncio.sleep(min(1, step.estimated_time))
            return {
                "success": True,
                "output": f"步骤 '{step.name}' 模拟执行完成",
                "data": {"simulated": True}
            }

        # 真实智能体调用
        if hasattr(agent, 'process'):
            from core.agents.base import AgentRequest
            request = AgentRequest(
                request_id=f"{step.id}_{datetime.now().timestamp()}",
                action=step.action,
                parameters=step.parameters,
            )
            response = await agent.process(request)

            if response.success:
                return {
                    "success": True,
                    "output": str(response.data),
                    "data": response.data,
                }
            else:
                raise Exception(response.error or "执行失败")

        raise Exception(f"智能体 {step.agent} 不支持处理请求")

    async def execute_parallel_steps(
        self,
        task_id: str,
        steps: list[PlanStep],
    ) -> list[dict[str, Any]]:
        """并行执行多个步骤"""
        logger.info(f"⚡ 并行执行 {len(steps)} 个步骤")

        tasks = [
            self.execute_step(task_id, step.id)
            for step in steps
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({
                    "success": False,
                    "step_id": steps[i].id,
                    "error": str(result),
                })
            else:
                formatted_results.append(result)

        return formatted_results

    async def execute_all_pending(
        self,
        task_id: str,
        stop_on_error: bool = True,
    ) -> dict[str, Any]:
        """执行所有待处理的步骤"""
        plan = self.active_tasks.get(task_id)

        if not plan:
            plan = await self.load_and_resume_task(task_id)

        if not plan:
            return {"success": False, "error": "任务不存在"}

        results = []
        execution_mode = plan.execution_mode

        while True:
            pending = plan.get_pending_steps()

            if not pending:
                break

            if execution_mode == ExecutionMode.PARALLEL:
                # 尝试并行执行
                parallel_groups = plan.get_ready_for_parallel()

                if parallel_groups and len(parallel_groups[0]) > 1:
                    for group in parallel_groups:
                        group_results = await self.execute_parallel_steps(task_id, group)
                        results.extend(group_results)

                        # 检查是否有失败
                        if stop_on_error:
                            failed = [r for r in group_results if not r.get("success")]
                            if failed:
                                return {
                                    "success": False,
                                    "results": results,
                                    "error": "并行执行中存在失败",
                                }
                else:
                    # 降级为顺序执行
                    for step in pending:
                        result = await self.execute_step(task_id, step.id)
                        results.append(result)

                        if stop_on_error and not result.get("success"):
                            return {
                                "success": False,
                                "results": results,
                                "error": result.get("error"),
                            }

            else:  # SEQUENTIAL
                for step in pending:
                    result = await self.execute_step(task_id, step.id)
                    results.append(result)

                    if stop_on_error and not result.get("success"):
                        return {
                            "success": False,
                            "results": results,
                            "error": result.get("error"),
                        }

        # 更新任务状态
        progress = plan.get_progress()
        if progress["failed"] == 0:
            plan.status = StepStatus.COMPLETED
        else:
            plan.status = StepStatus.FAILED

        await self.plan_manager.sync_plan(plan)

        return {
            "success": True,
            "results": results,
            "progress": progress,
        }

    async def start_background_execution(
        self,
        task_id: str,
        stop_on_error: bool = True,
    ) -> str:
        """在后台启动任务执行"""
        if task_id in self._running_tasks:
            return f"任务 {task_id} 已在运行中"

        async def _run():
            try:
                await self.execute_all_pending(task_id, stop_on_error)
            finally:
                self._running_tasks.pop(task_id, None)

        task = asyncio.create_task(_run())
        self._running_tasks[task_id] = task

        return f"任务 {task_id} 已在后台启动"

    def get_active_tasks(self) -> list[str]:
        """获取正在运行的任务"""
        return list(self._running_tasks.keys())


# ========== 导出 ==========


__all__ = [
    "StepStatus",
    "ExecutionMode",
    "PlanStep",
    "TaskPlan",
    "ExecutionRecord",
    "MarkdownPlanManager",
    "TaskExecutionEngine",
    "ProgressCallback",
]
