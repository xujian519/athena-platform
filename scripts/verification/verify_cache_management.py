#!/usr/bin/env python3
"""
cache_management工具验证脚本
验证统一缓存管理系统的完整可用性
"""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_dependencies():
    """验证依赖项"""

    print("=" * 80)
    print("📦 验证依赖项")
    print("=" * 80)

    dependencies = []

    # 1. redis
    try:
        import redis
        version = redis.__version__
        dependencies.append({"name": "redis", "status": "✅ 已安装", "version": version})
        print(f"✅ redis: 已安装 (版本: {version})")
    except ImportError:
        dependencies.append({"name": "redis", "status": "❌ 未安装", "version": None})
        print("❌ redis: 未安装")

    print()

    # 检查是否所有依赖都已安装
    all_installed = all(dep["status"] == "✅ 已安装" for dep in dependencies)

    if not all_installed:
        print("⚠️ 部分依赖项未安装，请运行:")
        print("   pip install redis")
        print()

    return all_installed, dependencies


async def verify_redis_service():
    """验证Redis服务"""

    print("=" * 80)
    print("🔍 验证Redis服务")
    print("=" * 80)

    try:
        import redis

        # 测试连接
        client = redis.Redis(
            host='localhost',
            port=6379,
            password='redis123',
            decode_responses=True
        )

        # 测试ping
        client.ping()
        print("✅ Redis服务运行中")
        print("   端点: localhost:6379")

        # 获取信息
        info = client.info('server')
        print(f"   Redis版本: {info.get('redis_version', 'unknown')}")

        # 检查内存使用
        mem_info = client.info('memory')
        used_memory = mem_info.get('used_memory_human', 'unknown')
        print(f"   内存使用: {used_memory}")

        # 检查数据库大小
        db_size = client.dbsize()
        print(f"   键数量: {db_size}")

        return True

    except Exception as e:
        print(f"❌ Redis服务连接失败: {e}")
        print("   请检查Redis是否运行:")
        print("   docker ps | grep redis")
        return False

    print()


async def verify_unified_cache():
    """验证统一缓存系统"""

    print("=" * 80)
    print("🗄️ 验证统一缓存系统")
    print("=" * 80)

    try:
        from core.cache.unified_cache import UnifiedCache

        # 创建实例
        print("创建UnifiedCache实例...")
        cache = UnifiedCache()

        print("✅ 统一缓存系统创建成功")
        print(f"   默认TTL: {cache.default_ttl}秒")

        # 测试基本操作
        print("\n测试缓存操作...")

        # 1. 设置缓存
        print("  1. 设置缓存...")
        success = await cache.set(
            key="test_key",
            value={"test": "data", "timestamp": "2026-04-19"},
            ttl=60
        )
        if success:
            print("     ✅ 设置成功")
        else:
            print("     ❌ 设置失败")
            return False

        # 2. 获取缓存
        print("  2. 获取缓存...")
        value = await cache.get("test_key")
        if value:
            print(f"     ✅ 获取成功: {value}")
        else:
            print("     ❌ 获取失败")
            return False

        # 3. 检查存在
        print("  3. 检查缓存存在...")
        exists = await cache.exists("test_key")
        if exists:
            print("     ✅ 缓存存在")
        else:
            print("     ❌ 缓存不存在")
            return False

        # 4. 获取统计
        print("  4. 获取缓存统计...")
        stats = await cache.get_stats()
        print(f"     ✅ 统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")

        # 5. 删除缓存
        print("  5. 删除缓存...")
        success = await cache.delete("test_key")
        if success:
            print("     ✅ 删除成功")
        else:
            print("     ❌ 删除失败")
            return False

        # 6. 验证删除
        print("  6. 验证删除...")
        exists = await cache.exists("test_key")
        if not exists:
            print("     ✅ 缓存已删除")
        else:
            print("     ❌ 缓存仍然存在")
            return False

        return True

    except Exception as e:
        print(f"❌ 统一缓存系统验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()


async def create_handler_wrapper():
    """创建Handler包装器"""

    print("=" * 80)
    print("📝 创建Handler包装器")
    print("=" * 80)

    handler_code = '''#!/usr/bin/env python3
"""
统一缓存管理Handler
"""

from typing import Any, Dict
from core.tools.decorators import tool

@tool(
    name="cache_management",
    category="cache_management",
    description="统一缓存管理系统 - 提供Redis缓存读写、批量操作、统计和清理功能",
    tags=["cache", "redis", "performance", "storage"]
)
async def cache_management_handler(
    action: str,
    key: str = None,
    value: Any = None,
    ttl: int = 3600,
    pattern: str = None,
    keys: list[str] = None
) -> Dict[str, Any]:
    """
    统一缓存管理Handler

    参数:
        action: 操作类型 (get/set/delete/exists/clear/stats/multi_get/multi_set)
        key: 缓存键（用于get/set/delete/exists操作）
        value: 缓存值（用于set操作）
        ttl: 过期时间（秒，默认3600，用于set操作）
        pattern: 键模式（用于clear操作，如"test:*"）
        keys: 键列表（用于multi_get操作）

    返回:
        {
            "success": true,
            "action": "...",
            "result": {...}
        }
    """
    try:
        from core.cache.unified_cache import UnifiedCache

        # 参数验证
        if not action:
            return {
                "success": False,
                "error": "缺少必需参数: action"
            }

        # 创建缓存实例
        cache = UnifiedCache()

        # 执行相应的操作
        if action == "get":
            if not key:
                return {"success": False, "error": "get操作需要key参数"}
            result = await cache.get(key)
            return {
                "success": True,
                "action": "get",
                "key": key,
                "result": result,
                "exists": result is not None
            }

        elif action == "set":
            if not key or value is None:
                return {"success": False, "error": "set操作需要key和value参数"}
            success = await cache.set(key, value, ttl)
            return {
                "success": success,
                "action": "set",
                "key": key,
                "ttl": ttl
            }

        elif action == "delete":
            if not key:
                return {"success": False, "error": "delete操作需要key参数"}
            success = await cache.delete(key)
            return {
                "success": success,
                "action": "delete",
                "key": key
            }

        elif action == "exists":
            if not key:
                return {"success": False, "error": "exists操作需要key参数"}
            exists = await cache.exists(key)
            return {
                "success": True,
                "action": "exists",
                "key": key,
                "exists": exists
            }

        elif action == "clear":
            if not pattern:
                return {"success": False, "error": "clear操作需要pattern参数"}
            count = await cache.clear_pattern(pattern)
            return {
                "success": True,
                "action": "clear",
                "pattern": pattern,
                "deleted_count": count
            }

        elif action == "stats":
            stats = await cache.get_stats()
            return {
                "success": True,
                "action": "stats",
                "stats": stats
            }

        elif action == "multi_get":
            if not keys:
                return {"success": False, "error": "multi_get操作需要keys参数"}
            results = await cache.get_multi(keys)
            return {
                "success": True,
                "action": "multi_get",
                "keys": keys,
                "results": results
            }

        else:
            return {
                "success": False,
                "error": f"不支持的操作: {action}",
                "supported_actions": ["get", "set", "delete", "exists", "clear", "stats", "multi_get"]
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "action": action
        }
'''

    print("✅ Handler包装器代码已生成")

    # 保存到文件
    output_file = Path("/Users/xujian/Athena工作平台/core/tools/cache_management_handler.py")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(handler_code)

    print(f"\n✅ Handler已保存到: {output_file}")

    return True


async def test_handler():
    """测试Handler功能"""

    print("=" * 80)
    print("🧪 测试Handler功能")
    print("=" * 80)

    try:
        from core.tools.cache_management_handler import cache_management_handler

        print("✅ Handler导入成功")

        # 测试1: set操作
        print("\n测试1: set操作")
        result = await cache_management_handler(
            action="set",
            key="test_cache_key",
            value={"test": "data", "number": 123},
            ttl=60
        )
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("success"):
            print("✅ set操作成功")
        else:
            print(f"❌ set操作失败: {result.get('error')}")
            return False

        # 测试2: get操作
        print("\n测试2: get操作")
        result = await cache_management_handler(
            action="get",
            key="test_cache_key"
        )
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("success") and result.get("exists"):
            print("✅ get操作成功")
        else:
            print("❌ get操作失败")
            return False

        # 测试3: exists操作
        print("\n测试3: exists操作")
        result = await cache_management_handler(
            action="exists",
            key="test_cache_key"
        )
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("success") and result.get("exists"):
            print("✅ exists操作成功")
        else:
            print("❌ exists操作失败")
            return False

        # 测试4: stats操作
        print("\n测试4: stats操作")
        result = await cache_management_handler(
            action="stats"
        )
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("success"):
            print("✅ stats操作成功")
        else:
            print("❌ stats操作失败")
            return False

        # 测试5: delete操作
        print("\n测试5: delete操作")
        result = await cache_management_handler(
            action="delete",
            key="test_cache_key"
        )
        print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if result.get("success"):
            print("✅ delete操作成功")
        else:
            print("❌ delete操作失败")
            return False

        # 测试6: 验证删除
        print("\n测试6: 验证删除")
        result = await cache_management_handler(
            action="exists",
            key="test_cache_key"
        )
        if result.get("success") and not result.get("exists"):
            print("✅ 验证删除成功")
        else:
            print("❌ 验证删除失败")
            return False

        return True

    except Exception as e:
        print(f"❌ Handler测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def generate_report(deps_ok, redis_ok, cache_ok, handler_ok):
    """生成验证报告"""

    report = {
        "timestamp": "2026-04-19",
        "summary": {
            "dependencies_ok": deps_ok,
            "redis_service_ok": redis_ok,
            "unified_cache_ok": cache_ok,
            "handler_ok": handler_ok,
            "overall_ready": all([deps_ok, redis_ok, cache_ok, handler_ok])
        },
        "details": {
            "dependencies": deps_ok,
            "redis_service": {
                "status": "✅ 运行中" if redis_ok else "❌ 未运行",
                "endpoint": "localhost:6379"
            },
            "unified_cache": {
                "status": "✅ 可用" if cache_ok else "❌ 不可用"
            },
            "handler": {
                "status": "✅ 已创建" if handler_ok else "❌ 创建失败"
            }
        },
        "recommendations": []
    }

    # 生成建议
    if not deps_ok:
        report["recommendations"].append("安装依赖项: pip install redis")

    if not redis_ok:
        report["recommendations"].append("启动Redis服务: docker-compose up -d redis")

    if report["summary"]["overall_ready"]:
        report["recommendations"].append("✅ 所有验证通过，可以开始迁移")

    # 保存报告
    report_path = Path("/Users/xujian/Athena工作平台/reports/cache_management_verification.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print("📄 验证报告")
    print("=" * 80)
    print(f"\n报告已保存到: {report_path}\n")

    # 打印摘要
    print("验证摘要:")
    print(f"  依赖项: {'✅' if deps_ok else '❌'}")
    print(f"  Redis服务: {'✅' if redis_ok else '❌'}")
    print(f"  统一缓存系统: {'✅' if cache_ok else '❌'}")
    print(f"  Handler: {'✅' if handler_ok else '❌'}")
    print(f"\n整体状态: {'✅ 准备就绪' if report['summary']['overall_ready'] else '❌ 需要修复'}")

    if report["recommendations"]:
        print("\n建议:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

    print()

    return report


async def main():
    """主函数"""

    print("\n" + "=" * 80)
    print("🔍 cache_management工具验证")
    print("=" * 80)
    print()

    # 1. 验证依赖项
    deps_ok, dependencies = await verify_dependencies()

    if not deps_ok:
        print("⚠️ 依赖项缺失，无法继续验证")
        await generate_report(deps_ok, False, False, False)
        return

    # 2. 验证Redis服务
    redis_ok = await verify_redis_service()

    if not redis_ok:
        print("⚠️ Redis服务不可用，无法继续验证")
        await generate_report(deps_ok, redis_ok, False, False)
        return

    # 3. 验证统一缓存系统
    cache_ok = await verify_unified_cache()

    # 4. 创建Handler包装器
    handler_ok = await create_handler_wrapper()

    # 5. 测试Handler功能
    if handler_ok:
        handler_ok = await test_handler()

    # 6. 生成报告
    report = await generate_report(deps_ok, redis_ok, cache_ok, handler_ok)

    print("=" * 80)
    if report["summary"]["overall_ready"]:
        print("✅ cache_management工具验证完成，可以开始迁移")
    else:
        print("❌ cache_management工具存在问题，需要先修复")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
