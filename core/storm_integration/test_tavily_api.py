#!/usr/bin/env python3
"""
测试 Tavily API Key

验证 Tavily API Key 是否正常工作

作者: Athena 平台团队
创建时间: 2026-01-03
"""

import asyncio
import json
import logging

import aiohttp

# Tavily API Key
TAVILY_API_KEY = "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"


async def test_tavily_api():
    """测试 Tavily API"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    logger.info("=" * 70)
    logger.info("Tavily API 测试")
    logger.info("=" * 70)
    logger.info(f"API Key: {TAVILY_API_KEY[:20]}...")

    url = "https://api.tavily.com/search"

    test_queries = [
        "深度学习在专利检索中的应用",
        "专利创造性判断标准",
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"测试查询 {i}: {query}")
        logger.info(f"{'='*70}")

        params = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "include_raw_content": False,
            "max_results": 5,
        }

        try:
            # 忽略 SSL 验证
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30), connector=connector
            ) as session, session.post(url, json=params) as response:
                logger.info(f"HTTP 状态码: {response.status}")

                if response.status == 200:
                    data = await response.json()

                    logger.info("✅ 请求成功!")
                    logger.info(f"响应键: {list(data.keys())}")

                    # 检查 answer
                    if "answer" in data:
                        logger.info(f"\n_ai Answer:\n{data['answer']}\n")

                    # 检查 results
                    if "results" in data:
                        results = data["results"]
                        logger.info(f"找到 {len(results)} 条搜索结果:")

                        for j, result in enumerate(results, 1):
                            title = result.get("title", "N/A")
                            url = result.get("url", "N/A")
                            content = result.get("content", "")[:150]

                            logger.info(f"\n{j}. {title}")
                            logger.info(f"   URL: {url}")
                            logger.info(f"   内容: {content}...")
                    else:
                        logger.warning("⚠️ 响应中没有 'results' 字段")
                        logger.info(
                            f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}"
                        )
                else:
                    error_text = await response.text()
                    logger.error(f"❌ API 错误: {error_text}")

        except Exception as e:
            logger.error(f"❌ 请求异常: {e}")
            import traceback

            traceback.print_exc()

    logger.info(f"\n{'='*70}")
    logger.info("测试完成!")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(test_tavily_api())
