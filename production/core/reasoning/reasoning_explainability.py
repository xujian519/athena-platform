#!/usr/bin/env python3
"""
推理结果可解释性增强系统
Reasoning Result Explainability Enhancement System

作者: Athena AI团队
版本: v1.0.0
创建时间: 2026-01-26

功能:
1. 推理过程可视化
2. 生成推理过程报告
3. 支持交互式推理调整
4. 推理链追踪和分析
5. 推理质量评估
"""

from __future__ import annotations
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ExplainabilityLevel(Enum):
    """可解释性级别"""

    MINIMAL = "minimal"  # 最小解释(仅结论)
    BASIC = "basic"  # 基本解释(结论+关键步骤)
    DETAILED = "detailed"  # 详细解释(完整推理链)
    COMPREHENSIVE = "comprehensive"  # 全面解释(包含所有元数据)


class VisualizationFormat(Enum):
    """可视化格式"""

    TEXT = "text"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    MERMAID = "mermaid"  # 流程图
    ASCII = "ascii"  # ASCII图


@dataclass
class ReasoningStep:
    """推理步骤"""

    step_id: str
    step_number: int
    description: str
    reasoning_type: str

    # 输入输出
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    # 置信度和时间
    confidence: float = 0.0
    execution_time: float = 0.0

    # 依赖关系
    dependencies: list[str] = field(default_factory=list)

    # 解释
    explanation: str = ""
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ReasoningChain:
    """推理链"""

    chain_id: str
    task_description: str
    reasoning_mode: str

    # 步骤列表
    steps: list[ReasoningStep] = field(default_factory=list)

    # 元数据
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    total_duration: float = 0.0

    # 最终结果
    final_conclusion: str = ""
    final_confidence: float = 0.0

    # 质量评估
    quality_score: float = 0.0
    completeness_score: float = 0.0
    consistency_score: float = 0.0

    def add_step(self, step: ReasoningStep) -> None:
        """添加推理步骤"""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)

    def get_step_by_id(self, step_id: str) -> ReasoningStep | None:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        if self.end_time:
            data["end_time"] = self.end_time.isoformat()
        return data


@dataclass
class ReasoningAdjustment:
    """推理调整"""

    adjustment_id: str
    target_step_id: str

    # 调整类型
    adjustment_type: str  # modify, remove, insert, reroute

    # 调整内容
    original_content: dict[str, Any] = field(default_factory=dict)
    new_content: dict[str, Any] = field(default_factory=dict)

    # 调整原因
    reason: str = ""

    # 影响分析
    affected_steps: list[str] = field(default_factory=list)
    impact_score: float = 0.0


class ReasoningExplainer:
    """推理解释器"""

    def __init__(self, default_level: ExplainabilityLevel = ExplainabilityLevel.DETAILED):
        self.default_level = default_level

        logger.info("📝 推理解释器初始化完成")

    def explain_reasoning(
        self,
        reasoning_chain: ReasoningChain,
        level: ExplainabilityLevel | None = None,
        format: VisualizationFormat = VisualizationFormat.TEXT,
    ) -> str:
        """解释推理过程

        Args:
            reasoning_chain: 推理链
            level: 解释级别
            format: 输出格式

        Returns:
            格式化的解释文本
        """
        level = level or self.default_level

        if format == VisualizationFormat.TEXT:
            return self._explain_as_text(reasoning_chain, level)
        elif format == VisualizationFormat.MARKDOWN:
            return self._explain_as_markdown(reasoning_chain, level)
        elif format == VisualizationFormat.HTML:
            return self._explain_as_html(reasoning_chain, level)
        elif format == VisualizationFormat.JSON:
            return self._explain_as_json(reasoning_chain, level)
        elif format == VisualizationFormat.MERMAID:
            return self._explain_as_mermaid(reasoning_chain, level)
        elif format == VisualizationFormat.ASCII:
            return self._explain_as_ascii(reasoning_chain, level)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _explain_as_text(
        self, chain: ReasoningChain, level: ExplainabilityLevel
    ) -> str:
        """生成文本格式解释"""
        lines = []

        # 标题
        lines.append("=" * 80)
        lines.append(f"推理过程解释 ({level.value})")
        lines.append("=" * 80)
        lines.append("")

        # 基本信息
        if level in [ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
            lines.append("📋 基本信息:")
            lines.append(f"  任务: {chain.task_description}")
            lines.append(f"  模式: {chain.reasoning_mode}")
            lines.append(f"  开始时间: {chain.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"  总耗时: {chain.total_duration:.3f}秒")
            lines.append("")

        # 推理步骤
        if level != ExplainabilityLevel.MINIMAL:
            lines.append("🔍 推理步骤:")
            lines.append("")

            for step in chain.steps:
                lines.append(f"  步骤 {step.step_number}: {step.description}")
                lines.append(f"    类型: {step.reasoning_type}")

                if level in [ExplainabilityLevel.BASIC, ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
                    if step.confidence > 0:
                        lines.append(f"    置信度: {step.confidence:.2%}")
                    if step.execution_time > 0:
                        lines.append(f"    耗时: {step.execution_time:.3f}秒")

                if level in [ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
                    if step.explanation:
                        lines.append(f"    解释: {step.explanation}")
                    if step.rationale:
                        lines.append(f"    理由: {step.rationale}")

                    if step.inputs:
                        lines.append(f"    输入: {json.dumps(step.inputs, ensure_ascii=False)}")
                    if step.outputs:
                        lines.append(f"    输出: {json.dumps(step.outputs, ensure_ascii=False)}")

                lines.append("")

        # 最终结论
        lines.append("✅ 最终结论:")
        lines.append(f"  {chain.final_conclusion}")

        if chain.final_confidence > 0:
            lines.append(f"  置信度: {chain.final_confidence:.2%}")

        # 质量评估(仅全面解释)
        if level == ExplainabilityLevel.COMPREHENSIVE:
            lines.append("")
            lines.append("📊 质量评估:")
            lines.append(f"  质量分数: {chain.quality_score:.3f}")
            lines.append(f"  完整性: {chain.completeness_score:.3f}")
            lines.append(f"  一致性: {chain.consistency_score:.3f}")

        return "\n".join(lines)

    def _explain_as_markdown(
        self, chain: ReasoningChain, level: ExplainabilityLevel
    ) -> str:
        """生成Markdown格式解释"""
        lines = []

        # 标题
        lines.append("# 推理过程解释")
        lines.append("")
        lines.append(f"**级别**: {level.value}")
        lines.append("")

        # 基本信息
        if level in [ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
            lines.append("## 📋 基本信息")
            lines.append("")
            lines.append(f"- **任务**: {chain.task_description}")
            lines.append(f"- **模式**: {chain.reasoning_mode}")
            lines.append(f"- **开始时间**: {chain.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"- **总耗时**: {chain.total_duration:.3f}秒")
            lines.append("")

        # 推理步骤
        if level != ExplainabilityLevel.MINIMAL:
            lines.append("## 🔍 推理步骤")
            lines.append("")

            for step in chain.steps:
                lines.append(f"### 步骤 {step.step_number}: {step.description}")
                lines.append("")
                lines.append(f"- **类型**: {step.reasoning_type}")

                if level in [ExplainabilityLevel.BASIC, ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
                    if step.confidence > 0:
                        lines.append(f"- **置信度**: {step.confidence:.2%}")
                    if step.execution_time > 0:
                        lines.append(f"- **耗时**: {step.execution_time:.3f}秒")

                if level in [ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
                    if step.explanation:
                        lines.append(f"- **解释**: {step.explanation}")
                    if step.rationale:
                        lines.append(f"- **理由**: {step.rationale}")

                    if step.inputs:
                        lines.append(f"- **输入**: `{json.dumps(step.inputs, ensure_ascii=False)}`")
                    if step.outputs:
                        lines.append(f"- **输出**: `{json.dumps(step.outputs, ensure_ascii=False)}`")

                lines.append("")

        # 最终结论
        lines.append("## ✅ 最终结论")
        lines.append("")
        lines.append(chain.final_conclusion)

        if chain.final_confidence > 0:
            lines.append("")
            lines.append(f"**置信度**: {chain.final_confidence:.2%}")

        # 质量评估
        if level == ExplainabilityLevel.COMPREHENSIVE:
            lines.append("")
            lines.append("## 📊 质量评估")
            lines.append("")
            lines.append(f"- **质量分数**: {chain.quality_score:.3f}")
            lines.append(f"- **完整性**: {chain.completeness_score:.3f}")
            lines.append(f"- **一致性**: {chain.consistency_score:.3f}")

        return "\n".join(lines)

    def _explain_as_html(
        self, chain: ReasoningChain, level: ExplainabilityLevel
    ) -> str:
        """生成HTML格式解释"""
        html = []

        # 样式
        html.append("<style>")
        html.append("""
        .reasoning-container { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; }
        .reasoning-header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .reasoning-steps { margin: 20px 0; }
        .reasoning-step { background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .reasoning-step h3 { margin-top: 0; color: #333; }
        .reasoning-conclusion { background: #e8f5e9; padding: 20px; border-radius: 5px; margin-top: 20px; }
        .confidence-meter { height: 10px; background: #ddd; border-radius: 5px; overflow: hidden; }
        .confidence-fill { height: 100%; background: #4caf50; transition: width 0.3s; }
        """)
        html.append("</style>")

        # 容器
        html.append('<div class="reasoning-container">')

        # 标题
        html.append('<div class="reasoning-header">')
        html.append(f"<h1>推理过程解释 ({level.value})</h1>")
        html.append("</div>")

        # 基本信息
        if level in [ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
            html.append("<h2>📋 基本信息</h2>")
            html.append("<ul>")
            html.append(f"<li><strong>任务</strong>: {chain.task_description}</li>")
            html.append(f"<li><strong>模式</strong>: {chain.reasoning_mode}</li>")
            html.append(f"<li><strong>开始时间</strong>: {chain.start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>")
            html.append(f"<li><strong>总耗时</strong>: {chain.total_duration:.3f}秒</li>")
            html.append("</ul>")

        # 推理步骤
        if level != ExplainabilityLevel.MINIMAL:
            html.append('<div class="reasoning-steps">')
            html.append("<h2>🔍 推理步骤</h2>")

            for step in chain.steps:
                html.append('<div class="reasoning-step">')
                html.append(f"<h3>步骤 {step.step_number}: {step.description}</h3>")
                html.append(f"<p><strong>类型</strong>: {step.reasoning_type}</p>")

                if level in [ExplainabilityLevel.BASIC, ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
                    if step.confidence > 0:
                        html.append(f"<p><strong>置信度</strong>: {step.confidence:.2%}</p>")
                        html.append(f'<div class="confidence-meter"><div class="confidence-fill" style="width: {step.confidence * 100}%"></div></div>')
                    if step.execution_time > 0:
                        html.append(f"<p><strong>耗时</strong>: {step.execution_time:.3f}秒</p>")

                if level in [ExplainabilityLevel.DETAILED, ExplainabilityLevel.COMPREHENSIVE]:
                    if step.explanation:
                        html.append(f"<p><strong>解释</strong>: {step.explanation}</p>")
                    if step.rationale:
                        html.append(f"<p><strong>理由</strong>: {step.rationale}</p>")

                html.append("</div>")

            html.append("</div>")

        # 最终结论
        html.append('<div class="reasoning-conclusion">')
        html.append("<h2>✅ 最终结论</h2>")
        html.append(f"<p>{chain.final_conclusion}</p>")

        if chain.final_confidence > 0:
            html.append(f"<p><strong>置信度</strong>: {chain.final_confidence:.2%}</p>")
            html.append(f'<div class="confidence-meter"><div class="confidence-fill" style="width: {chain.final_confidence * 100}%"></div></div>')

        html.append("</div>")
        html.append("</div>")

        return "\n".join(html)

    def _explain_as_json(
        self, chain: ReasoningChain, level: ExplainabilityLevel
    ) -> str:
        """生成JSON格式解释"""
        data = {
            "level": level.value,
            "chain": chain.to_dict(),
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _explain_as_mermaid(
        self, chain: ReasoningChain, level: ExplainabilityLevel
    ) -> str:
        """生成Mermaid流程图"""
        lines = []
        lines.append("graph TD")

        # 添加节点
        for i, step in enumerate(chain.steps):
            node_id = f"S{i}"
            label = f"{step.step_number}. {step.description[:30]}..."

            if level == ExplainabilityLevel.MINIMAL:
                lines.append(f"    {node_id}[{label}]")
            else:
                confidence_str = f"<br>{step.confidence:.0%}" if step.confidence > 0 else ""
                lines.append(f'    {node_id}["{label}{confidence_str}"]')

        # 添加边
        for i, step in enumerate(chain.steps):
            if i < len(chain.steps) - 1:
                lines.append(f"    S{i} --> S{i+1}")

            # 添加依赖关系
            for dep in step.dependencies:
                lines.append(f"    {dep} -.-> S{i}")

        # 添加最终结论
        if chain.steps:
            last_step = f"S{len(chain.steps) - 1}"
            lines.append(f'    Final["✅ {chain.final_conclusion[:30]}..."]')
            lines.append(f"    {last_step} --> Final")

        return "\n".join(lines)

    def _explain_as_ascii(
        self, chain: ReasoningChain, level: ExplainabilityLevel
    ) -> str:
        """生成ASCII艺术图"""
        lines = []

        if not chain.steps:
            return "无推理步骤"

        # 简单的垂直流程图
        for i, step in enumerate(chain.steps):
            # 步骤框
            lines.append("┌" + "─" * 76 + "┐")
            lines.append(f"│ 步骤 {step.step_number}: {step.description[:70]:70s} │")

            if level != ExplainabilityLevel.MINIMAL:
                lines.append(f"│ 类型: {step.reasoning_type:20s}  "
                           f"置信度: {step.confidence:.0%:6s}  "
                           f"耗时: {step.execution_time:.3f}s │")

            lines.append("└" + "─" * 76 + "┘")

            # 箭头
            if i < len(chain.steps) - 1:
                lines.append("         │")
                lines.append("         ▼")
                lines.append("")

        # 最终结论
        lines.append("┌" + "─" * 76 + "┐")
        lines.append(f"│ ✅ 最终结论: {chain.final_conclusion[:70]:70s} │")
        if chain.final_confidence > 0:
            lines.append(f"│ 置信度: {chain.final_confidence:.0%:76s} │")
        lines.append("└" + "─" * 76 + "┘")

        return "\n".join(lines)


class InteractiveReasoningEditor:
    """交互式推理编辑器"""

    def __init__(self):
        self.adjustments: list[ReasoningAdjustment] = []
        self.chains: dict[str, ReasoningChain] = {}

        logger.info("🔧 交互式推理编辑器初始化完成")

    def load_chain(self, chain: ReasoningChain) -> None:
        """加载推理链"""
        self.chains[chain.chain_id] = chain
        logger.info(f"加载推理链: {chain.chain_id}")

    def modify_step(
        self,
        chain_id: str,
        step_id: str,
        new_description: str | None = None,
        new_explanation: str | None = None,
        new_rationale: str | None = None,
        reason: str = "",
    ) -> ReasoningAdjustment:
        """修改推理步骤"""
        chain = self.chains.get(chain_id)
        if not chain:
            raise ValueError(f"未找到推理链: {chain_id}")

        step = chain.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"未找到步骤: {step_id}")

        # 保存原始内容
        original_content = {
            "description": step.description,
            "explanation": step.explanation,
            "rationale": step.rationale,
        }

        # 应用修改
        if new_description is not None:
            step.description = new_description
        if new_explanation is not None:
            step.explanation = new_explanation
        if new_rationale is not None:
            step.rationale = new_rationale

        # 创建调整记录
        new_content = {
            "description": step.description,
            "explanation": step.explanation,
            "rationale": step.rationale,
        }

        adjustment = ReasoningAdjustment(
            adjustment_id=f"adj_{datetime.now().timestamp()}",
            target_step_id=step_id,
            adjustment_type="modify",
            original_content=original_content,
            new_content=new_content,
            reason=reason,
        )

        self.adjustments.append(adjustment)
        logger.info(f"修改步骤: {step_id}")

        return adjustment

    def analyze_impact(self, chain_id: str, step_id: str) -> dict[str, Any]:
        """分析修改影响"""
        chain = self.chains.get(chain_id)
        if not chain:
            raise ValueError(f"未找到推理链: {chain_id}")

        step = chain.get_step_by_id(step_id)
        if not step:
            raise ValueError(f"未找到步骤: {step_id}")

        # 找出依赖此步骤的所有后续步骤
        affected_steps = []
        step_index = chain.steps.index(step)

        for s in chain.steps[step_index + 1:]:
            if step_id in s.dependencies:
                affected_steps.append(s.step_id)

        return {
            "step_id": step_id,
            "affected_steps": affected_steps,
            "impact_count": len(affected_steps),
            "recommendation": "需要重新执行后续步骤" if affected_steps else "无影响",
        }

    def generate_adjustment_report(self) -> str:
        """生成调整报告"""
        if not self.adjustments:
            return "无调整记录"

        lines = []
        lines.append("=" * 80)
        lines.append("推理调整报告")
        lines.append("=" * 80)
        lines.append("")

        for adj in self.adjustments:
            lines.append(f"调整ID: {adj.adjustment_id}")
            lines.append(f"目标步骤: {adj.target_step_id}")
            lines.append(f"调整类型: {adj.adjustment_type}")

            if adj.reason:
                lines.append(f"原因: {adj.reason}")

            lines.append(f"影响步骤: {', '.join(adj.affected_steps) if adj.affected_steps else '无'}")
            lines.append(f"影响分数: {adj.impact_score:.3f}")
            lines.append("")

        return "\n".join(lines)


class ReasoningQualityAssessor:
    """推理质量评估器"""

    def __init__(self):
        logger.info("🎯 推理质量评估器初始化完成")

    def assess(
        self, chain: ReasoningChain
    ) -> dict[str, Any]:
        """评估推理质量

        Args:
            chain: 推理链

        Returns:
            质量评估结果
        """
        # 完整性评估
        completeness = self._assess_completeness(chain)

        # 一致性评估
        consistency = self._assess_consistency(chain)

        # 逻辑性评估
        logic_score = self._assess_logic(chain)

        # 创新性评估
        innovation_score = self._assess_innovation(chain)

        # 综合质量分数
        quality_score = (
            completeness * 0.3
            + consistency * 0.3
            + logic_score * 0.25
            + innovation_score * 0.15
        )

        # 更新链的分数
        chain.quality_score = quality_score
        chain.completeness_score = completeness
        chain.consistency_score = consistency

        # 生成建议
        recommendations = self._generate_recommendations({
            "quality": quality_score,
            "completeness": completeness,
            "consistency": consistency,
            "logic": logic_score,
            "innovation": innovation_score,
        })

        return {
            "overall_quality": quality_score,
            "completeness": completeness,
            "consistency": consistency,
            "logic": logic_score,
            "innovation": innovation_score,
            "recommendations": recommendations,
        }

    def _assess_completeness(self, chain: ReasoningChain) -> float:
        """评估完整性"""
        if not chain.steps:
            return 0.0

        # 检查每个步骤的完整性
        complete_steps = 0
        for step in chain.steps:
            if (step.description
                and step.reasoning_type
                and (step.inputs or step.outputs)):
                complete_steps += 1

        return complete_steps / len(chain.steps)

    def _assess_consistency(self, chain: ReasoningChain) -> float:
        """评估一致性"""
        if len(chain.steps) < 2:
            return 1.0

        # 检查相邻步骤的一致性
        consistent_count = 0
        for i in range(len(chain.steps) - 1):
            current = chain.steps[i]
            next_step = chain.steps[i + 1]

            # 检查输出是否匹配输入
            if current.outputs and next_step.inputs:
                # 简化的检查: 看是否有共同的键
                if set(current.outputs.keys()) & set(next_step.inputs.keys()):
                    consistent_count += 1

        return consistent_count / max(len(chain.steps) - 1, 1)

    def _assess_logic(self, chain: ReasoningChain) -> float:
        """评估逻辑性"""
        # 基于置信度的评估
        if not chain.steps:
            return 0.0

        confidences = [s.confidence for s in chain.steps if s.confidence > 0]
        if not confidences:
            return 0.5  # 中性分数

        return sum(confidences) / len(confidences)

    def _assess_innovation(self, chain: ReasoningChain) -> float:
        """评估创新性"""
        # 简化的创新性评估
        # 检查是否使用了多样化的推理类型
        reasoning_types = {s.reasoning_type for s in chain.steps}
        diversity_score = min(len(reasoning_types) / 5, 1.0)  # 最多5种类型

        return diversity_score

    def _generate_recommendations(self, scores: dict[str, float]) -> list[str]:
        """生成改进建议"""
        recommendations = []

        if scores["completeness"] < 0.7:
            recommendations.append("建议补充缺失的推理步骤信息")

        if scores["consistency"] < 0.7:
            recommendations.append("建议检查步骤间的逻辑一致性")

        if scores["logic"] < 0.7:
            recommendations.append("建议提升推理的置信度")

        if scores["innovation"] < 0.5:
            recommendations.append("建议增加推理类型多样性")

        if not recommendations:
            recommendations.append("推理质量良好,暂无改进建议")

        return recommendations


# 全局单例
_explainer_instance: ReasoningExplainer | None = None
_editor_instance: InteractiveReasoningEditor | None = None
_assessor_instance: ReasoningQualityAssessor | None = None


def get_explainer() -> ReasoningExplainer:
    """获取推理解释器实例"""
    global _explainer_instance
    if _explainer_instance is None:
        _explainer_instance = ReasoningExplainer()
    return _explainer_instance


def get_editor() -> InteractiveReasoningEditor:
    """获取交互式编辑器实例"""
    global _editor_instance
    if _editor_instance is None:
        _editor_instance = InteractiveReasoningEditor()
    return _editor_instance


def get_assessor() -> ReasoningQualityAssessor:
    """获取质量评估器实例"""
    global _assessor_instance
    if _assessor_instance is None:
        _assessor_instance = ReasoningQualityAssessor()
    return _assessor_instance


# 便捷函数
def explain_reasoning(
    chain: ReasoningChain,
    level: ExplainabilityLevel = ExplainabilityLevel.DETAILED,
    format: VisualizationFormat = VisualizationFormat.TEXT,
) -> str:
    """解释推理过程(便捷函数)"""
    explainer = get_explainer()
    return explainer.explain_reasoning(chain, level, format)


# 测试代码
if __name__ == "__main__":
    # 创建测试推理链
    chain = ReasoningChain(
        chain_id="test_chain",
        task_description="测试推理可解释性",
        reasoning_mode="sequential",
    )

    # 添加推理步骤
    step1 = ReasoningStep(
        step_id="step_1",
        step_number=1,
        description="分析问题",
        reasoning_type="analysis",
        confidence=0.9,
        execution_time=0.5,
        explanation="深入分析问题的各个方面",
        rationale="全面理解是解决问题的前提",
    )
    chain.add_step(step1)

    step2 = ReasoningStep(
        step_id="step_2",
        step_number=2,
        description="生成假设",
        reasoning_type="hypothesis",
        confidence=0.8,
        execution_time=1.0,
        explanation="基于分析结果生成多个假设",
        rationale="多假设可以提高结论可靠性",
        dependencies=["step_1"],
    )
    chain.add_step(step2)

    step3 = ReasoningStep(
        step_id="step_3",
        step_number=3,
        description="验证假设",
        reasoning_type="verification",
        confidence=0.85,
        execution_time=0.8,
        explanation="通过测试验证假设的有效性",
        rationale="验证确保结论的正确性",
        dependencies=["step_2"],
    )
    chain.add_step(step3)

    chain.final_conclusion = "经过分析和验证,结论成立"
    chain.final_confidence = 0.85
    chain.end_time = datetime.now()
    chain.total_duration = 2.3

    # 测试解释器
    explainer = get_explainer()

    print("=" * 80)
    print("🧪 测试推理解释器")
    print("=" * 80)

    # 文本格式
    print("\n📝 文本格式:")
    print(explainer.explain_reasoning(chain, ExplainabilityLevel.DETAILED, VisualizationFormat.TEXT))

    # Markdown格式
    print("\n📋 Markdown格式:")
    print(explainer.explain_reasoning(chain, ExplainabilityLevel.BASIC, VisualizationFormat.MARKDOWN))

    # ASCII格式
    print("\n🎨 ASCII格式:")
    print(explainer.explain_reasoning(chain, ExplainabilityLevel.MINIMAL, VisualizationFormat.ASCII))

    # Mermaid格式
    print("\n📊 Mermaid流程图:")
    print(explainer.explain_reasoning(chain, ExplainabilityLevel.BASIC, VisualizationFormat.MERMAID))

    # 测试质量评估
    print("\n" + "=" * 80)
    print("🎯 测试质量评估器")
    print("=" * 80)

    assessor = get_assessor()
    quality = assessor.assess(chain)

    print(f"\n质量分数: {quality['overall_quality']:.3f}")
    print(f"完整性: {quality['completeness']:.3f}")
    print(f"一致性: {quality['consistency']:.3f}")
    print(f"逻辑性: {quality['logic']:.3f}")
    print(f"创新性: {quality['innovation']:.3f}")

    print("\n💡 改进建议:")
    for rec in quality["recommendations"]:
        print(f"  - {rec}")

    # 测试交互式编辑器
    print("\n" + "=" * 80)
    print("🔧 测试交互式编辑器")
    print("=" * 80)

    editor = get_editor()
    editor.load_chain(chain)

    # 修改步骤
    adjustment = editor.modify_step(
        chain_id="test_chain",
        step_id="step_1",
        new_description="深入分析问题的各个方面",
        reason="提高描述的准确性"
    )

    print(f"\n修改步骤: {adjustment.target_step_id}")
    print(f"原因: {adjustment.reason}")

    # 分析影响
    impact = editor.analyze_impact("test_chain", "step_1")
    print("\n影响分析:")
    print(f"  受影响步骤: {impact['affected_steps']}")
    print(f"  建议: {impact['recommendation']}")

    # 生成调整报告
    print("\n调整报告:")
    print(editor.generate_adjustment_report())
