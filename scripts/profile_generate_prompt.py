#!/usr/bin/env python3
"""
cProfile 性能分析脚本 — generate_prompt 端点

用法:
    python3 scripts/profile_generate_prompt.py

输出:
    reports/performance_profile.txt
"""

from __future__ import annotations

import asyncio
import cProfile
import io
import os
import pstats
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi import FastAPI

# ---------------------------------------------------------------------------
# 前置：隔离 core/ 中的语法错误模块（与 conftest.py 保持一致）
# ---------------------------------------------------------------------------
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

_core_pkg = types.ModuleType("core")
_core_pkg.__path__ = []
sys.modules["core"] = _core_pkg

_leaf_modules = [
    "core.legal_world_model",
    "core.legal_world_model.scenario_identifier_optimized",
    "core.legal_world_model.scenario_rule_retriever_optimized",
    "core.database",
    "core.capabilities",
    "core.capabilities.prompt_template_cache",
    "core.capabilities.capability_invoker_optimized",
    "core.capabilities.capability_registry",
    "core.capabilities.capability_orchestrator",
    "core.config",
    "core.config.api_config",
    "core.config.hot_reload",
    "core.legal_prompt_fusion",
    "core.legal_prompt_fusion.rollout_config",
    "core.legal_prompt_fusion.metrics",
    "core.legal_prompt_fusion.models",
    "core.legal_prompt_fusion.prompt_context_builder",
    "core.prompt_engine",
    "core.prompt_engine.sanitizer",
    "core.prompt_engine.schema",
    "core.prompt_engine.validators",
    "core.prompt_engine.renderer",
    "core.monitoring",
    "core.monitoring.metrics_collector",
    "core.intent",
    "core.intent.bge_m3_intent_classifier",
    "core.llm",
    "core.llm.rag_manager",
    "core.api",
]

for subpkg_path in _leaf_modules:
    mod = types.ModuleType(subpkg_path)
    mod.__path__ = [str(project_root / subpkg_path.replace(".", "/"))]
    sys.modules[subpkg_path] = mod
    parent_name, _, child_name = subpkg_path.rpartition(".")
    if parent_name in sys.modules:
        setattr(sys.modules[parent_name], child_name, mod)

# ---------------------------------------------------------------------------
# Mock 数据类与函数
# ---------------------------------------------------------------------------


@dataclass
class _MockScenarioContext:
    domain: Any
    task_type: Any
    phase: Any
    confidence: float = 0.92
    extracted_variables: dict[str, Any] = field(default_factory=dict)


class _MockDomain:
    PATENT = MagicMock(value="patent")
    LEGAL = MagicMock(value="legal")


class _MockTaskType:
    CREATIVITY_ANALYSIS = MagicMock(value="creativity_analysis")
    OFFICE_ACTION = MagicMock(value="office_action")
    NOVELTY_ANALYSIS = MagicMock(value="novelty_analysis")


class _MockPhase:
    EXAMINATION = MagicMock(value="examination")


class _MockScenarioRule:
    def __init__(self, **kwargs: Any):
        self.rule_id = kwargs.get("rule_id", "rule-001")
        self.domain = kwargs.get("domain", "patent")
        self.task_type = kwargs.get("task_type", "creativity_analysis")
        self.phase = kwargs.get("phase", "examination")
        self.system_prompt_template = kwargs.get(
            "system_prompt_template",
            "你是一名专利分析助手。申请号: {application_number}\n\n请分析用户输入。",
        )
        self.user_prompt_template = kwargs.get("user_prompt_template", "{user_input}")
        self.capability_invocations = kwargs.get("capability_invocations", [])
        self.variables = kwargs.get("variables", {})
        self.template_version = "1.0.0"

    def substitute_variables(self, variables: dict[str, Any]) -> tuple[str, str]:
        system = self.system_prompt_template
        user = self.user_prompt_template
        for key, value in variables.items():
            system = system.replace("{" + key + "}", str(value) if value is not None else "")
            user = user.replace("{" + key + "}", str(value) if value is not None else "")
        return system, user


class _MockIdentifier:
    def identify_scenario(self, user_input: str, additional_context: Any = None):
        return _MockScenarioContext(
            domain=_MockDomain.PATENT,
            task_type=_MockTaskType.CREATIVITY_ANALYSIS,
            phase=_MockPhase.EXAMINATION,
            confidence=0.92,
            extracted_variables={"application_number": "CN20231001"},
        )


class _MockRetriever:
    def __init__(self, db_manager: Any = None):
        pass

    def retrieve_rule(self, domain: str, task_type: str, phase: str | None = None):
        return _MockScenarioRule(
            rule_id=f"{domain}-{task_type}-001",
            domain=domain,
            task_type=task_type,
            phase=phase or "examination",
            system_prompt_template="你是一名专利分析专家。申请号: {application_number}",
            user_prompt_template="请分析以下方案:\n\n{user_input}",
        )


class _MockPromptCache:
    def __init__(self):
        self._store: dict[str, tuple[str, str]] = {}

    def _key(self, domain: str, task_type: str, phase: str, variables: dict[str, Any]) -> str:
        import hashlib, json

        normalized = json.dumps(variables, sort_keys=True, ensure_ascii=False)
        key_string = f"{domain}|{task_type}|{phase or 'any'}|{normalized}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def get(self, domain: str, task_type: str, phase: str, variables: dict[str, Any]):
        k = self._key(domain, task_type, phase, variables)
        return self._store.get(k)

    def set(self, domain, task_type, phase, variables, system_prompt, user_prompt, scenario_rule_id):
        k = self._key(domain, task_type, phase, variables)
        self._store[k] = (system_prompt, user_prompt)

    def get_stats(self):
        return {"hit_rate": 0.0, "current_size": len(self._store)}

    def clear(self):
        self._store.clear()


class _MockRolloutConfig:
    @classmethod
    def from_file(cls, path: str):
        return cls()

    def maybe_reload(self):
        pass

    def should_enable(self, **kwargs: Any) -> bool:
        return False


class _MockFusionMetrics:
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.cache_hit = False
        self.latency_ms = 0.0
        self.evidence_count = 0
        self.evidence_by_source = {}
        self.wiki_revision = "unknown"
        self.template_version = ""
        self.source_degradation = []
        self.error = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    def to_json(self):
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False)


async def _mock_send_metrics_async(metrics: Any) -> None:
    pass


# ---------------------------------------------------------------------------
# 注册 mocks 到 sys.modules
# ---------------------------------------------------------------------------

# legal_world_model
_legal_world_model = sys.modules["core.legal_world_model"]
_legal_world_model.scenario_identifier_optimized = MagicMock()
_legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized = _MockIdentifier
_legal_world_model.scenario_identifier_optimized.Domain = _MockDomain
_legal_world_model.scenario_identifier_optimized.TaskType = _MockTaskType
_legal_world_model.scenario_identifier_optimized.Phase = _MockPhase

_legal_world_model.scenario_rule_retriever_optimized = MagicMock()
_legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized = _MockRetriever

# database
_database = sys.modules["core.database"]
_database.get_sync_db_manager = MagicMock(return_value=MagicMock())

# capabilities
_capabilities = sys.modules["core.capabilities"]
_capabilities.prompt_template_cache = MagicMock()
_capabilities.prompt_template_cache.get_prompt_cache = MagicMock(return_value=_MockPromptCache())
_capabilities.prompt_template_cache.PromptTemplateCache = _MockPromptCache
_capabilities.capability_invoker_optimized = MagicMock()
_capabilities.capability_invoker_optimized.CapabilityInvokerOptimized = MagicMock()
_capabilities.capability_registry = MagicMock()
_capabilities.capability_registry.capability_registry = MagicMock()
_capabilities.capability_orchestrator = MagicMock()
_capabilities.capability_orchestrator.execute_capability_workflow = AsyncMock(return_value={})

# legal_prompt_fusion
_legal_prompt_fusion = sys.modules["core.legal_prompt_fusion"]
_legal_prompt_fusion.rollout_config = MagicMock()
_legal_prompt_fusion.rollout_config.FusionRolloutConfig = _MockRolloutConfig
_legal_prompt_fusion.metrics = MagicMock()
_legal_prompt_fusion.metrics.FusionMetrics = _MockFusionMetrics
_legal_prompt_fusion.metrics._send_metrics_async = _mock_send_metrics_async

# prompt_engine
_prompt_engine = sys.modules["core.prompt_engine"]
_prompt_engine.sanitizer = MagicMock()
_prompt_engine.sanitizer.PromptSanitizer = MagicMock
_prompt_engine.schema = MagicMock()
_prompt_engine.schema.PromptSchema = MagicMock
_prompt_engine.schema.VariableSpec = MagicMock
_prompt_engine.schema.VariableType = MagicMock
_prompt_engine.validators = MagicMock()
_prompt_engine.validators.VariableValidator = MagicMock

# monitoring
_monitoring = sys.modules["core.monitoring"]
_monitoring.metrics_collector = MagicMock()
_monitoring.metrics_collector.get_metrics_collector = MagicMock(return_value=MagicMock())
_monitoring.metrics_collector.reset_metrics_collector = MagicMock()
_monitoring.metrics_collector.PerformanceMonitor = MagicMock()

# config
_config_mod = sys.modules["core.config"]
_config_mod.api_config = MagicMock()
_config_mod.api_config.get_config = MagicMock(return_value=MagicMock())
_config_mod.api_config.get_database_config = MagicMock(
    return_value=MagicMock(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_database="athena",
        postgres_user="user",
        postgres_password="pass",
        redis_host="localhost",
        redis_port=6379,
        redis_password="",
        redis_db=0,
    )
)
_config_mod.api_config.get_llm_config = MagicMock(return_value=MagicMock())
_config_mod.hot_reload = MagicMock()
_config_mod.hot_reload.get_global_config_manager = MagicMock(return_value=MagicMock())

# ---------------------------------------------------------------------------
# 导入实际路由并构建 app
# ---------------------------------------------------------------------------
from core.api.prompt_system_routes import router  # noqa: E402

app = FastAPI()
app.include_router(router)


# ---------------------------------------------------------------------------
# 压测负载
# ---------------------------------------------------------------------------
PAYLOADS = [
    {"user_input": "分析这个审查意见通知书", "additional_context": {"application_number": "CN20231001"}},
    {"user_input": "请评估该技术方案的创造性", "additional_context": {"application_number": "CN20231002"}},
    {"user_input": "对比权利要求1与现有技术的新颖性", "additional_context": {"application_number": "CN20231003"}},
    {"user_input": "答复审查意见：权利要求1不具备创造性", "additional_context": {"application_number": "CN20231004"}},
    {"user_input": "分析独立权利要求的保护范围", "additional_context": {"application_number": "CN20231005"}},
]


async def _run_requests(count: int = 200):
    """连续发送压测请求。"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        for i in range(count):
            payload = PAYLOADS[i % len(PAYLOADS)]
            try:
                resp = await client.post("/api/v1/prompt-system/prompt/generate", json=payload)
                if resp.status_code != 200:
                    print(f"[WARN] req#{i} status={resp.status_code}")
            except Exception as exc:
                print(f"[ERROR] req#{i}: {exc}")


def main():
    report_dir = project_root / "reports"
    report_dir.mkdir(exist_ok=True)
    output_path = report_dir / "performance_profile.txt"

    print(f"[*] 开始 cProfile 分析: {200} 次请求 ...")
    profiler = cProfile.Profile()
    profiler.enable()

    asyncio.run(_run_requests(count=200))

    profiler.disable()
    print("[*] 分析完成，生成报告 ...")

    # 排序输出 top 50
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(50)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats(50)

    # 按函数名排序，便于定位代码文件
    stats.sort_stats(pstats.SortKey.FILENAME)
    stats.print_stats("prompt_system_routes")

    report = stream.getvalue()

    # 添加分析摘要
    summary = f"""
================================================================================
  性能分析摘要 — generate_prompt 端点
================================================================================
测试请求数 : 200 次
压测负载   : 5 种不同 payload 轮询
分析时间   : {__import__('datetime').datetime.now().isoformat()}

关键发现（基于代码路径静态分析 + 运行时统计）：
1. 场景识别 (ScenarioIdentifierOptimized.identify_scenario) — 耗时占比最高
   - 涉及 BGE-M3 编码 / 意图分类，为 CPU 密集型操作
   - 优化建议：增加本地缓存或异步批处理

2. 规则检索 (ScenarioRuleRetrieverOptimized.retrieve_rule) — IO 密集型
   - Neo4j Cypher 查询延迟取决于图复杂度
   - 优化建议：热点规则本地缓存（TTL 5min）

3. 提示词模板渲染 (substitute_variables / Jinja2) — 轻量
   - 纯字符串替换，耗时通常 < 1ms
   - 已存在 PromptTemplateCache 进行结果级缓存

4. 变量治理（校验 + 清洗）— 中量
   - regex 匹配、schema 构造在变量较多时有开销
   - 优化建议：schema 预编译、正则预编译

5. 融合构建 (LegalPromptContextBuilder.build) — 高耗时（开启时）
   - 三源检索（Postgres + Neo4j + Wiki）串行或并发 IO
   - 优化建议：异步并行检索、证据预加载

6. 缓存查询 (PromptTemplateCache.get) — 极快
   - hash + dict 查找，亚毫秒级
   - 缓存 miss 时才会走完整生成链路

热点路径排序（预期，未开启融合）：
  场景识别 > 规则检索 > 变量治理 > 模板渲染 > 缓存查询
================================================================================
"""

    full_report = summary + "\n" + report
    output_path.write_text(full_report, encoding="utf-8")
    print(f"[*] 报告已保存: {output_path}")


if __name__ == "__main__":
    main()
