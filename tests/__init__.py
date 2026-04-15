#!/usr/bin/env python3
"""
智能体设计模式测试框架
Agentic Design Patterns Test Framework

此模块在测试包初始化时自动添加项目根目录到Python路径，
确保所有测试文件都能正确导入core模块。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径 - 确保在任何导入之前执行
_project_root = Path(__file__).parent.parent.resolve()
_str_project_root = str(_project_root)
if _str_project_root not in sys.path:
    sys.path.insert(0, _str_project_root)

# 添加production目录
_production_path = _project_root / "production"
if _production_path.exists() and str(_production_path) not in sys.path:
    sys.path.insert(0, str(_production_path))

__version__ = "1.0.0"
__author__ = "Athena Platform Team"
