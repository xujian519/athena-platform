#!/usr/bin/env python3
from __future__ import annotations
"""
Hermes Agent 设计模式集成配置

提供新模块的集成接口和配置。

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ========================================
# 集成状态检查
# ========================================

INTEGRATION_STATUS = {
    # P0 优先级
    "toolsets": {
        "module": "core.tools.toolsets",
        "status": "implemented",
        "integrated_with": "core.tools.tool_manager",
        "integration_method": "ToolsetManager.auto_select_toolset()",
    },
    "smart_model_routing": {
        "module": "core.llm.smart_model_routing",
        "status": "implemented",
        "integrated_with": "core.llm.unified_llm_manager",
        "integration_method": "SmartModelRouter.route_request()",
    },
    "context_compressor": {
        "module": "core.context.context_compressor",
        "status": "enhanced",
        "enhancements": [
            "LEGAL_KEYWORDS 法律关键词识别",
            "FrozenSnapshot 冻结快照",
            "_score_legal_importance() 法律重要性评分",
        ],
    },
    # P1 优先级
    "unified_registry": {
        "module": "core.tools.registry",
        "status": "implemented",
        "integration_method": "@register_tool() 装饰器",
    },
    "persistent_memory": {
        "module": "core.memory.persistent_memory.manager",
        "status": "implemented",
        "storage": "MEMORY.md + USER.md",
    },
    "cron_scheduler": {
        "module": "core.scheduling.cron_scheduler",
        "status": "implemented",
        "features": ["自然语言调度", "任务持久化", "专利状态监控"],
    },
    "session_search": {
        "module": "core.search.session_search",
        "status": "implemented",
        "features": ["语义搜索", "关键词搜索", "混合搜索", "跨会话引用"],
    },
    "subagent_delegation": {
        "module": "core.collaboration.subagent_delegation",
        "status": "implemented",
        "features": ["隔离上下文并行执行", "结果聚合", "最多3个子代理"],
    },
    "platform_adapter": {
        "module": "core.prompts.platform_adapter",
        "status": "implemented",
        "platforms": ["Claude", "GPT", "GLM", "DeepSeek", "Qwen"],
    },
}


def get_integration_status() -> dict[str, Any]:
    """
    获取所有集成状态

    Returns:
        dict: 集成状态信息
    """
    return {
        "total_modules": len(INTEGRATION_STATUS),
        "implemented": sum(
            1 for m in INTEGRATION_STATUS.values() if m["status"] in ("implemented", "enhanced")
        ),
        "details": INTEGRATION_STATUS,
    }


def check_integration_health() -> dict[str, bool]:
    """
    检查所有模块的健康状态

    Returns:
        dict: 模块导入状态
    """
    health_status = {}

    for name, config in INTEGRATION_STATUS.items():
        try:
            module_path = config["module"]
            parts = module_path.rsplit(".", 1)
            if len(parts) == 2:
                package, clazz = parts
                module = __import__(package, fromlist=[clazz])
                getattr(module, clazz.split(".")[0])
            else:
                __import__(module_path)
            health_status[name] = True
        except (ImportError, AttributeError):
            health_status[name] = False

    return health_status


# ========================================
# 快速集成指南
# ========================================

INTEGRATION_GUIDES = {
    "smart_model_routing": """
# 智能模型路由集成指南

from core.llm.smart_model_routing import SmartModelRouter
from core.llm.base import LLMRequest

# 初始化路由器
router = SmartModelRouter()

# 路由请求
request = LLMRequest(message="分析这个专利的新颖性", task_type="novelty_analysis")
decision = await router.route_request(request)

print(f"选择的模型: {decision.selected_model}")
print(f"复杂度分数: {decision.complexity_score}")
print(f"节省成本: ¥{decision.cost_saved}")
""",
    "toolsets": """
# 工具集集成指南

from core.tools.toolsets import ToolsetManager

# 初始化管理器
manager = ToolsetManager()

# 自动选择工具集
toolset = await manager.auto_select_toolset("检索关于人工智能的专利")
print(f"选择的工具集: {toolset.display_name if toolset else 'None'}")

# 获取工具集的 OpenAI schema
schemas = toolset.to_openai_schema()
""",
    "subagent_delegation": """
# 子代理委托集成指南

from core.collaboration.subagent_delegation import (
    SubagentDelegationManager,
    SubagentTask,
    TaskPriority,
)

# 初始化管理器
manager = SubagentDelegationManager(max_concurrent=3)

# 创建子任务
task1 = manager.create_task(
    name="专利检索",
    description="检索相关专利",
    task_type="patent_search",
    priority=TaskPriority.HIGH,
)

# 委托执行
result = await manager.delegate(
    parent_task="专利分析",
    subtasks=[task1],
    aggregation_strategy="combine",
)
""",
    "session_search": """
# 会话搜索集成指南

from core.search.session_search import get_session_search_engine

# 获取搜索引擎
engine = get_session_search_engine()

# 创建会话
session = engine.create_session(name="专利分析讨论")

# 添加消息
engine.add_message(session.session_id, "user", "请帮我分析这个专利的新颖性")

# 搜索历史
results = engine.search("新颖性分析", mode="hybrid", limit=10)
""",
    "cron_scheduler": """
# Cron 调度集成指南

from core.scheduling.cron_scheduler import get_cron_scheduler

# 获取调度器
scheduler = get_cron_scheduler()

# 创建任务（支持自然语言）
task = scheduler.schedule_task(
    task_id="daily_patent_check",
    name="每日专利状态检查",
    description="检查专利状态变化",
    schedule="每天早上",  # 自然语言: "0 9 * * *"
    task_type="patent_status_check",
    parameters={"patent_ids": ["CN123456", "CN789012"]},
)

# 启动调度器
await scheduler.start()
""",
}


def get_integration_guide(module_name: str) -> str | None:
    """
    获取模块的集成指南

    Args:
        module_name: 模块名称

    Returns:
        str | None: 集成指南
    """
    return INTEGRATION_GUIDES.get(module_name)


__all__ = [
    "INTEGRATION_STATUS",
    "INTEGRATION_GUIDES",
    "check_integration_health",
    "get_integration_guide",
    "get_integration_status",
]
