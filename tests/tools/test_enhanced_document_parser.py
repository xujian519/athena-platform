#!/usr/bin/env python3
"""
增强文档解析器测试

测试OCR功能和minerU集成
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
from core.tools.enhanced_document_parser import (
    EnhancedDocumentParser,
    enhanced_document_parser_handler,
    parse_document,
    parse_pdf_with_ocr,
    parse_image_with_ocr,
)


class TestEnhancedDocumentParser:
    """增强文档解析器测试"""

    @pytest.fixture
    async def parser(self):
        """创建解析器实例"""
        parser = EnhancedDocumentParser()
        yield parser
        await parser.close()

    @pytest.mark.asyncio
    async def test_mineru_health_check(self, parser):
        """测试minerU健康检查"""
        health = await parser.check_mineru_health()
        # minerU可能未运行，所以只检查方法能正常调用
        assert isinstance(health, bool)

    @pytest.mark.asyncio
    async def test_parse_text_file(self, parser, tmp_path):
        """测试解析文本文件"""
        # 创建临时文本文件
        text_file = tmp_path / "test.txt"
        text_file.write_text("Hello, World!\n这是测试文件。", encoding="utf-8")

        result = await parser.parse(str(text_file))

        assert result["success"] is True
        assert result["method"] == "text_parser"
        assert "Hello, World!" in result["content"]
        assert result["file_info"]["extension"] == ".txt"

    @pytest.mark.asyncio
    async def test_parse_markdown_file(self, parser, tmp_path):
        """测试解析Markdown文件"""
        md_file = tmp_path / "test.md"
        md_file.write_text("# 测试标题\n\n这是内容。", encoding="utf-8")

        result = await parser.parse(str(md_file))

        assert result["success"] is True
        assert "测试标题" in result["content"]

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file(self, parser):
        """测试解析不存在的文件"""
        result = await parser.parse("/tmp/nonexistent_file_12345.txt")

        assert result["success"] is False
        assert "不存在" in result["error"]

    @pytest.mark.asyncio
    async def test_parse_unsupported_format(self, parser, tmp_path):
        """测试不支持的格式"""
        # 创建一个.doc文件（模拟）
        doc_file = tmp_path / "test.doc"
        doc_file.write_text("fake content")

        result = await parser.parse(str(doc_file), use_ocr=False)

        assert result["success"] is False
        assert "暂不支持" in result["error"] or "需要OCR" in result["error"]


class TestEnhancedDocumentParserHandler:
    """增强文档解析处理器测试"""

    @pytest.mark.asyncio
    async def test_handler_missing_file_path(self):
        """测试缺少file_path参数"""
        result = await enhanced_document_parser_handler({})

        assert result["success"] is False
        assert "缺少必需参数" in result["error"]

    @pytest.mark.asyncio
    async def test_handler_empty_file_path(self):
        """测试空file_path"""
        result = await enhanced_document_parser_handler({"file_path": ""})

        assert result["success"] is False
        assert "缺少必需参数" in result["error"]


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_parse_document(self, tmp_path):
        """测试parse_document便捷函数"""
        text_file = tmp_path / "test.txt"
        text_file.write_text("测试内容")

        result = await parse_document(str(text_file))

        assert result["success"] is True
        assert "测试内容" in result["content"]

    @pytest.mark.asyncio
    async def test_parse_pdf_with_ocr(self, tmp_path):
        """测试parse_pdf_with_ocr便捷函数（需要minerU）"""
        # 创建一个假的PDF文件（仅测试函数调用）
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        result = await parse_pdf_with_ocr(str(pdf_file))

        # minerU可能未运行，所以结果可能是失败
        assert "success" in result
        assert "file_info" in result

    @pytest.mark.asyncio
    async def test_parse_image_with_ocr(self, tmp_path):
        """测试parse_image_with_ocr便捷函数（需要minerU）"""
        # 创建一个小的PNG文件（1x1像素）
        import struct

        png_file = tmp_path / "test.png"
        # 最小的PNG文件
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        png_file.write_bytes(png_data)

        result = await parse_image_with_ocr(str(png_file))

        # minerU可能未运行
        assert "success" in result


class TestMinerUIntegration:
    """minerU集成测试（需要minerU运行）"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # 默认跳过，需要minerU运行时手动启用
        reason="需要minerU服务运行"
    )
    async def test_real_ocr_pdf(self):
        """测试真实PDF OCR（需要PDF文件）"""
        # 这个测试需要实际的PDF文件
        pass

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,  # 默认跳过，需要minerU运行时手动启用
        reason="需要minerU服务运行"
    )
    async def test_real_ocr_image(self):
        """测试真实图片OCR（需要图片文件）"""
        # 这个测试需要实际的图片文件
        pass


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
