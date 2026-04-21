"""
小娜专业智能体模块

该模块将小娜拆分为多个专业智能体，每个智能体专注于特定领域。
通过小诺的动态编排，可以根据业务场景灵活组合这些智能体。

智能体列表：
- Phase 1: RetrieverAgent, AnalyzerAgent, WriterAgent
- Phase 2: PlannerAgent, RuleAgent
- Phase 3: PolisherAgent, TranslatorAgent
"""

from core.agents.xiaona.base_component import BaseXiaonaComponent
from core.agents.xiaona.retriever_agent import RetrieverAgent
from core.agents.xiaona.analyzer_agent import AnalyzerAgent
from core.agents.xiaona.writer_agent import WriterAgent

__all__ = [
    "BaseXiaonaComponent",
    "RetrieverAgent",
    "AnalyzerAgent",
    "WriterAgent",
]

# 版本信息
__version__ = "1.0.0"
__phase__ = 1  # 当前实现的阶段
