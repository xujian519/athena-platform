#!/usr/bin/env python3
"""
学术搜索Handler测试
Academic Search Handler Tests

测试学术搜索工具的完整功能

作者: Athena平台团队
版本: v1.0.0
创建: 2026-04-19
"""

import pytest

from core.tools.handlers.academic_search_handler import (
    academic_search_handler,
    search_papers,
    _extract_year,
    _title_similarity
)


@pytest.mark.asyncio
async def test_academic_search_basic():
    """测试基本搜索功能（Semantic Scholar）"""
    result = await academic_search_handler(
        query="artificial intelligence",
        source="semantic_scholar",
        limit=5
    )

    assert result["success"] == True
    assert "results" in result
    assert len(result["results"]) > 0
    assert result["source"] == "semantic_scholar"

    # 验证结果结构
    paper = result["results"][0]
    assert "title" in paper
    assert "authors" in paper
    assert "url" in paper


@pytest.mark.asyncio
async def test_academic_search_with_year():
    """测试带年份过滤的搜索"""
    result = await academic_search_handler(
        query="machine learning",
        source="semantic_scholar",
        year="2024",
        limit=10
    )

    assert result["success"] == True
    # 验证结果年份（如果有）
    for paper in result["results"]:
        if paper.get("year"):
            assert paper["year"] == 2024


@pytest.mark.asyncio
async def test_academic_search_empty_query():
    """测试空查询处理"""
    result = await academic_search_handler(
        query="",
        limit=10
    )

    assert result["success"] == False
    assert "error" in result


@pytest.mark.asyncio
async def test_academic_search_limit_validation():
    """测试limit参数验证"""
    # 测试超出范围
    result = await academic_search_handler(
        query="deep learning",
        limit=200  # 超过最大值100
    )

    # 应该自动限制到100
    assert result["success"] == True


@pytest.mark.asyncio
async def test_academic_search_auto_source():
    """测试自动选择数据源"""
    result = await academic_search_handler(
        query="neural networks",
        source="auto",
        limit=5
    )

    # 默认应该使用Semantic Scholar
    assert result["success"] == True
    assert result["source"] == "semantic_scholar"


@pytest.mark.asyncio
@pytest.mark.skipif(
    True,  # 需要配置SERPER_API_KEY才能运行
    reason="需要SERPER_API_KEY环境变量"
)
async def test_academic_search_google_scholar():
    """测试Google Scholar搜索（需要API密钥）"""
    result = await academic_search_handler(
        query="patent law",
        source="google_scholar",
        limit=5
    )

    assert result["success"] == True
    assert result["source"] == "google_scholar"


@pytest.mark.asyncio
async def test_search_papers_convenience_function():
    """测试便捷函数"""
    result = await search_papers(
        query="computer vision",
        limit=5
    )

    assert result["success"] == True
    assert "results" in result


def test_extract_year():
    """测试年份提取函数"""
    # 测试正常年份
    assert _extract_year("Nature 2024") == 2024
    assert _extract_year("Science, 2023, pp.123-145") == 2023

    # 测试无年份
    assert _extract_year("Journal of AI") is None

    # 测试多个年份（取第一个）
    assert _extract_year("2020-2024") == 2020


def test_title_similarity():
    """测试标题相似度函数"""
    # 完全相同
    assert _title_similarity("Test Title", "Test Title") == 1.0

    # 包含关系
    assert _title_similarity("Test Title", "Test Title Extended") >= 0.9

    # 部分相似
    similarity = _title_similarity("Machine Learning", "Machine Learning Algorithms")
    assert similarity > 0.5

    # 完全不同
    assert _title_similarity("AI", "Blockchain") < 0.5


@pytest.mark.asyncio
async def test_academic_search_result_structure():
    """测试返回结果的结构完整性"""
    result = await academic_search_handler(
        query="quantum computing",
        limit=3
    )

    if result["success"]:
        # 验证顶层结构
        assert "query" in result
        assert "source" in result
        assert "total_results" in result
        assert "timestamp" in result

        # 验证论文结构
        for paper in result["results"]:
            assert "index" in paper
            assert "title" in paper
            assert "authors" in paper
            assert "url" in paper
            assert isinstance(paper["authors"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_academic_search_real_query():
    """集成测试：真实查询"""
    result = await academic_search_handler(
        query="patent analytics machine learning",
        limit=10
    )

    assert result["success"] == True
    assert len(result["results"]) > 0

    # 验证结果质量
    paper = result["results"][0]
    assert len(paper["title"]) > 0
    assert len(paper["authors"]) >= 0
    assert paper["url"] or paper["abstract"]  # 至少有链接或摘要


@pytest.mark.asyncio
async def test_academic_search_error_handling():
    """测试错误处理"""
    # 测试无效数据源
    result = await academic_search_handler(
        query="test",
        source="invalid_source"
    )

    # 应该降级到默认数据源
    assert result["success"] == True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
