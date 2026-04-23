#!/usr/bin/env python3
from __future__ import annotations

"""
场景规则检索器 - 生产优化版本
Scenario Rule Retriever - Production Optimized Version

版本: 2.1.0
优化内容:
- P0: 修复Cypher注入漏洞(使用参数化查询)
- P0: 添加输入验证
- P1: 实现缓存机制
- P1: 完善错误处理
- P1: 添加规则预加载功能 ✨
- P2: 添加性能指标
"""

import asyncio
import html
import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


def _parse_json_field(value, default):
    """
    解析JSON字段,处理列表或字符串两种情况

    Neo4j 可能返回:
    - Python list/dict (当直接存储数组时)
    - JSON string (当存储为字符串时)

    Args:
        value: 从 Neo4j 获取的值
        default: 默认JSON字符串

    Returns:
        解析后的 Python 对象
    """
    if value is None:
        return json.loads(default)
    # 如果已经是列表或字典(从Neo4j数组直接返回),直接返回
    if isinstance(value, (list, dict)):
        return value
    # 如果是字符串,尝试解析
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return json.loads(default)
    # 其他情况返回默认值
    return json.loads(default)


class ValidationError(Exception):
    """输入验证错误"""

    pass


class PreloadStatus(Enum):
    """预加载状态"""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ScenarioRule:
    """
    场景规则数据类

    包含场景的所有规则信息:提示词模板、处理规则、工作流等
    """

    rule_id: str
    domain: str
    task_type: str
    phase: str

    # 提示词模板
    system_prompt_template: str
    user_prompt_template: str

    # 处理规则和工作流
    processing_rules: list[str] = field(default_factory=list)
    workflow_steps: list[dict[str, Any] = field(default_factory=list)

    # 变量定义
    variables: dict[str, str] = field(default_factory=dict)

    # 法律依据和参考案例
    legal_basis: list[str] = field(default_factory=list)
    reference_cases: list[dict[str, str] = field(default_factory=list)

    # 专家配置
    expert_config: dict[str, Any] = field(default_factory=dict)

    # 系统配置
    agent_level: str = "L2"
    lyra_optimization: bool = True
    lyra_focus: list[str] = field(default_factory=list)

    def substitute_variables(self, variables: dict[str, Any]) -> tuple[str, str]:
        """
        替换提示词模板中的变量

        支持两种语法：
        - 传统 {var} 简单替换（向后兼容）
        - Jinja2 {{ var }} 语法（新模板协议）

        Args:
            variables: 变量值字典

        Returns:
            (system_prompt, user_prompt): 替换后的提示词
        """
        system_prompt = self.system_prompt_template
        user_prompt = self.user_prompt_template

        # 若模板包含 Jinja2 语法（{{ 或 {%），使用 Jinja2 渲染
        is_jinja2 = "{{" in system_prompt or "{%" in system_prompt

        if is_jinja2:
            from core.prompt_engine.renderer import PromptRenderer
            renderer = PromptRenderer()
            system_prompt = renderer.render(system_prompt, variables)
            user_prompt = renderer.render(user_prompt, variables)
        else:
            # 传统简单替换（向后兼容）
            for key, value in variables.items():
                placeholder = "{" + key + "}"
                # 确保值是字符串并转义(防止注入)
                str_value = html.escape(str(value)) if value is not None else ""
                system_prompt = system_prompt.replace(placeholder, str_value)
                user_prompt = user_prompt.replace(placeholder, str_value)

        return system_prompt, user_prompt

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule_id": self.rule_id,
            "domain": self.domain,
            "task_type": self.task_type,
            "phase": self.phase,
            "system_prompt_template": self.system_prompt_template,
            "user_prompt_template": self.user_prompt_template,
            "processing_rules": self.processing_rules,
            "workflow_steps": self.workflow_steps,
            "variables": self.variables,
            "legal_basis": self.legal_basis,
            "reference_cases": self.reference_cases,
            "expert_config": self.expert_config,
            "agent_level": self.agent_level,
            "lyra_optimization": self.lyra_optimization,
            "lyra_focus": self.lyra_focus,
        }


class ScenarioRuleRetrieverOptimized:
    """
    场景规则检索器 - 生产优化版本

    优化点:
    1. 修复Cypher注入漏洞(使用参数化查询)
    2. 添加输入验证和清理
    3. 实现LRU缓存机制
    4. 完善错误处理和重试逻辑
    5. 添加性能指标收集
    """

    # 允许的领域和任务类型白名单
    ALLOWED_DOMAINS = {"patent", "trademark", "legal", "copyright", "other"}
    ALLOWED_TASK_TYPES = {
        "creativity_analysis",
        "novelty_analysis",
        "infringement",
        "infringement_analysis",
        "infringement_risk",
        "similarity",
        "validity",
        "drafting",
        "search",
        "claims_layout",
        "specification_completion",
        "drawings_design",
        "quality_check",
        "novelty_response",
        "creativity_response",
        "utility_response",
        "amendment_response",
        "correction_response",
        "invalidation_analysis",
        "invalidation_defense",
        "invalidation_drafting",
        "review_petition",
        "stability_analysis",
        "fto_search",
        "design_arround",
        "valuation",
        "portfolio_management",
        "licensing_negotiation",
        "other",
    }
    ALLOWED_PHASES = {
        "application",
        "examination",
        "opposition",
        "litigation",
        "invalidation",
        "review",
        "freedom_to_operate",
        "assessment",
        "management",
        "licensing",
        "any",
        "other"
    }

    def __init__(
        self,
        db_manager,
        cache_ttl: int = 3600,
        enable_metrics: bool = True,
        enable_preload: bool = True,
        preload_on_init: bool = True,
        preload_domains: set[str] | None = None,
    ):
        """
        初始化规则检索器

        Args:
            db_manager: 数据库管理器实例
            cache_ttl: 缓存生存时间(秒)
            enable_metrics: 是否启用性能指标收集
            enable_preload: 是否启用预加载功能
            preload_on_init: 是否在初始化时预加载
            preload_domains: 预加载的领域集合(None表示全部)
        """
        self.db_manager = db_manager
        self.cache_ttl = cache_ttl
        self.enable_metrics = enable_metrics
        self.enable_preload = enable_preload
        self.preload_on_init = preload_on_init
        self.preload_domains = preload_domains or self.ALLOWED_DOMAINS

        # 缓存存储(带时间戳)
        self._cache: OrderedDict[str, tuple[Any, datetime] = OrderedDict()

        # 预加载状态追踪
        self._preload_status = PreloadStatus.NOT_STARTED
        self._preload_progress: dict[str, int] = {}
        self._preload_errors: list[str] = []

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

        logger.info("✅ 场景规则检索器初始化完成(v2.1.0)")

        # 自动预加载
        if self.enable_preload and self.preload_on_init:
            self.preload_common_rules()

    def _validate_domain(self, domain: str) -> str:
        """
        验证领域参数

        Args:
            domain: 领域字符串

        Returns:
            验证后的领域

        Raises:
            ValidationError: 验证失败
        """
        if not domain or not isinstance(domain, str):
            raise ValidationError("domain必须是非空字符串")

        domain = domain.strip().lower()

        if domain not in self.ALLOWED_DOMAINS:
            raise ValidationError(f"无效的domain: {domain},允许的值: {self.ALLOWED_DOMAINS}")

        return domain

    def _validate_task_type(self, task_type: str) -> str:
        """
        验证任务类型参数

        Args:
            task_type: 任务类型字符串

        Returns:
            验证后的任务类型

        Raises:
            ValidationError: 验证失败
        """
        if not task_type or not isinstance(task_type, str):
            raise ValidationError("task_type必须是非空字符串")

        task_type = task_type.strip().lower()

        if task_type not in self.ALLOWED_TASK_TYPES:
            raise ValidationError(
                f"无效的task_type: {task_type},允许的值: {self.ALLOWED_TASK_TYPES}"
            )

        return task_type

    def _validate_phase(self, phase: str,) -> str | None:
        """
        验证阶段参数

        Args:
            phase: 阶段字符串

        Returns:
            验证后的阶段(如果phase为None则返回None)

        Raises:
            ValidationError: 验证失败
        """
        if phase is None:
            return None

        if not isinstance(phase, str):
            raise ValidationError("phase必须是字符串或None")

        phase = phase.strip().lower()

        if phase and phase not in self.ALLOWED_PHASES:
            raise ValidationError(f"无效的phase: {phase},允许的值: {self.ALLOWED_PHASES}")

        return phase

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
                # 缓存过期,删除
                del self._cache[cache_key]

        self.metrics["cache_misses"] += 1
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存"""
        # 限制缓存大小
        if len(self._cache) >= 1024:
            # 删除最旧的条目
            self._cache.popitem(last=False)

        self._cache[cache_key] = (data, datetime.now())

    def retrieve_rule(
        self, domain: str, task_type: str, phase: str | None = None
    ) -> ScenarioRule | None:
        """
        从Neo4j检索场景规则(优化版本)

        Args:
            domain: 领域 (patent/trademark/legal)
            task_type: 任务类型 (creativity_analysis/novelty_analysis/etc.)
            phase: 阶段 (application/examination/litigation),可选

        Returns:
            ScenarioRule: 场景规则对象,如果未找到则返回None

        Raises:
            ValidationError: 参数验证失败
        """
        start_time = datetime.now()

        try:
            # 验证输入参数
            domain = self._validate_domain(domain)
            task_type = self._validate_task_type(task_type)
            phase = self._validate_phase(phase)

            self.metrics["total_queries"] += 1

            logger.info(f"🔍 检索场景规则: {domain}/{task_type}/{phase or 'any'}")

            # 检查缓存
            cache_key = self._get_cache_key(domain, task_type, phase)
            cached_rule = self._get_from_cache(cache_key)
            if cached_rule is not None:
                logger.info(f"✅ 从缓存返回规则: {cached_rule.rule_id}")
                return cached_rule

            # 从数据库查询
            with self.db_manager.session() as session:
                # 构建安全的参数化查询(防止Cypher注入)
                params = {"domain": domain, "task_type": task_type}

                if phase:
                    params["phase"] = phase

                # 使用参数化查询,防止注入
                cypher = """
                    MATCH (sr:ScenarioRule)
                    WHERE sr.domain = $domain
                      AND sr.task_type = $task_type
                      AND sr.is_active = true
                """

                # 动态添加phase条件(仍然使用参数化)
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
                    logger.warning(f"⚠️ 未找到场景规则: {domain}/{task_type}/{phase or 'any'}")
                    return None

                sr_node = record["sr"]

                # 解析JSON字段 - 处理 Neo4j 可能返回列表或字符串的情况
                try:
                    processing_rules = _parse_json_field(sr_node.get("processing_rules"), "[]")
                    workflow_steps = _parse_json_field(sr_node.get("workflow_steps"), "[]")
                    variables = _parse_json_field(sr_node.get("variables"), "{}")
                    legal_basis = _parse_json_field(sr_node.get("legal_basis"), "[]")
                    reference_cases = _parse_json_field(sr_node.get("reference_cases"), "[]")
                    expert_config = _parse_json_field(sr_node.get("expert_config"), "{}")
                    lyra_focus = _parse_json_field(sr_node.get("lyra_focus"), "[]")
                except Exception as e:
                    logger.error(f"❌ 解析规则JSON失败: {e}")
                    self.metrics["error_count"] += 1
                    return None

                rule = ScenarioRule(
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

                # 缓存结果
                self._set_cache(cache_key, rule)

                # 更新性能指标
                if self.enable_metrics:
                    query_time = (datetime.now() - start_time).total_seconds() * 1000
                    self.metrics["avg_query_time_ms"] = (
                        self.metrics["avg_query_time_ms"] * (self.metrics["total_queries"] - 1)
                        + query_time
                    ) / self.metrics["total_queries"]

                logger.info(f"✅ 找到场景规则: {rule.rule_id}")

                return rule

        except ValidationError as e:
            logger.error(f"❌ 参数验证失败: {e}")
            self.metrics["error_count"] += 1
            raise
        except Exception as e:
            logger.error(f"❌ 检索规则失败: {e}", exc_info=True)
            self.metrics["error_count"] += 1
            return None

    def retrieve_all_rules_for_domain(self, domain: str) -> list[ScenarioRule]:
        """
        检索指定领域的所有规则(优化版本)

        Args:
            domain: 领域

        Returns:
            list[ScenarioRule]: 规则列表
        """
        try:
            # 验证domain
            domain = self._validate_domain(domain)

            logger.info(f"🔍 检索领域所有规则: {domain}")

            with self.db_manager.session() as session:
                # 参数化查询
                cypher = """
                    MATCH (sr:ScenarioRule)
                    WHERE sr.domain = $domain
                      AND sr.is_active = true
                    RETURN sr
                    ORDER BY sr.task_type, sr.phase, sr.version DESC
                """

                result = session.run(cypher, domain=domain)

                rules = []
                for record in result:
                    sr_node = record["sr"]

                    try:
                        rule = ScenarioRule(
                            rule_id=sr_node.get("rule_id", ""),
                            domain=sr_node.get("domain", ""),
                            task_type=sr_node.get("task_type", ""),
                            phase=sr_node.get("phase", ""),
                            system_prompt_template=sr_node.get("system_prompt_template", ""),
                            user_prompt_template=sr_node.get("user_prompt_template", ""),
                            processing_rules=_parse_json_field(sr_node.get("processing_rules"), "[]"),
                            workflow_steps=_parse_json_field(sr_node.get("workflow_steps"), "[]"),
                            variables=_parse_json_field(sr_node.get("variables"), "{}"),
                            legal_basis=_parse_json_field(sr_node.get("legal_basis"), "[]"),
                            reference_cases=_parse_json_field(sr_node.get("reference_cases"), "[]"),
                            expert_config=_parse_json_field(sr_node.get("expert_config"), "{}"),
                            agent_level=sr_node.get("agent_level", "L2"),
                            lyra_optimization=sr_node.get("lyra_optimization", True),
                            lyra_focus=_parse_json_field(sr_node.get("lyra_focus"), "[]"),
                        )

                        rules.append(rule)
                    except Exception as e:
                        logger.error(f"❌ 解析规则JSON失败: {e}")
                        self.metrics["error_count"] += 1
                        continue

                logger.info(f"✅ 找到 {len(rules)} 条规则")

                return rules

        except ValidationError as e:
            logger.error(f"❌ 参数验证失败: {e}")
            self.metrics["error_count"] += 1
            raise
        except Exception as e:
            logger.error(f"❌ 检索规则失败: {e}", exc_info=True)
            self.metrics["error_count"] += 1
            return []

    def retrieve_legal_basis_for_rule(self, rule_id: str) -> list[dict[str, Any]:
        """
        检索规则关联的法律依据(优化版本)

        Args:
            rule_id: 规则ID

        Returns:
            list[Dict]: 法律依据列表
        """
        try:
            # 验证rule_id
            if not rule_id or not isinstance(rule_id, str):
                raise ValidationError("rule_id必须是非空字符串")

            # 限制长度
            if len(rule_id) > 100:
                raise ValidationError("rule_id长度超过限制")

            logger.info(f"🔍 检索法律依据: {rule_id}")

            with self.db_manager.session() as session:
                # 参数化查询
                cypher = """
                    MATCH (sr:ScenarioRule {rule_id: $rule_id})-[:HAS_LEGAL_BASIS]->(law)
                    RETURN law.title AS title,
                           law.content AS content,
                           labels(law)[0] AS law_type,
                           law.node_id AS law_id
                    ORDER BY law_type, title
                """

                result = session.run(cypher, rule_id=rule_id)

                legal_basis = []
                for record in result:
                    content = record.get("content", "")
                    # 限制长度并转义
                    if len(content) > 500:
                        content = content[:500]

                    legal_basis.append(
                        {
                            "title": html.escape(record["title"] or ""),
                            "content": html.escape(content),
                            "law_type": record["law_type"],
                            "law_id": record.get("law_id", ""),
                        }
                    )

                logger.info(f"✅ 找到 {len(legal_basis)} 条法律依据")

                return legal_basis

        except ValidationError as e:
            logger.error(f"❌ 参数验证失败: {e}")
            self.metrics["error_count"] += 1
            raise
        except Exception as e:
            logger.error(f"❌ 检索法律依据失败: {e}", exc_info=True)
            self.metrics["error_count"] += 1
            return []

    def retrieve_reference_cases_for_rule(self, rule_id: str) -> list[dict[str, Any]:
        """
        检索规则关联的参考案例(优化版本)

        Args:
            rule_id: 规则ID

        Returns:
            list[Dict]: 参考案例列表
        """
        try:
            # 验证rule_id
            if not rule_id or not isinstance(rule_id, str):
                raise ValidationError("rule_id必须是非空字符串")

            if len(rule_id) > 100:
                raise ValidationError("rule_id长度超过限制")

            logger.info(f"🔍 检索参考案例: {rule_id}")

            with self.db_manager.session() as session:
                # 参数化查询
                cypher = """
                    MATCH (sr:ScenarioRule {rule_id: $rule_id})-[:HAS_REFERENCE_CASE]->(case)
                    RETURN case.case_number AS case_number,
                           case.title AS title,
                           case.court_name AS court,
                           substring(case.judgment_result, 0, 500) AS result
                    LIMIT 10
                """

                result = session.run(cypher, rule_id=rule_id)

                cases = []
                for record in result:
                    cases.append(
                        {
                            "case_number": html.escape(record["case_number"] or ""),
                            "title": html.escape(record["title"] or ""),
                            "court": html.escape(record.get("court", "")),
                            "result": html.escape(record.get("result", "")),
                        }
                    )

                logger.info(f"✅ 找到 {len(cases)} 个参考案例")

                return cases

        except ValidationError as e:
            logger.error(f"❌ 参数验证失败: {e}")
            self.metrics["error_count"] += 1
            raise
        except Exception as e:
            logger.error(f"❌ 检索参考案例失败: {e}", exc_info=True)
            self.metrics["error_count"] += 1
            return []

    def retrieve_rule_with_relations(
        self, domain: str, task_type: str, phase: str | None = None
    ) -> ScenarioRule | None:
        """
        检索规则及其关联的法律依据和参考案例(优化版本)

        Args:
            domain: 领域
            task_type: 任务类型
            phase: 阶段

        Returns:
            ScenarioRule: 包含法律依据和参考案例的规则对象
        """
        # 1. 检索规则
        rule = self.retrieve_rule(domain, task_type, phase)
        if not rule:
            return None

        # 2. 检索法律依据
        legal_basis = self.retrieve_legal_basis_for_rule(rule.rule_id)
        rule.legal_basis = legal_basis

        # 3. 检索参考案例
        reference_cases = self.retrieve_reference_cases_for_rule(rule.rule_id)
        rule.reference_cases = reference_cases

        return rule

    def preload_common_rules(
        self, domains: set[str] = None, force: bool = False
    ) -> dict[str, Any]:
        """
        预加载常用规则到缓存

        Args:
            domains: 要预加载的领域(None使用初始化时的配置)
            force: 是否强制重新加载(即使已加载)

        Returns:
            预加载结果统计
        """
        if not self.enable_preload:
            logger.info("⚠️ 预加载功能未启用")
            return {"status": "disabled", "count": 0}

        # 检查是否已加载
        if not force and self._preload_status == PreloadStatus.COMPLETED:
            logger.info("✅ 规则已预加载,跳过")
            return {
                "status": "already_loaded",
                "count": self.metrics["preload_count"],
                "cached": len(self._cache),
            }

        start_time = datetime.now()
        self._preload_status = PreloadStatus.IN_PROGRESS
        self._preload_errors.clear()

        domains_to_load = domains or self.preload_domains
        loaded_count = 0
        error_count = 0

        logger.info(f"🔄 开始预加载规则,领域: {domains_to_load}")

        try:
            # 遍历所有领域和任务类型的组合
            for domain in domains_to_load:
                if domain not in self.ALLOWED_DOMAINS:
                    logger.warning(f"⚠️ 跳过无效领域: {domain}")
                    continue

                domain_count = 0
                for task_type in self.ALLOWED_TASK_TYPES:
                    try:
                        # 尝试加载规则(不指定phase)
                        rule = self.retrieve_rule(domain, task_type, None)
                        if rule:
                            loaded_count += 1
                            domain_count += 1

                            # 同时加载常用phase的规则
                            for phase in ["application", "examination", "other"]:
                                try:
                                    rule_with_phase = self.retrieve_rule(domain, task_type, phase)
                                    if rule_with_phase:
                                        loaded_count += 1
                                        domain_count += 1
                                except Exception:
                                    # phase可选,加载失败不记为错误
                                    pass

                    except Exception as e:
                        error_msg = f"{domain}/{task_type}: {e!s}"
                        self._preload_errors.append(error_msg)
                        error_count += 1
                        logger.debug(f"⚠️ 预加载失败: {error_msg}")

                self._preload_progress[domain] = domain_count
                logger.info(f"  ✅ {domain}: 已加载 {domain_count} 条规则")

            # 更新状态和指标
            self._preload_status = (
                PreloadStatus.COMPLETED if error_count == 0 else PreloadStatus.PARTIAL
            )
            preload_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["preload_count"] = loaded_count
            self.metrics["preload_time_ms"] = preload_time

            result = {
                "status": self._preload_status.value,
                "count": loaded_count,
                "errors": error_count,
                "cached": len(self._cache),
                "time_ms": round(preload_time, 2),
                "progress": self._preload_progress.copy(),
            }

            if error_count > 0:
                result["error_details"] = self._preload_errors[:10]  # 最多返回10个错误

            logger.info(
                f"✅ 预加载完成: {loaded_count}条规则, {error_count}个错误, {preload_time:.0f}ms"
            )

            return result

        except Exception as e:
            self._preload_status = PreloadStatus.FAILED
            logger.error(f"❌ 预加载失败: {e}", exc_info=True)
            return {"status": "failed", "error": str(e), "count": loaded_count}

    async def preload_common_rules_async(
        self, domains: set[str] = None, force: bool = False
    ) -> dict[str, Any]:
        """
        异步预加载常用规则

        Args:
            domains: 要预加载的领域
            force: 是否强制重新加载

        Returns:
            预加载结果统计
        """
        # 在线程池中执行同步预加载
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.preload_common_rules(domains, force))

    def get_preload_status(self) -> dict[str, Any]:
        """
        获取预加载状态

        Returns:
            状态信息字典
        """
        return {
            "status": self._preload_status.value,
            "progress": self._preload_progress.copy(),
            "cached_rules": len(self._cache),
            "errors": self._preload_errors.copy(),
            "metrics": {
                "preload_count": self.metrics["preload_count"],
                "preload_time_ms": self.metrics["preload_time_ms"],
            },
        }

    def is_preloaded(self) -> bool:
        """检查是否已完成预加载"""
        return self._preload_status == PreloadStatus.COMPLETED

    def get_metrics(self) -> dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("🗑️ 缓存已清除")


# 便捷函数
def retrieve_scenario_rule(
    db_manager: Any | None = None, domain: str | None = None, task_type: str | None = None, phase: str | None = None
) -> ScenarioRule | None:
    """
    便捷函数:检索场景规则(优化版本)

    Args:
        db_manager: 数据库管理器
        domain: 领域
        task_type: 任务类型
        phase: 阶段

    Returns:
        ScenarioRule: 规则对象或None
    """
    retriever = ScenarioRuleRetrieverOptimized(db_manager)
    return retriever.retrieve_rule_with_relations(domain, task_type, phase)
