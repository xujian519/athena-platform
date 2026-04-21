from __future__ import annotations
"""
NPE专利风险检测器

基于论文#20《Predicting Patent Quality》
- NPE专利中55%是"坏专利"
- 宽泛权利要求、模糊技术特征是高风险指标

作者: 小娜·天秤女神
创建时间: 2026-03-20
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class NPERiskAssessment:
    """NPE风险评估结果"""
    risk_level: str  # low/medium/high
    risk_score: float  # 0-1
    claim_risk_indicators: list[str] = field(default_factory=list)
    technology_risk_factors: list[str] = field(default_factory=list)
    mitigation_suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "claim_risk_indicators": self.claim_risk_indicators,
            "technology_risk_factors": self.technology_risk_factors,
            "mitigation_suggestions": self.mitigation_suggestions,
        }


class NPERiskDetector:
    """
    NPE (Non-Practicing Entity) 专利风险检测器

    基于论文#20的关键发现:
    - NPE专利中55%是"坏专利"
    - 高风险特征: 宽泛权利要求、模糊技术特征、软件/商业方法

    检测维度:
    1. 权利要求宽泛度
    2. 技术特征清晰度
    3. 技术领域风险
    4. 引用模式分析
    """

    # NPE高风险关键词
    NPE_INDICATORS = [
        "计算机实现的方法",
        "系统",
        "计算机程序产品",
        "存储介质",
        "网络",
        "数据处理",
        "一种方法",
        "一种系统",
        "其中所述",
    ]

    # NPE专利常见权利要求模式
    NPE_CLAIM_PATTERNS = [
        "一种...方法，包括:",
        "一种...系统，包括:",
        "一种计算机程序产品",
        "一种存储介质",
        "一种计算机实现的",
    ]

    # 高风险技术领域
    HIGH_RISK_TECH_AREAS = [
        ("G06F", "数据处理"),
        ("G06Q", "商业方法"),
        ("G06N", "人工智能"),
        ("H04L", "通信网络"),
    ]

    def __init__(self):
        self.name = "NPE风险检测器"
        self.logger = logging.getLogger(self.name)

    async def detect(
        self,
        claims: list[str],
        assignee_type: str = "unknown",
        citations: list[dict] | None = None,
    ) -> NPERiskAssessment:
        """
        检测NPE专利风险

        Args:
            claims: 权利要求列表
            assignee_type: 权利人类型
            citations: 引用数据

        Returns:
            NPERiskAssessment: 风险评估结果
        """
        # 1. 分析权利要求风险
        claim_risk = self._analyze_claim_risk(claims)

        # 2. 分析技术领域风险
        tech_risk = self._analyze_technology_risk(claims)

        # 3. 分析引用模式 (如果提供)
        citation_risk = 0.0
        if citations:
            citation_risk = self._analyze_citation_pattern(citations)

        # 4. 综合评估
        overall_risk = self._calculate_overall_risk(
            claim_risk,
            tech_risk,
            citation_risk,
            assignee_type,
        )

        # 5. 生成缓解建议
        suggestions = self._generate_mitigation_suggestions(
            claim_risk,
            tech_risk,
        )

        return NPERiskAssessment(
            risk_level=overall_risk["level"],
            risk_score=overall_risk["score"],
            claim_risk_indicators=claim_risk["indicators"],
            technology_risk_factors=tech_risk["factors"],
            mitigation_suggestions=suggestions,
        )

    def _analyze_claim_risk(self, claims: list[str]) -> dict:
        """分析权利要求风险"""
        indicators = []
        risk_score = 0.0

        claim_text = " ".join(claims).lower()

        # 检测NPE典型模式
        for pattern in self.NPE_CLAIM_PATTERNS:
            pattern_lower = pattern.lower().replace("...", "")
            if pattern_lower in claim_text or self._fuzzy_match_pattern(claim_text, pattern):
                indicators.append(f"发现NPE典型模式: {pattern[:15]}...")
                risk_score += 0.15

        # 检查权利要求宽度
        for i, claim in enumerate(claims[:3]):  # 检查前3个权利要求
            if self._is_broad_claim(claim):
                indicators.append(f"权利要求{i+1}可能过于宽泛")
                risk_score += 0.10

        # 检查技术特征清晰度
        vague_features = self._check_vague_features(claim_text)
        if vague_features:
            indicators.append(f"技术特征描述模糊: {', '.join(vague_features[:3])}")
            risk_score += 0.10

        # 检查限定词密度
        qualifier_density = self._calculate_qualifier_density(claims)
        if qualifier_density < 0.3:
            indicators.append("限定词密度低，权利要求可能过宽")
            risk_score += 0.10

        return {
            "indicators": list(dict.fromkeys(indicators))[:5],
            "score": min(1.0, risk_score),
        }

    def _analyze_technology_risk(self, claims: list[str]) -> dict:
        """分析技术领域风险"""
        factors = []
        risk_score = 0.0

        claim_text = " ".join(claims).lower()

        # 软件相关
        software_keywords = ["计算机", "程序", "软件", "算法", "数据处理", "存储"]
        if any(kw in claim_text for kw in software_keywords):
            factors.append("涉及软件技术")
            risk_score += 0.20

        # 商业方法
        business_keywords = ["商业", "交易", "支付", "管理", "金融", "电子商务"]
        if any(kw in claim_text for kw in business_keywords):
            factors.append("涉及商业方法")
            risk_score += 0.25

        # 通信/网络
        network_keywords = ["网络", "通信", "传输", "协议", "互联网"]
        if any(kw in claim_text for kw in network_keywords):
            factors.append("涉及网络通信")
            risk_score += 0.15

        # AI/ML
        ai_keywords = ["人工智能", "机器学习", "神经网络", "深度学习", "模型"]
        if any(kw in claim_text for kw in ai_keywords):
            factors.append("涉及人工智能技术")
            risk_score += 0.20

        return {
            "factors": factors,
            "score": min(1.0, risk_score),
        }

    def _analyze_citation_pattern(self, citations: list[dict]) -> float:
        """分析引用模式"""
        if not citations:
            return 0.0

        risk_score = 0.0

        # 高引用但非专利引用比例低
        forward_cites = sum(1 for c in citations if c.get("type") == "forward")
        np_cites = sum(1 for c in citations if c.get("is_non_patent", False))

        if forward_cites > 10 and np_cites / len(citations) < 0.1:
            risk_score += 0.10  # 可能是投机性专利

        return risk_score

    def _calculate_overall_risk(
        self,
        claim_risk: dict,
        tech_risk: dict,
        citation_risk: float,
        assignee_type: str,
    ) -> dict:
        """计算综合风险"""
        # 基础评分
        base_score = (
            claim_risk["score"] * 0.5 +
            tech_risk["score"] * 0.3 +
            citation_risk * 0.2
        )

        # 权利人类型加权
        if assignee_type.lower() in ["npe", "non-practicing", "patent_troll", "individual"]:
            base_score = min(1.0, base_score * 1.3)

        # 确定风险等级
        if base_score >= 0.7:
            level = "high"
        elif base_score >= 0.4:
            level = "medium"
        else:
            level = "low"

        return {"level": level, "score": base_score}

    def _generate_mitigation_suggestions(
        self,
        claim_risk: dict,
        tech_risk: dict,
    ) -> list[str]:
        """生成缓解建议"""
        suggestions = []

        if claim_risk["score"] > 0.3:
            suggestions.append("增加具体技术特征限定，避免宽泛表述")
            suggestions.append("使用更精确的技术术语替换模糊描述")

        if tech_risk["score"] > 0.3:
            suggestions.append("强调技术实现的具体细节和创新性")
            suggestions.append("说明技术方案的技术效果和技术进步")

        if claim_risk["score"] > 0.5:
            suggestions.append("考虑缩小保护范围以增加稳定性")

        if not suggestions:
            suggestions.append("保持当前权利要求的清晰度和完整性")

        return list(dict.fromkeys(suggestions))[:5]

    def _is_broad_claim(self, claim: str) -> bool:
        """判断权利要求是否过宽"""
        words = claim.split()
        qualifiers = ["其中", "所述", "包括", "特别是", "尤其是", "具体"]

        # 长度短且限定词少
        if len(words) < 50:
            qualifier_count = sum(1 for q in qualifiers if q in claim)
            if qualifier_count < 2:
                return True

        # 开头过于通用
        generic_starts = ["一种方法", "一种系统", "一种装置"]
        for start in generic_starts:
            if claim.strip().startswith(start) and len(claim) < 200:
                return True

        return False

    def _check_vague_features(self, text: str) -> list[str]:
        """检查模糊技术特征"""
        vague_terms = [
            ("适当的", "应具体说明"),
            ("合适的", "应具体说明"),
            ("等等", "应完整列举"),
            ("例如", "应作为必要特征"),
            ("如", "应明确范围"),
            ("等", "应完整列举"),
            ("多个", "应明确数量范围"),
            ("若干", "应明确数量"),
        ]

        found = []
        for term, suggestion in vague_terms:
            if term in text:
                found.append(f"'{term}'{suggestion}")

        return found

    def _calculate_qualifier_density(self, claims: list[str]) -> float:
        """计算限定词密度"""
        qualifiers = ["其中", "所述", "包括", "包含", "具有", "特别是", "尤其是", "具体"]
        total_words = sum(len(c.split()) for c in claims)

        if total_words == 0:
            return 0.0

        qualifier_count = sum(sum(1 for q in qualifiers if q in c) for c in claims)
        return min(1.0, qualifier_count / (total_words / 50))

    def _fuzzy_match_pattern(self, text: str, pattern: str) -> bool:
        """模糊匹配模式"""
        # 简化实现: 检查关键词
        keywords = pattern.replace("...", "").replace("一种", "").replace("，包括:", "")
        return keywords.lower() in text.lower()


# 便捷函数
def get_npe_risk_detector() -> NPERiskDetector:
    """获取NPE风险检测器实例"""
    return NPERiskDetector()
