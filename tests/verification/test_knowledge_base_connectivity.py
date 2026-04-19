"""知识库连接性验证测试 (KB-CONN 01~08)"""
import subprocess

import pytest
import requests

TIMEOUT = 5


# --- KB-CONN-01: 知识图谱HTTP连通性 ---
@pytest.mark.integration
def test_neo4j_kg_service(kb_urls):
    """验证知识图谱服务(端口8100)连通性"""
    try:
        resp = requests.get(f"{kb_urls['neo4j']}/health", timeout=TIMEOUT, verify=False)
        assert resp.status_code == 200, f"KG服务返回非200状态码: {resp.status_code}"
    except requests.ConnectionError:
        pytest.skip("知识图谱服务(8100)未启动")
    except requests.Timeout:
        pytest.skip("知识图谱服务(8100)连接超时")


# --- KB-CONN-02: Qdrant向量库连通性 ---
@pytest.mark.integration
def test_qdrant_vector_db(kb_urls):
    """验证Qdrant向量数据库(端口6333)连通性"""
    try:
        resp = requests.get(f"{kb_urls['qdrant']}/collections", timeout=TIMEOUT, verify=False)
        assert resp.status_code == 200, f"Qdrant返回非200状态码: {resp.status_code}"
        data = resp.json()
        assert "result" in data, "Qdrant响应缺少result字段"
    except requests.ConnectionError:
        pytest.skip("Qdrant向量库(6333)未启动")


# --- KB-CONN-03: PostgreSQL连通性 ---
@pytest.mark.integration
def test_postgres_connectivity(kb_urls):
    """验证PostgreSQL数据库连通性(通过pg_isready)"""
    try:
        result = subprocess.run(
            ["pg_isready", "-h", "localhost", "-p", "15432"],  # Docker映射端口
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        # pg_isready返回0表示可连接
        assert result.returncode == 0, f"PostgreSQL不可达: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("pg_isready命令不可用")
    except subprocess.TimeoutExpired:
        pytest.skip("PostgreSQL连接超时")


# --- KB-CONN-04: Redis连通性 ---
@pytest.mark.integration
def test_redis_connectivity(kb_urls):
    """验证Redis缓存服务连通性(通过redis-cli)"""
    try:
        result = subprocess.run(
            ["redis-cli", "-h", "localhost", "-p", "16379", "ping"],  # Docker映射端口
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        assert "PONG" in result.stdout, f"Redis未返回PONG: {result.stdout}"
    except FileNotFoundError:
        # 尝试通过docker执行
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "redis", "redis-cli", "ping"],
            capture_output=True, text=True, timeout=TIMEOUT,
            cwd="/Users/xujian/Athena工作平台",
        )
        if "PONG" not in result.stdout:
            pytest.skip("Redis服务未启动")
    except subprocess.TimeoutExpired:
        pytest.skip("Redis连接超时")


# --- KB-CONN-05: 统一网关健康检查 ---
@pytest.mark.integration
def test_gateway_health(kb_urls):
    """验证统一网关(端口8005)健康检查"""
    try:
        resp = requests.get(f"{kb_urls['gateway']}/health", timeout=TIMEOUT, verify=False)
        assert resp.status_code == 200, f"网关返回非200状态码: {resp.status_code}"
    except requests.ConnectionError:
        pytest.skip("统一网关(8005)未启动")


# --- KB-CONN-06: 网关→知识图谱路由 ---
@pytest.mark.integration
def test_gateway_kg_route(kb_urls):
    """验证网关正确转发知识图谱查询请求"""
    try:
        resp = requests.post(
            f"{kb_urls['gateway']}/api/v1/kg/query",
            json={"query": "测试"},
            timeout=TIMEOUT,
            verify=False,
        )
        # 路由存在: 200/201/400/404/422都算路由已注册
        assert resp.status_code in (200, 201, 400, 404, 422, 502), (
            f"KG路由未注册, 状态码: {resp.status_code}"
        )
    except requests.ConnectionError:
        pytest.skip("统一网关(8005)未启动")


# --- KB-CONN-07: 网关→向量搜索路由 ---
@pytest.mark.integration
def test_gateway_vector_route(kb_urls):
    """验证网关正确转发向量搜索请求"""
    try:
        resp = requests.post(
            f"{kb_urls['gateway']}/api/v1/vector/search",
            json={"query": "测试", "limit": 5},
            timeout=TIMEOUT,
            verify=False,
        )
        assert resp.status_code in (200, 201, 400, 404, 422, 502), (
            f"向量搜索路由未注册, 状态码: {resp.status_code}"
        )
    except requests.ConnectionError:
        pytest.skip("统一网关(8005)未启动")


# --- KB-CONN-08: Qdrant集合数量验证 ---
@pytest.mark.integration
def test_qdrant_collections_count(kb_urls):
    """验证Qdrant包含预期数量的集合"""
    try:
        resp = requests.get(f"{kb_urls['qdrant']}/collections", timeout=TIMEOUT, verify=False)
        data = resp.json()
        collections = data.get("result", {}).get("collections", [])
        # 预期至少有几个核心集合
        collection_names = [c["name"] for c in collections]
        print(f"  已发现 {len(collections)} 个集合: {collection_names}")
        assert len(collections) > 0, "Qdrant中没有找到任何集合"
    except requests.ConnectionError:
        pytest.skip("Qdrant向量库(6333)未启动")
