#!/usr/bin/env python3
"""
高级专利检索系统 - 提升检索准确性和覆盖范围
Advanced Patent Search System - Enhanced Accuracy and Coverage

针对专利检索的高准确性要求,集成:
1. 智能查询扩展和同义词分析
2. 布尔逻辑检索式构建
3. 多维度检索策略
4. 相关性评分优化
5. 专利分类系统匹配
"""

import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any



logger = logging.getLogger(__name__)


class SearchStrategy(Enum):
    """检索策略枚举"""

    KEYWORD_EXACT = "keyword_exact"  # 精确关键词匹配
    BOOLEAN_LOGIC = "boolean_logic"  # 布尔逻辑检索
    SEMANTIC_EXPANSION = "semantic_expansion"  # 语义扩展检索
    CLASSIFICATION_BASED = "classification_based"  # 基于分类检索
    HYBRID_APPROACH = "hybrid_approach"  # 混合策略


@dataclass
class SearchTerm:
    """检索词数据结构"""

    term: str
    weight: float = 1.0
    is_mandatory: bool = False
    is_excluded: bool = False
    synonyms: list[str] | None = None
    field_specific: dict[str, list[str]] | None = None  # 字段特定检索词


@dataclass
class SearchQuery:
    """增强检索查询结构"""

    original_query: str
    expanded_terms: list[SearchTerm]
    boolean_expression: str
    ipc_classifications: list[str]
    date_range: dict[str, str] | None = None
    assignee_filters: list[str] | None = None
    inventor_filters: list[str] | None = None
    strategy: SearchStrategy = SearchStrategy.HYBRID_APPROACH


class AdvancedPatentSearchSystem:
    """高级专利检索系统"""

    def __init__(self, download_dir: str | None = None):
        """初始化高级检索系统"""
        # 导入基础检索器
        from .enhanced_patent_retriever import EnhancedPatentRetriever

        self.base_retriever = EnhancedPatentRetriever(download_dir)

        # 初始化同义词词典和技术映射
        self.technical_synonyms = self._load_technical_synonyms()
        self.ipc_mapping = self._load_ipc_mapping()
        self.field_mapping = self._load_field_mapping()

        # 检索历史和缓存
        self.search_history = []
        self.query_cache = {}

        # 性能参数
        self.max_expansion_terms = 10
        self.relevance_threshold = 0.3
        self.max_search_rounds = 3

    async def initialize(self):
        """初始化检索系统"""
        await self.base_retriever.initialize()
        logger.info("✅ 高级专利检索系统初始化完成")

    async def close(self):
        """关闭检索系统"""
        await self.base_retriever.close()

    def _load_technical_synonyms(self) -> dict[str, list[str]]:
        """加载技术同义词词典"""
        return {
            # 人工智能相关
            "artificial intelligence": [
                "AI",
                "machine intelligence",
                "cognitive computing",
                "intelligent system",
            ],
            "machine learning": [
                "ML",
                "statistical learning",
                "pattern recognition",
                "predictive modeling",
            ],
            "deep learning": [
                "DL",
                "neural network",
                "deep neural network",
                "CNN",
                "RNN",
                "LSTM",
                "Transformer",
            ],
            "neural network": [
                "NN",
                "artificial neural network",
                "ANN",
                "perceptron",
                "multi-layer perceptron",
            ],
            "algorithm": ["method", "procedure", "technique", "approach", "computational method"],
            # 通信技术相关
            "5G": ["fifth generation", "5th generation", "next generation mobile", "IMT-2020"],
            "wireless communication": [
                "radio communication",
                "RF communication",
                "wireless transmission",
            ],
            "mobile communication": [
                "cellular communication",
                "mobile network",
                "cellular network",
            ],
            # 计算机技术相关
            "computer vision": [
                "image processing",
                "image analysis",
                "visual recognition",
                "object detection",
            ],
            "natural language processing": [
                "NLP",
                "text processing",
                "language understanding",
                "text analysis",
            ],
            "blockchain": [
                "distributed ledger",
                "DLT",
                "cryptocurrency",
                "smart contract",
                "decentralized",
            ],
            # 材料科学相关
            "nanotechnology": ["nano material", "nanoparticle", "nanostructure", "quantum dot"],
            "composite material": [
                "composite",
                "reinforced material",
                "fiber reinforced",
                "polymer composite",
            ],
            # 医疗技术相关
            "medical device": [
                "healthcare device",
                "diagnostic device",
                "therapeutic device",
                "clinical device",
            ],
            "biotechnology": [
                "genetic engineering",
                "gene therapy",
                "biopharmaceutical",
                "molecular biology",
            ],
            # 通用技术词汇
            "system": ["apparatus", "device", "equipment", "mechanism", "arrangement"],
            "method": ["process", "procedure", "technique", "approach", "algorithm"],
            "data": ["information", "signal", "dataset", "digital content"],
            "network": ["communication network", "data network", "connectivity", "interconnection"],
            "control": ["management", "regulation", "supervision", "optimization"],
        }

    def _load_ipc_mapping(self) -> dict[str, list[str]]:
        """加载IPC分类映射"""
        return {
            "G06F": ["Electric digital data processing", "Computer technology", "Data processing"],
            "G06N": ["Neural networks", "Machine learning", "Artificial intelligence"],
            "H04L": ["Digital information transmission", "Data communication", "Network protocols"],
            "H04W": [
                "Wireless communication networks",
                "Mobile communication",
                "Radio communication",
            ],
            "H04B": ["Radio transmission", "Wireless communication", "Radio communication"],
            "G01N": ["Testing", "Measurement", "Analysis", "Sensing"],
            "A61B": ["Medical diagnosis", "Medical equipment", "Healthcare"],
            "A61K": ["Medical preparations", "Pharmaceuticals", "Drug delivery"],
            "C07K": ["Peptides", "Proteins", "Biotechnology"],
            "B01D": ["Separation", "Filtration", "Purification"],
            "C08L": ["Compositions", "Polymer compositions", "Material science"],
            "H01M": ["Batteries", "Energy storage", "Electrochemical devices"],
        }

    def _load_field_mapping(self) -> dict[str, str]:
        """加载字段映射表"""
        return {
            "title": "intitle:",  # 标题字段
            "abstract": "inabstract:",  # 摘要字段
            "claims": "inclaims:",  # 权利要求字段
            "description": "indescription:",  # 说明书字段
            "inventor": "inventor:",  # 发明人字段
            "assignee": "assignee:",  # 申请人字段
            "ipc": "CPC:",  # IPC/CPC分类字段
            "publication": "publication:",  # 公开号字段
            "application": "application:",  # 申请号字段
            "priority": "priority:",  # 优先权字段
            "family": "family:",  # 专利族字段
            "citing": "citing:",  # 引用字段
            "citedby": "citedby:",  # 被引用字段
        }

    async def enhanced_patent_search(
        self,
        query: str,
        max_results: int = 50,
        search_strategy: SearchStrategy = SearchStrategy.HYBRID_APPROACH,
        accuracy_level: str = "high",
    ) -> dict[str, Any]:
        """
        高级专利检索主入口

        Args:
            query: 检索查询
            max_results: 最大结果数
            search_strategy: 检索策略
            accuracy_level: 准确性要求 ('low', 'medium', 'high')

        Returns:
            增强的检索结果
        """
        logger.info(f"🚀 开始高级专利检索: '{query}'")
        logger.info(f"📋 策略: {search_strategy.value}, 准确性要求: {accuracy_level}")

        start_time = time.time()

        try:
            # 步骤1: 查询理解和扩展
            enhanced_query = await self._analyze_and_expand_query(query, accuracy_level)

            # 步骤2: 构建检索式
            search_expressions = self._construct_search_expressions(enhanced_query, search_strategy)

            # 步骤3: 多轮检索
            all_patents = []
            for round_num, expression in enumerate(search_expressions, 1):
                logger.info(f"🔄 第{round_num}轮检索: {expression[:100]}...")

                # 执行基础检索
                patents = await self.base_retriever.search_patents(
                    query=expression,
                    limit=max_results // len(search_expressions) + 10,
                    download_pdfs=False,  # 先不下载PDF,提高检索速度
                    get_fulltext=True,
                )

                # 应用高级过滤
                filtered_patents = await self._apply_advanced_filters(
                    patents, enhanced_query, accuracy_level
                )

                all_patents.extend(filtered_patents)

                # 如果已经找到足够多的高质量结果,可以提前结束
                high_quality_patents = [p for p in all_patents if p.get("relevance_score", 0) > 0.7]
                if len(high_quality_patents) >= max_results * 0.8:
                    logger.info("✅ 已找到足够高质量专利,提前结束检索")
                    break

            # 步骤4: 去重和排序
            deduplicated_patents = self._deduplicate_and_rank(all_patents, enhanced_query)

            # 步骤5: 限制结果数量
            final_results = deduplicated_patents[:max_results]

            # 步骤6: 为需要的专利下载PDF
            if accuracy_level in ["medium", "high"]:
                final_results = await self._download_pdfs_for_top_results(final_results)

            execution_time = time.time() - start_time

            # 生成检索报告
            search_report = self._generate_search_report(
                query, enhanced_query, final_results, execution_time
            )

            logger.info(f"✅ 高级检索完成: {len(final_results)}个专利,耗时{execution_time:.2f}秒")

            return {
                "query": query,
                "enhanced_query": enhanced_query,
                "strategy": search_strategy.value,
                "accuracy_level": accuracy_level,
                "results": final_results,
                "total_found": len(final_results),
                "execution_time": execution_time,
                "search_report": search_report,
            }

        except Exception as e:
            logger.error(f"❌ 高级专利检索失败: {e}")
            raise

    async def _analyze_and_expand_query(self, query: str, accuracy_level: str) -> SearchQuery:
        """查询理解和扩展"""
        logger.info("🧠 步骤1: 查询理解和扩展")

        # 基础分词和清理
        clean_query = self._clean_query(query)
        terms = self._extract_terms(clean_query)

        # 语义扩展
        expanded_terms = []
        for term in terms:
            search_term = SearchTerm(term=term)

            # 同义词扩展
            synonyms = self._get_synonyms(term)
            if synonyms and accuracy_level in ["medium", "high"]:
                search_term.synonyms = synonyms[: self.max_expansion_terms]

            # 字段特定扩展
            field_terms = self._get_field_specific_terms(term, accuracy_level)
            if field_terms:
                search_term.field_specific = field_terms

            # 权重分配
            search_term.weight = self._calculate_term_weight(term, terms)

            expanded_terms.append(search_term)

        # 构建布尔表达式
        boolean_expression = self._build_boolean_expression(expanded_terms, accuracy_level)

        # 自动IPC分类建议
        ipc_classifications = self._suggest_ipc_classifications(expanded_terms)

        return SearchQuery(
            original_query=query,
            expanded_terms=expanded_terms,
            boolean_expression=boolean_expression,
            ipc_classifications=ipc_classifications,
            strategy=SearchStrategy.HYBRID_APPROACH,
        )

    def _clean_query(self, query: str) -> str:
        """清理查询字符串"""
        # 转小写,移除特殊字符,保留技术术语
        cleaned = query.lower().strip()
        # 移除停用词但保留技术含义
        stop_words = {"a", "an", "the", "for", "and", "or", "but", "in", "on", "at", "to", "of"}
        words = [word for word in cleaned.split() if word not in stop_words]
        return " ".join(words)

    def _extract_terms(self, query: str) -> list[str]:
        """提取关键术语"""
        # 使用正则表达式提取技术术语
        # 这里简化处理,实际可以使用更复杂的NLP技术
        terms = []

        # 提取引号中的精确短语
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)
        terms.extend(phrases)

        # 移除已提取的短语
        query_without_phrases = re.sub(phrase_pattern, "", query)

        # 提取单个技术词汇
        words = [word.strip() for word in query_without_phrases.split() if len(word) > 2]
        terms.extend(words)

        return terms

    def _get_synonyms(self, term: str) -> list[str]:
        """获取同义词"""
        synonyms = []

        # 直接同义词匹配
        if term in self.technical_synonyms:
            synonyms.extend(self.technical_synonyms[term])

        # 反向查找(这个词是某个其他词的同义词)
        for key, value_list in self.technical_synonyms.items():
            if term in value_list:
                synonyms.extend([key] + [v for v in value_list if v != term])

        # 部分匹配
        for key, value_list in self.technical_synonyms.items():
            if term in key or key in term:
                synonyms.extend(value_list)

        return list(set(synonyms))

    def _get_field_specific_terms(self, term: str, accuracy_level: str) -> dict[str, list[str]]:
        """获取字段特定检索词"""
        field_terms = {}

        if accuracy_level == "high":
            # 高精度检索需要字段特定搜索
            field_terms.update(
                {
                    "title": [term],  # 标题中必须包含
                    "abstract": [term],  # 摘要中包含
                    "claims": [term],  # 权利要求中包含
                }
            )

            # 对于某些术语,特别关注某些字段
            if term in ["method", "system", "apparatus"]:
                field_terms["title"] = [term]
                field_terms["claims"] = [term]
            elif term in ["material", "composition"]:
                field_terms["description"] = [term]  # 说明书中详细描述

        return field_terms

    def _calculate_term_weight(self, term: str, all_terms: list[str]) -> float:
        """计算术语权重"""
        base_weight = 1.0

        # 长度权重(长术语更具体)
        length_weight = min(len(term.split()) * 0.3, 1.0)

        # 唯一性权重(出现频率低的术语更重要)
        term_frequency = all_terms.count(term)
        uniqueness_weight = 1.0 / (1.0 + term_frequency)

        # 技术术语权重
        technical_terms = [
            "algorithm",
            "system",
            "method",
            "apparatus",
            "device",
            "network",
            "protocol",
        ]
        technical_weight = 1.2 if any(tech in term for tech in technical_terms) else 1.0

        return base_weight * length_weight * uniqueness_weight * technical_weight

    def _build_boolean_expression(self, terms: list[SearchTerm], accuracy_level: str) -> str:
        """构建布尔检索表达式"""
        expressions = []

        for search_term in terms:
            term_expressions = []

            # 原词
            term_expressions.append(search_term.term)

            # 同义词 (OR关系)
            if search_term.synonyms and accuracy_level in ["medium", "high"]:
                synonym_expr = " OR ".join(search_term.synonyms)
                term_expressions.append(f"({synonym_expr})")

            # 字段特定检索
            if search_term.field_specific and accuracy_level == "high":
                field_exprs = []
                for field, field_terms in search_term.field_specific.items():
                    if field in self.field_mapping:
                        field_prefix = self.field_mapping[field]
                        field_term = " OR ".join(field_terms)
                        field_exprs.append(f"{field_prefix}{field_term}")

                if field_exprs:
                    term_expressions.extend(field_exprs)

            # 组合术语的所有表达式
            if len(term_expressions) > 1:
                combined_expr = " OR ".join(term_expressions)
                expressions.append(f"({combined_expr})")
            else:
                expressions.append(term_expressions[0])

        # 构建最终表达式
        if accuracy_level == "high":
            # 高精度:所有术语都必须匹配 (AND关系)
            return " AND ".join(expressions)
        elif accuracy_level == "medium":
            # 中等精度:主要术语必须匹配,其他术语可选
            if expressions:
                mandatory_terms = [expr for expr in expressions if len(expr) > 2]  # 长术语作为必需
                optional_terms = [expr for expr in expressions if expr not in mandatory_terms]

                if mandatory_terms and optional_terms:
                    return f"({' AND '.join(mandatory_terms)}) AND ({' OR '.join(optional_terms)})"
                elif mandatory_terms:
                    return " AND ".join(mandatory_terms)
                else:
                    return " OR ".join(optional_terms)
            return " OR ".join(expressions)
        else:
            # 低精度:任意术语匹配即可 (OR关系)
            return " OR ".join(expressions)

    def _suggest_ipc_classifications(self, terms: list[SearchTerm]) -> list[str]:
        """建议IPC分类"""
        suggested_classes = []
        term_texts = [term.term.lower() for term in terms]

        for term_text in term_texts:
            for ipc_class, keywords in self.ipc_mapping.items():
                if any(
                    keyword.lower() in term_text or term_text in keyword.lower()
                    for keyword in keywords
                ) and ipc_class not in suggested_classes:
                    suggested_classes.append(ipc_class)

        return suggested_classes

    def _construct_search_expressions(
        self, enhanced_query: SearchQuery, strategy: SearchStrategy
    ) -> list[str]:
        """构建检索表达式"""
        expressions = []

        if strategy == SearchStrategy.BOOLEAN_LOGIC:
            expressions = [enhanced_query.boolean_expression]

        elif strategy == SearchStrategy.SEMANTIC_EXPANSION:
            # 语义扩展检索
            expressions.append(enhanced_query.boolean_expression)

            # 添加同义词检索
            for term in enhanced_query.expanded_terms:
                if term.synonyms:
                    synonym_expr = " OR ".join(term.synonyms)
                    expressions.append(synonym_expr)

        elif strategy == SearchStrategy.CLASSIFICATION_BASED:
            # 基于分类的检索
            for ipc in enhanced_query.ipc_classifications:
                classification_expr = (
                    f"{enhanced_query.boolean_expression} AND {self.field_mapping['ipc']}{ipc}"
                )
                expressions.append(classification_expr)

        elif strategy == SearchStrategy.HYBRID_APPROACH:
            # 混合策略:多种方法结合
            expressions.append(enhanced_query.boolean_expression)

            # 添加IPC分类检索
            for ipc in enhanced_query.ipc_classifications[:2]:  # 限制数量
                classification_expr = (
                    f"{enhanced_query.boolean_expression} AND {self.field_mapping['ipc']}{ipc}"
                )
                expressions.append(classification_expr)

            # 添加同义词检索
            main_terms = [term for term in enhanced_query.expanded_terms if term.weight > 1.0]
            if main_terms:
                synonym_expr = (
                    " OR ".join(main_terms[0].synonyms[:3]) if main_terms[0].synonyms else ""
                )
                if synonym_expr:
                    expressions.append(synonym_expr)

        return expressions[: self.max_search_rounds]  # 限制检索轮数

    async def _apply_advanced_filters(
        self, patents: list[dict[str, Any]], enhanced_query: SearchQuery, accuracy_level: str
    ) -> list[dict[str, Any]]:
        """应用高级过滤"""
        logger.info("🔍 应用高级过滤...")

        filtered_patents = []

        for patent in patents:
            if not patent.get("success"):
                continue

            # 计算相关性评分
            relevance_score = self._calculate_relevance_score(patent, enhanced_query)
            patent["relevance_score"] = relevance_score

            # 应用准确性阈值
            min_score = {"low": 0.2, "medium": 0.4, "high": 0.6}.get(accuracy_level, 0.4)

            if relevance_score >= min_score:
                # IPC分类过滤
                if enhanced_query.ipc_classifications:
                    patent_ipc = patent.get("ipc_classifications", [])
                    ipc_match = any(ipc in enhanced_query.ipc_classifications for ipc in patent_ipc)
                    if accuracy_level == "high" and not ipc_match:
                        continue

                filtered_patents.append(patent)

        return filtered_patents

    def _calculate_relevance_score(
        self, patent: dict[str, Any], enhanced_query: SearchQuery
    ) -> float:
        """计算专利相关性评分"""
        score = 0.0
        total_weight = sum(term.weight for term in enhanced_query.expanded_terms)

        if total_weight == 0:
            return 0.0

        patent_text = (
            patent.get("title", "")
            + " "
            + patent.get("abstract", "")
            + " "
            + patent.get("full_text", "")
        ).lower()

        for search_term in enhanced_query.expanded_terms:
            term_score = 0.0

            # 原词匹配
            term_matches = patent_text.count(search_term.term.lower())
            term_score += term_matches * search_term.weight

            # 同义词匹配
            if search_term.synonyms:
                for synonym in search_term.synonyms:
                    synonym_matches = patent_text.count(synonym.lower())
                    term_score += synonym_matches * search_term.weight * 0.8  # 同义词权重略低

            # 标题匹配加分
            title_text = patent.get("title", "").lower()
            if search_term.term.lower() in title_text:
                term_score += search_term.weight * 3.0

            # 摘要匹配加分
            abstract_text = patent.get("abstract", "").lower()
            if search_term.term.lower() in abstract_text:
                term_score += search_term.weight * 2.0

            score += term_score

        # 归一化评分
        normalized_score = min(score / (total_weight * 5), 1.0)

        # IPC分类匹配加分
        if enhanced_query.ipc_classifications:
            patent_ipc = patent.get("ipc_classifications", [])
            for ipc in enhanced_query.ipc_classifications:
                if ipc in patent_ipc:
                    normalized_score += 0.1

        return min(normalized_score, 1.0)

    def _deduplicate_and_rank(
        self, patents: list[dict[str, Any]], enhanced_query: SearchQuery
    ) -> list[dict[str, Any]]:
        """去重和排序"""
        # 按专利号去重
        seen_patents = set()
        unique_patents = []

        for patent in patents:
            patent_id = patent.get("patent_id", "")
            if patent_id and patent_id not in seen_patents:
                seen_patents.add(patent_id)
                unique_patents.append(patent)

        # 按相关性评分排序
        unique_patents.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        return unique_patents

    async def _download_pdfs_for_top_results(
        self, patents: list[dict[str, Any]], top_n: int = 10
    ) -> list[dict[str, Any]]:
        """为顶部结果下载PDF"""
        logger.info(f"📥 为前{top_n}个专利下载PDF...")

        for _i, patent in enumerate(patents[:top_n]):
            try:
                if patent.get("success") and patent.get("pdf_available"):
                    patent_id = patent.get("patent_id")
                    logger.info(f"下载PDF: {patent_id}")

                    # 使用基础检索器下载PDF
                    if patent.get("pdf_url"):
                        pdf_path = await self.base_retriever._download_pdf_file(
                            patent_id, patent["pdf_url"]
                        )
                        if pdf_path:
                            patent["pdf_downloaded"] = True
                            patent["pdf_path"] = pdf_path

            except Exception as e:
                logger.error(f"PDF下载失败 {patent.get('patent_id')}: {e}")

        return patents

    def _generate_search_report(
        self,
        original_query: str,
        enhanced_query: SearchQuery,
        results: list[dict[str, Any]],        execution_time: float,
    ) -> dict[str, Any]:
        """生成检索报告"""
        successful_results = [r for r in results if r.get("success")]

        if successful_results:
            scores = [r.get("relevance_score", 0) for r in successful_results]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)

            with_fulltext = sum(1 for r in successful_results if r.get("full_text"))
            with_pdf = sum(1 for r in successful_results if r.get("pdf_available"))
            pdf_downloaded = sum(1 for r in successful_results if r.get("pdf_downloaded"))
        else:
            avg_score = max_score = 0
            with_fulltext = with_pdf = pdf_downloaded = 0

        return {
            "original_query": original_query,
            "expanded_terms_count": len(enhanced_query.expanded_terms),
            "ipc_suggestions": enhanced_query.ipc_classifications,
            "boolean_expression": enhanced_query.boolean_expression,
            "total_results": len(results),
            "successful_results": len(successful_results),
            "success_rate": len(successful_results) / len(results) if results else 0,
            "avg_relevance_score": avg_score,
            "max_relevance_score": max_score,
            "with_fulltext": with_fulltext,
            "with_pdf": with_pdf,
            "pdf_downloaded": pdf_downloaded,
            "execution_time": execution_time,
            "quality_distribution": self._analyze_quality_distribution(successful_results),
        }

    def _analyze_quality_distribution(self, patents: list[dict[str, Any]]) -> dict[str, int]:
        """分析结果质量分布"""
        distribution = {
            "high_quality": 0,  # 评分 > 0.8
            "medium_quality": 0,  # 评分 0.6-0.8
            "low_quality": 0,  # 评分 0.4-0.6
            "very_low_quality": 0,  # 评分 < 0.4
        }

        for patent in patents:
            score = patent.get("relevance_score", 0)
            if score > 0.8:
                distribution["high_quality"] += 1
            elif score > 0.6:
                distribution["medium_quality"] += 1
            elif score > 0.4:
                distribution["low_quality"] += 1
            else:
                distribution["very_low_quality"] += 1

        return distribution


async def main():
    """测试高级专利检索系统"""
    logger.info(str("=" * 80))
    logger.info("🚀 高级专利检索系统测试")
    logger.info(str("=" * 80))

    try:
        # 创建高级检索系统
        search_system = AdvancedPatentSearchSystem()
        await search_system.initialize()

        # 测试查询
        test_queries = [
            "machine learning algorithm for image recognition",
            "5G wireless communication network optimization",
            "blockchain technology for supply chain management",
        ]

        for query in test_queries:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 测试查询: {query}")
            logger.info(f"{'='*60}")

            # 执行高级检索
            result = await search_system.enhanced_patent_search(
                query=query,
                max_results=20,
                search_strategy=SearchStrategy.HYBRID_APPROACH,
                accuracy_level="high",
            )

            # 显示结果摘要
            report = result["search_report"]
            logger.info("\n📊 检索结果摘要:")
            logger.info(f"  ✅ 成功结果: {report['successful_results']}/{report['total_results']}")
            logger.info(f"  📈 平均相关性: {report['avg_relevance_score']:.3f}")
            logger.info(f"  🎯 最高相关性: {report['max_relevance_score']:.3f}")
            logger.info(f"  📖 包含全文: {report['with_fulltext']}")
            logger.info(f"  📄 PDF可用: {report['with_pdf']}")
            logger.info(f"  💾 PDF已下载: {report['pdf_downloaded']}")
            logger.info(f"  ⏱️  执行时间: {report['execution_time']:.2f}秒")

            # 质量分布
            quality_dist = report["quality_distribution"]
            logger.info("\n📊 质量分布:")
            logger.info(f"  🟢 高质量(>0.8): {quality_dist['high_quality']}")
            logger.info(f"  🟡 中质量(0.6-0.8): {quality_dist['medium_quality']}")
            logger.info(f"  🟠 低质量(0.4-0.6): {quality_dist['low_quality']}")
            logger.info(f"  🔴 极低质量(<0.4): {quality_dist['very_low_quality']}")

            # 显示扩展的检索词
            logger.info("\n🔍 查询扩展:")
            logger.info(f"  📝 布尔表达式: {report['boolean_expression'][:100]}...")
            logger.info(f"  🏷️  IPC建议: {report['ipc_suggestions']}")

        await search_system.close()

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


# 入口点: @async_main装饰器已添加到main函数
