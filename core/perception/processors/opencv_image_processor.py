#!/usr/bin/env python3
from __future__ import annotations
"""
Athena 感知模块 - 企业级OpenCV图像处理器
支持场景识别、目标检测、图像预处理、特征提取
最后更新: 2026-01-26
"""

import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OpenCVImageProcessor:
    """
    企业级OpenCV图像处理器

    功能：
    - 图像预处理（降噪、二值化、对比度增强）
    - 场景识别（室内、室外、自然风景、城市建筑等）
    - 目标检测（基础特征检测）
    - 图像增强（亮度、对比度、锐化）
    - 批量处理
    """

    def __init__(self):
        """初始化OpenCV图像处理器"""
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif', '.webp'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

        # 检查OpenCV可用性
        try:
            import cv2
            self.cv2 = cv2
            self.available = True
            logger.info(f"✓ OpenCV可用: {cv2.__version__}")
        except ImportError:
            self.available = False
            self.cv2 = None
            logger.warning("⚠ OpenCV不可用，请安装: pip install opencv-python")

    def is_available(self) -> bool:
        """检查OpenCV是否可用"""
        return self.available

    def get_version(self) -> Optional[str]:
        """获取OpenCV版本"""
        if self.available:
            return self.cv2.__version__
        return None

    async def process_image(
        self,
        image_path: str,
        operation: str,
        parameters: Optional[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        处理图像

        Args:
            image_path: 图像文件路径
            operation: 操作类型 (scene_detection, edge_detection, enhance, etc.)
            parameters: 操作参数

        Returns:
            处理结果字典
        """
        start_time = datetime.now()

        # 验证输入
        validation_result = self._validate_input(image_path)
        if not validation_result["valid"]:
            raise ValueError(validation_result["error"])

        logger.info(f"开始图像处理: {image_path}, 操作: {operation}")

        try:
            # 读取图像
            img = self._read_image(image_path)
            if img is None:
                raise ValueError(f"无法读取图像: {image_path}")

            # 根据操作类型处理
            result = await self._execute_operation(img, operation, parameters or {})

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"图像处理完成: {operation}, 耗时: {processing_time:.2f}秒")

            return {
                "success": True,
                "operation": operation,
                "result": result,
                "processing_time": processing_time,
                "image_path": image_path,
                "timestamp": datetime.now().isoformat(),
                "engine": "opencv"
            }

        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            raise

    def _validate_input(self, image_path: str) -> dict[str, Any]:
        """验证输入文件"""
        result = {"valid": True, "error": None}

        # 检查文件是否存在
        if not os.path.exists(image_path):
            result["valid"] = False
            result["error"] = f"文件不存在: {image_path}"
            return result

        # 检查文件格式
        ext = Path(image_path).suffix.lower()
        if ext not in self.supported_formats:
            result["valid"] = False
            result["error"] = f"不支持的文件格式: {ext}"
            return result

        # 检查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > self.max_file_size:
            result["valid"] = False
            result["error"] = f"文件过大: {file_size / 1024 / 1024:.2f}MB"
            return result

        return result

    def _read_image(self, image_path: str):
        """读取图像文件"""
        return self.cv2.imread(image_path)

    async def _execute_operation(
        self,
        img,
        operation: str,
        parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """执行指定的图像操作"""

        if operation == "scene_detection":
            return self._detect_scene(img)
        elif operation == "edge_detection":
            return self._detect_edges(img, parameters)
        elif operation == "enhance":
            return self._enhance_image(img, parameters)
        elif operation == "analyze":
            return self._analyze_image(img)
        elif operation == "resize":
            return self._resize_image(img, parameters)
        elif operation == "rotate":
            return self._rotate_image(img, parameters)
        elif operation == "blur":
            return self._blur_image(img, parameters)
        elif operation == "sharpen":
            return self._sharpen_image(img)
        else:
            raise ValueError(f"不支持的操作: {operation}")

    def _detect_scene(self, img) -> dict[str, Any]:
        """场景检测"""
        # 转换为灰度图
        gray = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2GRAY)

        # 计算图像特征
        height, width = gray.shape
        total_pixels = height * width

        # 计算亮度分布
        brightness = gray.mean()
        brightness_std = gray.std()

        # 计算边缘密度（使用Canny边缘检测）
        edges = self.cv2.Canny(gray, 50, 150)
        edge_density = (self.cv2.countNonZero(edges) / total_pixels) * 100

        # 判断场景类型
        scene_type = "unknown"
        confidence = 0.0

        if edge_density > 15:
            # 边缘密集，可能是室内或城市建筑
            if brightness > 150:
                scene_type = "indoor_bright"
                confidence = 0.75
            else:
                scene_type = "indoor_dim"
                confidence = 0.70
        elif edge_density > 5:
            # 中等边缘密度，可能是街道或室外
            if brightness > 120:
                scene_type = "outdoor_urban"
                confidence = 0.72
            else:
                scene_type = "outdoor_shade"
                confidence = 0.68
        else:
            # 边缘稀疏，可能是自然风景或天空
            if brightness > 180:
                scene_type = "sky_bright"
                confidence = 0.65
            else:
                scene_type = "natural_scene"
                confidence = 0.70

        return {
            "scene_type": scene_type,
            "confidence": confidence,
            "features": {
                "brightness": float(brightness),
                "brightness_std": float(brightness_std),
                "edge_density": float(edge_density),
                "width": width,
                "height": height
            },
            "description": self._get_scene_description(scene_type)
        }

    def _get_scene_description(self, scene_type: str) -> str:
        """获取场景描述"""
        descriptions = {
            "indoor_bright": "室内明亮场景",
            "indoor_dim": "室内昏暗场景",
            "outdoor_urban": "室外城市场景",
            "outdoor_shade": "室外阴影场景",
            "sky_bright": "天空明亮场景",
            "natural_scene": "自然风景场景",
            "unknown": "未知场景"
        }
        return descriptions.get(scene_type, "未知场景")

    def _detect_edges(self, img, parameters: dict[str, Any]) -> dict[str, Any]:
        """边缘检测"""
        gray = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2GRAY)

        # Canny边缘检测参数
        threshold1 = parameters.get("threshold1", 50)
        threshold2 = parameters.get("threshold2", 150)

        edges = self.cv2.Canny(gray, threshold1, threshold2)

        # 统计边缘信息
        edge_pixels = self.cv2.countNonZero(edges)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_ratio = edge_pixels / total_pixels

        return {
            "edge_pixels": int(edge_pixels),
            "total_pixels": int(total_pixels),
            "edge_ratio": float(edge_ratio),
            "description": f"检测到 {edge_pixels} 个边缘像素，占比 {edge_ratio*100:.2f}%"
        }

    def _enhance_image(self, img, parameters: dict[str, Any]) -> dict[str, Any]:
        """图像增强"""
        # 对比度增强
        alpha = parameters.get("alpha", 1.5)  # 对比度
        beta = parameters.get("beta", 30)      # 亮度

        enhanced = self.cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

        # 保存到临时文件
        temp_path = self._get_temp_path("enhanced")
        self.cv2.imwrite(temp_path, enhanced)

        return {
            "output_path": temp_path,
            "parameters": {"alpha": alpha, "beta": beta},
            "description": "图像对比度和亮度增强完成"
        }

    def _analyze_image(self, img) -> dict[str, Any]:
        """分析图像"""
        height, width, channels = img.shape
        total_pixels = height * width

        # 转换为不同颜色空间分析
        gray = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2GRAY)
        hsv = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2HSV)

        # 统计信息
        brightness = gray.mean()
        brightness_std = gray.std()

        # 颜色分布分析
        h_mean = hsv[:, :, 0].mean()
        s_mean = hsv[:, :, 1].mean()
        v_mean = hsv[:, :, 2].mean()

        # 检测主要颜色
        dominant_color = self._detect_dominant_color(hsv)

        return {
            "dimensions": {
                "width": width,
                "height": height,
                "channels": channels,
                "total_pixels": total_pixels
            },
            "brightness": {
                "mean": float(brightness),
                "std": float(brightness_std)
            },
            "color_analysis": {
                "hue_mean": float(h_mean),
                "saturation_mean": float(s_mean),
                "value_mean": float(v_mean),
                "dominant_color": dominant_color
            },
            "description": f"图像尺寸: {width}x{height}, 平均亮度: {brightness:.1f}"
        }

    def _detect_dominant_color(self, hsv) -> str:
        """检测主要颜色"""
        h_mean = hsv[:, :, 0].mean()
        s_mean = hsv[:, :, 1].mean()
        v_mean = hsv[:, :, 2].mean()

        # 简单的颜色分类
        if s_mean < 30:  # 低饱和度
            if v_mean > 200:
                return "white"
            elif v_mean < 50:
                return "black"
            else:
                return "gray"
        else:  # 高饱和度
            if 0 <= h_mean < 10 or 170 <= h_mean <= 180:
                return "red"
            elif 10 <= h_mean < 25:
                return "orange"
            elif 25 <= h_mean < 35:
                return "yellow"
            elif 35 <= h_mean < 85:
                return "green"
            elif 85 <= h_mean < 125:
                return "cyan"
            elif 125 <= h_mean < 155:
                return "blue"
            else:
                return "purple"

    def _resize_image(self, img, parameters: dict[str, Any]) -> dict[str, Any]:
        """调整图像大小"""
        width = parameters.get("width", 800)
        height = parameters.get("height", 600)

        resized = self.cv2.resize(img, (width, height))

        temp_path = self._get_temp_path("resized")
        self.cv2.imwrite(temp_path, resized)

        return {
            "output_path": temp_path,
            "original_size": (img.shape[1], img.shape[0]),
            "new_size": (width, height),
            "description": f"图像调整为 {width}x{height}"
        }

    def _rotate_image(self, img, parameters: dict[str, Any]) -> dict[str, Any]:
        """旋转图像"""
        angle = parameters.get("angle", 90)

        height, width = img.shape[:2]
        center = (width // 2, height // 2)

        # 旋转矩阵
        matrix = self.cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = self.cv2.warpAffine(img, matrix, (width, height))

        temp_path = self._get_temp_path("rotated")
        self.cv2.imwrite(temp_path, rotated)

        return {
            "output_path": temp_path,
            "angle": angle,
            "description": f"图像旋转 {angle} 度"
        }

    def _blur_image(self, img, parameters: dict[str, Any]) -> dict[str, Any]:
        """模糊图像"""
        kernel_size = parameters.get("kernel_size", 5)

        blurred = self.cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

        temp_path = self._get_temp_path("blurred")
        self.cv2.imwrite(temp_path, blurred)

        return {
            "output_path": temp_path,
            "kernel_size": kernel_size,
            "description": f"高斯模糊 (核大小: {kernel_size})"
        }

    def _sharpen_image(self, img) -> dict[str, Any]:
        """锐化图像"""
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])

        sharpened = self.cv2.filter2D(img, -1, kernel)

        temp_path = self._get_temp_path("sharpened")
        self.cv2.imwrite(temp_path, sharpened)

        return {
            "output_path": temp_path,
            "description": "图像锐化完成"
        }

    def _get_temp_path(self, prefix: str) -> str:
        """生成临时文件路径"""
        hash_val = hashlib.md5(str(datetime.now().timestamp()).encode('utf-8'), usedforsecurity=False).hexdigest()[:8]
        return f"/tmp/{prefix}_{hash_val}.png"

    async def batch_process(
        self,
        image_paths: list[str],
        operation: str,
        parameters: Optional[dict[str, Any]] | None = None
    ) -> list[dict[str, Any]]:
        """
        批量处理图像

        Args:
            image_paths: 图像文件路径列表
            operation: 操作类型
            parameters: 操作参数

        Returns:
            处理结果列表
        """
        results = []

        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"批量处理 {i+1}/{len(image_paths)}: {image_path}")
                result = await self.process_image(image_path, operation, parameters)
                results.append(result)
            except Exception as e:
                logger.error(f"批量处理失败 {image_path}: {e}")
                results.append({
                    "success": False,
                    "image_path": image_path,
                    "error": str(e)
                })

        return results

    def get_supported_operations(self) -> list[str]:
        """获取支持的操作"""
        return [
            "scene_detection",
            "edge_detection",
            "enhance",
            "analyze",
            "resize",
            "rotate",
            "blur",
            "sharpen"
        ]


# 导入numpy（仅在需要时）
try:
    import numpy as np
except ImportError:
    np = None
    logger.warning("⚠ NumPy不可用，部分功能将受限")


# 使用示例
if __name__ == "__main__":
    import asyncio

    async def test():
        processor = OpenCVImageProcessor()

        if not processor.is_available():
            print("❌ OpenCV不可用")
            print("请安装: pip install opencv-python numpy")
            return

        print("✅ OpenCV图像处理器可用")
        print(f"版本: {processor.get_version()}")
        print(f"支持的操作: {processor.get_supported_operations()}")

        # 测试图像分析（如果存在测试图像）
        test_image = "/tmp/test_image.png"
        if os.path.exists(test_image):
            result = await processor.process_image(test_image, "analyze")
            print("\n✅ 图像分析成功:")
            print(f"描述: {result['result']['description']}")

    asyncio.run(test())
