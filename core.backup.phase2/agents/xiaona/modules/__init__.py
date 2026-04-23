"""
小娜模块系统

该目录包含小娜智能代理的模块化组件，支持灵活的功能扩展和组合。

模块列表：
- drafting_module: 专利撰写相关功能
- response_module: 响应生成和格式化
- orchestration_module: 任务编排和协调
- utility_module: 通用工具函数

TODO: 实现各模块的具体功能
"""

# 导入模块类
from core.agents.xiaona.modules.drafting_module import PatentDraftingModule
from core.agents.xiaona.modules.response_module import ResponseModule
from core.agents.xiaona.modules.orchestration_module import OrchestrationModule
from core.agents.xiaona.modules.utility_module import UtilityModule

# 模块导出
__all__ = [
    "PatentDraftingModule",
    "ResponseModule",
    "OrchestrationModule",
    "UtilityModule",
]
