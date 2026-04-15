#!/usr/bin/env python3
"""
专利合规性检查引擎
Patent Compliance Engine

基于知识图谱和规则的专利合规性智能分析系统
作者: 小诺·双鱼座
创建时间: 2025-12-21
版本: v1.0.0 "智能合规"
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..knowledge.patent_analysis.enhanced_knowledge_graph import (
    EnhancedPatentKnowledgeGraph,
    HybridSearchConfig,
    QueryType,
)

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """合规性状态"""

    COMPLIANT = "compliant"  # 合规
    NON_COMPLIANT = "non_compliant"  # 不合规
    UNCERTAIN = "uncertain"  # 不确定
    NEEDS_REVIEW = "needs_review"  # 需要审查


class RiskLevel(Enum):
    """风险等级"""

    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 严重风险


@dataclass
class ComplianceIssue:
    """合规性问题"""

    issue_id: str
    title: str
    description: str
    severity: RiskLevel
    category: str
    related_rules: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ComplianceAnalysis:
    """合规性分析结果"""

    patent_id: str
    patent_title: str
    overall_status: ComplianceStatus
    risk_level: RiskLevel
    issues: list[ComplianceIssue]
    confidence_score: float
    analysis_time: datetime
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceReport:
    """合规性报告"""

    analysis: ComplianceAnalysis
    executive_summary: str
    key_findings: list[str]
    next_steps: list[str]
    detailed_analysis: str


class PatentComplianceEngine:
    """专利合规性检查引擎"""

    def __init__(self, knowledge_graph: EnhancedPatentKnowledgeGraph | None = None):
        self.knowledge_graph = knowledge_graph
        self.name = "专利合规性检查引擎"
        self.version = "1.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 合规性规则库
        self.compliance_rules = self._init_compliance_rules()

        # 风险评估权重
        self.risk_weights = {
            "novelty": 0.3,  # 新颖性权重
            "inventiveness": 0.25,  # 创造性权重
            "industrial_applicability": 0.2,  # 实用性权重
            "formality": 0.15,  # 形式要求权重
            "disclosure": 0.1,  # 公开充分权重
        }

    async def initialize(self):
        """初始化合规性检查引擎"""
        try:
            # 如果没有提供知识图谱,创建一个
            if self.knowledge_graph is None:
                self.knowledge_graph = await EnhancedPatentKnowledgeGraph.initialize()

            # 验证知识图谱连接
            test_query = "专利法 第三条"
            test_results = await self.knowledge_graph.search_hybrid(
                test_query, QueryType.LEGAL_COMPLIANCE
            )

            if test_results:
                self._initialized = True
                self.logger.info("✅ PatentComplianceEngine 初始化完成")
                return True
            else:
                self.logger.error("❌ 知识图谱连接测试失败")
                return False

        except Exception as e:
            self.logger.error(f"❌ PatentComplianceEngine 初始化失败: {e}")
            return False

    def _init_compliance_rules(self) -> dict[str, dict[str, Any]]:
        """初始化合规性规则库"""
        return {
            "novelty": {
                "title": "新颖性检查",
                "description": "检查专利是否具有新颖性",
                "keywords": ["现有技术", "公开使用", "抵触申请", "新颖性"],
                "rules": [
                    "申请专利的发明创造不属于现有技术",
                    "申请专利的发明创造在申请日以前没有同样的发明在国内外出版物上公开发表过",
                    "申请专利的发明创造在申请日以前没有在国内公开使用过或者以其他方式为公众所知",
                ],
            },
            "inventiveness": {
                "title": "创造性检查",
                "description": "检查专利是否具有创造性",
                "keywords": ["创造性", "显著进步", "实质性特点", "显而易见"],
                "rules": [
                    "同申请日以前已有的技术相比,该发明有突出的实质性特点和显著的进步",
                    "该发明不属于显而易见的改进",
                ],
            },
            "industrial_applicability": {
                "title": "实用性检查",
                "description": "检查专利是否具有实用性",
                "keywords": ["实用性", "产业应用", "技术方案", "可实施"],
                "rules": ["该发明能够制造或者使用,并且能够产生积极效果", "具有产业上的可实施性"],
            },
            "formality": {
                "title": "形式要求检查",
                "description": "检查专利申请的形式要求",
                "keywords": ["说明书", "权利要求书", "摘要", "形式要求"],
                "rules": [
                    "说明书应当对发明作出清楚、完整的说明",
                    "权利要求书应当以说明书为依据",
                    "摘要应当简要说明发明的技术要点",
                ],
            },
            "disclosure": {
                "title": "公开充分性检查",
                "description": "检查专利公开是否充分",
                "keywords": ["公开充分", "技术方案", "实施方式", "具体实施方式"],
                "rules": [
                    "说明书应当公开充分,使所属技术领域的技术人员能够实现",
                    "应当包含具体的技术方案和实施方式",
                ],
            },
        }

    async def analyze_compliance(
        self, patent_data: dict[str, Any], analysis_config: dict[str, Any] | None = None
    ) -> ComplianceReport:
        """
        分析专利合规性

        Args:
            patent_data: 专利数据,包含title, description, claims, abstract等
            analysis_config: 分析配置

        Returns:
            ComplianceReport: 合规性分析报告
        """
        if not self._initialized:
            self.logger.error("❌ 合规性检查引擎未初始化")
            return self._create_empty_report(patent_data)

        start_time = datetime.now()

        try:
            patent_id = patent_data.get("id", "unknown")
            patent_title = patent_data.get("title", "未知专利")

            self.logger.info(f"🔍 开始分析专利合规性: {patent_title} ({patent_id})")

            # 1. 执行各项合规性检查
            compliance_scores = {}
            issues = []

            for category, rule_config in self.compliance_rules.items():
                try:
                    score, category_issues = await self._check_category_compliance(
                        patent_data, category, rule_config
                    )
                    compliance_scores[category] = score
                    issues.extend(category_issues)

                except Exception as e:
                    self.logger.error(f"❌ {category} 检查失败: {e}")
                    compliance_scores[category] = 0.0

            # 2. 计算总体合规性分数
            overall_score = self._calculate_overall_score(compliance_scores)

            # 3. 确定合规性状态和风险等级
            overall_status = self._determine_compliance_status(overall_score)
            risk_level = self._determine_risk_level(issues)

            # 4. 生成分析结果
            analysis = ComplianceAnalysis(
                patent_id=patent_id,
                patent_title=patent_title,
                overall_status=overall_status,
                risk_level=risk_level,
                issues=issues,
                confidence_score=overall_score,
                analysis_time=start_time,
                context={
                    "compliance_scores": compliance_scores,
                    "analysis_duration": (datetime.now() - start_time).total_seconds(),
                },
            )

            # 5. 生成报告
            report = await self._generate_compliance_report(analysis)

            self.logger.info(f"✅ 合规性分析完成: {patent_title} - {overall_status.value}")
            return report

        except Exception as e:
            self.logger.error(f"❌ 合规性分析失败: {e}")
            return self._create_error_report(patent_data, e)

    async def _check_category_compliance(
        self, patent_data: dict[str, Any], category: str, rule_config: dict[str, Any]
    ) -> tuple[float, list[ComplianceIssue]]:
        """
        检查特定类别的合规性

        Args:
            patent_data: 专利数据
            category: 检查类别
            rule_config: 规则配置

        Returns:
            tuple[float, list[ComplianceIssue]]: (合规性分数, 发现的问题列表)
        """
        issues = []
        base_score = 0.8  # 基础分数

        # 根据专利内容进行搜索
        search_content = f"{patent_data.get('title', '')} {patent_data.get('description', '')} {patent_data.get('claims', '')}"

        # 搜索相关的法规和案例
        search_results = await self.knowledge_graph.search_hybrid(
            query=search_content,
            query_type=QueryType.LEGAL_COMPLIANCE,
            config=HybridSearchConfig(top_k=20, re_rank_top_k=10),
        )

        # 分析搜索结果,识别潜在问题
        if search_results:
            for result in search_results:
                # 检查是否包含负面信息
                if self._contains_negative_indicators(result.content):
                    issue = ComplianceIssue(
                        issue_id=f"{category}_{result.node_id}",
                        title=f"{rule_config['title']} - 潜在问题",
                        description=f"在相关法规中发现可能的不合规因素: {result.title}",
                        severity=RiskLevel.MEDIUM,
                        category=category,
                        related_rules=[result.node_id],
                        recommendations=["建议重新审查相关条款", "咨询专利代理师"],
                    )
                    issues.append(issue)
                    base_score -= 0.2

        # 基于专利内容进行基本检查
        content_issues = self._check_content_compliance(patent_data, category, rule_config)
        issues.extend(content_issues)

        # 确保分数在0-1范围内
        final_score = max(0.0, min(1.0, base_score))

        return final_score, issues

    def _check_content_compliance(
        self, patent_data: dict[str, Any], category: str, rule_config: dict[str, Any]
    ) -> list[ComplianceIssue]:
        """检查专利内容的合规性"""
        issues = []

        patent_data.get("title", "")
        description = patent_data.get("description", "")
        claims = patent_data.get("claims", "")
        patent_data.get("abstract", "")

        # 根据类别进行特定检查
        if category == "novelty":
            # 检查是否包含可能表示缺乏新颖性的表述
            negative_phrases = ["现有技术", "已知的", "公知的", "常规技术"]
            for phrase in negative_phrases:
                if phrase in description.lower():
                    issues.append(
                        ComplianceIssue(
                            issue_id=f"{category}_negative_phrase_{phrase}",
                            title="新颖性 - 负面表述",
                            description=f"说明书中包含可能影响新颖性的表述: {phrase}",
                            severity=RiskLevel.MEDIUM,
                            category=category,
                            recommendations=["修改相关表述", "强调发明的创新点"],
                        )
                    )

        elif category == "disclosure":
            # 检查公开充分性
            if len(description) < 500:  # 说明太短
                issues.append(
                    ComplianceIssue(
                        issue_id=f"{category}_insufficient_disclosure",
                        title="公开充分性 - 描述过短",
                        description="说明书描述可能不够充分",
                        severity=RiskLevel.HIGH,
                        category=category,
                        recommendations=["扩展技术方案的详细描述", "增加具体实施方式"],
                    )
                )

        elif category == "formality":
            # 检查形式要求
            if not claims:
                issues.append(
                    ComplianceIssue(
                        issue_id=f"{category}_missing_claims",
                        title="形式要求 - 缺少权利要求",
                        description="专利申请缺少权利要求书",
                        severity=RiskLevel.CRITICAL,
                        category=category,
                        recommendations=["添加权利要求书", "确保符合格式要求"],
                    )
                )

        return issues

    def _contains_negative_indicators(self, content: str) -> bool:
        """检查内容是否包含负面指示器"""
        negative_indicators = [
            "不符合",
            "不符合条件",
            "不具备",
            "不能授予",
            "驳回",
            "无效",
            "驳回理由",
            "不具备专利性",
        ]
        return any(indicator in content for indicator in negative_indicators)

    def _calculate_overall_score(self, compliance_scores: dict[str, float]) -> float:
        """计算总体合规性分数"""
        total_score = 0.0
        total_weight = 0.0

        for category, score in compliance_scores.items():
            weight = self.risk_weights.get(category, 0.2)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _determine_compliance_status(self, score: float) -> ComplianceStatus:
        """确定合规性状态"""
        if score >= 0.8:
            return ComplianceStatus.COMPLIANT
        elif score >= 0.6:
            return ComplianceStatus.NEEDS_REVIEW
        elif score >= 0.4:
            return ComplianceStatus.UNCERTAIN
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _determine_risk_level(self, issues: list[ComplianceIssue]) -> RiskLevel:
        """确定风险等级"""
        if not issues:
            return RiskLevel.LOW

        # 统计各风险等级的问题数量
        critical_count = sum(1 for issue in issues if issue.severity == RiskLevel.CRITICAL)
        high_count = sum(1 for issue in issues if issue.severity == RiskLevel.HIGH)
        medium_count = sum(1 for issue in issues if issue.severity == RiskLevel.MEDIUM)

        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count > 0:
            return RiskLevel.HIGH
        elif medium_count > 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    async def _generate_compliance_report(self, analysis: ComplianceAnalysis) -> ComplianceReport:
        """生成合规性报告"""
        # 生成执行摘要
        executive_summary = self._generate_executive_summary(analysis)

        # 生成关键发现
        key_findings = self._generate_key_findings(analysis)

        # 生成后续步骤
        next_steps = self._generate_next_steps(analysis)

        # 生成详细分析
        detailed_analysis = self._generate_detailed_analysis(analysis)

        return ComplianceReport(
            analysis=analysis,
            executive_summary=executive_summary,
            key_findings=key_findings,
            next_steps=next_steps,
            detailed_analysis=detailed_analysis,
        )

    def _generate_executive_summary(self, analysis: ComplianceAnalysis) -> str:
        """生成执行摘要"""
        status_map = {
            ComplianceStatus.COMPLIANT: "符合专利法规要求",
            ComplianceStatus.NEEDS_REVIEW: "需要进一步审查",
            ComplianceStatus.UNCERTAIN: "合规性不确定",
            ComplianceStatus.NON_COMPLIANT: "不符合专利法规要求",
        }

        risk_map = {
            RiskLevel.LOW: "低风险",
            RiskLevel.MEDIUM: "中等风险",
            RiskLevel.HIGH: "高风险",
            RiskLevel.CRITICAL: "严重风险",
        }

        return f"""
专利 "{analysis.patent_title}" 的合规性分析已完成。

总体评估: {status_map[analysis.overall_status]}
风险等级: {risk_map[analysis.risk_level]}
置信度: {analysis.confidence_score:.2%}
发现的问题数: {len(analysis.issues)}

建议: 基于当前分析结果,{"建议积极完善专利申请材料" if analysis.overall_status != ComplianceStatus.COMPLIANT else "专利申请材料基本符合要求"}。
        """

    def _generate_key_findings(self, analysis: ComplianceAnalysis) -> list[str]:
        """生成关键发现"""
        findings = []

        if analysis.issues:
            # 按严重程度分组统计问题
            critical_issues = [
                issue for issue in analysis.issues if issue.severity == RiskLevel.CRITICAL
            ]
            high_issues = [issue for issue in analysis.issues if issue.severity == RiskLevel.HIGH]

            if critical_issues:
                findings.append(f"发现 {len(critical_issues)} 个严重合规性问题")

            if high_issues:
                findings.append(f"发现 {len(high_issues)} 个高风险合规性问题")

            # 按类别统计问题
            category_counts = {}
            for issue in analysis.issues:
                category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

            for category, count in category_counts.items():
                rule_config = self.compliance_rules.get(category, {})
                findings.append(f"{rule_config.get('title', category)}: {count} 个问题")

        else:
            findings.append("未发现重大合规性问题")

        return findings

    def _generate_next_steps(self, analysis: ComplianceAnalysis) -> list[str]:
        """生成后续步骤"""
        steps = []

        if analysis.issues:
            critical_count = sum(
                1 for issue in analysis.issues if issue.severity == RiskLevel.CRITICAL
            )
            sum(1 for issue in analysis.issues if issue.severity == RiskLevel.HIGH)

            if critical_count > 0:
                steps.append("立即解决严重合规性问题")
                steps.append("考虑重新撰写相关部分")
            else:
                steps.append("完善专利申请材料")
                steps.append("进行必要的修改和补充")

            steps.append("建议咨询专利代理师")
        else:
            steps.append("准备提交专利申请")
            steps.append("继续完善申请材料")

        return steps

    def _generate_detailed_analysis(self, analysis: ComplianceAnalysis) -> str:
        """生成详细分析"""
        analysis_text = f"""
# 专利合规性详细分析报告

## 基本信息
- 专利ID: {analysis.patent_id}
- 专利标题: {analysis.patent_title}
- 分析时间: {analysis.analysis_time.strftime('%Y-%m-%d %H:%M:%S')}
- 总体状态: {analysis.overall_status.value}
- 风险等级: {analysis.risk_level.value}
- 置信度: {analysis.confidence_score:.2%}

## 合规性分数详情
"""

        # 添加各合规性类别的详细分数
        if "compliance_scores" in analysis.context:
            for category, score in analysis.context["compliance_scores"].items():
                rule_config = self.compliance_rules.get(category, {})
                analysis_text += f"\n- {rule_config.get('title', category)}: {score:.2%}"

        # 添加问题详情
        if analysis.issues:
            analysis_text += "\n\n## 发现的问题\n"
            for i, issue in enumerate(analysis.issues, 1):
                analysis_text += f"""
### 问题 {i}: {issue.title}
- 描述: {issue.description}
- 严重程度: {issue.severity.value}
- 相关规则: {', '.join(issue.related_rules)}
- 建议: {', '.join(issue.recommendations)}
"""
        else:
            analysis_text += "\n\n## 未发现问题\n本次分析未发现重大合规性问题。"

        return analysis_text

    def _create_empty_report(self, patent_data: dict[str, Any]) -> ComplianceReport:
        """创建空报告"""
        empty_analysis = ComplianceAnalysis(
            patent_id=patent_data.get("id", "unknown"),
            patent_title=patent_data.get("title", "未知专利"),
            overall_status=ComplianceStatus.UNCERTAIN,
            risk_level=RiskLevel.MEDIUM,
            issues=[],
            confidence_score=0.0,
            analysis_time=datetime.now(),
        )

        return ComplianceReport(
            analysis=empty_analysis,
            executive_summary="无法完成合规性分析",
            key_findings=["引擎未初始化或数据不足"],
            next_steps=["请检查系统状态和输入数据"],
            detailed_analysis="详细分析不可用",
        )

    def _create_error_report(
        self, patent_data: dict[str, Any], error: Exception
    ) -> ComplianceReport:
        """创建错误报告"""
        error_analysis = ComplianceAnalysis(
            patent_id=patent_data.get("id", "unknown"),
            patent_title=patent_data.get("title", "未知专利"),
            overall_status=ComplianceStatus.UNCERTAIN,
            risk_level=RiskLevel.HIGH,
            issues=[
                ComplianceIssue(
                    issue_id="system_error",
                    title="系统错误",
                    description=f"分析过程中发生错误: {error!s}",
                    severity=RiskLevel.HIGH,
                    category="system",
                    recommendations=["检查系统配置", "联系技术支持"],
                )
            ],
            confidence_score=0.0,
            analysis_time=datetime.now(),
        )

        return ComplianceReport(
            analysis=error_analysis,
            executive_summary="合规性分析失败",
            key_findings=[f"系统错误: {error!s}"],
            next_steps=["检查错误日志", "重新运行分析"],
            detailed_analysis=f"分析过程遇到错误: {error!s}",
        )

    async def close(self):
        """关闭合规性检查引擎"""
        if self.knowledge_graph:
            await self.knowledge_graph.cleanup()

        self._initialized = False
        self.logger.info("✅ PatentComplianceEngine 已关闭")


# 便捷函数
async def create_compliance_engine(
    knowledge_graph: EnhancedPatentKnowledgeGraph | None = None,
) -> PatentComplianceEngine:
    """创建合规性检查引擎实例"""
    engine = PatentComplianceEngine(knowledge_graph)
    await engine.initialize()
    return engine


async def quick_compliance_check(patent_data: dict[str, Any]) -> ComplianceReport:
    """快速合规性检查"""
    engine = await create_compliance_engine()
    return await engine.analyze_compliance(patent_data)
