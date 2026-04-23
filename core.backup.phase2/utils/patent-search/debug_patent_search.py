#!/usr/bin/env python3
from __future__ import annotations
"""
调试专利搜索功能
Debug Patent Search
"""

import asyncio
import logging
import re

import aiohttp

logger = logging.getLogger(__name__)

async def debug_google_patents_search():
    """调试Google Patents搜索"""
    logger.info(str('=' * 80))
    logger.info('🔍 调试Google Patents搜索')
    logger.info(str('=' * 80))

    # 创建HTTP会话
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    )

    try:
        # 测试查询
        query = '人工智能'
        logger.info(f"🔍 测试查询: {query}")

        # 构建搜索URL
        search_url = 'https://patents.google.com/search'
        params = {
            'q': query,
            'oq': query,
            'page': 1
        }

        logger.info(f"📡 请求URL: {search_url}")
        logger.info(f"📡 请求参数: {params}")

        # 发送请求
        async with session.get(search_url, params=params) as response:
            logger.info(f"📊 响应状态码: {response.status}")
            logger.info(f"📊 响应头: {dict(response.headers)}")

            if response.status == 200:
                html = await response.text()
                logger.info(f"📄 HTML长度: {len(html)} 字符")

                # 查找专利号模式
                patent_patterns = [
                    r'patent/([A-Z]{2}\d+[A-Z]?\d*)',
                    r"publication-number='([^']+)'",
                    r"'publication_number':'([^']+)'",
                    r"data-result='([^']*patent[^']*)'",
                    r"href='/patent/([^']+)'",
                ]

                all_patent_numbers = []

                for i, pattern in enumerate(patent_patterns, 1):
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    logger.info(f"\n🔍 模式 {i}: {pattern}")
                    logger.info(f"   找到 {len(matches)} 个匹配")
                    if matches:
                        logger.info(f"   示例: {matches[:5]}")
                        all_patent_numbers.extend(matches)

                # 去重
                unique_patents = list({p for p in all_patent_numbers if p and len(p) > 3})
                logger.info(f"\n📋 总计找到 {len(unique_patents)} 个唯一专利号:")
                for patent in unique_patents[:10]:
                    logger.info(f"   - {patent}")

                # 检查HTML内容
                logger.info("\n📄 HTML内容检查:")
                logger.info(f"   是否包含'patent': {'patent' in html.lower()}")
                logger.info(f"   是否包含'results': {'results' in html.lower()}")
                logger.info(f"   是否包含'search-result': {'search-result' in html.lower()}")

                # 保存HTML用于调试
                with open('debug_google_patents.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info("\n💾 HTML已保存到 debug_google_patents.html")

            else:
                logger.info(f"❌ 请求失败，状态码: {response.status}")
                error_text = await response.text()
                logger.info(f"❌ 错误信息: {error_text[:500]}")

    except Exception as e:
        logger.info(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await session.close()

async def test_jina_ai_extraction():
    """测试Jina AI内容提取"""
    logger.info(str("\n" + '=' * 80))
    logger.info('🤖 测试Jina AI内容提取')
    logger.info(str('=' * 80))

    # Google Patents搜索URL
    query = '人工智能'
    google_url = f"https://patents.google.com/search?q={query}"

    # Jina AI提取URL
    jina_url = f"https://r.jina.ai/http://{google_url.replace('https://', '')}"

    logger.info(f"📡 Jina AI URL: {jina_url}")

    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

    try:
        async with session.get(jina_url) as response:
            logger.info(f"📊 Jina AI响应状态: {response.status}")

            if response.status == 200:
                content = await response.text()
                logger.info(f"📄 Jina AI提取内容长度: {len(content)} 字符")

                # 查找专利号
                patent_pattern = r'([A-Z]{2}\d+[A-Z]?\d*)'
                matches = re.findall(patent_pattern, content)
                logger.info(f"🔍 从Jina AI内容中找到 {len(matches)} 个专利号:")
                for match in matches[:10]:
                    logger.info(f"   - {match}")

                # 保存Jina AI内容
                with open('debug_jina_ai_content.txt', 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info("💾 Jina AI内容已保存到 debug_jina_ai_content.txt")
            else:
                logger.info(f"❌ Jina AI请求失败，状态码: {response.status}")

    except Exception as e:
        logger.info(f"❌ Jina AI测试失败: {e}")

    finally:
        await session.close()

async def main():
    """主函数"""
    logger.info('🚀 开始调试专利搜索功能')

    # 调试Google Patents直接搜索
    await debug_google_patents_search()

    # 测试Jina AI提取
    await test_jina_ai_extraction()

    logger.info("\n🎉 调试完成")

if __name__ == '__main__':
    asyncio.run(main())
