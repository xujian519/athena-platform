#!/usr/bin/env python3

"""
Athena多智能体协作演示

展示小诺(调度官)如何协调小娜(法律专家)完成任务。
"""

import asyncio
import logging

from core.framework.agents.base import AgentRegistry
from core.framework.agents.xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2 as XiaonuoAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """多智能体协作演示"""
    logger.info("=" * 70)
    logger.info("🎭 Athena多智能体协作演示")
    logger.info("=" * 70)

    # ========== 步骤1: 创建并注册智能体 ==========
    logger.info("【步骤1】创建并注册智能体...")

    # 创建小娜·法律专家
    logger.info("  创建小娜·法律专家...")
    # xiaona = ApplicationReviewerProxy() 或其他专业代理
    AgentRegistry.register(xiaona)
    await xiaona.initialize()
    logger.info(f"    ✅ {xiaona.name} - {len(xiaona.get_capabilities())}项法律能力")

    # 创建小诺·调度官
    logger.info("  创建小诺·调度官...")
    xiaonuo = XiaonuoAgent()
    AgentRegistry.register(xiaonuo)
    await xiaonuo.initialize()
    logger.info(f"    ✅ {xiaonuo.name} - 调度官已就位")

    # ========== 步骤2: 小诺展示平台状态 ==========
    logger.info("【步骤2】小诺展示平台状态...")

    status_req = {
        "request_id": "platform-status",
        "action": "platform-status",
        "parameters": {},
    }
    from core.framework.agents.base import AgentRequest
    status_response = await xiaonuo.safe_process(AgentRequest(**status_req))

    logger.info(f"  平台智能体: {status_response.data['platform_state']['total_agents']}")
    logger.info(f"  活跃智能体: {status_response.data['platform_state']['active_agents']}")

    # ========== 步骤3: 小诺调度小娜执行专利检索 ==========
    logger.info("【步骤3】小诺调度小娜执行专利检索...")

    schedule_req = {
        "request_id": "schedule-001",
        "action": "schedule-task",
        "parameters": {
            "target_agent": "xiaona-legal",
            "action": "patent-search",
            "parameters": {
                "query": "深度学习 图像识别",
                "search_fields": ["title", "abstract"],
                "databases": ["CN", "US"],
            },
        },
    }
    schedule_response = await xiaonuo.safe_process(AgentRequest(**schedule_req))

    logger.info(f"  调度目标: {schedule_response.data['target_agent']}")
    logger.info(f"  执行操作: {schedule_response.data['action']}")
    logger.info(f"  执行结果: {'✅ 成功' if schedule_response.data['success'] else '❌ 失败'}")
    if schedule_response.data['success']:
        logger.info(f"  检索结果: {schedule_response.data['result']['total_results']}条")

    # ========== 步骤4: 小诺编排工作流 ==========
    logger.info("【步骤4】小诺编排并行工作流...")

    workflow_req = {
        "request_id": "workflow-001",
        "action": "parallel-execute",
        "parameters": {
            "tasks": [
                {
                    "agent": "xiaona-legal",
                    "action": "get-stats",
                    "parameters": {},
                },
                {
                    "agent": "xiaona-legal",
                    "action": "get-capabilities",
                    "parameters": {},
                },
            ],
        },
    }
    workflow_response = await xiaonuo.safe_process(AgentRequest(**workflow_req))

    logger.info(f"  工作流类型: {workflow_response.data['task_type']}")
    logger.info(f"  执行任务数: {workflow_response.data['executed_tasks']}")
    logger.info(f"  成功完成: {workflow_response.data['success_count']}")

    # ========== 步骤5: 小诺进行健康检查 ==========
    logger.info("【步骤5】小诺进行全局健康检查...")

    health_req = {
        "request_id": "health-001",
        "action": "health-check-all",
        "parameters": {},
    }
    health_response = await xiaonuo.safe_process(AgentRequest(**health_req))

    logger.info(f"  总智能体数: {health_response.data['total_agents']}")
    logger.info(f"  健康智能体: {health_response.data['healthy_agents']}")
    for name, info in health_response.data['health_details'].items():
        status_icon = "✅" if info['healthy'] else "❌"
        logger.info(f"    {status_icon} {name}: {info['status']}")

    # ========== 步骤6: 小诺陪伴聊天 ==========
    logger.info("【步骤6】小诺的温暖陪伴...")

    chat_req = {
        "request_id": "chat-001",
        "action": "chat",
        "parameters": {"message": "小诺，辛苦你了！"},
    }
    chat_response = await xiaonuo.safe_process(AgentRequest(**chat_req))

    logger.info(f"  用户: {chat_response.data['user_message']}")
    logger.info(f"  小诺: {chat_response.data['response']}")

    # ========== 步骤7: 关闭所有智能体 ==========
    logger.info("【步骤7】关闭所有智能体...")

    await AgentRegistry.shutdown_all()

    for name in AgentRegistry.list_agents():
        agent = AgentRegistry.get(name)
        logger.info(f"    {name}: {agent.status.value}")

    logger.info("=" * 70)
    logger.info("🎭 多智能体协作演示完成！")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

