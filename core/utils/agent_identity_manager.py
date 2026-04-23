#!/usr/bin/env python3
from __future__ import annotations
"""
智能体身份信息管理器
Agent Identity Manager

负责统一管理所有智能体的身份信息和展示功能
"""

import json
from pathlib import Path
from typing import Any


class AgentIdentityManager:
    """智能体身份信息管理器"""

    def __init__(self):
        self.config_path = (
            Path(__file__).parent.parent.parent / "config" / "agents_identity_config.json"
        )
        self.identity_config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """加载身份配置"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            # 如果配置文件不存在,返回默认配置
            return {
                "agents_identity": {},
                "display_settings": {
                    "show_on_startup": True,
                    "show_slogan": True,
                    "show_port": True,
                    "show_role": True,
                },
            }

    def get_agent_identity(self, agent_key: str) -> Optional[dict[str, Any]]:
        """获取智能体身份信息"""
        return self.identity_config.get("agents_identity", {}).get(agent_key)

    def display_agent_startup(self, agent_key: str) -> str:
        """生成智能体启动时的身份展示信息"""
        agent = self.get_agent_identity(agent_key)
        if not agent:
            return f"⚠️ 未找到智能体 {agent_key} 的身份配置"

        settings = self.identity_config.get("display_settings", {})

        # 构建显示信息
        lines = []
        lines.append(
            f"\n{agent.get('color', '🤖')} {agent.get('full_name', agent.get('name', '未知'))}"
        )
        lines.append("=" * (len(agent.get("full_name", "")) + 3))

        if settings.get("show_role", True):
            lines.append(f"📋 角色:{agent.get('role', '未设定')}")
            lines.append(f"🏷️  称号:{agent.get('title', '未设定')}")

        if settings.get("show_port", True):
            lines.append(f"📍 端口:{agent.get('port', '未知')}")

        if settings.get("show_slogan", True):
            lines.append(f"💫 Slogan:{agent.get('slogan', '未设定')}")

        lines.append(f"✨ 座右铭:{agent.get('motto', '未设定')}")
        lines.append("")

        if agent.get("startup_message"):
            lines.append(f"💝 {agent.get('startup_message')}")

        lines.append("")

        return "\n".join(lines)

    def get_service_info(self, agent_key: str) -> dict[str, Any]:
        """获取用于API返回的服务信息"""
        agent = self.get_agent_identity(agent_key)
        if not agent:
            return {}

        return {
            "service": f"{agent.get('color', '')} {agent.get('full_name', '')} - {agent.get('title', '')}",
            "name": agent.get("name"),
            "role": agent.get("role"),
            "expert": f"我是{agent.get('name')},{agent.get('title', '')}",
            "slogan": agent.get("slogan"),
            "motto": agent.get("motto"),
            "version": "v2.0 Enhanced",
            "port": agent.get("port"),
            "message": agent.get("startup_message"),
            "capabilities": self._get_capabilities(agent.get("role", "")),
        }

    def _get_capabilities(self, role: str) -> list:
        """根据角色获取能力列表"""
        capability_map = {
            "平台总调度官": [
                "🎮 平台全量控制",
                "🤖 智能体调度管理",
                "📊 系统状态监控",
                "💬 对话交互",
                "💻 开发辅助",
                "🏠 生活管理",
                "🚀 资源调度优化",
            ],
            "知识产权法律专家": [
                "⚖️ 专利申请与保护",
                "📝 商标注册与维权",
                "©️ 版权登记与纠纷",
                "📋 法律文书起草",
                "🔍 法律风险预警",
            ],
            "自媒体运营专家": [
                "📝 内容创作策划",
                "🎬 视频制作指导",
                "📊 数据分析优化",
                "🚀 流量增长策略",
                "💬 社群运营管理",
            ],
            "YunPat IP管理专家": [
                "📋 IP组合管理",
                "🔍 专利监控预警",
                "📊 价值评估分析",
                "💰 维权费用优化",
                "🌐 全球IP布局",
            ],
        }

        return capability_map.get(role, ["💫 能力待定义"])


# 全局实例
identity_manager = AgentIdentityManager()


# 便捷函数
def display_identity(agent_key: str) -> str:
    """显示智能体身份"""
    return identity_manager.display_agent_startup(agent_key)


def get_service_info(agent_key: str) -> dict[str, Any]:
    """获取服务信息"""
    return identity_manager.get_service_info(agent_key)
