#!/usr/bin/env python3

"""
小娜专利命名系统 - 向后兼容重定向
Xiaona Patent Naming System - Backward Compatibility Redirect

⚠️  此文件已重构，所有功能已迁移到新位置

新位置: core.cognition.xiaona_patent_naming_system (模块化目录)

迁移指南:
------------------------------------------------------
旧导入方式:
    from core.cognition.xiaona_patent_naming_system import (
        XiaonaPatentNamingSystem,
        PatentType,
        PatentNamingRequest,
        PatentNamingResult,
    )

新导入方式:
    from core.cognition.xiaona_patent_naming_system import (
        XiaonaPatentNamingSystem,
        PatentType,
        NamingStyle,
        PatentNamingRequest,
        PatentNamingResult,
    )
------------------------------------------------------

完整的迁移指南请参考: MIGRATION_GUIDE.md
"""

import warnings

# 导入重构后的模块
from .xiaona_patent_naming_system import (
    NamingStyle,
    PatentNamingRequest,
    PatentNamingResult,
    PatentType,
    XiaonaPatentNamingSystem,
)

# 发出弃用警告
warnings.warn(
    "xiaona_patent_naming_system.py 已重构为模块化目录 "
    "core.cognition.xiaona_patent_naming_system/。"
    "请更新您的导入语句。详细信息请参考 MIGRATION_GUIDE.md",
    DeprecationWarning,
    stacklevel=2,
)

# 导出公共接口以保持向后兼容
__all__ = [
    "PatentType",
    "NamingStyle",
    "PatentNamingRequest",
    "PatentNamingResult",
    "XiaonaPatentNamingSystem",
]

