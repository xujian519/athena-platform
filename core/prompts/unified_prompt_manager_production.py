#!/usr/bin/env python3
from __future__ import annotations
"""
生产就绪的统一提示词管理器
Production-Ready Unified Prompt Manager

修复了关键问题,添加了错误处理、缓存、监控等生产功能
"""

import functools
import logging
import time
from collections import defaultdict
from typing import Any

from core.legal_world_model.scenario_identifier_optimized import (
    ScenarioContext,
)
from core.legal_world_model.scenario_identifier_optimized import (
    ScenarioIdentifierOptimized as ScenarioIdentifier,
)
from core.legal_world_model.scenario_rule_retriever_optimized import (
    ScenarioRule,
)
from core.legal_world_model.scenario_rule_retriever_optimized import (
    ScenarioRuleRetrieverOptimized as ScenarioRuleRetriever,
)
from core.prompts.integrated_prompt_generator import IntegratedPromptGenerator
from core.prompts.unified_prompt_manager import UnifiedPromptManager

logger = logging.getLogger(__name__)


class SimpleNeo4jManager:
    """简单的Neo4j管理器,用于提示词管理器"""

    def __init__(self):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "athena_neo4j_2024")
        )

    def neo4j_session(self):
        """返回Neo4j会话上下文管理器"""
        return self.driver.session()

    def session(self):
        """返回Neo4j会话上下文管理器（兼容方法）"""
        return self.driver.session()

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()


# 生产配置
PRODUCTION_CONFIG = {
    "max_input_length": 10000,  # 最大输入长度
    "cache_ttl": 3600,  # 缓存过期时间(秒)
    "max_retries": 3,  # 最大重试次数
    "retry_delay": 0.1,  # 重试延迟(秒)
    "enable_metrics": True,  # 启用指标收集
    "enable_cache": True,  # 启用缓存
}


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.errors = defaultdict(int)

    def increment(self, metric: str, value: int = 1):
        """增加计数器"""
        self.counters[metric] += value

    def record_time(self, metric: str, duration: float):
        """记录时间"""
        self.timers[metric].append(duration)

    def record_error(self, metric: str):
        """记录错误"""
        self.errors[metric] += 1

    def get_stats(self, metric: str) -> dict[str, Any]:
        """获取统计信息"""
        stats = {"count": self.counters[metric], "errors": self.errors[metric], "error_rate": 0}

        if self.timers.get(metric):
            durations = self.timers[metric]
            stats["avg_time"] = sum(durations) / len(durations)
            stats["min_time"] = min(durations)
            stats["max_time"] = max(durations)
            stats["total_time"] = sum(durations)

        if stats["count"] > 0:
            stats["error_rate"] = stats["errors"] / stats["count"]

        return stats


class CacheManager:
    """缓存管理器"""

    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.timestamps = {}
        self.ttl = ttl

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        if key in self.cache:
            # 检查是否过期
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                # 过期,删除
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()

    def cleanup_expired(self):
        """清理过期缓存"""
        now = time.time()
        expired_keys = [k for k, t in self.timestamps.items() if now - t >= self.ttl]
        for key in expired_keys:
            del self.cache[key]
            del self.timestamps[key]


def validate_input(user_input: str, max_length: int = PRODUCTION_CONFIG["max_input_length"]):
    """验证输入"""
    if not user_input:
        raise ValueError("输入不能为空")

    if len(user_input) > max_length:
        raise ValueError(f"输入长度超过限制({max_length}字符)")

    # 基本的XSS防护
    if "<script>" in user_input.lower():
        logger.warning("检测到可能的XSS攻击")
        raise ValueError("输入包含非法内容")


def retry_on_failure(
    max_retries: int = PRODUCTION_CONFIG["max_retries"],
    delay: float = PRODUCTION_CONFIG["retry_delay"],
):
    """重试装饰器"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} 失败,重试 {attempt + 1}/{max_retries}: {e}"
                        )
                        time.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        logger.error(f"{func.__name__} 失败,已达最大重试次数")
            raise last_exception

        return wrapper

    return decorator


class ProductionUnifiedPromptManager(UnifiedPromptManager):
    """
    生产就绪的统一提示词管理器

    添加了:
    - 输入验证
    - 错误处理和重试
    - 缓存
    - 性能监控
    - 限流
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 初始化数据库管理器
        if not hasattr(self, 'db_manager') or self.db_manager is None:
            self.db_manager = SimpleNeo4jManager()

        # 初始化组件
        self.scenario_identifier = ScenarioIdentifier()
        self.scenario_rule_retriever = ScenarioRuleRetriever(self.db_manager)

        # 初始化生成器
        self.integrated_prompt_generator = IntegratedPromptGenerator(
            unified_prompt_manager=self,
            expert_prompt_generator=getattr(self, "expert_generator", None),
        )

        # 初始化缓存
        self.cache = (
            CacheManager(ttl=PRODUCTION_CONFIG["cache_ttl"])
            if PRODUCTION_CONFIG["enable_cache"]
            else None
        )

        # 初始化指标收集
        self.metrics = PerformanceMetrics() if PRODUCTION_CONFIG["enable_metrics"] else None

        # 初始化限流
        self.request_timestamps = []
        self.rate_limit = 100  # 每秒100个请求

        logger.info("✅ 生产就绪提示词管理器初始化完成")

    def _check_rate_limit(self):
        """检查限流"""
        now = time.time()
        # 移除1秒前的时间戳
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 1.0]

        if len(self.request_timestamps) >= self.rate_limit:
            logger.warning(f"超过限流阈值: {len(self.request_timestamps)}/秒")
            raise Exception("请求过于频繁,请稍后重试")

        self.request_timestamps.append(now)

    def _record_metrics(self, metric: str, duration: float, success: bool = True):
        """记录指标"""
        if self.metrics:
            self.metrics.increment(metric)
            self.metrics.record_time(metric, duration)
            if not success:
                self.metrics.record_error(metric)

    def get_metrics_summary(self) -> dict[str, Any]:
        """获取指标摘要"""
        if not self.metrics:
            return {}

        return {
            "scenario_identification": self.metrics.get_stats("scenario_identification"),
            "rule_retrieval": self.metrics.get_stats("rule_retrieval"),
            "prompt_generation": self.metrics.get_stats("prompt_generation"),
            "total_requests": self.metrics.counters["total_requests"],
            "total_errors": sum(self.metrics.errors.values()),
        }

    @retry_on_failure()
    def identify_scenario_with_validation(self, user_input: str) -> ScenarioContext:
        """带验证的场景识别"""
        # 输入验证
        validate_input(user_input)

        # 检查缓存
        if self.cache:
            cache_key = f"scenario:{hash(user_input)}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("使用缓存的场景识别结果")
                return cached

        # 识别场景
        start = time.time()
        try:
            context = self.scenario_identifier.identify_scenario(user_input)
            duration = time.time() - start

            # 记录指标
            self._record_metrics("scenario_identification", duration, True)

            # 缓存结果
            if self.cache:
                self.cache.set(cache_key, context)

            return context

        except Exception:
            duration = time.time() - start
            self._record_metrics("scenario_identification", duration, False)
            raise

    @retry_on_failure()
    def retrieve_rule_with_validation(
        self, domain: str, task_type: str, phase: Optional[str] = None
    ) -> ScenarioRule | None:
        """带验证的规则检索"""
        # 参数验证
        if not domain or not task_type:
            raise ValueError("domain和task_type不能为空")

        # 检查缓存
        if self.cache:
            cache_key = f"rule:{domain}:{task_type}:{phase or 'any'}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug("使用缓存的规则")
                return cached

        # 检索规则
        start = time.time()
        try:
            rule = self.scenario_rule_retriever.retrieve_rule_with_relations(
                domain, task_type, phase
            )
            duration = time.time() - start

            # 记录指标
            self._record_metrics("rule_retrieval", duration, True)

            # 缓存结果
            if self.cache and rule:
                self.cache.set(cache_key, rule)

            return rule

        except Exception:
            duration = time.time() - start
            self._record_metrics("rule_retrieval", duration, False)
            raise

    def generate_scenario_based_prompt(
        self,
        user_input: str,
        scenario_context: ScenarioContext | None = None,
        additional_context: Optional[dict[str, Any]] = None,
        enable_l1_l4: bool = True,
        enable_expert: bool = True,
        enable_lyra: bool = True,
    ) -> dict[str, Any]:
        """
        生成场景感知提示词(生产就绪版本)

        添加了输入验证、错误处理、缓存、监控
        """
        start = time.time()
        self.metrics.increment("total_requests") if self.metrics else None

        try:
            # 限流检查
            self._check_rate_limit()

            # 输入验证
            validate_input(user_input)

            logger.info(f"🎯 生成场景感知提示词: {user_input[:100]}...")

            # 1. 场景识别(带验证和缓存)
            if not scenario_context:
                scenario_context = self.identify_scenario_with_validation(user_input)

            logger.info(
                f"  场景: {scenario_context.domain.value}/"
                f"{scenario_context.task_type.value}/"
                f"{scenario_context.phase.value}"
            )

            # 2. 规则检索(带验证和缓存)
            scenario_rule = self.retrieve_rule_with_validation(
                domain=scenario_context.domain.value,
                task_type=scenario_context.task_type.value,
                phase=(
                    scenario_context.phase.value
                    if scenario_context.phase.value != "other"
                    else None
                ),
            )

            if not scenario_rule:
                logger.warning("⚠️ 未找到场景规则,使用默认提示词")
                return self._generate_default_prompt(user_input, scenario_context)

            logger.info(f"  规则: {scenario_rule.rule_id}")

            # 3. 生成集成提示词
            integrated_prompt = self.integrated_prompt_generator.generate(
                scenario_context=scenario_context,
                scenario_rule=scenario_rule,
                user_input=user_input,
            )

            # 4. 构建结果
            result = {
                "system_prompt": integrated_prompt.system_prompt,
                "user_prompt": integrated_prompt.user_prompt,
                "scenario": {
                    "domain": integrated_prompt.scenario_domain,
                    "task_type": integrated_prompt.scenario_task_type,
                    "rule_id": integrated_prompt.scenario_rule_id,
                    "confidence": integrated_prompt.confidence,
                },
                "config": {
                    "agent_level": integrated_prompt.agent_level,
                    "expert_config": integrated_prompt.expert_config,
                    "processing_rules": integrated_prompt.processing_rules,
                    "workflow_steps": integrated_prompt.workflow_steps,
                },
                "legal_context": {
                    "legal_basis": integrated_prompt.legal_basis,
                    "reference_cases": integrated_prompt.reference_cases,
                },
                "optimization": {
                    "lyra_optimized": integrated_prompt.lyra_optimized,
                    "lyra_focus": integrated_prompt.lyra_focus,
                },
                "metadata": integrated_prompt.metadata,
                "ready_for_llm": True,
            }

            # 记录指标
            duration = time.time() - start
            self._record_metrics("prompt_generation", duration, True)

            logger.info(f"✅ 场景感知提示词生成完成 ({duration*1000:.2f}ms)")

            return result

        except ValueError as e:
            # 输入验证错误
            logger.error(f"❌ 输入验证失败: {e}")
            duration = time.time() - start
            self._record_metrics("prompt_generation", duration, False)
            raise

        except Exception as e:
            # 其他错误
            logger.error(f"❌ 提示词生成失败: {e}")
            duration = time.time() - start
            self._record_metrics("prompt_generation", duration, False)

            # 返回降级结果
            return self._generate_fallback_prompt(user_input, str(e))

    def _generate_default_prompt(
        self, user_input: str, scenario_context: ScenarioContext
    ) -> dict[str, Any]:
        """生成默认提示词(当未找到场景规则时)"""
        from core.prompts.unified_prompt_manager import PromptFormat

        default_system = self.load_prompt("xiaona", PromptFormat.MARKDOWN)

        return {
            "system_prompt": default_system,
            "user_prompt": user_input,
            "scenario": {
                "domain": scenario_context.domain.value,
                "task_type": scenario_context.task_type.value,
                "rule_id": "default",
                "confidence": scenario_context.confidence,
            },
            "config": {
                "agent_level": "L2",
                "expert_config": {},
                "processing_rules": [],
                "workflow_steps": [],
            },
            "legal_context": {"legal_basis": [], "reference_cases": []},
            "optimization": {"lyra_optimized": False, "lyra_focus": []},
            "metadata": {
                "generation_method": "default",
                "fallback_reason": "no_scenario_rule_found",
            },
            "ready_for_llm": True,
        }

    def _generate_fallback_prompt(self, user_input: str, error_message: str) -> dict[str, Any]:
        """生成降级提示词(当发生错误时)"""
        logger.warning(f"使用降级提示词: {error_message}")

        return {
            "system_prompt": "你是一个专业的AI助手,请尽力帮助用户解决问题。",
            "user_prompt": user_input,
            "scenario": {
                "domain": "unknown",
                "task_type": "unknown",
                "rule_id": "fallback",
                "confidence": 0.0,
            },
            "config": {
                "agent_level": "L1",
                "expert_config": {},
                "processing_rules": [],
                "workflow_steps": [],
            },
            "legal_context": {"legal_basis": [], "reference_cases": []},
            "optimization": {"lyra_optimized": False, "lyra_focus": []},
            "metadata": {"generation_method": "fallback", "error": error_message},
            "ready_for_llm": True,
            "fallback": True,
        }

    def cleanup(self):
        """清理资源"""
        if self.cache:
            self.cache.cleanup_expired()
        logger.info("✅ 资源清理完成")


# 便捷函数
def create_production_prompt_manager(*args, **kwargs) -> ProductionUnifiedPromptManager:
    """
    创建生产就绪的提示词管理器

    Args:
        *args: 传递给UnifiedPromptManager的参数
        **kwargs: 传递给UnifiedPromptManager的关键字参数

    Returns:
        ProductionUnifiedPromptManager: 生产就绪的提示词管理器实例
    """
    return ProductionUnifiedPromptManager(*args, **kwargs)
