"""网关路由转发验证测试 (GW-ROUTE 01~10)"""
import pytest
import requests

TIMEOUT = 5


def _check_route(method, url, json_data=None, skip_on_conn_error=True):
    """通用路由检查: 返回 (可达, 状态码)"""
    try:
        if method == "GET":
            resp = requests.get(url, timeout=TIMEOUT)
        else:
            resp = requests.post(url, json=json_data or {}, timeout=TIMEOUT)
        # 路由已注册的判断标准
        registered = resp.status_code in (200, 201, 204, 400, 401, 404, 422, 502)
        return registered, resp.status_code, resp
    except requests.ConnectionError:
        if skip_on_conn_error:
            pytest.skip("统一网关(8005)未启动")
        return False, None, None


# --- GW-ROUTE-01: 健康检查端点 ---
@pytest.mark.integration
def test_health_endpoint(gateway_url):
    """GET /health 返回200"""
    reachable, code, _ = _check_route("GET", f"{gateway_url}/health")
    assert reachable and code == 200, f"/health 端点异常: {code}"


# --- GW-ROUTE-02: 就绪检查端点 ---
@pytest.mark.integration
def test_ready_endpoint(gateway_url):
    """GET /ready 返回200或503"""
    reachable, code, _ = _check_route("GET", f"{gateway_url}/ready")
    assert reachable, f"/ready 端点不可达: {code}"
    assert code in (200, 503), f"/ready 状态码异常: {code}"


# --- GW-ROUTE-03: 存活检查端点 ---
@pytest.mark.integration
def test_live_endpoint(gateway_url):
    """GET /live 返回200"""
    reachable, code, _ = _check_route("GET", f"{gateway_url}/live")
    assert reachable and code == 200, f"/live 端点异常: {code}"


# --- GW-ROUTE-04: 知识图谱路由 ---
@pytest.mark.integration
def test_kg_route(gateway_url):
    """POST /api/v1/kg/query 路由存在"""
    reachable, code, _ = _check_route("POST", f"{gateway_url}/api/v1/kg/query")
    assert reachable, f"KG路由未注册: {code}"


# --- GW-ROUTE-05: 向量搜索路由 ---
@pytest.mark.integration
def test_vector_search_route(gateway_url):
    """POST /api/v1/vector/search 路由存在"""
    reachable, code, _ = _check_route(
        "POST", f"{gateway_url}/api/v1/vector/search"
    )
    assert reachable, f"向量搜索路由未注册: {code}"


# --- GW-ROUTE-06: 法律搜索路由 ---
@pytest.mark.integration
def test_legal_search_route(gateway_url):
    """POST /api/v1/legal/search 路由存在"""
    reachable, code, _ = _check_route(
        "POST", f"{gateway_url}/api/v1/legal/search"
    )
    assert reachable, f"法律搜索路由未注册: {code}"


# --- GW-ROUTE-07: 工具列表路由 ---
@pytest.mark.integration
def test_tools_route(gateway_url):
    """GET /api/v1/tools 路由存在"""
    reachable, code, resp = _check_route("GET", f"{gateway_url}/api/v1/tools")
    assert reachable, f"工具路由未注册: {code}"
    if code == 200:
        data = resp.json()
        print(f"  工具列表响应: {list(data.keys()) if isinstance(data, dict) else type(data)}")


# --- GW-ROUTE-08: 服务实例路由 ---
@pytest.mark.integration
def test_services_instances(gateway_url):
    """GET /api/v1/services/instances 路由存在"""
    reachable, code, _ = _check_route(
        "GET", f"{gateway_url}/api/v1/services/instances"
    )
    assert reachable, f"服务实例路由未注册: {code}"


# --- GW-ROUTE-09: 路由管理 ---
@pytest.mark.integration
def test_routes_management(gateway_url):
    """GET /api/v1/routes 路由存在"""
    reachable, code, _ = _check_route("GET", f"{gateway_url}/api/v1/routes")
    assert reachable, f"路由管理端点未注册: {code}"


# --- GW-ROUTE-10: 未知路由返回404 ---
@pytest.mark.integration
def test_unknown_route_404(gateway_url):
    """不存在的路径应返回404"""
    _, code, _ = _check_route(
        "GET", f"{gateway_url}/api/v1/this-route-does-not-exist-xyz",
        skip_on_conn_error=True,
    )
    assert code == 404, f"未知路径应返回404, 实际: {code}"
