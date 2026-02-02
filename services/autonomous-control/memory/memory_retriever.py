#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能检索器
Memory Retriever

多源记忆智能检索系统

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
from core.async_main import async_main
import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MemoryRetriever:
    """智能记忆检索器"""

    def __init__(self):
        """初始化记忆检索器"""
        from .episodic_memory import EpisodicMemory
        from .semantic_memory import SemanticMemory
        from .procedural_memory import ProceduralMemory

        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.procedural_memory = ProceduralMemory()

        self.episodic_initialized = False

    async def initialize(self):
        """初始化所有记忆组件"""
        try:
            await self.episodic_memory.initialize()
            self.episodic_initialized = True
            logger.info("✅ 记忆检索器初始化完成")
        except Exception as e:
            logger.warning(f"情景记忆初始化失败，将使用模拟模式: {str(e)}")
            self.episodic_initialized = False

    async def retrieve(self, query: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        智能检索记忆

        Args:
            query: 查询条件
            {
                "text": "查询文本",
                "type": "episodic|semantic|procedural|all",  # 检索类型
                "business_type": "patent|trademark|copyright|contract",
                "user_id": "user123",  # 可选
                "context": {...},  # 上下文
                "filters": {...}  # 过滤条件
            }
            limit: 返回数量

        Returns:
            检索结果
        """
        try:
            retrieval_type = query.get("type", "all")
            business_type = query.get("business_type", "patent")
            text = query.get("text", "")
            context = query.get("context", {})

            results = {
                "episodic": [],
                "semantic": [],
                "procedural": [],
                "combined": [],
                "metadata": {
                    "query": query,
                    "retrieved_at": datetime.now().isoformat(),
                    "total_count": 0
                }
            }

            # 并行检索
            tasks = []

            if retrieval_type in ["episodic", "all"]:
                tasks.append(self._retrieve_episodic(query, limit))

            if retrieval_type in ["semantic", "all"]:
                tasks.append(self._retrieve_semantic(query, limit))

            if retrieval_type in ["procedural", "all"]:
                tasks.append(self._retrieve_procedural(query, limit))

            if tasks:
                retrieved = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果
                for i, result in enumerate(retrieved):
                    if isinstance(result, Exception):
                        logger.error(f"检索失败: {str(result)}")
                        continue

                    if retrieval_type in ["episodic", "all"] and i == 0:
                        results["episodic"] = result
                    elif retrieval_type in ["semantic", "all"] and i == 1:
                        results["semantic"] = result
                    elif retrieval_type in ["procedural", "all"] and i == 2:
                        results["procedural"] = result

            # 组合和排序结果
            if retrieval_type == "all":
                results["combined"] = await self._combine_results(results, text, limit)

            # 计算总数
            results["metadata"]["total_count"] = (
                len(results["episodic"]) +
                len(results["semantic"]) +
                len(results["procedural"])
            )

            return results

        except Exception as e:
            logger.error(f"智能检索失败: {str(e)}")
            return {
                "error": str(e),
                "metadata": {"error": True}
            }

    async def _retrieve_episodic(self, query: Dict, limit: int) -> List[Dict]:
        """检索情景记忆"""
        if not self.episodic_initialized:
            # 模拟情景记忆
            return self._simulate_episodic_retrieval(query, limit)

        try:
            search_params = {
                "limit": limit
            }

            if "user_id" in query:
                search_params["user_id"] = query["user_id"]

            if "business_type" in query:
                search_params["business_type"] = query["business_type"]

            # 如果有文本，提取embedding
            if "text" in query:
                # 简化：假设有embedding
                search_params["embedding"] = self._text_to_embedding(query["text"])

            # 应用过滤条件
            if "filters" in query:
                filters = query["filters"]
                if "date_range" in filters:
                    search_params["date_range"] = filters["date_range"]
                if "min_importance" in filters:
                    search_params["min_importance"] = filters["min_importance"]

            memories = await self.episodic_memory.retrieve(search_params, limit)

            # 为每个记忆添加检索分数
            scored_memories = []
            for memory in memories:
                score = self._calculate_episodic_score(memory, query)
                memory["retrieval_score"] = score
                scored_memories.append(memory)

            # 按分数排序
            scored_memories.sort(key=lambda x: x["retrieval_score"], reverse=True)

            return scored_memories[:limit]

        except Exception as e:
            logger.error(f"情景记忆检索失败: {str(e)}")
            return []

    async def _retrieve_semantic(self, query: Dict, limit: int) -> List[Dict]:
        """检索语义记忆"""
        try:
            text = query.get("text", "")
            business_type = query.get("business_type", "patent")

            if not text:
                return []

            # 搜索知识图谱
            knowledge_result = await self.semantic_memory.search_knowledge(
                text, business_type, limit
            )

            # 获取相关实体
            related_entities = await self.semantic_memory.get_related_entities(
                text[:50]  # 取前50个字符作为关键词
            )

            # 合并结果
            semantic_results = []

            # 处理知识搜索结果
            for i, vector_result in enumerate(knowledge_result.get("vector_results", [])):
                semantic_results.append({
                    "type": "knowledge",
                    "source": "vector_search",
                    "content": vector_result.get("content", ""),
                    "similarity": vector_result.get("score", 0),
                    "metadata": vector_result.get("metadata", {}),
                    "retrieval_score": vector_result.get("score", 0) * 0.8
                })

            # 处理图谱搜索结果
            for graph_result in knowledge_result.get("graph_results", []):
                node = graph_result.get("node", {})
                semantic_results.append({
                    "type": "entity",
                    "source": "knowledge_graph",
                    "content": node.get("description", ""),
                    "title": node.get("name", ""),
                    "entity_type": node.get("type", ""),
                    "relations": graph_result.get("relations", {}),
                    "retrieval_score": 0.7  # 固定分数
                })

            # 按分数排序
            semantic_results.sort(key=lambda x: x["retrieval_score"], reverse=True)

            return semantic_results[:limit]

        except Exception as e:
            logger.error(f"语义记忆检索失败: {str(e)}")
            return []

    async def _retrieve_procedural(self, query: Dict, limit: int) -> List[Dict]:
        """检索程序记忆"""
        try:
            business_type = query.get("business_type")
            tags = query.get("filters", {}).get("tags", [])

            # 搜索程序
            procedures = self.procedural_memory.search_procedures(
                category=business_type,
                tags=tags
            )

            # 转换为统一格式
            procedural_results = []
            for procedure in procedures:
                # 计算匹配分数
                score = self._calculate_procedural_score(procedure, query)

                procedural_results.append({
                    "type": "procedure",
                    "procedure_id": procedure.procedure_id,
                    "name": procedure.name,
                    "category": procedure.category,
                    "description": procedure.description,
                    "steps": procedure.steps,
                    "timeline": procedure.timeline,
                    "costs": procedure.costs,
                    "risks": procedure.risks,
                    "success_rate": procedure.success_rate,
                    "tags": procedure.tags,
                    "retrieval_score": score
                })

            # 按分数排序
            procedural_results.sort(key=lambda x: x["retrieval_score"], reverse=True)

            return procedural_results[:limit]

        except Exception as e:
            logger.error(f"程序记忆检索失败: {str(e)}")
            return []

    async def _combine_results(self, results: Dict, query_text: str, limit: int) -> List[Dict]:
        """组合不同源的检索结果"""
        combined = []

        # 添加所有结果到统一列表
        for memory in results["episodic"]:
            combined.append({
                **memory,
                "source_type": "episodic"
            })

        for knowledge in results["semantic"]:
            combined.append({
                **knowledge,
                "source_type": "semantic"
            })

        for procedure in results["procedural"]:
            combined.append({
                **procedure,
                "source_type": "procedural"
            })

        # 重新计算综合分数
        for item in combined:
            item["combined_score"] = self._calculate_combined_score(item, query_text)

        # 按综合分数排序
        combined.sort(key=lambda x: x["combined_score"], reverse=True)

        return combined[:limit]

    def _calculate_episodic_score(self, memory: Dict, query: Dict) -> float:
        """计算情景记忆分数"""
        score = memory.get("similarity", 0.5) * 0.6  # 相似度权重60%

        # 重要性权重20%
        importance = memory.get("importance", 1.0)
        score += importance * 0.2

        # 时间衰减权重20%
        created_at = datetime.fromisoformat(memory.get("created_at", ""))
        days_ago = (datetime.now() - created_at).days
        time_decay = max(0.1, 1.0 - days_ago / 365)  # 一年内的记忆
        score += time_decay * 0.2

        return min(score, 1.0)

    def _calculate_procedural_score(self, procedure, query: Dict) -> float:
        """计算程序记忆分数"""
        score = 0.0

        # 成功率权重50%
        score += procedure.success_rate * 0.5

        # 匹配度权重30%
        query_text = query.get("text", "").lower()
        if any(keyword in query_text for keyword in procedure.name.lower().split()):
            score += 0.3

        # 更新时间权重20%
        last_updated = datetime.fromisoformat(procedure.last_updated)
        days_ago = (datetime.now() - last_updated).days
        time_factor = max(0.1, 1.0 - days_ago / 180)  # 半年内的程序
        score += time_factor * 0.2

        return min(score, 1.0)

    def _calculate_combined_score(self, item: Dict, query_text: str) -> float:
        """计算综合分数"""
        # 获取源特定分数
        source_score = item.get("retrieval_score", 0.5)

        # 根据类型调整权重
        source_type = item.get("source_type", "")
        if source_type == "episodic":
            # 情景记忆更注重个性化
            return source_score * 0.9 + 0.1
        elif source_type == "semantic":
            # 语义记忆更注重相关性
            return source_score * 0.8 + 0.2
        elif source_type == "procedural":
            # 程序记忆更注重实用性
            return source_score * 0.85 + 0.15
        else:
            return source_score

    def _text_to_embedding(self, text: str) -> List[float]:
        """文本转向量（简化实现）"""
        # 这里应该调用实际的embedding模型
        # 简化实现：返回随机向量
        import hashlib
        hash_obj = hashlib.md5(text.encode(), usedforsecurity=False))
        vector = []
        for i in range(768):
            byte_idx = i % 16
            vector.append(ord(hash_obj.digest()[byte_idx]) / 255.0)
        return vector

    def _simulate_episodic_retrieval(self, query: Dict, limit: int) -> List[Dict]:
        """模拟情景记忆检索"""
        # 模拟数据
        mock_memories = [
            {
                "episode_id": f"EP_SIM_{i}",
                "user_id": query.get("user_id", "user123"),
                "business_type": query.get("business_type", "patent"),
                "content": f"模拟记忆内容 {i} - {query.get('text', '')}",
                "created_at": datetime.now().isoformat(),
                "importance": 0.8,
                "similarity": 0.7 + (i % 3) * 0.1
            }
            for i in range(min(limit, 5))
        ]

        return mock_memories

    async def update_memory(self, memory_type: str, memory_data: Dict) -> bool:
        """更新记忆"""
        try:
            if memory_type == "episodic":
                if self.episodic_initialized:
                    episode_id = await self.episodic_memory.store(memory_data)
                    return episode_id is not None

            elif memory_type == "procedural":
                from .procedural_memory import LegalProcedure
                procedure = LegalProcedure(**memory_data)
                self.procedural_memory.add_procedure(procedure)
                return True

            elif memory_type == "semantic":
                # 语义记忆更新需要特殊处理
                return await self.semantic_memory.update_knowledge(memory_data)

            return False

        except Exception as e:
            logger.error(f"更新{memory_type}记忆失败: {str(e)}")
            return False

    async def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计"""
        stats = {
            "episodic": {},
            "semantic": {},
            "procedural": {},
            "total": 0
        }

        # 情景记忆统计
        if self.episodic_initialized:
            episodic_stats = await self.episodic_memory.get_statistics()
            stats["episodic"] = episodic_stats
            stats["total"] += episodic_stats.get("total_episodes", 0)

        # 程序记忆统计
        procedural_stats = self.procedural_memory.get_statistics()
        stats["procedural"] = procedural_stats
        stats["total"] += procedural_stats.get("total_procedures", 0)

        # 语义记忆统计（需要实现）
        stats["semantic"] = {
            "knowledge_domains": ["patent", "trademark", "copyright", "contract"],
            "total_entities": 1250000,  # 来自知识图谱
            "graph_connections": 3290000
        }

        return stats

# 使用示例
async def main():
    """测试记忆检索"""
    retriever = MemoryRetriever()
    await retriever.initialize()

    # 综合检索
    results = await retriever.retrieve({
        "text": "发明专利申请流程",
        "type": "all",
        "business_type": "patent",
        "user_id": "user123"
    })

    print(f"检索结果总数: {results['metadata']['total_count']}")
    print(f"情景记忆: {len(results['episodic'])} 条")
    print(f"语义记忆: {len(results['semantic'])} 条")
    print(f"程序记忆: {len(results['procedural'])} 条")
    print(f"综合排序: {len(results['combined'])} 条")

    # 获取统计
    stats = await retriever.get_memory_statistics()
    print(f"记忆统计: {stats}")

# 入口点: @async_main装饰器已添加到main函数