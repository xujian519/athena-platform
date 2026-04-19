#!/usr/bin/env python3
from __future__ import annotations
"""
XiaonaLegalAgent 演示脚本

展示小娜·天秤女神的10大法律能力。
"""

import asyncio

from core.agents.base import AgentRegistry, AgentRequest
from core.agents.xiaona_legal import XiaonaLegalAgent


async def main():
    """主演示函数"""
    print("=" * 60)
    print("⚖️ 小娜·天秤女神 v2.0 - 演示")
    print("=" * 60)

    # 创建智能体
    print("\n1. 创建小娜·天秤女神...")
    agent = XiaonaLegalAgent()
    print(f"   名称: {agent.name}")
    print(f"   版本: {agent.get_metadata().version}")
    print(f"   状态: {agent.status.value}")

    # 初始化
    print("\n2. 初始化...")
    await agent.initialize()
    print(f"   状态: {agent.status.value}")
    print(f"   就绪: {agent.is_ready}")

    # 注册到注册中心
    print("\n3. 注册到AgentRegistry...")
    AgentRegistry.register(agent)
    print(f"   已注册: {AgentRegistry.list_agents()}")

    # 展示能力
    print("\n4. 小娜的10大法律能力:")
    capabilities = agent.get_capabilities()
    for i, cap in enumerate(capabilities, 1):
        print(f"   CAP{i:02d}. {cap.name}: {cap.description}")

    # 演示意见答复能力
    print("\n5. 演示意见答复能力...")
    request = AgentRequest(
        request_id="demo-001",
        action="office-action-response",
        parameters={
            "oa_number": "OA2023001234",
            "patent_id": "CN202310123456.7",
            "rejection_reasons": ["新颖性", "创造性"],
        },
    )
    response = await agent.safe_process(request)
    print(f"   成功: {response.success}")
    print(f"   任务类型: {response.data['task_type']}")
    print(f"   成功概率: {response.data.get('estimated_success_rate', 0)*100:.0f}%")

    # 演示专利撰写能力
    print("\n6. 演示专利撰写能力...")
    request = AgentRequest(
        request_id="demo-002",
        action="patent-drafting",
        parameters={
            "invention_title": "一种智能控制系统",
            "technical_field": "自动化控制",
            "technical_problem": "现有控制方式不够智能",
            "technical_solution": "采用AI算法优化",
            "beneficial_effects": "提高控制精度30%",
        },
    )
    response = await agent.safe_process(request)
    print(f"   成功: {response.success}")
    print(f"   发明名称: {response.data['invention_title']}")
    print(f"   权利要求数: {len(response.data['draft_content']['claims'])}")
    print(f"   质量评分: {response.data.get('quality_score', 0)*100:.0f}/100")

    # 演示专利检索能力
    print("\n7. 演示专利检索能力...")
    request = AgentRequest(
        request_id="demo-003",
        action="patent-search",
        parameters={
            "query": "深度学习 图像识别",
            "search_fields": ["title", "abstract"],
            "databases": ["CN", "US"],
        },
    )
    response = await agent.safe_process(request)
    print(f"   成功: {response.success}")
    print(f"   查询: {response.data['query']}")
    print(f"   结果数: {response.data['total_results']}")
    print(f"   检索耗时: {response.data.get('search_time_ms', 0)}ms")

    # 健康检查
    print("\n8. 健康检查...")
    health = await agent.health_check()
    print(f"   状态: {health.status.value}")
    print(f"   消息: {health.message}")
    print(f"   推理引擎: {'✅' if health.details.get('orchestrator_available') else '❌'}")
    print(f"   OA答复服务: {'✅' if health.details.get('oa_responder_available') else '❌'}")

    # 统计信息
    print("\n9. 统计信息...")
    stats = agent.get_stats()
    print(f"   总请求数: {stats['total_requests']}")
    print(f"   成功数: {stats['successful_requests']}")
    print(f"   失败数: {stats['failed_requests']}")

    # 关闭
    print("\n10. 关闭小娜...")
    await agent.shutdown()
    print(f"   最终状态: {agent.status.value}")

    print("\n" + "=" * 60)
    print("⚖️ 演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
