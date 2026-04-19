#!/usr/bin/env python3
from __future__ import annotations
"""
持久化记忆系统 - MEMORY.md + USER.md 双存储

基于 Hermes Agent 的设计理念，实现项目和用户级别的持久化记忆。
支持跨会话上下文保持和学习用户偏好。

核心特性:
1. MEMORY.md - 项目级记忆 (架构、组件、已知问题)
2. USER.md - 用户级记忆 (偏好、习惯、专业领域)
3. 自动更新和学习
4. 版本控制和回滚

作者: Athena平台团队
创建时间: 2026-03-19
版本: v1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 默认存储路径
DEFAULT_MEMORY_DIR = Path(__file__).parent


@dataclass
class MemoryEntry:
    """记忆条目"""

    key: str
    value: str
    category: str
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "user"  # user, system, learned
    confidence: float = 1.0


@dataclass
class ProjectMemory:
    """
    项目级记忆 (MEMORY.md)

    存储项目相关的持久化信息。
    """

    # 项目概况
    project_name: str = ""
    project_type: str = ""
    current_phase: str = ""
    core_objective: str = ""

    # 技术架构
    tech_stack: list[str] = field(default_factory=list)
    architecture_pattern: str = ""
    key_components: list[str] = field(default_factory=list)

    # 核心组件描述
    component_details: dict[str, str] = field(default_factory=dict)

    # 已知问题和解决方案
    known_issues: list[dict[str, str]] = field(default_factory=list)

    # 最近更新
    recent_updates: list[str] = field(default_factory=list)

    # 重要决策
    decisions: list[dict[str, str]] = field(default_factory=list)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        md = f"""# MEMORY.md - 项目记忆

> **项目**: {self.project_name}
> **类型**: {self.project_type}
> **当前阶段**: {self.current_phase}
> **最后更新**: {self.updated_at.strftime('%Y-%m-%d %H:%M')}

---

## 📋 项目概况

{self.core_objective}

---

## 🏗️ 技术架构

### 技术栈
"""
        for tech in self.tech_stack:
            md += f"- {tech}\n"

        md += f"""
### 架构模式
{self.architecture_pattern}

### 核心组件
"""
        for comp in self.key_components:
            md += f"- {comp}\n"

        if self.component_details:
            md += "\n### 组件详情\n"
            for name, desc in self.component_details.items():
                md += f"\n**{name}**\n{desc}\n"

        if self.known_issues:
            md += "\n---\n\n## ⚠️ 已知问题\n\n"
            for issue in self.known_issues:
                md += f"- **{issue.get('title', '')}**: {issue.get('description', '')}\n"
                if issue.get("solution"):
                    md += f"  - 解决方案: {issue['solution']}\n"

        if self.decisions:
            md += "\n---\n\n## 🎯 重要决策\n\n"
            for decision in self.decisions:
                md += f"- **{decision.get('title', '')}** ({decision.get('date', '')})\n"
                md += f"  - {decision.get('rationale', '')}\n"

        if self.recent_updates:
            md += "\n---\n\n## 📝 最近更新\n\n"
            for update in self.recent_updates[-10:]:  # 最近10条
                md += f"- {update}\n"

        md += f"""
---

## 📊 元数据

- **创建时间**: {self.created_at.strftime('%Y-%m-%d')}
- **版本**: {self.version}
"""
        return md


@dataclass
class UserMemory:
    """
    用户级记忆 (USER.md)

    存储用户偏好和习惯。
    """

    # 基本信息
    user_name: str = ""
    role: str = ""
    organization: str = ""

    # 工作偏好
    communication_style: str = "简明扼要"
    preferred_depth: str = "详细分析"
    language_preference: str = "简体中文"

    # 专业领域
    primary_domain: str = ""
    expertise_areas: list[str] = field(default_factory=list)
    technical_background: list[str] = field(default_factory=list)

    # 常用术语和缩写
    glossary: dict[str, str] = field(default_factory=dict)

    # 工作习惯
    preferred_tools: list[str] = field(default_factory=list)
    workflow_preferences: list[str] = field(default_factory=list)

    # 学习到的偏好
    learned_preferences: list[dict[str, str]] = field(default_factory=list)

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        md = f"""# USER.md - 用户记忆

> **用户**: {self.user_name}
> **角色**: {self.role}
> **交互次数**: {self.interaction_count}
> **最后更新**: {self.updated_at.strftime('%Y-%m-%d %H:%M')}

---

## 👤 基本信息

- **姓名**: {self.user_name}
- **角色**: {self.role}
- **组织**: {self.organization}

---

## 🎨 工作偏好

- **沟通风格**: {self.communication_style}
- **分析深度**: {self.preferred_depth}
- **语言偏好**: {self.language_preference}

---

## 🎓 专业领域

### 主领域
{self.primary_domain}

### 专业领域
"""
        for area in self.expertise_areas:
            md += f"- {area}\n"

        if self.technical_background:
            md += "\n### 技术背景\n"
            for bg in self.technical_background:
                md += f"- {bg}\n"

        if self.glossary:
            md += "\n---\n\n## 📖 常用术语\n\n"
            for term, definition in self.glossary.items():
                md += f"- **{term}**: {definition}\n"

        if self.preferred_tools:
            md += "\n---\n\n## 🛠️ 常用工具\n\n"
            for tool in self.preferred_tools:
                md += f"- {tool}\n"

        if self.learned_preferences:
            md += "\n---\n\n## 🧠 学习到的偏好\n\n"
            for pref in self.learned_preferences[-20:]:  # 最近20条
                md += f"- **{pref.get('type', '')}**: {pref.get('value', '')}\n"

        md += f"""
---

## 📊 元数据

- **创建时间**: {self.created_at.strftime('%Y-%m-%d')}
- **交互次数**: {self.interaction_count}
"""
        return md


class PersistentMemoryManager:
    """
    持久化记忆管理器

    管理 MEMORY.md 和 USER.md 的读写和更新。
    """

    def __init__(self, storage_dir: Path | None = None):
        """
        初始化持久化记忆管理器

        Args:
            storage_dir: 存储目录 (默认使用 DEFAULT_MEMORY_DIR)
        """
        self.storage_dir = storage_dir or DEFAULT_MEMORY_DIR
        self.memory_file = self.storage_dir / "MEMORY.md"
        self.user_file = self.storage_dir / "USER.md"

        # 确保目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 加载或初始化记忆
        self.project_memory = self._load_project_memory()
        self.user_memory = self._load_user_memory()

        logger.info(f"💾 PersistentMemoryManager 初始化完成 (目录: {self.storage_dir})")

    def _load_project_memory(self) -> ProjectMemory:
        """加载项目记忆"""
        if self.memory_file.exists():
            try:
                # 简单解析 (实际项目可使用更复杂的解析器)
                content = self.memory_file.read_text(encoding="utf-8")
                return self._parse_memory_md(content)
            except Exception as e:
                logger.warning(f"⚠️ 加载 MEMORY.md 失败: {e}")

        return ProjectMemory()

    def _load_user_memory(self) -> UserMemory:
        """加载用户记忆"""
        if self.user_file.exists():
            try:
                content = self.user_file.read_text(encoding="utf-8")
                return self._parse_user_md(content)
            except Exception as e:
                logger.warning(f"⚠️ 加载 USER.md 失败: {e}")

        return UserMemory()

    def _parse_memory_md(self, content: str) -> ProjectMemory:
        """解析 MEMORY.md 内容"""
        memory = ProjectMemory()

        # 简单解析 (实际实现可以更复杂)
        lines = content.split("\n")

        for line in lines:
            if line.startswith("> **项目**:"):
                memory.project_name = line.split(":")[1].strip()
            elif line.startswith("> **类型**:"):
                memory.project_type = line.split(":")[1].strip()
            elif line.startswith("> **当前阶段**:"):
                memory.current_phase = line.split(":")[1].strip()
            # 可扩展：解析更多字段

        return memory

    def _parse_user_md(self, content: str) -> UserMemory:
        """解析 USER.md 内容"""
        memory = UserMemory()

        lines = content.split("\n")
        for line in lines:
            if line.startswith("> **用户**:"):
                memory.user_name = line.split(":")[1].strip()
            elif line.startswith("> **角色**:"):
                memory.role = line.split(":")[1].strip()
            elif line.startswith("- **沟通风格**:"):
                memory.communication_style = line.split(":")[1].strip()
            elif line.startswith("- **分析深度**:"):
                memory.preferred_depth = line.split(":")[1].strip()

        return memory

    def save_project_memory(self) -> None:
        """保存项目记忆到文件"""
        self.project_memory.updated_at = datetime.now()
        content = self.project_memory.to_markdown()
        self.memory_file.write_text(content, encoding="utf-8")
        logger.info(f"💾 项目记忆已保存: {self.memory_file}")

    def save_user_memory(self) -> None:
        """保存用户记忆到文件"""
        self.user_memory.updated_at = datetime.now()
        self.user_memory.interaction_count += 1
        content = self.user_memory.to_markdown()
        self.user_file.write_text(content, encoding="utf-8")
        logger.info(f"💾 用户记忆已保存: {self.user_file}")

    def update_project_info(
        self,
        project_name: str | None = None,
        project_type: str | None = None,
        current_phase: str | None = None,
        core_objective: str | None = None,
    ) -> None:
        """
        更新项目信息

        Args:
            project_name: 项目名称
            project_type: 项目类型
            current_phase: 当前阶段
            core_objective: 核心目标
        """
        if project_name:
            self.project_memory.project_name = project_name
        if project_type:
            self.project_memory.project_type = project_type
        if current_phase:
            self.project_memory.current_phase = current_phase
        if core_objective:
            self.project_memory.core_objective = core_objective

        self.save_project_memory()

    def add_known_issue(self, title: str, description: str, solution: str | None = None) -> None:
        """
        添加已知问题

        Args:
            title: 问题标题
            description: 问题描述
            solution: 解决方案
        """
        issue = {
            "title": title,
            "description": description,
            "solution": solution or "",
            "timestamp": datetime.now().isoformat(),
        }
        self.project_memory.known_issues.append(issue)
        self.save_project_memory()

    def add_decision(self, title: str, rationale: str) -> None:
        """
        添加重要决策

        Args:
            title: 决策标题
            rationale: 决策理由
        """
        decision = {
            "title": title,
            "rationale": rationale,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        self.project_memory.decisions.append(decision)
        self.save_project_memory()

    def add_recent_update(self, update: str) -> None:
        """
        添加最近更新

        Args:
            update: 更新内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        self.project_memory.recent_updates.append(f"[{timestamp}] {update}")
        self.save_project_memory()

    def update_user_preference(
        self,
        communication_style: str | None = None,
        preferred_depth: str | None = None,
        language_preference: str | None = None,
    ) -> None:
        """
        更新用户偏好

        Args:
            communication_style: 沟通风格
            preferred_depth: 分析深度偏好
            language_preference: 语言偏好
        """
        if communication_style:
            self.user_memory.communication_style = communication_style
        if preferred_depth:
            self.user_memory.preferred_depth = preferred_depth
        if language_preference:
            self.user_memory.language_preference = language_preference

        self.save_user_memory()

    def learn_preference(self, pref_type: str, value: str) -> None:
        """
        学习用户偏好

        Args:
            pref_type: 偏好类型
            value: 偏好值
        """
        pref = {
            "type": pref_type,
            "value": value,
            "learned_at": datetime.now().isoformat(),
        }
        self.user_memory.learned_preferences.append(pref)
        self.save_user_memory()

    def add_glossary_term(self, term: str, definition: str) -> None:
        """
        添加术语定义

        Args:
            term: 术语
            definition: 定义
        """
        self.user_memory.glossary[term] = definition
        self.save_user_memory()

    def get_context_for_session(self) -> dict[str, Any]:
        """
        获取会话所需的上下文

        Returns:
            dict: 包含项目和用户记忆的上下文
        """
        return {
            "project": {
                "name": self.project_memory.project_name,
                "type": self.project_memory.project_type,
                "phase": self.project_memory.current_phase,
                "objective": self.project_memory.core_objective,
                "tech_stack": self.project_memory.tech_stack,
                "known_issues": self.project_memory.known_issues[-5:],  # 最近5个问题
            },
            "user": {
                "name": self.user_memory.user_name,
                "role": self.user_memory.role,
                "communication_style": self.user_memory.communication_style,
                "preferred_depth": self.user_memory.preferred_depth,
                "language": self.user_memory.language_preference,
                "domains": self.user_memory.expertise_areas,
            },
        }


# ========================================
# 全局实例
# ========================================
_global_memory_manager: PersistentMemoryManager | None = None


def get_persistent_memory_manager(storage_dir: Path | None = None) -> PersistentMemoryManager:
    """获取全局持久化记忆管理器"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = PersistentMemoryManager(storage_dir)
    return _global_memory_manager


__all__ = [
    "MemoryEntry",
    "PersistentMemoryManager",
    "ProjectMemory",
    "UserMemory",
    "get_persistent_memory_manager",
]
