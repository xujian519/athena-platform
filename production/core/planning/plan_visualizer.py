#!/usr/bin/env python3
from __future__ import annotations
"""
计划可视化器 - Plan Visualizer
为执行计划提供多种可视化方式

支持的可视化格式:
1. Mermaid流程图
2. 文本列表
3. JSON结构
4. HTML表格

作者: 小诺·双鱼座
版本: v1.0.0 "可视化"
创建时间: 2025-01-05
"""

import json
from datetime import timedelta
from typing import Any

from .explicit_planner import ExecutionPlan, PlanStep


class PlanVisualizer:
    """计划可视化器"""

    def __init__(self):
        pass

    def visualize(self, plan: ExecutionPlan, format: str = "mermaid") -> str:
        """
        可视化计划

        Args:
            plan: 执行计划
            format: 可视化格式 (mermaid, text, json, html)

        Returns:
            可视化结果字符串
        """
        if format == "mermaid":
            return self.to_mermaid(plan)
        elif format == "text":
            return self.to_text(plan)
        elif format == "json":
            return self.to_json(plan)
        elif format == "html":
            return self.to_html(plan)
        else:
            raise ValueError(f"不支持的可视化格式: {format}")

    def to_mermaid(self, plan: ExecutionPlan) -> str:
        """
        转换为Mermaid流程图

        Mermaid语法:
        ```mermaid
        graph TD
            A[步骤1] --> B[步骤2]
            B --> C[步骤3]
        ```
        """
        lines = ["graph TD"]
        lines.append(f"    Start([开始]) --> Step{plan.steps[0].step_number}")

        # 添加所有步骤节点
        for step in plan.steps:
            step_id = f"Step{step.step_number}"

            # 根据置信度决定节点颜色(通过类名)
            confidence_class = self._get_confidence_class(step.confidence)

            # 节点定义
            node_text = f"{step.step_number}. {step.name}\\n预估: {self._format_duration(step.estimated_duration)}"
            node_def = f'    {step_id}["{node_text}"]:::{confidence_class}'
            lines.append(node_def)

            # 添加依赖关系
            for dep in step.dependencies:
                lines.append(f"    Step{dep} --> {step_id}")

            # 添加工具信息作为注释
            if step.tool:
                tool_info = f"{step.tool}: {step.description[:30]}..."
                lines.append(f"    %% {step_id}: {tool_info}")

        lines.append(f"    Step{plan.steps[-1].step_number} --> End([完成])")

        # 添加样式定义
        lines.append("\n    class_def high fill:#90EE90,stroke:#006400,stroke-width:2px")
        lines.append("    class_def medium fill:#FFD700,stroke:#B8860B,stroke-width:2px")
        lines.append("    class_def low fill:#FFB6C1,stroke:#8B0000,stroke-width:2px")
        lines.append("    class_def default fill:#E0E0E0,stroke:#666666,stroke-width:1px")

        return "\n".join(lines)

    def _get_confidence_class(self, confidence: float) -> str:
        """根据置信度返回CSS类名"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"

    def _format_duration(self, duration: timedelta) -> str:
        """格式化时间长度"""
        total_seconds = int(duration.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}秒"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}分钟"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"

    def to_text(self, plan: ExecutionPlan) -> str:
        """
        转换为文本格式

        格式:
        📋 执行计划名称
        总体描述
        ━━━━━━━━━━━━━━━━━━━━━━━
        ✅ 步骤1: 步骤名称
           工具: 工具名
           描述: 步骤描述
           预估时间: X分钟
           置信度: 90%
        """
        lines = []
        lines.append(f"📋 {plan.name}")
        lines.append(f"{plan.description}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"总步骤数: {len(plan.steps)}")
        lines.append(f"总预估时间: {self._format_duration(plan.total_duration)}")
        lines.append(f"总体置信度: {plan.total_confidence:.1%}")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        for step in plan.steps:
            emoji = self._get_step_emoji(step)
            lines.append(f"{emoji} 步骤{step.step_number}: {step.name}")
            lines.append(f"   🔧 工具: {step.tool}")
            lines.append(f"   📝 描述: {step.description}")

            if step.tool_parameters:
                params_str = ", ".join([f"{k}={v}" for k, v in step.tool_parameters.items()])
                lines.append(f"   ⚙️ 参数: {params_str}")

            if step.dependencies:
                deps_str = ", ".join([f"步骤{d}" for d in step.dependencies])
                lines.append(f"   🔗 依赖: {deps_str}")

            lines.append(f"   ⏱️ 预估: {self._format_duration(step.estimated_duration)}")
            lines.append(f"   📊 置信度: {step.confidence:.1%}")
            lines.append("")

        return "\n".join(lines)

    def _get_step_emoji(self, step: PlanStep) -> str:
        """根据步骤状态返回emoji"""
        status_emojis = {
            "pending": "⏳",
            "approved": "✅",
            "in_progress": "⚙️",
            "completed": "✅",
            "failed": "❌",
            "skipped": "⏭️",
        }
        return status_emojis.get(step.status.value, "📌")

    def to_json(self, plan: ExecutionPlan) -> str:
        """转换为JSON格式"""
        plan_dict = {
            "plan_id": plan.plan_id,
            "request_id": plan.request_id,
            "name": plan.name,
            "description": plan.description,
            "status": plan.status.value,
            "created_at": plan.created_at.isoformat(),
            "total_confidence": plan.total_confidence,
            "total_duration_minutes": plan.total_duration.total_seconds() / 60,
            "requires_approval": plan.requires_approval,
            "approved": plan.approved,
            "approval_comments": plan.approval_comments,
            "steps": [
                {
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
                for step in plan.steps
            ],
            "metadata": plan.metadata,
        }
        return json.dumps(plan_dict, ensure_ascii=False, indent=2)

    def to_html(self, plan: ExecutionPlan) -> str:
        """转换为HTML表格"""
        html_parts = []

        # HTML头部
        html_parts.append(
            """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{plan_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            text-align: left;
            padding: 12px;
            font-weight: bold;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-pending {{ background-color: #fff3cd; }}
        .status-completed {{ background-color: #d4edda; }}
        .status-failed {{ background-color: #f8d7da; }}
        .confidence-high {{ color: #28a745; font-weight: bold; }}
        .confidence-medium {{ color: #ffc107; font-weight: bold; }}
        .confidence-low {{ color: #dc3545; font-weight: bold; }}
        .step-number {{
            background-color: #007bff;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 {plan_name}</h1>
        <p><strong>描述:</strong> {description}</p>

        <div class="summary">
            <p><strong>总步骤数:</strong> {total_steps}</p>
            <p><strong>总预估时间:</strong> {total_duration}</p>
            <p><strong>总体置信度:</strong> {total_confidence}</p>
            <p><strong>状态:</strong> {status}</p>
        </div>

        <table>
            <thead>
                <tr>
                    <th>步骤</th>
                    <th>名称</th>
                    <th>工具</th>
                    <th>描述</th>
                    <th>预估时间</th>
                    <th>置信度</th>
                    <th>依赖</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
        """.format(
                plan_name=plan.name,
                description=plan.description,
                total_steps=len(plan.steps),
                total_duration=self._format_duration(plan.total_duration),
                total_confidence=f"{plan.total_confidence:.1%}",
                status=plan.status.value,
            )
        )

        # 表格行
        for step in plan.steps:
            confidence_class = self._get_confidence_class(step.confidence)
            status_class = f"status-{step.status.value}"

            dependencies_str = (
                ", ".join([f"步骤{d}" for d in step.dependencies]) if step.dependencies else "-"
            )

            html_parts.append(f"""
                <tr class="{status_class}">
                    <td><span class="step-number">{step.step_number}</span></td>
                    <td><strong>{step.name}</strong></td>
                    <td>{step.tool}</td>
                    <td>{step.description[:80]}...</td>
                    <td>{self._format_duration(step.estimated_duration)}</td>
                    <td class="confidence-{confidence_class}">{step.confidence:.1%}</td>
                    <td>{dependencies_str}</td>
                    <td>{self._get_step_emoji(step)} {step.status.value}</td>
                </tr>
            """)

        # HTML尾部
        html_parts.append("""
            </tbody>
        </table>
    </div>
</body>
</html>
        """)

        return "".join(html_parts)

    def get_step_details(self, plan: ExecutionPlan, step_number: int) -> dict[str, Any] | None:
        """获取特定步骤的详细信息"""
        for step in plan.steps:
            if step.step_number == step_number:
                return {
                    "step_id": step.step_id,
                    "step_number": step.step_number,
                    "name": step.name,
                    "description": step.description,
                    "tool": step.tool,
                    "tool_parameters": step.tool_parameters,
                    "dependencies": step.dependencies,
                    "confidence": step.confidence,
                    "estimated_duration": self._format_duration(step.estimated_duration),
                    "status": step.status.value,
                    "result": step.result,
                    "error": step.error,
                    "metadata": step.metadata,
                }
        return None

    def compare_plans(self, plan_before: ExecutionPlan, plan_after: ExecutionPlan) -> str:
        """
        比较两个计划,展示差异

        用于动态调整后展示变化
        """
        lines = ["📊 计划对比分析"]
        lines.append("=" * 50)

        # 基本统计对比
        lines.append(f"\n步骤数量: {len(plan_before.steps)} → {len(plan_after.steps)}")
        lines.append(
            f"总预估时间: {self._format_duration(plan_before.total_duration)} → {self._format_duration(plan_after.total_duration)}"
        )
        lines.append(
            f"总体置信度: {plan_before.total_confidence:.1%} → {plan_after.total_confidence:.1%}"
        )

        # 步骤变化
        lines.append("\n步骤变化:")
        lines.append("-" * 50)

        # 找出新增、修改、删除的步骤
        before_steps = {s.step_number: s for s in plan_before.steps}
        after_steps = {s.step_number: s for s in plan_after.steps}

        all_step_numbers = set(before_steps.keys()) | set(after_steps.keys())

        for step_num in sorted(all_step_numbers):
            before_step = before_steps.get(step_num)
            after_step = after_steps.get(step_num)

            if before_step and not after_step:
                lines.append(f"  ❌ 步骤{step_num}: 删除 - {before_step.name}")
            elif after_step and not before_step:
                lines.append(f"  ➕ 步骤{step_num}: 新增 - {after_step.name}")
            elif before_step.name != after_step.name:
                lines.append(f"  🔄 步骤{step_num}: 修改")
                lines.append(f"     旧: {before_step.name}")
                lines.append(f"     新: {after_step.name}")
            elif before_step.status != after_step.status:
                lines.append(
                    f"  📊 步骤{step_num}: 状态变化 {before_step.status.value} → {after_step.status.value}"
                )

        return "\n".join(lines)


# 全局实例
plan_visualizer = PlanVisualizer()


def get_plan_visualizer() -> PlanVisualizer:
    """获取计划可视化器单例"""
    return plan_visualizer
