#!/usr/bin/env python3
"""
Athena API Gateway 认证功能测试脚本
验证JWT令牌认证、API密钥管理和权限控制功能
"""

import asyncio
import logging
from datetime import datetime

import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gateway配置
GATEWAY_URL = "http://localhost:8080"


class AuthTester:
    """认证功能测试器"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.access_token = None
        self.api_key = None

    async def test_login(self):
        """测试用户登录"""
        logger.info("🔐 测试用户登录...")

        try:
            async with aiohttp.ClientSession() as session:
                # 测试管理员登录
                login_data = {"username": "admin", "password": "admin123"}

                async with session.post(
                    f"{GATEWAY_URL}/api/v1/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data["access_token"]
                        logger.info("✅ 管理员登录成功")
                        logger.info(f"  🎫 令牌: {self.access_token[:20]}...")
                        logger.info(f"  ⏰ 过期时间: {data['expires_in']} 秒")
                        logger.info(
                            f"  👤 用户: {data['user_info']['username']} ({data['user_info']['user_id']})"
                        )

                        self.test_results.append({"test": "admin_login", "status": "PASS"})

                        # 测试普通用户登录
                        await self.test_user_login()
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ 管理员登录失败: HTTP {response.status} - {error_text}")
                        self.test_results.append(
                            {
                                "test": "admin_login",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 登录测试异常: {e}")
            self.test_results.append({"test": "admin_login", "status": "FAIL", "error": str(e)})
            return False

    async def test_user_login(self):
        """测试普通用户登录"""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {"username": "testuser", "password": "test123"}

                async with session.post(
                    f"{GATEWAY_URL}/api/v1/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ 普通用户登录成功")
                        logger.info(
                            f"  👤 用户: {data['user_info']['username']} ({data['user_info']['user_id']})"
                        )
                        logger.info(f"  🔐 角色: {', '.join(data['user_info']['roles'])}")
                        logger.info(f"  🛡️ 权限: {', '.join(data['user_info']['permissions'])}")

                        self.test_results.append({"test": "user_login", "status": "PASS"})
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ 普通用户登录失败: HTTP {response.status} - {error_text}")
                        self.test_results.append(
                            {
                                "test": "user_login",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 用户登录测试异常: {e}")
            self.test_results.append({"test": "user_login", "status": "FAIL", "error": str(e)})
            return False

    async def test_invalid_login(self):
        """测试无效登录"""
        logger.info("🚫 测试无效登录...")

        try:
            async with aiohttp.ClientSession() as session:
                login_data = {"username": "invalid", "password": "wrong"}

                async with session.post(
                    f"{GATEWAY_URL}/api/v1/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 401:
                        logger.info("✅ 无效登录正确被拒绝")
                        self.test_results.append({"test": "invalid_login", "status": "PASS"})
                        return True
                    else:
                        logger.error(f"❌ 无效登录应该返回401，实际: HTTP {response.status}")
                        self.test_results.append(
                            {
                                "test": "invalid_login",
                                "status": "FAIL",
                                "error": f"Expected 401, got {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 无效登录测试异常: {e}")
            self.test_results.append({"test": "invalid_login", "status": "FAIL", "error": str(e)})
            return False

    async def test_jwt_authentication(self):
        """测试JWT令牌认证"""
        logger.info("🎫 测试JWT令牌认证...")

        if not self.access_token:
            logger.error("❌ 没有有效的访问令牌")
            return False

        try:
            # 测试使用JWT令牌访问受保护的API
            headers = {"Authorization": f"Bearer {self.access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GATEWAY_URL}/api/v1/auth/me",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ JWT认证成功")
                        logger.info(f"  👤 用户: {data['username']} ({data['user_id']})")
                        logger.info(f"  🛡️ 权限: {', '.join(data['permissions'])}")

                        self.test_results.append({"test": "jwt_auth", "status": "PASS"})
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ JWT认证失败: HTTP {response.status} - {error_text}")
                        self.test_results.append(
                            {
                                "test": "jwt_auth",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ JWT认证测试异常: {e}")
            self.test_results.append({"test": "jwt_auth", "status": "FAIL", "error": str(e)})
            return False

    async def test_api_key_authentication(self):
        """测试API密钥认证"""
        logger.info("🔑 测试API密钥认证...")

        try:
            # 使用默认的测试API密钥
            self.api_key = "athena-test-key-12345"
            headers = {"X-API-Key": self.api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GATEWAY_URL}/api/users",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ API密钥认证成功")
                        logger.info(f"  👥 返回 {len(data)} 个用户")

                        self.test_results.append({"test": "api_key_auth", "status": "PASS"})
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API密钥认证失败: HTTP {response.status} - {error_text}")
                        self.test_results.append(
                            {
                                "test": "api_key_auth",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ API密钥认证测试异常: {e}")
            self.test_results.append({"test": "api_key_auth", "status": "FAIL", "error": str(e)})
            return False

    async def test_permission_control(self):
        """测试权限控制"""
        logger.info("🛡️ 测试权限控制...")

        if not self.access_token:
            logger.error("❌ 没有有效的访问令牌")
            return False

        # 测试普通用户访问管理员API
        try:
            # 首先登录普通用户
            async with aiohttp.ClientSession() as session:
                login_data = {"username": "testuser", "password": "test123"}
                async with session.post(
                    f"{GATEWAY_URL}/api/v1/auth/login",
                    json=login_data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        user_token = data["access_token"]

                        # 尝试访问管理员API
                        headers = {"Authorization": f"Bearer {user_token}"}
                        async with session.get(
                            f"{GATEWAY_URL}/api/v1/auth/users",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as admin_response:
                            if admin_response.status == 403:
                                logger.info("✅ 权限控制正常：普通用户无法访问管理员API")
                                self.test_results.append(
                                    {"test": "permission_control", "status": "PASS"}
                                )
                                return True
                            else:
                                logger.error("❌ 权限控制失败：普通用户应该被拒绝访问管理员API")
                                self.test_results.append(
                                    {
                                        "test": "permission_control",
                                        "status": "FAIL",
                                        "error": f"Expected 403, got {admin_response.status}",
                                    }
                                )
                                return False
                    else:
                        logger.error("❌ 无法登录普通用户进行权限测试")
                        self.test_results.append(
                            {
                                "test": "permission_control",
                                "status": "FAIL",
                                "error": "User login failed",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 权限控制测试异常: {e}")
            self.test_results.append(
                {"test": "permission_control", "status": "FAIL", "error": str(e)}
            )
            return False

    async def test_api_key_management(self):
        """测试API密钥管理"""
        logger.info("🔧 测试API密钥管理...")

        if not self.access_token:
            logger.error("❌ 没有有效的访问令牌")
            return False

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}

            # 创建新的API密钥
            key_data = {"key_name": "Test Key", "permissions": ["read:api"], "expires_days": 30}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{GATEWAY_URL}/api/v1/auth/api-keys",
                    json=key_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("✅ API密钥创建成功")
                        logger.info(f"  🔑 密钥ID: {data['key_id']}")
                        logger.info(f"  📝 名称: {data['key_name']}")
                        logger.info(f"  🛡️ 权限: {', '.join(data['permissions'])}")

                        # 列出API密钥
                        async with session.get(
                            f"{GATEWAY_URL}/api/v1/auth/api-keys",
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as list_response:
                            if list_response.status == 200:
                                keys_data = await list_response.json()
                                logger.info(f"  📋 API密钥列表: {len(keys_data)} 个密钥")

                                self.test_results.append(
                                    {"test": "api_key_management", "status": "PASS"}
                                )
                                return True
                            else:
                                logger.error(f"❌ API密钥列表获取失败: HTTP {list_response.status}")
                                self.test_results.append(
                                    {
                                        "test": "api_key_management",
                                        "status": "FAIL",
                                        "error": f"HTTP {list_response.status}",
                                    }
                                )
                                return False
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API密钥创建失败: HTTP {response.status} - {error_text}")
                        self.test_results.append(
                            {
                                "test": "api_key_management",
                                "status": "FAIL",
                                "error": f"HTTP {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ API密钥管理测试异常: {e}")
            self.test_results.append(
                {"test": "api_key_management", "status": "FAIL", "error": str(e)}
            )
            return False

    async def test_unauthorized_access(self):
        """测试未授权访问"""
        logger.info("🚫 测试未授权访问...")

        try:
            async with aiohttp.ClientSession() as session:
                # 不提供认证信息访问受保护的API
                async with session.get(
                    f"{GATEWAY_URL}/api/v1/auth/me", timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 401:
                        logger.info("✅ 未授权访问正确被拒绝")
                        self.test_results.append({"test": "unauthorized_access", "status": "PASS"})
                        return True
                    else:
                        logger.error(f"❌ 未授权访问应该返回401，实际: HTTP {response.status}")
                        self.test_results.append(
                            {
                                "test": "unauthorized_access",
                                "status": "FAIL",
                                "error": f"Expected 401, got {response.status}",
                            }
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ 未授权访问测试异常: {e}")
            self.test_results.append(
                {"test": "unauthorized_access", "status": "FAIL", "error": str(e)}
            )
            return False

    async def generate_test_report(self):
        """生成测试报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests

        print("\n" + "=" * 60)
        print("🔐 Athena API Gateway 认证功能测试报告")
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
                print(f"  {status_icon} {test_name}")
            else:
                error_info = result.get("error", "未知错误")
                print(f"  {status_icon} {test_name} - {error_info}")

        print("\n" + "=" * 60)

        if failed_tests == 0:
            print("🎉 所有认证测试通过! 安全功能正常工作。")
        else:
            print(f"⚠️ {failed_tests} 个测试失败，请检查认证配置。")

        print("=" * 60)

        return passed_tests == total_tests

    async def run_all_tests(self):
        """运行所有认证测试"""
        logger.info("🚀 开始运行 Athena API Gateway 认证功能测试套件...")

        # 等待Gateway启动
        await asyncio.sleep(2)

        # 执行测试
        tests = [
            self.test_login,
            self.test_invalid_login,
            self.test_jwt_authentication,
            self.test_api_key_authentication,
            self.test_permission_control,
            self.test_api_key_management,
            self.test_unauthorized_access,
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
    tester = AuthTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
