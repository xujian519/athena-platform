#!/usr/bin/env python3
"""
庭审辅助工具

提供庭审要点整理、质证提纲、答辩策略等庭审辅助功能。
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrialPhase(Enum):
    """庭审阶段"""
    PRE_TRIAL = "pre_trial"  # 庭前准备
    COURT_INVESTIGATION = "court_investigation"  # 法庭调查
    COURT_DEBATE = "court_debate"  # 法庭辩论
    FINAL_STATEMENT = "final_statement"  # 最后陈述
    MEDIATION = "mediation"  # 调解


@dataclass
class TrialPoint:
    """庭审要点"""
    phase: TrialPhase
    point_type: str  # 要点类型
    content: str  # 要点内容
    priority: str  # 优先级 (high/medium/low)
    preparation: str  # 准备工作

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "phase": self.phase.value,
            "point_type": self.point_type,
            "content": self.content,
            "priority": self.priority,
            "preparation": self.preparation
        }


@dataclass
class ExaminationOutline:
    """质证提纲"""
    evidence_id: str
    evidence_name: str
    questions: list[str]  # 质证问题
    expected_answers: list[str]  # 预期回答
    objection_points: list[str]  # 异议要点

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "evidence_id": self.evidence_id,
            "evidence_name": self.evidence_name,
            "questions": self.questions,
            "expected_answers": self.expected_answers,
            "objection_points": self.objection_points
        }


@dataclass
class TrialStrategy:
    """庭审策略"""
    overall_strategy: str  # 总体策略
    key_winning_points: list[str]  # 关键胜诉点
    risk_points: list[str]  # 风险点
    response_strategy: dict[str, str]  # 应对策略
    settlement_recommendation: str | None  # 和解建议

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "overall_strategy": self.overall_strategy,
            "key_winning_points": self.key_winning_points,
            "risk_points": self.risk_points,
            "response_strategy": self.response_strategy,
            "settlement_recommendation": self.settlement_recommendation
        }


@dataclass
class TrialPreparationGuide:
    """庭审准备指南"""
    trial_points: list[TrialPoint]  # 庭审要点
    examination_outlines: list[ExaminationOutline]  # 质证提纲
    trial_strategy: TrialStrategy  # 庭审策略
    checklists: dict[str, list[str]  # 检查清单
    timeline: list[dict[str, str]  # 时间安排

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "trial_points": [p.to_dict() for p in self.trial_points],
            "examination_outlines": [e.to_dict() for e in self.examination_outlines],
            "trial_strategy": self.trial_strategy.to_dict(),
            "checklists": self.checklists,
            "timeline": self.timeline
        }


class TrialAssistant:
    """庭审辅助工具"""

    def __init__(self):
        """初始化辅助工具"""
        self.trial_templates = self._load_trial_templates()
        logger.info("✅ 庭审辅助工具初始化成功")

    def _load_trial_templates(self) -> dict[str, Any]:
        """加载庭审模板"""
        return {
            "phases": {
                "pre_trial": {
                    "name": "庭前准备",
                    "key_points": [
                        "证据交换和质证准备",
                        "梳理争议焦点",
                        "准备代理词和答辩状",
                        "确认出庭人员"
                    ]
                },
                "court_investigation": {
                    "name": "法庭调查",
                    "key_points": [
                        "陈述诉讼请求",
                        "举证和质证",
                        "回答法庭询问",
                        "总结争议焦点"
                    ]
                },
                "court_debate": {
                    "name": "法庭辩论",
                    "key_points": [
                        "发表代理意见",
                        "回应对方论点",
                        "反驳对方观点",
                        "总结辩论要点"
                    ]
                },
                "final_statement": {
                    "name": "最后陈述",
                    "key_points": [
                        "总结核心观点",
                        "强调胜诉理由",
                        "表达调解意愿"
                    ]
                }
            }
        }

    def prepare_trial(
        self,
        case_info: dict[str, Any],
        evidences: list[dict[str, Any],
        case_analysis: dict[str, Any] | None = None
    ) -> TrialPreparationGuide:
        """
        准备庭审

        Args:
            case_info: 案件信息
            evidences: 证据列表
            case_analysis: 案件分析（可选）

        Returns:
            TrialPreparationGuide对象
        """
        logger.info(f"⚖️ 开始准备庭审: {case_info.get('case_number', '')}")

        # 步骤1: 生成庭审要点
        trial_points = self._generate_trial_points(case_info, evidences)

        # 步骤2: 生成质证提纲
        examination_outlines = self._generate_examination_outlines(evidences)

        # 步骤3: 制定庭审策略
        trial_strategy = self._formulate_trial_strategy(case_info, case_analysis)

        # 步骤4: 生成检查清单
        checklists = self._generate_checklists(case_info, evidences)

        # 步骤5: 生成时间安排
        timeline = self._generate_timeline(case_info)

        return TrialPreparationGuide(
            trial_points=trial_points,
            examination_outlines=examination_outlines,
            trial_strategy=trial_strategy,
            checklists=checklists,
            timeline=timeline
        )

    def _generate_trial_points(
        self,
        case_info: dict[str, Any],
        evidences: list[dict[str, Any]
    ) -> list[TrialPoint]:
        """生成庭审要点"""
        points = []

        # 庭前准备要点
        points.append(TrialPoint(
            phase=TrialPhase.PRE_TRIAL,
            point_type="证据准备",
            content="完成所有证据的整理和编号，准备证据目录",
            priority="high",
            preparation="打印证据清单，准备原件和复印件"
        ))

        points.append(TrialPoint(
            phase=TrialPhase.PRE_TRIAL,
            point_type="争议焦点梳理",
            content="明确案件的核心争议点，准备相应证据和法律依据",
            priority="high",
            preparation="整理争议焦点清单，准备法律条文"
        ))

        # 法庭调查要点
        points.append(TrialPoint(
            phase=TrialPhase.COURT_INVESTIGATION,
            point_type="陈述准备",
            content="准备清晰的诉讼请求陈述，突出重点",
            priority="high",
            preparation="撰写陈述提纲，控制在3分钟内"
        ))

        points.append(TrialPoint(
            phase=TrialPhase.COURT_INVESTIGATION,
            point_type="质证准备",
            content=f"对{len(evidences)}项证据逐一准备质证意见",
            priority="high",
            preparation="准备质证提纲，标注关键证据"
        ))

        # 法庭辩论要点
        points.append(TrialPoint(
            phase=TrialPhase.COURT_DEBATE,
            point_type="辩论准备",
            content="准备核心论点，预判对方论点并准备反驳",
            priority="high",
            preparation="整理辩论要点，准备法律依据"
        ))

        # 最后陈述要点
        points.append(TrialPoint(
            phase=TrialPhase.FINAL_STATEMENT,
            point_type="总结陈述",
            content="准备简明扼要的最后陈述（2分钟内）",
            priority="medium",
            preparation="撰写陈述稿，强调核心观点"
        ))

        return points

    def _generate_examination_outlines(
        self,
        evidences: list[dict[str, Any]
    ) -> list[ExaminationOutline]:
        """生成质证提纲"""
        outlines = []

        for evi in evidences[:10]:  # 最多处理前10项证据
            evidence_id = evi.get("id", "")
            evidence_name = evi.get("name", "")

            # 根据证据类型生成问题
            questions = self._generate_examination_questions(evi)

            # 预期回答
            expected_answers = self._generate_expected_answers(evi)

            # 异议要点
            objection_points = self._identify_objection_points(evi)

            outline = ExaminationOutline(
                evidence_id=evidence_id,
                evidence_name=evidence_name,
                questions=questions,
                expected_answers=expected_answers,
                objection_points=objection_points
            )
            outlines.append(outline)

        return outlines

    def _generate_examination_questions(self, evidence: dict[str, Any]) -> list[str]:
        """生成质证问题"""
        questions = []

        evidence_type = evidence.get("evidence_type", "")
        description = evidence.get("description", "")

        # 基础问题
        questions.append(f"该{evidence_type}的真实性如何？")
        questions.append(f"该{evidence_type}的来源是否合法？")
        questions.append(f"该{evidence_type}与本案的关联性如何？")

        # 根据证据类型补充问题
        if "document" in evidence_type.lower():
            questions.append("文档是否完整？有无涂改或添加？")
            questions.append("文档的签署时间和签署人是否明确？")

        elif "material" in evidence_type.lower():
            questions.append("物证是否原始取得？保存是否完好？")
            questions.append("物证的取得过程是否有公证？")

        # 根据描述补充问题
        if "专利" in description:
            questions.append("专利证书是否有效？是否缴纳年费？")
        elif "合同" in description:
            questions.append("合同是否双方签署？是否实际履行？")

        return questions

    def _generate_expected_answers(self, evidence: dict[str, Any]) -> list[str]:
        """生成预期回答"""
        answers = []

        reliability = evidence.get("reliability", "medium")

        if reliability == "high":
            answers.append("该证据真实合法，应予采信")
            answers.append("该证据与本案密切相关，证明力强")
        elif reliability == "low":
            answers.append("该证据真实性存疑，需要补强")
            answers.append("该证据与本案关联性不足")
        else:
            answers.append("该证据需要结合其他证据综合认定")

        return answers

    def _identify_objection_points(self, evidence: dict[str, Any]) -> list[str]:
        """识别异议要点"""
        objections = []

        reliability = evidence.get("reliability", "medium")
        source = evidence.get("source", "")

        if reliability == "low":
            objections.append("证据真实性存疑")
            objections.append("证据证明力较弱")

        if "自制" in source or "单方" in source:
            objections.append("证据来源存疑，缺乏第三方认证")

        return objections

    def _formulate_trial_strategy(
        self,
        case_info: dict[str, Any],
        case_analysis: dict[str, Any] | None
    ) -> TrialStrategy:
        """制定庭审策略"""
        # 总体策略
        win_probability = case_analysis.get("win_probability", 0.5) if case_analysis else 0.5

        if win_probability >= 0.7:
            overall_strategy = "积极进攻，争取胜诉"
        elif win_probability >= 0.5:
            overall_strategy = "稳健推进，适时和解"
        else:
            overall_strategy = "防御为主，争取和解"

        # 关键胜诉点
        key_winning_points = [
            "专利权的有效性和稳定性",
            "侵权行为的认定",
            "损害赔偿的合理计算"
        ]

        # 风险点
        risk_points = [
            "专利可能被宣告无效",
            "侵权认定可能存在争议",
            "损害赔偿数额可能被调整"
        ]

        # 应对策略
        response_strategy = {
            "专利有效性争议": "准备专利检索报告，强调专利创造性",
            "侵权行为争议": "准备详细的技术特征对比分析",
            "赔偿数额争议": "准备详细的损失计算依据和证据"
        }

        # 和解建议
        if win_probability < 0.5:
            settlement_recommendation = "建议积极寻求和解，降低诉讼风险"
        elif win_probability < 0.7:
            settlement_recommendation = "可在庭审过程中根据情况评估和解可能性"
        else:
            settlement_recommendation = "坚持诉讼，暂不考虑和解"

        return TrialStrategy(
            overall_strategy=overall_strategy,
            key_winning_points=key_winning_points,
            risk_points=risk_points,
            response_strategy=response_strategy,
            settlement_recommendation=settlement_recommendation
        )

    def _generate_checklists(
        self,
        case_info: dict[str, Any],
        evidences: list[dict[str, Any]
    ) -> dict[str, list[str]:
        """生成检查清单"""
        checklists = {
            "庭前准备": [
                "□ 证据原件和复印件准备齐全",
                "□ 证据目录和质证意见打印",
                "□ 代理词和答辩状准备",
                "□ 授权委托书和律师证准备",
                "□ 出庭人员确认"
            ],
            "庭审材料": [
                f"□ 证据清单（{len(evidences)}项）",
                "□ 证据原件核对",
                "□ 法律条文汇编",
                "□ 代理词提纲",
                "□ 笔录本和笔"
            ],
            "程序事项": [
                "□ 核对对方当事人身份",
                "□ 确认合议庭组成人员",
                "□ 申请回避情况确认",
                "□ 举证期限确认"
            ]
        }

        return checklists

    def _generate_timeline(self, case_info: dict[str, Any]) -> list[dict[str, str]:
        """生成时间安排"""
        trial_date = case_info.get("trial_date", "待定")

        timeline = [
            {
                "stage": "庭前准备",
                "time": "开庭前3天",
                "tasks": "完成证据整理和质证准备"
            },
            {
                "stage": "庭前会议",
                "time": "开庭前1天",
                "tasks": "参加庭前会议，确认争议焦点"
            },
            {
                "stage": "开庭审理",
                "time": trial_date,
                "tasks": "参加庭审，发表代理意见"
            },
            {
                "stage": "庭后工作",
                "time": "庭审后3天内",
                "tasks": "提交代理词和补充材料"
            }
        ]

        return timeline


async def test_trial_assistant():
    """测试庭审辅助工具"""
    assistant = TrialAssistant()

    print("\n" + "="*80)
    print("⚖️ 庭审辅助工具测试")
    print("="*80)

    # 测试数据
    case_info = {
        "case_number": "(2026)京73民初123号",
        "trial_date": "2026年5月15日 上午9:30",
        "court": "北京市知识产权法院"
    }

    evidences = [
        {
            "id": "EVI_001",
            "name": "专利证书",
            "evidence_type": "document",
            "description": "发明专利证书原件",
            "source": "国家知识产权局",
            "reliability": "high"
        },
        {
            "id": "EVI_002",
            "name": "侵权产品",
            "evidence_type": "material",
            "description": "公证购买的侵权产品",
            "source": "公证处",
            "reliability": "high"
        },
        {
            "id": "EVI_003",
            "name": "销售记录",
            "evidence_type": "document",
            "description": "被告销售记录",
            "source": "企业内部",
            "reliability": "medium"
        }
    ]

    case_analysis = {
        "win_probability": 0.65,
        "risk_level": "medium"
    }

    # 准备庭审
    guide = assistant.prepare_trial(case_info, evidences, case_analysis)

    print("\n📋 庭审准备指南:")
    print(f"   庭审要点数: {len(guide.trial_points)}")
    print(f"   质证提纲数: {len(guide.examination_outlines)}")

    print("\n   庭审要点（前5个）:")
    for point in guide.trial_points[:5]:
        print(f"      [{point.phase.value}] {point.point_type}: {point.content[:40]}...")

    print("\n   质证提纲（前3个）:")
    for outline in guide.examination_outlines[:3]:
        print(f"      - {outline.evidence_name}: {len(outline.questions)}个质证问题")

    print("\n   庭审策略:")
    strategy = guide.trial_strategy
    print(f"      总体策略: {strategy.overall_strategy}")
    print(f"      关键胜诉点: {', '.join(strategy.key_winning_points[:2])}")
    print(f"      和解建议: {strategy.settlement_recommendation}")

    print("\n   检查清单:")
    for category, items in guide.checklists.items():
        print(f"      {category}: {len(items)}项")

    print("\n   时间安排:")
    for item in guide.timeline:
        print(f"      [{item['time']}] {item['stage']}: {item['tasks']}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_trial_assistant())
