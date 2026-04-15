#!/usr/bin/env python3
"""
LLM增强的向量搜索引擎
LLM Enhanced Vector Search with GLM-4.7 Cloud

集成GLM-4.7云端模型,提供查询理解和答案生成能力
已从本地Qwen模型迁移到云端GLM-4.7

作者: Athena AI Team
创建时间: 2026-01-09
版本: v2.0.0 (GLM-4.7 Cloud Migration)
更新: 2026-01-15
"""

from __future__ import annotations
import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from core.cognition.llm_interface import LLMInterface, LLMRequest
from core.vector_db.enhanced_vector_search_with_reranker import (
    EnhancedSearchResult,
    SearchMode,
    get_enhanced_searcher,
)

logger = logging.getLogger(__name__)


class LLMOperation(Enum):
    """LLM操作类型"""

    QUERY_REWRITE = "query_rewrite"  # 查询重写
    ANSWER_GENERATION = "answer_generation"  # 答案生成
    QUERY_UNDERSTANDING = "query_understanding"  # 查询理解
    RESULT_SUMMARY = "result_summary"  # 结果摘要
    FULL_PIPELINE = "full_pipeline"  # 完整流程


@dataclass
class LLMEnhancedSearchConfig:
    """LLM增强搜索配置(GLM-4.7云端版)"""

    # GLM-4.7云端模型配置
    use_cloud: bool = True  # 使用云端模型
    model_name: str = "glm-4.7"  # 模型名称
    temperature: float = 0.3  # 温度参数(专业任务较低)
    max_tokens: int = 500  # 最大生成token数

    # 任务类型配置
    task_type: str = "patent_analysis"  # 任务类型
    system_message: str | None = None  # 系统消息

    # 性能配置
    enable_cache: bool = True  # 启用缓存
    timeout: int = 60  # 超时时间(秒)

    # RAG增强配置
    use_rag: bool = False  # 是否使用RAG增强
    retrieve_k: int = 5  # 检索数量


class GLMCloudLLMService:
    """GLM云端LLM服务"""

    def __init__(self, config: LLMEnhancedSearchConfig):
        """初始化GLM云端服务

        Args:
            config: LLM增强搜索配置
        """
        self.config = config
        self.llm = LLMInterface()
        self.is_loaded = False

    async def load(self) -> bool:
        """加载GLM云端客户端"""
        try:
            logger.info("📡 连接GLM-4.7云端服务...")
            await self.llm.initialize()
            self.is_loaded = True
            logger.info("✅ GLM-4.7云端服务就绪")
            return True
        except Exception as e:
            logger.error(f"❌ GLM云端服务加载失败: {e}")
            return False

    async def unload(self):
        """卸载GLM云端服务"""
        if self.is_loaded:
            await self.llm.cleanup()
            self.is_loaded = False
            logger.info("🔒 GLM云端服务已卸载")

    async def generate(
        self, prompt: str, operation: LLMOperation = LLMOperation.ANSWER_GENERATION
    ) -> dict[str, Any]:
        """生成文本

        Args:
            prompt: 提示文本
            operation: LLM操作类型

        Returns:
            生成结果
        """
        if not self.is_loaded:
            raise RuntimeError("GLM云端服务未加载")

        # 根据操作类型选择系统消息
        system_messages = {
            LLMOperation.QUERY_REWRITE: "你是专业的查询优化专家,擅长改写和扩展查询。",
            LLMOperation.ANSWER_GENERATION: "你是专业的专利分析师,擅长基于检索结果生成专业答案。",
            LLMOperation.QUERY_UNDERSTANDING: "你是专业的查询理解专家,擅长分析用户意图。",
            LLMOperation.RESULT_SUMMARY: "你是专业的文档摘要专家,擅长提取关键信息。",
            LLMOperation.FULL_PIPELINE: "你是专业的智能助手,擅长处理复杂的检索和分析任务。",
        }

        system_message = system_messages.get(operation, "你是专业的智能助手。")

        # 构建请求
        request = LLMRequest(
            prompt=prompt,
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            system_message=system_message,
        )

        # 调用GLM
        start_time = time.time()
        response = await self.llm.call_llm(request)
        elapsed_time = time.time() - start_time

        return {
            "text": response.content,
            "model": response.model_used,
            "tokens_used": response.usage.get("total_tokens", 0),
            "generation_time": elapsed_time,
            "operation": operation.value,
        }


class LLMEnhancedVectorSearch:
    """LLM增强的向量搜索引擎(GLM云端版)"""

    def __init__(self, config: LLMEnhancedSearchConfig = None):
        """初始化LLM增强搜索引擎

        Args:
            config: 搜索配置
        """
        self.config = config or LLMEnhancedSearchConfig()

        # 初始化向量搜索引擎
        self.vector_searcher = get_enhanced_searcher()

        # 初始化LLM服务
        if self.config.use_cloud:
            self.llm_service = GLMCloudLLMService(self.config)
        else:
            logger.warning("⚠️  未启用云端LLM,部分功能将不可用")
            self.llm_service = None

        self.is_loaded = False
        self.stats = {
            "total_searches": 0,
            "llm_calls": 0,
            "avg_response_time": 0.0,
        }

    async def load(self) -> bool:
        """加载搜索引擎"""
        try:
            # 加载向量搜索引擎
            if not self.vector_searcher.is_loaded:
                self.vector_searcher.load()

            # 加载LLM服务
            if self.llm_service and not await self.llm_service.load():
                logger.warning("⚠️  LLM服务加载失败,将只使用向量搜索")

            self.is_loaded = True
            logger.info("✅ LLM增强搜索引擎初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 搜索引擎初始化失败: {e}")
            return False

    async def unload(self):
        """卸载搜索引擎"""
        if self.vector_searcher.is_loaded:
            self.vector_searcher.unload()

        if self.llm_service:
            await self.llm_service.unload()

        self.is_loaded = False
        logger.info("🔒 LLM增强搜索引擎已卸载")

    async def search(
        self,
        query: str,
        mode: SearchMode = SearchMode.HYBRID,
        top_k: int = 10,
        enable_llm: bool = True,
        operation: LLMOperation = LLMOperation.FULL_PIPELINE,
    ) -> EnhancedSearchResult:
        """执行增强搜索

        Args:
            query: 查询文本
            mode: 搜索模式
            top_k: 返回结果数量
            enable_llm: 是否启用LLM增强
            operation: LLM操作类型

        Returns:
            增强搜索结果
        """
        start_time = time.time()
        self.stats["total_searches"] += 1

        try:
            # 步骤1: 向量搜索
            search_results = self.vector_searcher.search(
                query=query,
                mode=mode,
                top_k=top_k,
            )

            # 步骤2: LLM增强(如果启用)
            llm_enhanced_result = None
            if enable_llm and self.llm_service and self.llm_service.is_loaded:
                self.stats["llm_calls"] += 1

                # 构建LLM提示
                llm_prompt = self._build_llm_prompt(query, search_results, operation)

                # 调用GLM生成
                llm_result = await self.llm_service.generate(llm_prompt, operation)

                llm_enhanced_result = {
                    "generated_text": llm_result["text"],
                    "model": llm_result["model"],
                    "tokens_used": llm_result["tokens_used"],
                    "generation_time": llm_result["generation_time"],
                    "operation": llm_result["operation"],
                }

            # 构建结果
            elapsed_time = time.time() - start_time
            self.stats["avg_response_time"] = (
                self.stats["avg_response_time"] * (self.stats["total_searches"] - 1) + elapsed_time
            ) / self.stats["total_searches"]

            return EnhancedSearchResult(
                query=query,
                results=search_results.results[:top_k],
                mode=mode,
                total_found=search_results.total_found,
                search_time=search_results.search_time,
                llm_enhanced=llm_enhanced_result,
                total_time=elapsed_time,
            )

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}", exc_info=True)
            raise

    def _build_llm_prompt(self, query: str, search_results: Any, operation: LLMOperation) -> str:
        """构建LLM提示

        Args:
            query: 原始查询
            search_results: 向量搜索结果
            operation: LLM操作类型

        Returns:
            LLM提示文本
        """
        if operation == LLMOperation.QUERY_REWRITE:
            return f"""请将以下查询改写为更适合向量检索的形式:

原始查询: {query}

要求:
1. 保留核心意图
2. 添加相关关键词
3. 使用专业术语
4. 输出改写后的查询

改写后的查询:"""

        elif operation == LLMOperation.ANSWER_GENERATION:
            results_text = "\n".join(
                [
                    f"{i+1}. {r.get('title', 'N/A')}: {r.get('content', 'N/A')[:100]}..."
                    for i, r in enumerate(search_results.results[:5])
                ]
            )

            return f"""基于以下检索结果,回答用户问题:

用户问题: {query}

检索结果:
{results_text}

请提供专业、准确的回答:"""

        elif operation == LLMOperation.QUERY_UNDERSTANDING:
            return f"""分析以下查询的意图和关键信息:

查询: {query}

请分析:
1. 用户意图
2. 关键实体
3. 领域分类
4. 相关概念

分析结果:"""

        elif operation == LLMOperation.RESULT_SUMMARY:
            results_text = "\n".join(
                [
                    f"- {r.get('title', 'N/A')}: {r.get('content', 'N/A')[:50]}..."
                    for r in search_results.results[:10]
                ]
            )

            return f"""请总结以下检索结果的关键信息:

检索结果:
{results_text}

请提供:
1. 主要发现
2. 关键信息
3. 建议行动

摘要:"""

        else:  # FULL_PIPELINE
            return f"""请处理以下查询并提供专业分析:

查询: {query}

请提供:
1. 查询理解
2. 相关信息检索
3. 专业分析和建议

完整回答:"""

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "is_loaded": self.is_loaded,
            "llm_available": self.llm_service is not None and self.llm_service.is_loaded,
        }


# 工厂函数
def get_llm_enhanced_searcher(config: LLMEnhancedSearchConfig = None) -> LLMEnhancedVectorSearch:
    """获取LLM增强搜索引擎实例

    Args:
        config: 搜索配置

    Returns:
        LLM增强搜索引擎实例
    """
    return LLMEnhancedVectorSearch(config)


# 使用示例
async def demo():
    """使用示例"""
    config = LLMEnhancedSearchConfig(
        use_cloud=True,
        model_name="glm-4.7",
        temperature=0.3,
    )

    searcher = get_llm_enhanced_searcher(config)

    # 加载
    await searcher.load()

    # 搜索
    result = await searcher.search(
        query="深度学习在图像识别中的应用",
        enable_llm=True,
        operation=LLMOperation.FULL_PIPELINE,
    )

    print(f"查询: {result.query}")
    print(f"找到 {result.total_found} 个结果")
    if result.llm_enhanced:
        print(f"LLM增强: {result.llm_enhanced['generated_text'][:200]}...")

    # 卸载
    await searcher.unload()


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo())
