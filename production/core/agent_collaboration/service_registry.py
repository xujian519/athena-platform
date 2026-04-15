"""
服务能力注册配置
定义平台所有80个微服务的能力描述
"""

# 避免循环导入
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


# 核心专利服务
PATENT_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "yunpat-agent",
        "service_name": "YunPat专利代理",
        "category": "patent",
        "description": "专业专利检索与分析服务,支持中国专利数据搜索,提供专利价值评估和技术分析",
        "keywords": ["专利", "搜索", "检索", "查询", "中国专利", "CN专利", "patent"],
        "semantic_tags": ["patent_search", "patent_analysis", "patent_evaluation"],
        "capabilities": [
            "patent_search",
            "patent_analysis",
            "patent_download",
            "value_assessment",
            "tech_analysis",
        ],
        "input_types": ["text_query", "patent_number", "tech_field"],
        "output_types": ["patent_list", "patent_detail", "analysis_report"],
        "metadata": {"port": 8020, "endpoint": "http://localhost:8020"},
    },
    {
        "service_id": "patent-analysis",
        "service_name": "专利分析服务",
        "category": "analysis",
        "description": "深度专利分析,包括技术趋势分析、竞争对手分析、专利布局分析",
        "keywords": [
            "专利",
            "分析",
            "评估",
            "专利分析",
            "技术趋势",
            "竞争对手",
            "专利布局",
            "技术挖掘",
            "价值分析",
            "技术含量",
        ],
        "semantic_tags": ["patent_analysis", "technology_trends", "competitive_intelligence"],
        "capabilities": [
            "tech_trend_analysis",
            "competitor_analysis",
            "patent_layout_analysis",
            "citation_analysis",
        ],
        "input_types": ["patent_list", "company_name", "tech_field"],
        "output_types": ["analysis_report", "trend_chart", "competitive_matrix"],
        "metadata": {"port": 8050, "endpoint": "http://localhost:8050"},
    },
    {
        "service_id": "patent-search",
        "service_name": "专利搜索服务",
        "category": "search",
        "description": "高效专利搜索引擎,支持全文检索、语义检索、多条件组合检索",
        "keywords": ["专利", "搜索", "专利搜索", "全文检索", "语义检索", "组合检索", "检索"],
        "semantic_tags": ["patent_search", "full_text_search", "semantic_search"],
        "capabilities": ["full_text_search", "semantic_search", "boolean_search", "facet_search"],
        "input_types": ["search_query", "search_filters"],
        "output_types": ["search_results", "patent_list", "search_summary"],
        "metadata": {"port": 8060, "endpoint": "http://localhost:8060"},
    },
]

# 浏览器自动化服务
BROWSER_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "browser-automation",
        "service_name": "浏览器自动化服务",
        "category": "browser",
        "description": "完整的浏览器自动化控制,支持网页操作、截图、数据提取、表单填写",
        "keywords": ["浏览器", "自动化", "网页操作", "截图", "数据提取", "表单填写"],
        "semantic_tags": ["browser_automation", "web_scraping", "ui_automation"],
        "capabilities": [
            "page_navigation",
            "element_interaction",
            "screenshot",
            "data_extraction",
            "form_filling",
        ],
        "input_types": ["url", "selector", "action_command"],
        "output_types": ["screenshot_image", "extracted_data", "action_result"],
        "metadata": {"port": 8030, "endpoint": "http://localhost:8030"},
    },
    {
        "service_id": "chrome-mcp",
        "service_name": "Chrome MCP服务",
        "category": "browser",
        "description": "Chrome浏览器MCP集成,提供标准化的浏览器控制接口",
        "keywords": ["Chrome", "浏览器控制", "MCP", "标签页管理", "书签管理"],
        "semantic_tags": ["chrome_control", "browser_management", "mcp_integration"],
        "capabilities": [
            "tab_management",
            "bookmark_management",
            "history_management",
            "chrome_devtools",
        ],
        "input_types": ["chrome_command", "tab_id"],
        "output_types": ["browser_state", "page_content"],
        "metadata": {"endpoint": "mcp://chrome-mcp-server"},
    },
]

# 自主控制服务
CONTROL_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "autonomous-control",
        "service_name": "自主控制系统",
        "category": "control",
        "description": "自主任务执行系统,支持复杂工作流的自动化执行和智能决策",
        "keywords": ["自主控制", "任务自动化", "工作流", "智能决策", "自动化执行"],
        "semantic_tags": ["autonomous_execution", "workflow_automation", "intelligent_decision"],
        "capabilities": [
            "workflow_execution",
            "task_scheduling",
            "decision_making",
            "error_recovery",
        ],
        "input_types": ["workflow_definition", "task_parameters"],
        "output_types": ["execution_result", "task_log", "decision_trace"],
        "metadata": {"port": 8040, "endpoint": "http://localhost:8040"},
    }
]

# 知识图谱服务
KNOWLEDGE_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "knowledge-graph-service",
        "service_name": "知识图谱服务",
        "category": "knowledge",
        "description": "专利知识图谱构建与查询,支持实体关系推理、图谱可视化、路径查询",
        "keywords": [
            "知识图谱",
            "图谱",
            "关系",
            "关系推理",
            "图谱查询",
            "实体识别",
            "关系抽取",
            "关联",
        ],
        "semantic_tags": [
            "knowledge_graph",
            "entity_relation",
            "graph_query",
            "graph_visualization",
        ],
        "capabilities": [
            "graph_construction",
            "entity_extraction",
            "relation_extraction",
            "graph_query",
            "path_finding",
            "graph_visualization",
        ],
        "input_types": ["text", "entity_list", "query_pattern"],
        "output_types": ["graph_data", "entity_relations", "query_result"],
        "metadata": {"endpoint": "http://localhost:8100"},
    },
    {
        "service_id": "vectorkg-unified",
        "service_name": "向量知识图谱统一服务",
        "category": "knowledge",
        "description": "向量存储与知识图谱融合服务,支持语义向量检索和图谱推理",
        "keywords": ["向量知识图谱", "向量检索", "图谱推理", "语义搜索", "混合检索"],
        "semantic_tags": ["vector_kg", "semantic_retrieval", "graph_reasoning", "hybrid_search"],
        "capabilities": ["vector_storage", "vector_search", "graph_reasoning", "hybrid_search"],
        "input_types": ["vector", "query_vector", "graph_query"],
        "output_types": ["search_results", "reasoning_result"],
        "metadata": {"endpoint": "http://localhost:8200"},
    },
]

# 学术搜索服务
ACADEMIC_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "academic-search-mcp",
        "service_name": "学术搜索MCP服务",
        "category": "search",
        "description": "学术论文搜索与检索,集成Semantic Scholar API,支持论文引用分析",
        "keywords": [
            "论文",
            "学术论文",
            "文献",
            "文献检索",
            "Semantic Scholar",
            "论文引用",
            "学术搜索",
            "参考文献",
        ],
        "semantic_tags": [
            "academic_search",
            "paper_retrieval",
            "citation_analysis",
            "scholarly_articles",
        ],
        "capabilities": [
            "paper_search",
            "citation_analysis",
            "author_search",
            "paper_recommendation",
        ],
        "input_types": ["search_query", "author_name", "paper_id"],
        "output_types": ["paper_list", "paper_detail", "citation_network"],
        "metadata": {"endpoint": "mcp://academic-search-mcp-server"},
    }
]

# 地图服务
MAP_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "gaode-mcp",
        "service_name": "高德地图MCP服务",
        "category": "utility",
        "description": "高德地图集成服务,提供地理编码、路径规划、周边搜索等功能",
        "keywords": [
            "地图",
            "高德",
            "路径规划",
            "路线",
            "路线规划",
            "地理编码",
            "周边搜索",
            "导航",
            "位置",
            "地址",
        ],
        "semantic_tags": ["map_service", "geocoding", "route_planning", "location_search"],
        "capabilities": [
            "geocoding",
            "reverse_geocoding",
            "route_planning",
            "nearby_search",
            "map_display",
        ],
        "input_types": ["address", "coordinates", "route_points"],
        "output_types": ["coordinates", "route_info", "nearby_places"],
        "metadata": {"endpoint": "mcp://gaode-mcp-server"},
    }
]

# AI服务
AI_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "jina-ai-mcp",
        "service_name": "Jina AI MCP服务",
        "category": "analysis",
        "description": "Jina AI集成服务,提供向量嵌入、文本重排序、网络搜索等AI能力",
        "keywords": ["Jina AI", "向量嵌入", "重排序", "网络搜索", "AI"],
        "semantic_tags": ["ai_service", "vector_embedding", "reranking", "web_search"],
        "capabilities": [
            "text_embedding",
            "document_reranking",
            "web_search",
            "content_extraction",
        ],
        "input_types": ["text", "document_list", "search_query"],
        "output_types": ["embedding_vector", "ranked_list", "search_results"],
        "metadata": {"endpoint": "mcp://jina-ai-mcp-server"},
    },
    {
        "service_id": "agent-core",
        "service_name": "Agent核心服务",
        "category": "agent",
        "description": "AI Agent核心引擎,提供意图识别、任务规划、多Agent协调能力",
        "keywords": ["AI Agent", "意图识别", "任务规划", "Agent协调", "智能体"],
        "semantic_tags": ["ai_agent", "intent_recognition", "task_planning", "agent_coordination"],
        "capabilities": [
            "intent_recognition",
            "task_planning",
            "agent_coordination",
            "context_management",
        ],
        "input_types": ["user_input", "task_description"],
        "output_types": ["intent_result", "execution_plan", "agent_response"],
        "metadata": {"endpoint": "http://localhost:8010"},
    },
]

# 存储服务
STORAGE_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "vector-storage",
        "service_name": "向量存储服务",
        "category": "storage",
        "description": "高性能向量数据库,支持大规模向量存储和相似度检索",
        "keywords": ["向量存储", "向量数据库", "相似度检索", "向量索引"],
        "semantic_tags": ["vector_storage", "similarity_search", "vector_index"],
        "capabilities": ["vector_store", "vector_search", "batch_insert", "index_management"],
        "input_types": ["vector", "vector_list", "search_query"],
        "output_types": ["search_results", "insert_result"],
        "metadata": {"endpoint": "qdrant://localhost:6333"},
    },
    {
        "service_id": "cache-service",
        "service_name": "缓存服务",
        "category": "storage",
        "description": "分布式缓存系统,提供高性能键值存储和缓存管理",
        "keywords": ["缓存", "Redis", "键值存储", "分布式缓存"],
        "semantic_tags": ["cache", "key_value_store", "distributed_cache"],
        "capabilities": ["cache_get", "cache_set", "cache_delete", "cache_invalidate"],
        "input_types": ["key", "value", "ttl"],
        "output_types": ["cached_value", "operation_result"],
        "metadata": {"endpoint": "redis://localhost:6379"},
    },
]

# 监控服务
MONITORING_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "prometheus",
        "service_name": "Prometheus监控",
        "category": "monitoring",
        "description": "系统监控和指标收集,提供实时监控数据",
        "keywords": ["监控", "指标", "Prometheus", "监控数据", "性能监控"],
        "semantic_tags": ["monitoring", "metrics", "performance_monitoring"],
        "capabilities": ["metrics_collection", "alerting", "query_metrics", "dashboard_generation"],
        "input_types": ["metric_name", "query_range"],
        "output_types": ["metric_data", "alert_status"],
        "metadata": {"port": 9090, "endpoint": "http://localhost:9090"},
    },
    {
        "service_id": "grafana",
        "service_name": "Grafana可视化",
        "category": "monitoring",
        "description": "数据可视化和监控面板,支持多种数据源",
        "keywords": ["可视化", "Grafana", "监控面板", "数据可视化", "仪表盘"],
        "semantic_tags": ["visualization", "dashboard", "monitoring_panel"],
        "capabilities": [
            "dashboard_display",
            "chart_generation",
            "data_visualization",
            "alert_notification",
        ],
        "input_types": ["dashboard_id", "query"],
        "output_types": ["dashboard_view", "chart_data"],
        "metadata": {"port": 3000, "endpoint": "http://localhost:3000"},
    },
]

# API网关服务
GATEWAY_SERVICES: list[dict[str, Any]] = [
    {
        "service_id": "api-gateway",
        "service_name": "API网关",
        "category": "utility",
        "description": "统一API网关,提供路由、认证、限流、负载均衡",
        "keywords": ["API网关", "路由", "认证", "限流", "负载均衡"],
        "semantic_tags": ["api_gateway", "routing", "authentication", "rate_limiting"],
        "capabilities": ["request_routing", "authentication", "rate_limiting", "load_balancing"],
        "input_types": ["api_request"],
        "output_types": ["api_response"],
        "metadata": {"port": 8080, "endpoint": "http://localhost:8080"},
    }
]

# 合并所有服务
ALL_SERVICES = (
    PATENT_SERVICES
    + BROWSER_SERVICES
    + CONTROL_SERVICES
    + KNOWLEDGE_SERVICES
    + ACADEMIC_SERVICES
    + MAP_SERVICES
    + AI_SERVICES
    + STORAGE_SERVICES
    + MONITORING_SERVICES
    + GATEWAY_SERVICES
)


def register_all_services(kg: Any) -> None:
    """注册所有服务到知识图谱"""
    # 动态导入避免循环依赖
    from core.agent_collaboration.service_kg import ServiceCapability, ServiceCategory

    for service_config in ALL_SERVICES:
        # 将category字符串转换为枚举
        if isinstance(service_config["category"], str):
            service_config["category"] = ServiceCategory(service_config["category"])

        service = ServiceCapability(**service_config)
        kg.register_service(service)

    print(f"已注册 {len(ALL_SERVICES)} 个服务到知识图谱")


def get_service_by_id(service_id: str) -> dict[str, Any] | None:
    """根据ID获取服务配置"""
    for service in ALL_SERVICES:
        if service["service_id"] == service_id:
            return service
    return None


def get_services_by_category(category: str) -> list[dict[str, Any]]:
    """根据分类获取服务列表"""
    return [s for s in ALL_SERVICES if s["category"] == category]
