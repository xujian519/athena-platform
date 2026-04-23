from __future__ import annotations

"""
专利权利要求质量评估器

基于论文3《Can Large Language Models Generate High-Quality Patent Claims?》
实现六维质量评估框架。

六个质量维度：
1. 新颖性 (Novelty) - 权利要求是否清楚限定与现有技术的区别
2. 清晰性 (Clarity) - 权利要求是否易于理解和执行
3. 完整性 (Completeness) - 是否包含保护发明的所有必要特征
4. 支持性 (Support) - 权利要求是否能够得到说明书的支持
5. 范围恰当性 (Scope Appropriateness) - 保护范围是否宽窄得当
6. 法律规范性 (Legal Compliance) - 是否符合专利法规范和格式要求
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QualityDimension(Enum):
    """质量维度枚举"""
    NOVELTY = "novelty"  # 新颖性
    CLARITY = "clarity"  # 清晰性
    COMPLETENESS = "completeness"  # 完整性
    SUPPORT = "support"  # 支持性
    SCOPE_APPROPRIATENESS = "scope_appropriateness"  # 范围恰当性
    LEGAL_COMPLIANCE = "legal_compliance"  # 法律规范性


class SeverityLevel(Enum):
    """问题严重程度"""
    CRITICAL = "critical"  # 严重，必须修复
    IMPORTANT = "important"  # 重要，强烈建议修复
    SUGGESTED = "suggested"  # 建议，可选修复


@dataclass
class QualityIssue:
    """质量问题"""
    dimension: QualityDimension
    description: str
    severity: SeverityLevel
    location: str | None = None  # 问题在文本中的位置
    suggestion: str | None = None


@dataclass
class DimensionScore:
    """维度评分"""
    dimension: QualityDimension
    score: float  # 0-10分
    issues: list[QualityIssue] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)  # 该维度的优点
    suggestions: list[str] = field(default_factory=list)


@dataclass
class QualityAssessment:
    """完整质量评估结果"""
    claim_text: str
    assessed_at: datetime
    overall_score: float  # 加权总分

    # 各维度得分
    dimension_scores: dict[QualityDimension, DimensionScore]

    # 汇总信息
    critical_issues: list[QualityIssue] = field(default_factory=list)
    improvement_priority: list[QualityDimension] = field(default_factory=list)

    # 评级
    quality_level: str = ""  # "优秀", "良好", "中等", "较差", "差"
    can_file: bool = True  # 是否可以直接提交

    def get_summary(self) -> str:
        """获取评估摘要"""
        return f"""
质量评估摘要
{'='*60}
总体评分: {self.overall_score:.1f}/10
质量等级: {self.quality_level}
可提交性: {'是' if self.can_file else '否 (需要改进)'}

各维度得分:
{'='*60}
{self._format_dimension_scores()}

关键问题:
{'='*60}
{self._format_issues()}

改进建议:
{'='*60}
{self._format_suggestions()}
{'='*60}
        """.strip()

    def _format_dimension_scores(self) -> str:
        """格式化维度得分"""
        lines = []
        for dim, score in self.dimension_scores.items():
            icon = self._get_score_icon(score.score)
            lines.append(f"  {icon} {dim.value:20s}: {score.score:.1f}/10")
        return "\n".join(lines)

    def _format_issues(self) -> str:
        """格式化问题列表"""
        if not self.critical_issues:
            return "  ✅ 无严重问题"

        lines = []
        for issue in self.critical_issues[:5]:  # 最多显示5个
            severity_icon = "🔴" if issue.severity == SeverityLevel.CRITICAL else "⚠️"
            lines.append(f"  {severity_icon} [{issue.dimension.value}] {issue.description}")

        if len(self.critical_issues) > 5:
            lines.append(f"  ... 还有 {len(self.critical_issues) - 5} 个问题")

        return "\n".join(lines)

    def _format_suggestions(self) -> str:
        """格式化改进建议"""
        all_suggestions = []
        for score in self.dimension_scores.values():
            all_suggestions.extend(score.suggestions)

        if not all_suggestions:
            return "  ✅ 暂无具体建议"

        lines = []
        for i, suggestion in enumerate(all_suggestions[:5], 1):
            lines.append(f"  {i}. {suggestion}")

        return "\n".join(lines)

    @staticmethod
    def _get_score_icon(score: float) -> str:
        """获取分数对应的图标"""
        if score >= 9:
            return "🟢"
        elif score >= 7:
            return "🟡"
        elif score >= 5:
            return "🟠"
        else:
            return "🔴"


class ClaimQualityAssessor:
    """
    专利权利要求质量评估器

    实现基于论文3的六维质量评估框架，结合LLM进行智能评估。
    """

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        QualityDimension.NOVELTY: 2.0,  # 新颖性最重要
        QualityDimension.CLARITY: 1.0,
        QualityDimension.COMPLETENESS: 1.0,
        QualityDimension.SUPPORT: 1.0,
        QualityDimension.SCOPE_APPROPRIATENESS: 1.5,  # 范围恰当性较重要
        QualityDimension.LEGAL_COMPLIANCE: 1.5,  # 法律规范性较重要
    }

    # 质量等级阈值
    QUALITY_LEVELS = {
        "优秀": (9.0, 10.0),
        "良好": (7.5, 9.0),
        "中等": (6.0, 7.5),
        "较差": (4.0, 6.0),
        "差": (0.0, 4.0),
    }

    def __init__(self, llm_client=None):
        """
        初始化评估器

        Args:
            llm_client: LLM客户端（Claude、GPT等）
        """
        self.llm = llm_client
        self._evaluation_prompts = self._load_prompts()

    def assess(self,
             claim_text: str,
             description: str,
             prior_art: list[str] | None = None,
             cpc_code: str | None = None) -> QualityAssessment:
        """
        全面评估权利要求质量

        Args:
            claim_text: 权利要求文本
            description: 说明书描述
            prior_art: 相关现有技术（可选）
            cpc_code: CPC分类代码（可选）

        Returns:
            QualityAssessment: 完整评估结果
        """
        dimension_scores = {}

        # 评估六个维度
        for dimension in QualityDimension:
            score = self._assess_dimension(
                dimension,
                claim_text,
                description,
                prior_art,
                cpc_code
            )
            dimension_scores[dimension] = score

        # 计算加权总分
        overall_score = self._calculate_overall_score(dimension_scores)

        # 提取关键问题
        critical_issues = self._extract_critical_issues(dimension_scores)

        # 确定改进优先级
        improvement_priority = self._determine_improvement_priority(dimension_scores)

        # 确定质量等级
        quality_level = self._determine_quality_level(overall_score)

        # 判断是否可直接提交
        can_file = quality_level in ["优秀", "良好"]

        return QualityAssessment(
            claim_text=claim_text,
            assessed_at=datetime.now(),
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            critical_issues=critical_issues,
            improvement_priority=improvement_priority,
            quality_level=quality_level,
            can_file=can_file
        )

    def _assess_dimension(self,
                      dimension: QualityDimension,
                      claim: str,
                      description: str,
                      prior_art: list[str] | None,
                      cpc_code: str | None) -> DimensionScore:
        """评估单个维度"""

        prompt = self._build_evaluation_prompt(
            dimension, claim, description, prior_art, cpc_code
        )

        # 调用LLM进行评估
        response = self.llm.generate(prompt)

        # 解析响应
        return self._parse_dimension_response(dimension, response, claim)

    def _build_evaluation_prompt(self,
                              dimension: QualityDimension,
                              claim: str,
                              description: str,
                              prior_art: list[str] | None,
                              cpc_code: str | None) -> str:
        """构建评估提示词"""

        base_prompt = self._evaluation_prompts.get(dimension.value)

        context_parts = []
        if prior_art:
            context_parts.append("相关现有技术:\n" + "\n".join(prior_art))
        if cpc_code:
            context_parts.append(f"CPC分类代码: {cpc_code}")

        context = "\n\n".join(context_parts) if context_parts else "无"

        return f"""
{base_prompt}

权利要求:
{claim}

说明书描述:
{description}

{context}

请严格按照以下JSON格式返回评估结果:
{{
    "score": <1-10分的评分>,
    "issues": [
        {{
            "description": "<问题描述>",
            "severity": "<critical/important/suggested>",
            "suggestion": "<改进建议>"
        }}
    ],
    "strengths": ["<优点1>", "<优点2>"],
    "analysis": "<详细分析>"
}}
        """.strip()

    def _parse_dimension_response(self,
                               dimension: QualityDimension,
                               response: str,
                               claim: str) -> DimensionScore:
        """解析LLM评估响应"""
        try:
            data = json.loads(response)
            score = float(data.get("score", 5.0))

            issues = []
            for issue_data in data.get("issues", []):
                severity = SeverityLevel.CRITICAL if \
                    issue_data.get("severity") == "critical" else \
                    (SeverityLevel.IMPORTANT if \
                        issue_data.get("severity") == "important" else \
                        SeverityLevel.SUGGESTED)

                issues.append(QualityIssue(
                    dimension=dimension,
                    description=issue_data.get("description", ""),
                    severity=severity,
                    suggestion=issue_data.get("suggestion")
                ))

            strengths = data.get("strengths", [])
            suggestions = []
            for issue in issues:
                if issue.suggestion:
                    suggestions.append(issue.suggestion)

            # 补充额外的分析建议
            analysis = data.get("analysis", "")
            if analysis:
                suggestions.append(f"分析: {analysis}")

            return DimensionScore(
                dimension=dimension,
                score=score,
                issues=issues,
                strengths=strengths,
                suggestions=suggestions
            )

        except json.JSONDecodeError:
            # 解析失败，返回默认评分
            return DimensionScore(
                dimension=dimension,
                score=5.0,
                issues=[],
                strengths=[],
                suggestions=["无法解析评估响应，请重试"]
            )

    def _calculate_overall_score(self,
                               dimension_scores: dict[QualityDimension, DimensionScore]) -> float:
        """计算加权总分"""
        total_weight = 0
        weighted_sum = 0

        for dimension, score in dimension_scores.items():
            weight = self.DIMENSION_WEIGHTS.get(dimension, 1.0)
            weighted_sum += score.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0

    def _extract_critical_issues(self,
                             dimension_scores: dict[QualityDimension, DimensionScore]) -> list[QualityIssue]:
        """提取所有严重和重要问题"""
        critical = []
        for score in dimension_scores.values():
            for issue in score.issues:
                if issue.severity in [SeverityLevel.CRITICAL, SeverityLevel.IMPORTANT]:
                    critical.append(issue)
        return critical

    def _determine_improvement_priority(self,
                                     dimension_scores: dict[QualityDimension, DimensionScore]) -> list[QualityDimension]:
        """确定改进优先级"""
        # 按得分升序排序（得分低的优先改进）
        sorted_dimensions = sorted(
            dimension_scores.items(),
            key=lambda x: (10 - x[1].score) * self.DIMENSION_WEIGHTS.get(x[0], 1.0)
        )
        return [dim for dim, _ in sorted_dimensions if dimension_scores[dim].score < 8.0]

    def _determine_quality_level(self, overall_score: float) -> str:
        """确定质量等级"""
        for level, (min_score, max_score) in self.QUALITY_LEVELS.items():
            if min_score <= overall_score <= max_score:
                return level
        return "差"

    @staticmethod
    def _load_prompts() -> dict[str, str]:
        """加载各维度的评估提示词"""
        return {
            QualityDimension.NOVELTY.value: """
你是一位经验丰富的专利审查员和专利代理人。请评估以下权利要求的新颖性。

评估要点：
1. 区别特征：权利要求是否包含与现有技术有明显区别的技术特征？
2. 具体性：这些区别特征是否具体且明确？
3. 技术贡献：这些特征是否构成技术上的进步？

评分标准（1-10分）：
- 9-10分：权利要求包含清楚的区别特征，技术贡献明显
- 7-8分：有区别特征，但技术贡献不够突出
- 5-6分：区别特征模糊或技术贡献不明确
- 1-4分：缺乏明显区别特征，难以区别于现有技术
            """,

            QualityDimension.CLARITY.value: """
你是一位专利审查员。请评估以下权利要求的清晰性。

评估要点：
1. 术语一致性：同一概念是否使用统一的术语表达？
2. 句子结构：句子是否完整，语法是否正确？
3. 引用关系：从属权利要求的引用是否清晰正确？
4. 易理解性：权利要求是否易于被技术人员理解？

评分标准（1-10分）：
- 9-10分：术语高度一致，结构完整，非常清晰
- 7-8分：基本清晰，有个别术语或表达问题
- 5-6分：存在多处术语混乱或句子结构问题
- 1-4分：术语混乱，结构混乱，难以理解
            """,

            QualityDimension.COMPLETENESS.value: """
你是一位专利代理人。请评估以下权利要求的完整性。

评估要点：
1. 核心特征：是否包含实现发明的所有核心技术特征？
2. 实施方式：是否描述了必要的实施细节？
3. 层级保护：是否有合理的从属权利要求层级？

评分标准（1-10分）：
- 9-10分：所有必要特征完整，层级结构合理
- 7-8分：核心特征齐全，但部分实施细节不够
- 5-6分：遗漏部分重要特征，层级结构不完整
- 1-4分：缺少核心技术特征，无法全面保护
            """,

            QualityDimension.SUPPORT.value: """
你是一位专利审查员。请评估权利要求是否得到说明书支持。

评估要点：
1. 依据公开：权利要求的特征是否在说明书中公开？
2. 实施可行性：从说明书能否推导出实施方式？
3. 一致性：权利要求与说明书术语是否一致？

评分标准（1-10分）：
- 9-10分：所有特征都有充分支持，完全一致
- 7-8分：大部分特征有支持，个别部分支持不足
- 5-6分：多处特征缺乏说明书支持
- 1-4分：大量特征无依据，无法实施
            """,

            QualityDimension.SCOPE_APPROPRIATENESS.value: """
你是一位资深专利代理人。请评估权利要求的保护范围是否恰当。

评估要点：
1. 宽窄平衡：保护范围是否既不过宽也不过窄？
2. 驳回风险：是否因范围过宽容易被驳回？
3. 保护力度：是否因范围过窄而限制保护力度？
4. 限定词使用："所述"、"包括"等限定词使用是否合理？

评分标准（1-10分）：
- 9-10分：保护范围宽窄得当，限定词使用合理
- 7-8分：范围基本恰当，有个别调整空间
- 5-6分：范围稍宽或稍窄，有调整必要
- 1-4分：范围严重不当，需大幅调整
            """,

            QualityDimension.LEGAL_COMPLIANCE.value: """
你是一位专利法务专家。请评估权利要求的法律规范性。

评估要点：
1. 单一性：是否满足专利法的单一性要求？
2. 格式规范：是否符合USPTO/EPO的格式要求？
3. 法律术语：是否使用标准的专利法术语？
4. 引用规范：权利要求引用是否符合法律规范？

评分标准（1-10分）：
- 9-10分：完全符合法律规范，格式正确
- 7-8分：基本符合规范，有小的格式问题
- 5-6分：存在单一性或格式问题
- 1-4分：多项法律规范问题，需重大修改
            """
        }
