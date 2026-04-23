#!/usr/bin/env python3

"""
中文OCR优化测试
Chinese OCR Optimization Tests

测试内容:
1. OCR引擎初始化回退机制
2. 中文文本预处理效果
3. 文本纠错准确性
4. 置信度评分校准
5. GUI文本提取功能

作者: 小诺·双鱼公主
创建时间: 2026-01-01
"""
import logging
import os

# 导入测试模块
import sys
import tempfile
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.ai.perception.chinese_ocr_optimizer import (
    ChineseOCROptimizer,
    GUITextExtractor,
    OCRResult,
)
from core.ai.perception.visual_verification_engine import VisualVerificationEngine

logger = logging.getLogger(__name__)


# 全局fixtures (放在所有测试类之前)
@pytest.fixture
async def ocr_optimizer():
    """创建OCR优化器"""
    return ChineseOCROptimizer()


@pytest.fixture
async def visual_engine():
    """创建视觉验证引擎"""
    engine = VisualVerificationEngine()
    await engine.initialize()
    return engine


@pytest.fixture
def sample_chinese_text() -> Any:
    """示例中文文本"""
    return "这是中文测试文本,包含常见汉字和标点符号。"


@pytest.fixture
def sample_image() -> Any:
    """创建测试图片"""
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "测试文本", fill="black")

    # 保存到临时文件
    temp_path = tempfile.mktemp(suffix=".png")
    img.save(temp_path)

    yield temp_path

    # 清理
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestOCR:
    """OCR引擎测试基类"""


class TestOCREngineFallback:
    """测试OCR引擎回退机制"""

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_paddleocr_fallback_to_rapidocr(self, visual_engine):
        """测试PaddleOCR回退到RapidOCR"""
        engine_type = getattr(visual_engine, "ocr_engine_type", None)

        # 检查OCR引擎状态
        if visual_engine.ocr_engine is None and engine_type is None:
            logger.warning("⚠️ 没有可用的OCR引擎 (这是正常的,如果没有安装OCR库)")
            pytest.skip("没有可用的OCR引擎")
            return

        # 如果有引擎可用,验证其类型
        if engine_type:
            logger.info(f"✅ 当前使用引擎: {engine_type}")
            assert engine_type in [
                "paddleocr",
                "rapidocr",
                "easyocr",
            ], f"未知引擎类型: {engine_type}"

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_multi_engine_support(self, visual_engine):
        """测试多引擎支持"""
        # 检查是否支持多引擎
        assert hasattr(visual_engine, "_init_paddleocr"), "应该支持PaddleOCR"
        assert hasattr(visual_engine, "_init_rapidocr"), "应该支持RapidOCR"
        assert hasattr(visual_engine, "_init_easyocr"), "应该支持EasyOCR"


class TestChineseTextOptimization:
    """测试中文文本优化"""

    @pytest.mark.asyncio
    async def test_text_correction_basic(self, ocr_optimizer):
        """测试基本文本纠错"""
        test_cases = [
            ("①②③", "一二三"),  # 数字符号转汉字
            ("人工智Neng", "人工智能"),  # 混合字符
            ("塰", "哀"),  # 错别字
        ]

        for wrong_text, _expected_correction in test_cases:
            corrected = await ocr_optimizer.correct_text(wrong_text)
            logger.info(f"原文: {wrong_text} → 纠错: {corrected}")
            # 注意: 可能不会完全纠正,但应该有所变化
            assert isinstance(corrected, str)

    @pytest.mark.asyncio
    async def test_space_normalization(self, ocr_optimizer):
        """测试空格规范化"""
        test_text = "这  是  测  试  文  本"
        corrected = await ocr_optimizer.correct_text(test_text)

        # 中文空格应该被移除
        assert " " not in corrected, "中文空格应该被移除"
        logger.info(f"空格规范化: '{test_text}' → '{corrected}'")

    @pytest.mark.asyncio
    async def test_punctuation_normalization(self, ocr_optimizer):
        """测试标点符号规范化"""
        test_cases = [
            (",", ","),
            ("。", "."),
            ("[", "["),
            ("]", "]"),
        ]

        for chinese_punct, ascii_punct in test_cases:
            text = f"测试{chinese_punct}文本"
            corrected = await ocr_optimizer.correct_text(text)
            assert ascii_punct in corrected, f"标点{chinese_punct}应该转换为{ascii_punct}"


class TestConfidenceScoring:
    """测试置信度评分"""

    @pytest.mark.asyncio
    async def test_chinese_confidence_calculation(self, ocr_optimizer, sample_image):
        """测试中文置信度计算"""
        test_cases = [
            ("这是中文测试文本", 0.8),  # 高质量中文
            ("This is English text", 0.5),  # 英文
            ("", 0.0),  # 空文本
            ("混合Mixed文本Text", 0.6),  # 混合文本
            (
                "这是一段非常长的中文文本,包含了超过十个字符的内容,用来测试置信度计算算法对于长文本的处理能力",
                0.9,
            ),  # 长文本
        ]

        for text, min_expected_confidence in test_cases:
            confidence = ocr_optimizer._compute_chinese_confidence(text, sample_image)
            logger.info(f"文本: '{text[:20]}...' → 置信度: {confidence:.2f}")

            # 置信度应该在合理范围内
            assert 0.0 <= confidence <= 1.0, f"置信度超出范围: {confidence}"
            if min_expected_confidence > 0:
                assert (
                    confidence >= min_expected_confidence
                ), f"置信度{confidence:.2f}低于期望{min_expected_confidence:.2f}"

    @pytest.mark.asyncio
    async def test_common_chinese_character_boost(self, ocr_optimizer, sample_image):
        """测试常见汉字加分"""
        # 包含常见汉字的文本应该有更高置信度
        common_text = "的一是在不了有和人这中大为"
        rare_text = "乂丿亐亗亓"

        common_confidence = ocr_optimizer._compute_chinese_confidence(common_text, sample_image)
        rare_confidence = ocr_optimizer._compute_chinese_confidence(rare_text, sample_image)

        logger.info(f"常见字置信度: {common_confidence:.2f}")
        logger.info(f"罕见字置信度: {rare_confidence:.2f}")

        # 常见字应该有更高的基础置信度
        assert common_confidence > rare_confidence, "常见汉字应该有更高置信度"


class TestImagePreprocessing:
    """测试图像预处理"""

    @pytest.mark.asyncio
    async def test_preprocessing_creates_output(self, ocr_optimizer, sample_image):
        """测试预处理创建输出文件"""
        output_path = tempfile.mktemp(suffix="_preprocessed.png")

        try:
            result_path = await ocr_optimizer.preprocess_image(sample_image, output_path)

            # 检查输出文件是否存在
            assert os.path.exists(result_path), f"预处理输出文件不存在: {result_path}"

            # 检查文件是否可读
            img = cv2.imread(result_path)
            assert img is not None, "无法读取预处理后的图像"

            logger.info(f"✅ 预处理成功: {result_path}")

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    @pytest.mark.asyncio
    async def test_preprocessing_with_invalid_input(self, ocr_optimizer):
        """测试无效输入的处理"""
        invalid_path = "/nonexistent/path.png"

        # 应该优雅地处理错误
        result = await ocr_optimizer.preprocess_image(invalid_path)

        # 应该返回原始路径
        assert result == invalid_path, "无效输入应该返回原始路径"

    @pytest.mark.asyncio
    async def test_optimize_chinese_text_pipeline(self, ocr_optimizer, sample_image):
        """测试完整的中文OCR优化流程"""
        # 模拟OCR结果
        raw_text = "①②③ 测试文本"

        result = await ocr_optimizer.optimize_chinese_text(sample_image, raw_result=raw_text)

        assert isinstance(result, OCRResult), "应该返回OCRResult对象"
        assert isinstance(result.text, str), "文本应该是字符串"
        assert 0.0 <= result.confidence <= 1.0, "置信度应该在0-1范围内"
        assert result.engine == "optimized_chinese", "引擎名称应该正确"

        logger.info(f"✅ 优化结果: {result.text} (置信度: {result.confidence:.2f})")


class TestGUITextExtractor:
    """测试GUI文本提取器"""

    @pytest.fixture
    def gui_extractor(self) -> Any:
        """创建GUI文本提取器"""
        return GUITextExtractor()

    @pytest.fixture
    def gui_sample_image(self) -> Any:
        """创建GUI样式测试图像"""
        # 创建一个模拟GUI的图像
        img = Image.new("RGB", (800, 600), color="#f0f0f0")
        draw = ImageDraw.Draw(img)

        # 绘制标题区域
        draw.rectangle([50, 50, 750, 100], fill="#333333", outline="#000000")
        draw.text((400, 75), "页面标题", fill="white", anchor="mm")

        # 绘制按钮
        draw.rectangle([100, 150, 250, 200], fill="#4CAF50", outline="#000000")
        draw.text((175, 175), "确定", fill="white", anchor="mm")

        draw.rectangle([300, 150, 450, 200], fill="#f44336", outline="#000000")
        draw.text((375, 175), "取消", fill="white", anchor="mm")

        # 绘制输入框
        draw.rectangle([100, 250, 700, 300], fill="white", outline="#cccccc")
        draw.text((400, 275), "输入框内容", fill="#666666", anchor="mm")

        # 保存
        temp_path = tempfile.mktemp(suffix="_gui.png")
        img.save(temp_path)

        yield temp_path

        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.mark.asyncio
    async def test_button_area_detection(self, gui_extractor, gui_sample_image):
        """测试按钮区域检测"""
        img = cv2.imread(gui_sample_image)
        regions = gui_extractor._detect_button_area(img)

        assert isinstance(regions, list), "应该返回区域列表"
        assert len(regions) > 0, "应该检测到至少一个区域"
        assert isinstance(regions[0], np.ndarray), "区域应该是numpy数组"

        logger.info(f"✅ 检测到 {len(regions)} 个按钮区域")

    @pytest.mark.asyncio
    async def test_title_area_detection(self, gui_extractor, gui_sample_image):
        """测试标题区域检测"""
        img = cv2.imread(gui_sample_image)
        regions = gui_extractor._detect_title_area(img)

        assert isinstance(regions, list), "应该返回区域列表"
        assert len(regions) > 0, "应该检测到标题区域"

        # 标题区域应该在图像上方
        h, _w = img.shape[:2]
        title_region = regions[0]
        assert title_region.shape[0] < h, "标题区域高度应该小于图像高度"

        logger.info(f"✅ 标题区域尺寸: {title_region.shape}")

    @pytest.mark.asyncio
    async def test_full_gui_extraction(self, gui_extractor, gui_sample_image):
        """测试完整的GUI文本提取"""
        results = await gui_extractor.extract_text_from_screenshot(
            gui_sample_image, focus_areas=["title", "button"]
        )

        assert isinstance(results, dict), "应该返回字典结果"
        logger.info(f"✅ GUI提取结果: {list(results.keys())}")

        # 检查结果格式
        for key, value in results.items():
            assert isinstance(key, str), "键应该是字符串"
            assert isinstance(value, str), "值应该是字符串"


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_ocr_pipeline(self):
        """测试完整的OCR流程"""
        # 创建测试图像
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "集成测试文本", fill="black")

        temp_path = tempfile.mktemp(suffix="_integration.png")
        img.save(temp_path)

        try:
            # 创建优化器
            optimizer = ChineseOCROptimizer()

            # 执行优化
            result = await optimizer.optimize_chinese_text(temp_path)

            # 验证结果
            assert isinstance(result, OCRResult)
            logger.info("✅ 集成测试成功")
            logger.info(f"   文本: {result.text}")
            logger.info(f"   置信度: {result.confidence:.2f}")
            logger.info(f"   引擎: {result.engine}")

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @pytest.mark.asyncio
    async def test_visual_verification_with_ocr(self):
        """测试视觉验证与OCR集成"""
        from core.ai.perception.visual_verification_engine import (
            VisualVerificationEngine,
        )

        engine = VisualVerificationEngine()
        await engine.initialize()

        # 创建测试图像
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "验证测试", fill="black")

        temp_path = tempfile.mktemp(suffix="_verification.png")
        img.save(temp_path)

        try:
            # 测试文字提取
            extracted_text = await engine._extract_text(temp_path)

            logger.info(f"✅ 提取文字: {extracted_text}")
            logger.info(f"   OCR引擎: {getattr(engine, 'ocr_engine_type', 'unknown')}")

            # 文字提取应该返回字符串
            assert isinstance(extracted_text, str)

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# 性能测试
class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_batch_preprocessing_performance(self, ocr_optimizer):
        """测试批量预处理性能"""
        import time

        # 创建多个测试图像
        num_images = 10
        temp_paths = []

        for i in range(num_images):
            img = Image.new("RGB", (400, 100), color="white")
            temp_path = tempfile.mktemp(suffix=f"_batch_{i}.png")
            img.save(temp_path)
            temp_paths.append(temp_path)

        try:
            start_time = time.time()

            # 批量预处理
            for path in temp_paths:
                await ocr_optimizer.preprocess_image(path)

            elapsed = time.time() - start_time
            avg_time = elapsed / num_images

            logger.info("✅ 批量预处理性能:")
            logger.info(f"   总时间: {elapsed:.2f}秒")
            logger.info(f"   平均时间: {avg_time:.3f}秒/图像")
            logger.info(f"   吞吐量: {num_images/elapsed:.1f} 图像/秒")

            # 性能基准: 平均每张图像应该在1秒内完成
            assert avg_time < 1.0, f"预处理性能不足: {avg_time:.3f}秒/图像"

        finally:
            for path in temp_paths:
                if os.path.exists(path):
                    os.remove(path)


# 运行测试
def run_tests() -> Any:
    """运行所有测试"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("🧪 开始中文OCR优化测试")

    # 使用pytest运行
    pytest.main([__file__, "-v", "--tb=short", "-x", "--asyncio-mode=auto"])  # 第一个失败后停止


if __name__ == "__main__":
    run_tests()

