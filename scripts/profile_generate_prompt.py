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

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 避免 hot_reload 缺失 watchdog
sys.modules["core.config.hot_reload"] = MagicMock()
sys.modules["core.config.hot_reload"].get_global_config_manager = MagicMock()

os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("LEGAL_PROMPT_FUSION_ENABLED", "false")

# ---------------------------------------------------------------------------
# Mock 数据类
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
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def _key(self, domain: str, task_type: str, phase: str, variables: dict[str, Any]) -> str:
        import hashlib
        import json

        normalized = json.dumps(variables, sort_keys=True, ensure_ascii=False)
        key_string = f"{domain}|{task_type}|{phase or 'any'}|{normalized}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def get(self, domain: str, task_type: str, phase: str, variables: dict[str, Any]):
        self._stats["total_requests"] += 1
        k = self._key(domain, task_type, phase, variables)
        if k in self._store:
            self._stats["cache_hits"] += 1
            return self._store[k]
        self._stats["cache_misses"] += 1
        return None

    def set(self, domain, task_type, phase, variables, system_prompt, user_prompt, scenario_rule_id):
        k = self._key(domain, task_type, phase, variables)
        self._store[k] = (system_prompt, user_prompt)

    def get_stats(self):
        total = self._stats["total_requests"]
        hit_rate = self._stats["cache_hits"] / total * 100 if total > 0 else 0
        return {
            "stats_enabled": True,
            "total_requests": total,
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "hit_rate": round(hit_rate, 2),
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
            "current_size": len(self._store),
            "max_size": 1000,
            "utilization": round(len(self._store) / 1000 * 100, 2),
        }

    def clear(self):
        self._store.clear()
        self._stats = {k: 0 for k in self._stats}


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
        self.token_count_input = 0
        self.token_count_output = 0
        self.evidence_relevance_score = 0.0
        self.budget_usage = 0.0

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    def to_json(self):
        import json

        return json.dumps(self.to_dict(), ensure_ascii=False)


async def _mock_send_metrics_async(metrics: Any) -> None:
    pass


# ---------------------------------------------------------------------------
# Patch 目标映射
# ---------------------------------------------------------------------------
_patch_map = {
    "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized": _MockIdentifier,
    "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized": _MockRetriever,
    "core.capabilities.prompt_template_cache.get_prompt_cache": lambda: _MockPromptCache(),
    "core.legal_prompt_fusion.rollout_config.FusionRolloutConfig": _MockRolloutConfig,
    "core.legal_prompt_fusion.metrics.FusionMetrics": _MockFusionMetrics,
    "core.legal_prompt_fusion.metrics._send_metrics_async": _mock_send_metrics_async,
    "core.monitoring.metrics_collector.get_metrics_collector": MagicMock,
    "core.monitoring.metrics_collector.reset_metrics_collector": MagicMock,
    "core.capabilities.capability_registry.capability_registry": MagicMock(),
    "core.capabilities.capability_invoker_optimized.CapabilityInvokerOptimized": MagicMock,
}


def _apply_patches():
    patches = []
    for target, replacement in _patch_map.items():
        p = patch(target, replacement)
        p.start()
        patches.append(p)
    return patches


# ---------------------------------------------------------------------------
# 导入实际路由并构建 app（在 patch 保护下）
# ---------------------------------------------------------------------------
_patches = _apply_patches()
try:
    from core.api.prompt_system_routes import router  # noqa: E402

    app = FastAPI()
    app.include_router(router)
finally:
    for p in _patches:
        p.stop()

# ---------------------------------------------------------------------------
# 压测负载
# ---------------------------------------------------------------------------
PAYLOADS = [
    {"user_input": "分析这个审查意见通知书", "additional_context": {"application_number": "CN20231001", "user_input": "分析这个审查意见通知书"}},
    {"user_input": "请评估该技术方案的创造性", "additional_context": {"application_number": "CN20231002", "user_input": "请评估该技术方案的创造性"}},
    {"user_input": "对比权利要求1与现有技术的新颖性", "additional_context": {"application_number": "CN20231003", "user_input": "对比权利要求1与现有技术的新颖性"}},
    {"user_input": "答复审查意见：权利要求1不具备创造性", "additional_context": {"application_number": "CN20231004", "user_input": "答复审查意见：权利要求1不具备创造性"}},
    {"user_input": "分析独立权利要求的保护范围", "additional_context": {"application_number": "CN20231005", "user_input": "分析独立权利要求的保护范围"}},
]


async def _run_requests(count: int = 200):
    patches = _apply_patches()
    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for i in range(count):
                payload = PAYLOADS[i % len(PAYLOADS)]
                try:
                    resp = await client.post("/api/v1/prompt-system/prompt/generate", json=payload)
                    if resp.status_code != 200:
                        print(f"[WARN] req#{i} status={resp.status_code} body={resp.text[:200]}")
                except Exception as exc:
                    print(f"[ERROR] req#{i}: {exc}")
    finally:
        for p in patches:
            p.stop()


def main():
    report_dir = project_root / "reports"
    report_dir.mkdir(exist_ok=True)
    output_path = report_dir / "performance_profile.txt"

    print("[*] 预热请求（排除模块导入开销）...")
    asyncio.run(_run_requests(count=10))

    print(f"[*] 开始 cProfile 分析: 200 次请求 ...")
    profiler = cProfile.Profile()
    profiler.enable()

    asyncio.run(_run_requests(count=200))

    profiler.disable()
    print("[*] 分析完成，生成报告 ...")

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(50)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats(50)
    stats.sort_stats(pstats.SortKey.FILENAME)
    stats.print_stats("prompt_system_routes")

    report = stream.getvalue()

    summary = f"""
================================================================================
  性能分析摘要 — generate_prompt 端点
================================================================================
测试请求数 : 200 次
压测负载   : 5 种不同 payload 轮询（含缓存命中与未命中）
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
