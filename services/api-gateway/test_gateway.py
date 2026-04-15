#!/usr/bin/env python3
"""
Athena API Gateway 测试脚本
验证微服务接入和API转发功能
"""

import asyncio
import logging
import time
from datetime import datetime

import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway配置
GATEWAY_URL = "http://localhost:8080"


class GatewayTester:
    """API Gateway测试器"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()

    async def test_gateway_health(self):
        """测试Gateway健康状态"""
        logger.info("🏥 测试Gateway健康状态...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GATEWAY_URL}/health", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Gateway健康检查通过: {data}")
                        self.test_results.append(
                            {"test": "health", "status": "PASS", "response_time": 0.1}
                        )
                        return True
                    else:
                        logger.error(f"❌ Gateway健康检查失败: HTTP {response.status}")
                        self.test_results.append(
                            {"test": "health", "status": "FAIL", "error": f"HTTP {response.status}"}
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ Gateway健康检查异常: {e}")
            self.test_results.append({"test": "health", "status": "FAIL", "error": str(e)})
            return False

    async def test_service_registration(self):
        """测试服务注册状态"""
        logger.info("📝 测试服务注册状态...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GATEWAY_URL}/api/v1/services", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        services = await response.json()
                        service_count = len(services)
                        total_instances = sum(len(instances) for instances in services.values())

                        logger.info(
                            f"✅ 服务注册检查通过: {service_count} 个服务, {total_instances} 个实例"
                        )

                        for service_name, instances in services.items():
                            healthy_count = len(
                                [inst for inst in instances if inst["status"] == "healthy"]
                            )
                            logger.info(
                                f"  📋 {service_name}: {healthy_count}/{len(instances)} 健康"
                            )

                        self.test_results.append(
                            {
                                "test": "service_registration",
                                "status": "PASS",
                                "services": service_count,
                                "instances": total_instances,
                            }
                        )
                        return service_count > 0
                    else:
                        logger.error(f"❌ 服务注册检查失败: HTTP {response.status}")
                        self.test_results.append(
                            {
                                "test": "service_registration",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 服务注册检查异常: {e}")
            self.test_results.append(
                {"test": "service_registration", "status": "FAIL", "error": str(e)}
            )
            return False

    async def test_route_configuration(self):
        """测试路由配置"""
        logger.info("🛣️ 测试路由配置...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GATEWAY_URL}/api/v1/routes", timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        routes = await response.json()
                        route_count = len(routes)

                        logger.info(f"✅ 路由配置检查通过: {route_count} 个路由")

                        for path, route in routes.items():
                            logger.info(
                                f"  🔗 {path} -> {route['service_name']} ({', '.join(route['methods'])})"
                            )

                        self.test_results.append(
                            {"test": "route_configuration", "status": "PASS", "routes": route_count}
                        )
                        return route_count > 0
                    else:
                        logger.error(f"❌ 路由配置检查失败: HTTP {response.status}")
                        self.test_results.append(
                            {
                                "test": "route_configuration",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 路由配置检查异常: {e}")
            self.test_results.append(
                {"test": "route_configuration", "status": "FAIL", "error": str(e)}
            )
            return False

    async def test_api_proxy(self):
        """测试API代理转发功能"""
        logger.info("🔄 测试API代理转发功能...")

        test_cases = [
            {
                "name": "用户服务-获取所有用户",
                "method": "GET",
                "path": "/api/users",
                "expected_service": "user-service",
            },
            {
                "name": "用户服务-获取指定用户",
                "method": "GET",
                "path": "/api/users/1",
                "expected_service": "user-service",
            },
            {
                "name": "产品服务-获取所有产品",
                "method": "GET",
                "path": "/api/products",
                "expected_service": "product-service",
            },
            {
                "name": "产品服务-获取指定产品",
                "method": "GET",
                "path": "/api/products/1",
                "expected_service": "product-service",
            },
            {
                "name": "产品服务-获取分类",
                "method": "GET",
                "path": "/api/categories",
                "expected_service": "product-service",
            },
        ]

        passed_tests = 0
        total_tests = len(test_cases)

        for test_case in test_cases:
            logger.info(f"  🧪 测试: {test_case['name']}")

            start_time = time.time()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=test_case["method"],
                        url=f"{GATEWAY_URL}{test_case['path']}",
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as response:
                        response_time = time.time() - start_time

                        if response.status == 200:
                            data = await response.json()
                            logger.info(
                                f"    ✅ 成功 (HTTP {response.status}, {response_time:.2f}s)"
                            )

                            # 验证返回数据
                            if isinstance(data, list):
                                logger.info(f"    📊 返回 {len(data)} 条记录")
                            elif isinstance(data, dict):
                                if "id" in data:
                                    logger.info(f"    📄 返回记录 ID: {data.get('id')}")
                                elif "categories" in data:
                                    logger.info(
                                        f"    📂 返回 {len(data.get('categories', []))} 个分类"
                                    )

                            self.test_results.append(
                                {
                                    "test": f"proxy_{test_case['name']}",
                                    "status": "PASS",
                                    "response_time": response_time,
                                    "http_status": response.status,
                                }
                            )
                            passed_tests += 1
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"    ❌ 失败 (HTTP {response.status}): {error_text[:100]}..."
                            )
                            self.test_results.append(
                                {
                                    "test": f"proxy_{test_case['name']}",
                                    "status": "FAIL",
                                    "error": f"HTTP {response.status}",
                                    "response_time": response_time,
                                }
                            )

            except Exception as e:
                response_time = time.time() - start_time
                logger.error(f"    ❌ 异常: {e}")
                self.test_results.append(
                    {
                        "test": f"proxy_{test_case['name']}",
                        "status": "FAIL",
                        "error": str(e),
                        "response_time": response_time,
                    }
                )

        logger.info(f"🔄 API代理测试完成: {passed_tests}/{total_tests} 通过")
        return passed_tests == total_tests

    async def test_error_handling(self):
        """测试错误处理"""
        logger.info("⚠️ 测试错误处理...")

        error_test_cases = [
            {"name": "不存在的路由", "path": "/api/nonexistent", "expected_status": 404},
            {"name": "不存在的用户", "path": "/api/users/999", "expected_status": 404},
            {"name": "不存在的产品", "path": "/api/products/999", "expected_status": 404},
        ]

        passed_tests = 0
        total_tests = len(error_test_cases)

        for test_case in error_test_cases:
            logger.info(f"  🧪 测试: {test_case['name']}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url=f"{GATEWAY_URL}{test_case['path']}",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status == test_case["expected_status"]:
                            logger.info(f"    ✅ 正确返回 HTTP {response.status}")
                            self.test_results.append(
                                {
                                    "test": f"error_{test_case['name']}",
                                    "status": "PASS",
                                    "expected_status": test_case["expected_status"],
                                    "actual_status": response.status,
                                }
                            )
                            passed_tests += 1
                        else:
                            logger.error(
                                f"    ❌ 期望 HTTP {test_case['expected_status']}, 实际 HTTP {response.status}"
                            )
                            self.test_results.append(
                                {
                                    "test": f"error_{test_case['name']}",
                                    "status": "FAIL",
                                    "expected_status": test_case["expected_status"],
                                    "actual_status": response.status,
                                }
                            )

            except Exception as e:
                logger.error(f"    ❌ 异常: {e}")
                self.test_results.append(
                    {"test": f"error_{test_case['name']}", "status": "FAIL", "error": str(e)}
                )

        logger.info(f"⚠️ 错误处理测试完成: {passed_tests}/{total_tests} 通过")
        return passed_tests == total_tests

    async def generate_test_report(self):
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("🧪 Athena API Gateway 测试报告")
        print("=" * 60)
        print(f"📅 测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ 测试耗时: {duration:.2f} 秒")
        print(
            f"📊 测试结果: {passed_tests}/{total_tests} 通过 ({passed_tests / total_tests * 100:.1f}%)"
        )
        print()

        # 详细结果
        print("📋 详细测试结果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            test_name = result["test"]

            if result["status"] == "PASS":
                if "response_time" in result:
                    print(f"  {status_icon} {test_name} ({result['response_time']:.2f}s)")
                else:
                    print(f"  {status_icon} {test_name}")
            else:
                error_info = result.get("error", "未知错误")
                print(f"  {status_icon} {test_name} - {error_info}")

        print("\n" + "=" * 60)

        if failed_tests == 0:
            print("🎉 所有测试通过! Athena API Gateway 运行正常。")
        else:
            print(f"⚠️ {failed_tests} 个测试失败，请检查相关配置和服务状态。")

        print("=" * 60)

        return passed_tests == total_tests

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始运行 Athena API Gateway 测试套件...")

        # 等待Gateway启动
        await asyncio.sleep(2)

        # 执行测试
        tests = [
            self.test_gateway_health,
            self.test_service_registration,
            self.test_route_configuration,
            self.test_api_proxy,
            self.test_error_handling,
        ]

        for test in tests:
            try:
                await test()
                await asyncio.sleep(1)  # 测试间隔
            except Exception as e:
                logger.error(f"测试执行异常: {e}")
                self.test_results.append({"test": test.__name__, "status": "FAIL", "error": str(e)})

        # 生成报告
        success = await self.generate_test_report()
        return success


async def main():
    """主函数"""
    tester = GatewayTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
