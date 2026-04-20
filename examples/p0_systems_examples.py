#!/usr/bin/env python3
"""
P0系统实战示例集

展示Skills、Plugins和会话记忆系统在真实场景中的应用。

作者: Athena平台团队
创建时间: 2026-04-21
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry
from core.skills.tool_mapper import SkillToolMapper
from core.plugins.loader import PluginLoader as PluginLoader
from core.plugins.registry import PluginRegistry
from core.memory.sessions.manager import SessionManager
from core.memory.sessions.storage import FileSessionStorage
from core.memory.sessions.types import MessageRole

logger = logging.getLogger(__name__)


# 示例1：专利分析工作流
class PatentAnalysisWorkflow:
    """专利分析工作流

    展示如何使用Skills和会话记忆系统完成专利分析任务。
    """

    def __init__(self):
        """初始化工作流"""
        # 初始化Skills系统
        self.skill_registry = SkillRegistry()
        self.skill_loader = SkillLoader(self.skill_registry)
        self.skill_loader.load_from_directory("core/skills/bundled")

        # 初始化会话记忆系统
        self.session_manager = SessionManager(
            storage=FileSessionStorage("data/sessions")
        )

        logger.info("✅ 专利分析工作流初始化完成")

    def analyze_patent(
        self,
        patent_id: str,
        user_id: str,
        session_id: str,
    ) -> Dict[str, any]:
        """分析专利

        Args:
            patent_id: 专利ID
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            dict: 分析结果
        """
        # 1. 创建或获取会话
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(
                session_id=session_id,
                user_id=user_id,
                agent_id="xiaona",
            )

        # 2. 用户请求
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=f"请分析专利 {patent_id} 的创造性",
            token_count=20,
        )

        # 3. 选择技能
        skill = self.skill_registry.get_skill("patent_analysis")
        if not skill:
            return {"error": "技能不可用"}

        # 4. 执行技能（简化实现）
        result = {
            "patent_id": patent_id,
            "skill_used": skill.id,
            "analysis": {
                "novelty": "具有创造性",
                "inventiveness": "高度",
                "industrial_applicability": "良好",
            },
            "confidence": 0.85,
        }

        # 5. 添加助手消息
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=f"根据 {skill.name}，专利 {patent_id} 的创造性分析如下：\n"
                    f"- 新颖性：{result['analysis']['novelty']}\n"
                    f"- 创造性：{result['analysis']['inventiveness']}\n"
                    f"- 工业实用性：{result['analysis']['industrial_applicability']}\n"
                    f"置信度：{result['confidence']}",
            token_count=150,
        )

        # 6. 返回结果
        return result


# 示例2：多轮对话管理
class MultiTurnDialogueManager:
    """多轮对话管理器

    展示如何使用会话记忆系统管理多轮对话。
    """

    def __init__(self):
        """初始化管理器"""
        self.session_manager = SessionManager(
            storage=FileSessionStorage("data/sessions")
        )

        # 初始化Skills系统
        self.skill_registry = SkillRegistry()
        loader = SkillLoader(self.skill_registry)
        loader.load_from_directory("core/skills/bundled")

        logger.info("✅ 多轮对话管理器初始化完成")

    def chat(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ) -> str:
        """处理对话

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息

        Returns:
            str: 助手回复
        """
        # 1. 获取或创建会话
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(
                session_id=session_id,
                user_id=user_id,
                agent_id="xiaona",
            )

        # 2. 添加用户消息
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=message,
            token_count=len(message.split()),
        )

        # 3. 获取对话历史
        history = self.session_manager.get_session_messages(
            session_id,
            count=10,
        )

        # 4. 生成回复（简化实现）
        if len(history) <= 1:
            response = "您好！我是小娜，请问有什么可以帮助您的？"
        else:
            # 根据历史上下文生成回复
            response = f"我理解您的需求。让我继续为您服务。"

        # 5. 添加助手消息
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response,
            token_count=len(response.split()),
        )

        return response

    def get_session_summary(self, session_id: str) -> Dict[str, any]:
        """获取会话摘要

        Args:
            session_id: 会话ID

        Returns:
            dict: 会话摘要
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}

        return {
            "session_id": session_id,
            "user_id": session.context.user_id,
            "message_count": session.context.message_count,
            "total_tokens": session.context.total_tokens,
            "duration": (
                datetime.now() - session.context.start_time
            ).total_seconds(),
        }


# 示例3：技能协调器
class SkillCoordinator:
    """技能协调器

    展示如何协调多个技能完成复杂任务。
    """

    def __init__(self):
        """初始化协调器"""
        self.skill_registry = SkillRegistry()
        loader = SkillLoader(self.skill_registry)
        loader.load_from_directory("core/skills/bundled")

        # 初始化工具映射器
        self.tool_mapper = SkillToolMapper(self.skill_registry)

        logger.info("✅ 技能协调器初始化完成")

    def coordinate_task(
        self,
        task_description: str,
        user_id: str,
        session_id: str,
    ) -> Dict[str, any]:
        """协调任务执行

        Args:
            task_description: 任务描述
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            dict: 执行结果
        """
        # 1. 分析任务，确定需要的技能
        required_skills = self._analyze_task(task_description)

        # 2. 检查技能可用性
        available_skills = []
        for skill_id in required_skills:
            skill = self.skill_registry.get_skill(skill_id)
            if skill and skill.is_enabled():
                available_skills.append(skill)

        if not available_skills:
            return {"error": "没有可用的技能"}

        # 3. 检查工具冲突
        conflicts = self.tool_mapper.detect_tool_conflicts()
        if conflicts:
            logger.warning(f"⚠️ 检测到工具冲突: {conflicts}")

        # 4. 执行技能
        results = []
        for skill in available_skills:
            result = {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "tools_used": skill.tools,
                "status": "completed",
            }
            results.append(result)

        return {
            "task": task_description,
            "skills_used": [s["skill_id"] for s in results],
            "results": results,
            "conflicts": conflicts,
        }

    def _analyze_task(self, task_description: str) -> List[str]:
        """分析任务，返回需要的技能ID

        Args:
            task_description: 任务描述

        Returns:
            list[str]: 技能ID列表
        """
        required_skills = []

        # 简单的关键词匹配
        if "专利" in task_description:
            if "分析" in task_description:
                required_skills.append("patent_analysis")
            elif "检索" in task_description:
                required_skills.append("case_retrieval")
        elif "案例" in task_description:
            if "检索" in task_description or "搜索" in task_description:
                required_skills.append("case_retrieval")
        elif "文书" in task_description:
            required_skills.append("document_writing")

        # 如果没有匹配，使用协调技能
        if not required_skills:
            required_skills.append("task_coordination")

        return required_skills


# 示例4：性能监控
class PerformanceMonitor:
    """性能监控器

    展示如何监控P0系统的性能指标。
    """

    def __init__(self):
        """初始化监控器"""
        self.metrics = {
            "skill_operations": [],
            "plugin_operations": [],
            "session_operations": [],
        }
        logger.info("✅ 性能监控器初始化完成")

    def monitor_skill_loading(self, registry: SkillRegistry):
        """监控技能加载性能"""
        import time

        start = time.time()
        skills = registry.list_skills()
        elapsed = time.time() - start

        self.metrics["skill_operations"].append({
            "operation": "list_skills",
            "count": len(skills),
            "elapsed": elapsed,
        })

        logger.info(f"📊 技能查询性能: {elapsed*1000:.2f}ms ({len(skills)} 个技能)")

        return elapsed

    def monitor_plugin_loading(self, registry: PluginRegistry):
        """监控插件加载性能"""
        import time

        start = time.time()
        plugins = registry.list_plugins()
        elapsed = time.time() - start

        self.metrics["plugin_operations"].append({
            "operation": "list_plugins",
            "count": len(plugins),
            "elapsed": elapsed,
        })

        logger.info(f"📊 插件查询性能: {elapsed*1000:.2f}ms ({len(plugins)} 个插件)")

        return elapsed

    def monitor_session_operations(self, manager: SessionManager):
        """监控会话操作性能"""
        import time

        # 测试添加100条消息的性能
        start = time.time()
        session = manager.create_session("perf_test", "user", "agent")
        for i in range(100):
            manager.add_message(
                "perf_test",
                MessageRole.USER,
                f"Message {i}",
                token_count=5,
            )
        elapsed = time.time() - start

        self.metrics["session_operations"].append({
            "operation": "add_100_messages",
            "elapsed": elapsed,
        })

        logger.info(f"📊 会话操作性能: {elapsed*1000:.2f}ms (100条消息)")

        return elapsed

    def get_performance_report(self) -> Dict[str, any]:
        """获取性能报告

        Returns:
            dict: 性能报告
        """
        def calculate_stats(operations):
            if not operations:
                return {"avg": 0, "min": 0, "max": 0}

            values = [op["elapsed"] for op in operations]
            return {
                "count": len(operations),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }

        return {
            "skills": calculate_stats(self.metrics["skill_operations"]),
            "plugins": calculate_stats(self.metrics["plugin_operations"]),
            "sessions": calculate_stats(self.metrics["session_operations"]),
        }


# 示例5：完整的Agent实现
class CompleteAgent:
    """完整的Agent实现

    集成了Skills、Plugins和会话记忆系统的智能Agent。
    """

    def __init__(self, name: str, agent_id: str):
        """初始化Agent

        Args:
            name: Agent名称
            agent_id: Agent ID
        """
        self.name = name
        self.agent_id = agent_id

        # 初始化所有系统
        self._init_skills()
        self._init_plugins()
        self._init_sessions()

        logger.info(f"✅ {self.name} 初始化完成")

    def _init_skills(self):
        """初始化Skills系统"""
        self.skill_registry = SkillRegistry()
        loader = SkillLoader(self.skill_registry)
        loader.load_from_directory("core/skills/bundled")

    def _init_plugins(self):
        """初始化Plugins系统"""
        self.plugin_registry = PluginRegistry()
        loader = PluginLoader(self.plugin_registry)
        loader.load_from_directory("core/plugins/bundled")

    def _init_sessions(self):
        """初始化会话记忆系统"""
        self.session_manager = SessionManager(
            storage=FileSessionStorage("data/sessions")
        )

    def process(
        self,
        user_input: str,
        session_id: str,
        user_id: str,
    ) -> str:
        """处理用户请求

        Args:
            user_input: 用户输入
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            str: 响应
        """
        # 1. 获取或创建会话
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(
                session_id=session_id,
                user_id=user_id,
                agent_id=self.agent_id,
            )

        # 2. 添加用户消息
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_input,
            token_count=len(user_input.split()),
        )

        # 3. 分析意图并选择技能
        skill = self._select_skill(user_input)

        # 4. 生成响应
        if skill:
            response = self._execute_skill(skill, user_input)
        else:
            response = "我理解您的请求，但暂时无法处理。"

        # 5. 添加助手消息
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response,
            token_count=len(response.split()),
        )

        return response

    def _select_skill(self, user_input: str) -> Optional[str]:
        """选择技能

        Args:
            user_input: 用户输入

        Returns:
            str | None: 技能ID
        """
        # 简单的关键词匹配
        if "专利" in user_input and "分析" in user_input:
            return "patent_analysis"
        elif "案例" in user_input and ("检索" in user_input or "搜索" in user_input):
            return "case_retrieval"
        elif "文书" in user_input:
            return "document_writing"
        else:
            return None

    def _execute_skill(self, skill_id: str, user_input: str) -> str:
        """执行技能

        Args:
            skill_id: 技能ID
            user_input: 用户输入

        Returns:
            str: 执行结果
        """
        skill = self.skill_registry.get_skill(skill_id)
        if not skill:
            return "技能不可用"

        # 简化实现：返回技能描述
        return f"根据 {skill.name}，针对您的请求：{user_input}，我已完成相应处理。"

    def get_system_stats(self) -> Dict[str, any]:
        """获取系统统计信息

        Returns:
            dict: 统计信息
        """
        skill_stats = self.skill_registry.get_stats()
        plugin_stats = self.plugin_registry.get_stats()
        session_stats = self.session_manager.get_session_stats()

        return {
            "skills": skill_stats,
            "plugins": plugin_stats,
            "sessions": session_stats,
        }


# 主函数
def main():
    """主函数 - 运行所有示例"""
    print("=" * 70)
    print("P0系统实战示例")
    print("=" * 70)

    # 示例1：专利分析工作流
    print("\n📊 示例1：专利分析工作流")
    print("-" * 70)

    workflow = PatentAnalysisWorkflow()
    result = workflow.analyze_patent(
        patent_id="CN123456789A",
        user_id="user123",
        session_id="patent_session_001",
    )
    print(f"分析结果: {result}")

    # 示例2：多轮对话管理
    print("\n💬 示例2：多轮对话管理")
    print("-" * 70)

    dialogue_manager = MultiTurnDialogueManager()

    # 第一轮对话
    response1 = dialogue_manager.chat(
        user_id="user456",
        session_id="chat_session_001",
        message="你好",
    )
    print(f"用户: 你好")
    print(f"小娜: {response1}")

    # 第二轮对话
    response2 = dialogue_manager.chat(
        user_id="user456",
        session_id="chat_session_001",
        message="帮我分析专利",
    )
    print(f"用户: 帮我分析专利")
    print(f"小娜: {response2}")

    # 获取会话摘要
    summary = dialogue_manager.get_session_summary("chat_session_001")
    print(f"\n会话摘要: 消息数={summary['message_count']}, "
          f"tokens={summary['total_tokens']}, "
          f"时长={summary['duration']:.1f}秒")

    # 示例3：技能协调
    print("\n🎯 示例3：技能协调")
    print("-" * 70)

    coordinator = SkillCoordinator()
    result = coordinator.coordinate_task(
        task_description="分析专利CN123456789A的创造性并检索相关案例",
        user_id="user789",
        session_id="coord_session_001",
    )
    print(f"任务: {result['task']}")
    print(f"使用的技能: {result['skills_used']}")
    print(f"执行结果: {len(result['results'])} 个技能已完成")

    # 示例4：性能监控
    print("\n⚡ 示例4：性能监控")
    print("-" * 70)

    monitor = PerformanceMonitor()

    # 监控技能系统
    monitor.monitor_skill_loading(workflow.skill_registry)

    # 创建插件注册表用于监控
    plugin_registry = PluginRegistry()
    plugin_loader = PluginLoader(plugin_registry)
    plugin_loader.load_from_directory("core/plugins/bundled")

    # 监控插件系统
    monitor.monitor_plugin_loading(plugin_registry)

    # 监控会话系统
    monitor.monitor_session_operations(workflow.session_manager)

    # 获取性能报告
    report = monitor.get_performance_report()
    print("\n性能报告:")
    print(f"  技能操作: {report['skills']['count']} 次, "
          f"平均 {report['skills']['avg']*1000:.2f}ms")
    print(f"  插件操作: {report['plugins']['count']} 次, "
          f"平均 {report['plugins']['avg']*1000:.2f}ms")
    print(f"  会话操作: {report['sessions']['count']} 次, "
          f"平均 {report['sessions']['avg']*1000:.2f}ms")

    print("\n" + "=" * 70)
    print("✅ 所有示例运行完成！")
    print("=" * 70)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 运行示例
    main()
