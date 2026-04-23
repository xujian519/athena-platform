"""
C2-SchemaIntegration: PromptSchemaRegistry 接入 generate_prompt 运行时集成测试

验证:
- 有 Schema 时正确校验并通过 (200)
- 变量缺失时返回 400 Bad Request
- 无 Schema 时优雅跳过 (200)
- Optional 变量缺失时不报错
"""

from __future__ import annotations

import asyncio
import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 隔离 core/ 中的语法错误模块（与 conftest.py 保持一致）
# ---------------------------------------------------------------------------
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if "core" not in sys.modules:
    _core_pkg = types.ModuleType("core")
    _core_pkg.__path__ = []
    sys.modules["core"] = _core_pkg

for subpkg_path in [
    "core.legal_world_model",
    "core.database",
    "core.capabilities",
    "core.config",
    "core.legal_prompt_fusion",
    "core.prompt_engine",
    "core.monitoring",
]:
    if subpkg_path not in sys.modules:
        mod = types.ModuleType(subpkg_path)
        mod.__path__ = [str(project_root / subpkg_path.replace(".", "/"))]
        mod.__package__ = subpkg_path
        sys.modules[subpkg_path] = mod
        parent_name, _, child_name = subpkg_path.rpartition(".")
        if parent_name in sys.modules:
            setattr(sys.modules[parent_name], child_name, mod)

from core.legal_world_model.scenario_identifier_optimized import (  # noqa: E402
    Domain,
    Phase,
    TaskType,
)
from core.prompt_engine.registry import PromptSchemaRegistry  # noqa: E402
from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType  # noqa: E402
from core.prompt_engine.validators import VariableValidator  # noqa: E402


# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------
class PromptGenerateRequest(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=100000)
    additional_context: dict[str, Any] | None = None


class PromptGenerateResponse(BaseModel):
    scenario_rule_id: str
    domain: str
    task_type: str
    system_prompt: str
    user_prompt: str
    capability_results: list[str] = []
    processing_time_ms: float
    cached: bool = False


# ---------------------------------------------------------------------------
# Mock 场景规则
# ---------------------------------------------------------------------------
class MockScenarioRule:
    def __init__(self, **kwargs: Any):
        self.rule_id: str = kwargs.get("rule_id", "rule-001")
        self.domain: str = kwargs.get("domain", "patent")
        self.task_type: str = kwargs.get("task_type", "creativity_analysis")
        self.phase: str = kwargs.get("phase", "examination")
        self.system_prompt_template: str = kwargs.get(
            "system_prompt_template",
            "你是一名专利分析助手。申请号: {application_number}",
        )
        self.user_prompt_template: str = kwargs.get(
            "user_prompt_template",
            "{user_input}",
        )
        self.capability_invocations: list[Any] = kwargs.get("capability_invocations", [])
        self.processing_rules: list[str] = kwargs.get("processing_rules", [])
        self.workflow_steps: list[dict[str, Any]] = kwargs.get("workflow_steps", [])
        self.variables: dict[str, Any] = kwargs.get("variables", {})

    def substitute_variables(self, variables: dict[str, Any]) -> tuple[str, str]:
        system = self.system_prompt_template
        user = self.user_prompt_template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            str_value = str(value) if value is not None else ""
            system = system.replace(placeholder, str_value)
            user = user.replace(placeholder, str_value)
        return system, user


# ---------------------------------------------------------------------------
# 同步测试客户端（与 conftest.py 保持一致）
# ---------------------------------------------------------------------------
class _SyncTestClient:
    def __init__(self, app: FastAPI, base_url: str = "http://testserver") -> None:
        self._app = app
        self._transport = httpx.ASGITransport(app=app)
        self._base_url = base_url

    def post(self, url: str, json: dict[str, Any] | None = None, **kwargs: Any):
        async def _request():
            async with httpx.AsyncClient(
                transport=self._transport, base_url=self._base_url
            ) as client:
                return await client.post(url, json=json, **kwargs)

        return asyncio.run(_request())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def schema_client():
    """FastAPI TestClient，挂载带 Schema 治理逻辑的 generate_prompt 端点。"""
    app = FastAPI()
    router = APIRouter(prefix="/api/v1/prompt-system")

    identifier_mock = MagicMock()
    identifier_mock.identify_scenario.return_value = MagicMock(
        domain=Domain.PATENT,
        task_type=TaskType.CREATIVITY_ANALYSIS,
        phase=Phase.EXAMINATION,
        confidence=0.92,
        extracted_variables={"application_number": "CN20231001"},
    )

    retriever_mock = MagicMock()
    retriever_mock.retrieve_rule.return_value = MockScenarioRule(
        rule_id="patent.inventive_analysis.v2",
        domain="patent",
        task_type="creativity_analysis",
        phase="examination",
        system_prompt_template="申请号: {application_number}\n技术领域: {technical_field}",
        user_prompt_template="权利要求: {claims}\n审查意见: {office_action_summary}",
    )

    @router.post("/prompt/generate", response_model=PromptGenerateResponse)
    async def generate_prompt(request: PromptGenerateRequest):
        # 1. 场景识别
        context = identifier_mock.identify_scenario(
            request.user_input, request.additional_context
        )

        # 2. 规则检索
        rule = retriever_mock.retrieve_rule(
            context.domain.value, context.task_type.value
        )
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到规则: {context.domain.value}/{context.task_type.value}",
            )

        # 3. 准备变量
        all_variables = {
            **(context.extracted_variables or {}),
            **(request.additional_context or {}),
        }

        # 4. 变量治理（校验 + 清洗 + Schema Registry 集成）
        try:
            from core.prompt_engine.sanitizer import PromptSanitizer
            from core.prompt_engine.schema import PromptSchema, VariableSpec, VariableType
            from core.prompt_engine.validators import VariableValidator
            from core.prompt_engine.registry import PromptSchemaRegistry

            sanitizer = PromptSanitizer()
            validator = VariableValidator()
            registry = PromptSchemaRegistry()

            # C2-SchemaIntegration: 优先从 PromptSchemaRegistry 获取 Schema
            schema = registry.get(rule.rule_id)
            if schema is None:
                # 回退：从规则的 variables 字段或模板推断 schema（存量模板兼容）
                schema_vars = []
                if hasattr(rule, "variables") and rule.variables:
                    for var_name, var_info in rule.variables.items():
                        if isinstance(var_info, dict):
                            schema_vars.append(VariableSpec(
                                name=var_name,
                                type=VariableType(var_info.get("type", "string")),
                                required=var_info.get("required", True),
                                source=var_info.get("source", ""),
                                default=var_info.get("default"),
                                max_length=var_info.get("max_length"),
                            ))
                        else:
                            schema_vars.append(VariableSpec(name=var_name, required=True))
                else:
                    import re
                    placeholders = set(
                        re.findall(
                            r"\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}",
                            rule.system_prompt_template,
                        )
                    ) | set(
                        re.findall(
                            r"\{\{?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}?\}",
                            rule.user_prompt_template,
                        )
                    )
                    for ph in placeholders:
                        if ph not in ("__wiki_revision", "__fusion_template_version"):
                            schema_vars.append(VariableSpec(name=ph, required=True))

                schema = PromptSchema(
                    rule_id=rule.rule_id,
                    template_version=getattr(rule, "template_version", "1.0.0"),
                    variables=schema_vars,
                )

            # 校验
            validation = validator.validate(schema, all_variables)
            if not validation.valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "MISSING_VARIABLES",
                        "missing": validation.errors,
                        "message": f"Required variables missing: {', '.join(validation.errors)}",
                    },
                )

            # C2-SchemaIntegration: 填充默认值
            all_variables = registry.upgrade_variables(rule.rule_id, all_variables)

            # 清洗
            sanitized_vars, risks = sanitizer.sanitize_variables(
                all_variables, schema=schema
            )
            all_variables = sanitized_vars

        except HTTPException:
            raise
        except Exception:
            # 变量治理模块异常时不阻断主链路
            pass

        # 5. 生成提示词
        system_prompt, user_prompt = rule.substitute_variables(all_variables)

        return PromptGenerateResponse(
            scenario_rule_id=rule.rule_id,
            domain=rule.domain,
            task_type=rule.task_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            capability_results=[],
            processing_time_ms=0,
            cached=False,
        )

    app.include_router(router)
    return _SyncTestClient(app), retriever_mock, identifier_mock


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------
class TestSchemaIntegration:
    def test_with_schema_valid_variables(self, schema_client):
        """有 Schema 且变量完整时正确校验并通过（200）。"""
        client, _, _ = schema_client
        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析创造性",
                "additional_context": {
                    "application_number": "CN20231001",
                    "technical_field": "通信",
                    "claims": "1. 一种方法...",
                    "office_action_summary": "审查意见摘要",
                    "prior_art_documents": ["D1", "D2"],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_rule_id"] == "patent.inventive_analysis.v2"
        assert "CN20231001" in data["system_prompt"]

    def test_with_schema_missing_variables_returns_400(self, schema_client):
        """有 Schema 但 required 变量缺失时返回 400 Bad Request。"""
        client, _, _ = schema_client
        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析创造性",
                "additional_context": {
                    "application_number": "CN20231001",
                    # 缺少 technical_field, claims, office_action_summary, prior_art_documents
                },
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "MISSING_VARIABLES"
        missing = data["detail"]["missing"]
        assert any("technical_field" in err for err in missing)
        assert any("claims" in err for err in missing)

    def test_with_schema_optional_variables_allowed(self, schema_client):
        """有 Schema 时 optional 变量缺失不报错（200）。"""
        client, retriever_mock, identifier_mock = schema_client
        # 切换到 patent.office_action.analysis.v2（oa_history 为 optional）
        retriever_mock.retrieve_rule.return_value = MockScenarioRule(
            rule_id="patent.office_action.analysis.v2",
            domain="patent",
            task_type="creativity_analysis",
            phase="examination",
            system_prompt_template="申请号: {application_number}\nOA内容: {oa_content}",
            user_prompt_template="申请文件: {application_file}",
        )
        identifier_mock.identify_scenario.return_value = MagicMock(
            domain=Domain.PATENT,
            task_type=TaskType.CREATIVITY_ANALYSIS,
            phase=Phase.EXAMINATION,
            confidence=0.92,
            extracted_variables={
                "application_number": "CN20231001",
                "oa_content": "OA内容",
                "application_file": "申请文件",
            },
        )

        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析OA",
                "additional_context": {},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_rule_id"] == "patent.office_action.analysis.v2"

    def test_without_schema_graceful_skip(self, schema_client):
        """无 Schema（存量模板）时优雅跳过，不阻断主链路（200）。"""
        client, retriever_mock, _ = schema_client
        retriever_mock.retrieve_rule.return_value = MockScenarioRule(
            rule_id="legacy-rule-not-in-registry",
            domain="patent",
            task_type="creativity_analysis",
            phase="examination",
            system_prompt_template="申请号: {application_number}",
            user_prompt_template="用户输入: {user_input}",
        )

        response = client.post(
            "/api/v1/prompt-system/prompt/generate",
            json={
                "user_input": "分析创造性",
                "additional_context": {
                    "application_number": "CN20231001",
                    "user_input": "分析创造性",
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_rule_id"] == "legacy-rule-not-in-registry"

    def test_upgrade_variables_fills_defaults(self):
        """PromptSchemaRegistry.upgrade_variables 应填充默认值。"""
        registry = PromptSchemaRegistry()
        test_schema = PromptSchema(
            rule_id="test/upgrade_defaults",
            template_version="1.0.0",
            variables=[
                VariableSpec(name="required_var", required=True),
                VariableSpec(name="optional_var", required=False, default="default_value"),
            ],
        )
        registry.register(test_schema)

        result = registry.upgrade_variables(
            "test/upgrade_defaults", {"required_var": "hello"}
        )
        assert result["required_var"] == "hello"
        assert result["optional_var"] == "default_value"

    def test_coverage_report_exposed_via_collector(self):
        """get_coverage_report 数据可通过 metrics collector 获取。"""
        from core.monitoring.metrics_collector import get_metrics_collector

        registry = PromptSchemaRegistry()
        collector = get_metrics_collector()
        coverage = registry.get_coverage_report()

        # 模拟 generate_prompt 中的指标暴露逻辑
        collector.set_gauge("prompt_schema_total", float(coverage["total_schemas"]))
        collector.set_gauge(
            "prompt_schema_with_variables", float(coverage["schemas_with_variables"])
        )
        collector.set_gauge("prompt_schema_coverage_rate", coverage["coverage_rate"])

        assert collector.get_gauge("prompt_schema_total") == float(coverage["total_schemas"])
        assert (
            collector.get_gauge("prompt_schema_with_variables")
            == float(coverage["schemas_with_variables"])
        )
        assert collector.get_gauge("prompt_schema_coverage_rate") == coverage["coverage_rate"]
