#!/usr/bin/env python3
from __future__ import annotations
"""
Serper API 管理器
Serper API Manager

统一管理 Serper API 调用,支持 Google Search、Scholar、Patents

作者: 小诺·双鱼公主 (Xiaonuo Pisces Princess)
版本: v1.0.0
创建: 2025-12-31
"""

import asyncio
import hashlib
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv

    # 加载项目根目录的 .env 文件
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"已加载 .env 文件: {env_path}")
except ImportError:
    # python-dotenv 未安装,跳过
    pass


class SerperSearchType(Enum):
    """Serper 搜索类型"""

    SEARCH = "search"  # Google 搜索
    SCHOLAR = "scholar"  # Google Scholar
    PATENTS = "patents"  # Google Patents


@dataclass
class SerperConfig:
    """Serper 配置"""

    api_key: str
    base_url: str = "https://google.serper.dev"
    timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_per_minute: int = 100
    enable_cache: bool = True
    cache_ttl_seconds: int = 86400  # 24小时


@dataclass
class SerperSearchRequest:
    """Serper 搜索请求"""

    query: str
    search_type: SerperSearchType = SerperSearchType.SEARCH
    num_results: int = 10
    page: int = 1
    # 高级参数
    gl: str | None = None  # 地区 (如: cn, us)
    hl: str | None = None  # 语言 (如: zh-CN, en)
    start: int | None = None  # 起始位置
    filter: int | None = None  # 过滤重复结果


@dataclass
class SerperSearchResult:
    """Serper 搜索结果"""

    success: bool
    query: str
    search_type: str
    total_results: int
    results: list[dict[str, Any]]
    search_time: float
    api_credits_used: int = 1
    error_message: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SerperAPIManager:
    """
    Serper API 管理器

    功能:
    • 统一的 API 调用接口
    • 自动速率限制
    • 智能重试机制
    • 信用点使用追踪
    • 结果缓存管理
    """

    def __init__(self, config: SerperConfig | None = None):
        """
        初始化 Serper API 管理器

        Args:
            config: Serper 配置 (如果为None,则从环境变量读取)
        """
        if config is None:
            # 从环境变量读取配置
            api_key = os.getenv("SERPER_API_KEY", "")
            if not api_key:
                logger.warning("⚠️  未找到 SERPER_API_KEY 环境变量")

            config = SerperConfig(
                api_key=api_key,
                base_url=os.getenv("SERPER_API_BASE_URL", "https://google.serper.dev"),
                timeout=int(os.getenv("SERPER_TIMEOUT", "10")),
                max_retries=int(os.getenv("SERPER_MAX_RETRIES", "3")),
                rate_limit_per_minute=int(os.getenv("SERPER_RATE_LIMIT", "100")),
            )

        self.config = config
        self.session: aiohttp.ClientSession | None = None

        # 速率限制
        self.request_times: list[datetime] = []
        self.rate_limit_lock = asyncio.Lock()

        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_credits_used = 0

        # 缓存
        self._cache: dict[str, SerperSearchResult] = {}

        logger.info("🔧 Serper API 管理器初始化完成")
        logger.info(f"   基础URL: {config.base_url}")
        logger.info(f"   速率限制: {config.rate_limit_per_minute}/分钟")
        logger.info(f"   API密钥: {config.api_key[:10]}...{config.api_key[-6:]}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def initialize(self) -> bool:
        """初始化 HTTP 会话"""
        try:
            if self.session is None:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self.session = aiohttp.ClientSession(timeout=timeout)
                logger.info("✅ Serper HTTP 会话已创建")
            return True
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def close(self):
        """关闭 HTTP 会话"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("🔌 Serper HTTP 会话已关闭")

    async def search(
        self, request: SerperSearchRequest, use_cache: bool | None = None
    ) -> SerperSearchResult:
        """
        执行搜索

        Args:
            request: 搜索请求
            use_cache: 是否使用缓存 (None 则使用配置默认值)

        Returns:
            SerperSearchResult: 搜索结果
        """
        # 检查缓存
        if use_cache is None:
            use_cache = self.config.enable_cache

        if use_cache:
            cached = self._get_from_cache(request)
            if cached:
                logger.info(f"💨 命中缓存: {request.query[:50]}...")
                return cached

        # 速率限制
        await self._wait_for_rate_limit()

        # 执行搜索
        result = await self._execute_search(request)

        # 更新统计
        self.total_requests += 1
        if result.success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        self.total_credits_used += result.api_credits_used

        # 缓存结果
        if use_cache and result.success:
            self._save_to_cache(request, result)

        return result

    async def batch_search(
        self, requests: list[SerperSearchRequest], max_concurrent: int = 5
    ) -> list[SerperSearchResult]:
        """
        批量搜索

        Args:
            requests: 搜索请求列表
            max_concurrent: 最大并发数

        Returns:
            list[SerperSearchResult]: 搜索结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def search_with_semaphore(req: SerperSearchRequest):
            async with semaphore:
                return await self.search(req)

        tasks = [search_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    SerperSearchResult(
                        success=False,
                        query=requests[i].query,
                        search_type=requests[i].search_type.value,
                        total_results=0,
                        results=[],
                        search_time=0.0,
                        error_message=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    def get_statistics(self) -> dict[str, Any]:
        """
        获取使用统计

        Returns:
            统计信息字典
        """
        success_rate = (
            self.successful_requests / self.total_requests * 100 if self.total_requests > 0 else 0
        )

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{success_rate:.2f}%",
            "total_credits_used": self.total_credits_used,
            "cache_size": len(self._cache),
            "remaining_budget": 2500 - self.total_credits_used,  # 假设初始2500
        }

    # === 私有方法 ===

    async def _execute_search(self, request: SerperSearchRequest) -> SerperSearchResult:
        """执行实际的搜索请求"""
        start_time = asyncio.get_event_loop().time()

        # 构建请求
        endpoint = f"/{request.search_type.value}"
        url = f"{self.config.base_url}{endpoint}"

        headers = {"X-API-KEY": self.config.api_key, "Content-Type": "application/json"}

        payload = {"q": request.query, "num": request.num_results}

        # 添加可选参数
        if request.gl:
            payload["gl"] = request.gl
        if request.hl:
            payload["hl"] = request.hl
        if request.start is not None:
            payload["start"] = request.start
        if request.filter is not None:
            payload["filter"] = request.filter

        # 执行请求(带重试)
        for attempt in range(self.config.max_retries):
            try:
                logger.info(
                    f"🔍 Serper 搜索 [{attempt+1}/{self.config.max_retries}]: "
                    f"{request.query[:50]}..."
                )

                async with self.session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        search_time = asyncio.get_event_loop().time() - start_time

                        result = SerperSearchResult(
                            success=True,
                            query=request.query,
                            search_type=request.search_type.value,
                            total_results=int(
                                data.get("search_Information", {})
                                .get("total_Results", "0")
                                .replace(",", "")
                            ),
                            results=self._parse_results(data, request.search_type),
                            search_time=search_time,
                            api_credits_used=1,
                        )

                        logger.info(
                            f"✅ 搜索成功: 找到 {result.total_results} 个结果, "
                            f"耗时 {search_time:.2f}s"
                        )

                        return result

                    elif response.status == 429:
                        # 速率限制,等待后重试
                        wait_time = self.config.retry_delay * (2**attempt)
                        logger.warning(f"⏳ 速率限制,等待 {wait_time:.1f}s 后重试...")
                        await asyncio.sleep(wait_time)
                        continue

                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API 错误 {response.status}: {error_text}")

                        if attempt == self.config.max_retries - 1:
                            return SerperSearchResult(
                                success=False,
                                query=request.query,
                                search_type=request.search_type.value,
                                total_results=0,
                                results=[],
                                search_time=asyncio.get_event_loop().time() - start_time,
                                error_message=f"HTTP {response.status}: {error_text}",
                            )

            except asyncio.TimeoutError:
                logger.warning(f"⏱️  请求超时 (尝试 {attempt+1})")
                if attempt == self.config.max_retries - 1:
                    return SerperSearchResult(
                        success=False,
                        query=request.query,
                        search_type=request.search_type.value,
                        total_results=0,
                        results=[],
                        search_time=0.0,
                        error_message="请求超时",
                    )

            except Exception as e:
                logger.error(f"❌ 请求异常: {e}")
                if attempt == self.config.max_retries - 1:
                    return SerperSearchResult(
                        success=False,
                        query=request.query,
                        search_type=request.search_type.value,
                        total_results=0,
                        results=[],
                        search_time=0.0,
                        error_message=str(e),
                    )

            # 等待后重试
            await asyncio.sleep(self.config.retry_delay)

        # 不应该到达这里
        return SerperSearchResult(
            success=False,
            query=request.query,
            search_type=request.search_type.value,
            total_results=0,
            results=[],
            search_time=0.0,
            error_message="未知错误",
        )

    def _parse_results(
        self, data: dict[str, Any], search_type: SerperSearchType
    ) -> list[dict[str, Any]]:
        """解析搜索结果"""
        results = []

        # 获取有机搜索结果
        organic = data.get("organic", [])

        if search_type == SerperSearchType.SCHOLAR:
            # Scholar 结果解析
            for item in organic:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "type": "scholar",
                    # Scholar 特有字段(如果有)
                    "authors": item.get("authors", []),
                    "year": item.get("year"),
                    "publication": item.get("publication"),
                    "citation": item.get("citation"),
                }
                results.append(result)

        elif search_type == SerperSearchType.PATENTS:
            # Patents 结果解析
            for item in organic:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "type": "patent",
                }
                results.append(result)

        else:
            # 普通 Google 搜索
            for item in organic:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "type": "web",
                }
                results.append(result)

        return results

    async def _wait_for_rate_limit(self):
        """等待以符合速率限制"""
        async with self.rate_limit_lock:
            now = datetime.now()

            # 清理超过1分钟的旧记录
            cutoff_time = now - timedelta(seconds=60)
            self.request_times = [t for t in self.request_times if t > cutoff_time]

            # 检查是否需要等待
            if len(self.request_times) >= self.config.rate_limit_per_minute:
                # 计算需要等待的时间
                oldest_request = self.request_times[0]
                wait_seconds = 60 - (now - oldest_request).total_seconds()

                if wait_seconds > 0:
                    logger.info(f"⏳ 速率限制等待 {wait_seconds:.1f}s...")
                    await asyncio.sleep(wait_seconds)

                    # 重新清理
                    cutoff_time = now - timedelta(seconds=60)
                    self.request_times = [t for t in self.request_times if t > cutoff_time]

            # 记录本次请求
            self.request_times.append(now)

    def _get_cache_key(self, request: SerperSearchRequest) -> str:
        """生成缓存键"""
        key_data = f"{request.search_type.value}:{request.query}:{request.num_results}"
        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, request: SerperSearchRequest) -> SerperSearchResult | None:
        """从缓存获取结果"""
        cache_key = self._get_cache_key(request)
        return self._cache.get(cache_key)

    def _save_to_cache(self, request: SerperSearchRequest, result: SerperSearchResult) -> Any:
        """保存结果到缓存"""
        cache_key = self._get_cache_key(request)
        self._cache[cache_key] = result

        # 限制缓存大小
        if len(self._cache) > 1000:
            # 删除最旧的10%
            keys_to_remove = list(self._cache.keys())[:100]
            for key in keys_to_remove:
                del self._cache[key]


# 工厂函数
async def create_serper_manager(
    api_key: str | None = None, config: SerperConfig | None = None
) -> SerperAPIManager:
    """
    创建并初始化 Serper API 管理器

    Args:
        api_key: Serper API 密钥 (如果为None,从环境变量读取)
        config: 可选的配置对象

    Returns:
        SerperAPIManager: 初始化完成的管理器
    """
    if config is None:
        if api_key is None:
            api_key = os.getenv("SERPER_API_KEY", "")
        config = SerperConfig(api_key=api_key)

    manager = SerperAPIManager(config)
    await manager.initialize()

    return manager


if __name__ == "__main__":
    # 测试代码
    async def test_serper():
        """测试 Serper API"""
        print("🧪 测试 Serper API 管理器")
        print()

        async with SerperAPIManager() as manager:
            # 测试 Google Scholar 搜索
            print("=" * 60)
            print("测试 1: Google Scholar 搜索")
            print("=" * 60)

            request = SerperSearchRequest(
                query="artificial intelligence", search_type=SerperSearchType.SCHOLAR, num_results=5
            )

            result = await manager.search(request)

            print(f"查询: {result.query}")
            print(f"成功: {result.success}")
            print(f"总结果数: {result.total_results}")
            print(f"搜索时间: {result.search_time:.2f}s")
            print(f"API 信用点使用: {result.api_credits_used}")

            if result.results:
                print(f"\n前 {len(result.results)} 个结果:")
                for i, r in enumerate(result.results[:3], 1):
                    print(f"\n{i}. {r['title']}")
                    print(f"   链接: {r['link']}")
                    print(f"   摘要: {r['snippet'][:100]}...")

            # 统计信息
            print("\n" + "=" * 60)
            print("统计信息")
            print("=" * 60)
            stats = manager.get_statistics()
            for key, value in stats.items():
                print(f"{key}: {value}")

    # 运行测试
    asyncio.run(test_serper())
