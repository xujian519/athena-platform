#!/usr/bin/env python3
"""
文章撰写服务测试脚本
Test Article Writer Service
"""

import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.writing_engine import ArticleWritingEngine, WritingRequest
from app.openclaw import ArticleContent, OpenClawHandover


async def test_openclaw_handover():
    """测试OpenClaw内容交接"""
    print("=" * 70)
    print("🧪 测试1: OpenClaw内容交接")
    print("=" * 70)

    handover = OpenClawHandover()

    # 获取状态
    status = handover.get_handover_status()
    print("\n📊 OpenClaw状态:")
    print(f"   路径: {status['openclaw_path']}")
    print(f"   可用: {status['available']}")
    print(f"   支持平台: {len(status['platforms'])}个")
    print(f"   配图风格: {len(status['image_styles'])}个")
    print(f"   文章统计: {status['article_counts']}")

    # 测试交接
    print("\n📝 测试文章交接...")

    article = ArticleContent(
        title="专利申请流程详解",
        content="""## 引言

专利申请是保护创新成果的重要手段。

## 主要流程

1. 专利检索
2. 准备材料
3. 提交申请
4. 等待审查
5. 获得授权

## 总结

专利申请需要专业知识和经验。
""",
        summary="详细介绍专利申请的完整流程",
        tags=["专利", "知识产权", "IP科普"]
    )

    result = await handover.handover_article(
        article=article,
        platforms=["小红书"]
    )

    print("\n✅ 交接结果:")
    print(f"   成功: {result.success}")
    print(f"   消息: {result.message}")
    print(f"   文章路径: {result.article_paths}")
    if result.errors:
        print(f"   错误: {result.errors}")


async def test_writing_engine():
    """测试文章撰写引擎"""
    print("\n" + "=" * 70)
    print("🧪 测试2: 文章撰写引擎")
    print("=" * 70)

    engine = ArticleWritingEngine()

    # 测试撰写
    result = await engine.write_article(
        WritingRequest(
            topic="专利无效宣告程序",
            article_type="ip_education",
            style="shandong_humor",
            platforms=["微信公众号", "小红书"]
        )
    )

    print("\n✅ 撰写结果:")
    print(f"   成功: {result.success}")
    if result.article:
        print(f"   标题: {result.article.title}")
        print(f"   类型: {result.article.article_type.value}")
        print(f"   质量: {result.article.quality_level.value}")
        print(f"   分数: {result.article.quality_score:.2f}")
    if result.warnings:
        print(f"   警告: {result.warnings}")

    # 测试交接
    if result.success and result.article:
        print("\n📤 测试自动交接...")
        handover_result = await engine.handover_to_openclaw(
            result.article,
            ["小红书"]
        )
        print(f"   交接成功: {handover_result['success']}")
        print(f"   文章路径: {handover_result['article_paths']}")


async def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 70)
    print("🧪 测试3: 便捷函数")
    print("=" * 70)

    from .service import write_article

    result = await write_article(
        article_type="ip_education",
        style="practical",
        platforms=["微信公众号"],
        handover=False
    )

    print("\n✅ 撰写结果:")
    print(f"   成功: {result.success}")
    if result.article:
        print(f"   标题: {result.article.title}")


async def main():
    """主测试函数"""
    print("\n🚀 Athena文章撰写服务测试")
    print("=" * 70)

    try:
        await test_openclaw_handover()
        await test_writing_engine()
        await test_convenience_function()

        print("\n" + "=" * 70)
        print("✅ 所有测试完成！")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
