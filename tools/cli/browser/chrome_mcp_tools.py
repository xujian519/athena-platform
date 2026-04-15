#!/usr/bin/env python3
"""
Chrome MCP命令行工具
提供便捷的浏览器自动化操作命令
作者: 小娜 & 小诺
创建时间: 2025-12-04
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from automation.chrome_mcp_integration import get_chrome_mcp


async def navigate_command(url: str, headless: bool = False):
    """导航命令"""
    chrome = get_chrome_mcp()
    chrome.headless = headless

    try:
        await chrome.initialize()
        result = await chrome.navigate_to(url)

        if result['success']:
            logger.info("✅ 导航成功")
            logger.info(f"   URL: {result['url']}")
            logger.info(f"   标题: {result['title']}")
            logger.info(f"   加载时间: {result['load_time']:.2f}秒")
        else:
            logger.info(f"❌ 导航失败: {result.get('error')}")

    finally:
        await chrome.close()

async def extract_command(url: str, selectors_file: str = None, headless: bool = False):
    """内容提取命令"""
    chrome = get_chrome_mcp()
    chrome.headless = headless

    try:
        await chrome.initialize()

        # 先导航
        nav_result = await chrome.navigate_to(url)
        if not nav_result['success']:
            logger.info(f"❌ 导航失败: {nav_result.get('error')}")
            return

        # 加载选择器
        selectors = {}
        if selectors_file and Path(selectors_file).exists():
            with open(selectors_file, encoding='utf-8') as f:
                selectors = json.load(f)

        # 提取内容
        extract_result = await chrome.extract_content(selectors)

        if extract_result['success']:
            content = extract_result['content']
            logger.info("✅ 内容提取成功")
            logger.info(f"   页面标题: {content.get('page_title', '')}")
            logger.info(f"   页面URL: {content.get('page_url', '')}")

            # 显示提取的内容
            for key, value in content.items():
                if key not in ['page_title', 'page_url'] and value:
                    logger.info(f"   {key}: {len(value)} 项")
                    if isinstance(value, list) and len(value) > 0:
                        for i, item in enumerate(value[:3]):  # 只显示前3项
                            if isinstance(item, dict):
                                logger.info(f"     {i+1}. {item.get('text', str(item))}")
                            else:
                                logger.info(f"     {i+1}. {str(item)[:100]}")
                        if len(value) > 3:
                            logger.info(f"     ... 还有 {len(value) - 3} 项")
        else:
            logger.info(f"❌ 提取失败: {extract_result.get('error')}")

    finally:
        await chrome.close()

async def screenshot_command(url: str, filename: str = None, full_page: bool = True, headless: bool = False):
    """截图命令"""
    chrome = get_chrome_mcp()
    chrome.headless = headless

    try:
        await chrome.initialize()

        # 先导航
        nav_result = await chrome.navigate_to(url)
        if not nav_result['success']:
            logger.info(f"❌ 导航失败: {nav_result.get('error')}")
            return

        # 截图
        screenshot_result = await chrome.take_screenshot(filename, full_page)

        if screenshot_result['success']:
            logger.info("✅ 截图成功")
            logger.info(f"   文件名: {screenshot_result['filename']}")
            logger.info(f"   路径: {screenshot_result['path']}")
            logger.info(f"   全页截图: {screenshot_result['full_page']}")
        else:
            logger.info(f"❌ 截图失败: {screenshot_result.get('error')}")

    finally:
        await chrome.close()

async def search_patents_command(query: str, source: str = 'google_patents', headless: bool = False):
    """专利搜索命令"""
    chrome = get_chrome_mcp()
    chrome.headless = headless

    try:
        await chrome.initialize()

        # 搜索专利
        search_result = await chrome.search_patents(query, source)

        if search_result['success']:
            results = search_result['results']
            logger.info("✅ 专利搜索成功")
            logger.info(f"   查询: {search_result['query']}")
            logger.info(f"   数据源: {search_result['source']}")
            logger.info(f"   URL: {search_result['url']}")

            # 显示搜索结果摘要
            for key, items in results.items():
                if items and key != 'page_title' and key != 'page_url':
                    logger.info(f"   {key}: {len(items)} 项")
        else:
            logger.info("❌ 专利搜索失败")

    finally:
        await chrome.close()

async def script_command(url: str, script: str, headless: bool = False):
    """脚本执行命令"""
    chrome = get_chrome_mcp()
    chrome.headless = headless

    try:
        await chrome.initialize()

        # 先导航
        nav_result = await chrome.navigate_to(url)
        if not nav_result['success']:
            logger.info(f"❌ 导航失败: {nav_result.get('error')}")
            return

        # 执行脚本
        script_result = await chrome.execute_script(script)

        if script_result['success']:
            logger.info("✅ 脚本执行成功")
            logger.info(f"   结果: {script_result['result']}")
        else:
            logger.info(f"❌ 脚本执行失败: {script_result.get('error')}")

    finally:
        await chrome.close()

def create_sample_selectors():
    """创建示例选择器文件"""
    sample_selectors = {
        'title': 'title',
        'main_heading': 'h1',
        'sub_headings': 'h2',
        'content': 'main, article, .content',
        'links': 'a[href]',
        'buttons': "button, input[type='submit']",
        'forms': 'form',
        'images': 'img[src]'
    }

    with open('sample_selectors.json', 'w', encoding='utf-8') as f:
        json.dump(sample_selectors, f, indent=2, ensure_ascii=False)

    logger.info('✅ 示例选择器文件已创建: sample_selectors.json')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Chrome MCP命令行工具')
    parser.add_argument('--headless', action='store_true', help='无头模式运行')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 导航命令
    nav_parser = subparsers.add_parser('navigate', help='导航到指定URL')
    nav_parser.add_argument('url', help='目标URL')

    # 内容提取命令
    extract_parser = subparsers.add_parser('extract', help='提取页面内容')
    extract_parser.add_argument('url', help='目标URL')
    extract_parser.add_argument('--selectors', help='选择器JSON文件')

    # 截图命令
    screenshot_parser = subparsers.add_parser('screenshot', help='截取页面截图')
    screenshot_parser.add_argument('url', help='目标URL')
    screenshot_parser.add_argument('--filename', help='截图文件名')
    screenshot_parser.add_argument('--no-full-page', action='store_false', dest='full_page', help='不截取全页')

    # 专利搜索命令
    patent_parser = subparsers.add_parser('patent', help='搜索专利')
    patent_parser.add_argument('query', help='搜索查询')
    patent_parser.add_argument('--source', default='google_patents', help='数据源')

    # 脚本执行命令
    script_parser = subparsers.add_parser('script', help='执行JavaScript脚本')
    script_parser.add_argument('url', help='目标URL')
    script_parser.add_argument('--code', required=True, help='JavaScript代码')

    # 创建示例文件
    subparsers.add_parser('create-sample', help='创建示例选择器文件')

    args = parser.parse_args()

    if args.command == 'navigate':
        asyncio.run(navigate_command(args.url, args.headless))
    elif args.command == 'extract':
        asyncio.run(extract_command(args.url, args.selectors, args.headless))
    elif args.command == 'screenshot':
        asyncio.run(screenshot_command(args.url, args.filename, args.full_page, args.headless))
    elif args.command == 'patent':
        asyncio.run(search_patents_command(args.query, args.source, args.headless))
    elif args.command == 'script':
        asyncio.run(script_command(args.url, args.code, args.headless))
    elif args.command == 'create-sample':
        create_sample_selectors()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
