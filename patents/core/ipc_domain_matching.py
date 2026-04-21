#!/usr/bin/env python3
from __future__ import annotations
"""
IPC技术领域智能匹配系统
IPC Technical Domain Matching System

基于IPC分类的智能技术领域匹配系统:
- 自动识别专利技术领域
- 推荐最佳IPC分类号
- 生成领域分析报告
- 支持专利撰写和分析

作者: 小诺·双鱼公主
创建时间: 2025-12-24
版本: v0.1.2 "晨星初现"
"""

import logging

# 导入相关模块
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from patents.core.ipc_vector_database import IPCClassificationResult, get_ipc_vector_db
from patents.core.negentropy_retrieval import get_negentropy_retrieval_system

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class DomainCategory(Enum):
    """领域类别"""

    SOFTWARE = "software"  # 软件/计算机
    ELECTRONICS = "electronics"  # 电子/通信
    MECHANICAL = "mechanical"  # 机械/制造
    CHEMICAL = "chemical"  # 化学/材料
    BIOTECH = "biotech"  # 生物/医药
    ENERGY = "energy"  # 能源/环保
    MEDICAL = "medical"  # 医疗设备
    AUTOMOTIVE = "automotive"  # 汽车/交通


@dataclass
class DomainRecommendation:
    """领域推荐"""

    domain_name: str  # 领域名称
    category: DomainCategory  # 领域类别
    confidence: float  # 置信度
    matched_ipcs: list[str]  # 匹配的IPC
    key_features: list[str]  # 关键特征
    similar_cases: list[str]  # 相似案例(参考)
    market_insight: str  # 市场洞察


@dataclass
class PatentDomainAnalysis:
    """专利领域分析报告"""

    patent_text: str  # 专利文本摘要
    analysis_time: str  # 分析时间

    # 分类结果
    primary_domain: str  # 主领域
    secondary_domains: list[str]  # 次要领域

    # IPC分类
    primary_ipc: str  # 主IPC分类
    recommended_ipcs: list[str]  # 推荐IPC列表

    # 领域推荐
    domain_recommendations: list[DomainRecommendation]

    # 技术特征
    technical_keywords: list[str]  # 技术关键词
    innovation_level: str  # 创新级别(高/中/低)

    # 市场/法律建议
    market_potential: str  # 市场潜力
    legal_considerations: list[str]  # 法律考虑因素

    # 置信度
    overall_confidence: float  # 总体置信度


class IPCDomainMatchingSystem:
    """
    IPC技术领域智能匹配系统

    核心功能:
    1. 自动识别专利技术领域
    2. 推荐最佳IPC分类号
    3. 生成领域分析报告
    4. 支持专利撰写和分析
    """

    def __init__(self):
        """初始化系统"""
        self.name = "IPC技术领域智能匹配系统"
        self.version = "v0.1.2"

        # 子系统
        self.ipc_db = get_ipc_vector_db()
        self.retrieval_system = get_negentropy_retrieval_system()

        # 领域知识库
        self.domain_knowledge = self._init_domain_knowledge()

        logger.info(f"🎯 {self.name} ({self.version}) 初始化完成")

    def _init_domain_knowledge(self) -> dict[str, Any]:
        """初始化领域知识库"""
        return {
            "software": {
                "primary_ipcs": ["G06F", "G06N", "G06Q", "G06K"],
                "keywords": ["软件", "算法", "数据处理", "计算机", "人工智能", "机器学习"],
                "market_potential": "高",
                "growth_rate": "15-20%/年",
                "key_players": ["腾讯", "阿里巴巴", "华为", "字节跳动"],
            },
            "electronics": {
                "primary_ipcs": ["H01", "H03", "H04", "H05"],
                "keywords": ["电路", "芯片", "半导体", "电子", "通信", "5G"],
                "market_potential": "高",
                "growth_rate": "10-15%/年",
                "key_players": ["华为", "中兴", "小米", "OPPO"],
            },
            "biotech": {
                "primary_ipcs": ["C12N", "C07K", "A01H", "C12Q"],
                "keywords": ["基因", "蛋白质", "生物", "医疗", "诊断", "疫苗"],
                "market_potential": "非常高",
                "growth_rate": "20-30%/年",
                "key_players": ["药明康德", "恒瑞医药", "百济神州"],
            },
            "automotive": {
                "primary_ipcs": ["B60", "B62", "F02P"],
                "keywords": ["汽车", "车辆", "驾驶", "新能源", "自动驾驶"],
                "market_potential": "中高",
                "growth_rate": "10-12%/年",
                "key_players": ["比亚迪", "蔚来", "小鹏", "理想"],
            },
            "mechanical": {
                "primary_ipcs": ["B23", "B25", "F16"],
                "keywords": ["机械", "制造", "加工", "设备", "自动化"],
                "market_potential": "中",
                "growth_rate": "5-8%/年",
                "key_players": ["三一重工", "中联重科", "沈阳机床"],
            },
        }

    async def analyze_patent_domain(
        self, patent_text: str, patent_title: str = ""
    ) -> PatentDomainAnalysis:
        """
        分析专利技术领域

        Args:
            patent_text: 专利文本
            patent_title: 专利标题(可选)

        Returns:
            领域分析报告
        """
        # 组合文本
        full_text = f"{patent_title} {patent_text}".strip()

        # 1. IPC分类
        ipc_classification = self.ipc_db.classify_patent(full_text)

        # 2. 领域识别
        primary_domain, secondary_domains = self._identify_domains(full_text, ipc_classification)

        # 3. 生成领域推荐
        recommendations = self._generate_recommendations(
            full_text, ipc_classification, primary_domain
        )

        # 4. 提取技术关键词
        technical_keywords = self._extract_technical_keywords(full_text)

        # 5. 评估创新级别
        innovation_level = self._assess_innovation_level(full_text, ipc_classification)

        # 6. 市场潜力分析
        market_potential = self._analyze_market_potential(primary_domain, ipc_classification)

        # 7. 法律考虑因素
        legal_considerations = self._generate_legal_considerations(ipc_classification)

        # 8. 计算总体置信度
        overall_confidence = ipc_classification.confidence

        return PatentDomainAnalysis(
            patent_text=patent_text[:200],
            analysis_time=datetime.now().isoformat(),
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            primary_ipc=ipc_classification.primary_classification,
            recommended_ipcs=[m.ipc_entry.ipc_code for m in ipc_classification.matched_ipcs[:5]],
            domain_recommendations=recommendations,
            technical_keywords=technical_keywords[:10],
            innovation_level=innovation_level,
            market_potential=market_potential,
            legal_considerations=legal_considerations,
            overall_confidence=overall_confidence,
        )

    def _identify_domains(
        self, text: str, ipc_classification: IPCClassificationResult
    ) -> tuple[str, list[str]]:
        """识别技术领域"""
        # 基于IPC分类匹配领域
        domain_scores = Counter()

        # 从IPC匹配结果中统计
        for match in ipc_classification.matched_ipcs:
            ipc_code = match.ipc_entry.ipc_code

            # 匹配领域知识库
            for domain, knowledge in self.domain_knowledge.items():
                if ipc_code in knowledge["primary_ipcs"]:
                    domain_scores[domain] += match.similarity_score * 2

                # 关键词匹配
                for keyword in knowledge["keywords"]:
                    if keyword.lower() in text.lower():
                        domain_scores[domain] += 0.3

        # 确定主领域和次要领域
        if domain_scores:
            primary = domain_scores.most_common(1)[0][0]
            secondary = [d for d, _ in domain_scores.most_common(5)[1:] if domain_scores[d] > 0.3]
        else:
            primary = "综合技术"
            secondary = ipc_classification.domain_suggestions

        return primary, secondary

    def _generate_recommendations(
        self, text: str, ipc_classification: IPCClassificationResult, primary_domain: str
    ) -> list[DomainRecommendation]:
        """生成领域推荐"""
        recommendations = []

        # 主领域推荐
        if primary_domain in self.domain_knowledge:
            knowledge = self.domain_knowledge[primary_domain]

            # 找到匹配的IPC
            matched_ipcs = [
                m.ipc_entry.ipc_code
                for m in ipc_classification.matched_ipcs
                if any(ipc in m.ipc_entry.ipc_code for ipc in knowledge["primary_ipcs"])
            ]

            recommendations.append(
                DomainRecommendation(
                    domain_name=primary_domain,
                    category=(
                        DomainCategory.SOFTWARE
                        if primary_domain == "software"
                        else DomainCategory.MECHANICAL
                    ),
                    confidence=ipc_classification.confidence,
                    matched_ipcs=matched_ipcs,
                    key_features=knowledge["keywords"][:5],
                    similar_cases=[],
                    market_insight=f"市场潜力{knowledge['market_potential']},年增长率{knowledge.get('growth_rate', 'N/A')}",
                )
            )

        # 次要领域推荐(基于IPC分类)
        for domain in ipc_classification.domain_suggestions[:3]:
            if domain != primary_domain and domain in self.domain_knowledge:
                knowledge = self.domain_knowledge[domain]
                recommendations.append(
                    DomainRecommendation(
                        domain_name=domain,
                        category=(
                            DomainCategory.SOFTWARE
                            if domain == "software"
                            else DomainCategory.MECHANICAL
                        ),
                        confidence=ipc_classification.confidence * 0.7,
                        matched_ipcs=knowledge["primary_ipcs"],
                        key_features=knowledge["keywords"][:3],
                        similar_cases=[],
                        market_insight=f"相关领域: {knowledge.get('market_potential', 'N/A')}",
                    )
                )

        return recommendations

    def _extract_technical_keywords(self, text: str) -> list[str]:
        """提取技术关键词"""
        # 简化实现:基于常见技术关键词
        tech_keywords = []

        # 从领域知识库中收集关键词
        for knowledge in self.domain_knowledge.values():
            for keyword in knowledge["keywords"]:
                if keyword.lower() in text.lower() and keyword not in tech_keywords:
                    tech_keywords.append(keyword)

        # 从IPC匹配中提取
        if hasattr(self, "last_ipc_matches"):
            for match in getattr(self, "last_ipc_matches", []):
                tech_keywords.extend(match.ipc_entry.keywords[:3])

        return tech_keywords

    def _assess_innovation_level(
        self, text: str, ipc_classification: IPCClassificationResult
    ) -> str:
        """评估创新级别"""
        # 基于IPC分类和负熵分数
        if ipc_classification.negentropy_score < 0.3:
            return "高"
        elif ipc_classification.negentropy_score < 0.6:
            return "中"
        else:
            return "低"

    def _analyze_market_potential(
        self, primary_domain: str, ipc_classification: IPCClassificationResult
    ) -> str:
        """分析市场潜力"""
        if primary_domain in self.domain_knowledge:
            knowledge = self.domain_knowledge[primary_domain]
            return f"{knowledge['market_potential']}潜力"
        return "中等"

    def _generate_legal_considerations(
        self, ipc_classification: IPCClassificationResult
    ) -> list[str]:
        """生成法律考虑因素"""
        considerations = []

        # 基于IPC分类生成建议
        primary_ipc = ipc_classification.primary_classification

        if primary_ipc.startswith("G06"):
            considerations.append("软件相关:注意考虑方法专利vs产品专利的选择")
            considerations.append("建议进行软件著作权登记作为补充保护")

        elif primary_ipc.startswith("A61"):
            considerations.append("医疗相关:注意临床试验数据的充分性")
            considerations.append("建议关注医疗器械注册要求")

        elif primary_ipc.startswith("H04"):
            considerations.append("通信技术:注意标准必要专利(SEP)的潜在问题")
            considerations.append("建议进行专利池分析")

        elif primary_ipc.startswith("C12"):
            considerations.append("生物技术:注意生物材料的保藏要求")
            considerations.append("建议充分公开实验数据")

        # 通用建议
        if ipc_classification.confidence < 0.7:
            considerations.append("分类置信度较低,建议进一步细分IPC分类")

        if len(ipc_classification.secondary_classifications) > 2:
            considerations.append("涉及多个IPC分类,建议考虑多件专利申请")

        return considerations

    def format_analysis_report(self, analysis: PatentDomainAnalysis) -> str:
        """格式化分析报告"""
        lines = []

        lines.append("=" * 60)
        lines.append("🎯 IPC技术领域分析报告")
        lines.append("=" * 60)
        lines.append(f"分析时间: {analysis.analysis_time}")
        lines.append("")

        lines.append("[技术领域识别]")
        lines.append(f"主领域: {analysis.primary_domain}")
        lines.append(f"次要领域: {', '.join(analysis.secondary_domains)}")
        lines.append("")

        lines.append("[IPC分类推荐]")
        lines.append(f"主IPC: {analysis.primary_ipc}")
        lines.append("推荐IPC:")
        for ipc in analysis.recommended_ipcs[:5]:
            lines.append(f"  • {ipc}")
        lines.append("")

        lines.append("[领域推荐]")
        for rec in analysis.domain_recommendations[:3]:
            lines.append(f"• {rec.domain_name}: {rec.market_insight}")
            lines.append(f"  匹配IPC: {', '.join(rec.matched_ipcs[:3])}")
            lines.append(f"  置信度: {rec.confidence:.1%}")
        lines.append("")

        lines.append("[技术特征]")
        lines.append(f"创新级别: {analysis.innovation_level}")
        lines.append(f"技术关键词: {', '.join(analysis.technical_keywords[:8])}")
        lines.append("")

        lines.append("[法律建议]")
        for consideration in analysis.legal_considerations:
            lines.append(f"• {consideration}")
        lines.append("")

        lines.append(f"总体置信度: {analysis.overall_confidence:.1%}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_domain_statistics(self) -> dict[str, Any]:
        """获取领域统计信息"""
        return {
            "total_domains": len(self.domain_knowledge),
            "supported_domains": list(self.domain_knowledge.keys()),
            "database_status": "ready" if self.ipc_db.is_loaded else "not_loaded",
        }


# 全局单例
_ipc_domain_system_instance = None


def get_ipc_domain_system() -> IPCDomainMatchingSystem:
    """获取IPC领域匹配系统单例"""
    global _ipc_domain_system_instance
    if _ipc_domain_system_instance is None:
        _ipc_domain_system_instance = IPCDomainMatchingSystem()
    return _ipc_domain_system_instance


# 测试代码
async def main():
    """测试IPC领域匹配系统"""

    print("\n" + "=" * 60)
    print("🎯 IPC技术领域智能匹配系统测试")
    print("=" * 60 + "\n")

    system = get_ipc_domain_system()

    # 测试:分析一个AI专利
    print("📝 测试: AI专利领域分析")
    patent_text = """
    本发明公开了一种基于注意力机制的自然语言处理方法,
    属于人工智能和计算机软件技术领域。该方法包括:
    1. 使用Transformer架构进行文本编码;
    2. 引入多头自注意力机制捕获长距离依赖;
    3. 使用预训练语言模型进行微调;
    应用于智能问答、文本分类等场景。
    """

    analysis = await system.analyze_patent_domain(
        patent_text=patent_text, patent_title="基于注意力机制的自然语言处理方法"
    )

    print(system.format_analysis_report(analysis))

    print("\n✅ 测试完成!")


# 入口点: @async_main装饰器已添加到main函数
