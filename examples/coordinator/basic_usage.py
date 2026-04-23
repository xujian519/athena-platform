#!/usr/bin/env python3
"""Coordinator模式基本使用示例

演示Coordinator模式的核心功能使用。
"""

from __future__ import annotations

from core.coordinator import (
    AdvancedCoordinator,
    AgentInfo,
    ConflictResolutionStrategy,
    ConflictType,
    Coordinator,
    CoordinatorConfig,
    MessagePriority,
    TaskDependency,
)


def main() -> None:
    """主函数"""
    print("=" * 60)
    print("Coordinator模式基本使用示例")
    print("=" * 60)

    # 1. 创建Coordinator
    print("\n1. 创建Coordinator")
    config = CoordinatorConfig(
        max_concurrent_tasks=10,
        enable_load_balancing=True,
        enable_conflict_detection=True,
    )
    coordinator = Coordinator(config)
    print("   ✓ Coordinator创建成功")

    # 2. 注册Agent
    print("\n2. 注册Agent")
    agents = [
        AgentInfo(
            agent_id="search-agent",
            name="专利检索Agent",
            capabilities=["patent_search", "search"],
            max_concurrent_tasks=3,
        ),
        AgentInfo(
            agent_id="analyze-agent",
            name="专利分析Agent",
            capabilities=["patent_analyze", "analyze"],
            max_concurrent_tasks=2,
        ),
        AgentInfo(
            agent_id="report-agent",
            name="报告生成Agent",
            capabilities=["report_generate", "write"],
            max_concurrent_tasks=2,
        ),
    ]

    for agent in agents:
        coordinator.register_agent(agent)
        print(f"   ✓ 注册Agent: {agent.name} ({agent.agent_id})")

    # 3. 提交任务
    print("\n3. 提交任务")
    assignment = coordinator.submit_task(
        task_id="task-search-001",
        task_type="patent_search",
        payload={"query": "人工智能", "limit": 10},
        priority=3,
    )

    if assignment:
        print(f"   ✓ 任务分配: {assignment.task_id} -> {assignment.agent_id}")

    # 4. 完成任务
    print("\n4. 完成任务")
    result = coordinator.complete_task(
        task_id="task-search-001",
        agent_id="search-agent",
        result={"count": 10, "patents": ["CN123456", "CN789012"]},
    )
    print(f"   ✓ 任务完成: {result}")

    # 5. 发送消息
    print("\n5. Agent间通信")
    coordinator.send_message(
        sender="search-agent",
        receiver="analyze-agent",
        content={"patents": ["CN123456", "CN789012"]},
        priority=MessagePriority.HIGH,
    )
    print("   ✓ 消息已发送: search-agent -> analyze-agent")

    # 6. 获取消息
    messages = coordinator.get_pending_messages("analyze-agent")
    print(f"   ✓ 待处理消息数: {len(messages)}")

    # 7. 查看状态
    print("\n6. Coordinator状态")
    state = coordinator.get_state()
    print(f"   - 总Agent数: {state['total_agents']}")
    print(f"   - 活跃Agent数: {state['active_agents']}")
    print(f"   - 总任务数: {state['total_tasks']}")
    print(f"   - 待处理任务: {state['pending_tasks']}")

    # 8. 高级功能：任务依赖
    print("\n7. 高级功能：任务依赖")
    advanced = AdvancedCoordinator(coordinator)

    dependency = TaskDependency(
        task_id="task-analyze-001",
        depends_on=["task-search-001"],
        wait_mode="all",
    )
    advanced.add_dependency(dependency)
    print("   ✓ 添加依赖: task-analyze-001 依赖 task-search-001")

    # 检查依赖
    can_run = advanced.check_dependencies("task-analyze-001")
    print(f"   - 依赖满足: {can_run}")

    # 9. 冲突检测和解决
    print("\n8. 冲突检测和解决")
    conflict = coordinator.detect_conflict(
        conflict_type=ConflictType.RESOURCE,
        agents=["search-agent", "analyze-agent"],
        resource_id="database-001",
        description="同时访问数据库",
    )
    print(f"   ✓ 检测到冲突: {conflict.conflict_id}")

    # 解决冲突
    coordinator.resolve_conflict(
        conflict.conflict_id,
        ConflictResolutionStrategy.PRIORITY,
    )
    print("   ✓ 冲突已解决")

    # 10. 查看指标
    print("\n9. 指标统计")
    metrics = coordinator.get_metrics()
    print(f"   - 总任务提交: {metrics['total_tasks_submitted']}")
    print(f"   - 总任务完成: {metrics['total_tasks_completed']}")
    print(f"   - 总消息发送: {metrics['total_messages_sent']}")

    print("\n" + "=" * 60)
    print("示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
