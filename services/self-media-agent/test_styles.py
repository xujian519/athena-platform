#!/usr/bin/env python3
"""
测试小宸不同内容风格
"""

import requests
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json

# API基础URL
BASE_URL = "http://localhost:8030"

def test_content_with_style(topic, platform, style) -> None:
    """测试指定风格的内容创作"""
    data = {
        "type": "article",
        "topic": topic,
        "platform": platform,
        "style": style
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/content/create",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ {style}风格创作成功！")
            print(f"标题: {result['content']['title']}")
            print(f"内容预览: {result['content']['body'][:100]}...")
            print(f"标签: {', '.join(result['content']['tags'])}")
        else:
            print(f"\n❌ {style}风格创作失败: {response.text}")

    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    print("🎨 测试小宸不同内容风格...")

    topic = "商标注册的注意事项"
    platform = "小红书"

    # 测试各种风格
    styles = ["professional", "casual", "humorous"]

    for style in styles:
        print(f"\n--- 测试 {style} 风格 ---")
        test_content_with_style(topic, platform, style)

    print("\n🎉 风格测试完成！")