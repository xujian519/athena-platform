#!/usr/bin/env python3
"""
专利诉讼支持主控制器

整合所有诉讼支持模块，提供完整的诉讼支持功能。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from .litigation_strategy_analyzer import (
        LitigationStrategyAnalyzer,
        LitigationType,
        LitigationRole,
        CaseAnalysis
    )
    from .evidence_organizer import (
        EvidenceOrganizer,
        EvidenceOrganizationResult
    )
    from .pleading_generator import (
        PleadingGenerator,
        PleadingType,
        PleadingResult
    )
    from .trial_assistant import (
        TrialAssistant,
        TrialPreparationGuide
    )
except ImportError:
    from core.patent.litigation.litigation_strategy_analyzer import (
        LitigationStrategyAnalyzer,
        LitigationType,
        LitigationRole,
        CaseAnalysis
    )
    from core.patent.litigation.evidence_organizer import (
        EvidenceOrganizer,
        EvidenceOrganizationResult
    )
    from core.patent.litigation.pleading_generator import (
        PleadingGenerator,
        PleadingType,
        PleadingResult
    )
    from core.patent.litigation.trial_assistant import (
        TrialAssistant,
        TrialPreparationGuide
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LitigationSupportOptions:
    """诉讼支持选项"""
    include_strategy_analysis: bool = True
    include_evidence_organization: bool = True
    include_pleading_generation: bool = True
    include_trial_preparation: bool = True
    auto_generate_documents: bool = True


@dataclass
class LitigationSupportResult:
    """诉讼支持结果"""
    patent_id: str
    case_number: str
    litigation_type: str
    strategy_analysis: Optional[CaseAnalysis] = None
    evidence_organization: Optional[EvidenceOrganizationResult] = None
    pleading_result: Optional[PleadingResult] = None
    trial_preparation: Optional[TrialPreparationGuide] = None
    summary: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "case_number": self.case_number,
            "litigation_type": self.litigation_type,
            "strategy_analysis": self.strategy_analysis.to_dict() if self.strategy_analysis else None,
            "evidence_organization": self.evidence_organization.to_dict() if self.evidence_organization else None,
            "pleading_result": self.pleading_result.to_dict() if self.pleading_result else None,
            "trial_preparation": self.trial_preparation.to_dict() if self.trial_preparation else None,
            "summary": self.summary,
            "metadata": self.metadata
        }


class LitigationSupporter:
    """专利诉讼支持主控制器"""

    def __init__(self):
        """初始化控制器"""
        self.strategy_analyzer = LitigationStrategyAnalyzer()
        self.evidence_organizer = EvidenceOrganizer()
        self.pleading_generator = PleadingGenerator()
        self.trial_assistant = TrialAssistant()
        logger.info("✅ 专利诉讼支持主控制器初始化成功")

    async def support_litigation(
        self,
        patent_id: str,
        case_number: str,
        litigation_type: LitigationType,
        litigation_role: LitigationRole,
        case_info: Dict[str, Any],
        evidences: Optional[List[Dict[str, Any]]] = None,
        pleading_arguments: Optional[List[Dict[str, Any]]] = None,
        options: Optional[LitigationSupportOptions] = None
    ) -> LitigationSupportResult:
        """
        提供完整的诉讼支持

        Args:
            patent_id: 专利号
            case_number: 案号
            litigation_type: 诉讼类型
            litigation_role: 诉讼角色
            case_info: 案件信息
            evidences: 证据列表（可选）
            pleading_arguments: 代理词论点（可选）
            options: 支持选项

        Returns:
            LitigationSupportResult对象
        """
        logger.info(f"⚖️ 开始提供诉讼支持: {case_number}")

        if options is None:
            options = LitigationSupportOptions()

        result = LitigationSupportResult(
            patent_id=patent_id,
            case_number=case_number,
            litigation_type=litigation_type.value
        )

        # 步骤1: 诉讼策略分析
        if options.include_strategy_analysis:
            logger.info("📊 步骤1: 诉讼策略分析")
            result.strategy_analysis = self.strategy_analyzer.analyze_case(
                patent_id,
                litigation_type,
                litigation_role,
                case_info,
                case_info.get("patent_info")
            )

        # 步骤2: 证据整理
        if options.include_evidence_organization and evidences:
            logger.info("📁 步骤2: 证据整理")
            result.evidence_organization = self.evidence_organizer.organize_evidences(
                patent_id,
                litigation_type.value,
                evidences
            )

        # 步骤3: 代理词生成
        if options.include_pleading_generation and pleading_arguments:
            logger.info("✍️ 步骤3: 代理词生成")
            pleading_type = (
                PleadingType.PLAINTIFF_STATEMENT
                if litigation_role == LitigationRole.PLAINTIFF
                else PleadingType.DEFENDANT_ANSWER
            )
            result.pleading_result = self.pleading_generator.generate_pleading(
                pleading_type,
                case_info,
                pleading_arguments
            )

        # 步骤4: 庭审准备
        if options.include_trial_preparation:
            logger.info("⚖️ 步骤4: 庭审准备")
            # 使用案件分析结果
            case_analysis = result.strategy_analysis.to_dict() if result.strategy_analysis else None
            result.trial_preparation = self.trial_assistant.prepare_trial(
                case_info,
                evidences or [],
                case_analysis
            )

        # 步骤5: 生成总结
        result.summary = self._generate_summary(result)

        # 步骤6: 添加元数据
        result.metadata = {
            "support_date": datetime.now().strftime("%Y-%m-%d"),
            "modules_completed": self._count_completed_modules(result),
            "litigation_role": litigation_role.value
        }

        logger.info("✅ 诉讼支持完成!")
        return result

    def _generate_summary(self, result: LitigationSupportResult) -> Dict[str, Any]:
        """生成总结"""
        summary = {
            "case_strength": None,
            "win_probability": None,
            "risk_level": None,
            "evidence_count": 0,
            "key_strengths": [],
            "key_weaknesses": [],
            "recommended_strategy": ""
        }

        # 从策略分析中提取
        if result.strategy_analysis:
            summary["case_strength"] = result.strategy_analysis.case_strength
            summary["win_probability"] = result.strategy_analysis.win_probability
            summary["risk_level"] = result.strategy_analysis.risk_level.value
            summary["key_strengths"] = result.strategy_analysis.strengths[:3]
            summary["key_weaknesses"] = result.strategy_analysis.weaknesses[:3]
            summary["recommended_strategy"] = result.strategy_analysis.recommended_strategy

        # 从证据整理中提取
        if result.evidence_organization:
            summary["evidence_count"] = len(result.evidence_organization.evidences)

        return summary

    def _count_completed_modules(self, result: LitigationSupportResult) -> int:
        """统计完成的模块数"""
        count = 0
        if result.strategy_analysis:
            count += 1
        if result.evidence_organization:
            count += 1
        if result.pleading_result:
            count += 1
        if result.trial_preparation:
            count += 1
        return count

    def save_to_files(
        self,
        result: LitigationSupportResult,
        output_dir: str
    ) -> List[str]:
        """
        保存结果到文件

        Args:
            result: 诉讼支持结果
            output_dir: 输出目录

        Returns:
            保存的文件路径列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = []

        # 保存策略分析
        if result.strategy_analysis:
            strategy_file = output_path / "01_诉讼策略分析.md"
            with open(strategy_file, 'w', encoding='utf-8') as f:
                f.write(self._format_strategy_analysis(result.strategy_analysis))
            saved_files.append(str(strategy_file))

        # 保存证据整理
        if result.evidence_organization:
            evidence_file = output_path / "02_证据整理清单.md"
            with open(evidence_file, 'w', encoding='utf-8') as f:
                f.write(self._format_evidence_organization(result.evidence_organization))
            saved_files.append(str(evidence_file))

        # 保存代理词
        if result.pleading_result:
            pleading_file = output_path / "03_代理词.md"
            with open(pleading_file, 'w', encoding='utf-8') as f:
                f.write(result.pleading_result.pleading_text)
            saved_files.append(str(pleading_file))

        # 保存庭审准备
        if result.trial_preparation:
            trial_file = output_path / "04_庭审准备指南.md"
            with open(trial_file, 'w', encoding='utf-8') as f:
                f.write(self._format_trial_preparation(result.trial_preparation))
            saved_files.append(str(trial_file))

        # 保存总结合
        summary_file = output_path / "00_总结合.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._format_summary(result))
        saved_files.append(str(summary_file))

        return saved_files

    def _format_strategy_analysis(self, analysis: CaseAnalysis) -> str:
        """格式化策略分析"""
        sections = []
        sections.append("# 诉讼策略分析\n")
        sections.append(f"**专利号**: {analysis.litigation_type}\n")
        sections.append(f"**诉讼类型**: {analysis.litigation_type.value}\n")
        sections.append(f"**诉讼角色**: {analysis.litigation_role.value}\n")
        sections.append(f"**案件强度**: {analysis.case_strength:.2f}\n")
        sections.append(f"**胜诉概率**: {analysis.win_probability:.1%}\n")
        sections.append(f"**风险等级**: {analysis.risk_level.value}\n")
        sections.append(f"**预计持续时间**: {analysis.estimated_duration}\n")
        sections.append(f"**预计费用**: {analysis.estimated_cost_range[0]:.0f}-{analysis.estimated_cost_range[1]:.0f}万元\n\n")

        sections.append("## 关键争议点\n")
        for issue in analysis.key_issues:
            sections.append(f"- {issue}\n")

        sections.append("\n## 己方优势\n")
        for strength in analysis.strengths:
            sections.append(f"- {strength}\n")

        sections.append("\n## 己方劣势\n")
        for weakness in analysis.weaknesses:
            sections.append(f"- {weakness}\n")

        sections.append("\n## 推荐策略\n")
        sections.append(f"{analysis.recommended_strategy}\n")

        return "\n".join(sections)

    def _format_evidence_organization(self, org: EvidenceOrganizationResult) -> str:
        """格式化证据整理"""
        sections = []
        sections.append("# 证据整理清单\n")
        sections.append(f"**专利号**: {org.patent_id}\n")
        sections.append(f"**证据总数**: {org.metadata['total_evidences']}\n")
        sections.append(f"**证据链数**: {org.metadata['total_chains']}\n\n")

        sections.append("## 证据分类\n")
        for category, evi_ids in org.category_summary.items():
            sections.append(f"### {category}\n")
            for evi_id in evi_ids:
                evi = next(e for e in org.evidences if e.id == evi_id)
                sections.append(f"- {evi_id}: {evi.name} ({evi.reliability.value})\n")
            sections.append("\n")

        sections.append("## 证据链\n")
        for chain in org.evidence_chains:
            sections.append(f"### {chain.title}\n")
            sections.append(f"强度: {chain.strength:.2f}\n")
            sections.append(f"逻辑: {chain.logical_flow}\n\n")

        sections.append("## 建议\n")
        for rec in org.recommendations:
            sections.append(f"- {rec}\n")

        return "\n".join(sections)

    def _format_trial_preparation(self, guide: TrialPreparationGuide) -> str:
        """格式化庭审准备"""
        sections = []
        sections.append("# 庭审准备指南\n")

        sections.append("## 庭审策略\n")
        strategy = guide.trial_strategy
        sections.append(f"**总体策略**: {strategy.overall_strategy}\n\n")
        sections.append(f"**关键胜诉点**:\n")
        for point in strategy.key_winning_points:
            sections.append(f"- {point}\n")
        sections.append(f"\n**风险点**:\n")
        for point in strategy.risk_points:
            sections.append(f"- {point}\n")
        sections.append(f"\n**和解建议**: {strategy.settlement_recommendation}\n\n")

        sections.append("## 庭审要点\n")
        for point in guide.trial_points:
            sections.append(f"### [{point.phase.value}] {point.point_type}\n")
            sections.append(f"{point.content}\n")
            sections.append(f"优先级: {point.priority}\n")
            sections.append(f"准备: {point.preparation}\n\n")

        sections.append("## 质证提纲\n")
        for outline in guide.examination_outlines[:5]:
            sections.append(f"### {outline.evidence_name}\n")
            for q in outline.questions[:3]:
                sections.append(f"- {q}\n")
            sections.append("\n")

        sections.append("## 检查清单\n")
        for category, items in guide.checklists.items():
            sections.append(f"### {category}\n")
            for item in items:
                sections.append(f"{item}\n")
            sections.append("\n")

        return "\n".join(sections)

    def _format_summary(self, result: LitigationSupportResult) -> str:
        """格式化总结"""
        sections = []
        sections.append("# 诉讼支持总结\n")
        sections.append(f"**案号**: {result.case_number}\n")
        sections.append(f"**专利号**: {result.patent_id}\n")
        sections.append(f"**诉讼类型**: {result.litigation_type}\n")
        sections.append(f"**支持日期**: {result.metadata['support_date']}\n")
        sections.append(f"**完成模块**: {result.metadata['modules_completed']}/4\n\n")

        summary = result.summary
        if summary["win_probability"]:
            sections.append(f"**胜诉概率**: {summary['win_probability']:.1%}\n")
        if summary["risk_level"]:
            sections.append(f"**风险等级**: {summary['risk_level']}\n")
        if summary["evidence_count"]:
            sections.append(f"**证据数量**: {summary['evidence_count']}\n")

        sections.append("\n## 关键优势\n")
        for strength in summary["key_strengths"]:
            sections.append(f"- {strength}\n")

        sections.append("\n## 关键劣势\n")
        for weakness in summary["key_weaknesses"]:
            sections.append(f"- {weakness}\n")

        if summary["recommended_strategy"]:
            sections.append("\n## 推荐策略\n")
            sections.append(f"{summary['recommended_strategy']}\n")

        return "\n".join(sections)


async def test_litigation_supporter():
    """测试诉讼支持主控制器"""
    supporter = LitigationSupporter()

    print("\n" + "="*80)
    print("⚖️ 专利诉讼支持主控制器测试")
    print("="*80)

    # 测试数据
    patent_id = "CN123456789A"
    case_number = "(2026)京73民初123号"

    case_info = {
        "court_name": "北京市知识产权法院",
        "case_number": case_number,
        "party_info": {
            "原告": "××科技有限公司",
            "被告": "××制造有限公司"
        },
        "case_brief": "专利侵权纠纷",
        "trial_date": "2026年5月15日",
        "evidence_quality": 0.7,
        "complexity": 1.2,
        "patent_info": {
            "validity_score": 0.8,
            "patent_type": "invention"
        }
    }

    evidences = [
        {
            "id": "EVI_001",
            "name": "专利证书",
            "evidence_type": "document",
            "description": "发明专利证书",
            "source": "国家知识产权局",
            "reliability": "high",
            "relevance": 0.9
        },
        {
            "id": "EVI_002",
            "name": "侵权产品",
            "evidence_type": "material",
            "description": "公证购买的侵权产品",
            "source": "公证处",
            "reliability": "high",
            "relevance": 0.95
        }
    ]

    pleading_arguments = [
        {
            "title": "被告实施了侵犯原告专利权的行为",
            "argument": "被告制造、销售的产品落入原告专利保护范围",
            "legal_basis": ["《专利法》第十一条"],
            "evidence_support": ["EVI_001", "EVI_002"]
        }
    ]

    # 提供诉讼支持
    result = await supporter.support_litigation(
        patent_id=patent_id,
        case_number=case_number,
        litigation_type=LitigationType.INFRINGEMENT,
        litigation_role=LitigationRole.PLAINTIFF,
        case_info=case_info,
        evidences=evidences,
        pleading_arguments=pleading_arguments
    )

    print(f"\n✅ 诉讼支持完成:")
    print(f"   案号: {result.case_number}")
    print(f"   诉讼类型: {result.litigation_type}")
    print(f"   完成模块: {result.metadata['modules_completed']}/4")

    print(f"\n📊 总结:")
    summary = result.summary
    if summary["win_probability"]:
        print(f"   胜诉概率: {summary['win_probability']:.1%}")
    if summary["risk_level"]:
        print(f"   风险等级: {summary['risk_level']}")
    if summary["evidence_count"]:
        print(f"   证据数量: {summary['evidence_count']}")

    # 保存到文件
    import tempfile
    output_dir = tempfile.mkdtemp(prefix="litigation_support_")
    saved_files = supporter.save_to_files(result, output_dir)

    print(f"\n💾 已保存{len(saved_files)}个文件到: {output_dir}")
    for file in saved_files:
        print(f"      - {Path(file).name}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_litigation_supporter())
