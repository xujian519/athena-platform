#!/usr/bin/env python3
"""
专利视角发现器 (Patent Perspective Discoverer)

基于专利内容自动发现多个分析视角,用于引导 STORM 的多角度提问。

视角类型:
- 技术视角: 技术方案、实现细节、创新点
- 法律视角: 权利要求、法律状态、侵权风险
- 时间视角: 申请时间、优先权、技术脉络
- 申请人视角: 申请人背景、专利布局
- 市场视角: 同族专利、引用关系、技术影响

作者: Athena 平台团队
创建时间: 2025-01-02
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


class PerspectiveType(Enum):
    """视角类型枚举"""

    TECHNICAL = "technical"  # 技术视角
    LEGAL = "legal"  # 法律视角
    TEMPORAL = "temporal"  # 时间视角
    APPLICANT = "applicant"  # 申请人视角
    MARKET = "market"  # 市场视角


@dataclass
class Perspective:
    """分析视角"""

    name: str  # 视角名称
    type: PerspectiveType  # 视角类型
    description: str  # 视角描述
    questions: list[str] = field(default_factory=list)  # 引导问题
    keywords: list[str] = field(default_factory=list)  # 相关关键词
    priority: int = 5  # 优先级 (1-10)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "questions": self.questions,
            "keywords": self.keywords,
            "priority": self.priority,
        }


@dataclass
class PatentBasicInfo:
    """专利基本信息"""

    patent_id: str  # 专利号
    title: str  # 标题
    abstract: str  # 摘要
    applicant: str  # 申请人
    inventor: str  # 发明人
    application_date: str  # 申请日期
    ipc_classification: str  # IPC 分类
    claims: list[str] = field(default_factory=list)  # 权利要求


class PatentPerspectiveDiscoverer:
    """
    专利视角发现器

    基于专利内容自动发现多个分析视角,用于 STORM 的多角度提问。

    使用示例:
        discoverer = PatentPerspectiveDiscoverer()

        patent_info = PatentBasicInfo(
            patent_id="CN202310123456.7",
            title="一种基于深度学习的图像识别方法",
            abstract="本发明公开了...",
            applicant="某某科技公司",
            ...
        )

        perspectives = discoverer.discover(patent_info)

        for perspective in perspectives:
            print(f"{perspective.name}: {perspective.description}")
            for question in perspective.questions:
                print(f"  - {question}")
    """

    # 预定义的视角模板
    PERSPECTIVE_TEMPLATES = {
        PerspectiveType.TECHNICAL: {
            "name": "技术分析视角",
            "description": "从技术实现的角度分析专利的技术方案、创新点和改进空间",
            "questions": [
                "这个专利的核心技术方案是什么?",
                "与现有技术相比,有哪些创新点?",
                "技术实现的关键难点在哪里?",
                "是否存在技术缺陷或可以改进的地方?",
                "该技术的应用场景有哪些?",
            ],
            "keywords": ["技术方案", "创新点", "技术特征", "实现方式", "技术效果"],
        },
        PerspectiveType.LEGAL: {
            "name": "法律分析视角",
            "description": "从法律保护的角度分析权利要求范围、法律状态和侵权风险",
            "questions": [
                "权利要求的保护范围有多大?",
                "是否存在权利要求不清楚或不支持的问题?",
                "该专利的法律状态如何?(有效/无效/审中)",
                "是否存在侵权风险?",
                "被无效宣告的可能性有多大?",
            ],
            "keywords": ["权利要求", "保护范围", "法律状态", "侵权", "无效"],
        },
        PerspectiveType.TEMPORAL: {
            "name": "时间发展视角",
            "description": "从时间发展的角度分析技术的演进脉络和最新动态",
            "questions": [
                "这项技术是如何发展演进的?",
                "申请时间对该专利的价值有什么影响?",
                "近期是否有相关的技术发展?",
                "优先权日对专利保护有什么意义?",
                "该技术未来的发展趋势是什么?",
            ],
            "keywords": ["申请时间", "优先权", "技术演进", "发展脉络", "最新技术"],
        },
        PerspectiveType.APPLICANT: {
            "name": "申请人分析视角",
            "description": "从申请人和发明人的角度分析专利布局和技术实力",
            "questions": [
                "申请人是什么类型的机构?",
                "申请人的技术实力如何?",
                "申请人的专利布局策略是什么?",
                "发明人在该领域的其他贡献?",
                "是否存在竞争对手的专利围堵?",
            ],
            "keywords": ["申请人", "发明人", "专利布局", "竞争对手", "技术实力"],
        },
        PerspectiveType.MARKET: {
            "name": "市场影响视角",
            "description": "从市场价值的角度分析同族专利、引用关系和商业化潜力",
            "questions": [
                "该专利是否有同族专利?布局在哪些国家?",
                "该专利被其他专利引用的情况?",
                "该技术的商业化潜力如何?",
                "是否存在相关的标准或产品?",
                "技术影响范围有多广?",
            ],
            "keywords": ["同族专利", "引用关系", "商业化", "技术影响", "市场规模"],
        },
    }

    def __init__(self):
        """初始化视角发现器"""
        logger.info("初始化专利视角发现器")

    def discover(self, patent_info: PatentBasicInfo) -> list[Perspective]:
        """
        基于专利信息发现相关视角

        Args:
            patent_info: 专利基本信息

        Returns:
            发现的视角列表,按优先级排序
        """
        logger.info(f"开始发现专利 {patent_info.patent_id} 的分析视角")

        perspectives = []

        # 1. 基础视角(所有专利都适用)
        for perspective_type, template in self.PERSPECTIVE_TEMPLATES.items():
            perspective = Perspective(
                name=template["name"],
                type=perspective_type,
                description=template["description"],
                questions=template["questions"].copy(),
                keywords=template["keywords"].copy(),
                priority=self._calculate_priority(perspective_type, patent_info),
            )
            perspectives.append(perspective)

        # 2. 基于专利特征定制视角
        custom_perspectives = self._generate_custom_perspectives(patent_info)
        perspectives.extend(custom_perspectives)

        # 3. 按优先级排序
        perspectives.sort(key=lambda p: p.priority, reverse=True)

        logger.info(f"发现 {len(perspectives)} 个分析视角")
        for p in perspectives:
            logger.debug(f"  - {p.name} (优先级: {p.priority})")

        return perspectives

    def _calculate_priority(
        self, perspective_type: PerspectiveType, patent_info: PatentBasicInfo
    ) -> int:
        """
        计算视角的优先级

        Args:
            perspective_type: 视角类型
            patent_info: 专利信息

        Returns:
            优先级分数 (1-10)
        """
        base_priority = 5  # 基础优先级

        # 根据专利特征调整优先级
        if perspective_type == PerspectiveType.TECHNICAL:
            # 技术专利,技术视角优先级高
            base_priority += 2
            if "发明" in patent_info.ipc_classification or "G06" in patent_info.ipc_classification:
                base_priority += 1  # 计算机类专利

        elif perspective_type == PerspectiveType.LEGAL:
            # 法律状态相关的优先级高
            if "权利要求" in str(patent_info.claims):
                base_priority += 2

        elif perspective_type == PerspectiveType.APPLICANT:
            # 大公司申请人,优先级高
            if any(
                company in patent_info.applicant
                for company in ["科技", "大学", "研究院", "集团", "有限"]
            ):
                base_priority += 1

        elif perspective_type == PerspectiveType.MARKET:
            # 近期申请的专利,市场视角优先级高
            if "2023" in patent_info.application_date or "2024" in patent_info.application_date:
                base_priority += 1

        return min(base_priority, 10)  # 最高10

    def _generate_custom_perspectives(self, patent_info: PatentBasicInfo) -> list[Perspective]:
        """
        基于专利特征生成定制视角

        Args:
            patent_info: 专利信息

        Returns:
            定制视角列表
        """
        custom_perspectives = []

        # 示例: 根据技术领域生成特定视角
        if "G06N" in patent_info.ipc_classification or "人工智能" in patent_info.title:
            # AI 相关专利
            custom_perspectives.append(
                Perspective(
                    name="算法性能视角",
                    type=PerspectiveType.TECHNICAL,
                    description="从算法性能的角度分析模型的准确率、效率和可扩展性",
                    questions=[
                        "该算法的准确率如何?",
                        "计算复杂度是多少?",
                        "是否需要大量训练数据?",
                        "模型的推理速度如何?",
                        "是否存在性能瓶颈?",
                    ],
                    keywords=["准确率", "效率", "复杂度", "训练数据", "推理速度"],
                    priority=7,
                )
            )

        elif "A61K" in patent_info.ipc_classification or "药物" in patent_info.title:
            # 药物相关专利
            custom_perspectives.append(
                Perspective(
                    name="临床试验视角",
                    type=PerspectiveType.TECHNICAL,
                    description="从临床试验的角度分析药物的有效性和安全性",
                    questions=[
                        "是否已完成临床试验?",
                        "临床试验的结果如何?",
                        "是否存在副作用?",
                        "与现有药物相比的优势?",
                        "是否获得监管批准?",
                    ],
                    keywords=["临床试验", "有效性", "安全性", "副作用", "监管批准"],
                    priority=8,
                )
            )

        # 更多定制视角可以在此添加...

        return custom_perspectives

    def get_questions_for_perspective(
        self, perspective: Perspective, context: str | None = None
    ) -> list[str]:
        """
        获取特定视角的引导问题

        Args:
            perspective: 视角对象
            context: 额外上下文(可选)

        Returns:
            引导问题列表
        """
        questions = perspective.questions.copy()

        # 如果有额外上下文,可以动态生成更多问题
        if context:
            # 这里可以集成 LLM 动态生成问题
            # 暂时返回预设问题
            pass

        return questions

    def format_perspectives_for_storm(self, perspectives: list[Perspective]) -> str:
        """
        格式化视角列表为 STORM 可用的格式

        Args:
            perspectives: 视角列表

        Returns:
            格式化的字符串
        """
        formatted = "专利分析视角:\n\n"

        for i, perspective in enumerate(perspectives, 1):
            formatted += f"{i}. {perspective.name}\n"
            formatted += f"   类型: {perspective.type.value}\n"
            formatted += f"   描述: {perspective.description}\n"
            formatted += "   关键问题:\n"

            for j, question in enumerate(perspective.questions[:3], 1):
                formatted += f"     {j}. {question}\n"

            formatted += "\n"

        return formatted


# 便捷函数
def discover_patent_perspectives(
    patent_id: str, title: str, abstract: str, applicant: str, **kwargs
) -> list[Perspective]:
    """
    便捷函数:发现专利视角

    Args:
        patent_id: 专利号
        title: 标题
        abstract: 摘要
        applicant: 申请人
        **kwargs: 其他专利信息

    Returns:
        视角列表
    """
    patent_info = PatentBasicInfo(
        patent_id=patent_id,
        title=title,
        abstract=abstract,
        applicant=applicant,
        ipc_classification=kwargs.get("ipc_classification", ""),
        application_date=kwargs.get("application_date", ""),
        inventor=kwargs.get("inventor", ""),
        claims=kwargs.get("claims", []),
    )

    discoverer = PatentPerspectiveDiscoverer()
    return discoverer.discover(patent_info)


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    # 创建测试专利信息
    test_patent = PatentBasicInfo(
        patent_id="CN202310123456.7",
        title="一种基于深度学习的图像识别方法",
        abstract="本发明公开了一种基于深度学习的图像识别方法,涉及人工智能技术领域...",
        applicant="某某科技公司",
        inventor="张三, 李四",
        application_date="2023-05-15",
        ipc_classification="G06N3/00",
        claims=[
            "1. 一种基于深度学习的图像识别方法,其特征在于...",
            "2. 根据权利要求1所述的方法,其特征在于...",
        ],
    )

    # 发现视角
    discoverer = PatentPerspectiveDiscoverer()
    perspectives = discoverer.discover(test_patent)

    # 打印结果
    print("=" * 60)
    print("专利视角发现测试")
    print("=" * 60)
    print(f"\n专利: {test_patent.title}")
    print(f"申请人: {test_patent.applicant}")
    print(f"\n发现 {len(perspectives)} 个分析视角:\n")

    for i, p in enumerate(perspectives, 1):
        print(f"{i}. {p.name} (优先级: {p.priority})")
        print(f"   {p.description}")
        print(f"   关键问题: {p.questions[0]}")
        print()

    # 格式化为 STORM 格式
    print("\n" + "=" * 60)
    print("STORM 格式输出:")
    print("=" * 60)
    print(discoverer.format_perspectives_for_storm(perspectives))
