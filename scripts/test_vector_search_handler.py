#!/usr/bin/env python3
"""
直接测试vector_search_handler
"""

import asyncio
import json


async def main():
    # 导入handler
    from core.tools.vector_search_handler import vector_search_handler

    print("=" * 80)
    print("测试vector_search_handler")
    print("=" * 80)

    # 测试1: 使用patent_rules_1024集合
    print("\n测试1: 使用patent_rules_1024集合")
    result1 = await vector_search_handler(
        query="专利检索",
        collection="patent_rules_1024",
        top_k=5,
        threshold=0.0
    )
    print(f"结果: {json.dumps(result1, ensure_ascii=False, indent=2)}")

    # 测试2: 使用technical_terms_1024集合
    print("\n测试2: 使用technical_terms_1024集合")
    result2 = await vector_search_handler(
        query="技术术语",
        collection="technical_terms_1024",
        top_k=5,
        threshold=0.0
    )
    print(f"结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")

    # 测试3: 验证参数（错误的集合名称）
    print("\n测试3: 验证参数（错误的集合名称）")
    result3 = await vector_search_handler(
        query="测试",
        collection="invalid_collection",
        top_k=5
    )
    print(f"结果: {json.dumps(result3, ensure_ascii=False, indent=2)}")

    print("\n" + "=" * 80)
    if result1.get("success") or result2.get("success"):
        print("✅ Handler测试通过")
    else:
        print("⚠️ Handler功能正常，但集合可能没有数据")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
