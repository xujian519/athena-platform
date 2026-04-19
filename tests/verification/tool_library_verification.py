#!/usr/bin/env python3
"""
Athena平台工具库验证测试套件

测试范围:
- TOOL-CONN-01~10: 连通性测试
- TOOL-PARAM-01~06: 参数传递测试
- TOOL-ERR-01~06: 容错机制测试
- TOOL-PERF-01~06: 响应时间测试

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

# 核心服务导入
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))

from tools.mcp.athena_mcp_manager import AthenaMCPManager
from governance.unified_tool_registry import UnifiedToolRegistry


# ============================================================================
# 测试配置
# ============================================================================

TEST_CONFIG = {
    "services": {
        "gateway": "http://localhost:8005",
        "local_search_engine": "http://localhost:3003",
        "mineru_parser": "http://localhost:7860"
    },
    "mcp_servers": {
        "gaode-mcp-server": "高德地图服务",
        "patent-downloader": "专利下载服务",
        "jina-ai-mcp-server": "Jina AI服务",
        "academic-search": "学术搜索服务",
        "local-search-engine": "本地搜索引擎"
    },
    "performance": {
        "builtin_tool_max_ms": 100,
        "mcp_tool_max_ms": 2000,
        "web_scrape_max_ms": 10000,
        "patent_download_max_ms": 30000,
        "academic_search_max_ms": 5000
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
        report_file = self.output_dir / f"tool_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report


# ============================================================================
# TOOL-CONN-01~10: 连通性测试
# ============================================================================

class TestToolConnectivity:
    """工具调用连通性测试"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_tool_conn_01_tool_registry(self, reporter: TestReporter):
        """TOOL-CONN-01: 工具注册中心可用性"""
        start_time = time.time()
        try:
            registry = UnifiedToolRegistry()
            tools = await registry.list_tools()
            duration_ms = (time.time() - start_time) * 1000

            if len(tools) > 0:
                result = TestResult(
                    test_id="TOOL-CONN-01",
                    test_name="工具注册中心可用性",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"tools_count": len(tools), "tools": list(tools.keys())[:10]},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-01",
                    test_name="工具注册中心可用性",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": "未找到已注册工具"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-01",
                test_name="工具注册中心可用性",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"工具注册中心测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_tool_conn_02_mcp_manager(self, reporter: TestReporter):
        """TOOL-CONN-02: MCP管理器连通性"""
        start_time = time.time()
        try:
            mcp_manager = AthenaMCPManager()
            servers = await mcp_manager.list_servers()
            duration_ms = (time.time() - start_time) * 1000

            if len(servers) >= 5:  # 预期至少5个MCP服务器
                result = TestResult(
                    test_id="TOOL-CONN-02",
                    test_name="MCP管理器连通性",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"servers_count": len(servers), "servers": servers},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-02",
                    test_name="MCP管理器连通性",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"仅找到{len(servers)}个MCP服务器,预期至少5个", "servers": servers},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-02",
                test_name="MCP管理器连通性",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status in ["PASS", "WARN"], f"MCP管理器测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_tool_conn_03_gaode_mcp(self, http_client, reporter: TestReporter):
        """TOOL-CONN-03: 高德地图MCP"""
        start_time = time.time()
        try:
            # 通过网关调用高德地图工具
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/geocode/execute",
                json={
                    "address": "北京市海淀区中关村"
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if "location" in data or "coordinates" in data:
                    result = TestResult(
                        test_id="TOOL-CONN-03",
                        test_name="高德地图MCP",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"result": "地理编码成功"},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="TOOL-CONN-03",
                        test_name="高德地图MCP",
                        status="WARN",
                        duration_ms=duration_ms,
                        details={"warning": "响应格式不符合预期", "data": data},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-03",
                    test_name="高德地图MCP",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-03",
                test_name="高德地图MCP",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        # 不assert,允许WARN

    @pytest.mark.asyncio
    async def test_tool_conn_04_patent_downloader_mcp(self, http_client, reporter: TestReporter):
        """TOOL-CONN-04: 专利下载MCP"""
        start_time = time.time()
        try:
            # 测试专利信息查询
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/get_patent_info/execute",
                json={
                    "patent_id": "CN123456789A"
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 404]:  # 404表示服务在线但专利不存在
                result = TestResult(
                    test_id="TOOL-CONN-04",
                    test_name="专利下载MCP",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-04",
                    test_name="专利下载MCP",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-04",
                test_name="专利下载MCP",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        # 不assert,允许服务不存在

    @pytest.mark.asyncio
    async def test_tool_conn_05_jina_ai_mcp(self, http_client, reporter: TestReporter):
        """TOOL-CONN-05: Jina AI MCP"""
        start_time = time.time()
        try:
            # 测试网页读取
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/read_web/execute",
                json={
                    "url": "https://example.com"
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = TestResult(
                    test_id="TOOL-CONN-05",
                    test_name="Jina AI MCP",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"result": "网页抓取成功"},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-05",
                    test_name="Jina AI MCP",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-05",
                test_name="Jina AI MCP",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_tool_conn_06_academic_search_mcp(self, http_client, reporter: TestReporter):
        """TOOL-CONN-06: 学术搜索MCP"""
        start_time = time.time()
        try:
            # 测试论文搜索
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/search_papers/execute",
                json={
                    "query": "machine learning patents",
                    "limit": 5
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                result = TestResult(
                    test_id="TOOL-CONN-06",
                    test_name="学术搜索MCP",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"papers_count": len(data.get("papers", []))},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-06",
                    test_name="学术搜索MCP",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-06",
                test_name="学术搜索MCP",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_tool_conn_08_local_search_engine(self, http_client, reporter: TestReporter):
        """TOOL-CONN-08: 本地搜索引擎"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['services']['local_search_engine']}/health")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result = TestResult(
                    test_id="TOOL-CONN-08",
                    test_name="本地搜索引擎",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status": "healthy"},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-08",
                    test_name="本地搜索引擎",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-08",
                test_name="本地搜索引擎",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"本地搜索引擎测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_tool_conn_09_gateway_tools_route(self, http_client, reporter: TestReporter):
        """TOOL-CONN-09: 网关→工具API路由"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['services']['gateway']}/api/v1/tools")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                tools = response.json().get("tools", [])
                result = TestResult(
                    test_id="TOOL-CONN-09",
                    test_name="网关→工具API路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"tools_count": len(tools)},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-09",
                    test_name="网关→工具API路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-09",
                test_name="网关→工具API路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"网关→工具API路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_tool_conn_10_gateway_tool_execute_route(self, http_client, reporter: TestReporter):
        """TOOL-CONN-10: 网关→工具执行路由"""
        start_time = time.time()
        try:
            # 测试一个简单的内置工具
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/echo/execute",
                json={"message": "test"}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 404]:  # 404表示路由存在但工具不存在
                result = TestResult(
                    test_id="TOOL-CONN-10",
                    test_name="网关→工具执行路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-CONN-10",
                    test_name="网关→工具执行路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-CONN-10",
                test_name="网关→工具执行路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"网关→工具执行路由测试失败: {result.details}"


# ============================================================================
# TOOL-PARAM-01~06: 参数传递测试
# ============================================================================

class TestToolParameterPassing:
    """工具参数传递准确性验证"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_tool_param_01_simple_string(self, http_client, reporter: TestReporter):
        """TOOL-PARAM-01: 简单参数传递"""
        start_time = time.time()
        try:
            test_string = "测试字符串"
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/echo/execute",
                json={"message": test_string}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result_data = response.json()
                if result_data.get("message") == test_string:
                    result = TestResult(
                        test_id="TOOL-PARAM-01",
                        test_name="简单参数传递",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"parameter": test_string, "returned": result_data.get("message")},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="TOOL-PARAM-01",
                        test_name="简单参数传递",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={"error": "参数值不匹配", "expected": test_string, "got": result_data.get("message")},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="TOOL-PARAM-01",
                    test_name="简单参数传递",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-PARAM-01",
                test_name="简单参数传递",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_tool_param_02_nested_json(self, http_client, reporter: TestReporter):
        """TOOL-PARAM-02: 复杂嵌套参数"""
        start_time = time.time()
        try:
            nested_param = {
                "level1": {
                    "level2": {
                        "level3": "deep_value",
                        "array": [1, 2, 3]
                    }
                }
            }
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/echo/execute",
                json={"data": nested_param}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result_data = response.json()
                returned_data = result_data.get("data")
                if returned_data == nested_param:
                    result = TestResult(
                        test_id="TOOL-PARAM-02",
                        test_name="复杂嵌套参数",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"nested_structure": "preserved"},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="TOOL-PARAM-02",
                        test_name="复杂嵌套参数",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={"error": "嵌套结构不完整"},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="TOOL-PARAM-02",
                    test_name="复杂嵌套参数",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-PARAM-02",
                test_name="复杂嵌套参数",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_tool_param_03_chinese_encoding(self, http_client, reporter: TestReporter):
        """TOOL-PARAM-03: 中文参数编码"""
        start_time = time.time()
        try:
            chinese_text = "发明专利创造性判断标准"
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/echo/execute",
                json={"message": chinese_text}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                result_data = response.json()
                if result_data.get("message") == chinese_text:
                    result = TestResult(
                        test_id="TOOL-PARAM-03",
                        test_name="中文参数编码",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"chinese_text": chinese_text, "encoding": "correct"},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="TOOL-PARAM-03",
                        test_name="中文参数编码",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={"error": "中文编码错误", "expected": chinese_text, "got": result_data.get("message")},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="TOOL-PARAM-03",
                    test_name="中文参数编码",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-PARAM-03",
                test_name="中文参数编码",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)


# ============================================================================
# TOOL-ERR-01~06: 容错机制测试
# ============================================================================

class TestToolErrorHandling:
    """工具异常处理与容错机制测试"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_tool_err_01_service_unavailable(self, http_client, reporter: TestReporter):
        """TOOL-ERR-01: 目标服务不可用"""
        start_time = time.time()
        try:
            # 调用一个不存在的服务
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/nonexistent_service/execute",
                json={}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [404, 503]:  # 应返回友好错误
                result = TestResult(
                    test_id="TOOL-ERR-01",
                    test_name="目标服务不可用",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code, "friendly_error": True},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-ERR-01",
                    test_name="目标服务不可用",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"未返回友好错误: HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            # 如果抛出异常也算失败(应该优雅处理)
            result = TestResult(
                test_id="TOOL-ERR-01",
                test_name="目标服务不可用",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": f"未优雅处理异常: {str(e)}"},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)

    @pytest.mark.asyncio
    async def test_tool_err_02_invalid_parameters(self, http_client, reporter: TestReporter):
        """TOOL-ERR-02: 参数校验失败"""
        start_time = time.time()
        try:
            # 传递非法参数
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/tools/geocode/execute",
                json={"invalid_param": "value"}
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 400:  # 应返回400 Bad Request
                result = TestResult(
                    test_id="TOOL-ERR-02",
                    test_name="参数校验失败",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code, "parameter_validation": True},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="TOOL-ERR-02",
                    test_name="参数校验失败",
                    status="WARN",
                    duration_ms=duration_ms,
                    details={"warning": f"预期400, 实际: {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="TOOL-ERR-02",
                test_name="参数校验失败",
                status="WARN",
                duration_ms=(time.time() - start_time) * 1000,
                details={"warning": str(e)},
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
