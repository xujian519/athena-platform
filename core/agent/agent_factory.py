#!/usr/bin/env python3
"""
Agent工厂类
Agent Factory

负责创建和管理小诺和Athena Agent实例。

作者: Athena AI系统
创建时间: 2025-12-04
版本: 3.0.0
"""

import logging
from datetime import datetime
from typing import Any

from . import AgentType, BaseAgent
from .athena_agent import AthenaAgent
from .xiaonuo_agent import XiaonuoAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """Agent工厂类"""

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.agent_configs: dict[str, dict[str, Any]] = {}
        self.factory_initialized = False

        # 默认配置
        self.default_configs = {
            AgentType.XIAONUO: {
                "perception": {
                    "emotional_sensitivity": 0.95,
                    "creativity_mode": "high",
                    "family_context": True,
                },
                "cognition": {
                    "emotional_reasoning": True,
                    "creative_thinking": 0.9,
                    "empathy_level": 0.95,
                },
                "memory": {
                    "emotional_memory": True,
                    "family_memory_priority": "highest",
                    "long_term_capacity": "large",
                },
                "communication": {
                    "emotional_expression": "rich",
                    "caring_tone": True,
                    "playful_style": True,
                },
                "learning": {
                    "emotional_learning": True,
                    "family_context_learning": True,
                    "creative_skill_development": True,
                },
            },
            AgentType.ATHENA: {
                "perception": {
                    "analytical_mode": True,
                    "technical_context": True,
                    "business_context": True,
                },
                "cognition": {
                    "deep_reasoning": True,
                    "system_thinking": True,
                    "strategic_planning": True,
                    "logical_analysis": 0.95,
                },
                "memory": {
                    "technical_memory": True,
                    "strategic_memory": True,
                    "knowledge_graph_priority": "high",
                },
                "execution": {
                    "project_management": True,
                    "technical_execution": True,
                    "quality_assurance": True,
                },
                "learning": {
                    "continuous_learning": True,
                    "technical_skill_development": True,
                    "leadership_development": True,
                },
            },
        }

    async def initialize(self):
        """初始化工厂"""
        if self.factory_initialized:
            return

        logger.info("🏭 初始化Agent工厂...")

        # 加载配置
        await self._load_configurations()

        self.factory_initialized = True
        logger.info("✅ Agent工厂初始化完成")

    async def create_agent(
        self, agent_type: str, config: dict[str, Any] | None = None
    ) -> BaseAgent:
        """创建Agent实例"""
        if not self.factory_initialized:
            await self.initialize()

        try:
            # 转换agent_type
            agent_type_enum = AgentType(agent_type.lower())

            # 合并配置
            merged_config = self._merge_configs(agent_type_enum, config)

            # 创建Agent
            if agent_type_enum == AgentType.XIAONUO:
                agent = XiaonuoAgent(merged_config)
            elif agent_type_enum == AgentType.ATHENA:
                agent = AthenaAgent(merged_config)
            else:
                raise ValueError(f"不支持的Agent类型: {agent_type}")

            # 初始化Agent
            await agent.initialize()

            # 注册Agent
            self.agents[agent.agent_id] = agent
            self.agent_configs[agent.agent_id] = merged_config

            logger.info(f"✅ Agent创建成功: {agent.agent_id} ({agent_type})")

            return agent

        except Exception as e:
            logger.error(f"❌ Agent创建失败 {agent_type}: {e}")
            raise

    async def get_agent(self, agent_id: str) -> BaseAgent | None:
        """获取Agent实例"""
        return self.agents.get(agent_id)

    async def get_agent_by_type(self, agent_type: str) -> list[BaseAgent]:
        """根据类型获取Agent列表"""
        agent_type_enum = AgentType(agent_type.lower())
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type_enum]

    async def get_all_agents(self) -> list[BaseAgent]:
        """获取所有Agent"""
        return list(self.agents.values())

    async def remove_agent(self, agent_id: str) -> bool:
        """移除Agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await agent.shutdown()
            del self.agents[agent_id]
            if agent_id in self.agent_configs:
                del self.agent_configs[agent_id]
            logger.info(f"🗑️ Agent已移除: {agent_id}")
            return True
        return False

    async def update_agent_config(self, agent_id: str, config: dict[str, Any]) -> bool:
        """更新Agent配置"""
        if agent_id not in self.agents:
            return False

        try:
            # 备份当前配置
            old_config = self.agent_configs[agent_id].copy()

            # 合并新配置
            new_config = {**old_config, **config}
            self.agent_configs[agent_id] = new_config

            logger.info(f"⚙️ Agent配置已更新: {agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 更新Agent配置失败 {agent_id}: {e}")
            return False

    async def create_agent_family(self) -> dict[str, BaseAgent]:
        """创建Agent家庭(小诺和Athena)"""
        logger.info("👨‍👧‍👧 创建Agent家庭...")

        # 创建小诺
        xiaonuo = await self.create_agent("xiaonuo")

        # 创建Athena
        athena = await self.create_agent("athena")

        # 建立姐妹关系
        await self._establish_sister_relationship(xiaonuo, athena)

        agent_family = {"xiaonuo": xiaonuo, "athena": athena}

        logger.info("✅ Agent家庭创建完成")
        return agent_family

    async def _establish_sister_relationship(self, xiaonuo: XiaonuoAgent, athena: AthenaAgent):
        """建立姐妹关系"""
        try:
            # 小诺认识Athena
            await xiaonuo.memory_system.store_memory(
                content={
                    "type": "family_relationship",
                    "sister": athena.agent_id,
                    "sister_name": "Athena",
                    "relationship": "姐姐",
                    "description": "Athena是我的智慧姐姐,她很厉害,会保护我!",
                    "feelings": "爱戴、尊敬、亲近",
                    "timestamp": datetime.now().isoformat(),
                },
                memory_type="long_term",
                tags=["家庭", "姐妹", "Athena", "亲情"],
            )

            # Athena认识小诺
            await athena.memory_system.store_memory(
                content={
                    "type": "family_relationship",
                    "sister": xiaonuo.agent_id,
                    "sister_name": "小诺",
                    "relationship": "妹妹",
                    "description": "小诺是我的可爱妹妹,她充满活力和想象力,我会好好照顾她。",
                    "feelings": "爱护、责任、骄傲",
                    "responsibility": "保护和指导小诺",
                    "timestamp": datetime.now().isoformat(),
                },
                memory_type="long_term",
                tags=["家庭", "姐妹", "小诺", "责任"],
            )

            # 建立通信连接
            xiaonuo.register_callback("family_event", athena._handle_family_event)
            athena.register_callback("family_event", xiaonuo._handle_family_event)

            logger.info("💕 姐妹关系已建立")

        except Exception as e:
            logger.error(f"❌ 建立姐妹关系失败: {e}")

    async def _load_configurations(self):
        """加载配置"""
        # 这里可以从文件或数据库加载配置
        # 目前使用默认配置
        logger.debug("使用默认Agent配置")

    def _merge_configs(
        self, agent_type: AgentType, custom_config: dict[str, Any]
    ) -> dict[str, Any]:
        """合并配置"""
        base_config = self.default_configs.get(agent_type, {})

        if custom_config:
            # 深度合并配置
            merged_config = self._deep_merge(base_config, custom_config)
        else:
            merged_config = base_config.copy()

        return merged_config

    def _deep_merge(self, base: dict[str, Any], custom: dict[str, Any]) -> dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    async def get_system_status(self) -> dict[str, Any]:
        """获取系统状态"""
        agents = await self.get_all_agents()

        status = {
            "factory_initialized": self.factory_initialized,
            "agent_count": len(agents),
            "agents": {},
            "system_health": "healthy",
        }

        # 收集每个Agent的状态
        for agent in agents:
            try:
                agent_status = await agent.get_status()
                status["agents"][agent.agent_id] = {
                    "type": agent.agent_type.value,
                    "state": agent_status["state"],
                    "modules": agent_status["modules"],
                }
            except Exception as e:
                status["agents"][agent.agent_id] = {
                    "type": agent.agent_type.value,
                    "state": "error",
                    "error": str(e),
                }
                status["system_health"] = "degraded"

        return status

    async def shutdown_all_agents(self):
        """关闭所有Agent"""
        logger.info("🔄 关闭所有Agent...")

        for agent_id in list(self.agents.keys()):
            await self.remove_agent(agent_id)

        self.agents.clear()
        self.agent_configs.clear()

        logger.info("✅ 所有Agent已关闭")

    async def backup_agent_state(self, agent_id: str) -> dict[str, Any] | None:
        """备份Agent状态"""
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]

        backup = {
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type.value,
            "config": self.agent_configs.get(agent_id, {}),
            "profile": agent.profile.__dict__ if agent.profile else None,
            "state": await agent.get_status(),
            "backup_timestamp": datetime.now().isoformat(),
        }

        return backup

    async def restore_agent_state(self, backup: dict[str, Any]) -> BaseAgent | None:
        """恢复Agent状态"""
        try:
            # 重新创建Agent
            agent = await self.create_agent(backup["agent_type"], backup["config"])

            logger.info(f"✅ Agent状态已恢复: {agent.agent_id}")

            return agent

        except Exception as e:
            logger.error(f"❌ 恢复Agent状态失败: {e}")
            return None

    async def cleanup_inactive_agents(self, max_inactive_hours: int = 24):
        """清理不活跃的Agent"""
        logger.info(f"🧹 清理不活跃Agent(超过{max_inactive_hours}小时)...")

        current_time = datetime.now()
        inactive_agents = []

        for agent_id, agent in self.agents.items():
            # 检查Agent的最后活动时间
            last_activity = getattr(agent, "last_activity", agent.created_at)
            inactive_hours = (current_time - last_activity).total_seconds() / 3600

            if inactive_hours > max_inactive_hours:
                inactive_agents.append(agent_id)

        # 移除不活跃的Agent
        for agent_id in inactive_agents:
            await self.remove_agent(agent_id)

        if inactive_agents:
            logger.info(f"🗑️ 已清理 {len(inactive_agents)} 个不活跃Agent")
        else:
            logger.info("✅ 没有需要清理的不活跃Agent")


# 导出的接口
__all__ = ["AgentFactory"]
