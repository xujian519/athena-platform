#!/usr/bin/env python3
from __future__ import annotations
"""
完整流程演示：从意图识别到工具调用
Complete Flow Demo: From Intent Recognition to Tool Execution

展示Athena平台如何：
1. 识别用户意图
2. 分解任务为可执行步骤
3. 调用相应的工具
4. 返回执行结果

Author: Athena Team
Version: 1.0.0
Date: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_step(step_num: int, title: str):
    """打印步骤"""
    print(f"\n📍 步骤 {step_num}: {title}")
    print("-" * 80)


async def demo_complete_flow():
    """演示完整的执行流程"""

    print_header("Athena平台 - 意图识别到工具调用完整流程演示")

    # ========================================
    # 步骤1: 用户输入
    # ========================================
    print_step(1, "用户输入")

    user_input = "我要搜索与AI人工智能相关的专利技术"

    print(f"👤 用户说: {user_input}")

    # ========================================
    # 步骤2: 意图识别 (增强意图分析器)
    # ========================================
    print_step(2, "意图识别 (EnhancedIntentAnalyzer)")

    from core.cognition.enhanced_intent_analyzer import analyze_intent_enhanced

    intent = await analyze_intent_enhanced(user_input)

    print("🧠 识别结果:")
    print(f"   意图类型: {intent.intent_type.value}")
    print(f"   主要目标: {intent.primary_goal}")
    print(f"   业务领域: {intent.domain.value}")
    print(f"   置信度: {intent.confidence:.2f}")

    if intent.patent_sub_domain:
        print(f"   技术领域: {intent.patent_sub_domain.value}")

    if intent.suggested_agent:
        print(f"   建议智能体: {intent.suggested_agent}")

    # ========================================
    # 步骤3: 任务分解 (TaskDecomposer)
    # ========================================
    print_step(3, "任务分解 (TaskDecomposer)")

    from core.cognition.integrated_planner_engine import EnhancedIntentAdapter

    # 转换为标准Intent格式
    standard_intent = EnhancedIntentAdapter.to_intent(intent)

    from core.cognition.task_decomposer import TaskDecomposer

    decomposer = TaskDecomposer()
    steps = await decomposer.decompose(standard_intent, {})

    print(f"📋 分解结果 ({len(steps)}个步骤):")
    for i, step in enumerate(steps, 1):
        deps = f" (依赖: {', '.join(step.dependencies)})" if step.dependencies else ""
        print(f"   {i}. {step.description}")
        print(f"      → 智能体: {step.agent}")
        print(f"      → 操作: {step.action}")
        print(f"      → 预估时间: {step.estimated_time}秒{deps}")

    # ========================================
    # 步骤4: 工具发现 (UnifiedToolRegistry)
    # ========================================
    print_step(4, "工具发现 (UnifiedToolRegistry)")

    from core.governance.unified_tool_registry import get_unified_registry

    registry = get_unified_registry()
    await registry.initialize()

    # 搜索相关工具
    search_query = "专利检索"
    tools = await registry.discover_tools(
        query=search_query,
        limit=5,
        use_vector=False,  # 使用关键词匹配
    )

    print(f"🔍 发现的工具 (查询: '{search_query}'):")
    for i, tool in enumerate(tools[:3], 1):
        print(f"   {i}. {tool.tool_id}")
        print(f"      名称: {tool.name}")
        print(f"      类别: {tool.category.value}")

    # ========================================
    # 步骤5: 工具执行 (SafeToolExecutor)
    # ========================================
    print_step(5, "工具执行 (SafeToolExecutor)")

    from core.governance.tool_executor import get_tool_executor

    executor = get_tool_executor()

    # 选择第一个合适的工具进行演示
    if tools:
        demo_tool = tools[0]
        print(f"🔧 执行工具: {demo_tool.tool_id}")

        try:
            # 准备参数
            params = {
                "query": "AI 人工智能",
                "max_results": 5
            }

            print(f"   参数: {params}")

            # 执行工具
            result = await executor.execute(
                tool_id=demo_tool.tool_id,
                parameters=params,
                timeout=30
            )

            print("\n✅ 执行结果:")
            print(f"   成功: {result['success']}")
            if result['success']:
                print(f"   执行时间: {result['execution_time']:.2f}秒")
                if 'result' in result:
                    print(f"   返回数据: {str(result['result'])[:100]}...")

        except Exception as e:
            print(f"❌ 执行失败: {e}")

    # ========================================
    # 步骤6: 完整流程 - 通过小诺协调器
    # ========================================
    print_step(6, "完整流程 - 通过小诺协调器")

    from core.agents.base import AgentRequest
    from core.agents.xiaonuo_coordinator import XiaonuoAgent

    # 创建小诺协调器
    xiaonuo = XiaonuoAgent()
    await xiaonuo.initialize()

    # 创建智能规划请求
    request = AgentRequest(
        request_id="demo-complete-flow",
        action="intelligent-plan",
        parameters={
            "user_input": user_input,
            "context": {"demo": True},
        },
    )

    print("📝 发送请求到小诺...")
    print(f"   Action: {request.action}")
    print(f"   Input: {user_input}")

    # 处理请求
    response = await xiaonuo.process(request)

    print("\n📊 小诺响应:")
    print(f"   成功: {response.success}")

    if response.success:
        data = response.data
        print(f"   方案ID: {data.get('plan_id')}")
        print(f"   意图类型: {data.get('intent_type')}")
        print(f"   置信度: {data.get('confidence')}")

        steps_data = data.get('steps', [])
        print(f"\n   执行步骤 ({len(steps_data)}个):")
        for i, step in enumerate(steps_data, 1):
            print(f"      {i}. {step.get('description')} ({step.get('agent', '')})")

    # ========================================
    # 架构总结
    # ========================================
    print_header("架构总结")

    print("""
┌─────────────────────────────────────────────────────────────────────┐
│                        Athena平台执行流程                             │
└─────────────────────────────────────────────────────────────────────┘

  用户输入
      │
      ↓
┌───────────────────────────────────────────────────────────────────┐
│  ① 意图识别层                              │
│  - EnhancedIntentAnalyzer                                           │
│  - 专利类型、子领域、意图类型识别                                    │
│  - 法律世界模型集成                                                  │
└─────────────────────────────────────┬─────────────────────────────┘
                                  │
                                  ↓
┌───────────────────────────────────────────────────────────────────┐
│  ② 任务规划层                              │
│  - XiaonuoPlannerEngine                                             │
│  - TaskDecomposer: 任务分解                                         │
│  - MultiPlanGenerator: 多方案生成                                   │
│  - PlanSelector: 方案选择                                           │
└─────────────────────────────────────┬─────────────────────────────┘
                                  │
                                  ↓
┌───────────────────────────────────────────────────────────────────┐
│  ③ 工具发现层                              │
│  - UnifiedToolRegistry                                             │
│  - 工具扫描、注册、发现                                              │
│  - 支持Builtin/MCP/Search/Service/Agent工具                         │
└─────────────────────────────────────┬─────────────────────────────┘
                                  │
                                  ↓
┌───────────────────────────────────────────────────────────────────┐
│  ④ 工具执行层                              │
│  - SafeToolExecutor                                                │
│  - 动态加载、参数验证、超时控制                                      │
│  - 异步执行支持                                                      │
└─────────────────────────────────────┬─────────────────────────────┘
                                  │
                                  ↓
┌───────────────────────────────────────────────────────────────────┐
│  ⑤ 智能体调度层                             │
│  - XiaonuoAgent (小诺协调器)                                         │
│  - AgentRegistry (智能体注册中心)                                    │
│  - 任务分发、结果聚合                                                │
└─────────────────────────────────────┬─────────────────────────────┘
                                  │
                                  ↓
                            返回用户结果
    """)

    # ========================================
    # 关键数据结构
    # ========================================
    print_header("关键数据结构")

    print("""
1. Intent (意图对象)
   ├── intent_type: IntentType        # 意图类型
   ├── primary_goal: str              # 主要目标
   ├── sub_goals: list[str]           # 子目标列表
   ├── entities: dict                 # 实体信息
   │   ├── domain: str                # 业务领域
   │   ├── patent_type: str           # 专利类型
   │   ├── patent_sub_domain: str     # 专利子领域
   │   └── suggested_agent: str       # 建议智能体
   ├── confidence: float              # 置信度
   └── context: dict                  # 上下文

2. ExecutionStep (执行步骤)
   ├── id: str                        # 步骤ID
   ├── description: str               # 描述
   ├── agent: str                     # 负责智能体
   ├── action: str                    # 操作名称
   ├── parameters: dict               # 操作参数
   ├── dependencies: list[str]        # 依赖步骤
   ├── estimated_time: int            # 预估时间
   └── fallback_strategy: str         # 回退策略

3. Tool (工具定义)
   ├── tool_id: str                   # 工具ID (如 utility.patent_excel_parser.main)
   ├── name: str                      # 工具名称
   ├── category: ToolCategory         # 工具类别
   ├── description: str               # 描述
   ├── parameters: list[ToolParam]    # 参数定义
   ├── function: Callable             # 实际函数
   └── metadata: dict                 # 元数据
    """)

    # ========================================
    # 工具调用示例
    # ========================================
    print_header("工具调用示例")

    print("""
# 示例1: 直接使用工具执行器
from core.governance.tool_executor import get_tool_executor

executor = get_tool_executor()
result = await executor.execute(
    tool_id="utility.patent_excel_parser.main",
    parameters={"file_path": "/data/patents.xlsx"},
    timeout=60
)

# 示例2: 通过智能体调用工具
from core.agents.xiaonuo_coordinator import XiaonuoAgent
from core.agents.base import AgentRequest

xiaonuo = XiaonuoAgent()
await xiaonuo.initialize()

request = AgentRequest(
    request_id="search-patents",
    action="schedule-task",
    parameters={
        "target_agent": "xiaona-legal",
        "action": "search_patents",
        "parameters": {"query": "AI技术", "max_results": 10}
    }
)

response = await xiaonuo.process(request)

# 示例3: 智能规划（自动工具选择）
request = AgentRequest(
    request_id="intelligent-plan",
    action="intelligent-plan",
    parameters={
        "user_input": "搜索AI相关专利",
        "context": {}
    }
)

response = await xiaonuo.process(request)
    """)

    # ========================================
    # 扩展：如何添加新工具
    # ========================================
    print_header("扩展指南：如何添加新工具")

    print("""
方法1: 在tools目录创建Python文件
--------------------------------------
# tools/utility/my_tool.py

async def my_function(param1: str, param2: int = 10) -> dict:
    \"\"\"工具函数描述

    Args:
        param1: 参数1说明
        param2: 参数2说明 (默认10)

    Returns:
        执行结果字典
    \"\"\"
    # 实现逻辑
    return {"success": True, "data": "..."}

# 工具会自动注册为: utility.my_tool.my_function

方法2: 动态注册工具
--------------------------------------
from core.governance.unified_tool_registry import get_unified_registry

registry = get_unified_registry()

# 注册工具
await registry.register_tool(
    tool_id="custom.my_tool",
    name="我的工具",
    category=ToolCategory.UTILITY,
    description="工具描述",
    function=my_function,
    parameters=[...]
)

方法3: MCP工具集成
--------------------------------------
# MCP服务器会在config/mcp_servers/中配置
# 工具会自动发现和注册
    """)

    print("\n" + "=" * 80)
    print("  ✅ 演示完成！")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_complete_flow())
