#!/usr/bin/env python3

"""
Athena工作平台 - 统一向量检索接口
Unified Vector Search Interface for Athena Platform

为Athena和小诺的记忆模块提供统一的向量检索服务
支持智能路由和多库联合检索
"""

# Numpy兼容性导入
import logging
import os
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from config.numpy_compatibility import random
from core.logging_config import setup_logging

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.vector_db.vector_db_manager import (
    VectorDBManager,
    VectorDBType,
    VectorQuery,
    VectorResult,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class MemoryType(Enum):
    """记忆类型枚举"""

    GENERAL = "general"  # 通用记忆
    CONVERSATION = "conversation"  # 对话记忆
    PATENT_KNOWLEDGE = "patent_knowledge"  # 专利知识
    LEGAL_KNOWLEDGE = "legal_knowledge"  # 法律知识
    TECHNICAL_KNOWLEDGE = "technical_knowledge"  # 技术知识
    LEARNING_HISTORY = "learning_history"  # 学习历史


class UnifiedVectorSearcher:
    """统一向量检索器"""

    def __init__(self):
        self.vector_db_manager = VectorDBManager()
        self._setup_memory_routing()
        self._setup_collection_dimensions()

    def _setup_collection_dimensions(self) -> Any:
        """设置各集合的向量维度"""
        # 从集合配置中获取维度信息
        self.collection_dimensions = {}

        for collection_name in self.vector_db_manager.existing_collections:
            info = self.vector_db_manager.get_collection_info(collection_name)
            if info:
                dimension = (
                    info.get("config", {}).get("params", {}).get("vectors", {}).get("size", 1024)
                )
                self.collection_dimensions[collection_name] = dimension
            else:
                # 默认维度
                self.collection_dimensions[collection_name] = 1024

        logger.info(f"📊 集合维度配置: {self.collection_dimensions}")

    def _setup_memory_routing(self) -> Any:
        """设置记忆路由规则"""
        # 记忆类型到向量库类型的映射
        self.memory_to_db_mapping = {
            MemoryType.GENERAL: [VectorDBType.GENERAL],
            MemoryType.CONVERSATION: [VectorDBType.GENERAL],
            MemoryType.PATENT_KNOWLEDGE: [VectorDBType.PATENT_RULES, VectorDBType.TECHNICAL_TERMS],
            MemoryType.LEGAL_KNOWLEDGE: [VectorDBType.LEGAL],
            MemoryType.TECHNICAL_KNOWLEDGE: [VectorDBType.TECHNICAL_TERMS],
            MemoryType.LEARNING_HISTORY: [VectorDBType.GENERAL],
        }

        # 智能路由关键词
        self.routing_keywords = {
            VectorDBType.PATENT_RULES: [
                "专利",
                "patent",
                "权利要求",
                "申请",
                "审查",
                "无效",
                "复审",
                "侵权",
                "保护",
            ],
            VectorDBType.LEGAL: [
                "法律",
                "法规",
                "法条",
                "判决",
                "诉讼",
                "合同",
                "责任",
                "权利",
                "义务",
            ],
            VectorDBType.TECHNICAL_TERMS: [
                "技术",
                "术语",
                "定义",
                "算法",
                "模型",
                "系统",
                "方法",
                "装置",
            ],
        }

    def _determine_db_types_from_query(self, query_text: str) -> list[VectorDBType]:
        """根据查询文本智能确定需要搜索的向量库类型"""
        if not query_text:
            return [VectorDBType.GENERAL]  # 默认搜索通用库

        query_lower = query_text.lower()
        detected_types = set()

        # 检查关键词
        for db_type, keywords in self.routing_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    detected_types.add(db_type)
                    break

        # 如果没有检测到特定类型,使用通用库
        if not detected_types:
            detected_types.add(VectorDBType.GENERAL)

        # 添加通用库作为后备
        if VectorDBType.GENERAL not in detected_types:
            detected_types.add(VectorDBType.GENERAL)

        return list(detected_types)

    def _get_collection_names_from_db_types(self, db_types: list[VectorDBType]) -> list[str]:
        """根据向量库类型获取集合名称"""
        collection_names = []
        for db_type in db_types:
            collection_name = self.vector_db_manager.collections.get(db_type)
            if collection_name and collection_name in self.vector_db_manager.existing_collections:
                collection_names.append(collection_name)
        return collection_names

    def search_by_memory_type(
        self, query: VectorQuery, memory_type: MemoryType
    ) -> dict[str, list[VectorResult]]:
        """根据记忆类型搜索"""
        db_types = self.memory_to_db_mapping.get(memory_type, [VectorDBType.GENERAL])
        collection_names = self._get_collection_names_from_db_types(db_types)

        logger.info(f"🔍 按记忆类型搜索: {memory_type.value}, 集合: {collection_names}")
        return self._batch_search_with_dimension_check(collection_names, query)

    def _batch_search_with_dimension_check(
        self, collection_names: list[str], query: VectorQuery
    ) -> dict[str, list[VectorResult]]:
        """带维度检查的批量搜索"""
        results = {}

        for collection_name in collection_names:
            # 检查向量维度是否匹配
            required_dimension = self.collection_dimensions.get(collection_name, 1024)
            actual_dimension = len(query.vector)

            if required_dimension != actual_dimension:
                logger.warning(
                    f"⚠️ 维度不匹配: {collection_name} 需要 {required_dimension} 维, 但提供的是 {actual_dimension} 维"
                )
                # 跳过不匹配维度的集合
                continue

            results[collection_name] = self.vector_db_manager.search_in_collection(
                collection_name, query
            )

        return results

    def intelligent_search(
        self, query: VectorQuery, query_text: Optional[str] = None
    ) -> dict[str, list[VectorResult]]:
        """智能搜索 - 根据查询内容自动路由到合适的向量库"""
        if query_text:
            db_types = self._determine_db_types_from_query(query_text)
            collection_names = self._get_collection_names_from_db_types(db_types)
        else:
            # 默认搜索所有可用集合
            collection_names = list(self.vector_db_manager.existing_collections)

        logger.info(f"🤖 智能搜索, 使用集合: {collection_names}")
        return self._smart_batch_search(collection_names, query)

    def _smart_batch_search(
        self, collection_names: list[str], query: VectorQuery
    ) -> dict[str, list[VectorResult]]:
        """智能批量搜索 - 为每个集合生成匹配维度的向量"""
        results = {}

        for collection_name in collection_names:
            # 检查向量维度是否匹配
            required_dimension = self.collection_dimensions.get(collection_name, 1024)
            actual_dimension = len(query.vector)

            if required_dimension != actual_dimension:
                logger.info(f"🔄 为 {collection_name} 生成 {required_dimension} 维向量")
                # 为该集合创建匹配维度的查询
                adjusted_query = VectorQuery(
                    vector=random(required_dimension).tolist(),
                    text=query.text,
                    filters=query.filters,
                    limit=query.limit,
                    with_payload=query.with_payload,
                    with_vectors=query.with_vectors,
                )
                results[collection_name] = self.vector_db_manager.search_in_collection(
                    collection_name, adjusted_query
                )
            else:
                results[collection_name] = self.vector_db_manager.search_in_collection(
                    collection_name, query
                )

        return results

    def multi_hop_search(
        self, query: VectorQuery, initial_memory_type: MemoryType, max_hops: int = 2
    ) -> dict[str, list[VectorResult]]:
        """多跳搜索 - 从一个记忆类型开始,扩展到相关类型"""
        results = {}

        # 第一跳:按初始记忆类型搜索
        initial_results = self.search_by_memory_type(query, initial_memory_type)
        results.update(initial_results)

        # 如果需要多跳,根据初始结果关键词扩展搜索
        if max_hops > 1:
            # 从初始结果中提取关键词
            keywords = self._extract_keywords_from_results(list(initial_results.values()))

            if keywords:
                # 使用关键词进行扩展搜索
                for keyword in keywords[:3]:  # 只取前3个关键词
                    expanded_query = VectorQuery(
                        vector=query.vector,
                        text=keyword,
                        limit=query.limit // 2,  # 减少扩展搜索的数量
                        with_payload=query.with_payload,
                        with_vectors=query.with_vectors,
                    )

                    # 智能搜索扩展
                    expanded_results = self.intelligent_search(expanded_query, keyword)
                    for collection, result_list in expanded_results.items():
                        if collection in results:
                            # 合并结果,避免重复
                            existing_ids = {r.id for r in results[collection]}
                            new_results = [r for r in result_list if r.id not in existing_ids]
                            results[collection].extend(new_results)
                        else:
                            results[collection] = result_list

        return results

    def _extract_keywords_from_results(self, all_results: list[list[VectorResult]) -> list[str]]:
        """从搜索结果中提取关键词"""
        keywords = set()

        for result_list in all_results:
            for result in result_list[:5]:  # 只处理前5个结果
                # 从payload中提取可能的关键词
                payload = result.payload
                if "text" in payload:
                    text = str(payload["text"])
                    # 简单的关键词提取(实际项目中可以使用更复杂的NLP技术)
                    words = text.split()[:10]  # 取前10个词
                    for word in words:
                        if len(word) > 2 and any(c.isalpha() for c in word):
                            keywords.add(word)

                if "term" in payload:
                    keywords.add(str(payload["term"]))

                if "category" in payload:
                    keywords.add(str(payload["category"]))

        return list(keywords)[:10]  # 返回前10个关键词

    def search_with_context(
        self,
        query: VectorQuery,
        context_user: str = "athena",  # 'athena' or 'xiaonuo'
        memory_type: Optional[MemoryType] = None,
    ) -> dict[str, list[VectorResult]]:
        """带有上下文的搜索,支持Athena和小诺的不同需求"""
        if memory_type:
            # 按指定记忆类型搜索
            return self.search_by_memory_type(query, memory_type)
        else:
            # 智能搜索,根据不同用户可能有不同偏好
            if context_user == "xiaonuo":
                # 小诺可能更关注对话和情感相关的内容
                query_filters = query.filters or {}
                query_filters["user_type"] = "xiaonuo"
                query.filters = query_filters
            elif context_user == "athena":
                # Athena可能更关注专业内容
                pass

            return self.intelligent_search(query, query.text)


class MemoryService:
    """记忆服务 - 为Athena和小诺提供统一的记忆访问接口"""

    def __init__(self):
        self.searcher = UnifiedVectorSearcher()
        self.memory_type = MemoryType

    def query_memory(
        self,
        query_text: str,
        vector: Optional[list[float]] = None,
        memory_type: Optional[MemoryType] = None,
        user_context: str = "athena",
        limit: int = 10,
    ) -> dict[str, Any]:
        """查询记忆"""
        # 确定目标集合以确定需要的向量维度
        if memory_type:
            db_types = self.searcher.memory_to_db_mapping.get(memory_type, [VectorDBType.GENERAL])
            target_collections = self.searcher._get_collection_names_from_db_types(db_types)
        else:
            # 智能搜索 - 可能需要多个维度,这里我们为每种维度创建不同的查询
            target_collections = list(self.searcher.vector_db_manager.existing_collections)

        # 如果没有指定特定的集合,或者目标集合为空,则使用默认维度
        if not target_collections:
            required_dimension = 1024  # 默认为1024维
        else:
            # 为第一个集合使用合适的维度
            first_collection = target_collections[0]
            required_dimension = self.searcher.collection_dimensions.get(first_collection, 1024)

        # 如果没有提供向量,则生成匹配维度的随机向量
        if vector is None:
            # 实际应用中应该调用embedding模型生成对应维度的向量
            vector = random(required_dimension).tolist()

        query = VectorQuery(vector=vector, text=query_text, limit=limit, with_payload=True)

        # 根据不同参数选择不同的搜索策略
        if memory_type:
            results = self.searcher.search_by_memory_type(query, memory_type)
        else:
            # 根据用户上下文进行智能搜索
            results = self.searcher.search_with_context(
                query, context_user=user_context, memory_type=memory_type
            )

        # 格式化结果
        formatted_results = {
            "query": query_text,
            "timestamp": datetime.now().isoformat(),
            "user_context": user_context,
            "memory_type": memory_type.value if memory_type else "auto",
            "results_by_collection": {},
            "total_results": 0,
            "collections_searched": list(results.keys()),
        }

        for collection_name, result_list in results.items():
            formatted_result_list = []
            for result in result_list:
                formatted_result = {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                }
                formatted_result_list.append(formatted_result)

            formatted_results["results_by_collection"][collection_name] = formatted_result_list
            formatted_results["total_results"] += len(result_list)

        return formatted_results


def main() -> None:
    """主函数 - 测试统一向量检索接口"""
    logger.info("🏗️  初始化统一向量检索接口...")

    # 创建统一检索器
    memory_service = MemoryService()

    logger.info(str("=" * 80))
    logger.info("🤖 Athena工作平台 - 统一向量检索接口")
    logger.info(str("=" * 80))
    logger.info(f"🎯 支持的记忆类型: {[e.value for e in MemoryType]}")
    logger.info(
        f"📚 已连接向量库: {len(memory_service.searcher.vector_db_manager.existing_collections)} 个"
    )
    logger.info(str("=" * 80))

    # 测试不同类型的查询
    test_queries = [
        ("通用知识查询", "人工智能的定义", MemoryType.GENERAL),
        ("专利知识查询", "专利权利要求书如何撰写", MemoryType.PATENT_KNOWLEDGE),
        ("法律知识查询", "合同法基本原则", MemoryType.LEGAL_KNOWLEDGE),
        ("技术术语查询", "机器学习算法", MemoryType.TECHNICAL_KNOWLEDGE),
    ]

    for query_desc, query_text, mem_type in test_queries:
        logger.info(f"\n🔍 {query_desc}: '{query_text}'")
        logger.info(str("-" * 60))

        try:
            # 生成测试向量
            test_vector = random(1024).tolist()

            results = memory_service.query_memory(
                query_text=query_text, vector=test_vector, memory_type=mem_type, limit=3
            )

            logger.info("📊 搜索结果:")
            logger.info(f"   - 总结果数: {results['total_results']}")
            logger.info(f"   - 搜索集合: {', '.join(results['collections_searched'])}")

            for collection, items in results["results_by_collection"].items():
                if items:  # 只显示有结果的集合
                    logger.info(f"   - {collection}: {len(items)} 个结果")
                    for i, item in enumerate(items[:2]):  # 只显示前2个
                        logger.info(f"     {i+1}. 评分: {item['score']:.3f}")
                        if "text" in item["payload"]:
                            text_preview = (
                                item["payload"]["text"][:50] + "..."
                                if len(item["payload"]["text"]) > 50
                                else item["payload"]["text"]
                            )
                            logger.info(f"         内容: {text_preview}")

        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")

    # 测试智能搜索
    logger.info("\n🤖 智能搜索测试")
    logger.info(str("-" * 60))

    smart_queries = ["专利侵权判定方法", "合同违约责任", "神经网络算法优化"]

    for query_text in smart_queries:
        logger.info(f"\n📝 查询: '{query_text}'")
        try:
            test_vector = random(1024).tolist()
            results = memory_service.query_memory(
                query_text=query_text, vector=test_vector, limit=2
            )

            logger.info(f"   - 自动选择搜索集合: {', '.join(results['collections_searched'])}")
            logger.info(f"   - 找到结果: {results['total_results']} 个")

        except Exception as e:
            logger.error(f"❌ 智能搜索失败: {e}")

    logger.info(str("\n" + "=" * 80))
    logger.info("✅ 统一向量检索接口测试完成")
    logger.info("🎯 现可为Athena和小诺的记忆模块提供服务")
    logger.info(str("=" * 80))

    return memory_service


if __name__ == "__main__":
    service = main()

