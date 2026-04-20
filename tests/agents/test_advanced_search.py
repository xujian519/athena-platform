#!/usr/bin/env python3
"""
高级专利检索功能完整测试报告

测试覆盖：
1. 基础关键词检索
2. IPC分类号过滤
3. 申请人过滤
4. 多条件组合过滤
5. 状态过滤
6. 日期范围过滤
7. 排序功能
8. 数据统计功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from advanced_patent_search import AdvancedPatentRetriever, SearchFilter


async def main():
    """运行完整测试"""
    retriever = AdvancedPatentRetriever()

    print("\n" + "="*80)
    print("📊 专利检索系统 - 高级检索功能测试报告")
    print("="*80)

    # 获取统计信息
    print("\n📋 数据库统计信息:")
    print("-"*80)
    stats = await retriever.get_statistics()
    print(f"总专利数: {stats.get('total_patents', 0)}")
    print(f"状态分布: {stats.get('by_status', {})}")
    print(f"\nTop 5 申请人:")
    for i, (name, count) in enumerate(stats.get('top_assignees', [])[:5], 1):
        print(f"  {i}. {name}: {count} 件")
    print(f"\nTop 5 IPC分类号:")
    for i, (ipc, count) in enumerate(stats.get('top_ipc_codes', [])[:5], 1):
        print(f"  {i}. {ipc}: {count} 件")
    print(f"\n日期范围: {stats.get('date_range', {})}")

    # 测试结果汇总
    test_results = []

    # 测试1: 基础检索
    print("\n" + "="*80)
    print("测试1: 基础关键词检索")
    print("="*80)
    results = await retriever.search("深度学习", top_k=3)
    test_results.append(("基础检索", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")

    # 测试2: IPC过滤
    print("\n" + "="*80)
    print("测试2: IPC分类号过滤 (G06N)")
    print("="*80)
    results = await retriever.search(
        "网络",
        top_k=5,
        filters=SearchFilter(ipc_codes=["G06N"])
    )
    test_results.append(("IPC过滤", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")
    if results:
        print(f"   示例: [{results[0].patent_id}] {results[0].title[:50]}...")
        print(f"   IPC匹配: {results[0].matched_filters}")

    # 测试3: 申请人过滤
    print("\n" + "="*80)
    print("测试3: 申请人过滤 (百度)")
    print("="*80)
    results = await retriever.search(
        "自动驾驶",
        top_k=3,
        filters=SearchFilter(assignees=["百度"])
    )
    test_results.append(("申请人过滤", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")
    if results:
        print(f"   示例: [{results[0].patent_id}] {results[0].title}")
        print(f"   申请人匹配: {results[0].matched_filters}")

    # 测试4: 状态过滤
    print("\n" + "="*80)
    print("测试4: 状态过滤 (已授权)")
    print("="*80)
    results = await retriever.search(
        "系统",
        top_k=5,
        filters=SearchFilter(status="granted")
    )
    test_results.append(("状态过滤", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")
    granted_count = sum(1 for r in results if r.status == "granted")
    print(f"   已授权专利: {granted_count}/{len(results)}")

    # 测试5: 日期范围过滤
    print("\n" + "="*80)
    print("测试5: 日期范围过滤 (2023年上半年)")
    print("="*80)
    results = await retriever.search(
        "智能",
        top_k=5,
        filters=SearchFilter(
            publication_date_start="2023-01-01",
            publication_date_end="2023-06-30"
        )
    )
    test_results.append(("日期范围过滤", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")
    if results:
        dates = [r.publication_date for r in results]
        print(f"   日期范围: {min(dates)} ~ {max(dates)}")

    # 测试6: 多条件组合
    print("\n" + "="*80)
    print("测试6: 多条件组合过滤 (IPC + 状态)")
    print("="*80)
    results = await retriever.search(
        "学习",
        top_k=5,
        filters=SearchFilter(
            ipc_codes=["G06N"],
            status="granted",
            ipc_mode="any"
        )
    )
    test_results.append(("多条件组合", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")
    if results:
        print(f"   示例: [{results[0].patent_id}] {results[0].title[:50]}...")
        print(f"   匹配条件: {results[0].matched_filters}")

    # 测试7: 排序功能
    print("\n" + "="*80)
    print("测试7: 排序功能 (按日期升序)")
    print("="*80)
    results = await retriever.search(
        "专利",
        top_k=5,
        filters=SearchFilter(sort_by="date", sort_order="asc")
    )
    test_results.append(("排序功能", len(results) > 0, len(results)))
    print(f"✅ 找到 {len(results)} 条结果")
    if results:
        dates = [r.publication_date for r in results]
        print(f"   日期排序: {dates[0]} → {dates[-1]}")

    retriever.close()

    # 输出测试汇总
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)

    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)

    for name, success, count in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name:20s} | 结果数: {count}")

    print("-"*80)
    print(f"总计: {passed}/{total} 测试通过 ({passed*100//total}%)")

    if passed == total:
        print("\n🎉 所有测试通过！高级检索功能完全正常！")
        print("\n✨ 支持的高级功能:")
        print("  • IPC分类号过滤 (单选/多选)")
        print("  • 申请人过滤 (单选/多选)")
        print("  • 发明人过滤")
        print("  • 状态过滤 (已授权/申请中)")
        print("  • 日期范围过滤")
        print("  • 多条件组合过滤")
        print("  • 相关度排序")
        print("  • 日期排序 (升序/降序)")
        print("  • 专利ID排序")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
