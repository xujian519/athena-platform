#!/usr/bin/env python3
from __future__ import annotations
"""
增强意图分析器 - 基于法律世界模型
Enhanced Intent Analyzer - Based on Legal World Model

整合法律世界模型的三层架构和场景识别能力，提供更精准的意图识别。

核心功能:
1. 增强领域识别（专利子领域：农业、机械、电子等）
2. 细化意图类型（专利撰写、检索、分析等）
3. 专利类型识别（发明、实用新型、外观设计）
4. 业务阶段识别（申请、审查、诉讼等）
5. 整合法律世界模型的三层架构

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from core.legal_world_model.constitution import (
    DocumentType,
    LayerType,
)
from core.legal_world_model.scenario_identifier import (
    Domain,
    Phase,
    ScenarioContext,
    ScenarioIdentifier,
    TaskType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# 增强枚举定义
# =============================================================================


class EnhancedIntentType(Enum):
    """增强意图类型 - 更细粒度的任务分类"""

    # === 专利相关意图 ===
    PATENT_WRITING = "patent_writing"           # 专利撰写
    PATENT_SEARCH = "patent_search"             # 专利检索
    PATENT_ANALYSIS = "patent_analysis"         # 专利分析
    PATENT_NOVELTY = "patent_novelty"           # 新颖性分析
    PATENT_CREATIVITY = "patent_creativity"     # 创造性分析
    PATENT_INFIRMINGEMENT = "patent_infringement"  # 侵权分析
    PATENT_INVALIDATION = "patent_invalidation" # 无效分析
    PATENT_COMPARISON = "patent_comparison"     # 专利对比

    # === 法律相关意图 ===
    LEGAL_CONSULTATION = "legal_consultation"   # 法律咨询
    LEGAL_DOCUMENT_REVIEW = "legal_document_review"  # 法律文书审查
    LEGAL_RESEARCH = "legal_research"           # 法律检索
    CONTRACT_REVIEW = "contract_review"         # 合同审查

    # === 商标相关意图 ===
    TRADEMARK_SEARCH = "trademark_search"       # 商标检索
    TRADEMARK_REGISTRATION = "trademark_registration"  # 商标注册
    TRADEMARK_ANALYSIS = "trademark_analysis"   # 商标分析

    # === 通用意图 ===
    QUERY = "query"                             # 查询
    CHAT = "chat"                               # 聊天
    UNKNOWN = "unknown"                         # 未知


class PatentSubDomain(Enum):
    """专利子领域分类"""

    # 农林牧渔
    AGRICULTURE = "agriculture"         # 农业
    FORESTRY = "forestry"               # 林业
    ANIMAL_HUSBANDRY = "animal_husbandry"  # 畜牧业
    FISHERY = "fishery"                 # 渔业

    # 机械制造
    MACHINERY = "machinery"             # 机械
    INSTRUMENTS = "instruments"         # 仪器
    VEHICLE = "vehicle"                 # 车辆
    AEROSPACE = "aerospace"             # 航空航天

    # 电子通信
    ELECTRONICS = "electronics"         # 电子
    COMMUNICATION = "communication"     # 通信
    COMPUTER = "computer"               # 计算机
    SEMICONDUCTOR = "semiconductor"     # 半导体

    # 化工材料
    CHEMISTRY = "chemistry"             # 化学
    MATERIALS = "materials"             # 材料
    PHARMACEUTICALS = "pharmaceuticals" # 医药
    BIOTECHNOLOGY = "biotechnology"     # 生物技术

    # 建筑工程
    CONSTRUCTION = "construction"       # 建筑
    CIVIL_ENGINEERING = "civil_engineering"  # 土木工程

    # 其他
    GENERAL = "general"                 # 通用
    OTHER = "other"                     # 其他


class PatentType(Enum):
    """专利类型"""

    INVENTION = "invention"             # 发明专利
    UTILITY_MODEL = "utility_model"     # 实用新型
    DESIGN = "design"                   # 外观设计


# =============================================================================
# 增强意图对象
# =============================================================================


@dataclass
class EnhancedIntent:
    """增强意图对象"""

    # 基础意图信息
    intent_type: EnhancedIntentType
    primary_goal: str
    confidence: float

    # 法律世界模型集成
    domain: Domain                      # 业务领域
    task_type: TaskType | None = None  # 任务类型
    phase: Phase | None = None       # 业务阶段
    layer_type: LayerType | None = None  # 相关层级

    # 专利特定信息
    patent_sub_domain: PatentSubDomain | None = None  # 专利子领域
    patent_type: PatentType | None = None            # 专利类型

    # 提取的实体和变量
    entities: dict[str, Any] = field(default_factory=dict)
    extracted_variables: dict[str, Any] = field(default_factory=dict)

    # 上下文信息
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # 建议的处理方式
    suggested_agent: Optional[str] = None
    required_documents: list[DocumentType] = field(default_factory=list)
    required_layers: list[LayerType] = field(default_factory=list)


# =============================================================================
# 增强意图分析器
# =============================================================================


class EnhancedIntentAnalyzer:
    """
    增强意图分析器

    整合法律世界模型，提供更精准的意图识别能力。
    """

    # 专利类型识别模式
    PATENT_TYPE_PATTERNS = {
        PatentType.INVENTION: [
            r"发明",
            r"invention",
            r"发明专利",
            r"方法发明",
            r"产品发明",
        ],
        PatentType.UTILITY_MODEL: [
            r"实用新型",
            r"utility.?model",
            r"实用新型专利",
            r"结构.*改进",
            r"构造.*优化",
        ],
        PatentType.DESIGN: [
            r"外观设计",
            r"外观",
            r"设计.*外观",
            r"design",
            r"外观设计专利",
            r"外观.*保护",
            r"产品.*外观",
        ],
    }

    # 专利子领域关键词映射
    PATENT_SUB_DOMAIN_KEYWORDS = {
        # 农林牧渔
        PatentSubDomain.AGRICULTURE: [
            "农业", "农作物", "种植", "收割", "灌溉", "施肥",
            "agriculture", "crop", "farm", "harvest", "irrigation",
        ],
        PatentSubDomain.FORESTRY: [
            "林业", "造林", "伐木", "木材", "森林",
            "forestry", "forest", "timber", "logging",
        ],
        PatentSubDomain.ANIMAL_HUSBANDRY: [
            "畜牧", "养殖", "牲畜", "饲料", "禽类",
            "livestock", "animal", "breeding", "feed", "poultry",
        ],
        PatentSubDomain.FISHERY: [
            "渔业", "水产", "养殖", "捕捞", "鱼", "虾",
            "fishery", "aquaculture", "fishing", "seafood",
        ],

        # 机械制造
        PatentSubDomain.MACHINERY: [
            "机械", "机床", "齿轮", "轴承", "传动", "发动机",
            "machinery", "machine", "gear", "bearing", "engine",
        ],
        PatentSubDomain.INSTRUMENTS: [
            "仪器", "仪表", "测量", "检测", "传感器",
            "instrument", "meter", "measurement", "sensor", "detector",
        ],
        PatentSubDomain.VEHICLE: [
            "车辆", "汽车", "火车", "自行车", "轮胎", "制动",
            "vehicle", "car", "automotive", "train", "bicycle", "brake",
        ],
        PatentSubDomain.AEROSPACE: [
            "航空", "航天", "飞机", "火箭", "卫星", "无人机",
            "aerospace", "aircraft", "rocket", "satellite", "drone",
        ],

        # 电子通信
        PatentSubDomain.ELECTRONICS: [
            "电子", "电路", "芯片", "集成电路", "电路板",
            "electronics", "circuit", "chip", "IC", "PCB",
        ],
        PatentSubDomain.COMMUNICATION: [
            "通信", "网络", "无线", "天线", "信号", "基站",
            "communication", "network", "wireless", "antenna", "signal",
        ],
        PatentSubDomain.COMPUTER: [
            "计算机", "软件", "算法", "数据", "程序", "系统",
            "computer", "software", "algorithm", "data", "program", "system",
        ],
        PatentSubDomain.SEMICONDUCTOR: [
            "半导体", "晶体管", "二极管", "LED", "光伏",
            "semiconductor", "transistor", "diode", "photovoltaic",
        ],

        # 化工材料
        PatentSubDomain.CHEMISTRY: [
            "化学", "化合物", "合成", "反应", "催化剂",
            "chemistry", "chemical", "compound", "synthesis", "catalyst",
        ],
        PatentSubDomain.MATERIALS: [
            "材料", "合金", "聚合物", "陶瓷", "复合材料",
            "material", "alloy", "polymer", "ceramic", "composite",
        ],
        PatentSubDomain.PHARMACEUTICALS: [
            "医药", "药物", "制药", "药品", "治疗", "疾病",
            "pharmaceutical", "medicine", "drug", "treatment", "disease",
        ],
        PatentSubDomain.BIOTECHNOLOGY: [
            "生物", "基因", "细胞", "蛋白质", "DNA", "RNA",
            "biology", "biotech", "gene", "cell", "protein",
        ],

        # 建筑工程
        PatentSubDomain.CONSTRUCTION: [
            "建筑", "房屋", "结构", "施工", "建筑材料",
            "construction", "building", "structure", "architecture",
        ],
        PatentSubDomain.CIVIL_ENGINEERING: [
            "土木", "桥梁", "道路", "隧道", "大坝", "基础设施",
            "civil", "bridge", "road", "tunnel", "dam", "infrastructure",
        ],
    }

    # 增强意图类型关键词
    INTENT_TYPE_KEYWORDS = {
        EnhancedIntentType.PATENT_WRITING: [
            "写", "撰写", "起草", "生成", "申请", "申请文件",
            "write", "draft", "create", "application", "filing",
        ],
        EnhancedIntentType.PATENT_SEARCH: [
            "检索", "搜索", "查新", "查找", "现有技术",
            "search", "find", "prior art", "retrieve",
        ],
        EnhancedIntentType.PATENT_ANALYSIS: [
            "分析", "评估", "诊断", "研究",
            "analyze", "evaluate", "assess", "study",
        ],
        EnhancedIntentType.PATENT_NOVELTY: [
            "新颖性", "现有技术", "公开", "不属于现有技术",
            "novelty", "prior art", "disclosed",
        ],
        EnhancedIntentType.PATENT_CREATIVITY: [
            "创造性", "创新性", "创新高度", "技术贡献",
            "creativity", "inventive step", "technical contribution",
        ],
        EnhancedIntentType.PATENT_INFIRMINGEMENT: [
            "侵权", "保护范围", "等同", "落入",
            "infringement", "scope", "equivalent", "fall into",
        ],
        EnhancedIntentType.PATENT_INVALIDATION: [
            "无效", "无效宣告", "不符合专利法", "稳定性",
            "invalidation", "invalid", "stability",
        ],
        EnhancedIntentType.PATENT_COMPARISON: [
            "对比", "比较", "区别", "差异",
            "compare", "comparison", "difference", "distinction",
        ],
    }

    def __init__(self, enable_scenario_identifier: bool = True):
        """
        初始化增强意图分析器

        Args:
            enable_scenario_identifier: 是否启用场景识别器
        """
        self.logger = logging.getLogger(__name__)
        self.enable_scenario_identifier = enable_scenario_identifier

        # 初始化场景识别器
        if enable_scenario_identifier:
            self.scenario_identifier = ScenarioIdentifier()

        # 识别历史
        self.recognition_history: list[dict[str, Any]] = []

        self.logger.info("🧠 增强意图分析器初始化完成")
        self.logger.info(f"   支持的意图类型: {len(EnhancedIntentType)}个")
        self.logger.info(f"   支持的专利子领域: {len(PatentSubDomain)}个")
        self.logger.info(f"   支持的专利类型: {len(PatentType)}个")

    async def analyze(
        self,
        user_input: str,
        context: Optional[dict[str, Any]] = None
    ) -> EnhancedIntent:
        """
        分析用户意图

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            EnhancedIntent: 增强意图对象
        """
        self.logger.info(f"🔍 [增强分析] 开始分析: {user_input[:50]}...")

        context = context or {}
        user_input.lower()

        # Step 1: 使用场景识别器识别基础场景
        scenario_context: ScenarioContext | None = None
        if self.enable_scenario_identifier:
            scenario_context = self.scenario_identifier.identify_scenario(user_input)
            self.logger.info(
                f"   场景: {scenario_context.domain.value}/"
                f"{scenario_context.task_type.value}/"
                f"{scenario_context.phase.value} "
                f"(置信度: {scenario_context.confidence:.2f})"
            )

        # Step 2: 识别增强意图类型
        intent_type = self._recognize_enhanced_intent_type(user_input, scenario_context)

        # Step 3: 识别专利类型
        patent_type = self._recognize_patent_type(user_input)

        # Step 4: 识别专利子领域
        patent_sub_domain = self._recognize_patent_sub_domain(user_input)

        # Step 5: 确定相关层级（基于法律世界模型）
        layer_types = self._determine_required_layers(intent_type, scenario_context)

        # Step 6: 提取主要目标
        primary_goal = self._extract_primary_goal(user_input, intent_type)

        # Step 7: 计算综合置信度
        confidence = self._calculate_confidence(
            user_input,
            intent_type,
            scenario_context,
            patent_type,
            patent_sub_domain
        )

        # Step 8: 建议处理方式
        suggested_agent = self._suggest_agent(intent_type, scenario_context)
        required_documents = self._determine_required_documents(intent_type, scenario_context)

        # Step 9: 构建增强意图对象
        intent = EnhancedIntent(
            intent_type=intent_type,
            primary_goal=primary_goal,
            confidence=confidence,
            domain=scenario_context.domain if scenario_context else Domain.OTHER,
            task_type=scenario_context.task_type if scenario_context else None,
            phase=scenario_context.phase if scenario_context else None,
            layer_type=layer_types[0] if layer_types else None,
            patent_sub_domain=patent_sub_domain,
            patent_type=patent_type,
            extracted_variables=scenario_context.extracted_variables if scenario_context else {},
            context={
                **context,
                "original_input": user_input,
                "scenario_context": scenario_context.__dict__ if scenario_context else None,
            },
            suggested_agent=suggested_agent,
            required_documents=required_documents,
            required_layers=layer_types,
        )

        # Step 10: 记录历史
        self.recognition_history.append({
            "input": user_input,
            "intent": intent,
            "timestamp": datetime.now(),
        })

        self.logger.info(
            f"   ✅ 增强分析完成: {intent_type.value} "
            f"(置信度: {confidence:.2f})"
        )

        if patent_type:
            self.logger.info(f"   专利类型: {patent_type.value}")
        if patent_sub_domain:
            self.logger.info(f"   专利子领域: {patent_sub_domain.value}")
        if suggested_agent:
            self.logger.info(f"   建议智能体: {suggested_agent}")

        return intent

    def _recognize_enhanced_intent_type(
        self,
        text: str,
        scenario_context: ScenarioContext | None = None
    ) -> EnhancedIntentType:
        """识别增强意图类型"""
        text_lower = text.lower()

        # 优先匹配场景识别器结果
        if scenario_context and scenario_context.domain == Domain.PATENT:
            if scenario_context.task_type == TaskType.DRAFTING:
                return EnhancedIntentType.PATENT_WRITING
            elif scenario_context.task_type == TaskType.SEARCH:
                return EnhancedIntentType.PATENT_SEARCH
            elif scenario_context.task_type == TaskType.NOVELTY_ANALYSIS:
                return EnhancedIntentType.PATENT_NOVELTY
            elif scenario_context.task_type == TaskType.CREATIVITY_ANALYSIS:
                return EnhancedIntentType.PATENT_CREATIVITY
            elif scenario_context.task_type == TaskType.INFRINGEMENT:
                return EnhancedIntentType.PATENT_INFIRMINGEMENT
            elif scenario_context.task_type == TaskType.VALIDITY:
                return EnhancedIntentType.PATENT_INVALIDATION

        # 关键词匹配
        max_score = 0
        best_intent = EnhancedIntentType.QUERY

        for intent_type, keywords in self.INTENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > max_score:
                max_score = score
                best_intent = intent_type

        # 聊天意图特殊处理
        chat_keywords = ["你好", "嗨", "在吗", "谢谢", "聊聊天", "hello", "hi"]
        if any(kw in text_lower for kw in chat_keywords):
            return EnhancedIntentType.CHAT

        return best_intent if max_score > 0 else EnhancedIntentType.UNKNOWN

    def _recognize_patent_type(self, text: str) -> PatentType | None:
        """识别专利类型"""
        text.lower()

        for patent_type, patterns in self.PATENT_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return patent_type

        return None

    def _recognize_patent_sub_domain(self, text: str) -> PatentSubDomain | None:
        """识别专利子领域"""
        text_lower = text.lower()

        max_score = 0
        best_domain = None

        for sub_domain, keywords in self.PATENT_SUB_DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > max_score:
                max_score = score
                best_domain = sub_domain

        # 至少匹配1个关键词就认为有效
        return best_domain if max_score >= 1 else None

    def _determine_required_layers(
        self,
        intent_type: EnhancedIntentType,
        scenario_context: ScenarioContext | None = None
    ) -> list[LayerType]:
        """确定需要的层级（基于法律世界模型三层架构）"""
        layers = []

        # 大多数专利任务需要专业层
        if intent_type in [
            EnhancedIntentType.PATENT_WRITING,
            EnhancedIntentType.PATENT_SEARCH,
            EnhancedIntentType.PATENT_ANALYSIS,
            EnhancedIntentType.PATENT_NOVELTY,
            EnhancedIntentType.PATENT_CREATIVITY,
        ]:
            layers.append(LayerType.PATENT_PROFESSIONAL_LAYER)

        # 侵权和无效分析需要司法案例层
        if intent_type in [
            EnhancedIntentType.PATENT_INFIRMINGEMENT,
            EnhancedIntentType.PATENT_INVALIDATION,
        ]:
            layers.append(LayerType.JUDICIAL_CASE_LAYER)

        # 复杂任务可能需要基础法律层
        if scenario_context and scenario_context.phase in [Phase.LITIGATION, Phase.OPPOSITION]:
            layers.insert(0, LayerType.FOUNDATION_LAW_LAYER)

        return layers

    def _extract_primary_goal(self, text: str, intent_type: EnhancedIntentType) -> str:
        """提取主要目标"""
        # 去除常见的修饰词
        text = re.sub(r"^(请|帮我|帮忙|麻烦|能否|可以|能不能|我要)", "", text)
        text = re.sub(r"(吗|呢|吧|呀)$", "", text)

        # 提取核心句子
        core = re.sub(r'[，。、！？\s,\.!?]+', " ", text).strip()

        return core if core else "未指定目标"

    def _calculate_confidence(
        self,
        text: str,
        intent_type: EnhancedIntentType,
        scenario_context: ScenarioContext | None = None,
        patent_type: PatentType | None = None,
        patent_sub_domain: PatentSubDomain | None = None,
    ) -> float:
        """计算综合置信度"""
        confidence = 0.5  # 基础置信度

        # 意图类型明确性
        if intent_type != EnhancedIntentType.UNKNOWN:
            confidence += 0.15

        # 场景识别置信度
        if scenario_context:
            confidence += scenario_context.confidence * 0.15

        # 专利类型识别
        if patent_type:
            confidence += 0.1

        # 子领域识别
        if patent_sub_domain:
            confidence += 0.1

        return min(confidence, 1.0)

    def _suggest_agent(
        self,
        intent_type: EnhancedIntentType,
        scenario_context: ScenarioContext | None = None
    ) -> Optional[str]:
        """建议处理智能体"""
        # 专利相关任务 -> 小娜
        if intent_type in [
            EnhancedIntentType.PATENT_WRITING,
            EnhancedIntentType.PATENT_SEARCH,
            EnhancedIntentType.PATENT_ANALYSIS,
            EnhancedIntentType.PATENT_NOVELTY,
            EnhancedIntentType.PATENT_CREATIVITY,
            EnhancedIntentType.PATENT_INFIRMINGEMENT,
            EnhancedIntentType.PATENT_INVALIDATION,
            EnhancedIntentType.PATENT_COMPARISON,
        ]:
            return "xiaona"  # 小娜·法律专家

        # 通用任务 -> 小诺
        if intent_type in [EnhancedIntentType.QUERY, EnhancedIntentType.CHAT]:
            return "xiaonuo"  # 小诺·调度官

        return None

    def _determine_required_documents(
        self,
        intent_type: EnhancedIntentType,
        scenario_context: ScenarioContext | None = None
    ) -> list[DocumentType]:
        """确定需要的文档类型"""
        documents = []

        if intent_type in [
            EnhancedIntentType.PATENT_WRITING,
            EnhancedIntentType.PATENT_NOVELTY,
            EnhancedIntentType.PATENT_CREATIVITY,
        ]:
            # 专利撰写和分析需要审查指南
            documents.append(DocumentType.GUIDELINE_DOC)
            documents.append(DocumentType.REGULATION_DOC)

        if intent_type in [
            EnhancedIntentType.PATENT_INFIRMINGEMENT,
            EnhancedIntentType.PATENT_INVALIDATION,
        ]:
            # 侵权和无效需要案例
            documents.append(DocumentType.INVALIDATION_DECISION_DOC)
            documents.append(DocumentType.CIVIL_JUDGMENT)

        return documents

    def get_recognition_stats(self) -> dict[str, Any]:
        """获取识别统计信息"""
        if not self.recognition_history:
            return {"total_recognitions": 0}

        intent_distribution = {}
        confidence_sum = 0
        patent_type_count = {}
        sub_domain_count = {}

        for record in self.recognition_history:
            intent = record["intent"]
            intent_type = intent.intent_type.value
            intent_distribution[intent_type] = intent_distribution.get(intent_type, 0) + 1
            confidence_sum += intent.confidence

            if intent.patent_type:
                patent_type_count[intent.patent_type.value] = (
                    patent_type_count.get(intent.patent_type.value, 0) + 1
                )

            if intent.patent_sub_domain:
                sub_domain_count[intent.patent_sub_domain.value] = (
                    sub_domain_count.get(intent.patent_sub_domain.value, 0) + 1
                )

        return {
            "total_recognitions": len(self.recognition_history),
            "intent_distribution": intent_distribution,
            "average_confidence": confidence_sum / len(self.recognition_history),
            "patent_type_distribution": patent_type_count,
            "sub_domain_distribution": sub_domain_count,
        }


# =============================================================================
# 便捷函数
# =============================================================================


async def analyze_intent_enhanced(
    user_input: str,
    context: Optional[dict[str, Any]] = None
) -> EnhancedIntent:
    """
    便捷的增强意图分析函数

    Args:
        user_input: 用户输入文本
        context: 上下文信息

    Returns:
        EnhancedIntent: 增强意图对象

    Example:
        >>> result = await analyze_intent_enhanced("我要写一篇农业领域的实用新型专利")
        >>> print(result.intent_type)
        EnhancedIntentType.PATENT_WRITING
        >>> print(result.patent_type)
        PatentType.UTILITY_MODEL
        >>> print(result.patent_sub_domain)
        PatentSubDomain.AGRICULTURE
    """
    analyzer = EnhancedIntentAnalyzer()
    return await analyzer.analyze(user_input, context)


__all__ = [
    "EnhancedIntentType",
    "PatentSubDomain",
    "PatentType",
    "EnhancedIntent",
    "EnhancedIntentAnalyzer",
    "analyze_intent_enhanced",
]
