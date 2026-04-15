#!/usr/bin/env python3
"""
Task Tool系统使用示例集
Task Tool System Examples Collection

提供Task Tool系统的完整使用示例,包括基础使用、代理类型使用、高级使用等。

作者: Agent-3 (domain-adapter-tester)
版本: 1.0.0
创建日期: 2026-04-05
"""

import os
import sys
import time

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# ========== 示例1: 基础任务执行 ==========


def example_1_basic_task_execution():
    """
    示例1: 基础任务执行

    演示TaskTool的基本使用方法,包括:
    - 创建TaskTool实例
    - 执行简单任务
    - 获取任务结果
    """
    print("=" * 60)
    print("示例1: 基础任务执行")
    print("=" * 60)

    from core.agents.task_tool import TaskTool

    # 创建TaskTool实例
    task_tool = TaskTool()

    # 执行简单任务
    print("\n执行任务: 分析专利CN202310123456.7...")
    result = task_tool.execute(
        prompt="分析专利CN202310123456.7的技术方案和创新点",
        tools=["patent-search", "patent-analysis"],
        agent_type="analysis",
    )

    # 输出结果
    print("\n✅ 任务执行完成!")
    print(f"任务ID: {result['task_id']}")
    print(f"状态: {result['status']}")
    print(f"代理ID: {result['agent_id']}")
    print(f"使用模型: {result['model']}")

    print("\n" + "=" * 60 + "\n")


# ========== 示例2: 异步后台任务 ==========


def example_2_background_task():
    """
    示例2: 异步后台任务

    演示后台任务的使用,包括:
    - 提交后台任务
    - 查询任务状态
    - 等待任务完成
    """
    print("=" * 60)
    print("示例2: 异步后台任务")
    print("=" * 60)

    from core.agents.task_tool import BackgroundTaskManager, TaskTool

    # 创建实例
    task_tool = TaskTool()
    task_manager = BackgroundTaskManager(max_workers=10)

    try:
        # 提交后台任务
        print("\n提交后台任务: 检索关于量子计算的专利...")
        task = task_manager.submit(
            func=task_tool.execute,
            kwargs={
                "prompt": "检索关于量子计算的专利",
                "tools": ["patent-search", "result-ranker"],
                "agent_type": "search",
                "background": False,
            },
            agent_id="search-agent-1",
        )

        task_id = task.task_id
        print("\n✅ 任务已提交!")
        print(f"任务ID: {task_id}")
        print(f"初始状态: {task.status}")

        # 查询任务状态
        print("\n等待任务完成...")
        for i in range(5):
            time.sleep(2)
            status = task_manager.get_task(task_id)
            print(f"  [{i + 1}/5] 状态: {status.status if status else '未找到'}")

        # 等待任务完成
        print("\n等待任务完成(超时: 60秒)...")
        result = task_manager.wait_get_task(task_id, timeout=60)

        print("\n✅ 任务完成!")
        print(f"最终状态: {result.status if result else '未找到'}")

    except Exception as e:
        print(f"\n❌ 任务执行出错: {e}")

    print("\n" + "=" * 60 + "\n")


# ========== 示例3: 模型选择和映射 ==========


def example_3_model_mapping():
    """
    示例3: 模型选择和映射

    演示ModelMapper的使用,包括:
    - 创建ModelMapper实例
    - 映射模型名称
    - 获取模型配置
    - 获取可用模型列表
    """
    print("=" * 60)
    print("示例3: 模型选择和映射")
    print("=" * 60)

    from core.agents.task_tool import ModelMapper

    # 创建ModelMapper实例
    mapper = ModelMapper()

    # 映射模型名称
    print("\n模型映射演示:")
    models_to_test = ["haiku", "sonnet", "opus"]
    for model in models_to_test:
        mapped = mapper.map(model)
        print(f"  {model:8s} → {mapped}")

    # 获取模型配置
    print("\n模型配置:")
    for model in models_to_test:
        config = mapper.get_model_config(model)
        print(f"\n  模型: {model}")
        print(f"    名称: {config['name']}")
        print(f"    温度: {config['temperature']}")
        print(f"    最大token: {config['max_tokens']}")
        print(f"    描述: {config['description']}")

    # 获取可用模型列表
    print(f"\n可用模型: {mapper.get_available_models()}")

    # 检查环境变量
    env_model = mapper.get_environment_model()
    if env_model:
        print(f"\n环境变量模型: {env_model}")
    else:
        print("\n环境变量模型: 未设置")

    print("\n" + "=" * 60 + "\n")


# ========== 示例4: 专利代理类型使用 ==========


def example_4_patent_agents():
    """
    示例4: 专利代理类型使用

    演示4种专利代理类型的使用,包括:
    - patent-analyst: 专利分析师
    - patent-searcher: 专利检索专家
    - legal-researcher: 法律研究员
    - patent-drafter: 专利撰写专家
    """
    print("=" * 60)
    print("示例4: 专利代理类型使用")
    print("=" * 60)

    from core.agents.task_tool import TaskTool

    # 创建TaskTool实例
    task_tool = TaskTool()

    # 1. 专利分析师 (使用sonnet模型)
    print("\n1. 专利分析师 - 分析专利技术方案")
    result = task_tool.execute(
        prompt="分析专利CN202310123456.7的技术方案和创新点",
        tools=["patent-search", "patent-analysis", "knowledge-graph-query"],
        agent_type="analysis",
    )
    print(f"   任务ID: {result['task_id']}")
    print(f"   使用模型: {result['model']}")

    # 2. 专利检索专家 (使用haiku模型)
    print("\n2. 专利检索专家 - 检索量子计算专利")
    result = task_tool.execute(
        prompt="检索关于量子计算的专利,最多返回50条",
        tools=["patent-search", "result-ranker", "patent-filter"],
        agent_type="search",
    )
    print(f"   任务ID: {result['task_id']}")
    print(f"   使用模型: {result['model']}")

    # 3. 法律研究员 (使用opus模型)
    print("\n3. 法律研究员 - 分析专利侵权判例")
    result = task_tool.execute(
        prompt="分析专利侵权判例,判断新颖性",
        tools=["legal-knowledge-query", "case-law-search", "legal-reasoning"],
        agent_type="legal",
    )
    print(f"   任务ID: {result['task_id']}")
    print(f"   使用模型: {result['model']}")

    # 4. 专利撰写专家 (使用opus模型)
    print("\n4. 专利撰写专家 - 撰写专利申请文件")
    result = task_tool.execute(
        prompt="基于以下技术方案撰写专利申请文件:\n技术方案: 一种新型量子计算算法...",
        tools=["patent-drafting", "patent-review", "patent-formatting"],
        agent_type="drafter",
    )
    print(f"   任务ID: {result['task_id']}")
    print(f"   使用模型: {result['model']}")

    print("\n" + "=" * 60 + "\n")


# ========== 示例5: 工作流集成 ==========


def example_5_workflow_integration():
    """
    示例5: 工作流集成

    演示工作流的完整使用流程,包括:
    - AnalysisWorkflow: 专利分析工作流
    - SearchWorkflow: 专利检索工作流
    - LegalWorkflow: 法律研究工作流
    """
    print("=" * 60)
    print("示例5: 工作流集成")
    print("=" * 60)

    print("\n注意: 工作流实现将在T3-3, T3-4, T3-5中完成")
    print("以下为示例代码,仅供参考\n")

    # 专利分析工作流示例
    print("1. 专利分析工作流 (AnalysisWorkflow):")
    print("""
    from core.patent.workflows import AnalysisWorkflow

    workflow = AnalysisWorkflow()
    result = workflow.execute(
        patent_number="CN202310123456.7",
        analysis_type="comprehensive",
        include_comparison=True,
        generate_report=True,
    )

    print(f"分析完成: {result['success']}")
    print(f"报告路径: {result['report_path']}")
    """)

    # 专利检索工作流示例
    print("\n2. 专利检索工作流 (SearchWorkflow):")
    print("""
    from core.patent.workflows import SearchWorkflow

    workflow = SearchWorkflow()
    result = workflow.execute(
        query="量子计算",
        data_sources=["local", "online"],
        max_results=50,
        export_format="csv",
        export_path="/path/to/results.csv",
    )

    print(f"检索完成: {result['success']}")
    print(f"找到专利数: {result['total_count']}")
    print(f"导出路径: {result['export_path']}")
    """)

    # 法律研究工作流示例
    print("\n3. 法律研究工作流 (LegalWorkflow):")
    print("""
    from core.patent.workflows import LegalWorkflow

    workflow = LegalWorkflow()
    result = workflow.execute(
        legal_query="分析专利侵权判例",
        case_types=["infringement", "invalidation"],
        include_trend_analysis=True,
        generate_opinion=True,
    )

    print(f"研究完成: {result['success']}")
    print(f"法律意见: {result['legal_opinion']}")
    """)

    print("\n" + "=" * 60 + "\n")


# ========== 示例6: 高级使用 - 错误处理和重试 ==========


def example_6_error_handling():
    """
    示例6: 高级使用 - 错误处理和重试

    演示错误处理和重试机制,包括:
    - 输入验证错误
    - 任务执行错误
    - 超时处理
    - 重试机制
    """
    print("=" * 60)
    print("示例6: 高级使用 - 错误处理和重试")
    print("=" * 60)

    from core.agents.task_tool import TaskTool

    # 创建TaskTool实例
    task_tool = TaskTool()

    # 错误处理示例
    print("\n错误处理演示:")

    # 1. 输入验证错误
    try:
        result = task_tool.execute(
            prompt="",  # 空提示词
            tools=["tool1"],
        )
    except ValueError as e:
        print(f"❌ 输入验证错误: {e}")

    # 2. 任务执行错误
    try:
        result = task_tool.execute(
            prompt="执行任务",
            tools=["tool1"],
        )
    except Exception as e:
        print(f"❌ 任务执行错误: {e}")

    # 重试机制示例
    print("\n重试机制演示:")
    max_retries = 3
    retry_delay = 2  # 秒

    for attempt in range(max_retries):
        try:
            print(f"\n尝试 {attempt + 1}/{max_retries}...")
            result = task_tool.execute(
                prompt="分析专利CN202310123456.7",
                tools=["patent-search", "patent-analysis"],
                agent_type="analysis",
            )
            print("✅ 任务执行成功!")
            print(f"任务ID: {result['task_id']}")
            break
        except Exception as e:
            print(f"❌ 尝试 {attempt + 1} 失败: {e}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                print("❌ 所有重试失败")

    print("\n" + "=" * 60 + "\n")


# ========== 示例7: 高级使用 - 任务状态监控 ==========


def example_7_task_monitoring():
    """
    示例7: 高级使用 - 任务状态监控

    演示任务状态的持续监控,包括:
    - 定期查询任务状态
    - 状态变化通知
    - 完成后处理
    """
    print("=" * 60)
    print("示例7: 高级使用 - 任务状态监控")
    print("=" * 60)

    from core.agents.task_tool import BackgroundTaskManager, TaskTool

    # 创建实例
    task_tool = TaskTool()
    task_manager = BackgroundTaskManager(max_workers=10)

    # 提交后台任务
    print("\n提交后台任务...")
    task = task_manager.submit(
        func=task_tool.execute,
        kwargs={
            "prompt": "检索关于量子计算的专利",
            "tools": ["patent-search", "result-ranker"],
            "agent_type": "search",
            "background": False,
        },
        agent_id="search-agent-monitor-1",
    )

    task_id = task.task_id
    print(f"任务ID: {task_id}")
    print(f"初始状态: {task.status}")

    # 状态监控
    print("\n开始监控任务状态...")
    monitor_interval = 2  # 秒
    timeout = 30  # 秒
    elapsed = 0

    while elapsed < timeout:
        time.sleep(monitor_interval)
        elapsed += monitor_interval

        current_task = task_manager.get_task(task_id)
        if current_task:
            print(f"[{elapsed:3d}s] 状态: {current_task.status.value}")

            # 检查任务是否完成
            if current_task.status.value in ["completed", "failed", "cancelled"]:
                print(f"\n✅ 任务完成! 最终状态: {current_task.status.value}")
                break
        else:
            print(f"[{elapsed:3d}s] 任务未找到")
            break

    if elapsed >= timeout:
        print(f"\n⚠️  监控超时 ({timeout}秒)")

    print("\n" + "=" * 60 + "\n")


# ========== 示例8: 高级使用 - 资源管理 ==========


def example_8_resource_management():
    """
    示例8: 高级使用 - 资源管理

    演示正确的资源管理,包括:
    - 使用上下文管理器
    - 及时释放资源
    - 并发控制
    """
    print("=" * 60)
    print("示例8: 高级使用 - 资源管理")
    print("=" * 60)


    print("\n资源管理演示:")

    # 1. 使用上下文管理器 (推荐)
    print("\n1. 使用上下文管理器 (推荐):")
    print("""
    # 推荐做法: 使用with语句确保资源正确释放
    from core.agents.task_tool import TaskTool, BackgroundTaskManager

    with BackgroundTaskManager(max_workers=10) as task_manager:
        task_tool = TaskTool()

        # 提交任务
        task = task_manager.submit(
            func=task_tool.execute,
            kwargs={"prompt": "执行任务"},
        )

        # ... 其他操作

    # 退出with块时,管理器自动关闭,确保资源释放
    """)

    # 2. 手动资源管理 (不推荐,需要小心)
    print("\n2. 手动资源管理 (不推荐):")
    print("""
    # 不推荐做法: 手动管理资源
    from core.agents.task_tool import TaskTool, BackgroundTaskManager

    task_manager = BackgroundTaskManager(max_workers=10)
    task_tool = TaskTool()

    try:
        # 提交任务
        task = task_manager.submit(
            func=task_tool.execute,
            kwargs={"prompt": "执行任务"},
        )

        # ... 其他操作

    finally:
        # 确保手动关闭管理器
        task_manager.shutdown(wait=True)
    """)

    # 3. 并发控制
    print("\n3. 并发控制:")
    print("""
    # 根据系统资源调整max_workers
    max_workers = 10  # 默认值

    # 如果系统资源有限,可以降低并发数
    # max_workers = 5  # 降低并发数

    task_manager = BackgroundTaskManager(max_workers=max_workers)
    """)

    print("\n" + "=" * 60 + "\n")


# ========== 主函数 ==========


def main():
    """主函数 - 运行所有示例"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 20 + "Task Tool 使用示例集" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n本示例集提供Task Tool系统的完整使用示例")
    print("每个示例都可以独立运行\n")

    # 运行示例
    examples = [
        ("基础任务执行", example_1_basic_task_execution),
        ("异步后台任务", example_2_background_task),
        ("模型选择和映射", example_3_model_mapping),
        ("专利代理类型使用", example_4_patent_agents),
        ("工作流集成", example_5_workflow_integration),
        ("错误处理和重试", example_6_error_handling),
        ("任务状态监控", example_7_task_monitoring),
        ("资源管理", example_8_resource_management),
    ]

    print("可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n选择要运行的示例 (1-8, 或按Enter运行所有): ", end="")
    choice = input().strip()

    if choice == "":
        # 运行所有示例
        for name, func in examples:
            try:
                func()
                time.sleep(1)  # 示例之间暂停
            except Exception as e:
                print(f"\n❌ 示例 '{name}' 执行出错: {e}\n")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        # 运行选定的示例
        index = int(choice) - 1
        name, func = examples[index]
        try:
            func()
        except Exception as e:
            print(f"\n❌ 示例 '{name}' 执行出错: {e}\n")
    else:
        print("\n无效选择,退出程序")

    print("\n" + "=" * 60)
    print("示例运行完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
