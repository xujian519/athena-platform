#!/usr/bin/env python3
"""
Athena 感知模块多智能体访问示例
演示不同智能体（Athena、小诺、小娜等）如何使用感知模块
最后更新: 2026-01-26
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import json


class PerceptionClient:
    """感知模块客户端，支持多智能体访问"""

    def __init__(
        self,
        base_url: str = "http://localhost:8070",
        agent_id: str = "default",
        api_key: str | None = None
    ):
        """
        初始化感知模块客户端

        Args:
            base_url: 感知模块API地址
            agent_id: 智能体ID（athena, xiaonuo, xiaona等）
            api_key: API密钥
        """
        self.base_url = base_url
        self.agent_id = agent_id
        self.api_key = api_key or "athena_perception_api_key_2024"
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            headers={
                "X-Agent-ID": self.agent_id,
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        response = await self.session.get(f"{self.base_url}/health")
        return await response.json()

    async def process_image(
        self,
        image_path: str,
        operation: str = "extract_text",
        **kwargs
    ) -> Dict[str, Any]:
        """
        图像处理

        Args:
            image_path: 图像文件路径
            operation: 操作类型（extract_text, scene_recognition, object_detection等）
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        payload = {
            "image_path": image_path,
            "operation": operation,
            **kwargs
        }

        response = await self.session.post(
            f"{self.base_url}/api/v1/perception/image",
            json=payload
        )

        return await response.json()

    async def ocr_recognize(
        self,
        image_path: str,
        language: str = "chinese",
        **kwargs
    ) -> Dict[str, Any]:
        """
        OCR文字识别

        Args:
            image_path: 图像文件路径
            language: 语言（chinese, english, mixed）
            **kwargs: 额外参数

        Returns:
            识别结果
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        payload = {
            "image_path": image_path,
            "language": language,
            **kwargs
        }

        response = await self.session.post(
            f"{self.base_url}/api/v1/perception/ocr",
            json=payload
        )

        return await response.json()

    async def process_audio(
        self,
        audio_path: str,
        operation: str = "transcribe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        音频处理

        Args:
            audio_path: 音频文件路径
            operation: 操作类型（transcribe, analyze等）
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        payload = {
            "audio_path": audio_path,
            "operation": operation,
            **kwargs
        }

        response = await self.session.post(
            f"{self.base_url}/api/v1/perception/audio",
            json=payload
        )

        return await response.json()

    async def process_video(
        self,
        video_path: str,
        operation: str = "extract_frames",
        **kwargs
    ) -> Dict[str, Any]:
        """
        视频处理

        Args:
            video_path: 视频文件路径
            operation: 操作类型（extract_frames, analyze等）
            **kwargs: 额外参数

        Returns:
            处理结果
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")

        payload = {
            "video_path": video_path,
            "operation": operation,
            **kwargs
        }

        response = await self.session.post(
            f"{self.base_url}/api/v1/perception/video",
            json=payload
        )

        return await response.json()


# ========================================
# Athena 智能体使用示例
# ========================================

async def athena_example():
    """Athena智能体：专利图像分析示例"""
    print("\n" + "=" * 60)
    print("Athena 智能体：专利图像分析")
    print("=" * 60)

    async with PerceptionClient(agent_id="athena") as client:
        # 健康检查
        health = await client.health_check()
        print(f"\n✓ 感知模块状态: {health.get('status', 'unknown')}")

        # 示例1：专利附图OCR识别
        print("\n[示例1] 专利附图OCR识别")
        result = await client.ocr_recognize(
            image_path="/data/patents/images/CN123456789U.png",
            language="chinese",
            preprocess=True
        )
        print(f"识别结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 示例2：技术图像场景识别
        print("\n[示例2] 技术图像场景识别")
        result = await client.process_image(
            image_path="/data/patents/tech_diagram.jpg",
            operation="scene_recognition",
            categories=["technical", "engineering", "schematic"]
        )
        print(f"识别场景: {result.get('scene', 'unknown')}")

        # 示例3：专利图像目标检测
        print("\n[示例3] 专利图像目标检测")
        result = await client.process_image(
            image_path="/data/patents/product.jpg",
            operation="object_detection",
            labels=["product", "component", "assembly"]
        )
        print(f"检测到的对象: {len(result.get('objects', []))}")


# ========================================
# 小诺智能体使用示例
# ========================================

async def xiaonuo_example():
    """小诺智能体：生活场景图像识别示例"""
    print("\n" + "=" * 60)
    print("小诺 智能体：生活场景识别")
    print("=" * 60)

    async with PerceptionClient(agent_id="xiaonuo") as client:
        # 健康检查
        health = await client.health_check()
        print(f"\n✓ 感知模块状态: {health.get('status', 'unknown')}")

        # 示例1：食物识别
        print("\n[示例1] 食物识别")
        result = await client.process_image(
            image_path="/data/life/food_photo.jpg",
            operation="food_recognition",
            detail_level="high"
        )
        print(f"识别结果: {result.get('food_name', 'unknown')}")

        # 示例2：场景分类
        print("\n[示例2] 场景分类")
        result = await client.process_image(
            image_path="/data/life/scene.jpg",
            operation="scene_classification",
            categories=["indoor", "outdoor", "urban", "nature"]
        )
        print(f"场景类型: {result.get('category', 'unknown')}")

        # 示例3：证件OCR识别
        print("\n[示例3] 证件OCR识别")
        result = await client.ocr_recognize(
            image_path="/data/life/id_card.jpg",
            language="mixed",
            extract_fields=["name", "id_number", "address"]
        )
        print(f"识别姓名: {result.get('fields', {}).get('name', 'unknown')}")


# ========================================
# 小娜智能体使用示例
# ========================================

async def xiaona_example():
    """小娜智能体：法律文档图像处理示例"""
    print("\n" + "=" * 60)
    print("小娜 智能体：法律文档处理")
    print("=" * 60)

    async with PerceptionClient(agent_id="xiaona") as client:
        # 健康检查
        health = await client.health_check()
        print(f"\n✓ 感知模块状态: {health.get('status', 'unknown')}")

        # 示例1：法律文书OCR
        print("\n[示例1] 法律文书OCR")
        result = await client.ocr_recognize(
            image_path="/data/legal/court_document.jpg",
            language="chinese",
            layout_analysis=True
        )
        print(f"识别文本长度: {len(result.get('text', ''))}")

        # 示例2：合同条款提取
        print("\n[示例2] 合同条款提取")
        result = await client.process_image(
            image_path="/data/legal/contract_scan.jpg",
            operation="extract_clauses",
            clause_types=["liability", "termination", "payment"]
        )
        print(f"提取条款数: {len(result.get('clauses', []))}")

        # 示例3：证据材料处理
        print("\n[示例3] 证据材料处理")
        result = await client.process_image(
            image_path="/data/legal/evidence_photo.jpg",
            operation="evidence_analysis",
            metadata={"case_id": "CASE-2024-001"}
        )
        print(f"证据类型: {result.get('evidence_type', 'unknown')}")


# ========================================
# 音频处理示例
# ========================================

async def audio_example():
    """音频处理示例"""
    print("\n" + "=" * 60)
    print("音频处理示例")
    print("=" * 60)

    async with PerceptionClient(agent_id="athena") as client:
        # 示例1：语音转文字
        print("\n[示例1] 语音转文字")
        result = await client.process_audio(
            audio_path="/data/audio/interview.mp3",
            operation="transcribe",
            language="chinese"
        )
        print(f"转录文本: {result.get('text', '')[:100]}...")

        # 示例2：音频分析
        print("\n[示例2] 音频分析")
        result = await client.process_audio(
            audio_path="/data/audio/meeting.wav",
            operation="analyze",
            features=["emotion", "speaker_detection", "keyword_extraction"]
        )
        print(f"音频时长: {result.get('duration', 0)}秒")


# ========================================
# 视频处理示例
# ========================================

async def video_example():
    """视频处理示例"""
    print("\n" + "=" * 60)
    print("视频处理示例")
    print("=" * 60)

    async with PerceptionClient(agent_id="xiaonuo") as client:
        # 示例1：视频关键帧提取
        print("\n[示例1] 视频关键帧提取")
        result = await client.process_video(
            video_path="/data/video/life_video.mp4",
            operation="extract_frames",
            frame_count=10
        )
        print(f"提取帧数: {len(result.get('frames', []))}")

        # 示例2：视频内容分析
        print("\n[示例2] 视频内容分析")
        result = await client.process_video(
            video_path="/data/video/demo.mp4",
            operation="analyze",
            analyze_types=["scene", "object", "action"]
        )
        print(f"主要场景: {result.get('main_scene', 'unknown')}")


# ========================================
# 多智能体并发示例
# ========================================

async def multi_agent_concurrent_example():
    """多智能体并发使用示例"""
    print("\n" + "=" * 60)
    print("多智能体并发使用示例")
    print("=" * 60)

    tasks = []

    # Athena智能体：专利图像分析
    async def athena_task():
        async with PerceptionClient(agent_id="athena") as client:
            return await client.ocr_recognize(
                image_path="/data/patents/fig1.png",
                language="chinese"
            )

    # 小诺智能体：生活图像识别
    async def xiaonuo_task():
        async with PerceptionClient(agent_id="xiaonuo") as client:
            return await client.process_image(
                image_path="/data/life/scene.jpg",
                operation="scene_recognition"
            )

    # 小娜智能体：法律文档处理
    async def xiaona_task():
        async with PerceptionClient(agent_id="xiaona") as client:
            return await client.ocr_recognize(
                image_path="/data/legal/doc.jpg",
                language="chinese"
            )

    # 并发执行所有任务
    tasks = [
        athena_task(),
        xiaonuo_task(),
        xiaona_task()
    ]

    print("\n启动并发任务...")
    start_time = datetime.now()

    results = await asyncio.gather(*tasks, return_exceptions=True)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n✓ 所有任务完成，总耗时: {duration:.2f}秒")
    print(f"\nAthena任务结果: {type(results[0])}")
    print(f"小诺任务结果: {type(results[1])}")
    print(f"小娜任务结果: {type(results[2])}")


# ========================================
# 主函数
# ========================================

async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Athena 感知模块 - 多智能体访问示例")
    print("=" * 60)

    try:
        # 运行各智能体示例
        await athena_example()
        await xiaonuo_example()
        await xiaona_example()
        await audio_example()
        await video_example()
        await multi_agent_concurrent_example()

        print("\n" + "=" * 60)
        print("✓ 所有示例运行完成")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
