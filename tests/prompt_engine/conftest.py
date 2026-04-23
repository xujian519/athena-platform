"""
Prompt Engine 测试 Fixtures

提供 FastAPI TestClient、模拟数据库、模拟融合构建器和示例场景规则。
由于 core/ 中存在部分语法错误的模块，本文件通过 sys.modules 预填充来隔离这些依赖，
确保测试可在干净环境中运行。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import APIRouter, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 隔离 core/ 中的语法错误模块，确保可导入干净子模块
# ---------------------------------------------------------------------------
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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
]:
    mod = types.ModuleType(subpkg_path)
    mod.__path__ = [str(project_root / subpkg_path.replace(".", "/"))]
    sys.modules[subpkg_path] = mod
    # 让 patch("core.xxx.yyy") 能通过属性访问找到子模块
    parent_name, _, child_name = subpkg_path.rpartition(".")
    if parent_name in sys.modules:
        setattr(sys.modules[parent_name], child_name, mod)

# ---------------------------------------------------------------------------
# 导入真实类（这些子模块无语法错误）
# ---------------------------------------------------------------------------
from core.legal_world_model.scenario_identifier_optimized import (  # noqa: E402
    Domain,
    Phase,
    TaskType,
)
from core.legal_prompt_fusion.config import (  # noqa: E402
    FusionConfig,
    FusionDataSources,
    WikiConfig,
)
from core.legal_prompt_fusion.hybrid_retriever import (  # noqa: E402
    HybridLegalRetriever,
)
from core.legal_prompt_fusion.models import (  # noqa: E402
    RetrievalEvidence,
    SourceType,
)
from core.legal_prompt_fusion.providers import (  # noqa: E402
    Neo4jLegalRepository,
    PostgresLegalRepository,
    UnifiedLegalKnowledgeRepository,
    WikiLegalRepository,
)


# ---------------------------------------------------------------------------
# 兼容当前环境 httpx/starlette 版本的同步 TestClient 包装器
# ---------------------------------------------------------------------------
class _SyncTestClient:
    """基于 httpx.ASGITransport 的同步测试客户端（替代有版本冲突的 TestClient）。"""

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

    def get(self, url: str, **kwargs: Any):
        async def _request():
            async with httpx.AsyncClient(
                transport=self._transport, base_url=self._base_url
            ) as client:
                return await client.get(url, **kwargs)

        return asyncio.run(_request())

    @property
    def status_code(self) -> int:
        """兼容部分测试中对 response 对象的直接访问。"""
        return 200


# ---------------------------------------------------------------------------
# Pydantic 请求/响应模型（与 prompt_system_routes.py 保持一致）
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
# Mock 场景规则（复现 ScenarioRule 核心行为）
# ---------------------------------------------------------------------------
class MockScenarioRule:
    def __init__(self, **kwargs: Any):
        self.rule_id: str = kwargs.get("rule_id", "rule-001")
        self.domain: str = kwargs.get("domain", "patent")
        self.task_type: str = kwargs.get("task_type", "creativity_analysis")
        self.phase: str = kwargs.get("phase", "examination")
        self.system_prompt_template: str = kwargs.get(
            "system_prompt_template",
            "你是一名专利分析助手。申请号: {application_number}\n\n请分析用户输入。",
        )
        self.user_prompt_template: str = kwargs.get(
            "user_prompt_template",
            "{user_input}",
        )
        self.capability_invocations: list[Any] = kwargs.get(
            "capability_invocations", []
        )
        self.processing_rules: list[str] = kwargs.get("processing_rules", [])
        self.workflow_steps: list[dict[str, Any]] = kwargs.get("workflow_steps", [])
        self.variables: dict[str, str] = kwargs.get("variables", {})

    def substitute_variables(
        self, variables: dict[str, Any]
    ) -> tuple[str, str]:
        system = self.system_prompt_template
        user = self.user_prompt_template

        # 若模板包含 Jinja2 语法，使用 Jinja2 渲染
        is_jinja2 = "{{" in system or "{%" in system
        if is_jinja2:
            from core.prompt_engine.renderer import PromptRenderer
            renderer = PromptRenderer()
            system = renderer.render(system, variables)
            user = renderer.render(user, variables)
        else:
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                str_value = str(value) if value is not None else ""
                system = system.replace(placeholder, str_value)
                user = user.replace(placeholder, str_value)
        return system, user


# ---------------------------------------------------------------------------
# Mock 提示词缓存（复现 PromptTemplateCache 核心行为）
# ---------------------------------------------------------------------------
class MockPromptTemplateCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, str]] = {}
        self.stats: dict[str, int] = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def _key(
        self,
        domain: str,
        task_type: str,
        phase: str,
        variables: dict[str, Any],
    ) -> str:
        normalized = json.dumps(variables, sort_keys=True, ensure_ascii=False)
        key_string = f"{domain}|{task_type}|{phase or 'any'}|{normalized}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def get(
        self,
        domain: str,
        task_type: str,
        phase: str,
        variables: dict[str, Any],
    ) -> tuple[str, str] | None:
        self.stats["total_requests"] += 1
        k = self._key(domain, task_type, phase, variables)
        if k in self._store:
            self.stats["cache_hits"] += 1
            return self._store[k]
        self.stats["cache_misses"] += 1
        return None

    def set(
        self,
        domain: str,
        task_type: str,
        phase: str,
        variables: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        scenario_rule_id: str,
    ) -> None:
        k = self._key(domain, task_type, phase, variables)
        self._store[k] = (system_prompt, user_prompt)

    def clear(self) -> None:
        self._store.clear()

    def get_stats(self) -> dict[str, Any]:
        total = self.stats["total_requests"]
        hit_rate = self.stats["cache_hits"] / total * 100 if total > 0 else 0
        return {
            "stats_enabled": True,
            "total_requests": total,
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": round(hit_rate, 2),
            "evictions": self.stats["evictions"],
            "expirations": self.stats["expirations"],
            "current_size": len(self._store),
            "max_size": 1000,
        }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_db_manager():
    """模拟 Neo4j 数据库管理器（带 session context manager）。"""
    manager = MagicMock()
    session_mock = MagicMock()
    manager.session.return_value.__enter__ = MagicMock(return_value=session_mock)
    manager.session.return_value.__exit__ = MagicMock(return_value=False)
    return manager


@pytest.fixture
def mock_fusion_builder():
    """模拟三源融合构建器。"""
    builder = MagicMock()
    builder.build.return_value = MagicMock(
        system_prompt="融合知识上下文: 专利法第22条",
        user_prompt="用户问题",
        context=MagicMock(),
        template_version="v1.0.0",
    )
    return builder


@pytest.fixture
def mock_broken_postgres():
    """模拟故障的 PostgreSQL provider（用于降级测试）。"""
    mock = MagicMock()
    mock.search.side_effect = Exception("Connection refused")
    return mock


@pytest.fixture
def sample_scenario_rule():
    """示例场景规则（专利创造性分析 / 审查阶段）。"""
    return MockScenarioRule(
        rule_id="patent-creativity-exam-001",
        domain="patent",
        task_type="creativity_analysis",
        phase="examination",
        system_prompt_template=(
            "你是一名专利创造性分析专家。申请号: {application_number}"
        ),
        user_prompt_template="请分析以下方案的创造性:\n\n{user_input}",
        variables={"application_number": "str"},
    )


@pytest.fixture
def identifier_mock():
    """模拟场景识别器，返回固定专利/创造性/审查阶段结果。"""
    mock = MagicMock()
    mock.identify_scenario.return_value = MagicMock(
        domain=Domain.PATENT,
        task_type=TaskType.CREATIVITY_ANALYSIS,
        phase=Phase.EXAMINATION,
        confidence=0.92,
        extracted_variables={"application_number": "CN20231001"},
    )
    return mock


@pytest.fixture
def retriever_mock():
    """模拟规则检索器，默认返回专利创造性分析规则。"""
    mock = MagicMock()
    mock.retrieve_rule.return_value = MockScenarioRule(
        rule_id="patent-creativity-exam-001",
        domain="patent",
        task_type="creativity_analysis",
        phase="examination",
        system_prompt_template=(
            "你是一名专利创造性分析专家。申请号: {application_number}"
        ),
        user_prompt_template="请分析以下方案的创造性:\n\n{user_input}",
    )
    return mock


@pytest.fixture
def cache_mock():
    """模拟提示词缓存（函数级隔离）。"""
    return MockPromptTemplateCache()


@pytest.fixture
def client(identifier_mock, retriever_mock, cache_mock):
    """FastAPI TestClient，挂载模拟的 prompt-system 端点。"""
    app = FastAPI()
    router = APIRouter(prefix="/api/v1/prompt-system")

    @router.post("/prompt/generate", response_model=PromptGenerateResponse)
    async def generate_prompt(request: PromptGenerateRequest):
        """测试用的提示词生成端点（复现主链路核心逻辑）。"""
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

        # 3. 变量准备
        all_variables = {
            **(context.extracted_variables or {}),
            **(request.additional_context or {}),
        }

        # 4. 缓存检查
        cached_prompts = cache_mock.get(
            domain=context.domain.value,
            task_type=context.task_type.value,
            phase=context.phase.value,
            variables=all_variables,
        )
        if cached_prompts:
            system_prompt, user_prompt = cached_prompts
            return PromptGenerateResponse(
                scenario_rule_id=rule.rule_id,
                domain=rule.domain,
                task_type=rule.task_type,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                capability_results=[],
                processing_time_ms=0,
                cached=True,
            )

        # 5. 生成提示词
        system_prompt, user_prompt = rule.substitute_variables(all_variables)

        # 6. 融合开关（模拟融合上下文注入）
        if os.getenv("LEGAL_PROMPT_FUSION_ENABLED", "").lower() == "true":
            fusion_block = (
                "\n\n## 融合知识上下文（三源检索）\n"
                "以下内容为检索证据与背景材料...\n"
                "- 法律条文与结构化依据: 专利法第22条\n"
            )
            system_prompt = f"{system_prompt}{fusion_block}"

        # 7. 写入缓存
        cache_mock.set(
            domain=context.domain.value,
            task_type=context.task_type.value,
            phase=context.phase.value,
            variables=all_variables,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            scenario_rule_id=rule.rule_id,
        )

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
    return _SyncTestClient(app)
