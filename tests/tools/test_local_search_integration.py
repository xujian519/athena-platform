#!/usr/bin/env python3
"""
本地搜索引擎集成测试

测试web_search工具使用本地搜索引擎（SearXNG + Firecrawl）
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio

from core.tools.real_tool_implementations import real_web_search_handler


class TestLocalSearchIntegration:
    """本地搜索引擎集成测试"""

    @pytest.mark.asyncio
    async def test_basic_search(self):
        """测试基本搜索功能"""
        params = {
            "query": "Python编程",
            "limit": 5
        }

        result = await real_web_search_handler(params)

        assert result["engine"] == "local-search-engine"
        assert result["engine_type"] == "SearXNG + Firecrawl"
        assert result["query"] == "Python编程"
        assert isinstance(result["total"], int)
        assert isinstance(result["results"], list)
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_search_with_results(self):
        """测试有结果的搜索"""
        params = {
            "query": "人工智能",
            "limit": 10
        }

        result = await real_web_search_handler(params)

        # 检查返回结构
        assert "query" in result
        assert "total" in result
        assert "results" in result
        assert "engine" in result

        # 检查结果格式
        if result["total"] > 0:
            first_result = result["results"][0]
            assert "title" in first_result
            assert "url" in first_result
            assert "snippet" in first_result

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """测试空查询（应该抛出异常）"""
        params = {
            "query": "",
            "limit": 5
        }

        with pytest.raises(ValueError, match="缺少必需参数"):
            await real_web_search_handler(params)

    @pytest.mark.asyncio
    async def test_search_missing_query(self):
        """测试缺少query参数（应该抛出异常）"""
        params = {
            "limit": 5
        }

        with pytest.raises(ValueError, match="缺少必需参数"):
            await real_web_search_handler(params)

    @pytest.mark.asyncio
    async def test_search_custom_limit(self):
        """测试自定义结果数量"""
        params = {
            "query": "机器学习",
            "limit": 3
        }

        result = await real_web_search_handler(params)

        # 结果数量不应超过limit
        assert result["total"] <= 3

    @pytest.mark.asyncio
    async def test_engine_info(self):
        """测试引擎信息"""
        params = {
            "query": "测试",
            "limit": 5
        }

        result = await real_web_search_handler(params)

        # 验证使用的是本地搜索引擎
        assert result["engine"] == "local-search-engine"
        assert result["engine_type"] == "SearXNG + Firecrawl"


class TestLocalSearchEngine:
    """本地搜索引擎类测试"""

    @pytest.mark.asyncio
    async def test_search_engine_singleton(self):
        """测试搜索引擎单例"""
        from core.tools.real_tool_implementations import _get_search_engine, LocalSearchEngine

        engine1 = await _get_search_engine()
        engine2 = await _get_search_engine()

        # 应该返回同一个实例
        assert engine1 is engine2
        assert isinstance(engine1, LocalSearchEngine)

    @pytest.mark.asyncio
    async def test_search_engine_base_url(self):
        """测试搜索引擎基础URL"""
        from core.tools.real_tool_implementations import _get_search_engine

        engine = await _get_search_engine()

        assert engine.base_url == "http://localhost:3003"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
