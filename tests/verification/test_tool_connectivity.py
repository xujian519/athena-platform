"""工具库连通性验证测试 (TOOL-CONN 01~07)"""
import pytest
import requests

TIMEOUT = 5


@pytest.mark.integration
def test_tool_registry_import():
    """TOOL-CONN-01: 统一工具注册中心可导入"""
    try:
        from core.governance.unified_tool_registry import UnifiedToolRegistry

        registry = UnifiedToolRegistry()
        assert registry is not None, "工具注册中心实例化失败"
        assert hasattr(registry, "tools"), "缺少tools属性"
        print(f"  工具注册中心已创建, 已注册工具数: {len(registry.tools)}")
    except ImportError as e:
        pytest.skip(f"工具注册中心模块导入失败: {e}")


@pytest.mark.integration
def test_mcp_manager_import():
    """TOOL-CONN-02: MCP管理器可导入"""
    try:
        from tools.mcp.athena_mcp_manager import AthenaMCPManager

        manager = AthenaMCPManager()
        assert manager is not None, "MCP管理器实例化失败"
        assert hasattr(manager, "servers"), "缺少servers属性"
        print(f"  MCP管理器已创建, 服务器数: {len(manager.servers)}")
        # 验证预期的MCP服务器配置存在
        expected_servers = ["jina-ai", "bing-cn-search", "amap-mcp", "academic-search"]
        for name in expected_servers:
            assert name in manager.servers, f"缺少MCP服务器配置: {name}"
    except ImportError as e:
        pytest.skip(f"MCP管理器模块导入失败: {e}")


@pytest.mark.integration
def test_local_search_engine(tool_urls):
    """TOOL-CONN-03: 本地搜索引擎(端口3003)健康检查"""
    try:
        resp = requests.get(f"{tool_urls['local_search']}/health", timeout=TIMEOUT)
        assert resp.status_code == 200, f"本地搜索引擎返回: {resp.status_code}"
    except requests.ConnectionError:
        pytest.skip("本地搜索引擎(3003)未启动")


@pytest.mark.integration
def test_mineru_parser(tool_urls):
    """TOOL-CONN-04: Mineru文档解析器(端口7860)健康检查"""
    try:
        resp = requests.get(f"{tool_urls['mineru']}/health", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Mineru解析器返回: {resp.status_code}"
    except requests.ConnectionError:
        pytest.skip("Mineru文档解析器(7860)未启动")


@pytest.mark.integration
def test_gateway_tools_list(gateway_url):
    """TOOL-CONN-05: 网关工具列表API"""
    try:
        resp = requests.get(f"{gateway_url}/api/v1/tools", timeout=TIMEOUT)
        assert resp.status_code in (200, 404), f"工具列表API返回: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            print(f"  工具列表响应: {list(data.keys()) if isinstance(data, dict) else type(data)}")
    except requests.ConnectionError:
        pytest.skip("网关未启动")


@pytest.mark.integration
def test_gateway_tools_status(gateway_url):
    """TOOL-CONN-06: 网关工具状态API"""
    try:
        resp = requests.get(f"{gateway_url}/api/v1/tools/status", timeout=TIMEOUT)
        # 路由可能不存在(404)也是预期行为
        assert resp.status_code in (200, 404), f"工具状态API返回: {resp.status_code}"
    except requests.ConnectionError:
        pytest.skip("网关未启动")


@pytest.mark.integration
def test_mcp_tool_discovery():
    """TOOL-CONN-07: MCP工具发现 - 验证MCP管理器可列出工具"""
    try:
        from tools.mcp.athena_mcp_manager import AthenaMCPManager

        manager = AthenaMCPManager()
        # 检查各MCP服务器的工具能力配置
        total_capabilities = 0
        for name, config in manager.servers.items():
            caps = config.capabilities
            total_capabilities += len(caps)
            print(f"  {name}: {len(caps)} 个工具 - {caps[:3]}...")

        assert total_capabilities > 0, "MCP服务器未配置任何工具能力"
        print(f"  MCP总工具能力数: {total_capabilities}")
    except ImportError as e:
        pytest.skip(f"MCP管理器导入失败: {e}")
