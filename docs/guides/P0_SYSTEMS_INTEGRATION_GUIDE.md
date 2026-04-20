# P0系统集成指南

**版本**: 1.0.0
**更新日期**: 2026-04-21
**适用对象**: Agent开发者

---

## 📚 目录

1. [系统概览](#系统概览)
2. [集成架构](#集成架构)
3. [完整示例](#完整示例)
4. [最佳实践](#最佳实践)
5. [性能优化](#性能优化)
6. [故障排查](#故障排查)

---

## 系统概览

P0阶段完成的三个核心系统：

| 系统 | 功能 | 核心价值 |
|------|------|---------|
| **Skills系统** | 能力组织 | 将Agent能力组织为可重用的技能模块 |
| **Plugins系统** | 功能扩展 | 动态加载和管理插件（Agent/Tool） |
| **会话记忆系统** | 状态管理 | 管理Agent的会话状态和记忆持久化 |

### 协作关系

```
┌─────────────────────────────────────────────────────┐
│                    Agent                             │
│                 (小娜/小诺/云熙)                       │
└─────────────────────────────────────────────────────┘
         │                    │                    │
         ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Skills系统   │    │ Plugins系统  │    │ 会话记忆系统 │
│ (能力组织)   │    │ (功能扩展)   │    │ (状态管理)   │
└──────────────┘    └──────────────┘    └──────────────┘
         │                    │                    │
         ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────┐
│              Tools + 四层记忆系统                     │
└─────────────────────────────────────────────────────┘
```

---

## 集成架构

### 三层架构

```
┌──────────────────────────────────────────────────┐
│                  Agent层                          │
│  - 选择技能                                       │
│  - 加载插件                                       │
│  - 管理会话                                       │
└──────────────────────────────────────────────────┘
         │                    │                    │
         ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Skills     │    │   Plugins    │    │  Sessions    │
│              │    │              │    │              │
│ - 定义能力   │    │ - 扩展功能   │    │ - 管理状态   │
│ - 组织工具   │    │ - 加载模块   │    │ - 存储消息   │
│ - 技能注册   │    │ - 插件管理   │    │ - 会话持久化 │
└──────────────┘    └──────────────┘    └──────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ↓
              ┌─────────────────────────┐
              │   Tools + 四层记忆        │
              │  - 工具注册和执行          │
              │  - HOT/WARM/COLD/ARCHIVE  │
              └─────────────────────────┘
```

### 数据流

```
用户请求
    ↓
Agent识别意图
    ↓
┌─────────────────────────────────────────┐
│ 1. Skills系统：选择相关技能             │
│    - 按类别/工具查找技能                │
│    - 验证技能可用性                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. Plugins系统：加载所需插件            │
│    - 检查插件依赖                       │
│    - 加载插件模块                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. 会话记忆系统：创建/恢复会话          │
│    - 创建新会话或恢复已有会话           │
│    - 记录请求和响应                     │
└─────────────────────────────────────────┘
    ↓
执行技能的工具
    ↓
返回结果并更新会话
```

---

## 完整示例

### 示例1：智能Agent集成

```python
#!/usr/bin/env python3
"""
P0系统集成示例 - 智能Agent

展示如何将Skills、Plugins和会话记忆系统集成到Agent中。

作者: Athena平台团队
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from core.skills.loader import SkillLoader
from core.skills.registry import SkillRegistry
from core.plugins.loader import PluginLoader as PluginLoader
from core.plugins.registry import PluginRegistry
from core.memory.sessions.manager import SessionManager
from core.memory.sessions.storage import FileSessionStorage
from core.memory.sessions.types import MessageRole

logger = logging.getLogger(__name__)


class IntegratedAgent:
    """集成Agent
    
    集成了Skills、Plugins和会话记忆系统的智能Agent。
    """
    
    def __init__(
        self,
        name: str,
        agent_id: str,
    ):
        """初始化Agent
        
        Args:
            name: Agent名称
            agent_id: Agent ID
        """
        self.name = name
        self.agent_id = agent_id
        
        # 初始化Skills系统
        self.skill_registry = SkillRegistry()
        self.skill_loader = SkillLoader(self.skill_registry)
        self._load_skills()
        
        # 初始化Plugins系统
        self.plugin_registry = PluginRegistry()
        self.plugin_loader = PluginLoader(self.plugin_registry)
        self._load_plugins()
        
        # 初始化会话记忆系统
        self.session_manager = SessionManager(
            storage=FileSessionStorage("data/sessions")
        )
        
        logger.info(f"✅ {self.name} 初始化完成")
    
    def _load_skills(self):
        """加载技能"""
        skills = self.skill_loader.load_from_directory("core/skills/bundled")
        logger.info(f"📚 加载了 {len(skills)} 个技能")
    
    def _load_plugins(self):
        """加载插件"""
        plugins = self.plugin_loader.load_from_directory("core/plugins/bundled")
        logger.info(f"📦 加载了 {len(plugins)} 个插件")
    
    def select_skill(self, task_description: str) -> str | None:
        """根据任务描述选择技能
        
        Args:
            task_description: 任务描述
            
        Returns:
            str | None: 技能ID
        """
        # 简单的关键词匹配
        if "专利" in task_description and "分析" in task_description:
            return "patent_analysis"
        elif "案例" in task_description and "检索" in task_description:
            return "case_retrieval"
        elif "文书" in task_description:
            return "document_writing"
        elif "协调" in task_description:
            return "task_coordination"
        
        # 默认返回协调技能
        return "task_coordination"
    
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
            logger.info(f"🆕 创建新会话: {session_id}")
        
        # 2. 添加用户消息到会话
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.USER,
            content=user_input,
            token_count=len(user_input.split()),
        )
        
        # 3. 选择技能
        skill_id = self.select_skill(user_input)
        if not skill_id:
            return "抱歉，我不理解您的请求。"
        
        # 4. 获取技能
        skill = self.skill_registry.get_skill(skill_id)
        if not skill:
            return f"技能 {skill_id} 不可用。"
        
        # 5. 执行技能（这里简化处理）
        logger.info(f"🎯 使用技能: {skill.name}")
        response = self._execute_skill(skill, user_input)
        
        # 6. 添加助手消息到会话
        self.session_manager.add_message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=response,
            token_count=len(response.split()),
        )
        
        return response
    
    def _execute_skill(
        self,
        skill,
        user_input: str,
    ) -> str:
        """执行技能（简化实现）
        
        Args:
            skill: 技能定义
            user_input: 用户输入
            
        Returns:
            str: 执行结果
        """
        # 这里应该实际执行技能的工具
        # 简化实现：返回模拟响应
        
        if skill.id == "patent_analysis":
            return f"我将为您分析专利。根据您的要求：{user_input}，我需要检索相关专利文献并进行创造性评估。"
        elif skill.id == "case_retrieval":
            return f"我将为您检索相关案例。基于：{user_input}，我会在案例数据库中搜索相似判决。"
        elif skill.id == "document_writing":
            return f"我将为您撰写法律文书。根据：{user_input}，我会生成符合要求的文档。"
        else:
            return f"我已收到您的请求：{user_input}，正在处理中..."
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 会话信息
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}
        
        return {
            "session_id": session.context.session_id,
            "user_id": session.context.user_id,
            "agent_id": session.context.agent_id,
            "status": session.context.status.value,
            "message_count": session.context.message_count,
            "total_tokens": session.context.total_tokens,
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            dict: 统计信息
        """
        skill_stats = self.skill_registry.get_stats()
        plugin_stats = self.plugin_registry.get_stats()
        session_stats = self.session_manager.get_session_stats()
        
        return {
            "skills": {
                "total": skill_stats["total_skills"],
                "by_category": skill_stats["by_category"],
            },
            "plugins": {
                "total": plugin_stats["total_plugins"],
                "by_type": plugin_stats["by_type"],
                "by_status": plugin_stats["by_status"],
            },
            "sessions": {
                "total": session_stats["total_sessions"],
                "active": session_stats["active_sessions"],
                "total_messages": session_stats["total_messages"],
                "total_tokens": session_stats["total_tokens"],
            },
        }


# 使用示例
def demo_integrated_agent():
    """演示集成Agent"""
    print("=" * 60)
    print("P0系统集成示例")
    print("=" * 60)
    
    # 创建Agent
    agent = IntegratedAgent(
        name="小娜",
        agent_id="xiaona",
    )
    
    # 模拟对话
    session_id = "demo_session_001"
    user_id = "user123"
    
    # 第一轮对话
    print("\n📝 用户: 帮我分析专利CN123456789A的创造性")
    response1 = agent.process(
        user_input="帮我分析专利CN123456789A的创造性",
        session_id=session_id,
        user_id=user_id,
    )
    print(f"🤖 {agent.name}: {response1}")
    
    # 第二轮对话
    print("\n📝 用户: 再帮我检索相关案例")
    response2 = agent.process(
        user_input="再帮我检索相关案例",
        session_id=session_id,
        user_id=user_id,
    )
    print(f"🤖 {agent.name}: {response2}")
    
    # 查看会话信息
    session_info = agent.get_session_info(session_id)
    print(f"\n📊 会话信息:")
    print(f"  会话ID: {session_info['session_id']}")
    print(f"  用户ID: {session_info['user_id']}")
    print(f"  消息数: {session_info['message_count']}")
    print(f"  Token数: {session_info['total_tokens']}")
    
    # 查看系统统计
    stats = agent.get_system_stats()
    print(f"\n📈 系统统计:")
    print(f"  技能总数: {stats['skills']['total']}")
    print(f"  插件总数: {stats['plugins']['total']}")
    print(f"  会话总数: {stats['sessions']['total']}")
    print(f"  活跃会话: {stats['sessions']['active']}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # 运行演示
    demo_integrated_agent()
