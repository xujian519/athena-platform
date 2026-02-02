#!/usr/bin/env python3
"""
异步场景规则检索器
Async Scenario Rule Retriever

版本: 1.0.0
功能:
- 异步数据库查询
- 批量预加载
- 连接池管理
- 优化N+1查询问题
"""

import asyncio
import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class PreloadStatus(Enum):
    """预加载状态"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ScenarioRule:
    """场景规则数据类"""

    rule_id: str
    domain: str
    task_type: str
    phase: str
    system_prompt_template: str
    user_prompt_template: str
    processing_rules: list[str] = field(default_factory=list)
    workflow_steps: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    legal_basis: list[str] = field(default_factory=list)
    reference_cases: list[dict[str, str]] = field(default_factory=list)
    expert_config: dict[str, Any] = field(default_factory=dict)
    agent_level: str = "L2"
    lyra_optimization: bool = True
    lyra_focus: list[str] = field(default_factory=list)

    def substitute_variables(self, variables: dict[str, Any]) -> tuple[str, str]:
        """替换提示词模板中的变量"""
        import html

        system_prompt = self.system_prompt_template
        user_prompt = self.user_prompt_template

        for key, value in variables.items():
            placeholder = "{" + key + "}"
            str_value = html.escape(str(value)) if value is not None else ""
            system_prompt = system_prompt.replace(placeholder, str_value)
            user_prompt = user_prompt.replace(placeholder, str_value)

        return system_prompt, user_prompt


class AsyncScenarioRuleRetriever:
    """
    异步场景规则检索器

    优化点:
    1. 异步数据库查询,避免阻塞事件循环
    2. 批量预加载,解决N+1查询问题
    3. 连接池复用
    """

    ALLOWED_DOMAINS = {"patent", "trademark", "legal", "copyright", "other"}
    ALLOWED_TASK_TYPES = {
        "creativity_analysis",
        "novelty_analysis",
        "infringement",
        "similarity",
        "validity",
        "drafting",
        "search",
        "other",
    }
    ALLOWED_PHASES = {"application", "examination", "opposition", "litigation", "other"}

    def __init__(
        self,
        db_manager,
        cache_ttl: int = 3600,
        enable_preload: bool = True,
        preload_on_init: bool = True,
        preload_domains: set[str | None = None,
    ):
        """
        初始化异步规则检索器

        Args:
            db_manager: 数据库管理器实例
            cache_ttl: 缓存生存时间(秒)
            enable_preload: 是否启用预加载
            preload_on_init: 是否在初始化时预加载
            preload_domains: 预加载的领域集合
        """
        self.db_manager = db_manager
        self.cache_ttl = cache_ttl
        self.enable_preload = enable_preload
        self.preload_on_init = preload_on_init
        self.preload_domains = preload_domains or self.ALLOWED_DOMAINS

        # 缓存存储
        self._cache: OrderedDict[str, tuple[Any, datetime]] = OrderedDict()

        # 预加载状态
        self._preload_status = PreloadStatus.NOT_STARTED
        self._preload_progress: dict[str, int] = {}

        # 性能指标
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_query_time_ms": 0,
            "error_count": 0,
            "preload_count": 0,
            "preload_time_ms": 0,
        }

        logger.info("✅ 异步场景规则检索器初始化完成")

        # 异步预加载
        if self.enable_preload and self.preload_on_init:
            asyncio.create_task(self.preload_common_rules_async())

    def _get_cache_key(self, domain: str, task_type: str, phase: str | None = None) -> str:
        """生成缓存键"""
        return f"{domain}:{task_type}:{phase or 'any'}"

    def _get_from_cache(self, cache_key: str) -> Any | None:
        """从缓存获取数据"""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            age = (datetime.now() - timestamp).total_seconds()

            if age < self.cache_ttl:
                self.metrics["cache_hits"] += 1
                return cached_data
            else:
                del self._cache[cache_key]

        self.metrics["cache_misses"] += 1
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存"""
        if len(self._cache) >= 1024:
            self._cache.popitem(last=False)
        self._cache[cache_key] = (data, datetime.now())

    async def retrieve_rule(
        self, domain: str, task_type: str, phase: str | None = None
    ) -> ScenarioRule | None:
        """
        异步检索场景规则

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段

        Returns:
            ScenarioRule或None
        """
        start_time = datetime.now()

        try:
            # 验证参数
            domain = domain.lower().strip()
            task_type = task_type.lower().strip()
            if phase:
                phase = phase.lower().strip()

            if domain not in self.ALLOWED_DOMAINS:
                raise ValueError(f"无效的domain: {domain}")

            self.metrics["total_queries"] += 1

            # 检查缓存
            cache_key = self._get_cache_key(domain, task_type, phase)
            cached_rule = self._get_from_cache(cache_key)
            if cached_rule is not None:
                logger.info(f"✅ 从缓存返回规则: {cached_rule.rule_id}")
                return cached_rule

            # 异步查询数据库
            rule = await self._query_database(domain, task_type, phase)

            if rule:
                # 缓存结果
                self._set_cache(cache_key, rule)

                # 更新性能指标
                query_time = (datetime.now() - start_time).total_seconds() * 1000
                self.metrics["avg_query_time_ms"] = (
                    self.metrics["avg_query_time_ms"] * (self.metrics["total_queries"] - 1)
                    + query_time
                ) / self.metrics["total_queries"]

                logger.info(f"✅ 找到场景规则: {rule.rule_id}")
                return rule

            return None

        except Exception as e:
            logger.error(f"❌ 检索规则失败: {e}", exc_info=True)
            self.metrics["error_count"] += 1
            return None

    async def _query_database(
        self, domain: str, task_type: str, phase: str,
    ) -> ScenarioRule | None:
        """
        异步查询数据库

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段

        Returns:
            ScenarioRule或None
        """
        # 在线程池中执行同步数据库查询
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_query, domain, task_type, phase)

    def _sync_query(
        self, domain: str, task_type: str, phase: str,
    ) -> ScenarioRule | None:
        """
        同步查询数据库(在线程池中执行)

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段

        Returns:
            ScenarioRule或None
        """
        with self.db_manager.neo4j_session() as session:
            params = {"domain": domain, "task_type": task_type}
            if phase:
                params["phase"] = phase

            cypher = """
                MATCH (sr:ScenarioRule)
                WHERE sr.domain = $domain
                  AND sr.task_type = $task_type
                  AND sr.is_active = true
            """

            if phase:
                cypher += " AND sr.phase = $phase"

            cypher += """
                RETURN sr
                ORDER BY sr.version DESC
                LIMIT 1
            """

            result = session.run(cypher, **params)
            record = result.single()

            if not record:
                return None

            sr_node = record["sr"]

            # 解析JSON字段
            try:
                processing_rules = json.loads(sr_node.get("processing_rules", "[]"))
                workflow_steps = json.loads(sr_node.get("workflow_steps", "[]"))
                variables = json.loads(sr_node.get("variables", "{}"))
                legal_basis = json.loads(sr_node.get("legal_basis", "[]"))
                reference_cases = json.loads(sr_node.get("reference_cases", "[]"))
                expert_config = json.loads(sr_node.get("expert_config", "{}"))
                lyra_focus = json.loads(sr_node.get("lyra_focus", "[]"))
            except json.JSONDecodeError as e:
                logger.error(f"❌ 解析规则JSON失败: {e}")
                return None

            return ScenarioRule(
                rule_id=sr_node.get("rule_id", ""),
                domain=sr_node.get("domain", ""),
                task_type=sr_node.get("task_type", ""),
                phase=sr_node.get("phase", ""),
                system_prompt_template=sr_node.get("system_prompt_template", ""),
                user_prompt_template=sr_node.get("user_prompt_template", ""),
                processing_rules=processing_rules,
                workflow_steps=workflow_steps,
                variables=variables,
                legal_basis=legal_basis,
                reference_cases=reference_cases,
                expert_config=expert_config,
                agent_level=sr_node.get("agent_level", "L2"),
                lyra_optimization=sr_node.get("lyra_optimization", True),
                lyra_focus=lyra_focus,
            )

    async def batch_retrieve_rules(
        self, queries: list[tuple[str, str, str]]) -> list[ScenarioRule | None]:
        """
        批量检索规则(解决N+1查询问题)

        Args:
            queries: 查询列表,每个元素为(domain, task_type, phase)

        Returns:
            规则列表
        """
        # 并发执行所有查询
        tasks = []
            self.retrieve_rule(domain, task_type, phase) for domain, task_type, phase in queries
        ]
        return await asyncio.gather(*tasks)

    async def preload_common_rules_async(
        self, domains: set["key"] = None, force: bool = False
    ) -> dict[str, Any]:
        """
        异步预加载常用规则

        Args:
            domains: 要预加载的领域
            force: 是否强制重新加载

        Returns:
            预加载结果统计
        """
        if not self.enable_preload:
            return {"status": "disabled", "count": 0}

        # 检查是否已加载
        if not force and self._preload_status == PreloadStatus.COMPLETED:
            return {"status": "already_loaded", "count": self.metrics["preload_count"]}

        start_time = datetime.now()
        self._preload_status = PreloadStatus.IN_PROGRESS

        domains_to_load = domains or self.preload_domains
        loaded_count = 0

        # 构建批量查询
        queries = []
        for domain in domains_to_load:
            if domain not in self.ALLOWED_DOMAINS:
                continue
            for task_type in self.ALLOWED_TASK_TYPES:
                queries.append((domain, task_type, None))
                # 添加常用phase
                for phase in ["application", "examination"]:
                    queries.append((domain, task_type, phase))

        # 批量执行查询
        results = await self.batch_retrieve_rules(queries)

        # 统计结果
        for result in results:
            if result is not None:
                loaded_count += 1

        # 更新状态
        self._preload_status = PreloadStatus.COMPLETED
        self.metrics["preload_count"] = loaded_count
        self.metrics["preload_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"✅ 异步预加载完成: {loaded_count}条规则")

        return {
            "status": "completed",
            "count": loaded_count,
            "time_ms": self.metrics["preload_time_ms"],
        }

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
