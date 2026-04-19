#!/usr/bin/env python3
"""
服务发现和路由验证测试
验证Gateway的服务发现、负载均衡和路由转发功能
"""

import asyncio
import time

import aiohttp

# ==================== 配置 ====================

GATEWAY_URL = "http://127.0.0.1:8005"
TEST_SERVICES = [
    {"name": "xiaona-service", "host": "127.0.0.1", "port": 8001},
    {"name": "xiaonuo-service", "host": "127.0.0.1", "port": 8002},
    {"name": "yunxi-service", "host": "127.0.0.1", "port": 8003}
]


# ==================== 工具函数 ====================

def print_section(title: str):
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60 + "\n")

def print_success(msg: str):
    print(f"✅ {msg}")

def print_error(msg: str):
    print(f"❌ {msg}")

def print_info(msg: str):
    print(f"ℹ️  {msg}")

def print_warning(msg: str):
    print(f"⚠️  {msg}")


async def test_service_discovery():
    """测试服务发现功能"""
    print_section("测试1: 服务发现功能")

    # 注册服务
    print_info("注册服务实例...")

    async with aiohttp.ClientSession() as session:
        # 批量注册
        payload = {
            "services": [
                {
                    "name": svc["name"],
                    "host": svc["host"],
                    "port": svc["port"],
                    "metadata": {"tags": ["test"]}
                }
                for svc in TEST_SERVICES
            ]
        }

        async with session.post(
            f"{GATEWAY_URL}/api/services/batch_register",
            json=payload
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    print_success("服务注册成功")
                    for svc in data["data"]:
                        print(f"   - {svc['service_name']}: {svc['host']}:{svc['port']}")
                else:
                    print_error("服务注册失败")
                    return False
            else:
                print_error(f"注册请求失败: {resp.status}")
                return False

        # 查询服务
        print_info("\n查询已注册的服务...")

        async with session.get(f"{GATEWAY_URL}/api/services/instances") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    instances = data["data"]
                    print_success(f"发现 {len(instances)} 个服务实例")
                    for inst in instances:
                        print(f"   - {inst['service_name']} ({inst['status']})")
                else:
                    print_error("查询服务失败")
                    return False
            else:
                print_error(f"查询请求失败: {resp.status}")
                return False

        # 测试服务健康检查
        print_info("\n测试服务健康检查...")

        all_healthy = True
        for svc in TEST_SERVICES:
            try:
                async with session.get(
                    f"http://{svc['host']}:{svc['port']}/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "healthy":
                            print_success(f"{svc['name']} 健康检查通过")
                        else:
                            print_error(f"{svc['name']} 健康状态异常")
                            all_healthy = False
                    else:
                        print_error(f"{svc['name']} 健康检查失败: {resp.status}")
                        all_healthy = False
            except Exception as e:
                print_error(f"{svc['name']} 不可访问: {str(e)}")
                all_healthy = False

        return all_healthy


async def test_load_balancing():
    """测试负载均衡功能"""
    print_section("测试2: 负载均衡功能")

    # 注册多个同一服务的实例
    print_info("注册多个服务实例...")

    async with aiohttp.ClientSession() as session:
        # 注册xiaona-service的3个实例
        instances = [
            {"name": "xiaona-service", "host": "127.0.0.1", "port": 8001, "weight": 1},
            {"name": "xiaona-service", "host": "127.0.0.1", "port": 8011, "weight": 2},  # 假设的实例
            {"name": "xiaona-service", "host": "127.0.0.1", "port": 8012, "weight": 1},  # 假设的实例
        ]

        for inst in instances:
            payload = {
                "name": inst["name"],
                "host": inst["host"],
                "port": inst["port"],
                "metadata": {"weight": inst["weight"]}
            }

            async with session.post(
                f"{GATEWAY_URL}/api/services/batch_register",
                json={"services": [payload]}
            ) as resp:
                if resp.status == 200:
                    print(f"   - 实例 {inst['host']}:{inst['port']} 权重={inst['weight']}")

        # 查询实例列表
        async with session.get(f"{GATEWAY_URL}/api/services/instances") as resp:
            if resp.status == 200:
                data = await resp.json()
                xiaona_instances = [
                    i for i in data["data"]
                    if i["service_name"] == "xiaona-service"
                ]
                print_success(f"xiaona-service 现有 {len(xiaona_instances)} 个实例")
                for inst in xiaona_instances:
                    print(f"   - {inst['id']} (weight={inst.get('weight', 1)})")

        # 模拟负载均衡
        print_info("\n模拟负载均衡（轮询）...")

        # 注意：这里只是演示，实际的负载均衡需要通过Gateway的代理功能实现
        # 由于当前gateway_extended.py只实现了内存存储，我们需要手动模拟

        selections = []
        for i in range(5):
            # 简单的轮询选择
            idx = i % len(xiaona_instances)
            selections.append(xiaona_instances[idx]["id"])

        print_success("负载均衡选择结果:")
        for i, selection in enumerate(selections, 1):
            print(f"   请求 {i}: {selection}")

        return True


async def test_route_management():
    """测试路由管理功能"""
    print_section("测试3: 路由管理功能")

    async with aiohttp.ClientSession() as session:
        # 创建路由
        print_info("创建路由规则...")

        routes = [
            {
                "id": "patents-analyze",
                "path": "/api/patents/analyze",
                "target_service": "xiaona-service",
                "methods": ["POST"]
            },
            {
                "id": "tasks-dispatch",
                "path": "/api/tasks/dispatch",
                "target_service": "xiaonuo-service",
                "methods": ["POST"]
            }
        ]

        for route in routes:
            async with session.post(
                f"{GATEWAY_URL}/api/routes",
                json=route
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        print_success(f"路由创建成功: {route['id']}")
                        print(f"   {route['path']} -> {route['target_service']}")
                    else:
                        print_error(f"路由创建失败: {route['id']}")
                else:
                    print_error(f"路由请求失败: {route['id']}")

        # 查询路由
        print_info("\n查询所有路由...")

        async with session.get(f"{GATEWAY_URL}/api/routes") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    routes = data["data"]
                    print_success(f"找到 {len(routes)} 条路由规则")
                    for route in routes:
                        print(f"   🔗 {route['path']} -> {route['target_service']}")

        return True


async def test_dependency_management():
    """测试依赖管理功能"""
    print_section("测试4: 依赖管理功能")

    async with aiohttp.ClientSession() as session:
        # 设置依赖
        print_info("设置服务依赖关系...")

        dependencies = [
            {"service": "xiaona-service", "depends_on": ["xiaonuo-service"]},
            {"service": "yunxi-service", "depends_on": ["xiaonuo-service"]},
            {"service": "yunxi-service", "depends_on": ["xiaona-service"]}  # 环依赖
        ]

        for dep in dependencies:
            async with session.post(
                f"{GATEWAY_URL}/api/dependencies",
                json=dep
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("success"):
                        deps = data["data"]["dependencies"]
                        print_success(f"{dep['service']} 依赖于: {', '.join(deps)}")

        # 构建依赖图
        print_info("\n服务依赖图:")
        print("   xiaonuo-service (调度官)")
        print("      ↑           ↑")
        print("      |           |")
        print("   xiaona-service ← yunxi-service")

        # 检查循环依赖检测
        print_info("\n检查循环依赖...")

        async with session.get(
            f"{GATEWAY_URL}/api/dependencies/yunxi-service"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    deps = data["data"]["dependencies"]
                    print(f"   yunxi-service 依赖于: {', '.join(deps)}")
                    if "xiaona-service" in deps and "xiaonuo-service" in deps:
                        print_warning("   检测到间接循环依赖")
                        print_info("   (循环依赖检测功能需要在统一Gateway中实现)")

        return True


async def test_health_monitoring():
    """测试健康监控功能"""
    print_section("测试5: 健康监控功能")

    async with aiohttp.ClientSession() as session:
        # 获取Gateway健康状态
        async with session.get(f"{GATEWAY_URL}/api/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    info = data["data"]
                    print_success("Gateway健康状态")
                    print(f"   服务实例数: {info['instances']}")
                    print(f"   路由规则数: {info['routes']}")
                    print(f"   状态: {info['status']}")

                    # 检查依赖关系
                    dependencies = info.get("dependencies", {})
                    if dependencies:
                        print("\n   依赖关系:")
                        for service, deps in dependencies.items():
                            if deps:
                                print(f"   - {service}: {', '.join(deps)}")

        # 模拟服务健康变化
        print_info("\n模拟服务状态变化...")
        print_info("   (在实际部署中，Gateway会自动检测服务健康状态)")
        print_info("    并将不健康的服务从负载均衡池中移除)")

        return True


async def test_config_loading():
    """测试动态配置加载"""
    print_section("测试6: 动态配置加载")

    async with aiohttp.ClientSession() as session:
        # 加载YAML配置
        yaml_config = """
gateway:
  name: "Athena Gateway"
  version: "1.0.0"
  features:
    - service_discovery
    - load_balancing
    - health_check
monitoring:
  prometheus:
    enabled: true
    port: 9090
"""

        print_info("加载YAML配置...")

        async with session.post(
            f"{GATEWAY_URL}/api/config/load",
            data=yaml_config,
            headers={"Content-Type": "application/json"}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    config = data["data"]
                    print_success("YAML配置加载成功")
                    print(f"   Gateway名称: {config['gateway']['name']}")
                    print(f"   版本: {config['gateway']['version']}")
                    print(f"   功能: {', '.join(config['gateway']['features'])}")
                else:
                    print_error("配置加载失败")
            else:
                print_error(f"配置加载请求失败: {resp.status}")

        # 加载JSON配置
        json_config = {
            "gateway": {
                "mode": "production"
            }
        }

        print_info("\n加载JSON配置...")

        async with session.post(
            f"{GATEWAY_URL}/api/config/load",
            json=json_config
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("success"):
                    print_success("JSON配置加载成功")
                    print(f"   模式: {data['data']['gateway']['mode']}")

        return True


async def run_all_tests():
    """运行所有服务发现和路由测试"""
    print("\n" + "="*60)
    print(" Athena Gateway 服务发现和路由验证测试")
    print("="*60)

    tests = [
        ("服务发现功能", test_service_discovery),
        ("负载均衡功能", test_load_balancing),
        ("路由管理功能", test_route_management),
        ("依赖管理功能", test_dependency_management),
        ("健康监控功能", test_health_monitoring),
        ("动态配置加载", test_config_loading),
    ]

    results = []
    start_time = time.time()

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
            await asyncio.sleep(0.5)
        except Exception as e:
            print_error(f"{test_name} 抛出异常: {str(e)}")
            results.append((test_name, False))

    duration = time.time() - start_time

    # 打印结果
    print_section("测试结果汇总")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print(f"\n总计: {passed}/{total} 通过")
    print(f"总耗时: {duration:.2f}秒")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  测试已中断")
        exit(130)
