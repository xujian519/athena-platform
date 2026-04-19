#!/usr/bin/env python3
"""
扩展领域知识库
Extended Domain Knowledge Base

扩展语义级跨域融合引擎的领域知识库

作者: Athena平台团队
创建时间: 2025-12-31
版本: 1.0.0
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

# 扩展的领域知识库
EXTENDED_DOMAIN_KNOWLEDGE = {
    "finance": {
        "core_concepts": [
            "投资回报率", "风险评估", "资产配置", "现金流",
            "资本结构", "估值模型", "财务分析", "预算管理",
            "成本控制", "收入确认", "审计合规", "财务报表",
            "股权融资", "债务融资", "并购重组", "IPO",
        ],
        "relations": {
            "投资回报率": ["related_to", "风险评估"],
            "现金流": ["influences", "估值模型"],
            "资本结构": ["determines", "财务风险"],
            "资产配置": ["optimizes", "投资组合"],
        },
        "typical_queries": [
            "如何评估投资项目的财务可行性",
            "如何优化公司资本结构",
            "如何进行现金流预测",
            "如何降低财务风险",
        ],
        "cross_domain_links": {
            "patent_law": ["知识产权价值评估", "专利许可收入", "IP质押融资"],
            "business": ["商业模式财务分析", "盈利模式设计", "成本结构优化"],
            "technology": ["技术投资评估", "研发成本控制", "技术ROI分析"],
        },
    },
    "medical": {
        "core_concepts": [
            "临床试验", "药物研发", "医疗器械", "诊断技术",
            "医疗AI", "基因组学", "精准医疗", "远程医疗",
            "医疗影像", "电子病历", "医院管理", "医保支付",
            "药物审批", "医疗器械注册", "医疗法规",
        ],
        "relations": {
            "临床试验": ["validates", "药物疗效"],
            "医疗AI": ["enhances", "诊断准确率"],
            "电子病历": ["improves", "医疗效率"],
            "基因组学": ["enables", "精准医疗"],
        },
        "typical_queries": [
            "如何设计临床试验方案",
            "如何评估医疗AI的临床价值",
            "如何进行医疗器械注册",
            "如何优化医院管理流程",
        ],
        "cross_domain_links": {
            "patent_law": ["医疗专利申请", "诊断方法专利", "药物专利保护"],
            "technology": ["医疗影像AI", "远程医疗技术", "医疗大数据"],
            "business": ["医疗服务商业模式", "医疗产品定价", "医疗保险产品"],
        },
    },
    "education": {
        "core_concepts": [
            "教学设计", "学习评估", "课程开发", "教育技术",
            "在线教育", "个性化学习", "智能辅导", "教育大数据",
            "学习分析", "知识图谱", "教育管理", "师资培训",
            "教育评价", "教育公平", "终身学习",
        ],
        "relations": {
            "个性化学习": ["improves", "学习效果"],
            "教育技术": ["enables", "在线教育"],
            "学习分析": ["informs", "教学优化"],
            "知识图谱": ["structures", "学习内容"],
        },
        "typical_queries": [
            "如何设计个性化学习方案",
            "如何评估学习效果",
            "如何开发在线教育平台",
            "如何进行教育数据分析",
        ],
        "cross_domain_links": {
            "technology": ["教育科技应用", "学习管理系统", "AI教育工具"],
            "business": ["教育商业模式", "在线课程定价", "教育产品营销"],
            "ai_ml": ["智能推荐系统", "学习行为预测", "自动批改系统"],
        },
    },
}

# 扩展的跨域概念映射
EXTENDED_CONCEPT_MAPPINGS = [
    # 专利法律 <-> 金融
    {
        "source_domain": "patent_law",
        "target_domain": "finance",
        "source_concept": "专利许可收入",
        "target_concept": "现金流预测",
        "semantic_similarity": 0.88,
        "mapping_confidence": 0.92,
        "context": "专利许可可以产生持续的现金流，是重要的收入来源",
    },
    {
        "source_domain": "patent_law",
        "target_domain": "finance",
        "source_concept": "专利价值评估",
        "target_concept": "资产估值",
        "semantic_similarity": 0.85,
        "mapping_confidence": 0.90,
        "context": "专利是重要的无形资产，需要专业估值",
    },
    {
        "source_domain": "patent_law",
        "target_domain": "finance",
        "source_concept": "IP质押",
        "target_concept": "债务融资",
        "semantic_similarity": 0.80,
        "mapping_confidence": 0.85,
        "context": "知识产权可以作为融资质押物",
    },

    # 专利法律 <-> 医疗
    {
        "source_domain": "patent_law",
        "target_domain": "medical",
        "source_concept": "药物专利",
        "target_concept": "药物研发",
        "semantic_similarity": 0.90,
        "mapping_confidence": 0.95,
        "context": "药物研发成果需要专利保护",
    },
    {
        "source_domain": "patent_law",
        "target_domain": "medical",
        "source_concept": "诊断方法专利",
        "target_concept": "医疗AI",
        "semantic_similarity": 0.87,
        "mapping_confidence": 0.90,
        "context": "AI诊断技术可以申请方法专利",
    },
    {
        "source_domain": "patent_law",
        "target_domain": "medical",
        "source_concept": "医疗器械专利",
        "target_concept": "医疗器械",
        "semantic_similarity": 0.92,
        "mapping_confidence": 0.93,
        "context": "医疗器械创新需要专利保护",
    },

    # 技术 <-> 金融
    {
        "source_domain": "technology",
        "target_domain": "finance",
        "source_concept": "技术投资",
        "target_concept": "投资回报率",
        "semantic_similarity": 0.82,
        "mapping_confidence": 0.88,
        "context": "技术投资需要评估ROI",
    },
    {
        "source_domain": "technology",
        "target_domain": "finance",
        "source_concept": "研发成本",
        "target_concept": "成本控制",
        "semantic_similarity": 0.78,
        "mapping_confidence": 0.85,
        "context": "研发是重要的成本中心，需要有效控制",
    },
    {
        "source_domain": "technology",
        "target_domain": "finance",
        "source_concept": "技术估值",
        "target_concept": "企业估值",
        "semantic_similarity": 0.85,
        "mapping_confidence": 0.90,
        "context": "核心技术是企业估值的重要组成",
    },

    # 技术 <-> 教育
    {
        "source_domain": "technology",
        "target_domain": "education",
        "source_concept": "教育科技",
        "target_concept": "在线教育",
        "semantic_similarity": 0.90,
        "mapping_confidence": 0.93,
        "context": "教育技术是在线教育的基础",
    },
    {
        "source_domain": "technology",
        "target_domain": "education",
        "source_concept": "学习管理系统",
        "target_concept": "教育管理",
        "semantic_similarity": 0.85,
        "mapping_confidence": 0.88,
        "context": "LMS是教育管理的重要工具",
    },
    {
        "source_domain": "ai_ml",
        "target_domain": "education",
        "source_concept": "智能推荐",
        "target_concept": "个性化学习",
        "semantic_similarity": 0.88,
        "mapping_confidence": 0.90,
        "context": "AI推荐是实现个性化学习的关键技术",
    },

    # 商业 <-> 金融
    {
        "source_domain": "business",
        "target_domain": "finance",
        "source_concept": "商业模式",
        "target_concept": "收入模式",
        "semantic_similarity": 0.92,
        "mapping_confidence": 0.95,
        "context": "商业模式决定了收入来源",
    },
    {
        "source_domain": "business",
        "target_domain": "finance",
        "source_concept": "定价策略",
        "target_concept": "盈利能力",
        "semantic_similarity": 0.85,
        "mapping_confidence": 0.90,
        "context": "定价策略直接影响盈利能力",
    },
    {
        "source_domain": "business",
        "target_domain": "finance",
        "source_concept": "成本结构",
        "target_concept": "成本控制",
        "semantic_similarity": 0.88,
        "mapping_confidence": 0.92,
        "context": "优化成本结构是财务健康的基础",
    },

    # AI/ML <-> 金融
    {
        "source_domain": "ai_ml",
        "target_domain": "finance",
        "source_concept": "量化交易",
        "target_concept": "投资策略",
        "semantic_similarity": 0.90,
        "mapping_confidence": 0.93,
        "context": "AI在量化交易中有广泛应用",
    },
    {
        "source_domain": "ai_ml",
        "target_domain": "finance",
        "source_concept": "风险评估模型",
        "target_concept": "风险控制",
        "semantic_similarity": 0.87,
        "mapping_confidence": 0.90,
        "context": "AI模型可以提升风险评估准确性",
    },
    {
        "source_domain": "ai_ml",
        "target_domain": "finance",
        "source_concept": "信用评分",
        "target_concept": "信贷决策",
        "semantic_similarity": 0.85,
        "mapping_confidence": 0.88,
        "context": "AI信用评分模型辅助信贷决策",
    },

    # 教育 <-> 医疗
    {
        "source_domain": "education",
        "target_domain": "medical",
        "source_concept": "医学教育",
        "target_concept": "医生培训",
        "semantic_similarity": 0.88,
        "mapping_confidence": 0.90,
        "context": "医学教育是医生培训的基础",
    },
    {
        "source_domain": "education",
        "target_domain": "medical",
        "source_concept": "患者教育",
        "target_concept": "健康管理",
        "semantic_similarity": 0.82,
        "mapping_confidence": 0.85,
        "context": "患者教育是健康管理的重要组成部分",
    },
]


def get_extended_domain_knowledge():
    """获取扩展的领域知识"""
    return EXTENDED_DOMAIN_KNOWLEDGE


def get_extended_concept_mappings():
    """获取扩展的概念映射"""
    return EXTENDED_CONCEPT_MAPPINGS


# 应用扩展知识的函数
async def apply_extended_knowledge(fusion_engine):
    """
    将扩展知识应用到融合引擎

    Args:
        fusion_engine: SemanticCrossDomainFusion实例
    """
    from production.core.fusion.semantic_cross_domain_fusion import DomainType

    logger.info("📚 应用扩展的领域知识...")

    # 添加新领域
    new_domains = {
        "finance": DomainType.FINANCE,
        "medical": DomainType.MEDICAL,
        "education": DomainType.EDUCATION,
    }

    # 更新知识库
    for domain_name, domain_type in new_domains.items():
        if domain_name not in fusion_engine.DOMAIN_KNOWLEDGE:
            fusion_engine.DOMAIN_KNOWLEDGE[domain_type] = EXTENDED_DOMAIN_KNOWLEDGE[domain_name]
            logger.info(f"✅ 已添加领域: {domain_name}")

    # 添加概念映射
    from production.core.fusion.semantic_cross_domain_fusion import ConceptMapping

    for mapping_data in EXTENDED_CONCEPT_MAPPINGS:
        # 转换域名
        domain_map = {
            "patent_law": DomainType.PATENT_LAW,
            "technology": DomainType.TECHNOLOGY,
            "business": DomainType.BUSINESS,
            "ai_ml": DomainType.AI_ML,
            "legal": DomainType.LEGAL,
            "finance": DomainType.FINANCE,
            "medical": DomainType.MEDICAL,
            "education": DomainType.EDUCATION,
        }

        mapping = ConceptMapping(
            source_domain=domain_map[mapping_data["source_domain"]],
            target_domain=domain_map[mapping_data["target_domain"]],
            source_concept=mapping_data["source_concept"],
            target_concept=mapping_data["target_concept"],
            semantic_similarity=mapping_data["semantic_similarity"],
            mapping_confidence=mapping_data["mapping_confidence"],
        )

        fusion_engine.CROSS_DOMAIN_MAPPINGS.append(mapping)

    logger.info(f"✅ 已添加 {len(EXTENDED_CONCEPT_MAPPINGS)} 个跨域概念映射")

    # 重建知识图谱
    await fusion_engine._build_knowledge_graph()

    logger.info("📚 扩展知识应用完成")
