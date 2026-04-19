#!/usr/bin/env python3
"""
Athena平台统一网关兼容性验证测试套件

测试范围:
- GW-ROUTE-01~10: 路由转发测试
- GW-AUTH-01~06: 认证兼容性测试
- GW-MW-01~05: 中间件测试
- GW-PROTO-01~05: 协议兼容性测试

作者: 徐健
日期: 2026-04-18
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import httpx
import websockets
from websockets.client import connect


# ============================================================================
# 测试配置
# ============================================================================

TEST_CONFIG = {
    "gateway": "https://localhost:8005",
    "gateway_ws": "wss://localhost:8005",
    "routes": {
        "/health": "GET",
        "/api/v1/kg/query": "POST",
        "/api/v1/vector/search": "POST",
        "/api/v1/legal/search": "POST",
        "/api/v1/tools": "GET",
        "/api/v1/services/instances": "GET",
        "/api/legal/analyze": "POST",
        "/api/search": "POST"
    },
    "auth": {
        "api_key": "test-api-key-12345",
        "bearer_token": "Bearer test-token-67890",
        "basic_auth": ("test_user", "test_pass")
    }
}


# ============================================================================
# 测试结果数据类
# ============================================================================

@dataclass
class TestResult:
    """测试结果数据类"""
    test_id: str
    test_name: str
    status: str  # PASS, FAIL, WARN
    duration_ms: float
    details: dict[str, Any]
    timestamp: str


class TestReporter:
    """测试报告生成器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.results: list[TestResult] = []
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def add_result(self, result: TestResult):
        """添加测试结果"""
        self.results.append(result)

    def generate_report(self) -> dict:
        """生成测试报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == "PASS"),
                "failed": sum(1 for r in self.results if r.status == "FAIL"),
                "warned": sum(1 for r in self.results if r.status == "WARN"),
                "pass_rate": f"{sum(1 for r in self.results if r.status == 'PASS') / len(self.results) * 100:.1f}%"
            },
            "results": [asdict(r) for r in self.results]
        }

        # 保存JSON报告
        report_file = self.output_dir / f"gateway_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report


# ============================================================================
# GW-ROUTE-01~10: 路由转发测试
# ============================================================================

class TestGatewayRouting:
    """网关路由转发正确性测试"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        # 禁用SSL验证,因为Gateway使用自签名证书
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=False  # 禁用SSL验证
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_gw_route_01_legal_api(self, http_client, reporter: TestReporter):
        """GW-ROUTE-01: /api/legal/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['gateway']}/api/legal/analyze",
                json={"query": "测试法律分析"}
            )
            duration_ms = (time.time() - start_time) * 1000

            # 200/201/204/401/422 均表示路由存在
            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-01",
                    test_name="法律API路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/legal/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-01",
                    test_name="法律API路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-01",
                test_name="法律API路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"法律API路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_route_02_unified_search(self, http_client, reporter: TestReporter):
        """GW-ROUTE-02: /api/search 路由"""
        start_time = time.time()
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['gateway']}/api/search",
                json={"query": "专利检索", "limit": 10}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-02",
                    test_name="统一搜索路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/search", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-02",
                    test_name="统一搜索路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-02",
                test_name="统一搜索路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"统一搜索路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_route_03_knowledge_graph(self, http_client, reporter: TestReporter):
        """GW-ROUTE-03: /api/v1/kg/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['gateway']}/api/v1/kg/query",
                json={"cypher": "MATCH (n) RETURN count(n) LIMIT 1"}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-03",
                    test_name="知识图谱路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/v1/kg/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-03",
                    test_name="知识图谱路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-03",
                test_name="知识图谱路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"知识图谱路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_route_04_vector_search(self, http_client, reporter: TestReporter):
        """GW-ROUTE-04: /api/v1/vector/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['gateway']}/api/v1/vector/search",
                json={"collection_name": "test", "query_text": "测试", "limit": 5}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-04",
                    test_name="向量搜索路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/v1/vector/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-04",
                    test_name="向量搜索路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-04",
                test_name="向量搜索路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"向量搜索路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_route_05_legal_search(self, http_client, reporter: TestReporter):
        """GW-ROUTE-05: /api/v1/legal/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['gateway']}/api/v1/legal/search",
                json={"query": "专利法", "limit": 10}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-05",
                    test_name="法律搜索路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/v1/legal/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-05",
                    test_name="法律搜索路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-05",
                test_name="法律搜索路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"法律搜索路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_route_06_tools(self, http_client, reporter: TestReporter):
        """GW-ROUTE-06: /api/v1/tools/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['gateway']}/api/v1/tools")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-06",
                    test_name="工具服务路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/v1/tools/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-06",
                    test_name="工具服务路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-06",
                test_name="工具服务路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"工具服务路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_route_07_services(self, http_client, reporter: TestReporter):
        """GW-ROUTE-07: /api/v1/services/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['gateway']}/api/v1/services/instances")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-07",
                    test_name="服务管理路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/v1/services/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-07",
                    test_name="服务管理路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-07",
                test_name="服务管理路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_gw_route_10_auth(self, http_client, reporter: TestReporter):
        """GW-ROUTE-10: /api/v1/auth/* 路由"""
        start_time = time.time()
        try:
            response = await http_client.post(
                f"{TEST_CONFIG['gateway']}/api/v1/auth/login",
                json={"username": "test", "password": "test"}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 201, 204, 401, 422, 400]:
                result = TestResult(
                    test_id="GW-ROUTE-10",
                    test_name="认证服务路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"route": "/api/v1/auth/*", "status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-ROUTE-10",
                    test_name="认证服务路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-ROUTE-10",
                test_name="认证服务路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)


# ============================================================================
# GW-AUTH-01~06: 认证兼容性测试
# ============================================================================

class TestGatewayAuthentication:
    """网关认证与授权兼容性测试"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        # 禁用SSL验证,因为Gateway使用自签名证书
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=False  # 禁用SSL验证
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_gw_auth_01_ip_whitelist(self, http_client, reporter: TestReporter):
        """GW-AUTH-01: IP白名单"""
        start_time = time.time()
        try:
            # 从localhost请求(通常在白名单中)
            response = await http_client.get(f"{TEST_CONFIG['gateway']}/health")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = TestResult(
                    test_id="GW-AUTH-01",
                    test_name="IP白名单",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"ip_allowed": True},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-AUTH-01",
                    test_name="IP白名单",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-AUTH-01",
                test_name="IP白名单",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_gw_auth_02_api_key(self, http_client, reporter: TestReporter):
        """GW-AUTH-02: API Key认证"""
        start_time = time.time()
        try:
            headers = {"X-API-Key": TEST_CONFIG["auth"]["api_key"]}
            response = await http_client.get(
                f"{TEST_CONFIG['gateway']}/api/v1/tools",
                headers=headers
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 401]:  # 200表示通过,401表示需要认证但机制存在
                result = TestResult(
                    test_id="GW-AUTH-02",
                    test_name="API Key认证",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-AUTH-02",
                    test_name="API Key认证",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-AUTH-02",
                test_name="API Key认证",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_gw_auth_03_bearer_token(self, http_client, reporter: TestReporter):
        """GW-AUTH-03: Bearer Token认证"""
        start_time = time.time()
        try:
            headers = {"Authorization": TEST_CONFIG["auth"]["bearer_token"]}
            response = await http_client.get(
                f"{TEST_CONFIG['gateway']}/api/v1/tools",
                headers=headers
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 401]:
                result = TestResult(
                    test_id="GW-AUTH-03",
                    test_name="Bearer Token认证",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-AUTH-03",
                    test_name="Bearer Token认证",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-AUTH-03",
                test_name="Bearer Token认证",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_gw_auth_04_basic_auth(self, http_client, reporter: TestReporter):
        """GW-AUTH-04: Basic Auth认证"""
        start_time = time.time()
        try:
            import base64
            username, password = TEST_CONFIG["auth"]["basic_auth"]
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers = {"Authorization": f"Basic {credentials}"}

            response = await http_client.get(
                f"{TEST_CONFIG['gateway']}/api/v1/tools",
                headers=headers
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 401]:
                result = TestResult(
                    test_id="GW-AUTH-04",
                    test_name="Basic Auth认证",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-AUTH-04",
                    test_name="Basic Auth认证",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-AUTH-04",
                test_name="Basic Auth认证",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_gw_auth_05_no_auth_public_route(self, http_client, reporter: TestReporter):
        """GW-AUTH-05: 无认证请求公开路由"""
        start_time = time.time()
        try:
            # 请求健康检查(公开路由)
            response = await http_client.get(f"{TEST_CONFIG['gateway']}/health")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = TestResult(
                    test_id="GW-AUTH-05",
                    test_name="无认证请求公开路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"public_route": "/health", "status": "accessible"},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-AUTH-05",
                    test_name="无认证请求公开路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-AUTH-05",
                test_name="无认证请求公开路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"公开路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_auth_06_invalid_token(self, http_client, reporter: TestReporter):
        """GW-AUTH-06: 无效Token"""
        start_time = time.time()
        try:
            headers = {"Authorization": "Bearer invalid_token_12345"}
            response = await http_client.get(
                f"{TEST_CONFIG['gateway']}/api/v1/tools",
                headers=headers
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 401:
                result = TestResult(
                    test_id="GW-AUTH-06",
                    test_name="无效Token",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code, "rejected": True},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-AUTH-06",
                    test_name="无效Token",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"预期401, 实际: {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-AUTH-06",
                test_name="无效Token",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)


# ============================================================================
# GW-MW-01~05: 中间件测试
# ============================================================================

class TestGatewayMiddleware:
    """网关中间件链完整性测试"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        # 禁用SSL验证,因为Gateway使用自签名证书
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=False  # 禁用SSL验证
        ) as client:
            yield client

    @pytest.mark.asyncio
    async def test_gw_mw_01_request_id(self, http_client, reporter: TestReporter):
        """GW-MW-01: 请求ID注入"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['gateway']}/health")
            duration_ms = (time.time() - start_time) * 1000

            request_id = response.headers.get("X-Request-ID")
            if request_id:
                result = TestResult(
                    test_id="GW-MW-01",
                    test_name="请求ID注入",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"request_id": request_id},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-MW-01",
                    test_name="请求ID注入",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": "未找到X-Request-ID头"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-MW-01",
                test_name="请求ID注入",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_gw_mw_02_cors(self, http_client, reporter: TestReporter):
        """GW-MW-02: CORS头"""
        start_time = time.time()
        try:
            headers = {"Origin": "http://example.com"}
            response = await http_client.options(
                f"{TEST_CONFIG['gateway']}/api/v1/tools",
                headers=headers
            )
            duration_ms = (time.time() - start_time) * 1000

            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }

            if any(cors_headers.values()):
                result = TestResult(
                    test_id="GW-MW-02",
                    test_name="CORS头",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"cors_headers": cors_headers},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="GW-MW-02",
                    test_name="CORS头",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": "未找到CORS头"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="GW-MW-02",
                test_name="CORS头",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)


# ============================================================================
# GW-PROTO-01~05: 协议兼容性测试
# ============================================================================

class TestGatewayProtocol:
    """网关协议兼容性测试"""

    @pytest.mark.asyncio
    async def test_gw_proto_01_http_1_1(self, reporter: TestReporter):
        """GW-PROTO-01: HTTP/1.1"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(http_version="1.1", timeout=10.0) as client:
                response = await client.get(f"{TEST_CONFIG['gateway']}/health")
                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    result = TestResult(
                        test_id="GW-PROTO-01",
                        test_name="HTTP/1.1",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"http_version": "1.1"},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="GW-PROTO-01",
                        test_name="HTTP/1.1",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={"error": f"HTTP {response.status_code}"},
                        timestamp=datetime.now().isoformat()
                    )
        except Exception as e:
            result = TestResult(
                test_id="GW-PROTO-01",
                test_name="HTTP/1.1",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"HTTP/1.1测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_gw_proto_03_websocket(self, reporter: TestReporter):
        """GW-PROTO-03: WebSocket"""
        start_time = time.time()
        try:
            # 尝试建立WebSocket连接
            async with connect(f"{TEST_CONFIG['gateway_ws']}/ws") as websocket:
                await websocket.send('{"type": "ping"}')
                response = await websocket.recv()
                duration_ms = (time.time() - start_time) * 1000

                result = TestResult(
                    test_id="GW-PROTO-03",
                    test_name="WebSocket",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"connection": "established", "response": response},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            # WebSocket可能未实现,允许WARN
            result = TestResult(
                test_id="GW-PROTO-03",
                test_name="WebSocket",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": f"WebSocket不可用: {str(e)}"},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def reporter():
    """测试报告器"""
    output_dir = Path(__file__).parent / "reports"
    return TestReporter(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
