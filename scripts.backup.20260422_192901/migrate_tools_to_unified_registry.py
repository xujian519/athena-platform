#!/usr/bin/env python3
"""
迁移7个已验证工具到统一工具注册表

工具列表:
1. decision_engine (100%可用)
2. document_parser (100%可用)
3. code_executor_sandbox (97%可用)
4. api_tester (100%可用)
5. risk_analyzer (100%可用)
6. emotional_support (94.1%可用)
7. text_embedding (已完成，跳过)

Author: Athena平台团队
Date: 2026-04-20
"""
import asyncio
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

from core.logging_config import setup_logging

logger = setup_logging()


async def migrate_tools():
    """迁移工具到统一工具注册表"""

    print("=" * 60)
    print("🔄 迁移7个已验证工具到统一工具注册表")
    print("=" * 60)

    from core.tools.unified_registry import get_unified_registry
    from core.tools.base import ToolDefinition, ToolCategory, ToolPriority

    # 获取统一工具注册表
    registry = get_unified_registry()

    # 等待注册表初始化
    if not registry._initialized:
        print("⏳ 初始化统一工具注册表...")
        await registry.initialize(auto_discover=False)
        print("✅ 初始化完成")

    # 定义要迁移的工具
    tools_to_migrate = [
        {
            "tool_id": "decision_engine",
            "name": "决策引擎",
            "description": "基于规则和逻辑的智能决策引擎",
            "category": ToolCategory.SEMANTIC_ANALYSIS,  # 使用语义分析分类
            "priority": ToolPriority.MEDIUM,
            "import_path": "core.tools.production_tool_implementations",
            "function_name": "decision_engine_handler",
            "can_handle": "决策分析、规则判断、逻辑推理",
        },
        {
            "tool_id": "document_parser",
            "name": "文档解析器",
            "description": "增强型文档解析器，支持多种格式",
            "category": ToolCategory.DATA_EXTRACTION,  # 使用数据提取分类
            "priority": ToolPriority.HIGH,
            "import_path": "core.tools.production_tool_implementations",
            "function_name": "document_parser_handler",
            "can_handle": "文档解析、PDF处理、Word文档、文本提取",
        },
        {
            "tool_id": "code_executor_sandbox",
            "name": "代码执行器（沙箱）",
            "description": "安全的代码执行环境，支持Python代码",
            "category": ToolCategory.CODE_ANALYSIS,  # 使用代码分析分类
            "priority": ToolPriority.LOW,
            "import_path": "core.tools.code_executor_sandbox_wrapper",
            "function_name": "code_executor_sandbox_handler",
            "can_handle": "代码执行、Python脚本、沙箱环境",
        },
        {
            "tool_id": "api_tester",
            "name": "API测试器",
            "description": "HTTP API测试工具",
            "category": ToolCategory.CODE_ANALYSIS,  # 使用代码分析分类
            "priority": ToolPriority.MEDIUM,
            "import_path": "core.tools.production_tool_implementations",
            "function_name": "api_tester_handler",
            "can_handle": "API测试、HTTP请求、接口调试",
        },
        {
            "tool_id": "risk_analyzer",
            "name": "风险分析器",
            "description": "技术风险和可行性分析工具",
            "category": ToolCategory.SEMANTIC_ANALYSIS,  # 使用语义分析分类
            "priority": ToolPriority.MEDIUM,
            "import_path": "core.tools.production_tool_implementations",
            "function_name": "risk_analyzer_handler",
            "can_handle": "风险评估、技术分析、可行性研究",
        },
        {
            "tool_id": "emotional_support",
            "name": "情感支持",
            "description": "提供情感支持和安慰的交互工具",
            "category": ToolCategory.SEMANTIC_ANALYSIS,  # 使用语义分析分类
            "priority": ToolPriority.LOW,
            "import_path": "core.tools.production_tool_implementations",
            "function_name": "emotional_support_handler",
            "can_handle": "情感交流、心理支持、用户关怀",
        },
    ]

    results = []

    for i, tool_config in enumerate(tools_to_migrate, 1):
        tool_id = tool_config["tool_id"]
        print(f"\n[{i}/{len(tools_to_migrate)}] 迁移工具: {tool_id}")

        try:
            # 检查工具是否已注册
            existing = registry.get(tool_id)
            if existing is not None:
                print(f"   ⚠️ 工具已存在，跳过注册")
                results.append((tool_id, "skipped", "已存在"))
                continue

            # 注册懒加载工具
            success = registry.register_lazy(
                tool_id=tool_id,
                import_path=tool_config["import_path"],
                function_name=tool_config["function_name"],
                metadata={
                    "name": tool_config["name"],
                    "description": tool_config["description"],
                    "category": tool_config["category"],
                    "priority": tool_config["priority"],
                    "can_handle": tool_config["can_handle"],
                }
            )

            if success:
                print(f"   ✅ 注册成功")
                results.append((tool_id, "success", "注册成功"))
            else:
                print(f"   ❌ 注册失败")
                results.append((tool_id, "failed", "注册失败"))

        except Exception as e:
            print(f"   ❌ 错误: {e}")
            results.append((tool_id, "error", str(e)))

    # 验证迁移结果
    print("\n" + "=" * 60)
    print("📊 迁移结果总结")
    print("=" * 60)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for tool_id, status, message in results:
        status_icon = {
            "success": "✅",
            "failed": "❌",
            "error": "❌",
            "skipped": "⏭️"
        }.get(status, "❓")

        print(f"{status_icon} {tool_id}: {message}")

        if status == "success":
            success_count += 1
        elif status in ("failed", "error"):
            failed_count += 1
        else:
            skipped_count += 1

    print(f"\n总计: {len(results)} 个工具")
    print(f"✅ 成功: {success_count}")
    print(f"⏭️ 跳过: {skipped_count}")
    print(f"❌ 失败: {failed_count}")

    # 验证工具可用性
    print("\n" + "=" * 60)
    print("🧪 验证工具可用性")
    print("=" * 60)

    for tool_id, status, _ in results:
        if status == "success":
            print(f"\n验证 {tool_id}...")
            try:
                tool = registry.get(tool_id)
                if tool is not None:
                    print(f"   ✅ 工具可访问")
                else:
                    print(f"   ❌ 工具无法访问")
            except Exception as e:
                print(f"   ❌ 错误: {e}")

    # 显示统计信息
    print("\n" + "=" * 60)
    print("📈 注册表统计")
    print("=" * 60)

    stats = registry.get_statistics()
    print(f"总工具数: {stats['total_tools']}")
    print(f"懒加载工具: {stats['lazy_tools']}")

    return failed_count == 0


async def verify_tools():
    """验证迁移后的工具"""
    print("\n" + "=" * 60)
    print("🔍 深度验证工具功能")
    print("=" * 60)

    from core.tools.unified_registry import get_unified_registry
    registry = get_unified_registry()

    # 测试decision_engine
    print("\n测试 decision_engine...")
    try:
        decision_tool = registry.get("decision_engine")
        if decision_tool:
            result = await decision_tool(
                params={
                    "scenario": "专利检索策略选择",
                    "options": ["使用关键词", "使用分类号", "使用申请人"],
                    "context": {"user_preference": "高精度"}
                },
                context={}
            )
            print(f"   ✅ decision_engine可用")
            print(f"   推荐: {result.get('recommendation', 'N/A')}")
    except Exception as e:
        print(f"   ❌ decision_engine测试失败: {e}")

    # 测试document_parser
    print("\n测试 document_parser...")
    try:
        parser_tool = registry.get("document_parser")
        if parser_tool:
            result = await parser_tool(
                params={
                    "file_path": "/Users/xujian/Athena工作平台/README.md",
                    "extract_sections": True
                },
                context={}
            )
            print(f"   ✅ document_parser可用")
            print(f"   解析状态: {result.get('success', 'N/A')}")
    except Exception as e:
        print(f"   ❌ document_parser测试失败: {e}")

    # 测试text_embedding（已完成）
    print("\n测试 text_embedding...")
    try:
        embedding_tool = registry.get("text_embedding")
        if embedding_tool:
            result = await embedding_tool(
                params={
                    "text": "专利检索是专利分析的基础",
                    "model": "bge-m3"
                },
                context={}
            )
            print(f"   ✅ text_embedding可用")
            print(f"   向量维度: {result.get('embedding_dim', 'N/A')}")
    except Exception as e:
        print(f"   ❌ text_embedding测试失败: {e}")


async def main():
    """主函数"""
    try:
        # 迁移工具
        success = await migrate_tools()

        if success:
            # 验证工具
            await verify_tools()

            print("\n" + "=" * 60)
            print("🎉 迁移完成！")
            print("=" * 60)
            return 0
        else:
            print("\n⚠️ 部分工具迁移失败，请检查错误信息")
            return 1

    except Exception as e:
        print(f"\n❌ 迁移过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
