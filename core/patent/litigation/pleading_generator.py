#!/usr/bin/env python3
"""
代理词生成器

生成专利诉讼代理词，包括原告代理词和被告答辩状。
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PleadingType(Enum):
    """代理词类型"""
    PLAINTIFF_STATEMENT = "plaintiff_statement"  # 原告代理词
    DEFENDANT_ANSWER = "defendant_answer"  # 被告答辩状
    REJOINDER = "rejoinder"  # 反驳词
    FINAL_ARGUMENT = "final_argument"  # 最终陈述


@dataclass
class LegalArgument:
    """法律论点"""
    title: str
    argument: str
    legal_basis: List[str]  # 法律依据
    evidence_support: List[str]  # 支持证据
    counter_argument: Optional[str] = None  # 预测对方论点

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "argument": self.argument,
            "legal_basis": self.legal_basis,
            "evidence_support": self.evidence_support,
            "counter_argument": self.counter_argument
        }


@dataclass
class PleadingStructure:
    """代理词结构"""
    pleading_type: PleadingType
    court_name: str
    case_number: str
    party_info: Dict[str, str]  # 当事人信息
    case_brief: str  # 案情简介
    main_arguments: List[LegalArgument]  # 主要论点
    conclusion: str  # 结论
    relief_sought: Optional[str] = None  # 诉讼请求
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pleading_type": self.pleading_type.value,
            "court_name": self.court_name,
            "case_number": self.case_number,
            "party_info": self.party_info,
            "case_brief": self.case_brief,
            "main_arguments": [arg.to_dict() for arg in self.main_arguments],
            "conclusion": self.conclusion,
            "relief_sought": self.relief_sought,
            "metadata": self.metadata
        }


@dataclass
class PleadingResult:
    """代理词生成结果"""
    pleading_text: str  # 代理词文本
    structure: PleadingStructure  # 结构化数据
    word_count: int  # 字数统计
    key_points: List[str]  # 要点总结

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pleading_text": self.pleading_text,
            "structure": self.structure.to_dict(),
            "word_count": self.word_count,
            "key_points": self.key_points
        }


class PleadingGenerator:
    """代理词生成器"""

    def __init__(self):
        """初始化生成器"""
        self.legal_templates = self._load_legal_templates()
        self.patent_laws = self._load_patent_laws()
        logger.info("✅ 代理词生成器初始化成功")

    def _load_legal_templates(self) -> Dict[str, Any]:
        """加载法律模板"""
        return {
            "plaintiff_statement": {
                "opening": "尊敬的审判长、审判员：",
                "introduction": "就{case_number}号案件，{party}依法委托代理人出庭参加诉讼，现发表如下代理意见：",
                "structure": [
                    "一、案件基本情况",
                    "二、主要事实和理由",
                    "三、法律依据",
                    "四、诉讼请求",
                    "五、结论"
                ]
            },
            "defendant_answer": {
                "opening": "尊敬的审判长、审判员：",
                "introduction": "就{case_number}号案件，{party}针对原告的诉讼请求，提出如下答辩意见：",
                "structure": [
                    "一、对案件事实的陈述",
                    "二、对原告主张的答辩",
                    "三、抗辩理由",
                    "四、结论"
                ]
            }
        }

    def _load_patent_laws(self) -> Dict[str, List[str]]:
        """加载专利法条"""
        return {
            "patent_law": [
                "《中华人民共和国专利法》第十一条 - 发明和实用新型专利权被授予后，除本法另有规定的以外，任何单位或者个人未经专利权人许可，都不得实施其专利",
                "《中华人民共和国专利法》第六十五条 - 侵犯专利权的赔偿数额按照权利人因被侵权所受到的实际损失确定",
                "《中华人民共和国专利法》第五十九条 - 发明或者实用新型专利权的保护范围以其权利要求的内容为准"
            ],
            "judicial_interpretation": [
                "《最高人民法院关于审理侵犯专利权纠纷案件应用法律若干问题的解释》第七条",
                "《最高人民法院关于审理专利纠纷案件适用法律问题的若干规定》第十七条"
            ]
        }

    def generate_pleading(
        self,
        pleading_type: PleadingType,
        case_info: Dict[str, Any],
        arguments: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> PleadingResult:
        """
        生成代理词

        Args:
            pleading_type: 代理词类型
            case_info: 案件信息
            arguments: 论点列表
            options: 可选配置

        Returns:
            PleadingResult对象
        """
        logger.info(f"✍️ 开始生成代理词: 类型={pleading_type.value}")

        # 步骤1: 构建结构化数据
        structure = self._build_structure(pleading_type, case_info, arguments)

        # 步骤2: 生成代理词文本
        pleading_text = self._generate_text(structure)

        # 步骤3: 统计字数
        word_count = len(pleading_text)

        # 步骤4: 提取要点
        key_points = self._extract_key_points(structure)

        return PleadingResult(
            pleading_text=pleading_text,
            structure=structure,
            word_count=word_count,
            key_points=key_points
        )

    def _build_structure(
        self,
        pleading_type: PleadingType,
        case_info: Dict[str, Any],
        arguments: List[Dict[str, Any]]
    ) -> PleadingStructure:
        """构建结构化数据"""
        # 转换论点为LegalArgument对象
        main_arguments = []
        for arg in arguments:
            legal_arg = LegalArgument(
                title=arg.get("title", ""),
                argument=arg.get("argument", ""),
                legal_basis=arg.get("legal_basis", []),
                evidence_support=arg.get("evidence_support", []),
                counter_argument=arg.get("counter_argument")
            )
            main_arguments.append(legal_arg)

        # 确定诉讼请求
        relief_sought = None
        if pleading_type == PleadingType.PLAINTIFF_STATEMENT:
            relief_sought = case_info.get("relief_sought", "")

        # 结论
        conclusion = self._generate_conclusion(pleading_type, case_info)

        return PleadingStructure(
            pleading_type=pleading_type,
            court_name=case_info.get("court_name", "××人民法院"),
            case_number=case_info.get("case_number", ""),
            party_info=case_info.get("party_info", {}),
            case_brief=case_info.get("case_brief", ""),
            main_arguments=main_arguments,
            conclusion=conclusion,
            relief_sought=relief_sought,
            metadata={
                "generation_date": datetime.now().strftime("%Y-%m-%d"),
                "arguments_count": len(main_arguments)
            }
        )

    def _generate_conclusion(
        self,
        pleading_type: PleadingType,
        case_info: Dict[str, Any]
    ) -> str:
        """生成结论"""
        if pleading_type == PleadingType.PLAINTIFF_STATEMENT:
            return (
                "综上所述，原告的诉讼请求事实清楚、证据充分、法律依据明确。"
                "恳请贵院依法支持原告的全部诉讼请求，维护原告的合法权益。"
            )
        else:  # DEFENDANT_ANSWER
            return (
                "综上所述，原告的诉讼请求缺乏事实和法律依据，被告的行为不构成侵权。"
                "恳请贵院依法驳回原告的诉讼请求，维护被告的合法权益。"
            )

    def _generate_text(self, structure: PleadingStructure) -> str:
        """生成代理词文本"""
        sections = []

        # 标题
        pleading_type_name = {
            PleadingType.PLAINTIFF_STATEMENT: "代理词",
            PleadingType.DEFENDANT_ANSWER: "答辩状",
            PleadingType.REJOINDER: "反驳词",
            PleadingType.FINAL_ARGUMENT: "最终陈述"
        }.get(structure.pleading_type, "代理词")

        sections.append(f"# {pleading_type_name}\n")

        # 抬头
        sections.append(f"{structure.court_name}：\n")

        # 当事人信息
        if structure.party_info:
            sections.append("## 当事人信息\n")
            for role, name in structure.party_info.items():
                sections.append(f"{role}: {name}\n")
            sections.append("\n")

        # 开场白
        template = self.legal_templates.get(
            structure.pleading_type.value,
            self.legal_templates["plaintiff_statement"]
        )

        party_name = structure.party_info.get("原告", "××公司") if structure.pleading_type == PleadingType.PLAINTIFF_STATEMENT else structure.party_info.get("被告", "××公司")

        sections.append(f"{template['opening']}\n")
        sections.append(f"{template['introduction'].format(case_number=structure.case_number, party=party_name)}\n\n")

        # 案情简介
        if structure.case_brief:
            sections.append("## 案情简介\n")
            sections.append(f"{structure.case_brief}\n\n")

        # 主要论点
        sections.append("## 主要事实和理由\n")
        for idx, arg in enumerate(structure.main_arguments, 1):
            sections.append(f"### {idx}. {arg.title}\n")
            sections.append(f"{arg.argument}\n\n")

            # 法律依据
            if arg.legal_basis:
                sections.append("**法律依据:**\n")
                for basis in arg.legal_basis:
                    sections.append(f"- {basis}\n")
                sections.append("\n")

            # 支持证据
            if arg.evidence_support:
                sections.append("**支持证据:**\n")
                for evidence in arg.evidence_support:
                    sections.append(f"- {evidence}\n")
                sections.append("\n")

            # 预测对方论点（可选）
            if arg.counter_argument:
                sections.append("**预期对方论点及反驳:**\n")
                sections.append(f"{arg.counter_argument}\n\n")

        # 诉讼请求（仅原告代理词）
        if structure.relief_sought:
            sections.append("## 诉讼请求\n")
            sections.append(f"{structure.relief_sought}\n\n")

        # 结论
        sections.append("## 结论\n")
        sections.append(f"{structure.conclusion}\n\n")

        # 结尾
        sections.append("此致\n")
        sections.append(f"{structure.court_name}\n\n")
        sections.append(f"代理人：×××\n")
        sections.append(f"{datetime.now().strftime('%Y年%m月%d日')}\n")

        return "\n".join(sections)

    def _extract_key_points(self, structure: PleadingStructure) -> List[str]:
        """提取要点总结"""
        key_points = []

        # 从主要论点中提取要点
        for arg in structure.main_arguments[:5]:  # 最多提取5个要点
            key_points.append(arg.title)

        # 如果有诉讼请求，也提取
        if structure.relief_sought:
            key_points.append(f"诉讼请求: {structure.relief_sought[:50]}...")

        return key_points


async def test_pleading_generator():
    """测试代理词生成器"""
    generator = PleadingGenerator()

    print("\n" + "="*80)
    print("✍️ 代理词生成器测试")
    print("="*80)

    # 测试案例: 原告代理词
    case_info = {
        "court_name": "北京市知识产权法院",
        "case_number": "(2026)京73民初123号",
        "party_info": {
            "原告": "××科技有限公司",
            "被告": "××制造有限公司"
        },
        "case_brief": (
            "原告是专利号为ZL202010123456.7的发明专利权人。"
            "被告未经许可，制造、销售、许诺销售落入原告专利保护范围的产品，"
            "严重侵犯了原告的合法权益。"
        ),
        "relief_sought": (
            "1. 判令被告立即停止侵犯原告专利权的行为；\n"
            "2. 判令被告赔偿原告经济损失及合理开支共计人民币200万元；\n"
            "3. 判令被告承担本案全部诉讼费用。"
        )
    }

    arguments = [
        {
            "title": "被告实施了侵犯原告专利权的行为",
            "argument": (
                "被告制造、销售的产品包含了原告专利权利要求1-5的全部技术特征，"
                "落入原告专利保护范围。根据专利法第十一条规定，任何单位或者个人 "
                "未经专利权人许可，都不得实施其专利。"
            ),
            "legal_basis": [
                "《中华人民共和国专利法》第十一条",
                "《中华人民共和国专利法》第五十九条"
            ],
            "evidence_support": [
                "证据EVI_001: 专利证书及权利要求书",
                "证据EVI_002: 公证购买的侵权产品",
                "证据EVI_003: 侵权产品技术特征分析报告"
            ]
        },
        {
            "title": "原告的专利权稳定有效",
            "argument": (
                "原告的专利经过国家知识产权局的实质审查，授权合法有效。"
                "被告未提供有效证据证明专利无效，专利权应予保护。"
            ),
            "legal_basis": [
                "《中华人民共和国专利法》第三十九条",
                "《中华人民共和国专利法》第四十五条"
            ],
            "evidence_support": [
                "证据EVI_001: 专利证书",
                "证据EVI_004: 专利登记簿副本"
            ]
        },
        {
            "title": "被告应承担侵权赔偿责任",
            "argument": (
                "被告的侵权行为给原告造成了巨大经济损失。根据专利法第六十五条规定，"
                "应按照原告的实际损失或被告的侵权获利确定赔偿数额。"
            ),
            "legal_basis": [
                "《中华人民共和国专利法》第六十五条",
                "《最高人民法院关于审理专利纠纷案件应用法律若干问题的解释》第二十条"
            ],
            "evidence_support": [
                "证据EVI_005: 原告销售合同及财务报表",
                "证据EVI_006: 被告销售记录及获利证据"
            ]
        }
    ]

    # 生成代理词
    result = generator.generate_pleading(
        pleading_type=PleadingType.PLAINTIFF_STATEMENT,
        case_info=case_info,
        arguments=arguments
    )

    print(f"\n📄 代理词生成结果:")
    print(f"   类型: {result.structure.pleading_type.value}")
    print(f"   字数: {result.word_count}字")
    print(f"   论点数: {len(result.structure.main_arguments)}")

    print(f"\n   要点总结:")
    for point in result.key_points:
        print(f"      - {point}")

    print(f"\n   代理词文本（前500字）:")
    print(result.pleading_text[:500] + "...")

    # 保存到文件
    import tempfile
    output_file = tempfile.mktemp(suffix='_pleading.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result.pleading_text)
    print(f"\n💾 代理词已保存到: {output_file}")

    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_pleading_generator())
