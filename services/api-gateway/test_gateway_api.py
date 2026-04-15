#!/usr/bin/env python3
"""
Athena Gateway API功能测试
自动测试Gateway的核心API功能
"""

import asyncio
import time
from typing import Any

import aiohttp

# ==================== 配置 ====================

GATEWAY_URL = "http://127.0.0.1:8005"
SERVICES = [
    {"name": "xiaona-service", "host": "127.0.0.1", "port": 8001, "tags": ["legal", "patent"]},
    {"name": "xiaonuo-service", "host": "127.0.0.1", "port": 8002, "tags": ["coord"]},
    {"name": "yunxi-service", "host": "127.0.0.1", "port": 8003, "tags": ["ip", "management"]}
]


# ==================== 测试工具 ====================

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


def print_section(title: str):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{title:^60}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")


async def test_api(session: aiohttp.ClientSession, method: str, url: str, **kwargs) -> dict[str, Any]:
    """发送API请求"""
    try:
        async with session.request(method, url, **kwargs) as response:
            data = await response.json() if response.content_type == "application/json" else await response.text()
            return {
                "status": response.status,
                "data": data,
                "success": 200 <= response.status < 300
            }
    except Exception as e:
        return {
            "status": 0,
            "data": str(e),
            "success": False,
            "error": str(e)
        }


# ==================== 测试用例 ====================

async def test_gateway_health(session: aiohttp.ClientSession) -> bool:
    """测试1: Gateway健康检查"""
    print_section("测试1: Gateway健康检查")

    result = await test_api(session, "GET", f"{GATEWAY_URL}/")

    if result["success"]:
        print_success("Gateway根路径访问成功")
        print(f"   响应: {result['data']}")
        return True
    else:
        print_error(f"Gateway访问失败: {result.get('error', result['data'])}")
        return False


async def test_batch_register(session: aiohttp.ClientSession) -> bool:
    """测试2: 批量服务注册"""
    print_section("测试2: 批量服务注册")

    # 构造批量注册请求
    payload = {
        "services": [
            {
                "name": svc["name"],
                "host": svc["host"],
                "port": svc["port"],
                "metadata": {"tags": svc["tags"]}
            }
            for svc in SERVICES
        ]
    }

    result = await test_api(
        session,
        "POST",
        f"{GATEWAY_URL}/api/services/batch_register",
        json=payload
    )

    if result["success"]:
        print_success("批量服务注册成功")
        data = result["data"]
        if data.get("success"):
            services = data.get("data", [])
            for svc in services:
                print(f"   ✅ {svc['service_name']}: {svc['host']}:{svc['port']} ({svc['id']})")
            return True
        else:
            print_error("注册响应success为false")
            return False
    else:
        print_error(f"批量注册失败: {result.get('error', result['data'])}")
        return False


async def test_list_instances(session: aiohttp.ClientSession) -> bool:
    """测试3: 查询服务实例"""
    print_section("测试3: 查询服务实例")

    result = await test_api(session, "GET", f"{GATEWAY_URL}/api/services/instances")

    if result["success"]:
        print_success("服务实例查询成功")
        data = result["data"]
        if data.get("success"):
            instances = data.get("data", [])
            for inst in instances:
                print(f"   📌 {inst['service_name']}: {inst['host']}:{inst['port']} [{inst['status']}]")
            return len(instances) == len(SERVICES)
        else:
            print_error("查询响应success为false")
            return False
    else:
        print_error(f"查询实例失败: {result.get('error', result['data'])}")
        return False


async def test_create_route(session: aiohttp.ClientSession) -> bool:
    """测试4: 创建路由"""
    print_section("测试4: 创建路由规则")

    routes = [
        {
            "id": "xiaona-patents",
            "path": "/api/patents/*",
            "target_service": "xiaona-service",
            "methods": ["GET", "POST"]
        },
        {
            "id": "xiaonuo-tasks",
            "path": "/api/tasks/*",
            "target_service": "xiaonuo-service",
            "methods": ["GET", "POST"]
        },
        {
            "id": "yunxi-ip",
            "path": "/api/ip/*",
            "target_service": "yunxi-service",
            "methods": ["GET", "POST", "PUT"]
        }
    ]

    all_success = True
    for route in routes:
        result = await test_api(
            session,
            "POST",
            f"{GATEWAY_URL}/api/routes",
            json=route
        )

        if result["success"] and result["data"].get("success"):
            print_success(f"路由创建成功: {route['id']} -> {route['target_service']}")
            print(f"   路径: {route['path']}")
            print(f"   方法: {', '.join(route['methods'])}")
        else:
            print_error(f"路由创建失败: {route['id']}")
            all_success = False

    return all_success


async def test_list_routes(session: aiohttp.ClientSession) -> bool:
    """测试5: 查询路由"""
    print_section("测试5: 查询路由规则")

    result = await test_api(session, "GET", f"{GATEWAY_URL}/api/routes")

    if result["success"]:
        print_success("路由查询成功")
        data = result["data"]
        if data.get("success"):
            routes = data.get("data", [])
            for route in routes:
                print(f"   🔗 {route['path']} -> {route['target_service']}")
                print(f"      方法: {', '.join(route['methods'])}")
            return True
        else:
            print_error("查询响应success为false")
            return False
    else:
        print_error(f"查询路由失败: {result.get('error', result['data'])}")
        return False


async def test_set_dependencies(session: aiohttp.ClientSession) -> bool:
    """测试6: 设置依赖关系"""
    print_section("测试6: 设置服务依赖关系")

    dependencies = [
        {
            "service": "xiaona-service",
            "depends_on": ["xiaonuo-service"]
        },
        {
            "service": "yunxi-service",
            "depends_on": ["xiaonuo-service"]
        }
    ]

    all_success = True
    for dep in dependencies:
        result = await test_api(
            session,
            "POST",
            f"{GATEWAY_URL}/api/dependencies",
            json=dep
        )

        if result["success"] and result["data"].get("success"):
            print_success(f"依赖设置成功: {dep['service']} -> {dep['depends_on']}")
        else:
            print_error(f"依赖设置失败: {dep['service']}")
            all_success = False

    return all_success


async def test_get_dependencies(session: aiohttp.ClientSession) -> bool:
    """测试7: 查询依赖关系"""
    print_section("测试7: 查询服务依赖关系")

    result = await test_api(
        session,
        "GET",
        f"{GATEWAY_URL}/api/dependencies/xiaona-service"
    )

    if result["success"]:
        print_success("依赖查询成功")
        data = result["data"]
        if data.get("success"):
            service = data["data"]["service"]
            deps = data["data"]["dependencies"]
            print(f"   📦 {service} 依赖: {', '.join(deps) if deps else '无'}")
            return True
        else:
            print_error("查询响应success为false")
            return False
    else:
        print_error(f"查询依赖失败: {result.get('error', result['data'])}")
        return False


async def test_gateway_health_detailed(session: aiohttp.ClientSession) -> bool:
    """测试8: Gateway健康详情"""
    print_section("测试8: Gateway健康详情")

    result = await test_api(session, "GET", f"{GATEWAY_URL}/api/health")

    if result["success"]:
        print_success("健康检查成功")
        data = result["data"]
        if data.get("success"):
            info = data["data"]
            print(f"   服务实例数: {info['instances']}")
            print(f"   路由数: {info['routes']}")
            print(f"   状态: {info['status']}")
            return info["status"] == "UP"
        else:
            print_error("健康检查响应success为false")
            return False
    else:
        print_error(f"健康检查失败: {result.get('error', result['data'])}")
        return False


async def test_update_instance(session: aiohttp.ClientSession) -> bool:
    """测试9: 更新服务实例"""
    print_section("测试9: 更新服务实例")

    # 先获取实例ID
    list_result = await test_api(session, "GET", f"{GATEWAY_URL}/api/services/instances")
    if not list_result["success"] or not list_result["data"].get("success"):
        print_error("无法获取实例列表")
        return False

    instances = list_result["data"]["data"]
    if not instances:
        print_error("没有可更新的实例")
        return False

    instance_id = instances[0]["id"]

    # 更新实例
    update_payload = {
        "weight": 5,
        "metadata": {"updated": True}
    }

    result = await test_api(
        session,
        "PUT",
        f"{GATEWAY_URL}/api/services/instances/{instance_id}",
        json=update_payload
    )

    if result["success"]:
        print_success(f"实例更新成功: {instance_id}")
        return True
    else:
        print_error(f"实例更新失败: {result.get('error', result['data'])}")
        return False


# ==================== 主测试流程 ====================

async def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print(f"{Colors.BOLD}Athena Gateway API功能测试{Colors.END}")
    print("="*60 + "\n")

    async with aiohttp.ClientSession() as session:
        tests = [
            ("Gateway健康检查", test_gateway_health),
            ("批量服务注册", test_batch_register),
            ("查询服务实例", test_list_instances),
            ("创建路由规则", test_create_route),
            ("查询路由规则", test_list_routes),
            ("设置依赖关系", test_set_dependencies),
            ("查询依赖关系", test_get_dependencies),
            ("Gateway健康详情", test_gateway_health_detailed),
            ("更新服务实例", test_update_instance),
        ]

        results = []
        start_time = time.time()

        for test_name, test_func in tests:
            try:
                result = await test_func(session)
                results.append((test_name, result))
            except Exception as e:
                print_error(f"{test_name}抛出异常: {str(e)}")
                results.append((test_name, False))

        # 等待一下再执行下一个测试
            await asyncio.sleep(0.5)

        duration = time.time() - start_time

        # 打印测试结果汇总
        print_section("测试结果汇总")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            if result:
                print_success(f"{test_name}")
            else:
                print_error(f"{test_name}")

        print(f"\n{Colors.BOLD}总计: {passed}/{total} 通过{Colors.END}")
        print(f"⏱️  总耗时: {duration:.2f}秒")

        if passed == total:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  部分测试失败{Colors.END}")

        return passed == total


# ==================== 入口 ====================

if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏸️  测试已中断")
        exit(130)
