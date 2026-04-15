#!/usr/bin/env python3
"""Input Validator Module"""

from __future__ import annotations
from typing import Any


class InputValidator:
    """输入验证器"""

    def validate(self, data: Any) -> bool:
        """验证输入数据"""
        return True

def get_input_validator() -> InputValidator:
    """获取输入验证器实例"""
    return InputValidator()
