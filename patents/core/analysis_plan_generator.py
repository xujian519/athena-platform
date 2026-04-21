#!/usr/bin/env python3
from __future__ import annotations
"""
分析计划生成器
Analysis Plan Generator

在文档完整性检查通过后，生成步骤2（智能分析）的详细计划

作者: 小诺·双鱼公主
创建时间: 2026-01-24
版本: v0.1.2 "晨星初现"
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

logger = setup_logging()


@dataclass
class AnalysisStep:
    """分析步骤"""

    step_number: int
    name: str
    description: str
    tools: list[str] = field(default_factory=list)
    estimated_time: str = ""
    output: str = ""


@dataclass
class AnalysisPlan:
    """分析计划"""

    plan_id: str
    target_application_number: str
    target_patent_title: str = ""

    # 审查意见信息
    examination_opinions: list[dict[str, Any]] = field(default_factory=list)
    legal_articles: list[str] = field(default_factory=list)
    target_claims: list[str] = field(default_factory=list)

    # 对比文件
    prior_art_count: int = 0

    # 分析步骤
    analysis_steps: list[AnalysisStep] = field(default_factory=list)

    # 预期结果
    expected_outcomes: list[str] = field(default_factory=list)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        """生成Markdown格式的分析计划"""
        md = []

        md.append("# 🎯 步骤2: 智能分析计划\n")
        md.append(f"**计划ID**: `{self.plan_id}`\n")
        md.append(f"**生成时间**: {self.created_at}\n\n")

        # 目标专利信息
        md.append("## 🎯 目标专利\n")
        md.append(f"- **申请号**: `{self.target_application_number}`\n")
        if self.target_patent_title:
            md.append(f"- **标题**: {self.target_patent_title}\n")
        md.append(f"- **涉及权利要求**: {', '.join(self.target_claims) if self.target_claims else '全部'}\n\n")

        # 审查意见摘要
        if self.examination_opinions:
            md.append("## 📋 审查意见摘要\n")
            for i, opinion in enumerate(self.examination_opinions, 1):
                md.append(f"### 意见 {i}\n")
                md.append(f"- **类型**: {opinion.get('opinion_type', 'N/A')}\n")
                md.append(f"- **涉及条款**: {', '.join(opinion.get('legal_articles', []))}\n")
                md.append(f"- **问题描述**: {opinion.get('issue_description', '')[:100]}...\n")
                md.append("")
            md.append("")

        # 法律条款
        if self.legal_articles:
            md.append("## ⚖️ 涉及法律条款\n")
            for article in self.legal_articles:
                md.append(f"- `{article}`\n")
            md.append("")

        # 对比文件
        if self.prior_art_count > 0:
            md.append(f"## 📄 对比文件 ({self.prior_art_count}个)\n")
            md.append("已确认所有对比文件全文已齐备\n\n")

        # 分析步骤
        md.append("## 📊 分析步骤\n")
        for step in self.analysis_steps:
            # 步骤0特别标注（小娜深度分析）
            if step.step_number == 0:
                md.append(f"### 🌟 步骤{step.step_number}: {step.name}\n")
            else:
                md.append(f"### 步骤{step.step_number}: {step.name}\n")

            md.append(f"{step.description}\n\n")
            if step.tools:
                md.append(f"**使用工具**: {', '.join(step.tools)}\n")
            if step.estimated_time:
                md.append(f"**预计耗时**: {step.estimated_time}\n")
            if step.output:
                md.append(f"**输出**: {step.output}\n")
            md.append("")

        # 预期结果
        md.append("## ✅ 预期成果\n")
        for outcome in self.expected_outcomes:
            md.append(f"- {outcome}\n")
        md.append("")

        # 用户确认
        md.append("---\n")
        md.append("## 🤔 请确认分析计划\n\n")
        md.append("- ✅ 回复 `确认` 或 `confirm` 开始智能分析\n")
        md.append("- ✏️  回复 `修改` 调整分析计划\n")
        md.append("- ❌ 回复 `取消` 返回上一步\n")

        return "".join(md)


class AnalysisPlanGenerator:
    """
    分析计划生成器

    根据审查意见和文档完整性状态，生成智能分析计划
    """

    def __init__(self):
        """初始化计划生成器"""
        logger.info("🎯 分析计划生成器初始化完成")

    def generate_plan(
        self,
        target_application_number: str,
        target_patent_title: str = "",
        examination_opinions: list[dict[str, Any]] | None = None,
        prior_art_count: int = 0,
    ) -> AnalysisPlan:
        """
        生成分析计划

        Args:
            target_application_number: 目标专利申请号
            target_patent_title: 目标专利标题
            examination_opinions: 审查意见列表
            prior_art_count: 对比文件数量

        Returns:
            AnalysisPlan: 分析计划
        """
        logger.info(f"🎯 生成分析计划: {target_application_number}")

        examination_opinions = examination_opinions or []

        # 生成计划ID
        plan_id = f"PLAN_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 提取涉及的法律条款和权利要求
        legal_articles = set()
        target_claims = set()

        for opinion in examination_opinions:
            for article in opinion.get("legal_articles", []):
                if isinstance(article, dict):
                    legal_articles.add(article.get("full_reference", ""))
                else:
                    legal_articles.add(str(article))

            for claim in opinion.get("target_claims", []):
                target_claims.add(claim)

        # 生成分析步骤
        analysis_steps = self._generate_analysis_steps(
            examination_opinions, prior_art_count
        )

        # 生成预期成果
        expected_outcomes = self._generate_expected_outcomes(
            examination_opinions, prior_art_count
        )

        plan = AnalysisPlan(
            plan_id=plan_id,
            target_application_number=target_application_number,
            target_patent_title=target_patent_title,
            examination_opinions=examination_opinions,
            legal_articles=sorted(legal_articles),
            target_claims=sorted(target_claims),
            prior_art_count=prior_art_count,
            analysis_steps=analysis_steps,
            expected_outcomes=expected_outcomes,
        )

        logger.info(f"✅ 分析计划生成完成: {plan_id}")
        return plan

    def _generate_analysis_steps(
        self,
        examination_opinions: list[dict[str, Any]],        prior_art_count: int,
    ) -> list[AnalysisStep]:
        """生成分析步骤"""
        steps = []

        # 步骤0: 小娜深度技术分析（新增）
        steps.append(
            AnalysisStep(
                step_number=0,
                name="小娜深度技术分析",
                description="使用小娜专利分析能力逐一分析目标专利和所有对比文件，"
                "提取技术特征、技术方案、技术效果，生成JSON和Markdown格式分析文档",
                tools=["XiaonaDeepTechnicalAnalyzer", "PatentAnalyzer", "KnowledgeConnector"],
                estimated_time=f"{prior_art_count + 1}-3分钟",
                output="目标专利技术分析文档 + 对比文件技术分析文档 + 对比分析报告(JSON+Markdown)",
            )
        )

        # 步骤1: 目标专利分析
        steps.append(
            AnalysisStep(
                step_number=1,
                name="目标专利全文分析",
                description="基于小娜深度分析结果，解析目标专利的说明书、权利要求书，"
                "构建技术特征体系",
                tools=["PatentParser", "FeatureExtractor", "KnowledgeGraph"],
                estimated_time="1-2分钟",
                output="技术特征列表、权利要求结构、技术方案架构",
            )
        )

        # 步骤2: 对比文件分析
        if prior_art_count > 0:
            steps.append(
                AnalysisStep(
                    step_number=2,
                    name="对比文件深度分析",
                    description=f"解析{prior_art_count}个对比文件，提取技术特征",
                    tools=["PatentParser", "FeatureExtractor", "MultiFileAnalyzer"],
                    estimated_time=f"{prior_art_count * 1}-2分钟",
                    output="对比文件技术特征列表",
                )
            )

        # 步骤3: 差异分析
        steps.append(
            AnalysisStep(
                step_number=3,
                name="技术特征差异分析",
                description="对比目标专利与对比文件的技术特征，识别区别技术特征",
                tools=["DifferenceAnalyzer", "SemanticComparator"],
                estimated_time="1-2分钟",
                output="区别技术特征列表、相似度矩阵",
            )
        )

        # 步骤4: 法律条款分析
        if examination_opinions:
            steps.append(
                AnalysisStep(
                    step_number=4,
                    name="法律条款符合性分析",
                    description="根据审查意见涉及的法律条款，分析符合性",
                    tools=["LegalArticleAnalyzer", "ComplianceChecker"],
                    estimated_time="2-3分钟",
                    output="法律条款符合性报告",
                )
            )

        # 步骤5: 答复策略制定
        steps.append(
            AnalysisStep(
                step_number=5,
                name="答复策略制定",
                description="基于差异分析和法律条款分析，制定答复策略",
                tools=[
                    "StrategyGenerator",
                    "CaseDatabase",
                    "QualitativeRuleEngine",
                    "HebbianOptimizer",
                ],
                estimated_time="2-3分钟",
                output="答复策略方案、争辩要点",
            )
        )

        # 步骤6: 争辩点梳理
        steps.append(
            AnalysisStep(
                step_number=6,
                name="争辩点梳理与论证",
                description="整理争辩要点，生成论证逻辑",
                tools=["ArgumentBuilder", "LogicValidator"],
                estimated_time="1-2分钟",
                output="争辩点清单、论证逻辑链",
            )
        )

        return steps

    def _generate_expected_outcomes(
        self,
        examination_opinions: list[dict[str, Any]],        prior_art_count: int,
    ) -> list[str]:
        """生成预期成果"""
        outcomes = []

        outcomes.append("目标专利技术特征完整提取")
        outcomes.append(f"{prior_art_count}个对比文件技术特征分析完成")

        if examination_opinions:
            outcomes.append(f"{len(examination_opinions)}条审查意见的深度分析")
            outcomes.append("针对每条意见的答复策略方案")

        outcomes.append("区别技术特征识别与论证")
        outcomes.append("法律条款符合性分析报告")
        outcomes.append("争辩要点清单与论证逻辑")
        outcomes.append("完整的答复方案文档")

        return outcomes


# 全局单例
_plan_generator_instance: AnalysisPlanGenerator | None = None


def get_analysis_plan_generator() -> AnalysisPlanGenerator:
    """获取计划生成器单例"""
    global _plan_generator_instance
    if _plan_generator_instance is None:
        _plan_generator_instance = AnalysisPlanGenerator()
    return _plan_generator_instance


# 测试代码
async def main():
    """测试计划生成器"""

    print("\n" + "=" * 70)
    print("🎯 分析计划生成器测试")
    print("=" * 70 + "\n")

    generator = get_analysis_plan_generator()

    # 模拟测试数据
    examination_opinions = [
        {
            "opinion_type": "权利要求不支持问题",
            "target_claims": ["2", "4-8"],
            "legal_articles": [
                {
                    "law_name": "专利法",
                    "article_number": "第26条第4款",
                    "full_reference": "专利法第26条第4款",
                    "description": "权利要求应当以说明书为依据",
                }
            ],
            "issue_description": "权利要求2、4-8不符合专利法第26条第4款规定...",
        },
        {
            "opinion_type": "新颖性/创造性问题",
            "target_claims": ["1"],
            "legal_articles": [
                {
                    "law_name": "专利法",
                    "article_number": "第22条第2款",
                    "full_reference": "专利法第22条第2款",
                    "description": "新颖性",
                },
                {
                    "law_name": "专利法",
                    "article_number": "第22条第3款",
                    "full_reference": "专利法第22条第3款",
                    "description": "创造性",
                },
            ],
            "issue_description": "权利要求1不具备新颖性和创造性...",
        },
    ]

    # 生成计划
    plan = generator.generate_plan(
        target_application_number="CN202310000001.X",
        target_patent_title="基于深度学习的图像识别方法",
        examination_opinions=examination_opinions,
        prior_art_count=2,
    )

    # 输出计划
    print(plan.to_markdown())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
