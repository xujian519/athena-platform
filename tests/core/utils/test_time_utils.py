#!/usr/bin/env python3
"""
时间处理工具模块单元测试
"""

from datetime import datetime, timedelta

from core.utils.time_utils import (
    add_days,
    add_hours,
    add_minutes,
    add_seconds,
    now_iso,
    now_str,
    parse_time,
)


class TestNowStr:
    """now_str函数测试"""

    def test_default_format(self):
        """测试默认格式"""
        result = now_str()
        assert isinstance(result, str)
        assert len(result) == 19  # "YYYY-MM-DD HH:MM:SS"

    def test_custom_format(self):
        """测试自定义格式"""
        result = now_str("%Y-%m-%d")
        assert len(result) == 10  # "YYYY-MM-DD"

    def test_year_format(self):
        """测试年份格式"""
        result = now_str("%Y")
        assert result.isdigit()
        assert len(result) == 4

    def test_time_format(self):
        """测试时间格式"""
        result = now_str("%H:%M:%S")
        assert ":" in result


class TestNowIso:
    """now_iso函数测试"""

    def test_iso_format(self):
        """测试ISO格式"""
        result = now_iso()
        assert isinstance(result, str)
        assert "T" in result  # ISO格式包含T

    def test_iso_parsing(self):
        """测试ISO格式可解析"""
        result = now_iso()
        parsed = datetime.fromisoformat(result)
        assert isinstance(parsed, datetime)


class TestParseTime:
    """parse_time函数测试"""

    def test_parse_valid_time(self):
        """测试解析有效时间"""
        time_str = "2026-04-21 12:00:00"
        result = parse_time(time_str)
        assert result is not None
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 21

    def test_parse_custom_format(self):
        """测试解析自定义格式"""
        time_str = "2026/04/21"
        result = parse_time(time_str, fmt="%Y/%m/%d")
        assert result is not None
        assert result.year == 2026

    def test_parse_invalid_time(self):
        """测试解析无效时间"""
        result = parse_time("invalid time")
        assert result is None

    def test_parse_empty_string(self):
        """测试解析空字符串"""
        result = parse_time("")
        assert result is None

    def test_parse_none(self):
        """测试解析None"""
        result = parse_time(None)
        assert result is None

    def test_parse_wrong_format(self):
        """测试错误格式"""
        result = parse_time("2026-04-21", fmt="%Y/%m/%d")
        assert result is None


class TestAddSeconds:
    """add_seconds函数测试"""

    def test_add_positive_seconds(self):
        """测试添加正秒数"""
        before = datetime.now()
        result = add_seconds(30)
        after = datetime.now()

        assert result >= before + timedelta(seconds=30)
        assert result <= after + timedelta(seconds=30)

    def test_add_negative_seconds(self):
        """测试添加负秒数"""
        before = datetime.now()
        result = add_seconds(-30)

        # 结果应该比当前时间早
        assert result < before

    def test_add_zero_seconds(self):
        """测试添加0秒"""
        before = datetime.now()
        result = add_seconds(0)
        after = datetime.now()

        assert result >= before
        assert result <= after


class TestAddMinutes:
    """add_minutes函数测试"""

    def test_add_positive_minutes(self):
        """测试添加正分钟数"""
        before = datetime.now()
        result = add_minutes(5)
        after = datetime.now()

        assert result >= before + timedelta(minutes=5)
        assert result <= after + timedelta(minutes=5)

    def test_add_negative_minutes(self):
        """测试添加负分钟数"""
        before = datetime.now()
        result = add_minutes(-5)

        # 结果应该比当前时间早
        assert result < before

    def test_add_zero_minutes(self):
        """测试添加0分钟"""
        before = datetime.now()
        result = add_minutes(0)
        after = datetime.now()

        assert result >= before
        assert result <= after


class TestAddHours:
    """add_hours函数测试"""

    def test_add_positive_hours(self):
        """测试添加正小时数"""
        before = datetime.now()
        result = add_hours(2)
        after = datetime.now()

        assert result >= before + timedelta(hours=2)
        assert result <= after + timedelta(hours=2)

    def test_add_negative_hours(self):
        """测试添加负小时数"""
        before = datetime.now()
        result = add_hours(-2)

        # 结果应该比当前时间早
        assert result < before

    def test_add_zero_hours(self):
        """测试添加0小时"""
        before = datetime.now()
        result = add_hours(0)
        after = datetime.now()

        assert result >= before
        assert result <= after


class TestAddDays:
    """add_days函数测试"""

    def test_add_positive_days(self):
        """测试添加正天数"""
        before = datetime.now()
        result = add_days(7)
        after = datetime.now()

        assert result >= before + timedelta(days=7)
        assert result <= after + timedelta(days=7)

    def test_add_negative_days(self):
        """测试添加负天数"""
        before = datetime.now()
        result = add_days(-7)

        # 结果应该比当前时间早
        assert result < before

    def test_add_zero_days(self):
        """测试添加0天"""
        before = datetime.now()
        result = add_days(0)
        after = datetime.now()

        assert result >= before
        assert result <= after


class TestIntegration:
    """集成测试"""

    def test_time_workflow(self):
        """测试时间工作流"""
        # 获取当前时间字符串
        time_str = now_str()
        assert isinstance(time_str, str)

        # 解析时间字符串
        parsed = parse_time(time_str)
        assert parsed is not None

        # 添加时间
        future = add_days(1)
        assert future > parsed

    def test_iso_workflow(self):
        """测试ISO格式工作流"""
        # 获取ISO格式时间
        iso_time = now_iso()
        assert "T" in iso_time

        # 解析ISO时间
        parsed = datetime.fromisoformat(iso_time)
        assert isinstance(parsed, datetime)

    def test_calculation_chain(self):
        """测试计算链"""
        # 当前时间
        datetime.now()

        # 添加各种时间
        t1 = add_seconds(30)
        t2 = add_minutes(5)
        t3 = add_hours(2)
        t4 = add_days(1)

        # 验证时间递增
        assert t4 > t3 > t2 > t1


class TestEdgeCases:
    """边缘情况测试"""

    def test_large_values(self):
        """测试大数值"""
        # 添加大量天数
        result = add_days(365)
        assert isinstance(result, datetime)

        # 添加大量秒数
        result = add_seconds(86400)  # 1天
        assert isinstance(result, datetime)

    def test_negative_large_values(self):
        """测试大负数值"""
        # 减去大量天数
        result = add_days(-365)
        assert isinstance(result, datetime)

    def test_fractional_not_supported(self):
        """测试不支持小数（函数参数是int）"""
        # 这些函数接受int，所以传入浮点数会失败或被转换
        result = add_days(1.5)  # 类型提示是int，但Python允许float
        assert isinstance(result, datetime)
