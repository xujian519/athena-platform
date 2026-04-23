#!/usr/bin/env python3
"""
小诺协调代理 - Xiaonuo Coordination Agent
平台总调度官，负责协调所有智能体

本文件作为桥接层，连接core/framework与services/intelligent-collaboration
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import sys

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "services" / "intelligent-collaboration"))


class XiaonuoAgent:
    """
    小诺协调代理

    职责：
    - 协调小娜的9个专业代理
    - 任务分发与调度
    - 资源管理与分配
    - 结果聚合与反馈

    特点：
    - 轻量级桥接层
    - 不包含复杂业务逻辑
    - 委托给services/intelligent-collaboration
    """

    def __init__(self):
        """初始化小诺协调代理"""
        self._xiaonuo_main = None
        self._initialized = False

    def _ensure_initialized(self):
        """延迟初始化小诺主程序"""
        if not self._initialized:
            try:
                # 动态导入xiaonuo_main
                from xiaonuo_main import XiaonuoMain
                self._xiaonuo_main = XiaonuoMain()
                self._initialized = True
            except ImportError as e:
                print(f"⚠️  小诺主程序导入失败: {e}")
                print("💡 提示: 小诺协调功能暂时不可用，但不会影响其他代理")
                self._xiaonuo_main = None

    async def coordinate_agents(
        self,
        task: str,
        agents: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        协调多个智能体完成任务

        Args:
            task: 任务描述
            agents: 需要调用的代理列表
            context: 任务上下文

        Returns:
            任务执行结果
        """
        self._ensure_initialized()

        if self._xiaonuo_main is None:
            return {
                "status": "degraded",
                "message": "小诺协调功能暂时不可用，请手动调用代理",
                "task": task,
                "agents": agents
            }

        # 委托给小诺主程序
        try:
            result = await self._xiaonuo_main.coordinate_task(task, agents, context)
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"协调失败: {str(e)}",
                "task": task,
                "agents": agents
            }

    async def route_to_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        路由任务到指定代理

        Args:
            agent_name: 代理名称（如xiaona-retriever）
            task: 任务描述
            context: 任务上下文

        Returns:
            代理执行结果
        """

        # 查找代理类
        agent_map = {
            "retriever": "retriever_agent.RetrieverAgent",
            "analyzer": "analyzer_agent.AnalyzerAgent",
            "writer": "unified_patent_writer.UnifiedPatentWriter",
            "novelty": "novelty_analyzer_proxy.NoveltyAnalyzerProxy",
            "creativity": "creativity_analyzer_proxy.CreativityAnalyzerProxy",
            "infringement": "infringement_analyzer_proxy.InfringementAnalyzerProxy",
            "invalidation": "invalidation_analyzer_proxy.InvalidationAnalyzerProxy",
            "application_reviewer": "application_reviewer_proxy.ApplicationDocumentReviewerProxy",
            "writing_reviewer": "writing_reviewer_proxy.WritingReviewerProxy",
        }

        if agent_name not in agent_map:
            return {
                "status": "error",
                "message": f"未知代理: {agent_name}",
                "available_agents": list(agent_map.keys())
            }

        # 动态加载代理
        try:
            module_path, class_name = agent_map[agent_name].rsplit('.', 1)
            module = __import__(
                f"core.framework.agents.xiaona.{module_path}",
                fromlist=[module_path]
            )
            agent_class = getattr(module, class_name)
            agent = agent_class()

            # 执行任务
            result = await agent.process(task, context or {})
            return {
                "status": "success",
                "agent": agent_name,
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"代理调用失败: {str(e)}",
                "agent": agent_name
            }

    async def get_status(self) -> Dict[str, Any]:
        """获取小诺协调代理状态"""
        self._ensure_initialized()

        status = {
            "agent_id": "xiaonuo-coordinator",
            "agent_type": "coordinator",
            "initialized": self._initialized,
            "xiaonuo_main_available": self._xiaonuo_main is not None
        }

        if self._xiaonuo_main is not None:
            # 获取小诺主程序状态
            try:
                xiaonuo_status = await self._xiaonuo_main.get_status()
                status.update(xiaonuo_status)
            except:
                pass

        return status

    def get_available_agents(self) -> List[str]:
        """获取可用的代理列表"""
        return [
            "xiaona-retriever",
            "xiaona-analyzer",
            "xiaona-writer",
            "xiaona-novelty",
            "xiaona-creativity",
            "xiaona-infringement",
            "xiaona-invalidation",
            "xiaona-application_reviewer",
            "xiaona-writing_reviewer",
        ]



# 便捷函数
async def create_xiaonuo_agent() -> str:
    """创建小诺协调代理实例"""
    return XiaonuoAgent()


# 导出
__all__ = [
    "XiaonuoAgent",
    "create_xiaonuo_agent",
]


