#!/usr/bin/env python3
"""
测试所有按需服务
Test All On-demand Services
"""

import asyncio
import requests
import sys
from pathlib import Path

# 添加路径
sys.path.append(str(Path(__file__).parent))

async def test_all_services():
    """测试所有按需服务"""
    print("🧪 测试按需服务管理（法律API、小宸、云夕）")
    print("=" * 60)

    # 导入管理器
    from core.services.on_demand_manager import (
        get_laws_api_url,
        get_xiaochen_api_url,
        get_yunxi_api_url,
        get_on_demand_manager
    )

    manager = get_on_demand_manager()

    # 测试列表
    services_to_test = [
        ("法律API", get_laws_api_url, "laws"),
        ("小宸对话API", get_xiaochen_api_url, "xiaochen"),
        ("云夕记忆API", get_yunxi_api_url, "yunxi")
    ]

    results = {}

    # 1. 测试按需启动
    print("\n🚀 测试按需启动...")
    for name, getter, key in services_to_test:
        print(f"\n📝 启动 {name}...")
        try:
            url = await getter()
            if url:
                print(f"   ✅ {name} 已启动: {url}")
                results[key] = {"url": url, "success": True}

                # 测试API响应
                try:
                    response = requests.get(f"{url}/", timeout=5)
                    if response.status_code == 200:
                        print(f"   📡 API响应正常")
                    else:
                        print(f"   ⚠️ API响应码: {response.status_code}")
                except Exception as e:
                    print(f"   ⚠️ API测试失败: {e}")
            else:
                print(f"   ❌ {name} 启动失败")
                results[key] = {"success": False}
        except Exception as e:
            print(f"   ❌ {name} 错误: {e}")
            results[key] = {"success": False, "error": str(e)}

    # 2. 显示运行状态
    print("\n📊 当前运行状态:")
    status = manager.get_status()
    for name, info in status.items():
        print(f"   - {name}: {'✅ 运行中' if info['running'] else '❌ 已停止'}")
        if info['running'] and info.get('start_time'):
            import time
            runtime = time.time() - info['start_time']
            print(f"     运行时间: {runtime:.1f}秒")

    # 3. 等待一段时间（模拟使用）
    print("\n⏳ 模拟使用中...")
    await asyncio.sleep(3)

    # 4. 手动停止服务
    print("\n🛑 测试停止服务...")
    from core.services.on_demand_manager import stop_all_ondemand_apis
    await stop_all_ondemand_apis()

    # 5. 验证服务已停止
    print("\n✅ 验证服务状态:")
    final_status = manager.get_status()
    all_stopped = all(not info['running'] for info in final_status.values())
    print(f"   所有服务已停止: {'✅ 是' if all_stopped else '❌ 否'}")

    # 6. 总结
    print("\n" + "=" * 60)
    print("📈 测试总结:")
    success_count = sum(1 for r in results.values() if r.get('success'))
    print(f"   - 成功启动: {success_count}/{len(services_to_test)}")

    if success_count == len(services_to_test):
        print("   🎉 所有按需服务测试通过！")
        print("\n💡 使用建议:")
        print("   - 服务会在需要时自动启动")
        print("   - 5分钟无使用会自动停止")
        print("   - 可通过管理函数手动控制")
    else:
        print("   ⚠️ 部分服务启动失败，请检查日志")

async def demo_usage():
    """演示实际使用场景"""
    print("\n🎭 使用场景演示")
    print("-" * 40)

    from core.services.on_demand_manager import get_laws_api_url, get_xiaochen_api_url

    # 场景1：法律咨询
    print("\n场景1：用户进行法律咨询")
    laws_url = await get_laws_api_url()
    if laws_url:
        print("   ✅ 法律API已按需启动")
        print(f"   📍 API地址: {laws_url}")
        # 这里可以进行实际的API调用...

    # 场景2：智能对话
    print("\n场景2：用户与小宸对话")
    xiaochen_url = await get_xiaochen_api_url()
    if xiaochen_url:
        print("   ✅ 小宸API已按需启动")
        print(f"   📍 API地址: {xiaochen_url}")

    print("\n💡 提示：服务将在5分钟无使用后自动停止")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_all_services())

    # 演示使用
    asyncio.run(demo_usage())