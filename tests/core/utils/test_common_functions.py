#!/usr/bin/env python3
"""
通用工具函数集合单元测试
"""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from core.utils.common_functions import (
    # 日志相关
    get_logger,
    setup_basic_logger,
    # 时间相关
    get_timestamp,
    get_timestamp_iso,
    current_time,
    now,
    # 文件路径相关
    ensure_dir,
    mkdir,
    file_exists,
    # JSON相关
    read_json,
    load_json,
    write_json,
    save_json,
    # 配置相关
    load_config,
    save_config,
    # 字符串相关
    sanitize_filename,
    truncate,
    # 验证相关
    is_empty,
    is_not_empty,
)


class TestLoggingFunctions:
    """日志相关函数测试"""

    def test_get_logger_with_name(self):
        """测试获取命名logger"""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_without_name(self):
        """测试获取默认logger"""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)

    def test_get_logger_same_instance(self):
        """测试获取相同名称的logger是同一实例"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2

    def test_setup_basic_logger(self):
        """测试设置基础日志"""
        # 清除已有的handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # 设置基础日志
        setup_basic_logger(logging.INFO)

        # 验证handlers已添加
        assert len(root_logger.handlers) > 0

        # 清理
        root_logger.handlers.clear()


class TestTimeFunctions:
    """时间相关函数测试"""

    def test_get_timestamp_default(self):
        """测试获取默认格式时间戳"""
        result = get_timestamp()
        assert isinstance(result, str)
        assert len(result) == 19  # "YYYY-MM-DD HH:MM:SS"

    def test_get_timestamp_custom_format(self):
        """测试获取自定义格式时间戳"""
        result = get_timestamp("%Y-%m-%d")
        assert len(result) == 10

    def test_get_timestamp_iso(self):
        """测试获取ISO格式时间戳"""
        result = get_timestamp_iso()
        assert isinstance(result, str)
        assert "T" in result

    def test_current_time(self):
        """测试获取当前时间"""
        result = current_time()
        assert isinstance(result, datetime)

    def test_now(self):
        """测试now函数（别名）"""
        result = now()
        assert isinstance(result, datetime)

    def test_time_functions_consistency(self):
        """测试时间函数一致性"""
        t1 = current_time()
        t2 = now()
        assert type(t1) == type(t2)


class TestPathFunctions:
    """文件路径相关函数测试"""

    def test_ensure_dir_new(self):
        """测试创建新目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new" / "nested" / "dir"
            result = ensure_dir(new_dir)
            assert result == new_dir
            assert new_dir.exists()
            assert new_dir.is_dir()

    def test_ensure_dir_existing(self):
        """测试确保已存在的目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            existing_dir = Path(temp_dir) / "existing"
            existing_dir.mkdir()

            result = ensure_dir(existing_dir)
            assert result == existing_dir
            assert existing_dir.exists()

    def test_mkdir_alias(self):
        """测试mkdir别名"""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "test"
            result = mkdir(new_dir)
            assert result == new_dir
            assert new_dir.exists()

    def test_file_exists_true(self):
        """测试文件存在"""
        with tempfile.NamedTemporaryFile() as f:
            assert file_exists(f.name) is True

    def test_file_exists_false(self):
        """测试文件不存在"""
        assert file_exists("/nonexistent/file.txt") is False

    def test_file_exists_with_path_object(self):
        """测试使用Path对象"""
        with tempfile.NamedTemporaryFile() as f:
            path = Path(f.name)
            assert file_exists(path) is True


class TestJsonFunctions:
    """JSON相关函数测试"""

    def test_read_json_existing(self):
        """测试读取存在的JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = f.name

        try:
            result = read_json(temp_path)
            assert result == {"key": "value"}
        finally:
            Path(temp_path).unlink()

    def test_read_json_nonexistent(self):
        """测试读取不存在的JSON文件"""
        result = read_json("/nonexistent/file.json")
        assert result == {}  # 默认返回空字典

    def test_read_json_with_default(self):
        """测试读取带默认值"""
        result = read_json("/nonexistent/file.json", default=None)
        # 当文件不存在且default=None时，函数返回{}（见实现）
        assert result == {}

    def test_read_json_invalid_json(self):
        """测试读取无效JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json")
            temp_path = f.name

        try:
            result = read_json(temp_path)
            assert result == {}  # 解析失败返回空字典
        finally:
            Path(temp_path).unlink()

    def test_load_json_alias(self):
        """测试load_json别名"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            result = load_json(temp_path)
            assert result == {"test": "data"}
        finally:
            Path(temp_path).unlink()

    def test_write_json_new_file(self):
        """测试写入新JSON文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.json"
            result = write_json(temp_path, {"key": "value"})
            assert result is True
            assert temp_path.exists()

            # 验证内容
            with open(temp_path) as f:
                loaded = json.load(f)
            assert loaded == {"key": "value"}

    def test_write_json_nested_directory(self):
        """测试写入嵌套目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "nested" / "dir" / "test.json"
            result = write_json(temp_path, {"key": "value"})
            assert result is True
            assert temp_path.exists()

    def test_write_json_with_indent(self):
        """测试写入带缩进的JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.json"
            write_json(temp_path, {"key": "value"}, indent=4)

            content = temp_path.read_text()
            assert "    " in content  # 4空格缩进

    def test_save_json_alias(self):
        """测试save_json别名"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.json"
            result = save_json(temp_path, {"key": "value"})
            assert result is True

    def test_json_roundtrip(self):
        """测试JSON读写往返"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.json"
            original_data = {"key": "value", "number": 123, "list": [1, 2, 3]}

            # 写入
            write_json(temp_path, original_data)

            # 读取
            loaded_data = read_json(temp_path)

            # 验证
            assert loaded_data == original_data


class TestConfigFunctions:
    """配置相关函数测试"""

    def test_load_config(self):
        """测试加载配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"setting": "value"}, f)
            temp_path = f.name

        try:
            result = load_config(temp_path)
            assert result == {"setting": "value"}
        finally:
            Path(temp_path).unlink()

    def test_load_config_nonexistent(self):
        """测试加载不存在的配置"""
        result = load_config("/nonexistent/config.json")
        assert result == {}

    def test_save_config(self):
        """测试保存配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "config.json"
            config = {"setting": "value"}

            result = save_config(temp_path, config)
            assert result is True

            # 验证
            loaded = load_config(temp_path)
            assert loaded == config


class TestStringFunctions:
    """字符串相关函数测试"""

    def test_sanitize_filename_basic(self):
        """测试基本文件名清理"""
        result = sanitize_filename("test<>file")
        assert result == "test__file"

    def test_sanitize_filename_all_invalid_chars(self):
        """测试所有非法字符"""
        result = sanitize_filename('file/:*?"<>|name')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_sanitize_filename_custom_replacement(self):
        """测试自定义替换字符"""
        result = sanitize_filename("test<file>", replacement="-")
        assert result == "test-file-"

    def test_sanitize_filename_strip_dots(self):
        """测试移除首尾点"""
        result = sanitize_filename("...test...")
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_sanitize_filename_strip_spaces(self):
        """测试移除首尾空格"""
        result = sanitize_filename("  test  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_sanitize_filename_too_long(self):
        """测试过长文件名截断"""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_sanitize_filename_empty_result(self):
        """测试清理所有非法字符后的结果"""
        result = sanitize_filename("<<<>>>")
        # 所有<和>都被替换为_，所以返回"______"
        assert result == "______"
        assert is_not_empty(result)

    def test_truncate_short_text(self):
        """测试截断短文本（不截断）"""
        result = truncate("short")
        assert result == "short"

    def test_truncate_long_text(self):
        """测试截断长文本"""
        result = truncate("a" * 200, max_length=100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_truncate_custom_suffix(self):
        """测试自定义后缀"""
        result = truncate("a" * 200, max_length=100, suffix=" [more]")
        assert len(result) == 100
        assert result.endswith(" [more]")

    def test_truncate_exact_length(self):
        """测试正好等于最大长度"""
        text = "a" * 100
        result = truncate(text, max_length=100)
        assert result == text


class TestValidationFunctions:
    """验证相关函数测试"""

    def test_is_empty_none(self):
        """测试None为空"""
        assert is_empty(None) is True

    def test_is_empty_string(self):
        """测试空字符串"""
        assert is_empty("") is True

    def test_is_empty_list(self):
        """测试空列表"""
        assert is_empty([]) is True

    def test_is_empty_dict(self):
        """测试空字典"""
        assert is_empty({}) is True

    def test_is_empty_tuple(self):
        """测试空元组"""
        assert is_empty(()) is True

    def test_is_empty_set(self):
        """测试空集合"""
        assert is_empty(set()) is True

    def test_is_not_empty_string(self):
        """测试非空字符串"""
        assert is_empty("text") is False

    def test_is_not_empty_list(self):
        """测试非空列表"""
        assert is_empty([1]) is False

    def test_is_not_empty_zero(self):
        """测试0不为空"""
        assert is_empty(0) is False

    def test_is_not_empty_false(self):
        """测试False不为空"""
        assert is_empty(False) is False

    def test_is_not_empty_function(self):
        """测试is_not_empty"""
        assert is_not_empty("text") is True
        assert is_not_empty("") is False
        assert is_not_empty(None) is False


class TestIntegration:
    """集成测试"""

    def test_config_workflow(self):
        """测试配置工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"

            # 保存配置
            config = {"key": "value", "number": 123}
            save_config(config_path, config)

            # 加载配置
            loaded = load_config(config_path)

            # 验证
            assert loaded == config

    def test_json_workflow_with_validation(self):
        """测试JSON工作流带验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "data.json"

            # 写入数据
            data = {"items": [1, 2, 3], "count": 3}
            write_json(json_path, data)

            # 读取并验证
            loaded = read_json(json_path)
            assert is_not_empty(loaded)
            assert loaded["count"] == len(loaded["items"])

    def test_file_workflow(self):
        """测试文件操作工作流"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建目录
            work_dir = ensure_dir(Path(temp_dir) / "work")

            # 检查存在
            assert file_exists(work_dir)

            # 创建文件
            file_path = work_dir / "data.json"
            write_json(file_path, {"test": "data"})

            # 验证文件存在
            assert file_exists(file_path)

    def test_logging_workflow(self):
        """测试日志工作流"""
        # 设置日志
        setup_basic_logger(logging.INFO)

        # 获取logger
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

        # 清理
        logging.getLogger().handlers.clear()

    def test_string_and_validation_workflow(self):
        """测试字符串和验证工作流"""
        # 清理文件名
        filename = sanitize_filename("test<>file")
        assert is_not_empty(filename)

        # 验证长度
        assert is_not_empty(truncate("a" * 300, max_length=100))


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_json_file(self):
        """测试空JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{}")
            temp_path = f.name

        try:
            result = read_json(temp_path)
            assert result == {}
        finally:
            Path(temp_path).unlink()

    def test_json_array(self):
        """测试JSON数组"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "array.json"
            data = [1, 2, 3, 4, 5]

            write_json(temp_path, data)
            loaded = read_json(temp_path)

            assert loaded == data

    def test_nested_json(self):
        """测试嵌套JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "nested.json"
            data = {
                "level1": {
                    "level2": {
                        "level3": "value"
                    }
                }
            }

            write_json(temp_path, data)
            loaded = read_json(temp_path)

            assert loaded == data

    def test_unicode_filename(self):
        """测试Unicode文件名"""
        filename = "测试文件<>name"
        result = sanitize_filename(filename)
        assert is_not_empty(result)
        assert "<" not in result
        assert ">" not in result

    def test_special_chars_in_json(self):
        """测试JSON中的特殊字符"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "special.json"
            data = {
                "chinese": "中文",
                "emoji": "😀",
                "special": "\n\t"
            }

            write_json(temp_path, data)
            loaded = read_json(temp_path)

            assert loaded["chinese"] == "中文"
            assert loaded["emoji"] == "😀"
