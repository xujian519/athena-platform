#!/usr/bin/env python3
"""
专利知识图谱SDK
Patent Knowledge Graph SDK

方便各种专利应用集成知识图谱服务的客户端SDK

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import asyncio
import logging
from typing import Any

import aiohttp
import requests

# 配置日志
logger = logging.getLogger(__name__)

class PatentKGClient:
    """专利知识图谱客户端SDK"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """
        初始化客户端

        Args:
            base_url: API服务地址
            api_key: API密钥（如果需要）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        # 设置请求头
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def query_knowledge(
        self,
        query: str,
        patent_text: str = "",
        context_type: str = "general",
        context: dict[str, Any] = None,
        user_id: str = None,
        application_id: str = None
    ) -> dict[str, Any]:
        """
        查询知识图谱

        Args:
            query: 查询问题
            patent_text: 专利文本
            context_type: 上下文类型
            context: 额外上下文
            user_id: 用户ID
            application_id: 应用ID

        Returns:
            查询结果
        """
        try:
            data = {
                "query": query,
                "patent_text": patent_text,
                "context_type": context_type,
                "context": context or {},
                "user_id": user_id,
                "application_id": application_id
            }

            response = self.session.post(
                f"{self.base_url}/query",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    def batch_query(
        self,
        queries: list[dict[str, Any],
        max_parallel: int = 5
    ) -> dict[str, Any]:
        """
        批量查询

        Args:
            queries: 查询列表
            max_parallel: 最大并行数

        Returns:
            批量查询结果
        """
        try:
            data = {
                "queries": queries,
                "max_parallel": max_parallel
            }

            response = self.session.post(
                f"{self.base_url}/batch/query",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Batch query failed: {e}")
            raise

    def extract_rules(
        self,
        patent_text: str,
        rule_types: list[str] = None,
        keywords: list[str] = None
    ) -> dict[str, Any]:
        """
        提取规则

        Args:
            patent_text: 专利文本
            rule_types: 规则类型
            keywords: 关键词

        Returns:
            提取的规则
        """
        try:
            data = {
                "patent_text": patent_text,
                "rule_types": rule_types or ["novelty", "creativity", "procedure"],
                "keywords": keywords
            }

            response = self.session.post(
                f"{self.base_url}/rules/extract",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Rule extraction failed: {e}")
            raise

    def similarity_search(
        self,
        text: str,
        similarity_threshold: float = 0.7,
        max_results: int = 10,
        collection: str = "patent_legal_vectors_1024"
    ) -> dict[str, Any]:
        """
        相似度搜索

        Args:
            text: 搜索文本
            similarity_threshold: 相似度阈值
            max_results: 最大结果数
            collection: 搜索集合

        Returns:
            搜索结果
        """
        try:
            data = {
                "text": text,
                "similarity_threshold": similarity_threshold,
                "max_results": max_results,
                "collection": collection
            }

            response = self.session.post(
                f"{self.base_url}/search/similarity",
                json=data
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            raise

    def get_statistics(self) -> dict[str, Any]:
        """获取服务统计"""
        try:
            response = self.session.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            raise

    def get_capabilities(self) -> dict[str, Any]:
        """获取服务能力"""
        try:
            response = self.session.get(f"{self.base_url}/capabilities")
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Get capabilities failed: {e}")
            raise


class PatentKGAsyncClient:
    """异步专利知识图谱客户端"""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        """
        初始化异步客户端

        Args:
            base_url: API服务地址
            api_key: API密钥
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    async def query_knowledge(
        self,
        query: str,
        patent_text: str = "",
        context_type: str = "general",
        context: dict[str, Any] = None,
        user_id: str = None,
        application_id: str = None
    ) -> dict[str, Any]:
        """异步查询知识图谱"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            data = {
                "query": query,
                "patent_text": patent_text,
                "context_type": context_type,
                "context": context or {},
                "user_id": user_id,
                "application_id": application_id
            }

            async with session.post(f"{self.base_url}/query", json=data) as response:
                response.raise_for_status()
                return await response.json()

    async def batch_query(
        self,
        queries: list[dict[str, Any],
        max_parallel: int = 5
    ) -> dict[str, Any]:
        """异步批量查询"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            data = {
                "queries": queries,
                "max_parallel": max_parallel
            }

            async with session.post(f"{self.base_url}/batch/query", json=data) as response:
                response.raise_for_status()
                return await response.json()


# 便捷函数

def create_client(**kwargs) -> PatentKGClient:
    """创建同步客户端"""
    return PatentKGClient(**kwargs)

def create_async_client(**kwargs) -> PatentKGAsyncClient:
    """创建异步客户端"""
    return PatentKGAsyncClient(**kwargs)


# 使用示例

def example_sync_usage() -> Any:
    """同步使用示例"""
    # 创建客户端
    client = create_client(base_url="http://localhost:8000")

    # 健康检查
    health = client.health_check()
    print(f"服务状态: {health.get('status')}")

    # 查询专利审查
    result = client.query_knowledge(
        query="这个专利是否符合新颖性要求？",
        patent_text="本发明涉及一种新的材料制备方法...",
        context_type="patent_review",
        application_id="patent_review_system"
    )

    print(f"查询ID: {result.get('query_id')}")
    print(f"识别意图: {result.get('intent')}")

    # 提取规则
    rules = client.extract_rules(
        patent_text="专利文本内容...",
        rule_types=["novelty", "creativity"]
    )

    print(f"提取规则数: {rules.get('rule_count')}")

async def example_async_usage():
    """异步使用示例"""
    # 创建异步客户端
    client = create_async_client()

    # 异步查询
    result = await client.query_knowledge(
        query="如何判断创造性？",
        patent_text="技术方案描述...",
        context_type="legal_advice"
    )

    print(f"异步查询结果: {result.get('query_id')}")

    # 批量查询
    queries = [
        {"query": "什么是专利的三性？"},
        {"query": "申请流程是什么？"}
    ]
    batch_result = await client.batch_query(queries)
    print(f"批量处理了 {batch_result.get('total_queries')} 个查询")

# 装饰器示例

def with_patent_kg(application_id: str = None) -> Any:
    """装饰器：为函数添加知识图谱功能"""
    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            client = create_client()
            # 从参数中提取 patent_text
            patent_text = kwargs.get('patent_text', '')

            if patent_text:
                # 自动提取规则
                rules = client.extract_rules(patent_text)
                kwargs['extracted_rules'] = rules

            # 执行原函数
            result = func(*args, **kwargs)

            return result
        return wrapper
    return decorator

# 使用装饰器的示例
@with_patent_kg(application_id="my_patent_app")
def analyze_patent(patent_text: str, **kwargs) -> Any:
    """分析专利函数"""
    rules = kwargs.get('extracted_rules', {})
    print(f"分析专利，提取了 {rules.get('rule_count', 0)} 条规则")
    return {"analysis": "completed", "rules": rules}

if __name__ == "__main__":
    # 运行示例
    print("=== 同步客户端示例 ===")
    example_sync_usage()

    print("\n=== 异步客户端示例 ===")
    asyncio.run(example_async_usage())

    print("\n=== 装饰器示例 ===")
    analyze_patent(
        patent_text="本发明涉及一种新技术...",
        extra_param="value"
    )
