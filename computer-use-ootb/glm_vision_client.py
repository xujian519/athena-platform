#!/usr/bin/env python3
"""
GLM-4V视觉服务客户端
直接调用智谱AI GLM-4V API
"""

import asyncio
import aiohttp
import base64
import io
import json
from PIL import ImageGrab
from typing import Dict, Optional

class GLMVisionClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    async def analyze_image(self, image_bytes: bytes, question: str, model: str = "glm-4v-plus") -> Dict:
        """
        使用GLM-4V分析图像
        """
        # 将图片转换为base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # 构建请求
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": question
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.3
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "content": result["choices"][0]["message"]["content"],
                            "usage": result.get("usage", {}),
                            "model": model
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"API错误: {response.status}",
                            "details": error_text
                        }
        except Exception as e:
            return {
                "success": False,
                "error": "请求异常",
                "details": str(e)
            }

# 测试GLM-4V连接
async def test_glm_connection():
    """测试GLM-4V API连接"""
    api_key = "9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe"
    client = GLMVisionClient(api_key)

    # 截取屏幕测试
    screenshot = ImageGrab.grab()
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # 测试分析
    question = "请描述这个屏幕截图的主要内容，包括可见的应用程序、窗口或图标。"

    print("🔍 正在测试GLM-4V视觉分析...")
    result = await client.analyze_image(
        img_byte_arr.getvalue(),
        question
    )

    if result["success"]:
        print("✅ GLM-4V连接成功！")
        print(f"📝 分析结果: {result['content'][:300]}...")
        return True
    else:
        print("❌ GLM-4V连接失败")
        print(f"错误信息: {result['error']}")
        if 'details' in result:
            print(f"详情: {result['details']}")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_glm_connection())

    if success:
        print("\n🎉 GLM-4V API配置成功！小诺现在可以使用完整的视觉分析功能了。")