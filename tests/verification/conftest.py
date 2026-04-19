"""Athena平台验证测试 - 共享fixture配置"""
import pytest

# 知识库服务URL配置 (使用Docker映射端口)
KB_SERVICE_URLS = {
    "neo4j": "http://localhost:17474",  # Docker映射端口
    "qdrant": "http://localhost:16333",  # Docker映射端口
    "postgres": "localhost:15432",       # Docker映射端口
    "redis": "localhost:16379",          # Docker映射端口
    "gateway": "https://localhost:8005",  # Gateway使用HTTPS
}

# 工具库服务URL配置
TOOL_SERVICE_URLS = {
    "local_search": "http://localhost:3003",
    "mineru": "http://localhost:7860",
    "gateway": "https://localhost:8005",  # Gateway使用HTTPS
}

# 网关配置
GATEWAY_BASE_URL = "http://localhost:8005"


@pytest.fixture(scope="session")
def kb_urls():
    """知识库服务URL字典"""
    return KB_SERVICE_URLS


@pytest.fixture(scope="session")
def tool_urls():
    """工具库服务URL字典"""
    return TOOL_SERVICE_URLS


@pytest.fixture(scope="session")
def gateway_url():
    """统一网关基础URL"""
    return GATEWAY_BASE_URL


@pytest.fixture(scope="session")
def golden_queries():
    """知识库检索基准查询集合"""
    return [
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
            "expected_top_entities": ["复审请求", "专利复审委员会"],
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
