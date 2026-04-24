"""
OpenTelemetry追踪器测试

测试AthenaTracer的核心功能。
"""

import pytest

# 标记为unit测试
pytestmark = pytest.mark.unit


class TestTracerInitialization:
    """测试追踪器初始化"""

    def test_tracer_import(self):
        """测试追踪模块可以正常导入"""
        from core.tracing import (
            AthenaTracer,
            TracingConfig,
            get_config,
            DEV_CONFIG,
            TEST_CONFIG,
            PROD_CONFIG
        )
        assert AthenaTracer is not None
        assert TracingConfig is not None
        assert get_config is not None
        assert DEV_CONFIG is not None
        assert TEST_CONFIG is not None
        assert PROD_CONFIG is not None

    def test_config_creation(self):
        """测试配置创建"""
        from core.tracing import TracingConfig

        config = TracingConfig(
            service_name="test-service",
            sample_rate=0.5
        )

        assert config.service_name == "test-service"
        assert config.sample_rate == 0.5
        assert config.environment == "dev"

    def test_config_validation(self):
        """测试配置验证"""
        from core.tracing import TracingConfig

        # 有效配置
        config = TracingConfig(sample_rate=0.5)
        assert config.sample_rate == 0.5

        # 无效配置应该抛出异常
        with pytest.raises(ValueError):
            TracingConfig(sample_rate=1.5)  # 超过1.0

        with pytest.raises(ValueError):
            TracingConfig(sample_rate=-0.1)  # 小于0

    def test_tracer_creation(self):
        """测试追踪器创建"""
        from core.tracing import AthenaTracer, TracingConfig

        config = TracingConfig(service_name="test-agent")
        tracer = AthenaTracer("test-agent", config=config)

        assert tracer is not None
        assert tracer.service_name == "test-agent"
        assert tracer.config == config


class TestAgentSpan:
    """测试Agent Span创建"""

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_agent_span_creation(self):
        """测试Agent Span创建"""
        from core.tracing import AthenaTracer

        tracer = AthenaTracer("test-agent")

        with tracer.start_agent_span("xiaona", "patent_analysis"):
            pass
        # Span应该自动结束并上报

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_agent_span_with_attributes(self):
        """测试带属性的Agent Span"""
        from core.tracing import AthenaTracer

        tracer = AthenaTracer("test-agent")

        with tracer.start_agent_span(
            agent_name="xiaona",
            task_type="analysis",
            request_id="req-123",
            session_id="sess-456"
        ):
            pass


class TestLLMSpan:
    """测试LLM Span创建"""

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_llm_span_creation(self):
        """测试LLM Span创建"""
        from core.tracing import AthenaTracer

        tracer = AthenaTracer("test-agent")

        with tracer.start_llm_span(
            provider="claude",
            model="claude-3-opus"
        ):
            pass


class TestToolSpan:
    """测试工具Span创建"""

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_tool_span_creation(self):
        """测试工具Span创建"""
        from core.tracing import AthenaTracer

        tracer = AthenaTracer("test-agent")

        with tracer.start_tool_span(
            tool_name="patent_search",
            category="patent"
        ):
            pass


class TestDatabaseSpan:
    """测试数据库Span创建"""

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_database_span_creation(self):
        """测试数据库Span创建"""
        from core.tracing import AthenaTracer

        tracer = AthenaTracer("test-agent")

        with tracer.start_database_span(
            db_system="postgresql",
            operation="SELECT",
            table="patents"
        ):
            pass


class TestHTTPSpan:
    """测试HTTP Span创建"""

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_http_span_creation(self):
        """测试HTTP Span创建"""
        from core.tracing import AthenaTracer

        tracer = AthenaTracer("test-agent")

        with tracer.start_http_span(
            method="GET",
            url="https://api.example.com/patents"
        ):
            pass


class TestTraceContext:
    """测试追踪上下文"""

    @pytest.mark.skipif(
        "not pytest.importorskip('opentelemetry')",
        reason="需要安装OpenTelemetry依赖"
    )
    def test_propagator_inject_extract(self):
        """测试上下文传播"""
        from core.tracing import TracePropagator

        propagator = TracePropagator()

        # 注入上下文
        carrier = {}
        propagator.inject(carrier)

        # 应该包含traceparent
        assert "traceparent" in carrier

        # 提取上下文
        context = propagator.extract(carrier)
        assert context is not None

    def test_trace_parent_parsing(self):
        """测试traceparent解析"""
        from core.tracing.propagator import TracePropagator

        # 有效的traceparent
        trace_parent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        result = TracePropagator.parse_trace_parent(trace_parent)

        assert result is not None
        assert result["version"] == "00"
        assert result["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert result["span_id"] == "00f067aa0ba902b7"
        assert result["trace_flags"] == "01"

        # 无效的traceparent
        invalid = "invalid"
        result = TracePropagator.parse_trace_parent(invalid)
        assert result is None


class TestRequestContext:
    """测试请求上下文"""

    def test_request_context_set_get(self):
        """测试请求上下文设置和获取"""
        from core.tracing import RequestContext

        RequestContext.set("key1", "value1")
        RequestContext.set("key2", "value2")

        assert RequestContext.get("key1") == "value1"
        assert RequestContext.get("key2") == "value2"
        assert RequestContext.get("key3") is None  # 不存在的键
        assert RequestContext.get("key3", "default") == "default"

    def test_request_context_update(self):
        """测试请求上下文更新"""
        from core.tracing import RequestContext

        RequestContext.update({"a": 1, "b": 2})
        assert RequestContext.get("a") == 1
        assert RequestContext.get("b") == 2

    def test_request_context_clear(self):
        """测试请求上下文清空"""
        from core.tracing import RequestContext

        RequestContext.set("temp", "value")
        assert RequestContext.get("temp") == "value"

        RequestContext.clear()
        assert RequestContext.get("temp") is None


class TestAgentSessionContext:
    """测试Agent会话上下文"""

    def test_session_lifecycle(self):
        """测试会话生命周期"""
        from core.tracing import AgentSessionContext

        # 开始会话
        AgentSessionContext.start_session(
            session_id="sess-123",
            agent_name="xiaona",
            request_id="req-456",
            user_id="user-789"
        )

        assert AgentSessionContext.get_session_id() == "sess-123"
        assert AgentSessionContext.get_agent_name() == "xiaona"
        assert AgentSessionContext.get_request_id() == "req-456"

        # 结束会话
        AgentSessionContext.end_session()
        assert AgentSessionContext.get_session_id() is None


class TestAttributes:
    """测试属性创建"""

    def test_agent_attributes(self):
        """测试Agent属性创建"""
        from core.tracing.attributes import AgentAttributes

        attrs = AgentAttributes.create(
            agent_name="xiaona",
            task_type="patent_analysis",
            agent_role="legal_expert"
        )

        assert attrs[AgentAttributes.AGENT_NAME] == "xiaona"
        assert attrs[AgentAttributes.AGENT_TASK_TYPE] == "patent_analysis"
        assert attrs[AgentAttributes.AGENT_ROLE] == "legal_expert"

    def test_llm_attributes(self):
        """测试LLM属性创建"""
        from core.tracing.attributes import LLMAttributes

        attrs = LLMAttributes.create(
            provider="claude",
            model="claude-3-opus",
            temperature=0.7
        )

        assert attrs[LLMAttributes.LLM_PROVIDER] == "claude"
        assert attrs[LLMAttributes.LLM_MODEL_NAME] == "claude-3-opus"
        assert attrs[LLMAttributes.LLM_TEMPERATURE] == 0.7

    def test_llm_response_attributes(self):
        """测试LLM响应属性"""
        from core.tracing.attributes import LLMAttributes

        attrs = LLMAttributes.create("claude", "claude-3-opus")
        attrs = LLMAttributes.add_response(
            attrs,
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300
        )

        assert attrs[LLMAttributes.LLM_TOKEN_COUNT_PROMPT] == 100
        assert attrs[LLMAttributes.LLM_TOKEN_COUNT_COMPLETION] == 200
        assert attrs[LLMAttributes.LLM_TOKEN_COUNT_TOTAL] == 300

    def test_database_attributes(self):
        """测试数据库属性"""
        from core.tracing.attributes import DatabaseAttributes

        attrs = DatabaseAttributes.create(
            db_system="postgresql",
            db_name="athena",
            operation="SELECT",
            table="patents"
        )

        assert attrs[DatabaseAttributes.DB_SYSTEM] == "postgresql"
        assert attrs[DatabaseAttributes.DB_NAME] == "athena"
        assert attrs[DatabaseAttributes.DB_OPERATION] == "SELECT"
        assert attrs[DatabaseAttributes.DB_TABLE] == "patents"

    def test_http_attributes(self):
        """测试HTTP属性"""
        from core.tracing.attributes import HTTPAttributes

        attrs = HTTPAttributes.create(
            method="GET",
            url="https://api.example.com/patents",
            status_code=200
        )

        assert attrs[HTTPAttributes.HTTP_METHOD] == "GET"
        assert attrs[HTTPAttributes.HTTP_URL] == "https://api.example.com/patents"
        assert attrs[HTTPAttributes.HTTP_STATUS_CODE] == 200

    def test_tool_attributes(self):
        """测试工具属性"""
        from core.tracing.attributes import ToolAttributes

        attrs = ToolAttributes.create(
            tool_name="patent_search",
            category="patent",
            status="success",
            duration_ms=150
        )

        assert attrs[ToolAttributes.TOOL_NAME] == "patent_search"
        assert attrs[ToolAttributes.TOOL_CATEGORY] == "patent"
        assert attrs[ToolAttributes.TOOL_STATUS] == "success"
        assert attrs[ToolAttributes.TOOL_DURATION_MS] == 150


class TestSetupFunction:
    """测试设置函数"""

    def test_get_config(self):
        """测试获取配置"""
        from core.tracing import get_config

        config = get_config()
        assert config is not None
        assert config.service_name == "athena-platform"

    def test_predefined_configs(self):
        """测试预定义配置"""
        from core.tracing import DEV_CONFIG, TEST_CONFIG, PROD_CONFIG

        assert DEV_CONFIG.environment == "dev"
        assert TEST_CONFIG.environment == "test"
        assert PROD_CONFIG.environment == "prod"

        # 测试采样率
        assert DEV_CONFIG.sample_rate == 0.1
        assert TEST_CONFIG.sample_rate == 1.0
        assert PROD_CONFIG.sample_rate == 0.01
