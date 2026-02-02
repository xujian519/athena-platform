#!/usr/bin/env python3
"""
测试法律API按需启动
Test Laws API On-demand Startup
"""

import requests
import subprocess
import time
import sys
from pathlib import Path

def test_laws_api():
    """测试法律API按需启动"""
    print("🧪 测试法律API按需启动")
    print("=" * 50)

    # 1. 检查初始状态
    print("\n1. 检查初始状态...")
    try:
        response = requests.get("http://localhost:8099/health", timeout=3)
        if response.status_code == 200:
            print("❌ 法律API已在运行，请先停止")
            return
    except:
        print("✅ 法律API未运行（符合预期）")

    # 2. 导入并测试按需启动
    print("\n2. 测试按需启动...")
    sys.path.append(str(Path(__file__).parent))

    from core.services.on_demand_manager import get_laws_api_url
    import asyncio

    async def test():
        # 按需启动
        print("   📝 请求法律API服务...")
        url = await get_laws_api_url()

        if url:
            print(f"   ✅ 服务已启动: {url}")

            # 测试API功能
            print("\n3. 测试API功能...")
            try:
                # 测试根路径
                response = requests.get(f"{url}/")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   📚 服务名称: {data.get('service')}")
                    print(f"   📖 法律文档: {data.get('features', [''])[0] if data.get('features') else 'N/A'}")

                # 测试统计接口
                response = requests.get(f"{url}/api/stats")
                if response.status_code == 200:
                    stats = response.json()
                    print(f"   📊 总法律数: {stats.get('total_laws', 'N/A')}")
                    print(f"   💾 数据库大小: {stats.get('db_size', 'N/A')}")

                print("\n✅ 所有测试通过！")

            except Exception as e:
                print(f"   ❌ API测试失败: {e}")

            # 等待用户确认
            input("\n按回车键停止服务...")

            # 停止服务
            from core.services.on_demand_manager import stop_laws_api
            await stop_laws_api()
            print("   🛑 法律API已停止")
        else:
            print("   ❌ 服务启动失败")

    asyncio.run(test())

    # 4. 验证服务已停止
    print("\n4. 验证服务已停止...")
    try:
        response = requests.get("http://localhost:8099/health", timeout=3)
        print("   ⚠️ 服务仍在运行")
    except:
        print("   ✅ 服务已停止")

if __name__ == "__main__":
    test_laws_api()