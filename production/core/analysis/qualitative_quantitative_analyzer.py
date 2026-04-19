#!/usr/bin/env python3
"""
定性定量结合分析器
Qualitative-Quantitative Integrated Analyzer

基于钱学森系统工程思想,实现定性与定量相结合的分析方法:
- 定性分析:专家规则、法律知识、LLM理解
- 定量分析:向量检索、知识图谱、统计分析
- 综合集成:决策逻辑、置信度计算、可解释性

作者: 小诺·双鱼公主
创建时间: 2025-12-23
版本: v1.0.0 "定性定量结合"
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ConfidenceLevel(Enum):
    """置信度等级"""

    VERY_LOW = (0, 0.3, "很低")
    LOW = (0.3, 0.5, "低")
    MEDIUM = (0.5, 0.7, "中等")
    HIGH = (0.7, 0.9, "高")
    VERY_HIGH = (0.9, 1.0, "很高")

    def __init__(self, min_val: float, max_val: float, label: str):
        self.min_val = min_val
        self.max_val = max_val
        self.label = label


@dataclass
class QualitativeResult:
    """定性分析结果"""

    has_inventiveness: bool
    novelty_level: str  # 高/中/低
    creativity_level: str  # 高/中/低
    legal_risk: str  # 高/中/低
    commercial_value: str  # 高/中/低
    reasoning: str
    confidence: float = 0.7
    key_factors: list[str] = field(default_factory=list)


@dataclass
class QuantitativeResult:
    """定量分析结果"""

    similar_patents: list[dict]
    max_similarity: float
    avg_similarity: float
    citation_count: int
    family_size: int
    legal_status_stats: dict
    market_data: dict
    confidence: float = 0.8


@dataclass
class IntegratedAnalysis:
    """综合分析结果"""

    conclusion: str  # patentable / not_patentable / risky
    decision_basis: str  # qualitative_dominant / quantitative_dominant / balanced
    confidence: float
    recommendation: str
    reasoning: str
    qualitative: QualitativeResult
    quantitative: QuantitativeResult
    action_items: list[str] = field(default_factory=list)


class QualitativeAnalyzer:
    """定性分析器(专家规则)"""

    def __init__(self):
        """初始化定性分析器"""
        # 专家规则库
        self.expert_rules = {
            # 可专利客体判断
            "subject_matter": {
                "ineligible": [
                    "纯抽象思想",
                    "数学公式本身",
                    "商业方法本身",
                    "自然规律",
                    "智力活动规则",
                ],
                "eligible_indicators": ["技术方案", "解决技术问题", "产生技术效果", "采用技术手段"],
            },
            # 创造性指标
            "inventiveness": {
                "high_indicators": [
                    "突破性技术",
                    "解决长期难题",
                    "预料不到的效果",
                    "克服技术偏见",
                    "开创性应用",
                ],
                "medium_indicators": ["改进型技术", "优化现有方案", "提高效率", "降低成本"],
                "low_indicators": ["简单组合", "常规替换", "显而易见"],
            },
            # 法律风险指标
            "legal_risk": {
                "high_indicators": ["存在大量相似专利", "核心技术被覆盖", "规避空间小"],
                "medium_indicators": ["部分相似", "存在差异化可能"],
                "low_indicators": ["技术领域差异大", "实现方式不同"],
            },
        }

    def analyze(self, patent_text: str, title: str = "") -> QualitativeResult:
        """
        定性分析

        Args:
            patent_text: 专利文本
            title: 专利标题

        Returns:
            定性分析结果
        """
        logger.info("🧠 开始定性分析...")

        # 1. 技术领域判断
        subject_matter_result = self._check_subject_matter(patent_text)
        if not subject_matter_result["eligible"]:
            return QualitativeResult(
                has_inventiveness=False,
                novelty_level="不适用",
                creativity_level="不适用",
                legal_risk="不适用",
                commercial_value="不适用",
                reasoning=subject_matter_result["reason"],
                confidence=0.95,
                key_factors=["不属于专利保护客体"],
            )

        # 2. 创造性评估
        inventiveness_result = self._assess_inventiveness(patent_text, title)

        # 3. 法律风险评估
        legal_risk_result = self._assess_legal_risk(patent_text)

        # 4. 商业价值评估
        commercial_value = self._assess_commercial_value(patent_text, title)

        # 综合判断
        has_inventiveness = inventiveness_result["level"] in ["高", "中"]

        return QualitativeResult(
            has_inventiveness=has_inventiveness,
            novelty_level=inventiveness_result.get("novelty", "中"),
            creativity_level=inventiveness_result["level"],
            legal_risk=legal_risk_result["level"],
            commercial_value=commercial_value["level"],
            reasoning=self._generate_qualitative_reasoning(
                inventiveness_result, legal_risk_result, commercial_value
            ),
            confidence=0.75,
            key_factors=inventiveness_result.get("factors", []),
        )

    def _check_subject_matter(self, text: str) -> dict:
        """检查是否属于可专利客体"""
        text.lower()

        # 检查 ineligible 指标
        for ineligible in self.expert_rules["subject_matter"]["ineligible"]:
            if ineligible in text:
                return {"eligible": False, "reason": f"属于{ineligible},不属于专利保护客体"}

        # 检查 eligible 指标
        eligible_count = 0
        for indicator in self.expert_rules["subject_matter"]["eligible_indicators"]:
            if indicator in text:
                eligible_count += 1

        if eligible_count >= 2:
            return {"eligible": True, "reason": "属于技术方案,符合专利保护客体要求"}
        else:
            return {"eligible": True, "reason": "初步判断属于可专利客体,需进一步分析"}

    def _assess_inventiveness(self, text: str, title: str) -> dict:
        """评估创造性"""
        score = 0
        factors = []

        # 高创造性指标
        for indicator in self.expert_rules["inventiveness"]["high_indicators"]:
            if indicator in text or indicator in title:
                score += 3
                factors.append(f"发现高创造性指标: {indicator}")

        # 中等创造性指标
        for indicator in self.expert_rules["inventiveness"]["medium_indicators"]:
            if indicator in text:
                score += 1
                factors.append(f"发现中等创造性指标: {indicator}")

        # 低创造性指标(减分)
        for indicator in self.expert_rules["inventiveness"]["low_indicators"]:
            if indicator in text:
                score -= 1
                factors.append(f"发现低创造性信号: {indicator}")

        # 判断等级
        if score >= 3:
            level = "高"
            novelty = "高"
        elif score >= 1:
            level = "中"
            novelty = "中"
        else:
            level = "低"
            novelty = "低"

        return {"level": level, "novelty": novelty, "score": score, "factors": factors}

    def _assess_legal_risk(self, text: str) -> dict:
        """评估法律风险"""
        # 简化实现:基于关键词判断
        high_risk_keywords = ["现有技术", "公知常识", "常规手段"]
        low_risk_keywords = ["独特", "创新", "首次", "原创"]

        high_count = sum(1 for kw in high_risk_keywords if kw in text)
        low_count = sum(1 for kw in low_risk_keywords if kw in text)

        if high_count > low_count + 1:
            level = "高"
        elif low_count > high_count + 1:
            level = "低"
        else:
            level = "中"

        return {"level": level}

    def _assess_commercial_value(self, text: str, title: str) -> dict:
        """评估商业价值"""
        # 简化实现
        high_value_keywords = ["市场", "产业", "应用", "效益"]
        value_count = sum(1 for kw in high_value_keywords if kw in text or kw in title)

        if value_count >= 3:
            level = "高"
        elif value_count >= 1:
            level = "中"
        else:
            level = "低"

        return {"level": level}

    def _generate_qualitative_reasoning(
        self, inventiveness: dict, legal_risk: dict, commercial: dict
    ) -> str:
        """生成定性分析推理"""
        reasoning = "[定性分析]\n"
        reasoning += f"创造性的:{inventiveness['level']}({inventiveness['score']}分)\n"
        reasoning += f"法律风险:{legal_risk['level']}\n"
        reasoning += f"商业价值:{commercial['level']}\n"

        if inventiveness.get("factors"):
            reasoning += "\n关键因素:\n"
            for factor in inventiveness["factors"]:
                reasoning += f"  • {factor}\n"

        return reasoning


class QuantitativeAnalyzer:
    """定量分析器(数据驱动)"""

    def __init__(self):
        """初始化定量分析器"""
        # 这里应该连接真实的向量库、知识图谱等
        # 目前使用模拟数据
        self.mock_data = True

    async def analyze(self, patent_text: str, title: str = "") -> QuantitativeResult:
        """
        定量分析

        Args:
            patent_text: 专利文本
            title: 专利标题

        Returns:
            定量分析结果
        """
        logger.info("📊 开始定量分析...")

        if self.mock_data:
            return self._mock_analyze(patent_text, title)
        else:
            return await self._real_analyze(patent_text, title)

    def _mock_analyze(self, text: str, title: str) -> QuantitativeResult:
        """模拟定量分析(用于测试)"""
        # 基于文本长度和关键词生成模拟数据
        text_length = len(text)

        # 模拟相似专利
        mock_similar_patents = [
            {
                "id": "CN123456789A",
                "title": "相似的专利技术方案",
                "similarity": min(0.85, 0.5 + text_length / 10000),
                "legal_status": "有效",
            },
            {
                "id": "US9876543B2",
                "title": "相关美国专利",
                "similarity": min(0.75, 0.4 + text_length / 12000),
                "legal_status": "有效",
            },
        ]

        max_similarity = max(p["similarity"] for p in mock_similar_patents)
        avg_similarity = sum(p["similarity"] for p in mock_similar_patents) / len(
            mock_similar_patents
        )

        return QuantitativeResult(
            similar_patents=mock_similar_patents,
            max_similarity=max_similarity,
            avg_similarity=avg_similarity,
            citation_count=5,
            family_size=3,
            legal_status_stats={"active": 0.7, "expired": 0.2, "invalidated": 0.1},
            market_data={"related_products": 10, "market_size": "中等"},
            confidence=0.8,
        )

    async def _real_analyze(self, text: str, title: str) -> QuantitativeResult:
        """真实的定量分析(连接实际数据源)"""
        # TODO: 实现真实的向量检索、知识图谱分析等
        # 1. 向量检索相似专利
        # 2. 知识图谱分析引证关系
        # 3. 统计分析法律状态
        # 4. 市场数据分析

        raise NotImplementedError("真实定量分析待实现")


class QualitativeQuantitativeIntegrator:
    """定性定量综合集成器"""

    def __init__(self):
        """初始化综合集成器"""
        self.qualitative_analyzer = QualitativeAnalyzer()
        self.quantitative_analyzer = QuantitativeAnalyzer()

    async def analyze_patent(self, patent_text: str, title: str = "") -> IntegratedAnalysis:
        """
        专利综合分析(定性定量结合)

        Args:
            patent_text: 专利文本
            title: 专利标题

        Returns:
            综合分析结果
        """
        logger.info("🔄 开始综合分析(定性定量结合)...")

        # 1. 定性分析
        qualitative = self.qualitative_analyzer.analyze(patent_text, title)

        # 2. 定量分析
        quantitative = await self.quantitative_analyzer.analyze(patent_text, title)

        # 3. 综合集成
        integrated = self._integrate(qualitative, quantitative)

        logger.info(f"✅ 综合分析完成:{integrated.conclusion}")

        return integrated

    def _integrate(
        self, qualitative: QualitativeResult, quantitative: QuantitativeResult
    ) -> IntegratedAnalysis:
        """
        综合集成逻辑

        核心思想:
        - 定性为大方向(专家规则判断基础可行性)
        - 定量为精细化(数据验证和风险预警)
        - 结合得出最终结论
        """
        # 第一步:检查定性基础判断
        if not qualitative.has_inventiveness:
            return IntegratedAnalysis(
                conclusion="not_patentable",
                decision_basis="qualitative_dominant",
                confidence=qualitative.confidence,
                recommendation="不建议申请专利,缺乏创造性",
                reasoning=f"[定性判断]{qualitative.reasoning}\n定性分析认为缺乏创造性,不建议继续。",
                qualitative=qualitative,
                quantitative=quantitative,
                action_items=["重新评估技术方案", "考虑增加创新点"],
            )

        # 第二步:基于定量数据精细化判断
        max_sim = quantitative.max_similarity

        if max_sim > 0.9:
            # 极高相似度,风险高
            return IntegratedAnalysis(
                conclusion="risky",
                decision_basis="quantitative_dominant",
                confidence=0.75,
                recommendation="存在高度相似专利,强烈建议进行规避设计",
                reasoning=f"[综合判断]\n"
                f"定性分析认为有创造性({qualitative.creativity_level}),\n"
                f"但定量分析发现存在{max_sim:.1%}相似度的专利,风险较高。",
                qualitative=qualitative,
                quantitative=quantitative,
                action_items=[
                    "详细分析相似专利的权利要求",
                    "寻找差异化特征",
                    "考虑规避设计",
                    "评估改本申请的可行性",
                ],
            )

        elif max_sim > 0.75:
            # 中等相似度,需要结合定性判断
            if qualitative.creativity_level == "高":
                return IntegratedAnalysis(
                    conclusion="patentable_with_modification",
                    decision_basis="balanced",
                    confidence=0.70,
                    recommendation="存在相似专利,但创造性较高,建议优化权利要求",
                    reasoning=f"[综合判断]\n"
                    f"定性分析:创造性{qualitative.creativity_level},具备专利性基础\n"
                    f"定量分析:存在{max_sim:.1%}相似专利,需注意区分\n"
                    f"综合建议:通过优化权利要求突出创新点",
                    qualitative=qualitative,
                    quantitative=quantitative,
                    action_items=[
                        "优化权利要求,突出核心创新点",
                        "增加技术特征描述",
                        "考虑从属权利要求的布局",
                    ],
                )
            else:
                return IntegratedAnalysis(
                    conclusion="risky",
                    decision_basis="balanced",
                    confidence=0.65,
                    recommendation="存在相似专利,且创造性评估为中等,建议谨慎",
                    reasoning=f"[综合判断]\n"
                    f"定性分析:创造性{qualitative.creativity_level}\n"
                    f"定量分析:存在{max_sim:.1%}相似专利\n"
                    f"综合判断:风险中等偏高,建议补充技术特征",
                    qualitative=qualitative,
                    quantitative=quantitative,
                    action_items=["补充技术特征", "考虑替代方案", "评估规避可能性"],
                )

        else:
            # 低相似度,定性判断占主导
            return IntegratedAnalysis(
                conclusion="patentable",
                decision_basis="qualitative_dominant",
                confidence=0.85,
                recommendation="相似度较低且具备创造性,建议申请专利",
                reasoning=f"[综合判断]\n"
                f"定性分析:具备{qualitative.creativity_level}创造性\n"
                f"定量分析:最高相似度{max_sim:.1%},处于安全范围\n"
                f"综合结论:具备可专利性,建议申请",
                qualitative=qualitative,
                quantitative=quantitative,
                action_items=["准备专利申请文件", "完善技术交底书", "考虑国际布局"],
            )

    def generate_report(self, analysis: IntegratedAnalysis) -> str:
        """生成可读的分析报告"""
        report = f"""
╔════════════════════════════════════════════════════════════╗
║              专利定性定量综合分析报告                          ║
╚════════════════════════════════════════════════════════════╝

📊 分析概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   结论:{analysis.conclusion}
   置信度:{analysis.confidence:.1%}
   决策依据:{analysis.decision_basis}

📋 建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   {analysis.recommendation}

🧠 定性分析(专家规则)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   创造性:{analysis.qualitative.creativity_level}
   新颖性:{analysis.qualitative.novelty_level}
   法律风险:{analysis.qualitative.legal_risk}
   商业价值:{analysis.qualitative.commercial_value}

{analysis.qualitative.reasoning}

📊 定量分析(数据支撑)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   相似专利数:{len(analysis.quantitative.similar_patents)} 件
   最高相似度:{analysis.quantitative.max_similarity:.1%}
   平均相似度:{analysis.quantitative.avg_similarity:.1%}
   引证次数:{analysis.quantitative.citation_count}
   同族数量:{analysis.quantitative.family_size}

   最相似的专利:
"""
        for patent in analysis.quantitative.similar_patents[:3]:
            report += f"   • {patent['id']} ({patent['similarity']:.1%}): {patent['title']}\n"

        report += f"""
🔄 综合推理
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{analysis.reasoning}

✅ 行动建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for i, action in enumerate(analysis.action_items, 1):
            report += f"   {i}. {action}\n"

        return report


# 全局单例
_integrator_instance = None


def get_qualitative_quantitative_integrator() -> QualitativeQuantitativeIntegrator:
    """获取定性定量综合集成器单例"""
    global _integrator_instance
    if _integrator_instance is None:
        _integrator_instance = QualitativeQuantitativeIntegrator()
    return _integrator_instance


# 测试代码
async def main():
    """测试定性定量结合分析"""

    print("\n" + "=" * 60)
    print("🔬 定性定量结合分析测试")
    print("=" * 60 + "\n")

    integrator = get_qualitative_quantitative_integrator()

    # 测试案例1:高创造性专利
    print("📝 测试案例1:高创造性专利")
    patent_1 = """
    本发明涉及一种基于深度学习的专利检索方法,
    通过引入多模态注意力机制和知识图谱增强技术,
    解决了传统专利检索精度低的问题,
    取得了预料不到的技术效果,
    是该领域的突破性技术创新。
    该技术方案可广泛应用于知识产权、科技情报等领域,
    具有重要的商业价值。
    """

    result_1 = await integrator.analyze_patent(patent_1, "基于深度学习的专利检索方法")
    print(integrator.generate_report(result_1))

    # 测试案例2:低创造性专利
    print("\n\n" + "=" * 60)
    print("📝 测试案例2:低创造性专利")
    patent_2 = """
    本发明涉及一种杯子,
    包括杯体和杯盖,
    用于盛放水。
    """

    result_2 = await integrator.analyze_patent(patent_2, "杯子")
    print(integrator.generate_report(result_2))

    print("\n\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
