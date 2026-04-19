#!/usr/bin/env python3
"""
API网关适配器测试用例
提供全面的测试套件，验证服务迁移后的功能完整性
"""

import asyncio
import json
import logging
import sys
import unittest
from datetime import datetime

import aiohttp
import pytest

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("test_results.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class TestConfig:
    """测试配置"""

    # 服务端点
    GATEWAY_URL = "http://localhost:8080"
    PATENT_SEARCH_URL = "http://localhost:8050"
    PATENT_WRITING_URL = "http://localhost:8051"
    AUTH_URL = "http://localhost:8052"
    TECH_ANALYSIS_URL = "http://localhost:8053"

    # 测试超时
    DEFAULT_TIMEOUT = 30
    LONG_TIMEOUT = 120

    # 测试数据
    TEST_USER = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "roles": ["user"],
    }

    TEST_PATENT = {
        "title": "基于人工智能的专利分析系统",
        "abstract": "一种使用机器学习技术分析专利文档的系统和方法",
        "claims": [
            "一种专利分析方法，包括：获取专利文档；使用机器学习模型分析所述专利文档的特征；生成分析报告。",
            "根据权利要求1所述的方法，其中所述机器学习模型包括深度神经网络。",
        ],
        "technicalField": "人工智能",
        "technicalProblem": "传统专利分析方法效率低下",
        "technicalSolution": "使用人工智能技术提高分析效率",
        "technicalFeatures": ["机器学习模型", "专利特征提取", "自动化分析"],
        "inventionType": "invention",
    }


class BaseTestCase(unittest.TestCase):
    """基础测试类"""

    def setUp(self):
        """测试前准备"""
        self.session = None
        self.auth_token = None

    async def asyncSetUp(self):
        """异步测试前准备"""
        self.session = aiohttp.ClientSession()

    def tearDown(self):
        """测试后清理"""
        if self.session:
            asyncio.create_task(self.session.close())

    async def asyncTearDown(self):
        """异步测试后清理"""
        if self.session:
            await self.session.close()

    async def make_request(
        self,
        method: str,
        url: str,
        data: dict = None,
        headers: dict = None,
        expected_status: int = 200,
    ) -> dict:
        """发送HTTP请求"""
        try:
            if method.upper() == "GET":
                async with self.session.get(
                    url, headers=headers, timeout=TestConfig.DEFAULT_TIMEOUT
                ) as response:
                    return await self._handle_response(response, expected_status)
            elif method.upper() == "POST":
                async with self.session.post(
                    url, json=data, headers=headers, timeout=TestConfig.DEFAULT_TIMEOUT
                ) as response:
                    return await self._handle_response(response, expected_status)
            elif method.upper() == "PUT":
                async with self.session.put(
                    url, json=data, headers=headers, timeout=TestConfig.DEFAULT_TIMEOUT
                ) as response:
                    return await self._handle_response(response, expected_status)
            elif method.upper() == "DELETE":
                async with self.session.delete(
                    url, headers=headers, timeout=TestConfig.DEFAULT_TIMEOUT
                ) as response:
                    return await self._handle_response(response, expected_status)
            else:
                raise ValueError(f"Unsupported method: {method}")

        except Exception as error:
            self.fail(f"Request failed: {error}")

    async def _handle_response(
        self, response: aiohttp.ClientResponse, expected_status: int
    ) -> dict:
        """处理HTTP响应"""
        try:
            response_data = await response.json()
        except Exception:
            response_data = await response.text()

        self.assertEqual(
            response.status,
            expected_status,
            f"Expected status {expected_status}, got {response.status}",
        )

        return response_data


class TestHealthChecks(BaseTestCase):
    """健康检查测试"""

    @pytest.mark.asyncio
    async def test_gateway_health(self):
        """测试网关健康检查"""
        response = await self.make_request("GET", f"{TestConfig.GATEWAY_URL}/health")

        self.assertIn("status", response)
        self.assertEqual(response["status"], "healthy")
        self.assertIn("timestamp", response)
        self.assertIn("version", response)

    @pytest.mark.asyncio
    async def test_patent_search_health(self):
        """测试专利检索服务健康检查"""
        response = await self.make_request("GET", f"{TestConfig.PATENT_SEARCH_URL}/health")

        self.assertIn("status", response)
        self.assertEqual(response["status"], "healthy")

    @pytest.mark.asyncio
    async def test_patent_writing_health(self):
        """测试专利撰写服务健康检查"""
        response = await self.make_request("GET", f"{TestConfig.PATENT_WRITING_URL}/health")

        self.assertIn("status", response)
        self.assertEqual(response["status"], "healthy")

    @pytest.mark.asyncio
    async def test_authentication_health(self):
        """测试认证服务健康检查"""
        response = await self.make_request("GET", f"{TestConfig.AUTH_URL}/health")

        self.assertIn("status", response)
        self.assertEqual(response["status"], "healthy")

    @pytest.mark.asyncio
    async def test_technical_analysis_health(self):
        """测试技术分析服务健康检查"""
        response = await self.make_request("GET", f"{TestConfig.TECH_ANALYSIS_URL}/health")

        self.assertIn("status", response)
        self.assertEqual(response["status"], "healthy")


class TestAuthentication(BaseTestCase):
    """认证服务测试"""

    @pytest.mark.asyncio
    async def test_user_registration(self):
        """测试用户注册"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/auth/register",
            data={"type": "register", **TestConfig.TEST_USER},
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("user", response["data"])
        self.assertIn("tokens", response["data"])

        # 保存token用于后续测试
        self.auth_token = response["data"]["tokens"]["accessToken"]

    @pytest.mark.asyncio
    async def test_user_login(self):
        """测试用户登录"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/auth/login",
            data={
                "type": "login",
                "username": TestConfig.TEST_USER["username"],
                "password": TestConfig.TEST_USER["password"],
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("tokens", response["data"])

        self.auth_token = response["data"]["tokens"]["accessToken"]

    @pytest.mark.asyncio
    async def test_token_verification(self):
        """测试令牌验证"""
        if not self.auth_token:
            await self.test_user_login()

        response = await self.make_request(
            "POST", f"{TestConfig.GATEWAY_URL}/api/v1/auth/verify", data={"token": self.auth_token}
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("user", response["data"])

    @pytest.mark.asyncio
    async def test_invalid_login(self):
        """测试无效登录"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/auth/login",
            data={"type": "login", "username": "invalid", "password": "invalid"},
            expected_status=401,
        )

        self.assertFalse(response.get("success", True))
        self.assertIn("error", response)


class TestPatentSearch(BaseTestCase):
    """专利检索服务测试"""

    @pytest.mark.asyncio
    async def test_patent_search(self):
        """测试专利搜索"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/search",
            data={"query": "人工智能", "limit": 10, "offset": 0, "sortBy": "relevance"},
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("patents", response["data"])
        self.assertIn("total", response["data"])
        self.assertIsInstance(response["data"]["patents"], list)

    @pytest.mark.asyncio
    async def test_patent_analysis(self):
        """测试专利分析"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/analyze",
            data={
                "title": TestConfig.TEST_PATENT["title"],
                "abstract": TestConfig.TEST_PATENT["abstract"],
                "analysisType": "patentability",
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("analysis", response["data"])

    @pytest.mark.asyncio
    async def test_patent_rules(self):
        """测试获取专利规则"""
        response = await self.make_request(
            "GET",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/rules",
            data={"category": "novelty", "keyword": " inventive step"},
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("rules", response["data"])

    @pytest.mark.asyncio
    async def test_chat_with_agent(self):
        """测试与AI智能体对话"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/chat",
            data={"message": "请帮我分析这个专利的新颖性", "userId": "testuser"},
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("response", response["data"])


class TestPatentWriting(BaseTestCase):
    """专利撰写服务测试"""

    @pytest.mark.asyncio
    async def test_create_draft(self):
        """测试创建专利草稿"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/drafts",
            data={
                "title": TestConfig.TEST_PATENT["title"],
                "inventionType": TestConfig.TEST_PATENT["inventionType"],
                "technicalFeatures": TestConfig.TEST_PATENT["technicalFeatures"],
                "technicalField": TestConfig.TEST_PATENT["technicalField"],
                "technicalProblem": TestConfig.TEST_PATENT["technicalProblem"],
                "technicalSolution": TestConfig.TEST_PATENT["technicalSolution"],
                "claimType": "method",
                "language": "zh-CN",
                "jurisdiction": "CN",
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("patentId", response["data"])
        self.assertIn("workflowId", response["data"])

    @pytest.mark.asyncio
    async def test_generate_claims(self):
        """测试生成权利要求"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/claims/generate",
            data={
                "title": TestConfig.TEST_PATENT["title"],
                "technicalFeatures": TestConfig.TEST_PATENT["technicalFeatures"],
                "claimType": "apparatus",
                "inventionType": TestConfig.TEST_PATENT["inventionType"],
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("claims", response["data"])

    @pytest.mark.asyncio
    async def test_optimize_content(self):
        """测试优化专利内容"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/optimize",
            data={
                "patentId": "test-patent-123",
                "contentType": "claims",
                "optimizationType": "broaden",
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("optimizedContent", response["data"])

    @pytest.mark.asyncio
    async def test_workflow_status(self):
        """测试获取工作流状态"""
        response = await self.make_request(
            "GET", f"{TestConfig.GATEWAY_URL}/api/v1/patents/workflows/test-workflow-123/status"
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("status", response["data"])


class TestTechnicalAnalysis(BaseTestCase):
    """技术分析服务测试"""

    @pytest.mark.asyncio
    async def test_novelty_analysis(self):
        """测试新颖性分析"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/analysis/novelty",
            data={
                "title": TestConfig.TEST_PATENT["title"],
                "abstract": TestConfig.TEST_PATENT["abstract"],
                "claims": TestConfig.TEST_PATENT["claims"],
                "technicalField": TestConfig.TEST_PATENT["technicalField"],
                "depth": "standard",
                "databases": ["CN", "US", "EP"],
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("results", response["data"])
        self.assertIn("novelty", response["data"]["results"])

    @pytest.mark.asyncio
    async def test_inventive_step_analysis(self):
        """测试创造性分析"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/analysis/inventive-step",
            data={
                "title": TestConfig.TEST_PATENT["title"],
                "abstract": TestConfig.TEST_PATENT["abstract"],
                "technicalProblem": TestConfig.TEST_PATENT["technicalProblem"],
                "technicalSolution": TestConfig.TEST_PATENT["technicalSolution"],
                "technicalFeatures": TestConfig.TEST_PATENT["technicalFeatures"],
                "comparisonBasis": "closest_prior_art",
                "technicalLevel": "ordinary_skilled_person",
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("results", response["data"])
        self.assertIn("inventiveStep", response["data"]["results"])

    @pytest.mark.asyncio
    async def test_patentability_analysis(self):
        """测试可专利性分析"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/analysis/patentability",
            data={
                "title": TestConfig.TEST_PATENT["title"],
                "abstract": TestConfig.TEST_PATENT["abstract"],
                "claims": TestConfig.TEST_PATENT["claims"],
                "technicalField": TestConfig.TEST_PATENT["technicalField"],
                "inventionType": TestConfig.TEST_PATENT["inventionType"],
                "includeNovelty": True,
                "includeInventiveStep": True,
                "includeIndustrialApplicability": True,
            },
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("results", response["data"])
        self.assertIn("patentability", response["data"]["results"])

    @pytest.mark.asyncio
    async def test_analysis_status(self):
        """测试获取分析状态"""
        response = await self.make_request(
            "GET", f"{TestConfig.GATEWAY_URL}/api/v1/analysis/test-analysis-123/status"
        )

        self.assertTrue(response.get("success", False))
        self.assertIn("data", response)
        self.assertIn("status", response["data"])


class TestErrorHandling(BaseTestCase):
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_endpoint(self):
        """测试无效端点"""
        response = await self.make_request(
            "GET", f"{TestConfig.GATEWAY_URL}/api/v1/invalid/endpoint", expected_status=404
        )

        self.assertFalse(response.get("success", True))
        self.assertIn("error", response)

    @pytest.mark.asyncio
    async def test_missing_parameters(self):
        """测试缺少参数"""
        response = await self.make_request(
            "POST",
            f"{TestConfig.GATEWAY_URL}/api/v1/patents/search",
            data={},  # 缺少query参数
            expected_status=400,
        )

        self.assertFalse(response.get("success", True))
        self.assertIn("error", response)

    @pytest.mark.asyncio
    async def test_invalid_json(self):
        """测试无效JSON"""
        try:
            headers = {"Content-Type": "application/json"}
            async with self.session.post(
                f"{TestConfig.GATEWAY_URL}/api/v1/patents/search",
                data="invalid json",
                headers=headers,
                timeout=TestConfig.DEFAULT_TIMEOUT,
            ) as response:
                self.assertEqual(response.status, 400)
        except Exception as error:
            self.fail(f"Invalid JSON test failed: {error}")

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试限流"""
        # 快速发送多个请求
        responses = []
        for _i in range(10):
            try:
                response = await self.make_request("GET", f"{TestConfig.GATEWAY_URL}/health")
                responses.append(response.get("success", False))
            except Exception:
                responses.append(False)

        # 至少应该有一些请求成功
        self.assertTrue(any(responses))


class TestPerformance(BaseTestCase):
    """性能测试"""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """测试响应时间"""
        start_time = datetime.now()

        await self.make_request("GET", f"{TestConfig.GATEWAY_URL}/health")

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000

        # 健康检查响应时间应该小于1秒
        self.assertLess(response_time, 1000, f"Health check took too long: {response_time}ms")

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求"""

        async def make_request_async():
            return await self.make_request("GET", f"{TestConfig.GATEWAY_URL}/health")

        # 并发执行10个请求
        tasks = [make_request_async() for _ in range(10)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查所有请求都成功
        successful_responses = [
            r for r in responses if isinstance(r, dict) and r.get("success", False)
        ]
        self.assertGreaterEqual(len(successful_responses), 8, "Too many concurrent requests failed")


class TestReporter:
    """测试报告生成器"""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()

    def add_result(self, test_name: str, status: str, duration: float, error: str = None):
        """添加测试结果"""
        self.test_results.append(
            {
                "test_name": test_name,
                "status": status,  # passed, failed, error
                "duration": duration,
                "error": error,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def generate_report(self) -> dict:
        """生成测试报告"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        passed_count = len([r for r in self.test_results if r["status"] == "passed"])
        failed_count = len([r for r in self.test_results if r["status"] == "failed"])
        error_count = len([r for r in self.test_results if r["status"] == "error"])
        total_count = len(self.test_results)

        report = {
            "test_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": total_duration,
                "total_tests": total_count,
                "passed": passed_count,
                "failed": failed_count,
                "errors": error_count,
                "success_rate": (passed_count / total_count * 100) if total_count > 0 else 0,
            },
            "test_results": self.test_results,
            "coverage": {
                "health_checks": len([r for r in self.test_results if "health" in r["test_name"]]),
                "authentication": len([r for r in self.test_results if "auth" in r["test_name"]]),
                "patent_search": len(
                    [r for r in self.test_results if "patent_search" in r["test_name"]]
                ),
                "patent_writing": len(
                    [r for r in self.test_results if "patent_writing" in r["test_name"]]
                ),
                "technical_analysis": len(
                    [r for r in self.test_results if "technical_analysis" in r["test_name"]]
                ),
                "error_handling": len([r for r in self.test_results if "error" in r["test_name"]]),
                "performance": len(
                    [r for r in self.test_results if "performance" in r["test_name"]]
                ),
            },
        }

        # 保存报告
        report_path = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report


async def main():
    """主测试函数"""
    print("开始API网关适配器测试...")

    # 创建测试报告器
    reporter = TestReporter()

    # 测试套件列表
    test_suites = [
        ("Health Checks", TestHealthChecks),
        ("Authentication", TestAuthentication),
        ("Patent Search", TestPatentSearch),
        ("Patent Writing", TestPatentWriting),
        ("Technical Analysis", TestTechnicalAnalysis),
        ("Error Handling", TestErrorHandling),
        ("Performance", TestPerformance),
    ]

    # 执行测试套件
    for suite_name, test_class in test_suites:
        print(f"\n执行测试套件: {suite_name}")

        # 获取测试方法
        test_methods = [method for method in dir(test_class) if method.startswith("test_")]

        for test_method_name in test_methods:
            test_instance = test_class(test_method_name)

            try:
                await test_instance.asyncSetUp()
                start_time = datetime.now()

                # 执行测试
                test_method = getattr(test_instance, test_method_name)
                await test_method()

                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                reporter.add_result(test_method_name, "passed", duration)
                print(f"  ✓ {test_method_name} ({duration:.2f}s)")

            except Exception as error:
                reporter.add_result(test_method_name, "failed", 0, str(error))
                print(f"  ✗ {test_method_name}: {error}")

            finally:
                try:
                    await test_instance.asyncTearDown()
                except Exception:
                    pass

    # 生成报告
    report = reporter.generate_report()

    print("\n测试完成!")
    print(f"总计: {report['test_summary']['total_tests']}")
    print(f"通过: {report['test_summary']['passed']}")
    print(f"失败: {report['test_summary']['failed']}")
    print(f"错误: {report['test_summary']['errors']}")
    print(f"成功率: {report['test_summary']['success_rate']:.1f}%")
    print(f"总耗时: {report['test_summary']['total_duration']:.2f}s")

    return 0 if report["test_summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
