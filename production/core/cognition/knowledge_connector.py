
# pyright: ignore
# !/usr/bin/env python3
"""
知识库连接器
Knowledge Base Connector

集成向量数据库和知识图谱,提供智能知识检索服务

作者: 小娜·天秤女神
创建时间: 2025-12-16
版本: v1.0 Knowledge Connector
"""

from __future__ import annotations
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class KnowledgeQuery:
    """知识查询请求"""

    query_text: str
    query_type: str = "similarity"  # similarity, relationship, hybrid
    technology_field: str | None = None
    patent_type: str | None = None
    analysis_type: str | None = None
    limit: int = 10
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeResult:
    """知识查询结果"""

    query_id: str
    results: list[dict[str, Any]]
    query_time: float
    total_found: int
    source_types: list[str]
    relevance_scores: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class MockKnowledgeBase:
    """模拟知识库(实际项目中替换为真实的向量数据库和图数据库)"""

    def __init__(self):
        self.patents_database = self._initialize_patents_db()
        self.legal_precedents = self._initialize_legal_db()
        self.technical_insights = self._initialize_tech_db()

    def _initialize_patents_db(self) -> list[dict[str, Any]]:
        """初始化专利数据库"""
        return [
            {
                "patent_number": "CN202310001234.5",
                "title": "基于深度学习的智能图像识别系统",
                "abstract": "本发明涉及一种基于深度学习的智能图像识别系统,采用卷积神经网络进行特征提取,支持实时图像处理。",
                "technology_field": "人工智能",
                "ipc_classification": "G06V",
                "application_date": "2023-01-01",
                "inventors": ["张三", "李四"],
                "keywords": ["深度学习", "图像识别", "CNN", "实时处理"],
                "similarity_score": 0.85,
            },
            {
                "patent_number": "CN202310002345.6",
                "title": "联邦学习在医疗诊断中的应用方法",
                "abstract": "本发明提供一种基于联邦学习的医疗诊断方法,保护患者隐私的同时实现模型协同训练。",
                "technology_field": "医疗AI",
                "ipc_classification": "G16H",
                "application_date": "2023-01-15",
                "inventors": ["王五", "赵六"],
                "keywords": ["联邦学习", "医疗诊断", "隐私保护", "协同训练"],
                "similarity_score": 0.78,
            },
            {
                "patent_number": "CN202310003456.7",
                "title": "多模态数据融合的人工智能系统",
                "abstract": "一种多模态数据融合的AI系统,支持文本、图像、音频等多种数据类型的统一处理。",
                "technology_field": "人工智能",
                "ipc_classification": "G06N",
                "application_date": "2023-02-01",
                "inventors": ["陈七", "周八"],
                "keywords": ["多模态", "数据融合", "人工智能", "统一处理"],
                "similarity_score": 0.72,
            },
        ]

    def _initialize_legal_db(self) -> list[dict[str, Any]]:
        """初始化法律先例数据库"""
        return [
            {
                "case_id": "CN_GZ_2023_001",
                "case_name": "XX公司诉YY公司专利侵权纠纷案",
                "court": "北京市高级人民法院",
                "judgment_date": "2023-03-15",
                "dispute_type": "专利侵权",
                "key_points": ["权利要求解释方法", "等同原则适用", "现有技术抗辩"],
                "outcome": "原告胜诉,被告停止侵权并赔偿损失",
                "relevance_score": 0.82,
            },
            {
                "case_id": "CN_GZ_2023_002",
                "case_name": "发明专利无效宣告请求案",
                "court": "国家知识产权局专利局",
                "judgment_date": "2023-04-20",
                "dispute_type": "专利无效",
                "key_points": ["新颖性判断", "创造性标准", "充分公开要求"],
                "outcome": "维持专利权有效",
                "relevance_score": 0.75,
            },
        ]

    def _initialize_tech_db(self) -> list[dict[str, Any]]:
        """初始化技术洞察数据库"""
        return [
            {
                "insight_id": "TECH_001",
                "title": "深度学习在图像识别中的最新进展",
                "technology_field": "人工智能",
                "content": "介绍了Transformer架构在图像识别中的应用,以及自监督学习的技术趋势。",
                "key_trends": ["Vision Transformer (ViT)", "自监督学习", "少样本学习"],
                "publication_date": "2023-05-01",
                "relevance_score": 0.88,
            },
            {
                "insight_id": "TECH_002",
                "title": "联邦学习技术发展现状",
                "technology_field": "分布式机器学习",
                "content": "分析了联邦学习在医疗、金融等领域的应用现状和技术挑战。",
                "key_trends": ["隐私保护技术", "通信效率优化", "异构设备支持"],
                "publication_date": "2023-05-15",
                "relevance_score": 0.80,
            },
        ]


class KnowledgeConnector:
    """知识库连接器"""

    def __init__(self):
        self.knowledge_base = MockKnowledgeBase()
        self.query_history = []
        self.similarity_cache = {}

    async def initialize(self):
        """初始化连接器"""
        logger.info("知识库连接器初始化完成")
        return True

    async def search_similar_patents(self, query: KnowledgeQuery) -> KnowledgeResult:
        """搜索相似专利"""
        start_time = datetime.now()
        query_id = f"patent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 提取关键词
        keywords = self._extract_keywords(query.query_text)

        # 计算相似度
        similar_patents = []
        for patent in self.knowledge_base.patents_database:
            similarity = self._calculate_similarity(
                keywords, patent["keywords"] + patent["abstract"].split()
            )

            if similarity > 0.3:  # 相似度阈值
                patent_copy = patent.copy()
                patent_copy["similarity_score"] = similarity
                similar_patents.append(patent_copy)

        # 排序并限制结果数量
        similar_patents.sort(key=lambda x: x["similarity_score"], reverse=True)  # type: ignore
        results = similar_patents[: query.limit]

        query_time = (datetime.now() - start_time).total_seconds()

        result = KnowledgeResult(
            query_id=query_id,
            results=results,
            query_time=query_time,
            total_found=len(similar_patents),
            source_types=["patent_database"],
            relevance_scores=[p["similarity_score"] for p in results],
            metadata={"keywords_extracted": keywords, "similarity_threshold": 0.3},
        )

        self.query_history.append(
            {
                "query_id": query_id,
                "query_type": "similar_patents",
                "query_time": query_time,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"相似专利搜索完成: 找到{len(results)}个结果,耗时{query_time:.2f}s")
        return result

    async def search_legal_precedents(self, query: KnowledgeQuery) -> KnowledgeResult:
        """搜索法律先例"""
        start_time = datetime.now()
        query_id = f"legal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 提取法律相关关键词
        legal_keywords = self._extract_legal_keywords(query.query_text)

        # 匹配法律先例
        matching_cases = []
        for case in self.knowledge_base.legal_precedents:
            relevance = self._calculate_legal_relevance(
                legal_keywords, case["key_points"] + [case["case_name"]]
            )

            if relevance > 0.3:
                case_copy = case.copy()
                case_copy["relevance_score"] = relevance
                matching_cases.append(case_copy)

        # 排序并限制结果
        matching_cases.sort(key=lambda x: x["relevance_score"], reverse=True)  # type: ignore
        results = matching_cases[: query.limit]

        query_time = (datetime.now() - start_time).total_seconds()

        result = KnowledgeResult(
            query_id=query_id,
            results=results,
            query_time=query_time,
            total_found=len(matching_cases),
            source_types=["legal_database"],
            relevance_scores=[c["relevance_score"] for c in results],
            metadata={"legal_keywords": legal_keywords, "relevance_threshold": 0.3},
        )

        self.query_history.append(
            {
                "query_id": query_id,
                "query_type": "legal_precedents",
                "query_time": query_time,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"法律先例搜索完成: 找到{len(results)}个结果,耗时{query_time:.2f}s")
        return result

    async def search_technical_insights(self, query: KnowledgeQuery) -> KnowledgeResult:
        """搜索技术洞察"""
        start_time = datetime.now()
        query_id = f"tech_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 提取技术关键词
        tech_keywords = self._extract_technical_keywords(query.query_text)

        # 匹配技术洞察
        matching_insights = []
        for insight in self.knowledge_base.technical_insights:
            relevance = self._calculate_tech_relevance(
                tech_keywords, insight["content"].split() + insight["key_trends"]
            )

            if relevance > 0.3:
                insight_copy = insight.copy()
                insight_copy["relevance_score"] = relevance
                matching_insights.append(insight_copy)

        # 排序并限制结果
        matching_insights.sort(key=lambda x: x["relevance_score"], reverse=True)  # type: ignore
        results = matching_insights[: query.limit]

        query_time = (datetime.now() - start_time).total_seconds()

        result = KnowledgeResult(
            query_id=query_id,
            results=results,
            query_time=query_time,
            total_found=len(matching_insights),
            source_types=["technical_database"],
            relevance_scores=[i["relevance_score"] for i in results],
            metadata={"tech_keywords": tech_keywords, "relevance_threshold": 0.3},
        )

        self.query_history.append(
            {
                "query_id": query_id,
                "query_type": "technical_insights",
                "query_time": query_time,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat(),
            }
        )

        logger.info(f"技术洞察搜索完成: 找到{len(results)}个结果,耗时{query_time:.2f}s")
        return result

    async def hybrid_search(self, query: KnowledgeQuery) -> KnowledgeResult:
        """混合搜索"""
        start_time = datetime.now()
        query_id = f"hybrid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 并行执行多种搜索
        patent_task = self.search_similar_patents(query)
        legal_task = self.search_legal_precedents(query)
        tech_task = self.search_technical_insights(query)

        # 等待所有搜索完成
        patent_result, legal_result, tech_result = await asyncio.gather(
            patent_task, legal_task, tech_task
        )

        # 合并结果
        all_results = []
        all_results.extend(patent_result.results)
        all_results.extend(legal_result.results)
        all_results.extend(tech_result.results)

        # 统一排序(根据相关性分数)
        all_results.sort(key=lambda x: self._get_relevance_score(x), reverse=True)  # type: ignore

        # 限制结果数量
        results = all_results[: query.limit]

        query_time = (datetime.now() - start_time).total_seconds()

        result = KnowledgeResult(
            query_id=query_id,
            results=results,
            query_time=query_time,
            total_found=len(all_results),
            source_types=["patent_database", "legal_database", "technical_database"],
            relevance_scores=[self._get_relevance_score(r) for r in results],
            metadata={
                "search_strategy": "hybrid",
                "patent_results": len(patent_result.results),
                "legal_results": len(legal_result.results),
                "tech_results": len(tech_result.results),
            },
        )

        logger.info(f"混合搜索完成: 总共找到{len(results)}个结果,耗时{query_time:.2f}s")
        return result

    async def get_domain_knowledge(self, technology_field: str) -> dict[str, Any]:
        """获取领域知识"""
        # 模拟领域知识获取
        domain_knowledge = {
            "technology_field": technology_field,
            "key_concepts": self._get_key_concepts(technology_field),
            "common_issues": self._get_common_issues(technology_field),
            "success_patterns": self._get_success_patterns(technology_field),
            "experts": self._get_domain_experts(technology_field),
            "recent_developments": self._get_recent_developments(technology_field),
        }

        logger.info(f"领域知识获取完成: {technology_field}")
        return domain_knowledge

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 简化的关键词提取(实际项目中应使用NLP工具)
        # 移除标点符号并转换为小写
        cleaned_text = re.sub(r"[^\w\s]", " ", text.lower())
        words = cleaned_text.split()

        # 过滤停用词
        stop_words = {
            "的",
            "是",
            "在",
            "有",
            "和",
            "与",
            "或",
            "但",
            "为",
            "了",
            "等",
            "及",
            "基于",
            "一种",
            "方法",
            "系统",
        }
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]

        return keywords[:20]  # 返回前20个关键词

    def _extract_legal_keywords(self, text: str) -> list[str]:
        """提取法律相关关键词"""
        legal_terms = [
            "专利",
            "侵权",
            "无效",
            "诉讼",
            "审查",
            "权利要求",
            "新颖性",
            "创造性",
            "实用性",
            "先例",
            "判决",
        ]
        keywords = self._extract_keywords(text)
        return [kw for kw in keywords if kw in legal_terms]

    def _extract_technical_keywords(self, text: str) -> list[str]:
        """提取技术关键词"""
        # 移除法律相关词汇,保留技术词汇
        keywords = self._extract_keywords(text)
        legal_terms = {"专利", "侵权", "无效", "诉讼", "审查", "权利要求"}
        return [kw for kw in keywords if kw not in legal_terms]

    def _calculate_similarity(self, keywords1: list[str], keywords2: list[str]) -> float:
        """计算关键词相似度"""
        if not keywords1 or not keywords2:
            return 0.0

        # 使用Jaccard相似度
        set1 = set(keywords1)
        set2 = set(keywords2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _calculate_legal_relevance(self, legal_keywords: list[str], case_text: list[str]) -> float:
        """计算法律相关性"""
        if not legal_keywords:
            return 0.0

        legal_text_set = {word.lower() for word in case_text}
        keyword_set = {kw.lower() for kw in legal_keywords}

        matches = len(legal_text_set.intersection(keyword_set))
        return matches / len(keyword_set)

    def _calculate_tech_relevance(self, tech_keywords: list[str], tech_text: list[str]) -> float:
        """计算技术相关性"""
        return self._calculate_similarity(tech_keywords, tech_text)

    def _get_relevance_score(self, item: dict[str, Any]) -> float:
        """获取项目的相关性分数"""
        if "similarity_score" in item:
            return item.get("similarity_score")
        elif "relevance_score" in item:
            return item.get("relevance_score")
        else:
            return 0.0

    def _get_key_concepts(self, field: str) -> list[str]:
        """获取领域关键概念"""
        concepts_map = {
            "人工智能": ["机器学习", "深度学习", "神经网络", "自然语言处理", "计算机视觉"],
            "医疗AI": ["医疗诊断", "医学影像", "电子病历", "精准医疗", "健康监测"],
            "通信技术": ["5G", "物联网", "网络安全", "无线通信", "协议栈"],
            "化学工程": ["有机合成", "催化反应", "高分子材料", "精细化工", "工艺优化"],
        }
        return concepts_map.get(field, ["技术创新", "应用研究", "产业发展"])

    def _get_common_issues(self, field: str) -> list[str]:
        """获取领域常见问题"""
        issues_map = {
            "人工智能": ["数据质量", "模型可解释性", "算法偏见", "计算资源需求"],
            "医疗AI": ["数据隐私", "监管合规", "临床验证", "误诊风险"],
            "通信技术": ["频谱资源", "标准兼容性", "网络安全", "服务质量"],
            "化学工程": ["环境污染", "能源消耗", "安全生产", "成本控制"],
        }
        return issues_map.get(field, ["技术成熟度", "市场接受度", "成本效益"])

    def _get_success_patterns(self, field: str) -> list[str]:
        """获取成功模式"""
        patterns_map = {
            "人工智能": ["大模型架构", "预训练技术", "迁移学习", "多模态融合"],
            "医疗AI": ["多中心验证", "专家系统结合", "临床决策支持", "远程医疗"],
            "通信技术": ["标准化协议", "网络切片", "边缘计算", "网络虚拟化"],
            "化学工程": ["绿色化学", "循环经济", "智能制造", "连续流工艺"],
        }
        return patterns_map.get(field, ["技术创新", "产业应用", "标准制定"])

    def _get_domain_experts(self, field: str) -> list[str]:
        """获取领域专家"""
        expert_map = {
            "人工智能": ["天狼", "大角", "北斗"],
            "医疗AI": ["织女", "毕宿"],
            "通信技术": ["天狼", "摇光", "五车"],
            "化学工程": ["织女", "天津"],
            "机械制造": ["北极", "心宿", "井宿"],
            "建筑": ["昴宿"],
            "纺织": ["奎宿"],
            "光学": ["南河"],
        }
        return expert_map.get(field, ["天狼", "织女", "北斗"])

    def _get_recent_developments(self, field: str) -> list[str]:
        """获取最新发展"""
        developments_map = {
            "人工智能": ["大语言模型突破", "多模态AI发展", "AI安全与伦理"],
            "医疗AI": ["AI辅助诊断普及", "个性化医疗发展", "远程医疗成熟"],
            "通信技术": ["6G研发启动", "卫星互联网建设", "量子通信发展"],
            "化学工程": ["绿色化工技术", "新能源材料", "智能制造应用"],
        }
        return developments_map.get(field, ["技术创新加速", "应用场景拓展", "标准体系完善"])

    def get_query_statistics(self) -> dict[str, Any]:
        """获取查询统计信息"""
        if not self.query_history:
            return {"total_queries": 0}

        query_types = {}
        avg_times = {}

        for record in self.query_history:
            query_type = record["query_type"]
            query_time = record["query_time"]

            query_types[query_type] = query_types.get(query_type, 0) + 1
            if query_type not in avg_times:
                avg_times[query_type] = []
            avg_times[query_type].append(query_time)

        # 计算平均查询时间
        for query_type in avg_times:
            times = avg_times[query_type]
            avg_times[query_type] = sum(times) / len(times)

        return {
            "total_queries": len(self.query_history),
            "query_types": query_types,
            "average_query_times": avg_times,
            "most_common_type": (
                max(query_types.items(), key=lambda x: x[1]) if query_types else None  # type: ignore
            ),
            "latest_query": self.query_history[-1]["timestamp"] if self.query_history else None,
        }

    async def cleanup(self):
        """清理资源"""
        logger.info("知识库连接器资源清理完成")


# 便捷函数
async def search_patent_knowledge(
    query_text: str | None = None, technology_field: str | None = None, limit: int = 5
) -> KnowledgeResult:
    """便捷的专利知识搜索函数"""
    connector = KnowledgeConnector()
    await connector.initialize()

    query = KnowledgeQuery(query_text=query_text, technology_field=technology_field, limit=limit)

    return await connector.hybrid_search(query)
