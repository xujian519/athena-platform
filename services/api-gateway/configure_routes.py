#!/usr/bin/env python3
"""
Athena API Gateway 路由配置脚本
用于配置微服务的路由规则
"""

import asyncio
import logging

import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway配置
GATEWAY_URL = "http://localhost:8080"

# 路由配置
ROUTES_CONFIG = [
    {
        "path": "/api/v1/legal/*",
        "service_name": "legal-world-model",
        "methods": ["GET", "POST"],
        "strip_prefix": True,
        "timeout": 30,
        "retries": 3,
        "rate_limit": {"requests_per_minute": 50},
        "auth_required": False,
        "cors_enabled": True,
    },
    {
        "path": "/api/users/*",
        "service_name": "user-service",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "strip_prefix": True,
        "timeout": 30,
        "retries": 3,
        "rate_limit": {"requests_per_minute": 100},
        "auth_required": False,
        "cors_enabled": True,
    },
    {
        "path": "/api/products/*",
        "service_name": "product-service",
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "strip_prefix": True,
        "timeout": 30,
        "retries": 2,
        "rate_limit": {"requests_per_minute": 200},
        "auth_required": False,
        "cors_enabled": True,
    },
    {
        "path": "/api/categories",
        "service_name": "product-service",
        "methods": ["GET"],
        "strip_prefix": True,
        "timeout": 15,
        "retries": 1,
        "rate_limit": {"requests_per_minute": 50},
        "auth_required": False,
        "cors_enabled": True,
    },
]


async def configure_routes():
    """配置所有路由"""
    success_count = 0
    error_count = 0

    async with aiohttp.ClientSession() as session:
        for route_config in ROUTES_CONFIG:
            try:
                logger.info(f"配置路由: {route_config['path']} -> {route_config['service_name']}")

                async with session.post(
                    f"{GATEWAY_URL}/api/v1/routes",
                    json=route_config,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info(f"路由配置成功: {route_config['path']}")
                        success_count += 1
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"路由配置失败 {route_config['path']}: HTTP {response.status} - {error_text}"
                        )
                        error_count += 1

            except Exception as e:
                logger.error(f"路由配置异常 {route_config['path']}: {e}")
                error_count += 1

    logger.info(f"路由配置完成 - 成功: {success_count}, 失败: {error_count}")
    return success_count, error_count


async def show_current_routes():
    """显示当前所有路由"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GATEWAY_URL}/api/v1/routes", timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    routes = await response.json()
                    logger.info("当前配置的路由:")

                    for path, route in routes.items():
                        logger.info(
                            f"  {path} -> {route['service_name']} ({', '.join(route['methods'])})"
                        )

                    return routes
                else:
                    logger.error(f"获取路由失败: HTTP {response.status}")
                    return None
    except Exception as e:
        logger.error(f"获取路由异常: {e}")
        return None


async def show_current_services():
    """显示当前所有服务"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GATEWAY_URL}/api/v1/services", timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    services = await response.json()
                    logger.info("当前注册的服务:")

                    for service_name, instances in services.items():
                        healthy_count = len(
                            [inst for inst in instances if inst["status"] == "healthy"]
                        )
                        total_count = len(instances)
                        logger.info(f"  {service_name}: {healthy_count}/{total_count} 健康")

                        for inst in instances:
                            status_icon = "✅" if inst["status"] == "healthy" else "❌"
                            logger.info(
                                f"    {status_icon} {inst['instance_id']} - {inst['host']}:{inst['port']}"
                            )

                    return services
                else:
                    logger.error(f"获取服务失败: HTTP {response.status}")
                    return None
    except Exception as e:
        logger.error(f"获取服务异常: {e}")
        return None


async def main():
    """主函数：配置所有路由"""
    print("🔧 开始配置Athena API Gateway路由...")

    # 注册法律世界模型路由
    legal_routes = [
        {
            "path": "/api/v1/legal/prompt/generate",
            "service_name": "legal-world-model",
            "methods": ["POST"],
            "description": "法律动态提示词生成接口",
        },
        {
            "path": "/api/v1/legal/planner/plan",
            "service_name": "legal-world-model",
            "methods": ["POST"],
            "description": "智能体执行计划生成接口",
        },
        {
            "path": "/api/v1/legal/health",
            "service_name": "legal-world-model",
            "methods": ["GET"],
            "description": "法律世界模型健康检查接口",
        },
    ]

    # 合并所有路由配置
    all_routes = ROUTES_CONFIG + legal_routes

    success_count = 0
    for route_config in all_routes:
        try:
            # 发送路由配置请求
            async with aiohttp.ClientSession() as session:
                payload = {
                    "path": route_config["path"],
                    "service_name": route_config["service_name"],
                    "methods": route_config["methods"],
                    "strip_prefix": route_config.get("strip_prefix", True),
                    "timeout": route_config.get("timeout", 30),
                    "retries": route_config.get("retries", 3),
                    "rate_limit": route_config.get("rate_limit"),
                    "auth_required": route_config.get("auth_required", False),
                    "cors_enabled": route_config.get("cors_enabled", True),
                    "description": route_config.get("description", ""),
                }

                async with session.post(f"{GATEWAY_URL}/api/v1/routes", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success", False):
                            logger.error(
                                f"路由配置失败: {route_config['path']} - {result.get('detail', 'Unknown error')}"
                            )
                        else:
                            logger.info(
                                f"✅ 路由配置成功: {route_config['path']} -> {result.get('message', 'Success')}"
                            )
                            success_count += 1
                    else:
                        logger.error(
                            f"路由配置请求失败: {response.status} - {route_config['path']}"
                        )

        except Exception as e:
            logger.error(f"配置路由 {route_config['path']} 失败: {e}")

    print("\n📊 路由配置完成")
    print(f"✅ 成功配置: {success_count}/{len(all_routes)} 个路由")
    print(f"❌ 失败配置: {len(all_routes) - success_count} 个路由")

    if success_count == len(all_routes):
        print("\n🎉 法律世界模型API已成功注册到Athena统一网关！")
    else:
        print("\n⚠️ 部分路由配置失败，请检查网关服务状态")
    """主函数"""
    print("=" * 60)
    print("Athena API Gateway 路由配置工具")
    print("=" * 60)

    # 等待Gateway启动
    logger.info("等待API Gateway启动...")
    await asyncio.sleep(3)

    # 检查Gateway健康状态
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GATEWAY_URL}/health", timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"API Gateway状态: {health_data['status']}")
                else:
                    logger.error("API Gateway未就绪")
                    return
    except Exception as e:
        logger.error(f"无法连接到API Gateway: {e}")
        logger.info("请确保API Gateway已启动: ./start_gateway.sh start")
        return

    # 显示当前服务状态
    print("\n📊 当前服务状态:")
    await show_current_services()

    # 显示当前路由配置
    print("\n🛣️ 当前路由配置:")
    await show_current_routes()

    # 配置新路由
    print("\n⚙️ 配置路由规则...")
    success, error = await configure_routes()

    if error == 0:
        print("✅ 所有路由配置成功!")
    else:
        print(f"⚠️ {error} 个路由配置失败，请检查日志")

    # 显示最终路由配置
    print("\n📋 最终路由配置:")
    await show_current_routes()

    print("\n" + "=" * 60)
    print("配置完成!")
    print("API Gateway地址: http://localhost:8080")
    print("API文档: http://localhost:8080/docs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
