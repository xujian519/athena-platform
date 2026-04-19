#!/usr/bin/env python3
"""
测试BaseAgent工具支持集成
Test BaseAgent Tool Support Integration

验证BaseAgent的工具调用能力:
- call_tool() - 调用工具
- discover_tools() - 发现工具
- list_tools() - 列出工具
- get_tool_info() - 获取工具信息

Author: Athena Team
Date: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class MockAgent:
    """模拟智能体用于测试工具支持"""

    def __init__(self, config=None):
        self._config = config or {}
        self._status = "initializing"
        self._tools_enabled = self._config.get("tools_enabled", True)
        self._tool_registry = None
        self.name = "mock-agent"

        # 设置日志
        import logging
        self.logger = logging.getLogger(self.name)

    async def _get_tool_registry(self):
        """获取工具注册中心"""
        if not self._tools_enabled:
            return None

        if self._tool_registry is None:
            try:
                from core.governance.unified_tool_registry import get_unified_registry

                self._tool_registry = get_unified_registry()

                # 初始化注册中心
                if not self._tool_registry.tools:
                    await self._tool_registry.initialize()

                self.logger.info(f"工具注册中心已连接,可用工具: {len(self._tool_registry.tools)}")

            except Exception as e:
                self.logger.error(f"初始化工具注册中心失败: {e}")
                self._tools_enabled = False
                return None

        return self._tool_registry

    async def call_tool(self, tool_id: str, parameters: dict, context: dict = None):
        """调用工具"""
        registry = await self._get_tool_registry()

        if not registry:
            return {
                "success": False,
                "error": "工具系统未启用",
                "tool_id": tool_id
            }

        try:
            result = await registry.execute_tool(tool_id, parameters, context)

            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "tool_id": tool_id,
                "execution_time": result.execution_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id
            }

    async def discover_tools(self, query: str, category: str = None, limit: int = 5):
        """发现工具"""
        registry = await self._get_tool_registry()

        if not registry:
            return []

        try:
            from core.governance.unified_tool_registry import ToolCategory

            category_enum = ToolCategory(category) if category else None

            return await registry.discover_tools(
                query=query,
                category=category_enum,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"工具发现失败: {e}")
            return []

    async def list_tools(self, category: str = None, status: str = None):
        """列出工具"""
        registry = await self._get_tool_registry()

        if not registry:
            return []

        try:
            from core.governance.unified_tool_registry import ToolCategory, ToolStatus

            category_enum = ToolCategory(category) if category else None
            status_enum = ToolStatus(status) if status else None

            return registry.list_tools(category=category_enum, status=status_enum)
        except Exception as e:
            self.logger.error(f"列出工具失败: {e}")
            return []

    async def get_tool_info(self, tool_id: str):
        """获取工具信息"""
        registry = await self._get_tool_registry()

        if not registry:
            return None

        try:
            return registry.get_tool_info(tool_id)
        except Exception as e:
            self.logger.error(f"获取工具信息失败: {e}")
            return None


async def test_tool_support():
    """测试工具支持功能"""

    print("=" * 80)
    print("🧪 BaseAgent 工具支持测试")
    print("=" * 80)
    print()

    # 创建模拟智能体
    agent = MockAgent()

    # 测试1: 列出工具
    print("📋 测试1: 列出所有工具")
    tools = await agent.list_tools()
    print(f"   总工具数: {len(tools)}")
    print()

    # 按类别统计
    from collections import Counter
    category_count = Counter(t["category"] for t in tools)
    print("   按类别统计:")
    for category, count in category_count.most_common():
        print(f"     {category}: {count}")
    print()

    # 测试2: 发现工具
    print("🔍 测试2: 智能工具发现")
    test_queries = ["搜索", "文件", "翻译", "专利"]
    for query in test_queries:
        discovered = await agent.discover_tools(query, limit=3)
        print(f"   查询 '{query}': 找到 {len(discovered)} 个工具")
        for tool in discovered[:2]:  # 只显示前2个
            print(f"     - {tool['name']}: {tool['description'][:50]}...")
    print()

    # 测试3: 获取工具详情
    print("📖 测试3: 获取工具详细信息")
    if tools:
        first_tool_id = tools[0]["tool_id"]
        info = await agent.get_tool_info(first_tool_id)
        if info:
            print(f"   工具ID: {info['tool_id']}")
            print(f"   名称: {info['name']}")
            print(f"   类别: {info['category']}")
            print(f"   版本: {info['version']}")
            print(f"   描述: {info['description'][:80]}...")
            print(f"   能力数: {len(info['capabilities'])}")
            print(f"   状态: {info['status']}")
    print()

    # 测试4: 工具调用(模拟)
    print("⚙️ 测试4: 工具调用(内置工具)")
    # 尝试调用一个内置工具
    result = await agent.call_tool(
        "builtin.file_read",
        {"path": "/tmp/test.txt"}
    )
    print(f"   调用结果: {result['success']}")
    if result.get("error"):
        print(f"   错误信息: {result['error']}")
    else:
        print(f"   执行时间: {result.get('execution_time', 0):.3f}秒")
    print()

    # 测试5: 工具未启用情况
    print("🔒 测试5: 工具系统禁用情况")
    disabled_agent = MockAgent(config={"tools_enabled": False})
    tools_disabled = await disabled_agent.list_tools()
    print(f"   工具系统禁用时: 返回 {len(tools_disabled)} 个工具")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


async def main():
    """主函数"""
    import logging
    logging.basicConfig(level=logging.INFO)

    await test_tool_support()


if __name__ == "__main__":
    asyncio.run(main())
