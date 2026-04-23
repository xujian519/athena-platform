#!/usr/bin/env python3
"""
工具迁移示例 - patent_search_handler

展示如何将现有工具迁移到统一工具注册表
"""

from typing import Any

from core.tools.decorators import tool

# ============================================================================
# 迁移前 (旧方式)
# ============================================================================

# async def patent_search_handler(params: Dict[str, Any], context: Dict) -> Dict[str, Any]:
#     """
#     专利检索工具Handler
#
#     参数:
#         query: 检索查询词（必需）
#         channel: 检索渠道
#             - "local_postgres": 本地PostgreSQL
#             - "google_patents": Google Patents
#             - "both": 同时使用两个渠道（默认）
#         max_results: 最大结果数（默认10）
#
#     返回:
#         {
#             "success": true,
#             "query": "...",
#             "channel": "...",
#             "total_results": 10,
#             "results": [...]
#         }
#     """
#     # 原实现...
#     pass


# ============================================================================
# 迁移后 (新方式)
# ============================================================================

@tool(
    name="patent_search",
    category="patent_search",
    description="在专利数据库中搜索专利（支持本地PostgreSQL和Google Patents）",
    priority="high",
    tags=["search", "patent", "database", "google_patents"],
    version="2.0.0",
    author="Athena平台团队",
    examples=[
        {
            "input": {"query": "人工智能", "channel": "both", "max_results": 10},
            "output": {"success": True, "total_results": 10, "results": [...]}
        }
    ]
)
async def patent_search_handler_v2(
    query: str,
    channel: str = "both",
    max_results: int = 10,
    context: dict[str, Any] = None
) -> dict[str, Any]:
    """
    专利检索工具Handler (v2.0)

    统一工具注册表版本，使用@tool装饰器自动注册。

    参数:
        query: 检索查询词（必需）
        channel: 检索渠道
            - "local_postgres": 本地PostgreSQL
            - "google_patents": Google Patents
            - "both": 同时使用两个渠道（默认）
        max_results: 最大结果数（默认10）
        context: 上下文信息（可选）

    返回:
        {
            "success": true,
            "query": "...",
            "channel": "...",
            "total_results": 10,
            "results": [...]
        }

    异常:
        ValueError: 缺少必需参数或参数值无效

    示例:
        >>> result = await patent_search_handler_v2(
        ...     query="人工智能",
        ...     channel="both",
        ...     max_results=10
        ... )
        >>> print(result["total_results"])
        10
    """
    try:
        # 参数验证
        if not query:
            raise ValueError("缺少必需参数: query")

        if max_results <= 0:
            raise ValueError("max_results必须大于0")

        # 原实现逻辑...
        # 这里保留原有的实现代码

        return {
            "success": True,
            "query": query,
            "channel": channel,
            "total_results": max_results,
            "results": []  # 实际结果
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "channel": channel
        }


# ============================================================================
# 迁移检查清单
# ============================================================================

"""
迁移检查清单:

✅ 1. 添加@tool装饰器
   - name: 工具唯一标识符
   - category: 工具分类
   - description: 工具描述
   - priority: 优先级 (high/medium/low)
   - tags: 标签列表
   - version: 版本号
   - author: 作者
   - examples: 使用示例

✅ 2. 更新函数签名
   - 使用类型注解
   - 提供默认值
   - 添加参数说明
   - 添加返回值说明

✅ 3. 更新文档字符串
   - 使用Google风格
   - 包含参数说明
   - 包含返回值说明
   - 包含异常说明
   - 包含使用示例

✅ 4. 添加错误处理
   - 参数验证
   - 异常捕获
   - 错误返回

✅ 5. 测试验证
   - 单元测试
   - 集成测试
   - 性能测试

✅ 6. 向后兼容
   - 保留旧API
   - 提供适配器
   - 更新调用方
"""


# ============================================================================
# 向后兼容适配器
# ============================================================================

async def patent_search_handler(params: dict[str, Any], context: dict = None) -> dict[str, Any]:
    """
    向后兼容适配器

    将旧的params字典格式转换为新的函数签名格式。
    """
    # 提取参数
    query = params.get("query")
    channel = params.get("channel", "both")
    max_results = params.get("max_results", 10)

    # 调用新版本
    return await patent_search_handler_v2(
        query=query,
        channel=channel,
        max_results=max_results,
        context=context
    )


# ============================================================================
# 测试代码
# ============================================================================

async def test_patent_search_migration():
    """测试专利搜索工具迁移"""

    from core.tools.unified_registry import get_unified_registry

    # 1. 验证工具已注册
    registry = get_unified_registry()
    tool = registry.get("patent_search")

    assert tool is not None, "工具未注册"
    print("✅ 工具已成功注册")

    # 2. 验证工具元数据
    assert tool.name == "patent_search"
    assert tool.category == "patent_search"
    assert tool.priority == "high"
    assert "search" in tool.tags
    print("✅ 工具元数据正确")

    # 3. 验证工具功能
    result = await tool.function(
        query="人工智能",
        channel="both",
        max_results=5
    )

    assert result["success"] is True
    assert result["query"] == "人工智能"
    assert result["channel"] == "both"
    print("✅ 工具功能正常")

    # 4. 验证错误处理
    error_result = await tool.function(
        query="",
        channel="both",
        max_results=5
    )

    assert error_result["success"] is False
    assert "error" in error_result
    print("✅ 错误处理正确")

    # 5. 验证向后兼容
    old_params = {
        "query": "测试",
        "channel": "local_postgres",
        "max_results": 10
    }

    compat_result = await patent_search_handler(old_params)
    new_result = await patent_search_handler_v2(
        query="测试",
        channel="local_postgres",
        max_results=10
    )

    assert compat_result["query"] == new_result["query"]
    print("✅ 向后兼容正常")

    print("\n🎉 所有测试通过！")


# ============================================================================
# 使用示例
# ============================================================================

async def example_usage():
    """使用示例"""

    from core.tools.unified_registry import get_unified_registry

    # 获取统一注册表
    registry = get_unified_registry()

    # 方法1: 使用工具ID获取
    tool = registry.get("patent_search")
    if tool:
        result = await tool.function(
            query="人工智能",
            channel="both",
            max_results=10
        )
        print(f"找到 {result['total_results']} 个结果")

    # 方法2: 使用require获取（不存在时抛出异常）
    try:
        tool = registry.require("patent_search")
        result = await tool.function(query="机器学习")
        print(f"找到 {result['total_results']} 个结果")
    except Exception as e:
        print(f"工具不存在: {e}")

    # 方法3: 按分类查找
    patent_tools = registry.find_by_category("patent_search")
    print(f"专利搜索工具数: {len(patent_tools)}")

    # 方法4: 按标签查找
    search_tools = registry.search_tools("search")
    print(f"搜索工具数: {len(search_tools)}")


if __name__ == "__main__":
    import asyncio

    print("=" * 80)
    print("🔧 工具迁移示例 - patent_search_handler")
    print("=" * 80)
    print()

    # 运行测试
    print("运行测试...")
    asyncio.run(test_patent_search_migration())

    print()
    print("=" * 80)
    print("✅ 迁移示例完成")
    print("=" * 80)
