#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PatentImageAnalyzer 单元测试

测试范围:
1. 模型加载 (ModelScope/HuggingFace)
2. 设备自动检测
3. 图像文件验证
4. 备用方案降级
5. 图像分类
6. 超时控制
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock

import pytest
import torch
import numpy as np
from PIL import Image

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from production.core.perception.processors.patent_image_analyzer import (
    PatentImageAnalyzer,
    ImageType,
    BLIPConfig,
    ModelPaths,
    ImageValidation,
    ModelLoading,
    with_timeout
)


# ============================================================================
# 测试配置类
# ============================================================================


class TestBLIPConfig:
    """测试BLIP配置常量"""

    def test_config_values(self):
        """测试配置值是否正确设置"""
        assert BLIPConfig.MAX_CAPTION_LENGTH == 50
        assert BLIPConfig.NUM_BEAMS == 5
        assert BLIPConfig.USE_EARLY_STOPPING is True


class TestModelPaths:
    """测试模型路径配置"""

    def test_default_values(self):
        """测试默认路径值"""
        assert "modelscope" in ModelPaths.MODELSCOPE_BLIP.lower()
        assert "huggingface" in ModelPaths.HUGGINGFACE_CACHE.lower()
        assert "blip-image-captioning-base" in ModelPaths.MODELSCOPE_BLIP

    def test_env_override(self, monkeypatch):
        """测试环境变量覆盖"""
        monkeypatch.setenv("MODELSCOPE_BLIP_PATH", "/custom/path/to/blip")
        # 重新导入以获取环境变量
        import importlib
        import production.core.perception.processors.patent_image_analyzer as pia
        importlib.reload(pia)
        assert "/custom/path/to/blip" in pia.ModelPaths.MODELSCOPE_BLIP


class TestImageValidationConfig:
    """测试图像验证配置类"""

    def test_max_file_size(self):
        """测试文件大小限制"""
        assert ImageValidation.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10MB

    def test_allowed_extensions(self):
        """测试允许的文件扩展名"""
        assert '.png' in ImageValidation.ALLOWED_EXTENSIONS
        assert '.jpg' in ImageValidation.ALLOWED_EXTENSIONS
        assert '.jpeg' in ImageValidation.ALLOWED_EXTENSIONS
        assert '.gif' in ImageValidation.ALLOWED_EXTENSIONS
        assert '.bmp' in ImageValidation.ALLOWED_EXTENSIONS
        assert '.tiff' in ImageValidation.ALLOWED_EXTENSIONS
        assert '.webp' in ImageValidation.ALLOWED_EXTENSIONS


class TestModelLoadingConfig:
    """测试模型加载配置类"""

    def test_timeout_values(self):
        """测试超时配置"""
        assert ModelLoading.CLIP_TIMEOUT == 120
        assert ModelLoading.BLIP_TIMEOUT == 180  # CPU上加载近1GB模型需要更长时间

    def test_retry_config(self):
        """测试重试配置"""
        assert ModelLoading.RETRY_DELAY == 5
        assert ModelLoading.MAX_RETRIES == 2


# ============================================================================
# 测试工具函数
# ============================================================================


class TestWithTimeout:
    """测试超时控制函数"""

    def test_timeout_success(self):
        """测试函数正常执行"""
        def quick_func():
            return "success"

        result = with_timeout(quick_func, 5, "超时测试")
        assert result == "success"

    def test_timeout_exception(self):
        """测试函数抛出异常"""
        def error_func():
            raise ValueError("测试错误")

        with pytest.raises(ValueError, match="测试错误"):
            with_timeout(error_func, 5, "超时测试")

    def test_timeout_exceeded(self):
        """测试超时触发"""
        def slow_func():
            time.sleep(10)  # 超过2秒超时

        with pytest.raises(TimeoutError, match="超时测试"):
            with_timeout(slow_func, 2, "超时测试")


# ============================================================================
# 测试PatentImageAnalyzer类
# ============================================================================


class TestPatentImageAnalyzerInit:
    """测试PatentImageAnalyzer初始化"""

    def test_init_with_defaults(self):
        """测试默认初始化"""
        analyzer = PatentImageAnalyzer()
        assert analyzer.clip_model_name == "openai/clip-vit-base-patch32"
        assert analyzer.blip_model_name == "Salesforce/blip-image-captioning-base"
        assert analyzer.device in ["cpu", "cuda", "mps"]
        assert analyzer.clip_model is None  # 延迟加载
        assert analyzer.blip_model is None

    def test_init_with_custom_device(self):
        """测试自定义设备初始化"""
        analyzer = PatentImageAnalyzer(device="cpu")
        assert analyzer.device == "cpu"

    def test_init_with_custom_cache_dir(self):
        """测试自定义缓存目录"""
        analyzer = PatentImageAnalyzer(cache_dir="/tmp/test_cache")
        assert "/tmp/test_cache" in analyzer.cache_dir


class TestDeviceDetection:
    """测试设备自动检测"""

    def test_detect_device_cpu(self):
        """测试CPU设备检测"""
        with patch('torch.cuda.is_available', return_value=False), \
             patch('torch.backends.mps.is_available', return_value=False):
            analyzer = PatentImageAnalyzer(device=None)
            assert analyzer.device == "cpu"

    @pytest.mark.skipif(not hasattr(torch, 'cuda'), reason="CUDA not available")
    def test_detect_device_cuda(self):
        """测试CUDA设备检测"""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.backends.mps.is_available', return_value=False):
            analyzer = PatentImageAnalyzer(device=None)
            # 如果有CUDA，应该优先使用
            if torch.cuda.is_available():
                assert analyzer.device == "cuda"

    @pytest.mark.skipif(sys.platform != "darwin", reason="MPS only on macOS")
    def test_detect_device_mps(self):
        """测试MPS设备检测（Apple Silicon）"""
        with patch('torch.backends.mps.is_available', return_value=True):
            analyzer = PatentImageAnalyzer(device=None)
            # MPS应该优先于CUDA
            if torch.backends.mps.is_available():
                assert analyzer.device == "mps"


class TestImageValidation:
    """测试图像文件验证"""

    def test_validate_success(self):
        """测试有效图像文件验证"""
        analyzer = PatentImageAnalyzer()

        # 创建临时图像文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            # 创建一个小的PNG图像
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f)

        try:
            result = analyzer._validate_image_file(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_validate_file_not_found(self):
        """测试文件不存在验证"""
        analyzer = PatentImageAnalyzer()
        with pytest.raises(ValueError, match="图像文件不存在"):
            analyzer._validate_image_file("/nonexistent/file.png")

    def test_validate_file_too_large(self):
        """测试文件大小超限验证"""
        analyzer = PatentImageAnalyzer()

        # 创建一个大于10MB的文件（使用mock）
        with patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=15 * 1024 * 1024):
            with pytest.raises(ValueError, match="图像文件过大"):
                analyzer._validate_image_file("/fake/large.png")

    def test_validate_invalid_extension(self):
        """测试无效文件扩展名验证"""
        analyzer = PatentImageAnalyzer()

        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            temp_path = f.name
            f.write(b"fake content")

        try:
            with pytest.raises(ValueError, match="不支持的文件类型"):
                analyzer._validate_image_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_extensions(self):
        """测试所有支持的扩展名"""
        analyzer = PatentImageAnalyzer()

        supported_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp']
        for ext in supported_extensions:
            assert ext in ImageValidation.ALLOWED_EXTENSIONS


class TestImageLoading:
    """测试图像加载"""

    def test_load_from_file(self):
        """测试从文件路径加载图像"""
        analyzer = PatentImageAnalyzer()

        # 创建临时图像文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            img = Image.new('RGB', (200, 200), color='blue')
            img.save(f)

        try:
            loaded_img = analyzer._load_image(temp_path)
            assert loaded_img is not None
            assert loaded_img.size == (200, 200)
            assert loaded_img.mode == 'RGB'
        finally:
            os.unlink(temp_path)

    def test_load_from_bytes(self):
        """测试从字节流加载图像"""
        analyzer = PatentImageAnalyzer()

        # 创建图像字节流
        img = Image.new('RGB', (150, 150), color='green')
        import io
        byte_stream = io.BytesIO()
        img.save(byte_stream, format='PNG')
        image_bytes = byte_stream.getvalue()

        loaded_img = analyzer._load_image(image_bytes)
        assert loaded_img is not None
        assert loaded_img.size == (150, 150)

    def test_load_from_numpy(self):
        """测试从numpy数组加载图像"""
        analyzer = PatentImageAnalyzer()

        # 创建numpy数组
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        loaded_img = analyzer._load_image(img_array)
        assert loaded_img is not None
        assert loaded_img.size == (100, 100)

    def test_load_invalid_input(self):
        """测试无效输入"""
        analyzer = PatentImageAnalyzer()
        result = analyzer._load_image({"invalid": "input"})
        assert result is None

    def test_load_image_resize(self):
        """测试大图像自动调整大小"""
        analyzer = PatentImageAnalyzer()

        # 创建大图像
        large_img = Image.new('RGB', (4000, 3000), color='yellow')

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            large_img.save(f)

        try:
            loaded_img = analyzer._load_image(temp_path)
            # 应该被调整为最大2048
            assert max(loaded_img.size) <= 2048
        finally:
            os.unlink(temp_path)


class TestImageClassification:
    """测试图像类型分类"""

    def test_classify_square_image(self):
        """测试方形图像分类"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (500, 500), color='white')
        img_type = analyzer._classify_image_type(img)
        assert img_type in ImageType

    def test_classify_wide_image(self):
        """测试宽幅图像分类"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (800, 400), color='white')
        img_type = analyzer._classify_image_type(img)
        assert img_type in ImageType

    def test_classify_tall_image(self):
        """测试长条图像分类"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (400, 800), color='white')
        img_type = analyzer._classify_image_type(img)
        # 长条图更可能是流程图
        assert img_type in ImageType


class TestFallbackCaption:
    """测试备用图像描述生成"""

    def test_fallback_caption_figure(self):
        """测试FIGURE类型的备用描述"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (500, 500), color='white')
        caption = analyzer._generate_fallback_caption(img, ImageType.FIGURE)
        assert "专利附图" in caption
        assert "技术元件" in caption or "技术信息" in caption

    def test_fallback_caption_flowchart(self):
        """测试FLOWCHART类型的备用描述"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (500, 500), color='white')
        caption = analyzer._generate_fallback_caption(img, ImageType.FLOWCHART)
        assert "流程图" in caption
        assert "处理步骤" in caption or "方法流程" in caption

    def test_fallback_caption_structure(self):
        """测试STRUCTURE类型的备用描述"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (500, 500), color='white')
        caption = analyzer._generate_fallback_caption(img, ImageType.STRUCTURE)
        assert "结构图" in caption
        assert "组成结构" in caption or "系统" in caption

    def test_fallback_caption_graph(self):
        """测试GRAPH类型的备用描述"""
        analyzer = PatentImageAnalyzer()
        img = Image.new('RGB', (500, 500), color='white')
        caption = analyzer._generate_fallback_caption(img, ImageType.GRAPH)
        assert "数据图表" in caption or "图表" in caption


class TestModelLoading:
    """测试模型加载"""

    @pytest.mark.slow
    @pytest.mark.skipif(os.getenv("CI") == "true", reason="跳过CI环境中的模型加载测试")
    def test_load_clip_model(self):
        """测试CLIP模型加载"""
        analyzer = PatentImageAnalyzer(device="cpu")
        # 检查本地是否有缓存的模型
        cache_path = os.path.expanduser(ModelPaths.HUGGINGFACE_CACHE)
        clip_cached = os.path.exists(os.path.join(cache_path, "models--openai--clip-vit-base-patch32"))

        if not clip_cached:
            pytest.skip("CLIP模型未缓存，跳过测试")

        analyzer.load_models()
        assert analyzer.clip_model is not None
        assert analyzer.clip_processor is not None

    @pytest.mark.slow
    def test_load_blip_model_from_modelscope(self):
        """测试从ModelScope加载BLIP模型"""
        ms_path = os.path.expanduser(ModelPaths.MODELSCOPE_BLIP)
        if not os.path.exists(ms_path):
            pytest.skip(f"ModelScope模型不存在: {ms_path}")

        analyzer = PatentImageAnalyzer(device="cpu")
        analyzer.load_models()
        assert analyzer.blip_model is not None
        assert analyzer.blip_processor is not None

    def test_load_blip_model_timeout_config(self):
        """测试BLIP模型加载超时配置（不实际加载）"""
        # 只测试配置是否正确，不实际加载模型
        assert ModelLoading.BLIP_TIMEOUT == 180  # CPU上加载近1GB模型需要更长时间


class TestImageAnalysis:
    """测试图像分析"""

    @pytest.mark.slow
    def test_analyze_with_file(self):
        """测试从文件分析图像"""
        analyzer = PatentImageAnalyzer(device="cpu")

        # 创建测试图像
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            img = Image.new('RGB', (400, 600), color='white')
            # 画一些简单图形
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.rectangle([100, 100, 300, 200], outline='black', width=3)
            img.save(f)

        try:
            result = analyzer._load_image(temp_path)
            assert result is not None
            # 测试图像分类
            img_type = analyzer._classify_image_type(result)
            assert img_type in ImageType
        finally:
            os.unlink(temp_path)

    def test_generate_image_id(self):
        """测试图像ID生成"""
        analyzer = PatentImageAnalyzer()
        id1 = analyzer._generate_image_id("/path/to/image.png")
        id2 = analyzer._generate_image_id("/path/to/image.png")
        id3 = analyzer._generate_image_id("/path/to/other.png")

        assert id1 == id2  # 相同路径应该生成相同ID
        assert id1 != id3  # 不同路径应该生成不同ID
        assert len(id1) == 16  # ID应该是16位MD5


class TestErrorHandling:
    """测试错误处理"""

    def test_blip_model_failure_graceful_degradation(self):
        """测试BLIP模型失败时的优雅降级"""
        analyzer = PatentImageAnalyzer()
        # 模拟BLIP未加载
        analyzer.blip_model = None
        analyzer.blip_processor = None

        # 创建测试图像
        img = Image.new('RGB', (400, 600), color='white')

        # 测试备用方案（异步方法需要在事件循环中运行）
        import asyncio
        async def test_fallback():
            caption = await analyzer._generate_caption(img)
            # BLIP不可用时应该返回空字符串或备用描述
            assert isinstance(caption, str)

        asyncio.run(test_fallback())

    def test_ocr_engine_failure(self):
        """测试OCR引擎失败时的处理"""
        analyzer = PatentImageAnalyzer()
        analyzer.ocr_engine = None  # 模拟OCR不可用

        import asyncio
        async def test_no_ocr():
            img = Image.new('RGB', (400, 600), color='white')
            ocr_text, regions = await analyzer._extract_text(img)
            assert ocr_text == ""
            assert regions == []

        asyncio.run(test_no_ocr())


# ============================================================================
# 测试集成场景
# ============================================================================


class TestIntegration:
    """集成测试"""

    @pytest.mark.slow
    def test_full_analysis_pipeline(self):
        """测试完整的分析流程"""
        analyzer = PatentImageAnalyzer(device="cpu")

        # 创建测试图像
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            img = Image.new('RGB', (800, 600), color='white')
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            # 画一个简单的流程图
            draw.rectangle([100, 100, 200, 150], outline='black', width=2)
            draw.rectangle([100, 300, 200, 350], outline='black', width=2)
            draw.line([150, 150, 150, 300], fill='black', width=2)
            img.save(f)

        try:
            # 加载图像
            loaded_img = analyzer._load_image(temp_path)
            assert loaded_img is not None

            # 分类图像
            img_type = analyzer._classify_image_type(loaded_img)
            assert img_type in ImageType

            # 生成备用描述
            caption = analyzer._generate_fallback_caption(loaded_img, img_type)
            assert len(caption) > 0

        finally:
            os.unlink(temp_path)


# ============================================================================
# 运行配置
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
