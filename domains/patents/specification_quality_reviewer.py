#!/usr/bin/env python3
from __future__ import annotations

"""
说明书质量审查器 (Specification Quality Reviewer)

在专利申请提交前进行自我审查，模拟审查员视角发现问题。

功能：
- 基于专利法条款（A22.2/A22.3/A26.3/A26.4/A33）进行审查
- 输出P0/P1/P2优先级问题清单
- 计算授权概率估算
- 生成修改建议

参考：
- OpenClaw patent-drafting skill Phase 6
- 与examiner_simulator.py的区别：
  - examiner_simulator.py: OA答复阶段，模拟审查员反驳
  - 本模块: 撰写阶段，提交前自我质量检查
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RejectionRisk(Enum):
    """驳回风险等级"""

    HIGH = "high"  # 高风险
    MEDIUM = "medium"  # 中风险
    LOW = "low"  # 低风险


class IssuePriority(Enum):
    """问题优先级"""

    P0 = "P0"  # 阻断性，必须修改
    P1 = "P1"  # 重要，建议修改
    P2 = "P2"  # 可选优化


class RejectionType(Enum):
    """驳回类型"""

    NOVELTY = "novelty"  # A22.2 新颖性
    INVENTIVE_STEP = "inventive_step"  # A22.3 创造性
    INSUFFICIENT_DISCLOSURE = "insufficient"  # A26.3 公开不充分
    UNCLEAR_CLAIMS = "unclear_claims"  # A26.4 权利要求不清楚
    SUPPORT_ISSUE = "support_issue"  # A26.4 权利要求不支持
    BEYOND_SCOPE = "beyond_scope"  # A33 修改超范围
    FORMALITY = "formality"  # 形式缺陷


@dataclass
class ReviewIssue:
    """审查问题"""

    issue_id: str
    priority: IssuePriority
    rejection_type: RejectionType
    risk_level: RejectionRisk
    location: str
    description: str
    legal_basis: str
    suggestion: str
    related_claims: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "issue_id": self.issue_id,
            "priority": self.priority.value,
            "rejection_type": self.rejection_type.value,
            "risk_level": self.risk_level.value,
            "location": self.location,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "suggestion": self.suggestion,
            "related_claims": self.related_claims,
        }


@dataclass
class QualityReviewReport:
    """质量审查报告"""

    case_id: str
    review_date: str
    overall_risk: RejectionRisk
    issues: list[ReviewIssue]
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    authorization_probability: float = 0.0
    summary: str = ""

    def __post_init__(self):
        self.p0_count = sum(1 for i in self.issues if i.priority == IssuePriority.P0)
        self.p1_count = sum(1 for i in self.issues if i.priority == IssuePriority.P1)
        self.p2_count = sum(1 for i in self.issues if i.priority == IssuePriority.P2)
        self._calculate_authorization_probability()

    def _calculate_authorization_probability(self):
        base_prob = 0.9
        base_prob -= self.p0_count * 0.30
        base_prob -= self.p1_count * 0.10
        base_prob -= self.p2_count * 0.05
        self.authorization_probability = max(0.0, min(1.0, base_prob))

        if self.authorization_probability >= 0.7:
            self.overall_risk = RejectionRisk.LOW
        elif self.authorization_probability >= 0.4:
            self.overall_risk = RejectionRisk.MEDIUM
        else:
            self.overall_risk = RejectionRisk.HIGH

    def to_markdown(self) -> str:
        risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        priority_emoji = {"P0": "🔴", "P1": "🟡", "P2": "🟢"}

        md = f"""# 说明书质量审查报告

> **案件ID**: {self.case_id}
> **审查日期**: {self.review_date}
> **整体风险**: {risk_emoji.get(self.overall_risk.value, '⚪')} {self.overall_risk.value.upper()}
> **授权概率**: {self.authorization_probability:.1%}

---

## 📊 问题统计

| 优先级 | 数量 | 说明 |
|:------:|:----:|------|
| 🔴 P0 | {self.p0_count} | 阻断性问题，必须修改 |
| 🟡 P1 | {self.p1_count} | 重要问题，建议修改 |
| 🟢 P2 | {self.p2_count} | 可选优化 |

---

## 📋 问题清单

"""
        sorted_issues = sorted(self.issues, key=lambda x: x.priority.value)

        for issue in sorted_issues:
            emoji = priority_emoji.get(issue.priority.value, "⚪")
            md += f"""### {emoji} {issue.issue_id}: {issue.description}

- **优先级**: {issue.priority.value}
- **驳回类型**: {issue.rejection_type.value}
- **风险等级**: {risk_emoji.get(issue.risk_level.value, '⚪')} {issue.risk_level.value}
- **问题位置**: {issue.location}
- **法律依据**: {issue.legal_basis}
- **修改建议**: {issue.suggestion}

---

"""

        md += f"""## 📝 审查摘要

{self.summary}

---

*报告生成时间: {self.review_date}*
*审查器版本: v1.0*
"""
        return md


class SpecificationQualityReviewer:
    """
    说明书质量审查器

    在提交前对专利申请文件进行全面质量检查。
    """

    def __init__(self, llm_manager=None):
        self.llm_manager = llm_manager
        self.issue_counter = 0

    def review(
        self, specification: dict, claims: dict, prior_art: list[dict] | None = None
    ) -> QualityReviewReport:
        """
        执行质量审查

        Args:
            specification: 说明书内容
            claims: 权利要求书
            prior_art: 对比文件列表

        Returns:
            QualityReviewReport: 审查报告
        """
        issues = []
        self.issue_counter = 0

        # 1. 检查权利要求清晰性 (A26.4)
        issues.extend(self._check_claim_clarity(claims))

        # 2. 检查说明书充分性 (A26.3)
        issues.extend(self._check_disclosure_sufficiency(specification))

        # 3. 检查权利要求支持性 (A26.4)
        issues.extend(self._check_claim_support(specification, claims))

        # 4. 检查新颖性/创造性风险
        if prior_art:
            issues.extend(self._check_novelty_inventive_step(claims, prior_art))

        # 5. 检查形式问题
        issues.extend(self._check_formality_issues(specification, claims))

        summary = self._generate_summary(issues)

        return QualityReviewReport(
            case_id=specification.get("case_id", "UNKNOWN"),
            review_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            overall_risk=RejectionRisk.LOW,
            issues=issues,
            summary=summary,
        )

    def _check_claim_clarity(self, claims: dict) -> list[ReviewIssue]:
        """检查权利要求清晰性"""
        issues = []
        unclear_patterns = ["等", "之类", "约", "大约", "左右", "例如"]

        for claim in claims.get("claims", []):
            claim_text = claim.get("content", "")
            claim_num = claim.get("claim_number", 0)

            for pattern in unclear_patterns:
                if pattern in claim_text:
                    self.issue_counter += 1
                    issues.append(
                        ReviewIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            priority=IssuePriority.P1,
                            rejection_type=RejectionType.UNCLEAR_CLAIMS,
                            risk_level=RejectionRisk.MEDIUM,
                            location=f"权利要求{claim_num}",
                            description=f"包含不确定表述「{pattern}」",
                            legal_basis="专利法第26条第4款",
                            suggestion=f"将「{pattern}」替换为具体技术特征或数值范围",
                            related_claims=[claim_num],
                        )
                    )

        return issues

    def _check_disclosure_sufficiency(self, specification: dict) -> list[ReviewIssue]:
        """检查说明书公开充分性"""
        issues = []

        # 检查具体实施方式长度
        detailed_desc = specification.get("detailed_description", {})
        content = (
            detailed_desc.get("content", "")
            if isinstance(detailed_desc, dict)
            else str(detailed_desc)
        )

        if len(content) < 500:
            self.issue_counter += 1
            issues.append(
                ReviewIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    priority=IssuePriority.P0,
                    rejection_type=RejectionType.INSUFFICIENT_DISCLOSURE,
                    risk_level=RejectionRisk.HIGH,
                    location="具体实施方式",
                    description="具体实施方式内容过短，可能导致公开不充分",
                    legal_basis="专利法第26条第3款",
                    suggestion="扩充具体实施方式，增加至少一个完整实施例",
                )
            )

        # 检查是否有效果描述
        invention_content = specification.get("invention_content", {})
        inv_text = (
            invention_content.get("content", "")
            if isinstance(invention_content, dict)
            else str(invention_content)
        )

        if "有益效果" not in inv_text and "技术效果" not in inv_text:
            self.issue_counter += 1
            issues.append(
                ReviewIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    priority=IssuePriority.P1,
                    rejection_type=RejectionType.INSUFFICIENT_DISCLOSURE,
                    risk_level=RejectionRisk.MEDIUM,
                    location="发明内容",
                    description="缺少有益效果/技术效果描述",
                    legal_basis="专利法第26条第3款",
                    suggestion="在发明内容中明确描述技术方案带来的有益效果",
                )
            )

        return issues

    def _check_claim_support(self, specification: dict, claims: dict) -> list[ReviewIssue]:
        """检查权利要求是否得到说明书支持"""
        issues = []

        spec_content = ""
        for key in ["detailed_description", "invention_content", "background_art"]:
            section = specification.get(key, {})
            if isinstance(section, dict):
                spec_content += section.get("content", "")
            else:
                spec_content += str(section)

        for claim in claims.get("claims", []):
            if claim.get("claim_type") == "independent" or claim.get("claim_number", 0) == 1:
                claim_text = claim.get("content", "")
                claim_num = claim.get("claim_number", 0)

                # 提取关键词检查
                keywords = self._extract_keywords(claim_text)
                missing = [kw for kw in keywords[:5] if kw and kw not in spec_content]

                if len(missing) >= 2:
                    self.issue_counter += 1
                    issues.append(
                        ReviewIssue(
                            issue_id=f"ISSUE-{self.issue_counter:03d}",
                            priority=IssuePriority.P1,
                            rejection_type=RejectionType.SUPPORT_ISSUE,
                            risk_level=RejectionRisk.MEDIUM,
                            location=f"权利要求{claim_num}",
                            description=f"技术特征「{', '.join(missing[:3])}」未在说明书中充分描述",
                            legal_basis="专利法第26条第4款",
                            suggestion="在具体实施方式中补充相关技术特征的详细描述",
                            related_claims=[claim_num],
                        )
                    )

        return issues

    def _check_novelty_inventive_step(
        self, claims: dict, prior_art: list[dict]
    ) -> list[ReviewIssue]:
        """检查新颖性和创造性风险"""
        issues = []

        for claim in claims.get("claims", []):
            if claim.get("claim_type") == "independent" or claim.get("claim_number", 0) == 1:
                claim_text = claim.get("content", "")
                claim_num = claim.get("claim_number", 0)

                for art in prior_art:
                    similarity = self._calculate_similarity(claim_text, art.get("abstract", ""))

                    if similarity > 0.8:
                        self.issue_counter += 1
                        issues.append(
                            ReviewIssue(
                                issue_id=f"ISSUE-{self.issue_counter:03d}",
                                priority=IssuePriority.P0,
                                rejection_type=RejectionType.NOVELTY,
                                risk_level=RejectionRisk.HIGH,
                                location=f"权利要求{claim_num}",
                                description=(
                                    f"与{art.get('document_number', 'D?')}"
                                    "高度相似，存在新颖性问题"
                                ),
                                legal_basis="专利法第22条第2款",
                                suggestion="增加区别技术特征，突出与现有技术的差异",
                                related_claims=[claim_num],
                            )
                        )
                    elif similarity > 0.6:
                        self.issue_counter += 1
                        issues.append(
                            ReviewIssue(
                                issue_id=f"ISSUE-{self.issue_counter:03d}",
                                priority=IssuePriority.P1,
                                rejection_type=RejectionType.INVENTIVE_STEP,
                                risk_level=RejectionRisk.MEDIUM,
                                location=f"权利要求{claim_num}",
                                description=f"与{art.get('document_number', 'D?')}相似度较高，存在创造性风险",
                                legal_basis="专利法第22条第3款",
                                suggestion="增加具有创造性的技术特征或补充技术效果说明",
                                related_claims=[claim_num],
                            )
                        )

        return issues

    def _check_formality_issues(self, specification: dict, claims: dict) -> list[ReviewIssue]:
        """检查形式问题"""
        issues = []

        # 检查发明名称长度
        title = specification.get("invention_title", "")
        if len(title) > 25:
            self.issue_counter += 1
            issues.append(
                ReviewIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    priority=IssuePriority.P2,
                    rejection_type=RejectionType.FORMALITY,
                    risk_level=RejectionRisk.LOW,
                    location="发明名称",
                    description=f"发明名称超过25个字（当前{len(title)}字）",
                    legal_basis="专利法实施细则",
                    suggestion="缩短发明名称，保持在25字以内",
                )
            )

        # 检查权利要求数量
        claims_list = claims.get("claims", [])
        if len(claims_list) > 10:
            self.issue_counter += 1
            issues.append(
                ReviewIssue(
                    issue_id=f"ISSUE-{self.issue_counter:03d}",
                    priority=IssuePriority.P2,
                    rejection_type=RejectionType.FORMALITY,
                    risk_level=RejectionRisk.LOW,
                    location="权利要求书",
                    description=f"权利要求数量较多（{len(claims_list)}项），可能增加审查费用",
                    legal_basis="费用相关规定",
                    suggestion="考虑合并部分从属权利要求",
                )
            )

        return issues

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        import re

        keywords = re.findall(r"[一种][\u4e00-\u9fa5]{2,10}[装置方法系统器组件模块]", text)
        return list(set(keywords))

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1)
        words2 = set(text2)
        if not words1 or not words2:
            return 0.0
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0

    def _generate_summary(self, issues: list[ReviewIssue]) -> str:
        """生成审查摘要"""
        if not issues:
            return "本次审查未发现明显问题，申请文件质量良好，建议提交。"

        p0 = [i for i in issues if i.priority == IssuePriority.P0]
        p1 = [i for i in issues if i.priority == IssuePriority.P1]

        parts = []
        if p0:
            parts.append(f"发现{len(p0)}个阻断性问题（P0），必须修改后才能提交。")
        if p1:
            parts.append(f"发现{len(p1)}个重要问题（P1），强烈建议修改以提高授权概率。")
        parts.append("建议按优先级顺序处理问题清单中的各项问题。")

        return " ".join(parts)


# 便捷函数
def review_specification(
    specification: dict, claims: dict, prior_art: list[dict] | None = None
) -> QualityReviewReport:
    """
    审查说明书质量的便捷函数

    Args:
        specification: 说明书
        claims: 权利要求书
        prior_art: 对比文件

    Returns:
        QualityReviewReport: 审查报告
    """
    reviewer = SpecificationQualityReviewer()
    return reviewer.review(specification, claims, prior_art)


# 测试
if __name__ == "__main__":
    spec = {
        "case_id": "TEST-001",
        "invention_title": "一种智能图像识别装置及方法",
        "detailed_description": {
            "content": "本实施例提供了一种智能图像识别装置..." * 50
        },
        "invention_content": {
            "content": "本发明提供了一种图像识别方法，有益效果包括识别准确率高等。"
        },
    }

    claims = {
        "claims": [
            {
                "claim_number": 1,
                "claim_type": "independent",
                "content": "一种图像识别装置，包括处理器等组件。",
            },
            {
                "claim_number": 2,
                "claim_type": "dependent",
                "content": "根据权利要求1所述的装置，处理器为GPU。",
            },
        ]
    }

    report = review_specification(spec, claims)
    print(report.to_markdown())
