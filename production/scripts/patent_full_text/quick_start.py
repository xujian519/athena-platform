#!/usr/bin/env python3
"""
专利下载快速开始示例
演示如何使用IntegratedPatentDownloader下载专利PDF

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from integrated_downloader import IntegratedPatentDownloader


def example1_manual_input() -> Any:
    """示例1: 手动输入专利号下载"""
    print("=" * 70)
    print("示例1: 手动输入专利号下载")
    print("=" * 70)

    # 准备专利号列表
    patent_numbers = [
        "CN112233445A",  # 中国专利
        "US8460931B2",   # 美国专利
    ]

    print(f"\n📋 待下载专利 ({len(patent_numbers)}个):")
    for i, pn in enumerate(patent_numbers, 1):
        print(f"   {i}. {pn}")

    # 创建下载器
    downloader = IntegratedPatentDownloader()

    # 创建下载请求
    requests = downloader.create_requests_from_patent_numbers(
        patent_numbers,
        metadata={
            "source": "manual_input",
            "case_id": "DEMO-001"
        }
    )

    # 批量下载
    print("\n🔄 开始下载...")
    results = downloader.download_batch(requests)

    # 输出结果
    print("\n📊 下载结果:")
    for request, result in zip(requests, results, strict=False):
        status = "✅" if result.success else "❌"
        print(f"{status} {request.patent_number}")
        if result.success:
            print(f"   文件: {result.file_path}")
            print(f"   大小: {result.file_size:,} bytes")

    return results


def example2_from_patent_search() -> Any:
    """示例2: 从patent-search结果下载"""
    print("\n" + "=" * 70)
    print("示例2: 从patent-search结果下载")
    print("=" * 70)

    # 模拟patent-search返回的结果
    # 实际使用时应该调用真实的patent-search MCP
    patent_search_results = [
        {
            "id": "demo-uuid-001",
            "patent_name": "一种基于人工智能的图像识别方法",
            "application_number": "CN202110001234",
            "publication_number": "CN112233445A",
            "patent_type": "发明",
            "applicant": "北京某某科技有限公司",
            "inventor": "张三;李四",
            "ipc_main_class": "G06F",
            "abstract": "本发明公开了一种图像识别方法..."
        }
    ]

    print(f"\n📋 patent-search检索结果 ({len(patent_search_results)}条):")
    for i, p in enumerate(patent_search_results, 1):
        print(f"   {i}. {p['publication_number']} - {p['patent_name']}")
        print(f"      PostgreSQL ID: {p['id']}")

    # 创建下载器
    downloader = IntegratedPatentDownloader()

    # 创建下载请求（自动包含完整元数据）
    requests = downloader.create_requests_from_patent_search(patent_search_results)

    # 批量下载
    print("\n🔄 开始下载...")
    results = downloader.download_batch(requests)

    # 输出结果
    print("\n📊 下载结果:")
    for request, result in zip(requests, results, strict=False):
        status = "✅" if result.success else "❌"
        print(f"{status} {request.patent_number}")
        if result.success:
            print(f"   文件: {result.file_path}")
            print(f"   PostgreSQL ID: {request.postgres_id}")

            # 模拟更新数据库
            print("\n💡 可以更新PostgreSQL:")
            print("   UPDATE patents SET")
            print(f"       pdf_path = '{result.file_path}',")
            print(f"       pdf_source = '{request.source}',")
            print("       pdf_downloaded_at = NOW(),")
            print("       full_text_processed = FALSE")
            print(f"   WHERE id = '{request.postgres_id}';")

    return results


def example3_query_mapping() -> Any:
    """示例3: 查询下载映射记录"""
    print("\n" + "=" * 70)
    print("示例3: 查询下载映射记录")
    print("=" * 70)

    downloader = IntegratedPatentDownloader()

    # 查询所有下载记录
    print("\n📋 下载映射记录:")
    print(f"映射文件: {downloader.tracker.mapping_file}")

    if downloader.tracker.mapping:
        print(f"总记录数: {len(downloader.tracker.mapping)}")
        for i, (_key, record) in enumerate(list(downloader.tracker.mapping.items())[:5], 1):
            print(f"\n[{i}] {record['patent_number']}")
            print(f"   文件: {record.get('file_path', 'N/A')}")
            file_size = record.get('file_size')
            if file_size:
                print(f"   大小: {file_size:,} bytes")
            else:
                print("   大小: N/A")
            print(f"   时间: {record.get('downloaded_at', 'N/A')}")
            print(f"   状态: {'成功' if record.get('success') else '失败'}")

        if len(downloader.tracker.mapping) > 5:
            print(f"\n... 还有 {len(downloader.tracker.mapping) - 5} 条记录")
    else:
        print("暂无下载记录")


def main() -> None:
    """主函数"""
    print("\n🚀 专利下载快速开始示例")
    print("=" * 70)

    # 示例1: 手动输入
    example1_manual_input()

    # 示例2: patent-search
    # example2_from_patent_search()  # 取消注释以启用

    # 示例3: 查询映射
    example3_query_mapping()

    print("\n" + "=" * 70)
    print("✅ 示例演示完成！")
    print("=" * 70)

    print("\n💡 提示:")
    print("   1. 查看 FINAL_ARCHITECTURE.md 了解完整架构")
    print("   2. 查看 PHASE1_COMPLETION_REPORT.md 了解系统状态")
    print("   3. 查看 integrated_downloader.py 了解API详情")


if __name__ == "__main__":
    main()
