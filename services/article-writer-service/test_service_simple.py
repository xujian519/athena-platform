#!/usr/bin/env python3
"""
文章撰写服务测试脚本（使用简化版引擎）
Test Article Writer Service with Simplified Engine
"""

import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from app.openclaw import OpenClawHandover, ArticleContent
from app.core.simple_writing_engine import SimpleArticleWritingEngine, WritingRequest


async def test_openclaw_handover():
    """测试OpenClaw内容交接"""
    print("=" * 70)
    print("🧪 测试1: OpenClaw内容交接")
    print("=" * 70)

    handover = OpenClawHandover()

    # 获取状态
    status = handover.get_handover_status()
    print(f"\n📊 OpenClaw状态:")
    print(f"   路径: {status['openclaw_path']}")
    print(f"   可用: {status['available']}")
    print(f"   支持平台: {len(status['platforms'])}个 - {', '.join(status['platforms'][:3])}...")
    print(f"   配图风格: {len(status['image_styles'])}个 - {', '.join(status['image_styles'][:3])}...")
    print(f"   文章统计: {status['article_counts']}")

    # 测试交接
    print(f"\n📝 测试文章交接...")

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

    print(f"\n✅ 交接结果:")
    print(f"   成功: {result.success}")
    print(f"   消息: {result.message}")
    print(f"   文章路径: {result.article_paths}")
    if result.errors:
        print(f"   错误: {result.errors}")

    return result


async def test_writing_engine():
    """测试文章撰写引擎"""
    print("\n" + "=" * 70)
    print("🧪 测试2: 文章撰写引擎")
    print("=" * 70)

    engine = SimpleArticleWritingEngine()

    # 测试撰写
    result = await engine.write_article(
        WritingRequest(
            topic="专利无效宣告程序",
            article_type="ip_education",
            style="shandong_humor",
            platforms=["微信公众号", "小红书"]
        )
    )

    print(f"\n✅ 撰写结果:")
    print(f"   成功: {result.success}")
    if result.article:
        print(f"   标题: {result.article['title']}")
        print(f"   类型: {result.article['article_type']}")
        print(f"   风格: {result.article['style']}")

    if result.markdown_content:
        print(f"\n📝 文章内容预览（前300字）:")
        print(result.markdown_content[:300] + "...")

    return result


async def test_full_workflow():
    """测试完整工作流：撰写+交接"""
    print("\n" + "=" * 70)
    print("🧪 测试3: 完整工作流（撰写+交接）")
    print("=" * 70)

    # 1. 撰写文章
    engine = SimpleArticleWritingEngine()

    write_result = await engine.write_article(
        WritingRequest(
            topic="商标注册流程指南",
            article_type="ip_education",
            style="practical",
            platforms=["小红书", "知乎"]
        )
    )

    if not write_result.success:
        print(f"❌ 撰写失败: {write_result.errors}")
        return

    print(f"\n✅ 步骤1: 文章撰写完成")
    print(f"   标题: {write_result.article['title']}")

    # 2. 交接到OpenClaw
    print(f"\n📤 步骤2: 交接到OpenClaw...")
    handover = OpenClawHandover()

    article_content = ArticleContent(
        title=write_result.article['title'],
        content=write_result.markdown_content,
        summary="实用指南：商标注册完整流程",
        tags=["商标", "知识产权", "IP科普", "实用指南"]
    )

    handover_result = await handover.handover_article(
        article=article_content,
        platforms=write_result.article['platforms']
    )

    print(f"\n✅ 交接完成:")
    print(f"   成功: {handover_result.success}")
    print(f"   消息: {handover_result.message}")
    print(f"   文章路径: {handover_result.article_paths}")


async def main():
    """主测试函数"""
    print("\n🚀 Athena文章撰写服务测试")
    print("=" * 70)

    try:
        # 测试1: OpenClaw交接
        await test_openclaw_handover()

        # 测试2: 文章撰写
        await test_writing_engine()

        # 测试3: 完整工作流
        await test_full_workflow()

        print("\n" + "=" * 70)
        print("✅ 所有测试完成！")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
