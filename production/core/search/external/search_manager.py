#!/usr/bin/env python3
from __future__ import annotations
"""
外部搜索引擎管理器
External Search Engine Manager

集成多个外部搜索引擎的统一管理器

作者: Athena AI系统
创建时间: 2025-12-04
"""

import asyncio
import hashlib
import logging
import ssl
import time
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import aiohttp
import certifi

from ..types import Document, SearchResult, SearchType

logger = logging.getLogger(__name__)


class ExternalSearchManager:
    """外部搜索引擎管理器"""

    def __init__(self, config: dict[str, Any]):
        """
        初始化外部搜索引擎管理器

        Args:
            config: 外部搜索配置
        """
        self.config = config
        self.initialized = False

        # 搜索引擎配置
        self.engines = {
            "baidu": {
                "url": "https://www.baidu.com/s",
                "params": {"wd": "", "pn": 0, "rn": 10},
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
            },
            "sogou": {
                "url": "https://www.sogou.com/web",
                "params": {"query": "", "page": 1, "num": 10},
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            },
            "bing": {
                "url": "https://www.bing.com/search",
                "params": {"q": "", "count": 10, "first": 1},
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                },
            },
        }

        # 启用的搜索引擎
        self.enabled_engines = self.config.get("engines", ["baidu", "sogou"])

    async def initialize(self):
        """初始化外部搜索引擎管理器"""
        if self.initialized:
            return

        logger.info("🚀 初始化外部搜索引擎管理器...")

        try:
            # 验证搜索引擎配置
            await self._verify_engines()

            self.initialized = True
            logger.info("✅ 外部搜索引擎管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 外部搜索引擎管理器初始化失败: {e}")
            raise

    async def _verify_engines(self):
        """验证搜索引擎配置"""
        for engine_name in self.enabled_engines:
            if engine_name in self.engines:
                logger.info(f"✅ 配置搜索引擎: {engine_name}")
            else:
                logger.warning(f"⚠️ 未知搜索引擎: {engine_name}")

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """
        执行外部搜索

        Args:
            query: 搜索查询
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        if not self.initialized:
            await self.initialize()

        logger.info(f"🌐 执行外部搜索: {query}")

        start_time = time.time()

        try:
            # 并行执行多个搜索引擎
            tasks = []
            for engine_name in self.enabled_engines:
                if engine_name in self.engines:
                    task = self._search_engine(engine_name, query, limit)
                    tasks.append(task)

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 处理结果
                all_results = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"搜索引擎 {self.enabled_engines[i]} 错误: {result}")
                    else:
                        all_results.extend(result)

                # 结果去重和处理
                processed_results = self._process_external_results(
                    query, all_results, time.time() - start_time
                )

                return processed_results

            return []

        except Exception as e:
            logger.error(f"❌ 外部搜索失败: {e}")
            return []

    async def _search_engine(self, engine_name: str, query: str, limit: int) -> list[Document]:
        """执行单个搜索引擎"""
        engine_config = self.engines[engine_name]

        try:
            # 创建SSL上下文，使用certifi证书库
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.get("timeout", 30)),
                connector=aiohttp.TCPConnector(ssl=ssl_context)
            ) as session:

                # 构建搜索URL
                search_params = engine_config["params"].copy()
                search_params.update(
                    {
                        (
                            "wd"
                            if engine_name == "baidu"
                            else "query" if engine_name in ["sogou", "bing"] else "q"
                        ): query,
                        (
                            "rn"
                            if engine_name == "baidu"
                            else "num" if engine_name == "bing" else "num"
                        ): limit,
                    }
                )

                url = f"{engine_config['url']}?{urlencode(search_params)}"

                logger.debug(f"搜索 {engine_name}: {url}")

                # 发送请求
                async with session.get(url, headers=engine_config["headers"]) as response:
                    if response.status == 200:
                        content = await response.text()
                        return self._parse_search_results(content, engine_name)
                    else:
                        logger.warning(f"⚠️ {engine_name} 搜索失败: HTTP {response.status}")
                        return []

        except asyncio.TimeoutError:
            logger.warning(f"⚠️ {engine_name} 搜索超时")
            return []
        except Exception as e:
            logger.error(f"❌ {engine_name} 搜索异常: {e}")
            return []

    def _parse_search_results(self, html_content: str, engine_name: str) -> list[Document]:
        """
        解析搜索结果HTML

        Args:
            html_content: HTML内容
            engine_name: 搜索引擎名称

        Returns:
            解析出的文档列表
        """
        # 这里应该实现具体的HTML解析逻辑
        # 现在返回模拟结果用于演示

        mock_results = [
            Document(
                id=f"{engine_name}_{i}_{hash(html_content[:100]) % 10000}",
                title=f"从{engine_name}找到的搜索结果 {i+1}",
                content=f"这是一个从{engine_name}搜索引擎找到的相关内容",
                metadata={
                    "source": "external_search",
                    "engine": engine_name,
                    "rank": i + 1,
                    "url": f"https://example.com/{engine_name}/{i+1}",
                },
            )
            for i in range(3)  # 模拟3个结果
        ]

        return mock_results

    def _process_external_results(
        self, query: str, raw_documents: list[Document], total_time: float
    ) -> list[SearchResult]:
        """
        处理外部搜索结果

        Args:
            query: 搜索查询
            raw_documents: 原始文档列表
            total_time: 总搜索时间

        Returns:
            处理后的搜索结果列表
        """
        if not raw_documents:
            return [
                SearchResult(
                    documents=[],
                    scores=[],
                    query=query,
                    search_type=SearchType.FULLTEXT,
                    total_time=total_time,
                    total_found=0,
                )
            ]

        # 去重(基于URL)
        seen_urls = set()
        unique_documents = []

        for doc in raw_documents:
            url = doc.metadata.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_documents.append(doc)

        # 按来源和排名排序
        unique_documents.sort(
            key=lambda x: (x.metadata.get("engine", ""), x.metadata.get("rank", 999))
        )

        # 创建搜索结果
        scores = [1.0 / (doc.metadata.get("rank", 1)) for doc in unique_documents]

        return [
            SearchResult(
                documents=unique_documents,
                scores=scores,
                query=query,
                search_type=SearchType.FULLTEXT,
                total_time=total_time,
                total_found=len(unique_documents),
            )
        ]

    def get_available_engines(self) -> list[str]:
        """获取可用的搜索引擎列表"""
        return self.enabled_engines

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        try:
            # 测试各个搜索引擎的连通性
            engine_status = {}
            for engine_name in self.enabled_engines:
                try:
                    # 简单的连通性测试
                    engine_config = self.engines[engine_name]
                    async with aiohttp.ClientSession(timeout=5) as session:
                        async with session.head(engine_config["url"]) as response:
                            engine_status[engine_name] = response.status == 200
                except Exception as e:
                    engine_status[engine_name] = False
                    logger.warning(f"搜索引擎 {engine_name} 健康检查失败: {e}")

            all_healthy = all(engine_status.values())

            return {
                "status": "healthy" if all_healthy else "degraded",
                "initialized": self.initialized,
                "engines": engine_status,
                "enabled_engines": self.enabled_engines,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def shutdown(self):
        """关闭外部搜索引擎管理器"""
        logger.info("🔄 关闭外部搜索引擎管理器...")
        self.initialized = False
        logger.info("✅ 外部搜索引擎管理器已关闭")

    def _generate_result_id(self, engine_name: str, title: str) -> str:
        """生成结果ID"""
        content = f"{engine_name}:{title}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
