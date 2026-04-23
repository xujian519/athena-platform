#!/usr/bin/env python3
"""
测试system_monitor工具注册
"""

from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 检查懒加载工具
print("懒加载工具列表:")
for tool_id, loader in registry._lazy_tools.items():
    if 'system_monitor' in tool_id:
        print(f"  - {tool_id}: {loader.import_path}.{loader.function_name}")

# 尝试手动加载
print("\n尝试手动加载system_monitor工具...")
try:
    from core.tools.system_monitor_wrapper import system_monitor_wrapper
    print("✅ system_monitor_wrapper导入成功")

    # 测试调用
    import asyncio

    async def test():
        result = await system_monitor_wrapper(
            params={"metrics": ["cpu"]},
            context={}
        )
        return result

    result = asyncio.run(test())
    print(f"✅ 调用成功: CPU使用率 {result['metrics']['cpu']['usage_percent']}%")

except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()

# 尝试注册
print("\n尝试手动注册system_monitor工具...")
try:
    success = registry.register_lazy(
        tool_id="system_monitor",
        import_path="core.tools.system_monitor_wrapper",
        function_name="system_monitor_wrapper",
        metadata={
            "name": "系统监控",
            "description": "系统监控工具 - 提供CPU使用率、内存使用情况、磁盘使用情况监控",
            "category": "system_monitoring",
            "version": "1.0.0",
        }
    )

    if success:
        print("✅ 注册成功")

        # 尝试获取工具
        tool = registry.get("system_monitor")
        if tool:
            print(f"✅ 工具获取成功: {tool.name}")
        else:
            print("❌ 工具获取失败")
    else:
        print("❌ 注册失败")

except Exception as e:
    print(f"❌ 注册失败: {e}")
    import traceback
    traceback.print_exc()
