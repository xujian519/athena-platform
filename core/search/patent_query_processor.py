#!/usr/bin/env python3
"""
专利查询处理器
Patent Query Processor

实现查询扩展、意图识别和查询优化
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.text_processing.patent_text_processor import get_patent_text_processor

# 配置日志
logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """查询意图枚举"""

    SEARCH = "search"  # 普通搜索
    NOVELTY = "novelty_search"  # 新颖性检索
    INVALIDITY = "invalidity_search"  # 无效检索
    INFRINGEMENT = "infringement"  # 侵权分析
    TECHNOLOGY_TREND = "tech_trend"  # 技术趋势
    PATENT_LANDSCAPE = "landscape"  # 专利布局
    SIMILARITY = "similarity"  # 相似性分析
    LEGAL_STATUS = "legal_status"  # 法律状态查询


class QueryType(Enum):
    """查询类型枚举"""

    KEYWORD = "keyword"  # 关键词查询
    SEMANTIC = "semantic"  # 语义查询
    STRUCTURED = "structured"  # 结构化查询
    NATURAL_LANGUAGE = "natural"  # 自然语言查询
    MIXED = "mixed"  # 混合查询


@dataclass
class ProcessedQuery:
    """处理后的查询"""

    original: str
    cleaned: str
    normalized: str
    intent: QueryIntent
    query_type: QueryType
    expanded_terms: list[str]
    filters: dict[str, Any]
    confidence: float
    explanation: str


class PatentQueryProcessor:
    """专利查询处理器"""

    def __init__(self):
        """初始化查询处理器"""
        logger.info("初始化专利查询处理器...")

        # 获取文本处理器
        self.text_processor = get_patent_text_processor()

        # 意图识别规则
        self.intent_patterns = self._load_intent_patterns()

        # 查询扩展资源
        self.synonym_dict = self._load_synonym_dict()
        self.tech_hierarchy = self._load_tech_hierarchy()
        self.ipc_mappings = self._load_ipc_mappings()

        # 查询模板
        self.query_templates = self._load_query_templates()

        logger.info("专利查询处理器初始化完成")

    def _load_intent_patterns(self) -> dict[str, tuple[QueryIntent, str]]:
        """加载意图识别模式"""
        return {
            # 新颖性检索
            r"新颖性|检索报告|查新|现有技术": (QueryIntent.NOVELTY, "新颖性检索模式"),
            r"是否具有新颖性|有没有新颖性": (QueryIntent.NOVELTY, "新颖性判断查询"),
            # 无效检索
            r"无效|无效宣告|无效检索|patent invalidity": (QueryIntent.INVALIDITY, "专利无效检索"),
            r"不具备.*性|缺少.*性|不满足.*性": (QueryIntent.INVALIDITY, "专利性分析"),
            # 侵权分析
            r"侵权|是否侵权|侵权风险|infringement": (QueryIntent.INFRINGEMENT, "侵权分析查询"),
            r"落入.*保护范围|是否涵盖|是否包含": (QueryIntent.INFRINGEMENT, "保护范围判断"),
            # 技术趋势
            r"趋势|发展趋势|技术发展|tech trend": (QueryIntent.TECHNOLOGY_TREND, "技术趋势分析"),
            r"发展历程|演进|发展路径": (QueryIntent.TECHNOLOGY_TREND, "技术演进查询"),
            # 专利布局
            r"布局|专利地图|专利分布|landscape": (QueryIntent.PATENT_LANDSCAPE, "专利布局分析"),
            r"竞争格局|主要申请人|核心专利": (QueryIntent.PATENT_LANDSCAPE, "竞争分析查询"),
            # 相似性分析
            r"相似|类似|相近|同样的|equivalent": (QueryIntent.SIMILARITY, "相似性分析"),
            r"对比|比较|difference": (QueryIntent.SIMILARITY, "对比分析"),
            # 法律状态
            r"法律状态|是否有效|有效期|legal status": (QueryIntent.LEGAL_STATUS, "法律状态查询"),
            r"授权|驳回|撤回|abandon": (QueryIntent.LEGAL_STATUS, "法律状态详情"),
        }

    def _load_synonym_dict(self) -> dict[str, list[str]]:
        """加载同义词词典"""
        return {
            # 技术术语同义词
            "人工智能": ["AI", "机器学习", "ML", "深度学习", "DL", "智能"],
            "神经网络": ["neural network", "NN", "深度神经网络", "DNN"],
            "卷积神经网络": ["CNN", "convolutional neural network", "卷积网络"],
            "循环神经网络": ["RNN", "recurrent neural network", "循环网络"],
            "注意力机制": ["attention", "注意力", "self-attention", "自注意力"],
            "区块链": ["blockchain", "分布式账本", "DLT", "链", "块链"],
            "物联网": ["IoT", "Internet of Things", "万物互联"],
            "云计算": ["cloud computing", "云服务", "云平台", "cloud"],
            "大数据": ["big data", "海量数据", "巨量数据"],
            "机器学习": ["machine learning", "ML", "统计学习"],
            "自然语言处理": ["NLP", "natural language processing", "文本处理"],
            "计算机视觉": ["CV", "computer vision", "图像识别", "视觉计算"],
            "语音识别": ["speech recognition", "ASR", "语音转文本", "speech to text"],
            # 专利术语同义词
            "权利要求": ["claims", "claim", "权要", "专利权项"],
            "说明书": ["specification", "描述书", "说明文档"],
            "摘要": ["abstract", "概要", "简介"],
            "现有技术": ["prior art", "背景技术", "已有技术", "先前技术"],
            "技术方案": ["technical solution", "技术解决方案", "方案"],
            "实施例": ["embodiment", "具体实施方式", "实现方式"],
            "优先权": ["priority", "优先权日", "priority date"],
            "公开日": ["publication date", "公开日期", "发布日期"],
            "申请日": ["filing date", "申请日期"],
            "发明人": ["inventor", "发明者"],
            "申请人": ["applicant", "申请主体", "专利权人"],
        }

    def _load_tech_hierarchy(self) -> dict[str, list[str]]:
        """加载技术层次结构"""
        return {
            "人工智能": [
                "机器学习",
                "深度学习",
                "强化学习",
                "监督学习",
                "无监督学习",
                "神经网络",
                "卷积神经网络",
                "循环神经网络",
                "生成对抗网络",
            ],
            "区块链": [
                "分布式账本",
                "共识机制",
                "智能合约",
                "加密算法",
                "工作量证明",
                "权益证明",
                "区块链网络",
            ],
            "物联网": [
                "传感器",
                "无线通信",
                "边缘计算",
                "云计算",
                "物联网协议",
                "物联网安全",
                "物联网平台",
            ],
            "计算机视觉": [
                "图像处理",
                "目标检测",
                "图像分割",
                "人脸识别",
                "OCR",
                "视频分析",
                "三维重建",
            ],
        }

    def _load_ipc_mappings(self) -> dict[str, str | list[str]]:
        """加载IPC分类映射"""
        return {
            # A部 - 人类生活必需
            "农业": "A01",
            "食品": ["A21", "A23"],
            "医疗": ["A61", "A63"],
            "个人用品": ["A41", "A42", "A43", "A44", "A45", "A46", "A47"],
            # B部 - 作业;运输
            "物理化学": "B01",
            "机械": ["B23", "B24", "B25", "B26", "B27", "B29", "B30"],
            "运输": ["B60", "B61", "B62", "B63", "B64", "B65"],
            # C部 - 化学;冶金
            "化学": ["C01", "C02", "C03", "C04", "C05", "C06", "C07"],
            "冶金": ["C21", "C22"],
            "有机化学": "C07",
            "高分子": "C08",
            # D部 - 纺织;造纸
            "纺织": ["D01", "D02", "D03", "D04", "D05", "D06", "D07"],
            "造纸": "D21",
            # E部 - 固定建筑物
            "建筑": ["E01", "E02", "E03", "E04", "E05", "E06"],
            "土木": "E21",
            # F部 - 机械工程;照明;加热;武器;爆破
            "机械工程": ["F01", "F02", "F03", "F04"],
            "照明": "F21",
            "加热": ["F22", "F23", "F24", "F25", "F26", "F27", "F28"],
            "武器": ["F41", "F42"],
            # G部 - 物理
            "物理": ["G01", "G02", "G03", "G04", "G05", "G06", "G07", "G08", "G09", "G10"],
            "光学": "G02",
            "控制": "G05",
            "计算": ["G06", "G11"],
            "信息": "G11",
            "测量": "G01",
            "核物理": "G21",
            # H部 - 电学
            "电学": ["H01", "H02", "H03", "H04", "H05"],
            "通信": "H04",
            "电子电路": "H03",
            "电力": "H02",
        }

    def _load_query_templates(self) -> dict[str, str]:
        """加载查询模板"""
        return {
            "novelty": "{terms} AND (公开日 < '{date}')",
            "invalidity": "{terms} AND (公开日 < '{date}')",
            "infringement": "{terms} AND (权利要求 containing '{key_claim}')",
            "trend": "{terms} GROUP BY 申请日",
            "landscape": "{terms} AND ({ipc_filter})",
            "similarity": "{terms} SIMILAR TO '{patent_id}'",
            "legal_status": "{patent_id} legal_status",
        }

    def process_query(self, query: str, context: dict[str, Any] | None = None) -> ProcessedQuery:
        """
        处理查询

        Args:
            query: 原始查询
            context: 上下文信息(如用户历史、偏好等)

        Returns:
            处理后的查询对象
        """
        logger.info(f"处理查询: {query}")

        # 1. 清洗和标准化
        cleaned = self.text_processor.clean_text(query)
        normalized = self.text_processor.normalize_text(cleaned)

        # 2. 意图识别
        intent, _intent_explanation = self._identify_intent(query)

        # 3. 查询类型判断
        query_type = self._detect_query_type(query)

        # 4. 查询扩展
        expanded_terms = self._expand_query(normalized, intent)

        # 5. 提取过滤条件
        filters = self._extract_filters(query, context)

        # 6. 计算置信度
        confidence = self._calculate_confidence(query, intent, query_type)

        # 7. 生成解释
        explanation = self._generate_explanation(query, intent, query_type, expanded_terms, filters)

        processed_query = ProcessedQuery(
            original=query,
            cleaned=cleaned,
            normalized=normalized,
            intent=intent,
            query_type=query_type,
            expanded_terms=expanded_terms,
            filters=filters,
            confidence=confidence,
            explanation=explanation,
        )

        logger.info(f"查询处理完成: 意图={intent.value}, 类型={query_type.value}")

        return processed_query

    def _identify_intent(self, query: str) -> tuple[QueryIntent, str]:
        """识别查询意图"""
        for pattern, (intent, explanation) in self.intent_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return intent, explanation

        # 默认为普通搜索
        return QueryIntent.SEARCH, "普通专利搜索"

    def _detect_query_type(self, query: str) -> QueryType:
        """检测查询类型"""
        # 检查是否有结构化查询特征
        if re.search(r"IPC[:=]|申请日期[:=]|申请人[:=]", query):
            return QueryType.STRUCTURED

        # 检查是否为自然语言查询
        if len(query) > 30 and any(
            word in query for word in ["请", "帮我", "查找", "搜索", "分析"]
        ):
            return QueryType.NATURAL_LANGUAGE

        # 检查是否包含多个概念
        words = self.text_processor.tokenize(query)
        if len(words) > 3:
            return QueryType.SEMANTIC

        # 默认为关键词查询
        return QueryType.KEYWORD

    def _expand_query(self, query: str, intent: QueryIntent) -> list[str]:
        """查询扩展"""
        words = self.text_processor.tokenize(query)
        expanded = list(words)  # 保留原始词

        # 同义词扩展
        for word in words:
            if word in self.synonym_dict:
                synonyms = self.synonym_dict[word]
                expanded.extend(synonyms[:2])  # 最多添加2个同义词

        # 技术层次扩展
        for word in words:
            if word in self.tech_hierarchy:
                related_terms = self.tech_hierarchy[word]
                expanded.extend(related_terms[:3])  # 最多添加3个相关词

        # 意图特定的扩展
        if intent == QueryIntent.NOVELTY:
            # 新颖性检索需要扩展技术特征词
            expanded.extend(["技术方案", "实现方法", "结构特征"])
        elif intent == QueryIntent.INVALIDITY:
            # 无效检索需要扩展法律特征词
            expanded.extend(["缺陷", "不足", "公开不充分", "不支持"])

        # 去重并限制数量
        expanded = list(set(expanded))
        return expanded[:15]  # 最多保留15个词

    def _extract_filters(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """提取过滤条件"""
        filters = {}

        # IPC分类过滤
        ipc_pattern = r"IPC[:\s=]\s*([ABCDEFGH]\d{2}[A-Z])"
        ipc_match = re.search(ipc_pattern, query)
        if ipc_match:
            filters["ipc_codes"] = [ipc_match.group(1)]

        # 日期过滤
        date_patterns = [
            (r"申请日期[:\s=]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})", "filing_date"),
            (r"公开日期[:\s=]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})", "publication_date"),
            (r"(\d{4})年之后", "after_year"),
            (r"(\d{4})年之前", "before_year"),
        ]
        for pattern, field in date_patterns:
            match = re.search(pattern, query)
            if match:
                filters[field] = match.group(1)

        # 申请人过滤
        applicant_pattern = r"申请人[:\s=]\s*([^\s,,、]+)"
        applicant_match = re.search(applicant_pattern, query)
        if applicant_match:
            filters["applicant"] = applicant_match.group(1)

        # 专利类型过滤
        if any(word in query for word in ["发明", "invention"]):
            filters["patent_type"] = "invention"
        elif any(word in query for word in ["实用新型", "utility"]):
            filters["patent_type"] = "utility_model"
        elif any(word in query for word in ["外观", "design"]):
            filters["patent_type"] = "design"

        # 从上下文添加过滤条件
        if context and "user_preferences" in context:
            pref = context["user_preferences"]
            if "default_ipc" in pref:
                filters.setdefault("ipc_codes", []).extend(pref["default_ipc"])
            if "preferred_applicants" in pref:
                filters.setdefault("applicants", []).extend(pref["preferred_applicants"])

        return filters

    def _calculate_confidence(
        self, query: str, intent: QueryIntent, query_type: QueryType
    ) -> float:
        """计算处理置信度"""
        confidence = 0.5  # 基础置信度

        # 意图明确的查询增加置信度
        if intent != QueryIntent.SEARCH:
            confidence += 0.2

        # 结构化查询增加置信度
        if query_type == QueryType.STRUCTURED:
            confidence += 0.2

        # 包含专业术语增加置信度
        tech_terms = sum(
            1
            for word in self.text_processor.tokenize(query)
            if word in self.text_processor.patent_terms
        )
        if tech_terms > 0:
            confidence += min(0.2, tech_terms * 0.05)

        return min(confidence, 1.0)

    def _generate_explanation(
        self,
        original: str,
        intent: QueryIntent,
        query_type: QueryType,
        expanded_terms: list[str],
        filters: dict[str, Any],    ) -> str:
        """生成查询处理解释"""
        explanation_parts = [f"识别意图: {intent.value}", f"查询类型: {query_type.value}"]

        if expanded_terms != self.text_processor.tokenize(original):
            explanation_parts.append(f"扩展查询词: {', '.join(expanded_terms)}")

        if filters:
            filter_strs = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_strs.append(f"{key}: {', '.join(map(str, value))}")
                else:
                    filter_strs.append(f"{key}: {value}")
            explanation_parts.append(f"应用过滤: {'; '.join(filter_strs)}")

        return " | ".join(explanation_parts)

    def suggest_queries(
        self, processed_query: ProcessedQuery, num_suggestions: int = 5
    ) -> list[str]:
        """
        建议相关查询

        Args:
            processed_query: 处理后的查询
            num_suggestions: 建议数量

        Returns:
            建议查询列表
        """
        suggestions = []

        # 基于意图的建议
        if processed_query.intent == QueryIntent.SEARCH:
            # 建议更具体的查询
            terms = processed_query.expanded_terms[:3]
            suggestions.append(f"{' AND '.join(terms)} AND 申请日期 > 2020-01-01")
            suggestions.append(f"{' AND '.join(terms)} AND 申请人 != '")

        # 基于关键词的建议
        if processed_query.expanded_terms:
            for term in processed_query.expanded_terms[:2]:
                if term in self.tech_hierarchy:
                    # 添加相关技术词
                    related = self.tech_hierarchy[term][:2]
                    suggestion = f"{processed_query.original} OR {' OR '.join(related)}"
                    suggestions.append(suggestion)

        # 基于IPC的建议
        for word in processed_query.expanded_terms:
            if word in self.ipc_mappings:
                ipc = self.ipc_mappings[word]
                suggestions.append(f"{processed_query.original} IPC:{ipc}")

        # 去重并限制数量
        suggestions = list(set(suggestions))
        return suggestions[:num_suggestions]

    def get_query_statistics(self, queries: list[str]) -> dict[str, Any]:
        """
        获取查询统计信息

        Args:
            queries: 查询列表

        Returns:
            统计信息字典
        """
        stats: dict[str, Any] = {
            "total_queries": len(queries),
            "intent_distribution": defaultdict(int),
            "type_distribution": defaultdict(int),
            "avg_query_length": 0,
            "most_common_terms": [],
            "filter_usage": defaultdict(int),
        }

        total_length = 0
        term_counter: dict[str, int] = defaultdict(int)  # type: ignore[assignment]

        for query in queries:
            # 处理查询
            processed = self.process_query(query)

            # 统计意图和类型
            stats["intent_distribution"][processed.intent.value] += 1
            stats["type_distribution"][processed.query_type.value] += 1

            # 统计查询长度
            total_length += len(processed.original)

            # 统计词汇
            for term in processed.expanded_terms:
                term_counter[term] += 1

            # 统计过滤条件使用
            for filter_key in processed.filters:
                stats["filter_usage"][filter_key] += 1

        # 计算平均长度
        if queries:
            stats["avg_query_length"] = total_length / len(queries)

        # 最常见词汇
        stats["most_common_terms"] = [
            (term, count)
            for term, count in sorted(term_counter.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]  # type: ignore
        ]

        return stats


# 全局实例
_query_processor = None


def get_patent_query_processor() -> PatentQueryProcessor:
    """获取专利查询处理器单例"""
    global _query_processor
    if _query_processor is None:
        _query_processor = PatentQueryProcessor()
    return _query_processor
