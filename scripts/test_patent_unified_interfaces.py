#!/usr/bin/env python3
"""
专利检索和下载接口测试脚本

测试统一接口的可用性：
1. 本地PostgreSQL检索
2. Google Patents检索
3. 双渠道检索
4. 专利下载
5. 错误处理

Author: Athena平台团队
Created: 2026-04-19
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tools.patent_retrieval import (
    UnifiedPatentRetriever,
    PatentRetrievalChannel,
    search_local_patents,
    search_google_patents,
    search_patents,
)
from core.tools.patent_download import (
    UnifiedPatentDownloader,
    download_patent,
    download_patents,
)


class PatentToolsTester:
    """专利工具测试器"""

    def __init__(self):
        self.test_results = []
        self.retriever = None
        self.downloader = None

    def log_test(self, test_name: str, success: bool, message: str, details: Dict = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        self.test_results.append(result)

        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        print(f"   {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        print()

    async def test_local_retriever_initialization(self):
        """测试1: 本地检索器初始化"""
        print("=" * 80)
        print("测试1: 本地PostgreSQL检索器初始化")
        print("=" * 80)
        print()

        try:
            retriever = UnifiedPatentRetriever()
            retriever._get_local_retriever()

            self.retriever = retriever

            self.log_test(
                "本地检索器初始化",
                True,
                "本地PostgreSQL检索器初始化成功",
                {
                    "retriever_type": "RealPatentHybridRetrieval",
                    "status": "ready"
                }
            )
        except Exception as e:
            self.log_test(
                "本地检索器初始化",
                False,
                f"本地PostgreSQL检索器初始化失败: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_google_retriever_initialization(self):
        """测试2: Google检索器初始化"""
        print("=" * 80)
        print("测试2: Google Patents检索器初始化")
        print("=" * 80)
        print()

        try:
            retriever = UnifiedPatentRetriever()
            retriever._get_google_retriever()

            self.retriever = retriever

            self.log_test(
                "Google检索器初始化",
                True,
                "Google Patents检索器初始化成功",
                {
                    "retriever_type": "GooglePatentsRetriever",
                    "status": "ready"
                }
            )
        except Exception as e:
            self.log_test(
                "Google检索器初始化",
                False,
                f"Google Patents检索器初始化失败: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_local_search(self):
        """测试3: 本地PostgreSQL检索"""
        print("=" * 80)
        print("测试3: 本地PostgreSQL检索功能")
        print("=" * 80)
        print()

        try:
            print("  🔍 检索查询: '深度学习'")
            print()

            results = await search_local_patents(
                query="深度学习",
                max_results=5
            )

            if results:
                self.log_test(
                    "本地PostgreSQL检索",
                    True,
                    f"成功检索到 {len(results)} 个结果",
                    {
                        "query": "深度学习",
                        "result_count": len(results),
                        "first_result": results[0] if results else None
                    }
                )

                # 显示前3个结果
                print("  📋 检索结果（前3个）:")
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. {result.get('patent_id', 'N/A')}")
                    print(f"       标题: {result.get('title', 'N/A')[:60]}...")
                    print(f"       来源: {result.get('source', 'N/A')}")
                    print()
            else:
                self.log_test(
                    "本地PostgreSQL检索",
                    False,
                    "检索返回空结果",
                    {"query": "深度学习", "result_count": 0}
                )

        except Exception as e:
            self.log_test(
                "本地PostgreSQL检索",
                False,
                f"检索失败: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_google_search(self):
        """测试4: Google Patents检索"""
        print("=" * 80)
        print("测试4: Google Patents检索功能")
        print("=" * 80)
        print()

        try:
            print("  🔍 检索查询: 'machine learning'")
            print()

            results = await search_google_patents(
                query="machine learning",
                max_results=5
            )

            if results:
                self.log_test(
                    "Google Patents检索",
                    True,
                    f"成功检索到 {len(results)} 个结果",
                    {
                        "query": "machine learning",
                        "result_count": len(results),
                        "first_result": results[0] if results else None
                    }
                )

                # 显示前3个结果
                print("  📋 检索结果（前3个）:")
                for i, result in enumerate(results[:3], 1):
                    print(f"    {i}. {result.get('patent_id', 'N/A')}")
                    print(f"       标题: {result.get('title', 'N/A')[:60]}...")
                    print(f"       来源: {result.get('source', 'N/A')}")
                    if result.get('url'):
                        print(f"       链接: {result.get('url', 'N/A')}")
                    print()
            else:
                self.log_test(
                    "Google Patents检索",
                    False,
                    "检索返回空结果",
                    {"query": "machine learning", "result_count": 0}
                )

        except Exception as e:
            self.log_test(
                "Google Patents检索",
                False,
                f"检索失败: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_dual_channel_search(self):
        """测试5: 双渠道并发检索"""
        print("=" * 80)
        print("测试5: 双渠道并发检索功能")
        print("=" * 80)
        print()

        try:
            print("  🔍 检索查询: 'artificial intelligence'")
            print("  🔄 使用双渠道并发检索")
            print()

            results = await search_patents(
                query="artificial intelligence",
                channel="both",
                max_results=10
            )

            if results:
                local_count = sum(1 for r in results if r.get('source') == 'local_postgres')
                google_count = sum(1 for r in results if r.get('source') == 'google_patents')

                self.log_test(
                    "双渠道并发检索",
                    True,
                    f"成功检索到 {len(results)} 个结果",
                    {
                        "query": "artificial intelligence",
                        "total_results": len(results),
                        "local_results": local_count,
                        "google_results": google_count
                    }
                )

                print("  📊 结果分布:")
                print(f"     本地数据库: {local_count} 个")
                print(f"     Google Patents: {google_count} 个")
                print(f"     总计: {len(results)} 个")
                print()
            else:
                self.log_test(
                    "双渠道并发检索",
                    False,
                    "检索返回空结果",
                    {"query": "artificial intelligence", "result_count": 0}
                )

        except Exception as e:
            self.log_test(
                "双渠道并发检索",
                False,
                f"检索失败: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_downloader_initialization(self):
        """测试6: 下载器初始化"""
        print("=" * 80)
        print("测试6: 专利下载器初始化")
        print("=" * 80)
        print()

        try:
            downloader = UnifiedPatentDownloader()
            downloader._get_downloader()

            self.downloader = downloader

            self.log_test(
                "专利下载器初始化",
                True,
                "Google Patents下载器初始化成功",
                {
                    "downloader_type": "GooglePatentsDownloader",
                    "status": "ready"
                }
            )
        except Exception as e:
            self.log_test(
                "专利下载器初始化",
                False,
                f"Google Patents下载器初始化失败: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_single_download(self):
        """测试7: 单个专利下载"""
        print("=" * 80)
        print("测试7: 单个专利下载功能")
        print("=" * 80)
        print()

        try:
            test_patent = "US1234567B2"
            output_dir = "/tmp/patent_test"

            print(f"  📥 下载专利: {test_patent}")
            print(f"  📁 输出目录: {output_dir}")
            print()

            result = await download_patent(
                patent_number=test_patent,
                output_dir=output_dir
            )

            if result.get("success"):
                self.log_test(
                    "单个专利下载",
                    True,
                    f"成功下载专利: {test_patent}",
                    {
                        "patent_number": test_patent,
                        "file_path": result.get("file_path"),
                        "file_size_mb": result.get("file_size_mb"),
                        "download_time": result.get("download_time")
                    }
                )
            else:
                self.log_test(
                    "单个专利下载",
                    False,
                    f"下载失败: {result.get('error')}",
                    {
                        "patent_number": test_patent,
                        "error": result.get("error")
                    }
                )

        except Exception as e:
            self.log_test(
                "单个专利下载",
                False,
                f"下载异常: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_batch_download(self):
        """测试8: 批量专利下载"""
        print("=" * 80)
        print("测试8: 批量专利下载功能")
        print("=" * 80)
        print()

        try:
            test_patents = ["US1234567B2", "US7654321B2"]
            output_dir = "/tmp/patent_batch_test"

            print(f"  📥 批量下载: {len(test_patents)} 个专利")
            print(f"  📁 输出目录: {output_dir}")
            print()

            results = await download_patents(
                patent_numbers=test_patents,
                output_dir=output_dir
            )

            successful = sum(1 for r in results if r.get("success"))
            failed = len(results) - successful

            self.log_test(
                "批量专利下载",
                True,
                f"批量下载完成: {successful} 成功, {failed} 失败",
                {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results
                }
            )

            print("  📊 下载统计:")
            for result in results:
                status = "✅" if result.get("success") else "❌"
                patent = result.get("patent_number", "N/A")
                print(f"     {status} {patent}")
                if result.get("success"):
                    print(f"        文件: {result.get('file_path')}")
                    print(f"        大小: {result.get('file_size_mb')} MB")
                else:
                    print(f"        错误: {result.get('error')}")
                print()

        except Exception as e:
            self.log_test(
                "批量专利下载",
                False,
                f"批量下载异常: {e}",
                {"error": str(e), "traceback": traceback.format_exc()}
            )

    async def test_error_handling(self):
        """测试9: 错误处理"""
        print("=" * 80)
        print("测试9: 错误处理机制")
        print("=" * 80)
        print()

        # 测试1: 缺少必需参数
        print("  测试9.1: 缺少query参数")
        try:
            retriever = UnifiedPatentRetriever()
            await retriever.search(
                query="",  # 空查询
                max_results=10
            )
            self.log_test(
                "错误处理-空查询",
                False,
                "应该拒绝空查询但未拒绝",
                {}
            )
        except Exception as e:
            self.log_test(
                "错误处理-空查询",
                True,
                "正确拒绝空查询",
                {"error": str(e)}
            )

        # 测试2: 无效的检索渠道
        print("  测试9.2: 无效的检索渠道")
        try:
            results = await search_patents(
                query="test",
                channel="invalid_channel",  # 无效渠道
                max_results=10
            )
            self.log_test(
                "错误处理-无效渠道",
                False,
                "应该拒绝无效渠道但未拒绝",
                {}
            )
        except (ValueError, KeyError) as e:
            self.log_test(
                "错误处理-无效渠道",
                True,
                "正确拒绝无效渠道",
                {"error": str(e)}
            )

    def generate_test_report(self):
        """生成测试报告"""
        print("=" * 80)
        print("📊 测试报告总结")
        print("=" * 80)
        print()

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {(passed_tests/total_tests*100):.1f}%")
        print()

        # 详细结果
        print("详细测试结果:")
        print("-" * 80)
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"{i}. {status} {result['test_name']}")
            print(f"   {result['message']}")
            if result.get("details"):
                for key, value in result["details"].items():
                    if key != "traceback":  # 不显示完整的traceback
                        print(f"   {key}: {value}")
            print()

        # 失败的测试
        if failed_tests > 0:
            print("失败的测试:")
            print("-" * 80)
            for result in self.test_results:
                if not result["success"]:
                    print(f"❌ {result['test_name']}")
                    print(f"   {result['message']}")
                    if result["details"].get("traceback"):
                        print(f"   错误详情:")
                        traceback_lines = result["details"]["traceback"].split('\n')
                        for line in traceback_lines[-5:]:  # 只显示最后5行
                            print(f"   {line}")
                    print()

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n")
        print("╔════════════════════════════════════════════════════════════════════════╗")
        print("║                                                                        ║")
        print("║           专利检索和下载接口测试套件                                ║")
        print("║                                                                        ║")
        print("╚════════════════════════════════════════════════════════════════════════╝")
        print("")

        # 运行测试
        await self.test_local_retriever_initialization()
        await self.test_google_retriever_initialization()
        await self.test_local_search()
        await self.test_google_search()
        await self.test_dual_channel_search()
        await self.test_downloader_initialization()
        await self.test_single_download()
        await self.test_batch_download()
        await self.test_error_handling()

        # 生成报告
        self.generate_test_report()

        print("=" * 80)
        print("✅ 测试完成")
        print("=" * 80)


async def main():
    """主函数"""
    tester = PatentToolsTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
