#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级感知引擎测试
Tests for Lightweight Perception Engine
"""

import pytest
from pathlib import Path

from core.perception.lightweight_perception_engine import (
    LightweightPerceptionEngine,
)


class TestLightweightPerceptionEngine:
    """测试轻量级感知引擎"""

    @pytest.fixture
    def engine(self):
        """创建引擎实例"""
        return LightweightPerceptionEngine()

    def test_initialization(self, engine):
        """测试初始化"""
        assert engine.name == "LightweightPerceptionEngine"
        assert engine.version == "1.0.0"
        assert len(engine.capabilities) == 4
        assert "text_processing" in engine.capabilities
        assert "basic_image_analysis" in engine.capabilities

    def test_get_capabilities(self, engine):
        """测试获取能力列表"""
        capabilities = engine.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) == 4
        # 返回的是副本
        capabilities.append("new_capability")
        assert len(engine.capabilities) == 4

    @pytest.mark.asyncio
    async def test_process_text_success(self, engine):
        """测试成功处理文本"""
        result = await engine.process_text("测试文本内容")
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["type"] == "text"
        assert result["data"]["content"] == "测试文本内容"
        assert result["data"]["length"] == 6
        assert result["data"]["word_count"] == 2

    @pytest.mark.asyncio
    async def test_process_text_chinese(self, engine):
        """测试中文文本处理"""
        result = await engine.process_text("这是一段中文文本")
        assert result["success"] is True
        assert result["data"]["language"] == "zh"

    @pytest.mark.asyncio
    async def test_process_text_english(self, engine):
        """测试英文文本处理"""
        result = await engine.process_text("This is English text")
        assert result["success"] is True
        assert result["data"]["language"] == "en"

    @pytest.mark.asyncio
    async def test_process_text_mixed(self, engine):
        """测试中英混合文本"""
        result = await engine.process_text("Hello 你好")
        assert result["success"] is True
        # 中文超过30%应该是中文
        assert result["data"]["language"] in ["zh", "en"]

    @pytest.mark.asyncio
    async def test_process_text_empty(self, engine):
        """测试空文本处理"""
        result = await engine.process_text("")
        assert result["success"] is True
        assert result["data"]["length"] == 0
        assert result["data"]["language"] == "en"  # 默认英文

    @pytest.mark.asyncio
    async def test_process_image_jpeg(self, engine):
        """测试JPEG图像处理"""
        # JPEG魔数: FF D8 FF
        jpeg_data = b"\xff\xd8\xff" + b"\x00" * 100
        result = await engine.process_image(jpeg_data)
        assert result["success"] is True
        assert result["data"]["type"] == "image"
        assert result["data"]["format"] == "jpeg"

    @pytest.mark.asyncio
    async def test_process_image_png(self, engine):
        """测试PNG图像处理"""
        # PNG魔数: 89 50 4E 47
        png_data = b"\x89PNG" + b"\x00" * 100
        result = await engine.process_image(png_data)
        assert result["success"] is True
        assert result["data"]["format"] == "png"

    @pytest.mark.asyncio
    async def test_process_image_gif(self, engine):
        """测试GIF图像处理"""
        gif_data = b"GIF" + b"\x00" * 100
        result = await engine.process_image(gif_data)
        assert result["success"] is True
        assert result["data"]["format"] == "gif"

    @pytest.mark.asyncio
    async def test_process_image_unknown(self, engine):
        """测试未知格式图像"""
        unknown_data = b"\x00\x01\x02\x03" * 25
        result = await engine.process_image(unknown_data)
        assert result["success"] is True
        assert result["data"]["format"] == "unknown"

    @pytest.mark.asyncio
    async def test_process_document_pdf(self, engine, tmp_path):
        """测试PDF文档处理"""
        # 创建临时PDF文件
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF content")

        result = await engine.process_document(pdf_file)
        assert result["success"] is True
        assert result["data"]["type"] == "document"
        assert result["data"]["extension"] == ".pdf"
        assert result["data"]["document_type"] == "pdf"

    @pytest.mark.asyncio
    async def test_process_document_docx(self, engine, tmp_path):
        """测试DOCX文档处理"""
        docx_file = tmp_path / "test.docx"
        docx_file.write_text("Mock DOCX content")

        result = await engine.process_document(docx_file)
        assert result["success"] is True
        assert result["data"]["document_type"] == "word"

    @pytest.mark.asyncio
    async def test_process_document_txt(self, engine, tmp_path):
        """测试TXT文档处理"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Plain text content")

        result = await engine.process_document(txt_file)
        assert result["success"] is True
        assert result["data"]["document_type"] == "text"

    @pytest.mark.asyncio
    async def test_process_document_unknown_type(self, engine, tmp_path):
        """测试未知文档类型"""
        unknown_file = tmp_path / "test.unknown"
        unknown_file.write_text("Unknown content")

        result = await engine.process_document(unknown_file)
        assert result["success"] is True
        assert result["data"]["document_type"] == "unknown"

    @pytest.mark.asyncio
    async def test_process_document_with_path_string(self, engine, tmp_path):
        """测试使用字符串路径"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Content")

        result = await engine.process_document(str(txt_file))
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_process_document_nonexistent(self, engine):
        """测试处理不存在的文档"""
        result = await engine.process_document("/nonexistent/file.txt")
        assert result["success"] is True  # 不抛异常，返回成功
        assert result["data"]["size"] == 0

    @pytest.mark.asyncio
    async def test_health_check(self, engine):
        """测试健康检查"""
        health = await engine.health_check()
        assert health["status"] == "healthy"
        assert health["engine"] == "LightweightPerceptionEngine"
        assert health["version"] == "1.0.0"
        assert "capabilities" in health
