#!/usr/bin/env python3
"""
专利检索与下载集成验证测试
验证patent-search MCP和patent-downloader MCP的集成能力

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/integration_verify_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class IntegrationVerifier:
    """集成验证器"""

    def __init__(self):
        self.results = {
            'patent_search': {},
            'patent_downloader': {},
            'integration': {}
        }

    async def test_patent_search(self):
        """测试patent-search MCP"""
        logger.info("=" * 70)
        logger.info("验证1: patent-search MCP检索功能")
        logger.info("=" * 70)

        # 连接patent-search MCP服务器
        server_params = StdioServerParameters(
            command="node",
            args=["/Users/xujian/Athena工作平台/mcp-servers/patent-search-mcp-server/index.js"]
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # 测试1: 搜索中国专利
                    logger.info("\n测试1.1: 搜索中国专利")
                    result = await session.call_tool("search_cn_patents", {
                        "query": "人工智能",
                        "patent_type": "发明",
                        "limit": 5
                    })

                    patents = json.loads(result.content[0].text)
                    logger.info(f"✅ 检索到 {patents['total']} 条专利")

                    # 分析返回的元数据字段
                    if patents['apps/apps/patents']:
                        sample = patents['apps/apps/patents'][0]
                        logger.info("✅ 元数据字段示例:")
                        for key, value in sample.items():
                            if value:
                                logger.info(f"   - {key}: {str(value)[:50]}...")

                        self.results['patent_search']['fields'] = list(sample.keys())
                        self.results['patent_search']['sample'] = sample
                        self.results['patent_search']['status'] = 'success'

                    # 测试2: 根据申请号获取专利详情
                    if patents['apps/apps/patents']:
                        app_number = patents['apps/apps/patents'][0]['application_number']
                        logger.info(f"\n测试1.2: 根据申请号获取详情 {app_number}")

                        result = await session.call_tool("get_cn_patent_by_id", {
                            "application_number": app_number
                        })

                        detail = json.loads(result.content[0].text)
                        logger.info("✅ 获取专利详情成功")
                        logger.info(f"   专利名称: {detail.get('patent_name', 'N/A')}")
                        logger.info(f"   申请人: {detail.get('applicant', 'N/A')}")
                        logger.info(f"   IPC分类: {detail.get('ipc_main_class', 'N/A')}")

                        self.results['patent_search']['get_by_id'] = 'success'

        except Exception as e:
            logger.error(f"❌ patent-search MCP测试失败: {e}")
            self.results['patent_search']['status'] = 'failed'
            self.results['patent_search']['error'] = str(e)

    async def test_patent_downloader(self):
        """测试patent-downloader MCP"""
        logger.info("\n" + "=" * 70)
        logger.info("验证2: patent-downloader MCP下载功能")
        logger.info("=" * 70)

        # 连接patent-downloader MCP服务器
        server_params = StdioServerParameters(
            command="/usr/local/bin/uvx",
            args=[
                "--with", "mcp",
                "patent-downloader",
                "mcp-server"
            ],
            env={
                "OUTPUT_DIR": "/Users/xujian/apps/apps/patents/PDF/test"
            }
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # 测试1: 获取专利信息
                    test_patent = "CN112233445A"
                    logger.info(f"\n测试2.1: 获取专利信息 {test_patent}")

                    result = await session.call_tool("get_patent_info", {
                        "patent_number": test_patent
                    })

                    info = json.loads(result.content[0].text)
                    logger.info("✅ 获取专利信息成功")
                    logger.info(f"   标题: {info.get('title', 'N/A')[:60]}...")
                    logger.info(f"   申请人: {info.get('assignee', 'N/A')}")

                    self.results['patent_downloader']['get_info'] = 'success'
                    self.results['patent_downloader']['info_fields'] = list(info.keys())

                    # 测试2: 下载单个专利
                    logger.info(f"\n测试2.2: 下载专利PDF {test_patent}")

                    result = await session.call_tool("download_patent", {
                        "patent_number": test_patent,
                        "output_dir": "/Users/xujian/apps/apps/patents/PDF/test"
                    })

                    download_result = json.loads(result.content[0].text)
                    logger.info(f"{'✅' if download_result.get('success') else '❌'} 下载结果: {download_result.get('message', 'N/A')}")

                    if download_result.get('file_path'):
                        logger.info(f"   文件路径: {download_result['file_path']}")

                    self.results['patent_downloader']['download'] = 'success' if download_result.get('success') else 'failed'

                    # 分析输入参数要求
                    logger.info("\n测试2.3: 分析输入参数")
                    logger.info("✅ 专利下载所需输入:")
                    logger.info("   - patent_number (必需): 专利号")
                    logger.info("   - output_dir (可选): 输出目录")
                    logger.info("⚠️ 当前限制: 只接受专利号，不接受其他元数据")
                    logger.info("⚠️ 无法传递: PostgreSQL记录ID、申请人、发明人等上下文信息")

        except Exception as e:
            logger.error(f"❌ patent-downloader MCP测试失败: {e}")
            self.results['patent_downloader']['status'] = 'failed'
            self.results['patent_downloader']['error'] = str(e)

    async def test_integration(self):
        """测试集成能力"""
        logger.info("\n" + "=" * 70)
        logger.info("验证3: 检索与下载集成")
        logger.info("=" * 70)

        logger.info("\n当前集成流程:")
        logger.info("1. patent-search检索 → 返回专利列表 + 元数据")
        logger.info("2. 提取专利号列表")
        logger.info("3. 传递给patent-downloader → 只接受专利号")
        logger.info("4. 下载PDF")
        logger.info("5. ❌ 丢失了与PostgreSQL记录的关联")

        logger.info("\n⚠️ 集成问题:")
        logger.info("   - patent-downloader不接受PostgreSQL记录ID")
        logger.info("   - 下载的PDF无法自动关联到数据库记录")
        logger.info("   - 需要后处理步骤来重建关联关系")

        self.results['integration']['issues'] = [
            "patent-downloader只接受专利号",
            "无法传递上下文元数据",
            "PDF与数据库记录关联丢失"
        ]

        logger.info("\n💡 改进方案:")
        logger.info("   方案1: 扩展patent-downloader接受元数据")
        logger.info("   方案2: 创建中间层记录映射关系")
        logger.info("   方案3: 后处理脚本重建关联")

    async def run_all_tests(self):
        """运行所有验证测试"""
        logger.info("开始集成验证测试...")

        await self.test_patent_search()
        await self.test_patent_downloader()
        await self.test_integration()

        # 输出总结报告
        logger.info("\n" + "=" * 70)
        logger.info("验证测试总结")
        logger.info("=" * 70)

        logger.info("\n1. patent-search MCP:")
        if self.results['patent_search'].get('status') == 'success':
            logger.info("   ✅ 检索功能正常")
            if 'fields' in self.results['patent_search']:
                logger.info(f"   ✅ 返回 {len(self.results['patent_search']['fields'])} 个元数据字段")
        else:
            logger.info("   ❌ 检索功能异常")

        logger.info("\n2. patent-downloader MCP:")
        if self.results['patent_downloader'].get('download') == 'success':
            logger.info("   ✅ 下载功能正常")
        else:
            logger.info("   ❌ 下载功能异常")

        logger.info("\n3. 集成能力:")
        if 'issues' in self.results['integration']:
            logger.info("   ⚠️ 发现集成问题:")
            for issue in self.results['integration']['issues']:
                logger.info(f"      - {issue}")

        # 保存结果
        output_file = Path('/Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text/verification_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"\n📋 详细结果已保存至: {output_file}")


async def main():
    """主函数"""
    verifier = IntegrationVerifier()
    await verifier.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
