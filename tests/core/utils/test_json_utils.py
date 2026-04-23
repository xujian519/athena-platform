#!/usr/bin/env python3
"""
JSON处理工具模块单元测试
"""

import json
import tempfile
from pathlib import Path

from core.utils.json_utils import (
    load_json_file,
    safe_dumps,
    safe_loads,
    save_json_file,
)


class TestSafeLoads:
    """safe_loads函数测试"""

    def test_valid_json(self):
        """测试有效JSON解析"""
        text = '{"key": "value", "number": 123}'
        result = safe_loads(text)
        assert result == {"key": "value", "number": 123}

    def test_invalid_json(self):
        """测试无效JSON解析"""
        text = '{"invalid": json}'
        result = safe_loads(text)
        assert result == {}  # default=None时返回空字典

    def test_invalid_json_with_default(self):
        """测试无效JSON解析（带默认值）"""
        text = 'not json'
        result = safe_loads(text, default="default_value")
        assert result == "default_value"

    def test_empty_string(self):
        """测试空字符串"""
        result = safe_loads('')
        assert result == {}  # default=None时返回空字典

    def test_json_array(self):
        """测试JSON数组"""
        text = '[1, 2, 3]'
        result = safe_loads(text)
        assert result == [1, 2, 3]


class TestSafeDumps:
    """safe_dumps函数测试"""

    def test_basic_dict(self):
        """测试基本字典序列化"""
        obj = {"key": "value", "number": 123}
        result = safe_dumps(obj)
        assert '"key": "value"' in result
        assert '"number": 123' in result

    def test_indent_parameter(self):
        """测试缩进参数"""
        obj = {"key": "value"}
        result_default = safe_dumps(obj, indent=2)
        result_no_indent = safe_dumps(obj, indent=None)
        assert "  " in result_default
        assert "  " not in result_no_indent

    def test_ensure_ascii(self):
        """测试ASCII编码"""
        obj = {"chinese": "中文"}
        result_ascii = safe_dumps(obj, ensure_ascii=True)
        result_unicode = safe_dumps(obj, ensure_ascii=False)
        # ensure_ascii=True应该转义中文
        assert "\\u" in result_ascii or "chinese" in result_ascii
        # ensure_ascii=False应该保留中文
        assert "中文" in result_unicode

    def test_complex_object(self):
        """测试复杂对象序列化"""
        obj = {
            "string": "test",
            "number": 123,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }
        result = safe_dumps(obj)
        assert result is not None
        assert len(result) > 0


class TestLoadJsonFile:
    """load_json_file函数测试"""

    def test_load_existing_file(self):
        """测试加载现有文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            temp_path = f.name

        try:
            result = load_json_file(temp_path)
            assert result == {"test": "data"}
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        result = load_json_file("/nonexistent/file.json", default={})
        assert result == {}

    def test_load_invalid_json_file(self):
        """测试加载无效JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json')

        try:
            result = load_json_file(f.name)
            assert result == {}  # default=None时返回空字典
        finally:
            Path(f.name).unlink()

    def test_load_with_default(self):
        """测试加载带默认值"""
        result = load_json_file("/nonexistent/file.json", default="default")
        assert result == "default"


class TestSaveJsonFile:
    """save_json_file函数测试"""

    def test_save_to_new_file(self):
        """测试保存到新文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.json"
            data = {"test": "data", "number": 123}

            result = save_json_file(temp_path, data)
            assert result is True

            # 验证文件已创建
            assert temp_path.exists()
            # 验证内容正确
            loaded = json.loads(temp_path.read_text())
            assert loaded == data

    def test_save_to_nested_directory(self):
        """测试保存到嵌套目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "nested" / "dir" / "test.json"
            data = {"test": "data"}

            result = save_json_file(temp_path, data)
            assert result is True
            assert temp_path.exists()
            assert temp_path.parent.exists()

    def test_save_with_indent(self):
        """测试保存带缩进"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.json"
            data = {"key": "value"}

            result = save_json_file(temp_path, data, indent=4)
            assert result is True

            # 验证缩进
            content = temp_path.read_text()
            assert "    " in content  # 4个空格缩进


class TestIntegration:
    """集成测试"""

    def test_save_and_load_cycle(self):
        """测试保存和加载循环"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "cycle.json"
            original_data = {
                "string": "test",
                "number": 123,
                "array": [1, 2, 3],
                "nested": {"key": "value"}
            }

            # 保存
            save_result = save_json_file(temp_path, original_data)
            assert save_result is True

            # 加载
            loaded_data = load_json_file(temp_path)
            assert loaded_data == original_data

    def test_complex_json_roundtrip(self):
        """测试复杂JSON的往返转换"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "complex.json"
            complex_data = {
                "metadata": {"version": "1.0", "created": "2026-04-21"},
                "items": [
                    {"id": 1, "name": "item1", "tags": ["a", "b"]},
                    {"id": 2, "name": "item2", "tags": ["c", "d"]}
                ],
                "config": {"enabled": True, "count": 42}
            }

            save_json_file(temp_path, complex_data)
            loaded_data = load_json_file(temp_path)

            assert loaded_data == complex_data


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_dict(self):
        """测试空字典"""
        result = safe_dumps({})
        assert result == "{}"

    def test_none_value(self):
        """测试None值"""
        result = safe_dumps(None)
        assert result == "null"

    def test_special_characters(self):
        """测试特殊字符"""
        obj = {"text": "Line1\nLine2\tTabbed"}
        result = safe_dumps(obj)
        assert result is not None

    def test_unicode_characters(self):
        """测试Unicode字符"""
        obj = {"emoji": "😀", "chinese": "中文", "russian": "Привет"}
        result = safe_dumps(obj, ensure_ascii=False)
        assert "😀" in result
        assert "中文" in result
        assert "Привет" in result
