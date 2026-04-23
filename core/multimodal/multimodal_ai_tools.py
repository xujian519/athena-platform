#!/usr/bin/env python3
from __future__ import annotations
"""
多模态AI工具接口
Multimodal AI Tools Interface

支持CogView-4图像生成和CogVideoX-3视频生成

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from types import TracebackType
from typing import Any

import aiohttp


class ModalityType(Enum):
    """模态类型"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class ImageStyle(Enum):
    """图像风格"""

    REALISTIC = "realistic"
    ARTISTIC = "artistic"
    TECHNICAL = "technical"
    MINIMALIST = "minimalist"
    CARTOON = "cartoon"
    BUSINESS = "business"
    PATENT_DRAWING = "patent_drawing"


class VideoStyle(Enum):
    """视频风格"""

    REALISTIC = "realistic"
    ANIMATED = "animated"
    THREE_D = "3d"
    CINEMATIC = "cinematic"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"


@dataclass
class ImageGenerationRequest:
    """图像生成请求"""

    prompt: str
    model: str = "cogview-4"
    size: str = "1024x1024"
    style: Optional[str] = None
    quality: str = "high"
    num_images: int = 1
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None


@dataclass
class VideoGenerationRequest:
    """视频生成请求"""

    prompt: str
    model: str = "cogvideox-3"
    duration: int = 6
    resolution: str = "4K"
    fps: int = 60
    style: Optional[str] = None
    image_url: Optional[str] = None  # 首帧参考
    end_image_url: Optional[str] = None  # 尾帧参考
    audio_enabled: bool = False


@dataclass
class GenerationResponse:
    """生成响应"""

    success: bool
    task_id: str
    modality: str
    model: str
    status: str
    result_urls: list[str] = field(default_factory=list)
    error: Optional[str] = None
    generation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class MultimodalAITools:
    """多模态AI工具类"""

    def __init__(self, api_key: Optional[str] = None):
        # 从环境变量获取API密钥(安全要求:禁止硬编码)
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API密钥未设置。请设置环境变量 ZHIPU_API_KEY "
                "或通过参数传入。获取密钥: https://open.bigmodel.cn/"
            )
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.session = None
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("MultimodalAITools")
        logger.setLevel(logging.INFO)  # Fixed: set_level → setLevel

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)  # Fixed: set_formatter → setFormatter
            logger.addHandler(handler)  # Fixed: add_handler → addHandler

        return logger

    async def __aenter__(self):
        """异步上下文入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),  # 视频生成可能需要更长时间
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ):
        """异步上下文出口"""
        if self.session:
            await self.session.close()

    async def generate_image(
        self, request: ImageGenerationRequest, save_path: Path | None = None
    ) -> GenerationResponse:
        """
        生成图像

        Args:
            request: 图像生成请求
            save_path: 可选的保存路径

        Returns:
            GenerationResponse: 生成响应
        """
        start_time = datetime.now()

        try:
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "size": request.size,
                "quality": request.quality,
                "n": request.num_images,
            }

            if request.negative_prompt:
                payload["negative_prompt"] = request.negative_prompt

            if request.seed:
                payload["seed"] = request.seed

            self.logger.info(f"🎨 开始生成图像: {request.prompt[:50]}...")

            if self.session is None:
                raise RuntimeError("Session not initialized. Use 'async with' context manager.")

            async with self.session.post(
                f"{self.base_url}/images/generations", json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # 提取图像URL
                    image_urls = []
                    if "data" in data:
                        for item in data["data"]:
                            if "url" in item:
                                image_urls.append(item["url"])

                    # 可选:下载并保存图像
                    if save_path and image_urls:
                        for i, url in enumerate(image_urls):
                            await self._download_image(url, save_path / f"generated_image_{i}.png")

                    generation_time = (datetime.now() - start_time).total_seconds()

                    self.logger.info(f"✅ 图像生成成功,耗时: {generation_time:.2f}秒")

                    return GenerationResponse(
                        success=True,
                        task_id=data.get("id", ""),
                        modality="image",
                        model=request.model,
                        status="completed",
                        result_urls=image_urls,
                        generation_time=generation_time,
                    )
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ 图像生成失败: {error_text}")
                    return GenerationResponse(
                        success=False,
                        task_id="",
                        modality="image",
                        model=request.model,
                        status="failed",
                        error=error_text,
                        generation_time=(datetime.now() - start_time).total_seconds(),
                    )

        except Exception as e:
            self.logger.error(f"❌ 图像生成异常: {e}")
            return GenerationResponse(
                success=False,
                task_id="",
                modality="image",
                model=request.model,
                status="error",
                error=str(e),
                generation_time=(datetime.now() - start_time).total_seconds(),
            )

    async def generate_video(self, request: VideoGenerationRequest) -> GenerationResponse:
        """
        生成视频

        Args:
            request: 视频生成请求

        Returns:
            GenerationResponse: 生成响应
        """
        start_time = datetime.now()

        try:
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "duration": request.duration,
            }

            if request.image_url:
                payload["image_url"] = request.image_url

            if request.end_image_url:
                payload["end_image_url"] = request.end_image_url

            self.logger.info(f"🎬 开始生成视频: {request.prompt[:50]}...")

            if self.session is None:
                raise RuntimeError("Session not initialized. Use 'async with' context manager.")

            async with self.session.post(
                f"{self.base_url}/videos/generations", json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # 提取视频URL
                    video_urls = []
                    if "data" in data:
                        for item in data["data"]:
                            if "url" in item:
                                video_urls.append(item["url"])

                    generation_time = (datetime.now() - start_time).total_seconds()

                    self.logger.info(f"✅ 视频生成成功,耗时: {generation_time:.2f}秒")

                    return GenerationResponse(
                        success=True,
                        task_id=data.get("id", ""),
                        modality="video",
                        model=request.model,
                        status="completed",
                        result_urls=video_urls,
                        generation_time=generation_time,
                    )
                else:
                    error_text = await response.text()
                    self.logger.error(f"❌ 视频生成失败: {error_text}")
                    return GenerationResponse(
                        success=False,
                        task_id="",
                        modality="video",
                        model=request.model,
                        status="failed",
                        error=error_text,
                        generation_time=(datetime.now() - start_time).total_seconds(),
                    )

        except Exception as e:
            self.logger.error(f"❌ 视频生成异常: {e}")
            return GenerationResponse(
                success=False,
                task_id="",
                modality="video",
                model=request.model,
                status="error",
                error=str(e),
                generation_time=(datetime.now() - start_time).total_seconds(),
            )

    async def _download_image(self, url: str, save_path: Path):
        """下载图像"""
        if self.session is None:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")

        async with self.session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(content)
                self.logger.info(f"💾 图像已保存: {save_path}")

    async def batch_generate_images(
        self, prompts: list[str], model: str = "cogview-4", **kwargs: Any
    ) -> list[GenerationResponse]:
        """批量生成图像"""
        tasks = []
        for prompt in prompts:
            request = ImageGenerationRequest(prompt=prompt, model=model, **kwargs)
            tasks.append(self.generate_image(request))

        return await asyncio.gather(*tasks)

    def create_patent_drawing_prompt(
        self, technical_feature: str, view_type: str = "front_view"
    ) -> str:
        """
        创建专利附图提示词

        Args:
            technical_feature: 技术特征描述
            view_type: 视图类型 (front_view, side_view, top_view, perspective, exploded)

        Returns:
            优化后的提示词
        """
        view_descriptions = {
            "front_view": "正视图",
            "side_view": "侧视图",
            "top_view": "俯视图",
            "perspective": "透视图",
            "exploded": "爆炸图",
        }

        prompt = f"""生成一张详细的专利技术附图{view_descriptions.get(view_type, '正视图')}。
技术特征: {technical_feature}
风格要求: 技术制图风格,清晰的线条,专业的标注,白底,高对比度
用途: 专利申请附图"""

        return prompt

    def create_marketing_video_prompt(
        self, product_name: str, key_features: list[str], duration: int = 6
    ) -> str:
        """
        创建营销视频提示词

        Args:
            product_name: 产品名称
            key_features: 关键特性列表
            duration: 视频时长

        Returns:
            优化后的提示词
        """
        features_str = "、".join(key_features)
        prompt = f"""创建一个{duration}秒的产品营销视频。
产品名称: {product_name}
核心特性: {features_str}
视觉风格: 现代科技感,动态流畅,高清画质
镜头运动: 平滑过渡,突出产品特点
背景音乐: 轻快现代(如启用音频)"""

        return prompt

    def create_technical_animation_prompt(
        self, technology_description: str, animation_type: str = "principle_demo"
    ) -> str:
        """
        创建技术动画提示词

        Args:
            technology_description: 技术描述
            animation_type: 动画类型

        Returns:
            优化后的提示词
        """
        prompt = f"""创建技术原理演示动画。
技术内容: {technology_description}
动画风格: 真实物理模拟,3D渲染,专业准确
演示方式: 循序渐进,突出关键步骤
时长: 6秒,60fps,4K分辨率"""

        return prompt


# 便捷函数
async def generate_patent_drawing(
    technical_feature: str, view_type: str = "front_view", save_path: Path | None = None
) -> GenerationResponse:
    """
    生成专利附图(便捷函数)

    Args:
        technical_feature: 技术特征
        view_type: 视图类型
        save_path: 保存路径

    Returns:
        GenerationResponse
    """
    tools = MultimodalAITools()

    async with tools:
        prompt_generator = tools
        prompt = prompt_generator.create_patent_drawing_prompt(technical_feature, view_type)

        request = ImageGenerationRequest(
            prompt=prompt, model="cogview-4", size="1024x1024", style="technical"
        )

        return await tools.generate_image(request, save_path)


async def generate_product_video(product_name: str, key_features: list[str]) -> GenerationResponse:
    """
    生成产品营销视频(便捷函数)

    Args:
        product_name: 产品名称
        key_features: 关键特性

    Returns:
        GenerationResponse
    """
    tools = MultimodalAITools()

    async with tools:
        prompt_generator = tools
        prompt = prompt_generator.create_marketing_video_prompt(product_name, key_features)

        request = VideoGenerationRequest(prompt=prompt, model="cogvideox-3", duration=6)

        return await tools.generate_video(request)


# 使用示例
async def main():
    """主函数示例"""
    tools = MultimodalAITools()

    async with tools:
        # 示例1: 生成专利附图
        print("📝 示例1: 生成专利附图")
        patent_prompt = tools.create_patent_drawing_prompt(
            "一种智能家居控制系统的触摸屏界面", "front_view"
        )
        print(f"提示词: {patent_prompt}")

        # 示例2: 生成产品视频
        print("\n🎬 示例2: 生成产品视频")
        video_prompt = tools.create_technical_animation_prompt("机器学习模型训练过程可视化")
        print(f"提示词: {video_prompt}")

        # 实际生成(需要API调用)
        # request = ImageGenerationRequest(prompt=patent_prompt)
        # response = await tools.generate_image(request)
        # print(f"结果: {response.success}, URLs: {response.result_urls}")


# 入口点: @async_main装饰器已添加到main函数
