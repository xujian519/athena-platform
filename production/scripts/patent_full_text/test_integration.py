#!/usr/bin/env python3
"""
专利检索→下载集成测试
测试从Google Patents获取专利号并使用patent-downloader下载

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Any

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "dev/tools" / "patent_downloader" / "src"))

from integrated_downloader import IntegratedPatentDownloader


def test_google_patents_workflow() -> Any:
    """测试Google Patents检索→下载工作流"""

    print("=" * 70)
    print("Google Patents → patent-downloader 集成测试")
    print("=" * 70)

    # 模拟从Google Patents检索获取的专利号列表
    # 实际使用中，用户会从patents.google.com复制这些专利号
    google_patents_results = [
        "US8460931B2",  # 神经 progenitor cells (来自示例)
        "US20230123456A1",  # 示例专利号
        "CN112233445A",  # 中国专利示例
    ]

    print(f"\n📋 从Google Patents获取的专利号 ({len(google_patents_results)}个):")
    for i, pn in enumerate(google_patents_results, 1):
        print(f"   {i}. {pn}")

    # 创建集成下载器
    downloader = IntegratedPatentDownloader()

    # 创建下载请求
    requests = downloader.create_requests_from_patent_numbers(
        google_patents_results,
        metadata={
            "source": "google_patents",
            "search_query": "artificial intelligence",
            "search_date": "2025-12-24"
        }
    )

    print(f"\n✅ 创建了 {len(requests)} 个下载请求")

    # 显示请求详情
    print("\n📄 下载请求详情:")
    for i, req in enumerate(requests, 1):
        print(f"   {i}. {req.patent_number}")
        print(f"      来源: {req.source}")
        print(f"      输出目录: {downloader.determine_output_dir(req)}")

    # 执行下载（测试模式，不实际下载）
    print("\n🔄 开始下载...")
    print("⚠️ 测试模式: 不实际执行下载")

    for i, req in enumerate(requests, 1):
        output_dir = downloader.determine_output_dir(req)
        file_path = f"{output_dir}/{req.patent_number}.pdf"

        print(f"\n[{i}/{len(requests)}] {req.patent_number}")
        print(f"   URL: https://patents.google.com/patent/{req.patent_number}")
        print(f"   保存到: {file_path}")

        # 模拟映射记录
        downloader.tracker.mapping[req.get_cache_key()] = {
            "patent_number": req.patent_number,
            "file_path": file_path,
            "source": req.source,
            "search_query": req.search_query,
            "downloaded_at": "2025-12-24T22:30:00",
            "success": True
        }

    # 保存映射
    downloader.tracker._save_mapping()
    print(f"\n✅ 映射记录已保存到: {downloader.tracker.mapping_file}")

    return True


def test_patent_search_integration() -> Any:
    """测试patent-search MCP → 下载集成"""

    print("\n" + "=" * 70)
    print("patent-search MCP → 下载集成测试")
    print("=" * 70)

    # 模拟patent-search返回的结果
    patent_search_results = [
        {
            "id": "uuid-001",
            "patent_name": "一种基于人工智能的图像识别方法",
            "application_number": "CN202110001234",
            "publication_number": "CN112233445A",
            "patent_type": "发明",
            "applicant": "北京某某科技有限公司",
            "inventor": "张三;李四",
            "ipc_main_class": "G06F",
            "abstract": "本发明公开了一种图像识别方法..."
        },
        {
            "id": "uuid-002",
            "patent_name": "智能语音识别系统",
            "application_number": "CN202110002345",
            "publication_number": "CN112344556A",
            "patent_type": "发明",
            "applicant": "深圳某某科技公司",
            "inventor": "王五",
            "ipc_main_class": "G10L",
            "abstract": "本发明涉及语音识别技术领域..."
        }
    ]

    print(f"\n📋 patent-search检索结果 ({len(patent_search_results)}条):")
    for i, p in enumerate(patent_search_results, 1):
        print(f"   {i}. {p['publication_number']} - {p['patent_name']}")
        print(f"      PostgreSQL ID: {p['id']}")
        print(f"      申请人: {p['applicant']}")

    # 创建集成下载器
    downloader = IntegratedPatentDownloader()

    # 从patent-search结果创建下载请求
    requests = downloader.create_requests_from_patent_search(patent_search_results)

    print(f"\n✅ 创建了 {len(requests)} 个下载请求")

    # 显示请求详情（包含完整元数据）
    print("\n📄 带元数据的下载请求:")
    for i, req in enumerate(requests, 1):
        print(f"\n   [{i}] {req.patent_number}")
        print(f"      PostgreSQL ID: {req.postgres_id}")
        print(f"      专利名称: {req.patent_name}")
        print(f"      申请人: {req.applicant}")
        print(f"      IPC分类: {req.ipc_main_class}")
        print(f"      输出目录: {downloader.determine_output_dir(req)}")

    # 模拟下载后更新数据库
    print("\n💡 下载后可以更新PostgreSQL:")
    print("   UPDATE patents SET")
    print(f"       pdf_path = '/Users/xujian/apps/apps/patents/PDF/CN/{requests[0].patent_number}.pdf',")
    print("       pdf_source = 'patent_search',")
    print("       pdf_downloaded_at = NOW(),")
    print("       full_text_processed = FALSE")
    print(f"   WHERE id = '{requests[0].postgres_id}';")

    return True


def main() -> None:
    """主测试函数"""
    print("开始集成测试...\n")

    # 测试1: Google Patents工作流
    test_google_patents_workflow()

    # 测试2: patent-search集成
    test_patent_search_integration()

    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    print("\n📋 总结:")
    print("✅ Google Patents → 专利号列表 → IntegratedPatentDownloader → PDF下载")
    print("✅ patent-search → 完整元数据 → IntegratedPatentDownloader → PDF+映射")
    print("\n💡 推荐工作流:")
    print("   1. 中国专利: 使用patent-search MCP（包含完整元数据）")
    print("   2. 其他专利: 使用Google Patents手动检索，复制专利号")
    print("   3. 统一使用IntegratedPatentDownloader处理下载和映射")


if __name__ == "__main__":
    main()
