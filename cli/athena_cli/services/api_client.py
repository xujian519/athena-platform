"""
API客户端模块
API Client Module

Athena Gateway和服务的HTTP客户端

性能优化特性：
- 并发处理批量请求
- 本地缓存减少重复调用
- 连接池复用提升性能
"""

import httpx
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
import logging
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SimpleCache:
    """简单的内存缓存"""

    def __init__(self, ttl: int = 3600):
        """
        初始化缓存

        Args:
            ttl: 缓存过期时间（秒），默认1小时
        """
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = ttl

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            value, expire_time = self._cache[key]
            if datetime.now() < expire_time:
                return value
            else:
                # 过期删除
                del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        expire_time = datetime.now() + timedelta(seconds=self.ttl)
        self._cache[key] = (value, expire_time)

    def clear(self):
        """清空缓存"""
        self._cache.clear()

    def stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "ttl": self.ttl,
        }


class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str
    title: str
    applicant: str
    date: str
    score: float
    abstract: Optional[str] = None


class AnalysisResult(BaseModel):
    """分析结果模型"""
    patent_id: str
    analysis_type: str
    creativity_level: str
    key_features: List[str]
    technical_effect: str
    authorization_prospects: str
    confidence: float
    details: Dict[str, Any] = {}


class APIClient:
    """Athena API客户端（性能优化版 + 真实API支持）"""

    def __init__(
        self,
        base_url: str = "http://localhost:8005",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        max_concurrent: int = 10,
        use_real_api: bool = False,
        real_api_url: str = "http://localhost:8009",
    ):
        """
        初始化API客户端

        Args:
            base_url: API基础URL
            api_key: API密钥
            timeout: 请求超时时间（秒）
            enable_cache: 是否启用缓存
            cache_ttl: 缓存过期时间（秒）
            max_concurrent: 最大并发数
            use_real_api: 是否使用真实API（通过小诺协调服务）
            real_api_url: 真实API服务地址
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.use_real_api = use_real_api

        # 初始化缓存
        self.cache = SimpleCache(ttl=cache_ttl) if enable_cache else None
        self.enable_cache = enable_cache

        # 真实API适配器
        if use_real_api:
            from athena_cli.services.real_api_adapter import RealAPIAdapter
            self.real_api = RealAPIAdapter(base_url=real_api_url, timeout=timeout)
        else:
            self.real_api = None

        # 创建HTTP客户端（优化连接池配置）
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers(),
            limits=limits,
            # http2=True,  # 需要h2包，暂时禁用
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Athena-CLI/0.1.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

    async def search_patents(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "patent",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        搜索专利（支持缓存 + 真实API）

        Args:
            query: 搜索查询
            limit: 结果数量限制
            search_type: 搜索类型（patent/literature/case）
            use_cache: 是否使用缓存

        Returns:
            搜索结果字典
        """
        try:
            # 检查缓存
            if self.enable_cache and use_cache:
                cache_key = self.cache._generate_key("search", query, limit, search_type)
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"缓存命中: query={query}")
                    return cached_result

            # 使用真实API或模拟API
            if self.use_real_api and self.real_api:
                logger.info(f"使用真实API搜索: query={query}")
                result = await self.real_api.search_patents(query, limit, search_type)
            else:
                # 模拟API调用
                logger.info(f"使用模拟API搜索: query={query}, limit={limit}")
                await asyncio.sleep(0.5)  # 模拟网络延迟

                results = [
                    SearchResult(
                        id=f"CN{1000+i}A",
                        title=f"{query}相关专利 - 实施例{i+1}",
                        applicant="广东冠一机械科技有限公司",
                        date="2024-01-01",
                        score=0.95 - i * 0.05,
                        abstract=f"本发明涉及{query}的技术领域..."
                    )
                    for i in range(min(limit, 5))
                ]

                result = {
                    "query": query,
                    "total": len(results),
                    "results": [r.model_dump() for r in results],
                    "search_time": 0.5,
                    "cached": False,
                    "source": "mock_api",
                }

            # 保存到缓存
            if self.enable_cache and use_cache:
                cache_key = self.cache._generate_key("search", query, limit, search_type)
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise

    async def analyze_patent(
        self,
        patent_id: str,
        analysis_type: str = "creativity",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        分析专利（支持缓存 + 真实API）

        Args:
            patent_id: 专利号或文件路径
            analysis_type: 分析类型（creativity/invalidation/infringement）
            use_cache: 是否使用缓存

        Returns:
            分析结果字典
        """
        try:
            # 检查缓存
            if self.enable_cache and use_cache:
                cache_key = self.cache._generate_key("analyze", patent_id, analysis_type)
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"缓存命中: patent_id={patent_id}")
                    return cached_result

            # 使用真实API或模拟API
            if self.use_real_api and self.real_api:
                logger.info(f"使用真实API分析: patent_id={patent_id}")
                result = await self.real_api.analyze_patent(patent_id, analysis_type)
            else:
                # 模拟API调用
                logger.info(f"使用模拟API分析: patent_id={patent_id}, type={analysis_type}")
                await asyncio.sleep(2.0)  # 模拟分析时间

                result = AnalysisResult(
                    patent_id=patent_id,
                    analysis_type=analysis_type,
                    creativity_level="较高" if analysis_type == "creativity" else "未评估",
                    key_features=[
                        "采用深度学习算法优化模型性能",
                        "引入多模态数据融合技术",
                        "实现分布式训练加速",
                    ],
                    technical_effect="显著提升了系统的准确性和处理效率",
                    authorization_prospects="良好",
                    confidence=0.87,
                    details={
                        "novelty": "具有新颖性",
                        "inventiveness": "具有创造性",
                        "practicality": "具有实用性",
                    }
                )

                result = result.model_dump()
                result["cached"] = False
                result["source"] = "mock_api"

            # 保存到缓存
            if self.enable_cache and use_cache:
                cache_key = self.cache._generate_key("analyze", patent_id, analysis_type)
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"分析失败: {e}")
            raise

    async def batch_search(
        self,
        queries: List[str],
        limit_per_query: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        批量搜索（并发处理）⭐

        Args:
            queries: 查询列表
            limit_per_query: 每个查询的结果数量

        Returns:
            搜索结果列表
        """
        logger.info(f"批量搜索开始: {len(queries)}个查询")

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def search_with_semaphore(query: str, index: int) -> Dict[str, Any]:
            """带并发控制的搜索"""
            async with semaphore:
                logger.info(f"批量搜索 [{index+1}/{len(queries)}]: {query}")
                try:
                    result = await self.search_patents(query, limit_per_query)
                    return result

                except Exception as e:
                    logger.error(f"搜索失败 [{index+1}/{len(queries)}] {query}: {e}")
                    return {
                        "query": query,
                        "error": str(e),
                        "results": [],
                    }

        # 并发执行所有搜索
        tasks = [
            search_with_semaphore(query, i)
            for i, query in enumerate(queries)
        ]

        results = await asyncio.gather(*tasks)

        logger.info(f"批量搜索完成: {len(results)}个结果")
        return results

    async def batch_analyze(
        self,
        patent_ids: List[str],
        analysis_type: str = "creativity",
    ) -> List[Dict[str, Any]]:
        """
        批量分析专利（并发处理）⭐

        Args:
            patent_ids: 专利号列表
            analysis_type: 分析类型

        Returns:
            分析结果列表
        """
        logger.info(f"批量分析开始: {len(patent_ids)}个专利")

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def analyze_with_semaphore(patent_id: str, index: int) -> Dict[str, Any]:
            """带并发控制的分析"""
            async with semaphore:
                logger.info(f"批量分析 [{index+1}/{len(patent_ids)}]: {patent_id}")
                try:
                    result = await self.analyze_patent(patent_id, analysis_type)
                    return {
                        "patent_id": patent_id,
                        "status": "completed",
                        "result": result,
                    }

                except Exception as e:
                    logger.error(f"分析失败 [{index+1}/{len(patent_ids)}] {patent_id}: {e}")
                    return {
                        "patent_id": patent_id,
                        "status": "failed",
                        "error": str(e),
                    }

        # 并发执行所有分析
        tasks = [
            analyze_with_semaphore(patent_id, i)
            for i, patent_id in enumerate(patent_ids)
        ]

        results = await asyncio.gather(*tasks)

        logger.info(f"批量分析完成: {len(results)}个结果")
        return results

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接（支持真实API）

        Returns:
            连接状态
        """
        try:
            if self.use_real_api and self.real_api:
                # 测试真实API连接
                result = await self.real_api.test_connection()
                result["api_endpoint"] = self.real_api.base_url
                result["api_type"] = "real"
            else:
                # 模拟API连接测试
                start_time = asyncio.get_event_loop().time()
                await asyncio.sleep(0.1)
                response_time = asyncio.get_event_loop().time() - start_time

                result = {
                    "status": "ok",
                    "api_endpoint": self.base_url,
                    "api_type": "mock",
                    "response_time": round(response_time, 3),
                    "message": "模拟API连接正常",
                }

            # 添加缓存统计
            if self.enable_cache:
                result["cache"] = self.cache.stats()

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    def clear_cache(self):
        """清空缓存"""
        if self.cache:
            self.cache.clear()
            logger.info("缓存已清空")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if self.cache:
            return self.cache.stats()
        return {"message": "缓存未启用"}


# 同步客户端包装器
class SyncAPIClient:
    """同步API客户端（用于简单场景）"""

    def __init__(
        self,
        base_url: str = "http://localhost:8005",
        api_key: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        max_concurrent: int = 10,
    ):
        self.async_client = APIClient(
            base_url=base_url,
            api_key=api_key,
            enable_cache=enable_cache,
            cache_ttl=cache_ttl,
            max_concurrent=max_concurrent,
        )
        self._loop = None

    def _get_loop(self):
        """获取事件循环"""
        try:
            import asyncio
            return asyncio.get_event_loop()
        except RuntimeError:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def search_patents(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """同步搜索专利"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.search_patents(query, limit)
        )

    def analyze_patent(self, patent_id: str, analysis_type: str = "creativity") -> Dict[str, Any]:
        """同步分析专利"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.analyze_patent(patent_id, analysis_type)
        )

    def batch_search(self, queries: List[str], limit_per_query: int = 10) -> List[Dict[str, Any]]:
        """同步批量搜索"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.batch_search(queries, limit_per_query)
        )

    def batch_analyze(self, patent_ids: List[str], analysis_type: str = "creativity") -> List[Dict[str, Any]]:
        """同步批量分析"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.batch_analyze(patent_ids, analysis_type)
        )

    def close(self):
        """关闭客户端"""
        if self._loop and self._loop.is_running():
            self._loop.run_until_complete(self.async_client.close())

    def clear_cache(self):
        """清空缓存"""
        self.async_client.clear_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.async_client.get_cache_stats()

    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        loop = self._get_loop()
        return loop.run_until_complete(
            self.async_client.test_connection()
        )
