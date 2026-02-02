#!/usr/bin/env python3
"""
语义推理引擎 v4.0 - 维特根斯坦版
Semantic Reasoning Engine v4.0 - Wittgenstein Edition

基于维特根斯坦《逻辑哲学论》的精确推理原则
- 诚实:不确定就明确说明
- 精确:可说的说清楚,不可说保持沉默
- 证据:每个结论都有明确证据支持
- 命题:推理结果都是逻辑命题
"""

import asyncio
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入v4.0模块 - 使用绝对路径导入
try:
    from core.v4.uncertainty_quantifier import (
        CertaintyLevel,
        Confidence,
        PropositionalResponse,
        UncertaintyQuantifier,
    )

    V4_AVAILABLE = True
except ImportError:
    UncertaintyQuantifier = None
    CertaintyLevel = None
    Confidence = None
    PropositionalResponse = None


# 简化版Confidence类(当v4模块不可用时使用)
@dataclass
class SimpleConfidence:
    """简化版置信度类"""

    value: float = 0.0
    level: str = "low"
    evidence: list = field(default_factory=list)

    def __init__(self, value: float = 0.0):
        self.value = value
        if value >= 0.9:
            self.level = "very_high"
        elif value >= 0.7:
            self.level = "high"
        elif value >= 0.5:
            self.level = "medium"
        elif value >= 0.3:
            self.level = "low"
        else:
            self.level = "very_low"


try:
    from sentence_transformers import SentenceTransformer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:

    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class ReasoningType(Enum):
    """推理类型"""

    RULE_BASED = "rule_based"  # 基于规则的推理
    SEMANTIC = "semantic"  # 语义推理
    CASE_BASED = "case_based"  # 基于案例的推理
    HYBRID = "hybrid"  # 混合推理
    TEMPORAL = "temporal"  # 时间推理
    CAUSAL = "causal"  # 因果推理


@dataclass
class ReasoningResultV4:
    """v4.0推理结果 - 基于维特根斯坦原则"""

    reasoning_type: ReasoningType
    conclusion: str  # 命题式结论
    confidence: Confidence  # v4.0置信度对象
    evidence: list[str]  # 支持证据
    reasoning_path: list[str]  # 推理路径
    metadata: dict[str, Any]  # 元数据
    timestamp: datetime
    limitations: list[str] = field(default_factory=list)  # 局限性
    is_certain: bool = False  # 是否确定
    is_sayable: bool = True  # 是否可说(是否在知识边界内)


@dataclass
class ReasoningRule:
    """推理规则"""

    rule_id: str
    name: str
    description: str
    conditions: list[str]
    conclusion_template: str
    confidence_base: float
    domain: str
    metadata: dict[str, Any]
class SemanticReasoningEngineV4:
    """语义推理引擎 v4.0 - 基于维特根斯坦原则"""

    def __init__(self):
        self.embedding_model = None
        self.reasoning_graph = nx.DiGraph() if NETWORKX_AVAILABLE else None
        self.reasoning_rules = {}
        self.case_database = {}
        self.ontology_concepts = {}

        # v4.0核心组件(如果可用)
        if V4_AVAILABLE and UncertaintyQuantifier is not None:
            self.uncertainty_quantifier = UncertaintyQuantifier()
            self.response_builder = PropositionalResponse(self.uncertainty_quantifier)
        else:
            logger.warning("⚠️ v4.0模块不可用,使用简化版不确定性量化")
            self.uncertainty_quantifier = None
            self.response_builder = None

        # 推理历史(用于学习和改进)
        self.reasoning_history = []

        # 初始化组件
        self._init_embedding_model()
        self._load_reasoning_rules()
        self._load_case_database()
        self._load_ontology()

    def _init_embedding_model(self) -> Any:
        """初始化嵌入模型 - 使用本地BGE-M3模型"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ 嵌入模型不可用,使用基础推理")
            return

        try:
            from core.nlp.bge_m3_loader import get_bge_m3_loader

            # 使用BGE-M3加载器
            loader = get_bge_m3_loader("bge-m3")

            if loader.load_model():
                self.embedding_model = loader.model
                logger.info("✅ BGE-M3嵌入模型加载成功")
                logger.info(f"📊 向量维度: {loader.config.get('dimension')}")
                logger.info(f"🔗 最大序列长度: {loader.config.get('max_seq_length')} tokens")
                logger.info(f"💻 设备: {loader.device}")
            else:
                # 降级到远程模型
                logger.warning("⚠️ BGE-M3本地模型加载失败,使用HuggingFace远程模型")
                import torch

                device = "cpu"
                if torch.backends.mps.is_available():
                    device = "mps"
                elif torch.cuda.is_available():
                    device = "cuda"

                self.embedding_model = SentenceTransformer("BAAI/bge-m3", device=device)
                logger.info(f"✅ BGE-M3远程模型加载成功,设备: {device}")

        except Exception as e:
            self.embedding_model = None

    def _load_reasoning_rules(self) -> Any:
        """加载推理规则"""
        # 法律推理规则
        self.reasoning_rules.update(
            {
                # 侵权责任推理
                "infringement_responsibility": ReasoningRule(
                    rule_id="infringement_responsibility",
                    name="侵权责任推理",
                    description="基于侵权行为的法律责任推理",
                    conditions=["存在违法行为", "造成损害结果", "具有因果关系"],
                    conclusion_template="由于存在{行为},造成{损害},且存在因果关系,应当承担{责任}",
                    confidence_base=0.8,
                    domain="legal",
                    metadata={"severity": "high", "legal_basis": "民法典第1165条"},
                ),
                # 合同效力推理
                "contract_validity": ReasoningRule(
                    rule_id="contract_validity",
                    name="合同效力推理",
                    description="基于合同要件的效力判断推理",
                    conditions=["当事人适格", "意思表示真实", "内容合法"],
                    conclusion_template="该合同满足法定要件,应当认定为{效力状态}",
                    confidence_base=0.85,
                    domain="legal",
                    metadata={"severity": "medium", "legal_basis": "民法典第143条"},
                ),
                # 专利新颖性推理
                "patent_novelty": ReasoningRule(
                    rule_id="patent_novelty",
                    name="专利新颖性推理",
                    description="基于现有技术的专利新颖性判断推理",
                    conditions=["不属于现有技术", "无抵触申请", "不丧失新颖性情形"],
                    conclusion_template="该技术方案{novelty_status},符合专利新颖性要求",
                    confidence_base=0.75,
                    domain="patent",
                    metadata={"severity": "high", "legal_basis": "专利法第22条"},
                ),
                # 专利创造性推理
                "patent_inventiveness": ReasoningRule(
                    rule_id="patent_inventiveness",
                    name="专利创造性推理",
                    description="基于技术进步性的专利创造性判断推理",
                    conditions=["具有实质性特点", "具有显著进步", "非显而易见"],
                    conclusion_template="该发明具有{inventiveness_level},符合专利创造性要求",
                    confidence_base=0.7,
                    domain="patent",
                    metadata={"severity": "high", "legal_basis": "专利法第22条"},
                ),
                # 因果关系推理
                "causation_reasoning": ReasoningRule(
                    rule_id="causation_reasoning",
                    name="因果关系推理",
                    description="基于时序和逻辑的因果关系推理",
                    conditions=["时间先后关系", "逻辑关联性", "无其他原因"],
                    conclusion_template="{前因}与{后果}之间存在因果关系",
                    confidence_base=0.6,
                    domain="general",
                    metadata={"reasoning_type": "causal"},
                ),
            }
        )

        logger.info(f"✅ 加载推理规则: {len(self.reasoning_rules)} 个")

    def _load_case_database(self) -> Any:
        """加载案例数据库"""
        # 法律案例示例
        self.case_database.update(
            {
                "legal_infringement_001": {
                    "case_id": "legal_infringement_001",
                    "title": "网络著作权侵权案例",
                    "facts": "被告未经许可在网站上传播原告享有著作权的作品",
                    "outcome": "法院判决被告承担侵权责任,赔偿经济损失",
                    "reasoning": "存在传播行为,造成权利人损失,构成侵权",
                    "keywords": ["著作权", "网络传播", "侵权", "赔偿"],
                    "domain": "legal",
                    "precedent_value": 0.8,
                },
                "patent_novelty_001": {
                    "case_id": "patent_novelty_001",
                    "title": "专利新颖性审查案例",
                    "facts": "申请人在申请日前公开了相同技术方案",
                    "outcome": "专利申请因缺乏新颖性被驳回",
                    "reasoning": "自我公开导致技术方案成为现有技术",
                    "keywords": ["专利", "新颖性", "自我公开", "现有技术"],
                    "domain": "patent",
                    "precedent_value": 0.9,
                },
                "contract_dispute_001": {
                    "case_id": "contract_dispute_001",
                    "title": "合同效力纠纷案例",
                    "facts": "合同双方当事人具有完全民事行为能力,意思表示真实,内容不违法",
                    "outcome": "法院认定合同有效",
                    "reasoning": "满足合同生效的全部法定要件",
                    "keywords": ["合同", "效力", "民事行为能力", "意思表示"],
                    "domain": "legal",
                    "precedent_value": 0.85,
                },
            }
        )

        logger.info(f"✅ 加载案例数据库: {len(self.case_database)} 个案例")

    def _load_ontology(self) -> Any:
        """加载本体知识"""
        # 法律本体概念
        self.ontology_concepts.update(
            {
                "legal": {
                    "rights": ["民事权利", "财产权", "人身权", "知识产权"],
                    "obligations": ["民事义务", "合同义务", "法定义务", "侵权责任"],
                    "legal_actions": ["起诉", "应诉", "上诉", "申诉", "执行"],
                    "legal_entities": ["自然人", "法人", "非法人组织"],
                    "contracts": ["买卖合同", "租赁合同", "劳动合同", "技术服务合同"],
                },
                "patent": {
                    "patent_types": ["发明专利", "实用新型专利", "外观设计专利"],
                    "patent_requirements": ["新颖性", "创造性", "实用性"],
                    "patent_procedures": ["申请", "审查", "授权", "无效", "终止"],
                    "technical_elements": ["技术方案", "技术特征", "技术问题", "技术效果"],
                    "inventive_concepts": ["创新点", "技术进步", "突破", "改进"],
                },
            }
        )

        logger.info(f"✅ 加载本体知识: {len(self.ontology_concepts)} 个领域")

    async def reason(
        self,
        query: str,
        str | None = None,
        Optional[list["key"] = None,
        str | None = None,
    ) -> list[ReasoningResultV4]:
        """
        执行推理 - v4.0版本

        Returns:
            v4.0格式的推理结果,包含完整的置信度和证据
        """
        if reasoning_types is None:
            reasoning_types = [
                ReasoningType.RULE_BASED,
                ReasoningType.SEMANTIC,
                ReasoningType.CASE_BASED,
            ]

        results = []

        # 基于规则的推理
        if ReasoningType.RULE_BASED in reasoning_types:
            rule_results = await self._rule_based_reasoning_v4(query, context, domain)
            results.extend(rule_results)

        # 语义推理
        if ReasoningType.SEMANTIC in reasoning_types and self.embedding_model:
            semantic_results = await self._semantic_reasoning_v4(query, context, domain)
            results.extend(semantic_results)

        # 基于案例的推理
        if ReasoningType.CASE_BASED in reasoning_types:
            case_results = await self._case_based_reasoning_v4(query, context, domain)
            results.extend(case_results)

        # 因果推理
        if ReasoningType.CAUSAL in reasoning_types:
            causal_results = await self._causal_reasoning_v4(query, context, domain)
            results.extend(causal_results)

        # 混合推理
        if ReasoningType.HYBRID in reasoning_types and len(results) > 1:
            hybrid_results = await self._hybrid_reasoning_v4(results, query, context)
            results.extend(hybrid_results)

        # 按置信度排序
        results.sort(key=lambda x: x.confidence.value, reverse=True)

        # 记录推理历史
        self.reasoning_history.append(
            {
                "timestamp": datetime.now(),
                "query": query,
                "context": context,
                "domain": domain,
                "results_count": len(results),
                "best_confidence": results.get(0).confidence.value if results else 0.0,
            }
        )

        return results

    def _quantify_confidence(
        self, claim: str, evidence: list, information_completeness: float
    ) -> Any:
        """安全地量化置信度(兼容v4模块不可用的情况)"""
        if self.uncertainty_quantifier is not None:
            return self.uncertainty_quantifier.quantify(
                claim=claim, evidence=evidence, information_completeness=information_completeness
            )
        else:
            # 简化版置信度计算
            confidence_value = min(0.9, information_completeness)
            return SimpleConfidence(value=confidence_value)

    async def _rule_based_reasoning_v4(
        self, query: str, context: Optional[str, str]
    ) -> list[ReasoningResultV4]:
        """基于规则的推理 - v4.0版本"""
        results = []

        # 合并查询和上下文
        full_text = f"{query} {context or ''}"

        for rule_id, rule in self.reasoning_rules.items():
            # 域过滤
            if domain and rule.domain != domain and rule.domain != "general":
                continue

            # 检查条件满足度
            satisfied_conditions = []
            for condition in rule.conditions:
                if self._check_condition(condition, full_text):
                    satisfied_conditions.append(condition)

            # 计算满足度
            if len(rule.conditions) == 0:
                continue

            satisfaction_rate = len(satisfied_conditions) / len(rule.conditions)

            # 如果满足度超过阈值,则进行推理
            if satisfaction_rate >= 0.6:  # 至少满足60%的条件
                # 使用v4.0不确定性量化
                claim = f"根据{rule.name},{rule.description}"

                # 构建证据列表
                evidence = [
                    f"满足条件: {', '.join(satisfied_conditions)}",
                    f"满足度: {satisfaction_rate:.1%}",
                    f"法律依据: {rule.metadata.get('legal_basis', '无')}",
                ]

                # 计算信息完整性
                information_completeness = satisfaction_rate

                # 量化置信度
                confidence = self._quantify_confidence(
                    claim=claim,
                    evidence=evidence,
                    information_completeness=information_completeness,
                )

                # 调整基础置信度
                confidence.value = confidence.value * rule.confidence_base * satisfaction_rate

                # 生成结论
                conclusion = self._generate_conclusion(rule, satisfied_conditions, full_text)

                # 构建推理路径
                reasoning_path = [
                    f"应用规则: {rule.name}",
                    f"满足条件: {', '.join(satisfied_conditions)}",
                    f"满足度: {satisfaction_rate:.1%}",
                    f"置信度: {confidence.value:.1%}",
                ]

                # 识别局限性
                limitations = []
                if satisfaction_rate < 1.0:
                    limitations.append(f"部分条件未满足(满足度{confidence.value:.1%})")
                if confidence.value < 0.7:
                    limitations.append("置信度不足,需要更多信息")

                result = ReasoningResultV4(
                    reasoning_type=ReasoningType.RULE_BASED,
                    conclusion=conclusion,
                    confidence=confidence,
                    evidence=evidence,
                    reasoning_path=reasoning_path,
                    metadata={
                        "rule_id": rule_id,
                        "rule_name": rule.name,
                        "satisfaction_rate": satisfaction_rate,
                        "domain": rule.domain,
                    },
                    timestamp=datetime.now(),
                    limitations=limitations,
                    is_certain=confidence.value >= 0.9,
                    is_sayable=True,
                )

                results.append(result)

        return results

    def _check_condition(self, condition: str, text: str) -> bool:
        """检查条件是否满足"""
        # 简化的条件检查逻辑
        condition_lower = condition.lower()
        text_lower = text.lower()

        # 关键词匹配
        if condition_lower in text_lower:
            return True

        # 模式匹配
        patterns = {
            "存在违法行为": ["侵权", "违法", "违反", "违约"],
            "造成损害结果": ["损害", "损失", "伤害", "影响"],
            "具有因果关系": ["导致", "因为", "由于", "原因"],
            "当事人适格": ["具备", "具有", "拥有", "享有"],
            "意思表示真实": ["真实", "自愿", "同意", "承诺"],
            "内容合法": ["合法", "不违法", "符合法律"],
            "不属于现有技术": ["新颖", "创新", "新", "首次"],
            "具有实质性特点": ["实质性", "本质", "关键", "重要"],
            "具有显著进步": ["进步", "提升", "改进", "优化"],
            "时间先后关系": ["先", "前", "然后", "之后"],
            "逻辑关联性": ["相关", "联系", "关联", "影响"],
        }

        for pattern, keywords in patterns.items():
            if condition == pattern:
                return any(keyword in text_lower for keyword in keywords)

        return False

    def _generate_conclusion(self, rule: ReasoningRule, conditions: list[str], text: str) -> str:
        """生成推理结论"""
        conclusion = rule.conclusion_template

        # 简单的模板替换
        if "行为" in conclusion:
            # 从文本中提取行为描述
            action_patterns = ["侵权", "违约", "违法", "传播", "使用", "制造"]
            for pattern in action_patterns:
                if pattern in text:
                    conclusion = conclusion.replace("{行为}", pattern)
                    break

        if "损害" in conclusion:
            # 从文本中提取损害描述
            damage_patterns = ["损失", "损害", "伤害", "影响"]
            for pattern in damage_patterns:
                if pattern in text:
                    conclusion = conclusion.replace("{损害}", pattern)
                    break

        if "责任" in conclusion:
            if rule.domain == "legal":
                conclusion = conclusion.replace("{责任}", "法律责任")
            else:
                conclusion = conclusion.replace("{责任}", "相应责任")

        if "效力状态" in conclusion:
            conclusion = conclusion.replace("{效力状态}", "有效")

        if "新颖性状态" in conclusion:
            conclusion = conclusion.replace("{novelty_status}", "具备新颖性")

        if "创造性水平" in conclusion:
            conclusion = conclusion.replace("{inventiveness_level}", "创造性")

        if "前因" in conclusion or "后果" in conclusion:
            # 简化的因果推理
            conclusion = conclusion.replace("{前因}", "前因")
            conclusion = conclusion.replace("{后果}", "后果")

        return conclusion

    async def _semantic_reasoning_v4(
        self, query: str, context: Optional[str, str]
    ) -> list[ReasoningResultV4]:
        """语义推理 - v4.0版本"""
        results = []

        if not self.embedding_model:
            return results

        try:
            # 生成查询向量
            query_vector = self.embedding_model.encode([query])

            # 本体概念推理
            if domain and domain in self.ontology_concepts:
                ontology_results = await self._ontology_reasoning_v4(query, query_vector, domain)
                results.extend(ontology_results)

            # 语义相似性推理
            if context:
                similarity = self._calculate_semantic_similarity(query, context)

                if similarity > 0.7:
                    # v4.0量化
                    claim = "查询内容与上下文具有相同的法律/专利含义"
                    evidence = [f"语义相似度: {similarity:.2f}"]
                    confidence = self._quantify_confidence(
                        claim=claim, evidence=evidence, information_completeness=similarity
                    )
                    confidence.value = similarity

                    result = ReasoningResultV4(
                        reasoning_type=ReasoningType.SEMANTIC,
                        conclusion=f"查询内容与上下文高度相似(相似度: {similarity:.2f}),具有相同的法律/专利含义",
                        confidence=confidence,
                        evidence=evidence,
                        reasoning_path=["语义向量计算", "相似度比较", "阈值判断"],
                        metadata={"similarity_score": similarity},
                        timestamp=datetime.now(),
                        limitations=["基于语义相似度,需结合具体案例"],
                        is_certain=similarity >= 0.9,
                        is_sayable=True,
                    )
                    results.append(result)

        except Exception as e:
            logger.warning(f"⚠️ 语义推理失败: {e}")

        return results

    async def _ontology_reasoning_v4(
        self, query: str, query_vector: np.ndarray, domain: str
    ) -> list[ReasoningResultV4]:
        """本体推理 - v4.0版本"""
        results = []

        if domain not in self.ontology_concepts:
            return results

        ontology = self.ontology_concepts[domain]

        for category, concepts in ontology.items():
            # 计算与概念的语义相似度
            for concept in concepts:
                concept_vector = self.embedding_model.encode([concept])
                similarity = np.dot(query_vector, concept_vector)[0]

                if similarity > 0.6:
                    # v4.0量化
                    claim = f"查询涉及{category}中的'{concept}'概念"
                    evidence = [f"概念匹配: {concept}", f"相似度: {similarity:.2f}"]
                    confidence = self._quantify_confidence(
                        claim=claim, evidence=evidence, information_completeness=similarity
                    )
                    confidence.value = similarity

                    result = ReasoningResultV4(
                        reasoning_type=ReasoningType.SEMANTIC,
                        conclusion=f"查询涉及{category}中的'{concept}'概念",
                        confidence=confidence,
                        evidence=evidence,
                        reasoning_path=[
                            f"本体推理: {category}",
                            f"概念识别: {concept}",
                            f"相似度计算: {similarity:.2f}",
                        ],
                        metadata={
                            "category": category,
                            "concept": concept,
                            "similarity": similarity,
                        },
                        timestamp=datetime.now(),
                        limitations=["基于概念相似性,需结合语境确认"],
                        is_certain=similarity >= 0.85,
                        is_sayable=True,
                    )
                    results.append(result)

        return results

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """计算语义相似度"""
        try:
            vector1 = self.embedding_model.encode([text1])
            vector2 = self.embedding_model.encode([text2])
            similarity = np.dot(vector1, vector2.T)[0][0]
            return float(similarity)
        except Exception as e:
            return 0.0

    async def _case_based_reasoning_v4(
        self, query: str, context: Optional[str, str]
    ) -> list[ReasoningResultV4]:
        """基于案例的推理 - v4.0版本"""
        results = []

        full_text = f"{query} {context or ''}"

        for case_id, case in self.case_database.items():
            # 域过滤
            if domain and case.get("domain") != domain:
                continue

            # 计算案例相似度
            similarity = await self._calculate_case_similarity(full_text, case)

            if similarity > 0.5:  # 相似度阈值
                # v4.0量化
                claim = f"参考案例'{case['title']}',{case['outcome']}"
                evidence = [
                    f"案例ID: {case_id}",
                    f"相似度: {similarity:.2f}",
                    f"案例推理: {case['reasoning']}",
                ]
                confidence = self._quantify_confidence(
                    claim=claim,
                    evidence=evidence,
                    information_completeness=similarity * case.get("precedent_value", 0.8),
                )
                confidence.value = similarity * case.get("precedent_value", 0.8)

                result = ReasoningResultV4(
                    reasoning_type=ReasoningType.CASE_BASED,
                    conclusion=f"参考案例'{case['title']}',{case['outcome']}",
                    confidence=confidence,
                    evidence=evidence,
                    reasoning_path=[
                        f"案例检索: {case['title']}",
                        f"事实比较: {similarity:.2f}",
                        f"类比推理: {case['reasoning']}",
                    ],
                    metadata={
                        "case_id": case_id,
                        "case_title": case["title"],
                        "case_outcome": case["outcome"],
                        "precedent_value": case.get("precedent_value", 0.8),
                    },
                    timestamp=datetime.now(),
                    limitations=["案例推理仅供参考,具体情况需具体分析"],
                    is_certain=confidence.value >= 0.85,
                    is_sayable=True,
                )
                results.append(result)

        return results

    async def _calculate_case_similarity(self, text: str, case: dict[str, Any]) -> float:
        """计算案例相似度"""
        if not self.embedding_model:
            return 0.0

        try:
            # 关键词匹配相似度
            text_words = set(text.lower().split())
            case_keywords = {kw.lower() for kw in case.get("keywords", [])}

            keyword_similarity = len(text_words & case_keywords) / max(
                len(text_words | case_keywords), 1
            )

            # 语义相似度(如果有嵌入模型)
            semantic_similarity = 0.0
            if self.embedding_model and case.get("facts"):
                semantic_similarity = self._calculate_semantic_similarity(text, case["facts"])

            # 综合相似度
            combined_similarity = keyword_similarity * 0.4 + semantic_similarity * 0.6

            return combined_similarity

        except Exception as e:
            return 0.0

    async def _causal_reasoning_v4(
        self, query: str, context: Optional[str, str]
    ) -> list[ReasoningResultV4]:
        """因果推理 - v4.0版本"""
        results = []

        # 简化的因果推理实现
        causal_patterns = {
            "cause_effect": ["因为", "由于", "导致", "引起", "造成"],
            "temporal": ["先", "然后", "之后", "随后", "接着"],
            "condition": ["如果", "假如", "只要", "一旦", "若是"],
        }

        text = f"{query} {context or ''}"

        for pattern_type, indicators in causal_patterns.items():
            for indicator in indicators:
                if indicator in text:
                    # 简单的因果分析
                    parts = text.split(indicator)
                    if len(parts) >= 2:
                        cause = parts[0].strip()
                        effect = parts[1].strip()

                        # v4.0量化
                        claim = f"识别到因果关系:{cause} -> {effect}"
                        evidence = [f"因果指示词: {indicator}"]
                        confidence = self._quantify_confidence(
                            claim=claim,
                            evidence=evidence,
                            information_completeness=0.6,  # 因果推理置信度中等
                        )
                        confidence.value = 0.6

                        result = ReasoningResultV4(
                            reasoning_type=ReasoningType.CAUSAL,
                            conclusion=f"识别到因果关系:{cause} -> {effect}",
                            confidence=confidence,
                            evidence=evidence,
                            reasoning_path=[f"因果模式识别: {pattern_type}", "因果关系提取"],
                            metadata={
                                "pattern_type": pattern_type,
                                "indicator": indicator,
                                "cause": cause,
                                "effect": effect,
                            },
                            timestamp=datetime.now(),
                            limitations=["因果推理基于语言模式,需结合实际情况验证"],
                            is_certain=False,
                            is_sayable=True,
                        )
                        results.append(result)
                        break

        return results

    async def _hybrid_reasoning_v4(
        self, initial_results: list[ReasoningResultV4], query: str, context: Optional[str]
    ) -> list[ReasoningResultV4]:
        """混合推理 - v4.0版本"""
        results = []

        if len(initial_results) < 2:
            return results

        try:
            # 找到置信度最高的几个结果
            top_results = sorted(initial_results, key=lambda x: x.confidence.value, reverse=True)[
                :3
            ]

            # 构建混合推理结论
            conclusions = [result.conclusion for result in top_results]
            confidences = [result.confidence.value for result in top_results]

            # 加权平均置信度
            avg_confidence = sum(confidences) / len(confidences)

            # 合并证据
            all_evidence = []
            for result in top_results:
                all_evidence.extend(result.evidence)

            # v4.0量化
            claim = "综合多种推理方法分析"
            evidence = list(set(all_evidence))
            confidence = self._quantify_confidence(
                claim=claim, evidence=evidence, information_completeness=avg_confidence
            )
            confidence.value = avg_confidence

            # 构建推理路径
            reasoning_path = ["混合推理分析"]
            for i, result in enumerate(top_results, 1):
                reasoning_path.append(
                    f"{i}. {result.reasoning_type.value}: {result.confidence.value:.2f}"
                )

            hybrid_conclusion = f"综合多种推理方法分析,{'; '.join(conclusions[:2])}"

            # 识别局限性
            limitations = ["混合推理基于多种方法,需结合具体场景"]
            if avg_confidence < 0.7:
                limitations.append("综合置信度不足,建议寻求更多证据")

            result = ReasoningResultV4(
                reasoning_type=ReasoningType.HYBRID,
                conclusion=hybrid_conclusion,
                confidence=confidence,
                evidence=evidence,
                reasoning_path=reasoning_path,
                metadata={
                    "combined_results": len(top_results),
                    "component_types": [r.reasoning_type.value for r in top_results],
                    "reasoning_method": "weighted_average",
                },
                timestamp=datetime.now(),
                limitations=limitations,
                is_certain=avg_confidence >= 0.9,
                is_sayable=True,
            )

            results.append(result)

        except Exception as e:
            logger.warning(f"⚠️ 案例推理失败: {e}")

        return results

    async def explain_uncertainty(self, result: ReasoningResultV4) -> str:
        """解释推理结果的不确定性 - v4.0核心特性"""
        return self.response_builder.build_response(
            claim=result.conclusion, evidence=result.evidence, completeness=result.confidence.value
        )

    def get_reasoning_statistics(self) -> dict[str, Any]:
        """获取推理统计信息"""
        return {
            "total_rules": len(self.reasoning_rules),
            "total_cases": len(self.case_database),
            "domains": list({rule.domain for rule in self.reasoning_rules.values()}),
            "reasoning_types": [rt.value for rt in ReasoningType],
            "ontology_concepts": {
                domain: sum(len(concepts) for concepts in categories.values())
                for domain, categories in self.ontology_concepts.items()
            },
            "total_reasonings": len(self.reasoning_history),
            "average_confidence": (
                sum(r["best_confidence"] for r in self.reasoning_history)
                / len(self.reasoning_history)
                if self.reasoning_history
                else 0.0
            ),
        }


# 全局实例
reasoning_engine_v4 = SemanticReasoningEngineV4()


@async_main
async def main():
    """测试v4.0语义推理引擎"""
    print("🧠 测试v4.0语义推理引擎(维特根斯坦版)...")

    engine = SemanticReasoningEngineV4()

    try:
        # 测试查询
        test_queries = [
            {
                "query": "某公司未经许可使用了我的专利技术,我该如何维权?",
                "context": "该公司生产的产品包含了我的专利权利要求中的所有技术特征",
                "domain": "patent",
            },
            {
                "query": "这份合同是否有效?",
                "context": "双方都是完全民事行为能力人,自愿签订合同,内容不违反法律规定",
                "domain": "legal",
            },
            {
                "query": "这个发明是否具有专利新颖性?",
                "context": "在申请日之前,没有人公开过相同的技术方案",
                "domain": "patent",
            },
        ]

        print("\n" + "=" * 80)
        print("🧠 v4.0语义推理测试结果:")
        print("=" * 80)

        for i, test_case in enumerate(test_queries, 1):
            print(f"\n{'='*80}")
            print(f"{i}. 测试查询 ({test_case['domain']}):")
            print(f"   查询: {test_case['query']}")
            if test_case["context"]:
                print(f"   上下文: {test_case['context'][:50]}...")

            # 执行推理
            results = await engine.reason(
                query=test_case["query"], context=test_case["context"], domain=test_case["domain"]
            )

            print(f"   🎯 推理结果: {len(results)} 个")

            for j, result in enumerate(results[:2], 1):  # 显示前2个结果
                print(f"\n   结果 {j}:")
                print(f"     类型: {result.reasoning_type.value}")
                print(
                    f"     置信度: {result.confidence.value:.2f} ({result.confidence.level.value})"
                )

                # v4.0特性:显示详细的不确定性解释
                explanation = await engine.explain_uncertainty(result)
                print(f"     {explanation}")

                if result.limitations:
                    print(f"     ⚠️ 局限性: {'; '.join(result.limitations)}")

        # 显示推理统计
        stats = engine.get_reasoning_statistics()
        print("\n" + "=" * 80)
        print("📊 v4.0推理引擎统计:")
        print("=" * 80)
        print(f"   推理规则数: {stats['total_rules']}")
        print(f"   案例数量: {stats['total_cases']}")
        print(f"   支持领域: {', '.join(stats['domains'])}")
        print(f"   推理类型: {', '.join(stats['reasoning_types'])}")
        print(f"   历史推理: {stats['total_reasonings']} 次")
        print(f"   平均置信度: {stats['average_confidence']:.2f}")

        print("\n🎉 v4.0语义推理引擎测试完成!")
        print("✨ 核心特性:诚实(明确不确定性)、精确(证据支持)、敬畏(承认局限)")
        return 0

    except Exception as e:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
