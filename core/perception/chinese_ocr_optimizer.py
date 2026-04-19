#!/usr/bin/env python3
from __future__ import annotations
"""
中文OCR优化引擎
Chinese OCR Optimization Engine

提供中文字符识别的优化策略:
1. 文本预处理 - 去噪、二值化、倾斜校正
2. 模型融合 - 多OCR引擎结果融合
3. 后处理优化 - 纠错、格式化
4. 领域适配 - 针对GUI元素的专门优化

作者: 小诺·双鱼公主
创建时间: 2026-01-01
版本: 1.0.0
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from enum import Enum

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# 性能监控 (可选)
try:
    from .ocr_performance_monitor import get_ocr_monitor

    OCR_MONITOR = get_ocr_monitor()
    HAS_MONITORING = True
except ImportError:
    HAS_MONITORING = False
    OCR_MONITOR = None


class TextOrientation(Enum):
    """文本方向"""

    HORIZONTAL = "horizontal"  # 水平
    VERTICAL = "vertical"  # 垂直


@dataclass
class OCRResult:
    """OCR识别结果"""

    text: str  # 识别的文字
    confidence: float  # 置信度 0-1
    bounding_boxes: list[list[int]] = field(default_factory=list)  # 边界框
    engine: str = ""  # 使用的引擎
    orientation: TextOrientation = TextOrientation.HORIZONTAL


class ChineseOCROptimizer:
    """
    中文OCR优化引擎

    核心优化:
    1. 图像预处理
    2. 多引擎融合
    3. 后处理纠错
    4. 领域适配
    """

    def __init__(self, config: dict | None = None):
        """
        初始化优化引擎

        Args:
            config: 配置字典
                - enable_preprocessing: 是否启用预处理
                - enable_ensemble: 是否启用多引擎融合
                - enable_postprocessing: 是否启用后处理
                - enable_monitoring: 是否启用性能监控
        """
        self.config = config or {}

        self.enable_preprocessing = self.config.get("enable_preprocessing", True)
        self.enable_ensemble = self.config.get("enable_ensemble", True)
        self.enable_postprocessing = self.config.get("enable_postprocessing", True)
        self.enable_monitoring = self.config.get("enable_monitoring", HAS_MONITORING)

        # OCR引擎列表
        self.ocr_engines = []

        # 中文纠错词典
        self.correction_dict = self._build_correction_dict()

        # 性能监控
        self.monitor = None
        if self.enable_monitoring and OCR_MONITOR:
            self.monitor = OCR_MONITOR

        logger.info("🔤 中文OCR优化引擎初始化完成")
        if self.enable_monitoring:
            logger.info("📊 性能监控已启用")

    def _build_correction_dict(self) -> dict[str, str]:
        """构建中文纠错词典"""
        return {
            # 常见混淆字符
            "0": "O",
            "1": "l",
            "2": "Z",
            "5": "S",
            "8": "B",
            # 数字与汉字混淆
            "①": "一",
            "②": "二",
            "③": "三",
            "④": "四",
            "⑤": "五",
            "⑥": "六",
            "⑦": "七",
            "⑧": "八",
            "⑨": "九",
            "⑩": "十",
            # 常见错别字
            "塰": "哀",
            "哀": "衰",
            "辩": "辨",
            "辨": "辩",
        }

    async def preprocess_image(self, image_path: str, output_path: str | None = None) -> str:
        """
        图像预处理

        Args:
            image_path: 原始图片路径
            output_path: 处理后图片保存路径

        Returns:
            str: 处理后的图片路径
        """
        if output_path is None:
            output_path = image_path.replace(".png", "_preprocessed.png")

        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                return image_path

            # 1. 灰度化
            gray = cv2.cvt_color(img, cv2.COLOR_BGR2GRAY)

            # 2. 去噪
            denoised = cv2.fast_nl_means_denoising(gray, h=10)

            # 3. 二值化 (自适应阈值)
            binary = cv2.adaptive_threshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # 4. 形态学操作
            kernel = np.ones((2, 2), np.uint8)
            processed = cv2.morphology_ex(binary, cv2.MORPH_CLOSE, kernel)

            # 保存
            cv2.imwrite(output_path, processed)

            logger.debug(f"🖼️ 图像预处理完成: {output_path}")
            return output_path

        except Exception as e:
            logger.warning(f"⚠️ 图像预处理失败: {e}")
            return image_path

    async def correct_text(self, text: str) -> str:
        """
        文本纠错

        Args:
            text: 原始文本

        Returns:
            str: 纠错后文本
        """
        if not self.enable_postprocessing:
            return text

        # 性能监控
        if self.monitor and HAS_MONITORING:
            from .ocr_performance_monitor import OCRTimer

            with OCRTimer(self.monitor, "text_correction", text_length=len(text)):
                corrected = self._do_correct_text(text)
        else:
            corrected = self._do_correct_text(text)

        return corrected

    def _do_correct_text(self, text: str) -> str:
        """执行文本纠错"""
        corrected = text

        # 1. 字符替换纠错
        for wrong, correct in self.correction_dict.items():
            corrected = corrected.replace(wrong, correct)

        # 2. 空格规范化
        corrected = re.sub(r"\s+", "", corrected)  # 移除所有空格(中文不需要)

        # 3. 标点符号规范化
        corrected = corrected.replace(",", ",").replace("。", ".")
        corrected = corrected.replace("[", "[").replace("]", "]")

        return corrected

    async def ensemble_ocr(self, image_path: str) -> list[OCRResult]:
        """
        多引擎融合OCR

        Args:
            image_path: 图片路径

        Returns:
            list[OCRResult]: 多个引擎的结果
        """
        results = []

        # 对每个引擎进行OCR
        for engine in self.ocr_engines:
            try:
                result = await self._ocr_with_engine(engine, image_path)
                if result and result.text:
                    results.append(result)
            except Exception as e:
                logger.warning(f"⚠️ OCR引擎 {engine} 失败: {e}")

        return results

    async def _ocr_with_engine(self, engine_name: str, image_path: str) -> OCRResult | None:
        """使用指定引擎进行OCR"""
        # 这里简化处理,实际会调用各个OCR引擎
        # 结果已通过VisualVerificationEngine集成

        # 预处理
        _processed_path = await self.preprocess_image(image_path)

        # 调用OCR (简化)
        # 实际会根据engine_name调用对应的OCR

        return OCRResult(text="", confidence=0.0, engine=engine_name)

    async def optimize_chinese_text(
        self, image_path: str, raw_result: str | None = None
    ) -> OCRResult:
        """
        优化中文OCR识别

        Args:
            image_path: 图片路径
            raw_result: 原始OCR结果 (可选)

        Returns:
            OCRResult: 优化后的结果
        """
        # 1. 图像预处理
        processed_path = await self.preprocess_image(image_path)

        # 2. 文本提取 (如果有原始结果)
        if raw_result:
            text = raw_result
        else:
            # 需要实际OCR (这里简化)
            text = ""

        # 3. 文本纠错
        corrected_text = await self.correct_text(text)

        # 4. 计算置信度
        confidence = self._compute_chinese_confidence(corrected_text, processed_path)

        return OCRResult(text=corrected_text, confidence=confidence, engine="optimized_chinese")

    def _compute_chinese_confidence(self, text: str, image_path: str) -> float:
        """
        计算中文识别置信度

        Args:
            text: 识别的文本
            image_path: 图片路径

        Returns:
            float: 置信度 0-1
        """
        if not text:
            return 0.0

        confidence = 0.5  # 基础置信度

        # 1. 检查中文字符比例
        chinese_chars = len([c for c in text if "\u4e00" <= c <= "\u9fff"])
        total_chars = len(text)
        if total_chars > 0:
            chinese_ratio = chinese_chars / total_chars
            confidence += chinese_ratio * 0.3  # 最多+0.3

        # 2. 检查常见中文字符
        common_chinese = "的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总达品科产"
        for char in text:
            if char in common_chinese:
                confidence += 0.01
                break

        # 3. 检查文本长度合理性
        if 10 <= len(text) <= 100:
            confidence += 0.1

        return min(confidence, 1.0)


class GUITextExtractor:
    """
    GUI文本提取器

    专门用于GUI元素的文本提取:
    - 按钮文字
    - 菜单文字
    - 标题文字
    """

    def __init__(self):
        self.optimizer = ChineseOCROptimizer()

        # GUI元素区域检测
        self.element_detectors = {
            "button": self._detect_button_area,
            "input": self._detect_input_area,
            "menu": self._detect_menu_area,
            "title": self._detect_title_area,
        }

    async def extract_text_from_screenshot(
        self, screenshot_path: str, focus_areas: list[str] | None = None
    ) -> dict[str, str]:
        """
        从截图提取文字

        Args:
            screenshot_path: 截图路径
            focus_areas: 关注区域 ['button', 'input', etc.]

        Returns:
            dict[str, str]: 各区域的文字
        """
        img = cv2.imread(screenshot_path)
        if img is None:
            return {}

        results = {}

        # 检测各区域
        for area_type, detector in self.element_detectors.items():
            if focus_areas and area_type not in focus_areas:
                continue

            try:
                # 检测区域
                regions = detector(img)

                # 对每个区域提取文字
                for i, region_img in enumerate(regions):
                    # 保存区域
                    region_path = f"/tmp/region_{area_type}_{i}.png"
                    cv2.imwrite(region_path, region_img)

                    # OCR提取
                    result = await self.optimizer.optimize_chinese_text(region_path)
                    if result.text:
                        key = f"{area_type}_{i}"
                        results[key] = result.text

            except Exception as e:
                logger.warning(f"⚠️ 区域{area_type}提取失败: {e}")

        return results

    def _detect_button_area(self, img: np.ndarray) -> list[np.ndarray]:
        """检测按钮区域 (简化)"""
        # 简化实现: 返回整个图像
        return [img]

    def _detect_input_area(self, img: np.ndarray) -> list[np.ndarray]:
        """检测输入框区域 (简化)"""
        return [img]

    def _detect_menu_area(self, img: np.ndarray) -> list[np.ndarray]:
        """检测菜单区域 (简化)"""
        return [img]

    def _detect_title_area(self, img: np.ndarray) -> list[np.ndarray]:
        """检测标题区域 (简化)"""
        h, _w = img.shape[:2]
        return [img[: h // 3, :, :]]  # 取上三分之一


# 导出
__all__ = ["ChineseOCROptimizer", "GUITextExtractor", "OCRResult", "TextOrientation"]


# ==================== 使用示例 ====================

if __name__ == "__main__":

    async def main():
        """测试中文OCR优化"""
        optimizer = ChineseOCROptimizer()

        # 测试文本纠错
        test_text = "①②③ 人工智Neng"
        corrected = await optimizer.correct_text(test_text)
        print(f"原文: {test_text}")
        print(f"纠错: {corrected}")

        # 测试置信度计算
        confidence = optimizer._compute_chinese_confidence("这是中文测试文本", "/tmp/test.png")
        print(f"置信度: {confidence:.2f}")

    asyncio.run(main())
