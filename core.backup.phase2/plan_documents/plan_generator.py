#!/usr/bin/env python3
from __future__ import annotations
"""
Markdown Plan文档生成器
Plan Document Generator - 生成和管理plan.md文档

作者: Athena平台团队
创建时间: 2026-01-20
版本: v1.0.0 "Phase 1"
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PlanStatus(Enum):
    """计划状态"""

    DRAFT = "draft"  # 草稿
    PENDING = "pending"  # 待确认
    APPROVED = "approved"  # 已确认
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 已失败
    PAUSED = "paused"  # 已暂停


@dataclass
class PlanStep:
    """计划步骤"""

    step_id: str
    name: str
    description: str
    status: str = "pending"
    context_file: str | None = None
    dependencies: list[str] | None = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        status_icon = {
            "pending": "⏸️",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
        }.get(self.status, "⏸️")

        md = f"- [{self.status}] {status_icon} {self.name}\n"

        if self.description:
            md += f"  {self.description}\n"

        if self.context_file:
            md += f"  📦 上下文: `{self.context_file}`\n"

        if self.dependencies:
            md += f"  📥 依赖: {', '.join(self.dependencies)}\n"

        return md


@dataclass
class PlanMetadata:
    """计划元数据"""

    task_id: str
    task_type: str  # professional / general
    domain: str
    thinking_mode: str  # SOPPlan, Plan, ReAct, TreeOfThought, Executor
    status: PlanStatus
    created_at: str
    updated_at: str
    version: int = 1


class PlanDocument:
    """Plan文档管理器"""

    def __init__(self, storage_path: Path | None = None):
        """
        初始化Plan文档管理器

        Args:
            storage_path: plan.md文件存储路径
        """
        self.storage_path = storage_path or Path("plans")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📄 Plan文档管理器初始化: {self.storage_path}")

    async def create_plan(
        self,
        task_id: str,
        task_description: str,
        classification: Any,
        steps: list[PlanStep],
        thinking_mode: str = "Plan",
        metadata: dict | None = None,
    ) -> str:
        """
        创建新的Plan文档

        Args:
            task_id: 任务ID
            task_description: 任务描述
            classification: 任务分类结果
            steps: 执行步骤列表
            thinking_mode: 思考模式
            metadata: 额外元数据

        Returns:
            str: plan.md文件路径
        """
        logger.info(f"📝 创建Plan文档: {task_id}")

        # 生成文件路径
        plan_file = self.storage_path / f"{task_id}.md"

        # 准备元数据
        plan_metadata = PlanMetadata(
            task_id=task_id,
            task_type=classification.category.value,
            domain=classification.domain.value if classification.domain else None,
            thinking_mode=thinking_mode,
            status=PlanStatus.PENDING,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        # 生成Markdown内容
        content = self._generate_markdown(
            task_description, classification, steps, plan_metadata, metadata or {}
        )

        # 写入文件
        with open(plan_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"✅ Plan文档已创建: {plan_file}")

        return str(plan_file)

    def _generate_markdown(
        self,
        task_description: str,
        classification: Any,
        steps: list[PlanStep],
        metadata: PlanMetadata,
        extra_data: dict,
    ) -> str:
        """生成Markdown内容"""

        # 专业任务模板
        if classification.category.value == "professional":
            return self._professional_template(
                task_description, classification, steps, metadata, extra_data
            )
        else:
            return self._general_template(
                task_description, classification, steps, metadata, extra_data
            )

    def _professional_template(
        self,
        task_description: str,
        classification: Any,
        steps: list[PlanStep],
        metadata: PlanMetadata,
        extra_data: dict,
    ) -> str:
        """专业任务模板"""

        md = f"""# 📋 专业任务计划: {task_description[:50]}

**任务ID**: {metadata.task_id}
**任务类型**: 专业任务({metadata.domain})
**思考模式**: {metadata.thinking_mode}
**状态**: {metadata.status.value}
**创建时间**: {metadata.created_at}
**版本**: {metadata.version}

---

## ⚖️ 规则依据

**检索来源**:
- 📖 专业规则库(待查询)
- 📊 知识图谱推理(待查询)
- 🎯 向量检索(待查询)

**关键规则**:
(规则查询后填充)

---

## 🎯 执行计划

"""

        # 添加步骤
        for i, step in enumerate(steps, 1):
            md += f"### 阶段{i}: {step.name}\n"
            md += step.to_markdown()
            md += "\n"

        # 添加进度追踪
        md += "\n## 📊 进度追踪\n\n"
        md += "| 阶段 | 状态 | 完成度 |\n"
        md += "|------|------|--------|\n"

        completed = sum(1 for s in steps if s.status == "completed")
        total = len(steps)

        for i, step in enumerate(steps, 1):
            status_map = {
                "pending": "⏸️ 待开始",
                "in_progress": "🔄 进行中",
                "completed": "✅ 完成",
                "failed": "❌ 失败",
            }
            status_text = status_map.get(step.status, "⏸️ 待开始")
            md += f"| 阶段{i} | {status_text} | {step.status} |\n"

        md += "\n## 🔄 断点恢复\n\n"
        md += f"**当前状态**: {metadata.status.value}\n"
        md += f"**完成度**: {completed}/{total} ({completed*100//total if total > 0 else 0}%)\n\n"
        md += "**恢复命令**:\n"
        md += "```bash\n"
        md += "curl -X POST http://localhost:8100/task/resume \\\\\n"
        md += f'  -d \'{{"task_id": "{metadata.task_id}"}}\'\n'
        md += "```\n\n"

        md += "---\n\n"
        md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += "**生成者**: 小诺·双鱼座 (Athena v6.0)\n"

        return md

    def _general_template(
        self,
        task_description: str,
        classification: Any,
        steps: list[PlanStep],
        metadata: PlanMetadata,
        extra_data: dict,
    ) -> str:
        """通用任务模板"""

        md = f"""# 📋 任务计划: {task_description[:50]}

**任务ID**: {metadata.task_id}
**任务类型**: 通用任务
**思考模式**: {metadata.thinking_mode}
**状态**: {metadata.status.value}
**创建时间**: {metadata.created_at}

---

## 💡 诺诺的分析

**任务理解**:
{task_description}

**执行策略**:
- 使用{metadata.thinking_mode}模式思考
- 智能分解任务
- 动态调整计划

---

## 🚀 执行计划

"""

        # 添加步骤
        for i, step in enumerate(steps, 1):
            md += f"### 步骤{i}: {step.name}\n"
            md += step.to_markdown()
            md += "\n"

        md += "\n## 📊 执行进度\n\n"

        completed = sum(1 for s in steps if s.status == "completed")
        total = len(steps)

        md += f"- 总步骤: {total}\n"
        md += f"- 已完成: {completed}\n"
        md += f"- 进行中: {sum(1 for s in steps if s.status == 'in_progress')}\n"
        md += f"- 待完成: {sum(1 for s in steps if s.status == 'pending')}\n"

        md += "\n---\n\n"
        md += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md += "**生成者**: 小诺·双鱼座 (Athena v6.0)\n"

        return md

    async def update_plan(self, task_id: str, updates: dict[str, Any]) -> bool:
        """
        更新Plan文档

        Args:
            task_id: 任务ID
            updates: 更新内容

        Returns:
            bool: 是否成功
        """
        plan_file = self.storage_path / f"{task_id}.md"

        if not plan_file.exists():
            logger.warning(f"⚠️ Plan文件不存在: {plan_file}")
            return False

        try:
            # 读取现有内容
            with open(plan_file, encoding="utf-8") as f:
                f.read()

            # 简单更新:在文档末尾添加更新记录
            update_section = "\n\n## 📝 更新记录\n\n"
            update_section += f"**更新时间**: {datetime.now().isoformat()}\n"

            for key, value in updates.items():
                update_section += f"- **{key}**: {value}\n"

            # 追加到文档末尾
            with open(plan_file, "a", encoding="utf-8") as f:
                f.write(update_section)

            logger.info(f"✅ Plan文档已更新: {plan_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 更新Plan文档失败: {e}")
            return False

    async def update_step_status(
        self, task_id: str, step_id: str, new_status: str, context_file: str | None = None
    ) -> bool:
        """
        更新步骤状态

        Args:
            task_id: 任务ID
            step_id: 步骤ID
            new_status: 新状态
            context_file: 上下文文件路径

        Returns:
            bool: 是否成功
        """
        # TODO: 实现步骤状态的精细更新
        # 目前先简单实现:使用update_plan
        updates = {f"步骤{step_id}状态": new_status}

        if context_file:
            updates[f"步骤{step_id}上下文"] = context_file

        return await self.update_plan(task_id, updates)


# 便捷函数
async def create_plan_document(
    task_id: str, task_description: str, classification: Any, steps: list[PlanStep]
) -> str:
    """
    便捷的Plan文档创建函数

    Args:
        task_id: 任务ID
        task_description: 任务描述
        classification: 任务分类
        steps: 执行步骤

    Returns:
        str: plan.md文件路径
    """
    generator = PlanDocument()
    return await generator.create_plan(
        task_id=task_id,
        task_description=task_description,
        classification=classification,
        steps=steps,
    )


__all__ = ["PlanDocument", "PlanMetadata", "PlanStatus", "PlanStep", "create_plan_document"]
