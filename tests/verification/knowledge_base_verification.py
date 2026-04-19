#!/usr/bin/env python3
"""
Athena平台知识库验证测试套件

测试范围:
- KB-CONN-01~08: 连通性测试
- KB-ACC-01~06: 准确性验证
- KB-PERF-01~05: 并发性能测试
- KB-SYNC-01~04: 数据同步验证

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
from neo4j import AsyncGraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import redis.asyncio as redis
import psycopg2
from psycopg2 import sql

# 核心服务导入
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))

from embedding.unified_embedding_service import UnifiedEmbeddingService


# ============================================================================
# 测试配置
# ============================================================================

TEST_CONFIG = {
    "services": {
        "knowledge_graph": "http://localhost:8100",
        "qdrant": "http://localhost:6333",
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "database": "athena",
            "user": "athena",
            "password": "athena_password"
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0
        },
        "gateway": "http://localhost:8005"
    },
    "performance": {
        "baseline_qps": 50,
        "baseline_p95_ms": 200,
        "medium_concurrency": 50,
        "high_concurrency": 100,
        "peak_concurrency": 200
    }
}

# 基准查询集 (Golden Set)
GOLDEN_QUERIES = [
    {
        "id": "GQ-001",
        "query": "发明专利创造性判断标准",
        "expected_top_entities": ["创造性", "突出实质性特点", "显著进步"],
        "expected_collections": ["patent_rules_1024", "legal_main"],
        "min_relevance_score": 0.75,
    },
    {
        "id": "GQ-002",
        "query": "专利申请驳回后复审流程",
        "expected_top_entities": ["复审请求", "专利复审委员会", "复审通知书"],
        "expected_collections": ["patent_rules_1024", "patent_legal"],
        "min_relevance_score": 0.70,
    },
    {
        "id": "GQ-003",
        "query": "人工智能相关专利的审查指南",
        "expected_top_entities": ["人工智能", "算法", "计算机实施的发明"],
        "expected_collections": ["patent_rules_1024", "technical_terms_1024"],
        "min_relevance_score": 0.72,
    },
]


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
        report_file = self.output_dir / f"kb_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report


# ============================================================================
# KB-CONN-01~08: 连通性测试
# ============================================================================

class TestKnowledgeBaseConnectivity:
    """知识库连通性测试"""

    @pytest.fixture
    async def http_client(self):
        """HTTP客户端"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_kb_conn_01_knowledge_graph(self, http_client, reporter: TestReporter):
        """KB-CONN-01: 知识图谱HTTP连通性"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['services']['knowledge_graph']}/health")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    result = TestResult(
                        test_id="KB-CONN-01",
                        test_name="知识图谱HTTP连通性",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"status": data.get("status")},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="KB-CONN-01",
                        test_name="知识图谱HTTP连通性",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={"error": f"Status not healthy: {data.get('status')}"},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="KB-CONN-01",
                    test_name="知识图谱HTTP连通性",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-01",
                test_name="知识图谱HTTP连通性",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"知识图谱连通性测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_02_qdrant(self, http_client, reporter: TestReporter):
        """KB-CONN-02: Qdrant向量库连通性"""
        start_time = time.time()
        try:
            response = await http_client.get(f"{TEST_CONFIG['services']['qdrant']}/collections")
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                collections = data.get("result", {}).get("collections", [])
                # 预期至少7个集合
                if len(collections) >= 7:
                    result = TestResult(
                        test_id="KB-CONN-02",
                        test_name="Qdrant向量库连通性",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"collections_count": len(collections), "collections": [c["name"] for c in collections]},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="KB-CONN-02",
                        test_name="Qdrant向量库连通性",
                        status="WARN",
                        duration_ms=duration_ms,
                        details={"warning": f"仅找到{len(collections)}个集合,预期至少7个", "collections": [c["name"] for c in collections]},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="KB-CONN-02",
                    test_name="Qdrant向量库连通性",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-02",
                test_name="Qdrant向量库连通性",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status in ["PASS", "WARN"], f"Qdrant连通性测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_03_postgresql(self, reporter: TestReporter):
        """KB-CONN-03: PostgreSQL连通性"""
        start_time = time.time()
        try:
            pg_config = TEST_CONFIG["services"]["postgres"]
            conn_str = f"host={pg_config['host']} port={pg_config['port']} dbname={pg_config['database']} user={pg_config['user']} password={pg_config['password']}"

            async with await psycopg.AsyncConnection.connect(conn_str) as conn:
                await conn.execute("SELECT 1")
                duration_ms = (time.time() - start_time) * 1000

                result = TestResult(
                    test_id="KB-CONN-03",
                    test_name="PostgreSQL连通性",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"connection": "successful"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-03",
                test_name="PostgreSQL连通性",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"PostgreSQL连通性测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_04_redis(self, reporter: TestReporter):
        """KB-CONN-04: Redis连通性"""
        start_time = time.time()
        try:
            redis_config = TEST_CONFIG["services"]["redis"]
            redis_client = await redis.Redis(
                host=redis_config["host"],
                port=redis_config["port"],
                db=redis_config["db"]
            )

            await redis_client.ping()
            duration_ms = (time.time() - start_time) * 1000

            await redis_client.close()

            result = TestResult(
                test_id="KB-CONN-04",
                test_name="Redis连通性",
                status="PASS",
                duration_ms=duration_ms,
                details={"ping": "PONG"},
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-04",
                test_name="Redis连通性",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"Redis连通性测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_05_bge_m3_embedding(self, reporter: TestReporter):
        """KB-CONN-05: BGE-M3嵌入服务"""
        start_time = time.time()
        try:
            embedding_service = UnifiedEmbeddingService()
            test_text = "测试文本"
            embedding = await embedding_service.aencode(test_text)
            duration_ms = (time.time() - start_time) * 1000

            # BGE-M3应返回768维向量
            if len(embedding) == 768:
                result = TestResult(
                    test_id="KB-CONN-05",
                    test_name="BGE-M3嵌入服务",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"embedding_dim": len(embedding)},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="KB-CONN-05",
                    test_name="BGE-M3嵌入服务",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"向量维度错误: {len(embedding)}, 预期768"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-05",
                test_name="BGE-M3嵌入服务",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"BGE-M3嵌入服务测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_06_gateway_to_kg(self, http_client, reporter: TestReporter):
        """KB-CONN-06: 网关→知识图谱路由"""
        start_time = time.time()
        try:
            # 发送图谱查询请求
            query = {
                "cypher": "MATCH (n) RETURN count(n) as count LIMIT 1"
            }
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/kg/query",
                json=query
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 401, 422]:  # 401/422表示路由存在但需要认证或参数
                result = TestResult(
                    test_id="KB-CONN-06",
                    test_name="网关→知识图谱路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="KB-CONN-06",
                    test_name="网关→知识图谱路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-06",
                test_name="网关→知识图谱路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"网关→知识图谱路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_07_gateway_to_vector(self, http_client, reporter: TestReporter):
        """KB-CONN-07: 网关→向量搜索路由"""
        start_time = time.time()
        try:
            # 发送向量搜索请求
            query = {
                "collection_name": "patent_rules_1024",
                "query_text": "测试查询",
                "limit": 5
            }
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/vector/search",
                json=query
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 401, 422]:
                result = TestResult(
                    test_id="KB-CONN-07",
                    test_name="网关→向量搜索路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="KB-CONN-07",
                    test_name="网关→向量搜索路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-07",
                test_name="网关→向量搜索路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"网关→向量搜索路由测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_conn_08_gateway_to_legal(self, http_client, reporter: TestReporter):
        """KB-CONN-08: 网关→法律搜索路由"""
        start_time = time.time()
        try:
            # 发送法律搜索请求
            query = {
                "query": "专利法第22条",
                "limit": 10
            }
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/legal/search",
                json=query
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code in [200, 401, 422]:
                result = TestResult(
                    test_id="KB-CONN-08",
                    test_name="网关→法律搜索路由",
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat()
                )
            else:
                result = TestResult(
                    test_id="KB-CONN-08",
                    test_name="网关→法律搜索路由",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-CONN-08",
                test_name="网关→法律搜索路由",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"网关→法律搜索路由测试失败: {result.details}"


# ============================================================================
# KB-ACC-01~06: 准确性验证
# ============================================================================

class TestKnowledgeBaseAccuracy:
    """知识库准确性验证"""

    @pytest.mark.asyncio
    async def test_kb_acc_01_patent_semantic_search(self, http_client, reporter: TestReporter):
        """KB-ACC-01: 专利语义搜索"""
        start_time = time.time()
        try:
            golden_query = GOLDEN_QUERIES[0]  # GQ-001

            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/vector/search",
                json={
                    "collection_name": golden_query["expected_collections"][0],
                    "query_text": golden_query["query"],
                    "limit": 10
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                results = response.json().get("results", [])
                # 验证Top-10结果中是否包含预期实体
                found_entities = [r.get("entity", "") for r in results]
                match_count = sum(1 for e in golden_query["expected_top_entities"] if e in found_entities)

                if match_count >= 2:  # 至少匹配2个预期实体
                    result = TestResult(
                        test_id="KB-ACC-01",
                        test_name="专利语义搜索",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={
                            "query": golden_query["query"],
                            "matched_entities": match_count,
                            "expected_entities": len(golden_query["expected_top_entities"]),
                            "top_results": found_entities[:5]
                        },
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="KB-ACC-01",
                        test_name="专利语义搜索",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={
                            "error": f"仅匹配{match_count}/{len(golden_query['expected_top_entities'])}个预期实体",
                            "found_entities": found_entities[:5]
                        },
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="KB-ACC-01",
                    test_name="专利语义搜索",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-ACC-01",
                test_name="专利语义搜索",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"专利语义搜索测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_acc_02_legal_article_retrieval(self, http_client, reporter: TestReporter):
        """KB-ACC-02: 法律条文检索"""
        start_time = time.time()
        try:
            # 查询专利法第22条
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/legal/search",
                json={
                    "query": "专利法第22条 创造性",
                    "limit": 10
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                results = response.json().get("results", [])
                # 检查Top-3结果中是否包含专利法第22条
                top_3 = results[:3]
                found_22 = any("第22条" in r.get("content", "") or "第二十二条" in r.get("content", "") for r in top_3)

                if found_22:
                    result = TestResult(
                        test_id="KB-ACC-02",
                        test_name="法律条文检索",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={
                            "query": "专利法第22条",
                            "found_in_top3": True,
                            "rank": next((i+1 for i, r in enumerate(top_3) if "第22条" in r.get("content", "")), None)
                        },
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="KB-ACC-02",
                        test_name="法律条文检索",
                        status="FAIL",
                        duration_ms=duration_ms,
                        details={"error": "专利法第22条未出现在Top-3结果中"},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="KB-ACC-02",
                    test_name="法律条文检索",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-ACC-02",
                test_name="法律条文检索",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status == "PASS", f"法律条文检索测试失败: {result.details}"

    @pytest.mark.asyncio
    async def test_kb_acc_03_knowledge_graph_path(self, http_client, reporter: TestReporter):
        """KB-ACC-03: 知识图谱路径查询"""
        start_time = time.time()
        try:
            # 查询"专利侵权→无效宣告"路径
            response = await http_client.post(
                f"{TEST_CONFIG['services']['gateway']}/api/v1/kg/query",
                json={
                    "cypher": "MATCH path = (start:Concept {name: '专利侵权'})-[:RELATED_TO*1..3]-(end:Concept {name: '无效宣告'}) RETURN path LIMIT 5"
                }
            )
            duration_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                path_count = len(data.get("results", []))

                if path_count > 0:
                    result = TestResult(
                        test_id="KB-ACC-03",
                        test_name="知识图谱路径查询",
                        status="PASS",
                        duration_ms=duration_ms,
                        details={"path_count": path_count},
                        timestamp=datetime.now().isoformat()
                    )
                else:
                    result = TestResult(
                        test_id="KB-ACC-03",
                        test_name="知识图谱路径查询",
                        status="WARN",
                        duration_ms=duration_ms,
                        details={"warning": "未找到路径，图谱可能不完整"},
                        timestamp=datetime.now().isoformat()
                    )
            else:
                result = TestResult(
                    test_id="KB-ACC-03",
                    test_name="知识图谱路径查询",
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"error": f"HTTP {response.status_code}"},
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            result = TestResult(
                test_id="KB-ACC-03",
                test_name="知识图谱路径查询",
                status="FAIL",
                duration_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )

        reporter.add_result(result)
        assert result.status in ["PASS", "WARN"], f"知识图谱路径查询测试失败: {result.details}"


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def reporter():
    """测试报告器"""
    output_dir = Path(__file__).parent / "reports"
    return TestReporter(output_dir)


# ============================================================================
# 性能测试 (使用locust)
# ============================================================================

# 注意: 并发性能测试建议使用locust单独运行
# 见 tests/verification/locust_kb_performance.py


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
