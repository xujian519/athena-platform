"""
统一搜索管理器
解决循环依赖问题,提供统一的搜索接口
"""

from __future__ import annotations
import asyncio

from .base import BaseSearchEngine, SearchQuery, SearchResponse, SearchType
from .factory import SearchEngineFactory


class UnifiedSearchManager:
    """统一搜索管理器"""

    def __init__(self):
        self._engines: dict[str, BaseSearchEngine] = {}
        self._default_engines: dict[SearchType, str] = {
            SearchType.WEB: "web",
            SearchType.PATENT: "patent",
            SearchType.ACADEMIC: "web",
            SearchType.DEEPSEARCH: "deepsearch",
        }

    def add_engine(
        self, name: str, engine: BaseSearchEngine, set_as_default: SearchType | None = None
    ) -> None:
        """
        添加搜索引擎

        Args:
            name: 引擎名称
            engine: 引擎实例
            set_as_default: 是否设置为默认引擎
        """
        self._engines[name] = engine
        if set_as_default:
            self._default_engines[set_as_default] = name

    def get_engine(
        self, name: str | None = None, search_type: SearchType | None = None
    ) -> BaseSearchEngine:
        """
        获取搜索引擎

        Args:
            name: 指定引擎名称
            search_type: 搜索类型

        Returns:
            搜索引擎实例
        """
        if name:
            if name not in self._engines:
                # 尝试创建新实例
                self._engines[name] = SearchEngineFactory.create_engine(name)
            return self._engines[name]

        if search_type:
            default_name = self._default_engines.get(search_type)
            if default_name and default_name not in self._engines:
                self._engines[default_name] = SearchEngineFactory.create_engine(default_name)
            return self._engines.get(default_name)

        raise ValueError("Must specify either name or search_type")

    async def search(
        self,
        query: str,
        search_type: SearchType = SearchType.WEB,
        engine_name: str | None = None,
        **kwargs,
    ) -> SearchResponse:
        """
        执行搜索

        Args:
            query: 搜索查询
            search_type: 搜索类型
            engine_name: 指定引擎名称
            **kwargs: 其他参数

        Returns:
            搜索结果
        """
        # 创建查询对象
        search_query = SearchQuery(query=query, search_type=search_type, **kwargs)

        # 获取搜索引擎
        engine = self.get_engine(engine_name, search_type)

        # 验证查询
        if not engine.validate_query(search_query):
            raise ValueError("Invalid search query")

        # 执行搜索
        return await engine.search(search_query)

    async def multi_search(
        self,
        query: str,
        engines: list[str | SearchType],
        merge_results: bool = True,
        **kwargs,
    ) -> list[SearchResponse] | SearchResponse:
        """
        多引擎搜索

        Args:
            query: 搜索查询
            engines: 引擎列表(名称或类型)
            merge_results: 是否合并结果
            **kwargs: 其他参数

        Returns:
            搜索结果列表或合并后的结果
        """
        tasks = []

        for engine_ref in engines:
            if isinstance(engine_ref, str):
                task = self.search(query, engine_name=engine_ref, **kwargs)
            else:
                task = self.search(query, search_type=engine_ref, **kwargs)
            tasks.append(task)

        # 并发执行搜索
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤异常结果
        valid_results = [r for r in results if isinstance(r, SearchResponse)]

        if merge_results and valid_results:
            # 合并结果
            merged = self._merge_results(valid_results)
            return merged

        return valid_results

    def _merge_results(self, results: list[SearchResponse]) -> SearchResponse:
        """合并多个搜索结果"""
        if not results:
            raise ValueError("No results to merge")

        # 使用第一个结果作为基础
        base = results[0]
        merged_results = list(base.results)
        total = base.total

        # 合并其他结果
        for response in results[1:]:
            merged_results.extend(response.results)
            total = max(total, response.total)  # 取最大值

        # 去重(基于URL或标题)
        seen = set()
        unique_results = []
        for result in merged_results:
            key = (result.title, result.url)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # 按相关性排序
        unique_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return SearchResponse(
            results=unique_results[: base.query.limit],  # 限制返回数量
            total=total,
            query=base.query,
            search_time=sum(r.search_time for r in results),
            engine=f"merged({', '.join(r.engine for r in results)})",
        )

    def get_available_engines(self) -> dict[str, dict]:
        """获取所有可用引擎的信息"""
        engines = {}

        # 获取已注册的引擎
        for name in SearchEngineFactory.get_available_engines():
            engines[name] = SearchEngineFactory.get_engine_info(name)

        # 添加已加载的实例
        for name, instance in self._engines.items():
            if name not in engines:
                engines[name] = {
                    "name": name,
                    "class": instance.__class__.__name__,
                    "available": instance.is_available(),
                    "loaded": True,
                }

        return engines


# 全局搜索管理器实例
_search_manager = None


def get_search_manager() -> UnifiedSearchManager:
    """获取全局搜索管理器实例"""
    global _search_manager
    if _search_manager is None:
        _search_manager = UnifiedSearchManager()
    return _search_manager


# 便捷函数
async def search(
    query: str,
    search_type: SearchType = SearchType.WEB,
    engine_name: str | None = None,
    **kwargs,
) -> SearchResponse:
    """便捷的搜索函数"""
    manager = get_search_manager()
    return await manager.search(query, search_type, engine_name, **kwargs)
