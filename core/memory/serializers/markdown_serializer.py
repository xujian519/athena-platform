#!/usr/bin/env python3
"""
Markdown序列化器

将WorkflowPattern序列化为人类可读的Markdown格式。

Author: Athena平台团队
Created: 2026-01-20
Version: v1.0.0
"""

import logging
from pathlib import Path
from typing import Any

from core.memory.workflow_pattern import WorkflowPattern

logger = logging.getLogger(__name__)


class PatternMarkdownSerializer:
    """
    Pattern Markdown序列化器

    将WorkflowPattern对象序列化为结构化的Markdown文档,
    便于人类阅读、版本控制和协作编辑。
    """

    def serialize(self, pattern: WorkflowPattern) -> str:
        """
        序列化为Markdown格式

        Args:
            pattern: WorkflowPattern对象

        Returns:
            Markdown格式的字符串
        """
        lines = []

        # 标题和基本信息
        lines.append(f"# Workflow Pattern: {pattern.name}")
        lines.append("")

        # Pattern Info
        lines.append("## Pattern Info")
        lines.append("")
        lines.append(f"- **Pattern ID**: `{pattern.pattern_id}`")
        lines.append(f"- **Domain**: `{pattern.domain}`")
        lines.append(f"- **Task Type**: `{pattern.task_type}`")
        lines.append(f"- **Created**: {pattern.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **Success Rate**: {pattern.success_rate:.1%}")
        lines.append(f"- **Usage Count**: {pattern.usage_count}")
        lines.append("")

        # Description
        lines.append("## Description")
        lines.append("")
        lines.append(pattern.description)
        lines.append("")

        # Workflow Steps
        lines.append("## Workflow Steps")
        lines.append("")
        lines.append(f"This pattern consists of {len(pattern.steps)} steps:")
        lines.append("")

        for i, step in enumerate(pattern.steps, 1):
            lines.append(f"### Step {i}: {step.name}")
            lines.append("")
            lines.append(f"- **Step ID**: `{step.step_id}`")
            # 处理Enum和str两种情况
            step_type_value = (
                step.step_type if isinstance(step.step_type, str) else step.step_type.value
            )
            lines.append(f"- **Type**: `{step_type_value}`")
            lines.append(f"- **Description**: {step.description}")

            if step.action:
                lines.append(f"- **Action**: `{step.action}`")

            if step.input_schema:
                lines.append("- **Input Schema**:")
                lines.append("```json")
                lines.append(f"{self._format_dict(step.input_schema)}")
                lines.append("```")

            if step.output_schema:
                lines.append("- **Output Schema**:")
                lines.append("```json")
                lines.append(f"{self._format_dict(step.output_schema)}")
                lines.append("```")

            if step.dependencies:
                deps = ", ".join([f"`{dep}`" for dep in step.dependencies])
                lines.append(f"- **Dependencies**: {deps}")

            lines.append("")

        # Success Criteria
        if pattern.success_criteria:
            lines.append("## Success Criteria")
            lines.append("")
            for key, value in pattern.success_criteria.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        # Performance Metrics
        lines.append("## Performance Metrics")
        lines.append("")
        lines.append(f"- **Average Execution Time**: {pattern.avg_execution_time:.2f}s")
        if pattern.min_execution_time != float("inf"):
            lines.append(f"- **Min Execution Time**: {pattern.min_execution_time:.2f}s")
        lines.append(f"- **Max Execution Time**: {pattern.max_execution_time:.2f}s")
        lines.append(f"- **Total Executions**: {pattern.total_executions}")
        lines.append(f"- **Successful Executions**: {pattern.successful_executions}")
        lines.append("")

        # Variations
        if pattern.variations:
            lines.append("## Variations")
            lines.append("")
            for var_name, var_value in pattern.variations.items():
                lines.append(f"### {var_name}")
                lines.append("")
                lines.append(f"{var_value}")
                lines.append("")

        # Usage Statistics
        lines.append("## Usage Statistics")
        lines.append("")
        lines.append(f"- **First Used**: {pattern.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        if pattern.last_used_at:
            lines.append(f"- **Last Used**: {pattern.last_used_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- **Confidence Score**: {pattern.get_confidence():.3f}")
        lines.append("")

        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Updated At**: {pattern.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        return "\n".join(lines)

    async def save_to_file(self, pattern: WorkflowPattern, file_path: str):
        """
        保存到Markdown文件

        Args:
            pattern: WorkflowPattern对象
            file_path: 文件路径
        """
        markdown_content = self.serialize(pattern)

        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"💾 Pattern已保存到Markdown: {file_path}")

    def _format_dict(self, d: dict[str, Any], indent: int = 0) -> str:
        """格式化字典为JSON字符串"""
        import json

        return json.dumps(d, ensure_ascii=False, indent=2)

    @staticmethod
    def get_file_path(
        pattern: WorkflowPattern, base_dir: str = "data/workflow_memory/patterns"
    ) -> str:
        """
        获取模式的Markdown文件路径

        Args:
            pattern: WorkflowPattern对象
            base_dir: 基础目录

        Returns:
            Markdown文件路径
        """
        return f"{base_dir}/{pattern.pattern_id}.md"


__all__ = ["PatternMarkdownSerializer"]
