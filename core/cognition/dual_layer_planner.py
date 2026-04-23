#!/usr/bin/env python3
from __future__ import annotations
"""
双层规划系统 (Dual-Layer Planning System)
参照 Manus 设计理念，实现用户可编辑的 Markdown Plan + 系统执行层

架构:
┌─────────────────────────────────────────────────────────┐
│                    用户交互层 (Layer 1)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │   Markdown Plan 文档 (用户可编辑)                  │  │
│  │   - 任务目标、步骤、状态                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         ↕ 双向同步
┌─────────────────────────────────────────────────────────┐
│                    系统执行层 (Layer 2)                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │   任务执行引擎 (解析、执行、同步)                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ========== 数据结构 ==========


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"  # 待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过
    BLOCKED = "blocked"  # 阻塞
    CANCELLED = "cancelled"  # 取消


@dataclass
class PlanStep:
    """计划步骤"""
    id: str
    name: str
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    agent: str = "xiaonuo"  # 执行智能体
    dependencies: list[str] = field(default_factory=list)
    estimated_time: int = 0  # 预估时间(秒)
    context_file: Optional[str] = None  # 上下文文件
    result: Optional[str] = None  # 执行结果
    error: Optional[str] = None  # 错误信息
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    user_notes: str = ""  # 用户备注

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
        }

        icon = status_icons.get(self.status, "⏸️")

        md = f"- [{self.status.value}] {icon} **{self.name}**\n"

        if self.description:
            md += f"  - 描述: {self.description}\n"

        if self.agent:
            md += f"  - 执行者: `{self.agent}`\n"

        if self.dependencies:
            md += f"  - 依赖: {', '.join(self.dependencies)}\n"

        if self.estimated_time:
            md += f"  - 预估: {self.estimated_time}秒\n"

        if self.context_file:
            md += f"  - 上下文: `{self.context_file}`\n"

        if self.result:
            md += f"  - 结果: {self.result[:100]}...\n" if len(self.result) > 100 else f"  - 结果: {self.result}\n"

        if self.error:
            md += f"  - 错误: {self.error}\n"

        if self.user_notes:
            md += f"  - 备注: {self.user_notes}\n"

        return md

    @classmethod
    def from_markdown(cls, md_text: str, step_id: str) -> "PlanStep":
        """从 Markdown 文本解析步骤"""
        lines = md_text.strip().split("\n")

        # 解析状态行
        status_match = re.search(r"- \[(\w+)\]\s*([^\*]+?)\s*\*\*(.+?)\*\*", lines[0])
        if not status_match:
            # 尝试另一种格式
            status_match = re.search(r"- \[(\w+)\]\s*(\S+)\s*\*\*(.+?)\*\*", lines[0])

        status = StepStatus.PENDING
        name = step_id

        if status_match:
            status_str = status_match.group(1)
            try:
                status = StepStatus(status_str)
            except ValueError:
                status = StepStatus.PENDING
            name = status_match.group(3).strip()

        step = cls(id=step_id, name=name, status=status)

        # 解析详细信息
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("- 描述:"):
                step.description = line.replace("- 描述:", "").strip()
            elif line.startswith("- 执行者:"):
                step.agent = line.replace("- 执行者:", "").strip().strip("`")
            elif line.startswith("- 依赖:"):
                deps = line.replace("- 依赖:", "").strip().split(",")
                step.dependencies = [d.strip() for d in deps]
            elif line.startswith("- 预估:"):
                time_str = line.replace("- 预估:", "").strip().replace("秒", "")
                try:
                    step.estimated_time = int(time_str)
                except ValueError:
                    pass
            elif line.startswith("- 上下文:"):
                step.context_file = line.replace("- 上下文:", "").strip().strip("`")
            elif line.startswith("- 备注:"):
                step.user_notes = line.replace("- 备注:", "").strip()

        return step


@dataclass
class TaskPlan:
    """任务计划"""
    task_id: str
    title: str
    description: str
    steps: list[PlanStep]
    status: StepStatus = StepStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_step_by_id(self, step_id: str) -> PlanStep | None:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_pending_steps(self) -> list[PlanStep]:
        """获取待执行的步骤（考虑依赖关系）"""
        completed_ids = {s.id for s in self.steps if s.status == StepStatus.COMPLETED}

        pending = []
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # 检查依赖是否都已完成
                deps_satisfied = all(dep in completed_ids for dep in step.dependencies)
                if deps_satisfied:
                    pending.append(step)

        return pending

    def get_progress(self) -> dict[str, Any]:
        """获取进度信息"""
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


# ========== Layer 1: Markdown Plan 管理器 ==========


class MarkdownPlanManager:
    """
    Markdown Plan 文档管理器 (Layer 1)

    负责:
    1. 生成 Markdown Plan 文档
    2. 解析 Markdown Plan 文档
    3. 同步状态到文档
    4. 支持用户编辑
    """

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path("plans")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📄 Markdown Plan 管理器初始化: {self.storage_path}")

    def get_plan_file(self, task_id: str) -> Path:
        """获取计划文件路径"""
        return self.storage_path / f"{task_id}.md"

    async def create_plan(self, plan: TaskPlan) -> str:
        """创建 Markdown Plan 文档"""
        plan_file = self.get_plan_file(plan.task_id)

        content = self._generate_markdown(plan)

        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ Plan 文档已创建: {plan_file}")
        return str(plan_file)

    def _generate_markdown(self, plan: TaskPlan) -> str:
        """生成 Markdown 内容"""
        progress = plan.get_progress()

        md = f"""# 📋 {plan.title}

**任务ID**: `{plan.task_id}`
**状态**: {plan.status.value}
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

        # 添加步骤
        for i, step in enumerate(plan.steps, 1):
            md += f"### 步骤 {i}: {step.name}\n\n"
            md += step.to_markdown()
            md += "\n"

        # 添加元数据
        if plan.metadata:
            md += "\n---\n\n## 📋 元数据\n\n"
            md += "```json\n"
            md += json.dumps(plan.metadata, indent=2, ensure_ascii=False)
            md += "\n```\n"

        # 添加更新记录
        md += "\n---\n\n## 📝 更新记录\n\n"
        md += f"**最后更新**: {plan.updated_at}\n"
        md += "\n<!-- 用户可以在此添加自定义备注 -->\n"

        md += "\n---\n\n"
        md += "**生成者**: 小诺·双鱼公主 (Athena v3.0)\n"

        return md

    async def load_plan(self, task_id: str) -> TaskPlan | None:
        """从 Markdown 文档加载计划"""
        plan_file = self.get_plan_file(task_id)

        if not plan_file.exists():
            logger.warning(f"⚠️ Plan 文件不存在: {plan_file}")
            return None

        try:
            with open(plan_file, encoding="utf-8") as f:
                content = f.read()

            return self._parse_markdown(content, task_id)

        except Exception as e:
            logger.error(f"❌ 解析 Plan 文档失败: {e}")
            return None

    def _parse_markdown(self, content: str, task_id: str) -> TaskPlan:
        """解析 Markdown 内容为 TaskPlan"""
        lines = content.split("\n")

        # 解析标题
        title = "未命名任务"
        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break

        # 解析元数据
        description = ""
        status = StepStatus.PENDING
        created_at = datetime.now().isoformat()
        updated_at = datetime.now().isoformat()
        version = 1

        # 提取元数据值
        for line in lines:
            if "**任务ID**:" in line:
                pass  # task_id 已知
            elif "**状态**:" in line:
                status_str = line.split("**状态**:")[1].strip()
                try:
                    status = StepStatus(status_str)
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
                    # 保存上一个步骤
                    if current_step_lines:
                        step_counter += 1
                        step = PlanStep.from_markdown(
                            "\n".join(current_step_lines),
                            f"step_{step_counter}"
                        )
                        steps.append(step)
                        current_step_lines = []
                elif line.startswith("##") or line.startswith("---"):
                    # 离开步骤区域
                    break
                else:
                    current_step_lines.append(line)

        # 最后一个步骤
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
            created_at=created_at,
            updated_at=updated_at,
            version=version,
        )

    async def sync_plan(self, plan: TaskPlan) -> bool:
        """同步计划到文档（更新状态）"""
        plan.updated_at = datetime.now().isoformat()
        plan_file = self.get_plan_file(plan.task_id)

        if not plan_file.exists():
            logger.warning(f"⚠️ Plan 文件不存在，将创建新文件: {plan_file}")
            return await self.create_plan(plan)

        try:
            content = self._generate_markdown(plan)
            with open(plan_file, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"✅ Plan 已同步: {plan_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 同步 Plan 失败: {e}")
            return False


# ========== Layer 2: 任务执行引擎 ==========


class TaskExecutionEngine:
    """
    任务执行引擎 (Layer 2)

    负责:
    1. 解析 Plan 文档
    2. 按步骤执行任务
    3. 同步执行状态到 Plan 文档
    4. 处理用户对 Plan 的修改
    """

    def __init__(self, plan_manager: MarkdownPlanManager | None = None):
        self.plan_manager = plan_manager or MarkdownPlanManager()
        self.active_tasks: dict[str, TaskPlan] = {}
        self.execution_history: list[dict[str, Any]] = []

        # 智能体注册表
        self.agents = {}

    def register_agent(self, name: str, agent: Any) -> None:
        """注册执行智能体"""
        self.agents[name] = agent
        logger.info(f"🤖 注册智能体: {name}")

    async def start_task(
        self,
        task_id: str,
        title: str,
        description: str,
        steps: list[PlanStep],
    ) -> str:
        """启动新任务，创建 Plan 文档"""
        plan = TaskPlan(
            task_id=task_id,
            title=title,
            description=description,
            steps=steps,
        )

        # 创建 Plan 文档
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

    async def execute_step(
        self,
        task_id: str,
        step_id: str,
    ) -> dict[str, Any]:
        """执行单个步骤"""
        plan = self.active_tasks.get(task_id)

        if not plan:
            # 尝试从文件加载
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

        # 执行步骤
        try:
            result = await self._execute_step_action(step)

            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now().isoformat()
            step.result = result.get("output", "")
            step.error = None

            # 同步状态
            await self.plan_manager.sync_plan(plan)

            logger.info(f"✅ 步骤完成: {step.name}")

            return {
                "success": True,
                "step_id": step_id,
                "result": result,
            }

        except Exception as e:
            step.status = StepStatus.FAILED
            step.completed_at = datetime.now().isoformat()
            step.error = str(e)

            await self.plan_manager.sync_plan(plan)

            logger.error(f"❌ 步骤失败: {step.name}, 错误: {e}")

            return {
                "success": False,
                "step_id": step_id,
                "error": str(e),
            }

    async def _execute_step_action(self, step: PlanStep) -> dict[str, Any]:
        """执行步骤的具体操作"""
        agent = self.agents.get(step.agent)

        if not agent:
            raise Exception(f"智能体不存在: {step.agent}")

        # 根据步骤名称/描述执行相应操作
        # 这里可以根据实际需求扩展

        return {
            "success": True,
            "output": f"步骤 '{step.name}' 执行完成",
        }

    async def execute_all_pending(self, task_id: str) -> dict[str, Any]:
        """执行所有待处理的步骤"""
        plan = self.active_tasks.get(task_id)

        if not plan:
            plan = await self.load_and_resume_task(task_id)

        if not plan:
            return {"success": False, "error": "任务不存在"}

        results = []

        while True:
            pending = plan.get_pending_steps()

            if not pending:
                break

            for step in pending:
                result = await self.execute_step(task_id, step.id)
                results.append(result)

                if not result.get("success"):
                    # 失败后停止
                    return {
                        "success": False,
                        "results": results,
                        "error": "执行失败",
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

    async def reload_plan_from_disk(self, task_id: str) -> bool:
        """从磁盘重新加载 Plan（用户可能修改了文档）"""
        plan = await self.plan_manager.load_plan(task_id)

        if plan:
            self.active_tasks[task_id] = plan
            logger.info(f"🔄 Plan 已重新加载: {task_id}")
            return True

        return False


# ========== 导出 ==========


__all__ = [
    "StepStatus",
    "PlanStep",
    "TaskPlan",
    "MarkdownPlanManager",
    "TaskExecutionEngine",
]
