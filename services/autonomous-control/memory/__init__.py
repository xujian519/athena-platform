#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆模块初始化
Memory Module Initialization

小娜智能体的记忆系统

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .procedural_memory import ProceduralMemory, LegalProcedure
from .memory_retriever import MemoryRetriever

logger = logging.getLogger(__name__)

class IntelligentMemorySystem:
    """智能记忆系统"""

    def __init__(self):
        """初始化记忆系统"""
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.procedural_memory = ProceduralMemory()
        self.memory_retriever = MemoryRetriever()
        self.initialized = False

    async def initialize(self):
        """初始化记忆系统"""
        try:
            await self.episodic_memory.initialize()
            await self.memory_retriever.initialize()
            self.initialized = True
            return True
        except Exception as e:
            logger.error(f"记忆系统初始化失败: {str(e)}")
            return False

    async def store(self, memory_data: Dict[str, Any]) -> str:
        """
        存储记忆

        Args:
            memory_data: 记忆数据
                {
                    "type": "episodic|semantic|procedural",
                    "data": {...}
                }

        Returns:
            记忆ID
        """
        memory_type = memory_data.get("type", "episodic")
        data = memory_data.get("data", {})

        if memory_type == "episodic":
            # 确保有必需字段
            required_fields = ["episode_id", "user_id", "business_type", "content"]
            for field in required_fields:
                if field not in data:
                    data[field] = f"auto_generated_{field}"

            episode_id = await self.episodic_memory.store(data)
            return episode_id

        elif memory_type == "procedural":
            if "procedure_id" not in data:
                data["procedure_id"] = f"PROC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            procedure = LegalProcedure(**data)
            return self.procedural_memory.add_procedure(procedure)

        elif memory_type == "semantic":
            # 语义记忆更新
            success = await self.semantic_memory.update_knowledge(data)
            return "semantic_updated" if success else "semantic_failed"

        return "unknown_type"

    async def retrieve(self, query: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
        """
        检索记忆

        Args:
            query: 查询条件
            limit: 返回数量

        Returns:
            检索结果
        """
        return await self.memory_retriever.retrieve(query, limit)

    async def recall(self, query: str, context: Dict = None) -> List[Dict]:
        """
        回忆相关信息

        Args:
            query: 查询文本
            context: 上下文

        Returns:
            相关记忆列表
        """
        # 构建查询
        search_query = {
            "text": query,
            "type": "all",
            "context": context or {}
        }

        # 检索记忆
        results = await self.retrieve(search_query, limit=20)

        # 返回综合排序的结果
        return results.get("combined", [])

    async def get_statistics(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        if self.initialized:
            return await self.memory_retriever.get_memory_statistics()
        else:
            return {
                "status": "not_initialized",
                "message": "记忆系统未初始化"
            }

    async def update_procedure_usage(self, procedure_id: str, success: bool):
        """更新程序使用记录"""
        self.procedural_memory.update_procedure_usage(procedure_id, success)

    async def recommend_action(self, situation: Dict[str, Any]) -> Dict | None:
        """
        基于记忆推荐行动

        Args:
            situation: 当前情况

        Returns:
            推荐的行动
        """
        # 检索相关记忆
        memories = await self.recall(
            f"{situation.get('description', '')} 推荐建议",
            {"business_type": situation.get("business_type")}
        )

        if not memories:
            return None

        # 提取最相关的程序
        procedural_memories = [m for m in memories if m.get("source_type") == "procedural"]
        if procedural_memories:
            best_procedure = procedural_memories[0]
            return {
                "action_type": "follow_procedure",
                "procedure_id": best_procedure.get("procedure_id"),
                "confidence": best_procedure.get("combined_score", 0),
                "description": f"建议遵循程序: {best_procedure.get('name', '')}"
            }

        # 提取相关案例
        episodic_memories = [m for m in memories if m.get("source_type") == "episodic"]
        if episodic_memories:
            best_memory = episodic_memories[0]
            return {
                "action_type": "reference_case",
                "episode_id": best_memory.get("episode_id"),
                "confidence": best_memory.get("combined_score", 0),
                "description": f"参考案例: {best_memory.get('title', '')}"
            }

        # 提取相关知识
        semantic_memories = [m for m in memories if m.get("source_type") == "semantic"]
        if semantic_memories:
            best_knowledge = semantic_memories[0]
            return {
                "action_type": "apply_knowledge",
                "knowledge_content": best_knowledge.get("content", ""),
                "confidence": best_knowledge.get("combined_score", 0),
                "description": "应用相关知识"
            }

        return None

__all__ = [
    'IntelligentMemorySystem',
    'EpisodicMemory',
    'SemanticMemory',
    'ProceduralMemory',
    'LegalProcedure',
    'MemoryRetriever'
]