#!/usr/bin/env python3
"""
详细测试小宸智能体功能
"""

import asyncio
import sys
sys.path.insert(0, '/Users/xujian/Athena工作平台/services/self-media-agent/app')

from app.core.content_creator import ContentCreator

async def test_content_creator():
    """测试内容创作模块"""
    print("\n=== 测试内容创作模块 ===")

    try:
        # 创建内容创作者
        creator = ContentCreator()
        await creator.initialize()

        # 测试内容创作
        content = await creator.create_content(
            content_type="article",
            topic="专利申请的基础知识",
            platform="小红书",
            style="casual"
        )

        print("✅ 内容创作成功！")
        print(f"标题: {content.get('title', '')}")
        print(f"内容长度: {len(content.get('body', ''))}")
        print(f"标签: {content.get('tags', [])}")

        return True

    except Exception as e:
        print(f"❌ 内容创作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_content_creator())
    if success:
        print("\n🎉 内容创作模块测试通过！")
    else:
        print("\n❌ 内容创作模块测试失败！")