#!/usr/bin/env python3
"""
路径处理工具模块单元测试
"""

import tempfile
from pathlib import Path

from core.utils.path_utils import (
    ensure_dir,
    get_ext,
    get_stem,
    safe_exists,
    safe_read,
    safe_write,
)


class TestEnsureDir:
    """ensure_dir函数测试"""

    def test_create_new_directory(self):
        """测试创建新目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new" / "nested" / "dir"
            result = ensure_dir(new_dir)
            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_existing_directory(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir) / "existing"
            existing_dir.mkdir()
            result = ensure_dir(existing_dir)
            assert result == existing_dir
            assert existing_dir.exists()


class TestSafeExists:
    """safe_exists函数测试"""

    def test_existing_path(self):
        """测试存在的路径"""
        with tempfile.NamedTemporaryFile() as f:
            assert safe_exists(f.name) is True

    def test_nonexistent_path(self):
        """测试不存在的路径"""
        assert safe_exists("/nonexistent/path/that/does/not/exist") is False

    def test_invalid_path(self):
        """测试无效路径（不应抛出异常）"""
        # 安全地处理异常情况
        result = safe_exists(None)
        # 应该返回False而不抛出异常
        assert result is False


class TestSafeRead:
    """safe_read函数测试"""

    def test_read_existing_file(self):
        """测试读取存在的文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("测试内容")
            temp_path = f.name

        try:
            result = safe_read(temp_path)
            assert result == "测试内容"
        finally:
            Path(temp_path).unlink()

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        result = safe_read("/nonexistent/file.txt")
        assert result is None

    def test_read_with_encoding(self):
        """测试指定编码读取"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='gbk') as f:
            f.write("中文内容")
            temp_path = f.name

        try:
            result = safe_read(temp_path, encoding='gbk')
            assert result == "中文内容"
        finally:
            Path(temp_path).unlink()


class TestSafeWrite:
    """safe_write函数测试"""

    def test_write_to_new_file(self):
        """测试写入新文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.txt"
            result = safe_write(temp_path, "测试内容")
            assert result is True
            assert temp_path.exists()
            assert temp_path.read_text(encoding='utf-8') == "测试内容"

    def test_write_to_nested_directory(self):
        """测试写入嵌套目录（自动创建父目录）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "nested" / "dir" / "test.txt"
            result = safe_write(temp_path, "内容")
            assert result is True
            assert temp_path.exists()
            assert temp_path.parent.exists()

    def test_write_with_encoding(self):
        """测试指定编码写入"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.txt"
            result = safe_write(temp_path, "中文", encoding='gbk')
            assert result is True
            content = temp_path.read_text(encoding='gbk')
            assert content == "中文"


class TestGetExt:
    """get_ext函数测试"""

    def test_get_extension(self):
        """测试获取扩展名"""
        assert get_ext("test.txt") == ".txt"
        assert get_ext("document.pdf") == ".pdf"
        assert get_ext("archive.tar.gz") == ".gz"  # 只获取最后一个

    def test_get_extension_lowercase(self):
        """测试扩展名转为小写"""
        assert get_ext("TEST.TXT") == ".txt"
        assert get_ext("file.PDF") == ".pdf"

    def test_no_extension(self):
        """测试无扩展名文件"""
        assert get_ext("filename") == ""
        assert get_ext("path/to/file") == ""

    def test_path_object(self):
        """测试Path对象"""
        assert get_ext(Path("test.txt")) == ".txt"


class TestGetStem:
    """get_stem函数测试"""

    def test_get_stem(self):
        """测试获取文件名（不含扩展名）"""
        assert get_stem("test.txt") == "test"
        assert get_stem("document.pdf") == "document"
        assert get_stem("archive.tar.gz") == "archive.tar"

    def test_no_extension(self):
        """测试无扩展名文件"""
        assert get_stem("filename") == "filename"
        assert get_stem("path/to/file") == "file"

    def test_path_object(self):
        """测试Path对象"""
        assert get_stem(Path("test.txt")) == "test"


class TestIntegration:
    """集成测试"""

    def test_write_read_cycle(self):
        """测试写入读取循环"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "cycle.txt"
            original_content = "测试内容\n第二行"

            # 写入
            write_result = safe_write(temp_path, original_content)
            assert write_result is True

            # 读取
            read_content = safe_read(temp_path)
            assert read_content == original_content

    def test_directory_and_file_operations(self):
        """测试目录和文件操作组合"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建目录
            work_dir = ensure_dir(Path(temp_dir) / "work")
            assert work_dir.exists()

            # 写入文件
            file_path = work_dir / "data.txt"
            safe_write(file_path, "数据")

            # 检查存在
            assert safe_exists(file_path) is True

            # 获取文件信息
            assert get_ext(file_path) == ".txt"
            assert get_stem(file_path) == "data"

            # 读取验证
            content = safe_read(file_path)
            assert content == "数据"


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_string_path(self):
        """测试空字符串路径"""
        result = safe_exists("")
        # 空字符串可能被解析为当前目录，不应该抛出异常
        assert isinstance(result, bool)

    def test_special_characters_in_filename(self):
        """测试文件名中的特殊字符"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 使用常见特殊字符
            filename = "test_file-123.txt"
            temp_path = Path(temp_dir) / filename
            result = safe_write(temp_path, "content")
            assert result is True
            assert temp_path.exists()

    def test_unicode_filename(self):
        """测试Unicode文件名"""
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = "测试文件.txt"
            temp_path = Path(temp_dir) / filename
            result = safe_write(temp_path, "内容")
            assert result is True
            assert temp_path.exists()
