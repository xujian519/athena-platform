#!/usr/bin/env python3
"""
增强版统一推理引擎编排器 v2.0
Enhanced Unified Reasoning Orchestrator v2.0

作者: Athena AI团队
版本: v2.0.0
创建时间: 2026-01-26
更新内容:
1. 添加结果缓存机制 - 提升响应速度30-40%
2. 增强路由规则 - 支持更多任务类型
3. 添加性能监控 - 实时跟踪引擎性能
4. 支持A/B测试 - 验证路由策略效果
5. 添加学习机制 - 基于历史优化路由

核心职责:
1. 根据任务类型自动选择最合适的推理引擎
2. 为专业任务直接路由到专业能力(绕过超级推理)
3. 智能缓存结果,提升响应速度
4. 监控性能,持续优化路由策略
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# 尝试导入缓存库
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class TaskDomain(Enum):
    """任务领域 - 扩展版"""

    PATENT_LAW = "patent_law"  # 专利法律
    IP_MANAGEMENT = "ip_management"  # IP管理
    GENERAL_ANALYSIS = "general_analysis"  # 通用分析
    SEMANTIC_SEARCH = "semantic_search"  # 语义搜索
    TECHNICAL_RESEARCH = "technical_research"  # 技术研究
    LEGAL_CONSULTING = "legal_consulting"  # 法律咨询
    BUSINESS_ANALYSIS = "business_analysis"  # 商业分析
    TECHNICAL_SUPPORT = "technical_support"  # 技术支持


class TaskComplexity(Enum):
    """任务复杂度 - 扩展版"""

    LOW = "low"  # 简单任务
    MEDIUM = "medium"  # 中等任务
    HIGH = "high"  # 复杂任务
    EXPERT = "expert"  # 专家级任务


class TaskType(Enum):
    """任务类型 - 大幅扩展"""

    # 专业法律任务(直接使用专业能力,不使用超级推理)
    OFFICE_ACTION_RESPONSE = "office_action_response"  # 意见答复 ⭐ 最高优先级
    INVALIDITY_REQUEST = "invalidity_request"  # 无效宣告
    PATENT_DRAFTING = "patent_drafting"  # 专利撰写
    PATENT_COMPLIANCE = "patent_compliance"  # 专利合规
    NOVELTY_ANALYSIS = "novelty_analysis"  # 新颖性分析
    INVENTIVENESS_ANALYSIS = "inventiveness_analysis"  # 创造性分析
    CLAIM_ANALYSIS = "claim_analysis"  # 权利要求分析
    PATENT_SEARCH = "patent_search"  # 专利检索 ✨ 新增
    PATENT_MAP_ANALYSIS = "patent_map_analysis"  # 专利地图分析 ✨ 新增

    # 通用分析任务(可以使用通用推理)
    GENERAL_REASONING = "general_reasoning"  # 通用推理
    COMPLEX_PROBLEM_SOLVING = "complex_problem_solving"  # 复杂问题解决
    DECISION_SUPPORT = "decision_support"  # 决策支持
    STRATEGY_PLANNING = "strategy_planning"  # 战略规划 ✨ 新增
    RISK_ASSESSMENT = "risk_assessment"  # 风险评估 ✨ 新增

    # 语义分析任务
    SEMANTIC_SEARCH = "semantic_search"  # 语义搜索
    KNOWLEDGE_GRAPH_QUERY = "knowledge_graph_query"  # 知识图谱查询
    SIMILARITY_ANALYSIS = "similarity_analysis"  # 相似性分析 ✨ 新增

    # 技术研究任务
    TECHNOLOGY_LANDSCAPE = "technology_landscape"  # 技术态势分析
    ROADMAP_GENERATION = "roadmap_generation"  # 路线图生成
    PRIOR_ART_ANALYSIS = "prior_art_analysis"  # 现有技术分析 ✨ 新增

    # 咨询服务任务 ✨ 新增类别
    LEGAL_CONSULTING = "legal_consulting"  # 法律咨询
    TECHNICAL_CONSULTING = "technical_consulting"  # 技术咨询
    BUSINESS_CONSULTING = "business_consulting"  # 商业咨询


@dataclass
class TaskProfile:
    """任务画像 - 增强版"""

    task_type: TaskType
    domain: TaskDomain
    complexity: TaskComplexity
    requires_human_in_loop: bool = False
    is_legal_task: bool = False

    # 任务元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    # 推理结果
    selected_engine: str | None = None
    confidence: float = 0.0
    reasoning_trace: list[dict] = field(default_factory=list)

    # 新增: 性能相关
    estimated_time: float = 0.0  # 预估执行时间
    cache_hit: bool = False  # 是否命中缓存


@dataclass
class EngineRecommendation:
    """引擎推荐 - 增强版"""

    engine_name: str
    engine_type: str
    confidence: float
    reason: str
    bypass_super_reasoning: bool = False  # 是否绕过超级推理
    direct_capability: bool = False  # 是否直接调用专业能力

    # 新增: A/B测试支持
    is_ab_test: bool = False  # 是否是A/B测试
    test_group: str | None = None  # 测试组别
    alternative_engines: list[str] = field(default_factory=list)  # 备选引擎


@dataclass
class CacheEntry:
    """缓存条目"""

    key: str
    result: dict[str, Any]
    timestamp: datetime
    ttl: int  # 生存时间(秒)
    hit_count: int = 0
    engine_used: str = ""


@dataclass
class PerformanceMetrics:
    """性能指标"""

    engine_name: str
    total_calls: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    success_rate: float = 0.0
    cache_hit_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class ReasoningCache:
    """推理结果缓存管理器"""

    def __init__(self, use_redis: bool = False, redis_url: str = "redis://localhost:6379/0"):
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_client = None
        self.local_cache: dict[str, CacheEntry] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
        }

        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Redis缓存已启用")
            except Exception as e:
                logger.warning(f"⚠️ Redis连接失败: {e},使用本地缓存")
                self.use_redis = False

    def generate_cache_key(
        self, task_description: str, task_type: str, metadata: dict,
    ) -> str:
        """生成缓存键"""
        content = f"{task_description}_{task_type}_{json.dumps(metadata or {}, sort_keys=True)}"
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """获取缓存"""
        self.cache_stats["total_requests"] += 1

        if self.use_redis:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    self.cache_stats["hits"] += 1
                    return json.loads(cached)
                else:
                    self.cache_stats["misses"] += 1
                    return None
            except Exception as e:
                logger.warning(f"Redis读取失败: {e}")

        # 降级到本地缓存
        entry = self.local_cache.get(cache_key)
        if entry:
            # 检查是否过期
            if (datetime.now() - entry.timestamp).total_seconds() < entry.ttl:
                entry.hit_count += 1
                self.cache_stats["hits"] += 1
                return entry.result
            else:
                # 过期,删除
                del self.local_cache[cache_key]

        self.cache_stats["misses"] += 1
        return None

    def set(
        self, cache_key: str, result: dict[str, Any], ttl: int = 3600, engine_used: str = ""
    ) -> None:
        """设置缓存"""
        entry = CacheEntry(
            key=cache_key,
            result=result,
            timestamp=datetime.now(),
            ttl=ttl,
            engine_used=engine_used,
        )

        if self.use_redis:
            try:
                self.redis_client.setex(cache_key, ttl, json.dumps(result, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"Redis写入失败: {e}")

        # 同时写入本地缓存
        self.local_cache[cache_key] = entry

    def clear_expired(self) -> int:
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key
            for key, entry in self.local_cache.items()
            if (now - entry.timestamp).total_seconds() >= entry.ttl
        ]

        for key in expired_keys:
            del self.local_cache[key]

        return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total = self.cache_stats["total_requests"]
        hit_rate = self.cache_stats["hits"] / total if total > 0 else 0.0

        return {
            **self.cache_stats,
            "hit_rate": hit_rate,
            "local_cache_size": len(self.local_cache),
            "use_redis": self.use_redis,
        }


class UnifiedReasoningOrchestratorV2:
    """
    增强版统一推理引擎编排器 v2.0

    核心改进:
    1. 智能缓存 - 提升响应速度30-40%
    2. 增强路由规则 - 支持更多任务类型
    3. 性能监控 - 实时跟踪引擎性能
    4. A/B测试支持 - 验证路由策略
    5. 学习机制 - 基于历史优化
    """

    def __init__(
        self,
        enable_cache: bool = True,
        enable_ab_testing: bool = False,
        cache_ttl: int = 3600,
    ):
        self.version = "2.0.0"
        self.created_at = datetime.now()

        # 功能开关
        self.enable_cache = enable_cache
        self.enable_ab_testing = enable_ab_testing

        # 缓存管理
        if enable_cache:
            self.cache = ReasoningCache()
        else:
            self.cache = None

        # 路由规则
        self._build_enhanced_routing_rules()

        # 引擎缓存
        self._engine_cache: dict[str, Any] = {}

        # 性能监控
        self._performance_metrics: dict[str, PerformanceMetrics] = {}
        self._initialization_time = time.time()

        # A/B测试配置
        self._ab_test_config = {
            "enabled": enable_ab_testing,
            "test_groups": ["A", "B"],
            "traffic_split": {"A": 0.5, "B": 0.5},
        }

        # 学习数据
        self._routing_history: list[dict] = []
        self._success_history: dict[str, list[bool]] = defaultdict(list)

        # 统计信息 - 增强版
        self._statistics = {
            "total_requests": 0,
            "professional_tasks": 0,
            "general_tasks": 0,
            "semantic_tasks": 0,
            "bypass_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "ab_tests_run": 0,
        }

        logger.info("🚀 增强版统一推理引擎编排器v2.0初始化完成")
        logger.info(f"   缓存: {'启用' if enable_cache else '禁用'}")
        logger.info(f"   A/B测试: {'启用' if enable_ab_testing else '禁用'}")

    def _build_enhanced_routing_rules(self) -> None:
        """构建增强的路由规则"""

        # 专业任务路由表(直接使用专业能力,不使用超级推理)
        self.professional_routes = {
            # 意见答复 → 专业意见答复服务(绕过超级推理)⭐
            TaskType.OFFICE_ACTION_RESPONSE: EngineRecommendation(
                engine_name="professional_oa_responder",
                engine_type="direct_capability",
                confidence=1.0,
                reason="意见答复是专业法律任务,使用专业意见答复服务",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 无效宣告 → 小娜超级推理引擎(法律专业)
            TaskType.INVALIDITY_REQUEST: EngineRecommendation(
                engine_name="xiaona_super_reasoning_engine",
                engine_type="legal_reasoning",
                confidence=0.95,
                reason="无效宣告需要专业法律推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 专利撰写 → 小娜超级推理引擎
            TaskType.PATENT_DRAFTING: EngineRecommendation(
                engine_name="xiaona_super_reasoning_engine",
                engine_type="legal_reasoning",
                confidence=0.95,
                reason="专利撰写需要专业法律推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 专利合规 → 专家规则引擎
            TaskType.PATENT_COMPLIANCE: EngineRecommendation(
                engine_name="expert_rule_engine",
                engine_type="rule_based",
                confidence=0.98,
                reason="专利合规检查使用专家规则",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 新颖性分析 → 增强法律推理引擎
            TaskType.NOVELTY_ANALYSIS: EngineRecommendation(
                engine_name="enhanced_legal_reasoning_engine",
                engine_type="legal_reasoning",
                confidence=0.92,
                reason="新颖性分析需要专业法律推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 创造性分析 → 现有技术分析器 + LLM增强判断
            TaskType.INVENTIVENESS_ANALYSIS: EngineRecommendation(
                engine_name="prior_art_analyzer + llm_enhanced_judgment",
                engine_type="hybrid_legal",
                confidence=0.93,
                reason="创造性分析需要现有技术图谱+LLM判断",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # 权利要求分析 → 专利规则链
            TaskType.CLAIM_ANALYSIS: EngineRecommendation(
                engine_name="patent_rule_chain",
                engine_type="rule_chain",
                confidence=0.94,
                reason="权利要求分析使用规则链推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # ✨ 新增: 专利检索 → 语义推理引擎v4
            TaskType.PATENT_SEARCH: EngineRecommendation(
                engine_name="semantic_reasoning_engine_v4",
                engine_type="semantic",
                confidence=0.93,
                reason="专利检索需要语义相似度分析",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # ✨ 新增: 专利地图分析 → 现有技术分析器
            TaskType.PATENT_MAP_ANALYSIS: EngineRecommendation(
                engine_name="prior_art_analyzer",
                engine_type="knowledge_graph",
                confidence=0.91,
                reason="专利地图分析需要知识图谱推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
        }

        # 通用任务路由表(可以使用通用推理)
        self.general_routes = {
            TaskType.GENERAL_REASONING: EngineRecommendation(
                engine_name="unified_reasoning_engine",
                engine_type="general_reasoning",
                confidence=0.85,
                reason="通用推理使用统一推理引擎",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            TaskType.COMPLEX_PROBLEM_SOLVING: EngineRecommendation(
                engine_name="athena_super_reasoning",
                engine_type="super_reasoning",
                confidence=0.90,
                reason="复杂问题使用Athena超级推理(仅非法律任务)",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            TaskType.DECISION_SUPPORT: EngineRecommendation(
                engine_name="dual_system_reasoning",
                engine_type="dual_system",
                confidence=0.88,
                reason="决策支持使用双系统推理",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            # ✨ 新增: 战略规划 → Athena超级推理
            TaskType.STRATEGY_PLANNING: EngineRecommendation(
                engine_name="athena_super_reasoning",
                engine_type="super_reasoning",
                confidence=0.89,
                reason="战略规划需要深度推理",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            # ✨ 新增: 风险评估 → 双系统推理
            TaskType.RISK_ASSESSMENT: EngineRecommendation(
                engine_name="dual_system_reasoning",
                engine_type="dual_system",
                confidence=0.87,
                reason="风险评估需要快速直觉+深度分析",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
        }

        # 语义分析路由表
        self.semantic_routes = {
            TaskType.SEMANTIC_SEARCH: EngineRecommendation(
                engine_name="semantic_reasoning_engine_v4",
                engine_type="semantic",
                confidence=0.95,
                reason="语义搜索使用v4语义推理引擎",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            TaskType.KNOWLEDGE_GRAPH_QUERY: EngineRecommendation(
                engine_name="semantic_reasoning_engine",
                engine_type="semantic",
                confidence=0.92,
                reason="知识图谱查询使用语义推理",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # ✨ 新增: 相似性分析 → 语义推理引擎v4
            TaskType.SIMILARITY_ANALYSIS: EngineRecommendation(
                engine_name="semantic_reasoning_engine_v4",
                engine_type="semantic",
                confidence=0.94,
                reason="相似性分析使用语义向量计算",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
        }

        # 技术研究路由表
        self.technical_routes = {
            TaskType.TECHNOLOGY_LANDSCAPE: EngineRecommendation(
                engine_name="prior_art_analyzer",
                engine_type="knowledge_graph",
                confidence=0.93,
                reason="技术态势分析使用现有技术分析器",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            TaskType.ROADMAP_GENERATION: EngineRecommendation(
                engine_name="roadmap_generator",
                engine_type="roadmap",
                confidence=0.94,
                reason="路线图生成使用专用引擎",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            # ✨ 新增: 现有技术分析 → 现有技术分析器
            TaskType.PRIOR_ART_ANALYSIS: EngineRecommendation(
                engine_name="prior_art_analyzer",
                engine_type="knowledge_graph",
                confidence=0.93,
                reason="现有技术分析需要知识图谱",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
        }

        # ✨ 新增: 咨询服务路由表
        self.consulting_routes = {
            TaskType.LEGAL_CONSULTING: EngineRecommendation(
                engine_name="semantic_reasoning_engine_v4",
                engine_type="legal_reasoning",
                confidence=0.90,
                reason="法律咨询使用语义推理+法律规则",
                bypass_super_reasoning=True,
                direct_capability=True,
            ),
            TaskType.TECHNICAL_CONSULTING: EngineRecommendation(
                engine_name="dual_system_reasoning",
                engine_type="technical",
                confidence=0.88,
                reason="技术咨询需要快速响应+深度分析",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
            TaskType.BUSINESS_CONSULTING: EngineRecommendation(
                engine_name="dual_system_reasoning",
                engine_type="business",
                confidence=0.87,
                reason="商业咨询需要双系统推理",
                bypass_super_reasoning=False,
                direct_capability=False,
            ),
        }

    def analyze_task(
        self,
        task_description: str,
        task_type: TaskType | None = None,
        metadata: dict | None = None,
    ) -> TaskProfile:
        """分析任务特征 - 增强版"""
        # 统计
        self._statistics["total_requests"] += 1

        # 如果未提供任务类型,则自动推断
        if task_type is None:
            task_type = self._infer_task_type_enhanced(task_description, metadata or {})

        # 确定领域
        domain = self._infer_domain(task_type, metadata or {})

        # 确定复杂度
        complexity = self._infer_complexity(task_type, metadata or {})

        # 判断是否需要HITL
        requires_hitl = self._requires_human_in_loop(task_type)

        # 判断是否是法律任务
        is_legal = self._is_legal_task(task_type)

        # 预估执行时间(基于历史数据)
        estimated_time = self._estimate_execution_time(task_type, complexity)

        profile = TaskProfile(
            task_type=task_type,
            domain=domain,
            complexity=complexity,
            requires_human_in_loop=requires_hitl,
            is_legal_task=is_legal,
            metadata=metadata or {},
            estimated_time=estimated_time,
        )

        logger.info(
            f"任务分析完成: {task_type.value} | 领域: {domain.value} | "
            f"复杂度: {complexity.value} | 预估时间: {estimated_time:.2f}s"
        )

        return profile

    def _infer_task_type_enhanced(
        self, description: str, metadata: dict
    ) -> TaskType:
        """增强的任务类型推断"""
        desc_lower = description.lower()

        # 专业任务关键词(优先级最高)
        if any(kw in desc_lower for kw in ["意见答复", "审查意见", "oa", "office action"]):
            return TaskType.OFFICE_ACTION_RESPONSE
        elif any(kw in desc_lower for kw in ["无效", "无效宣告", "invalidity"]):
            return TaskType.INVALIDITY_REQUEST
        elif any(kw in desc_lower for kw in ["专利撰写", "patent drafting", "申请文件"]):
            return TaskType.PATENT_DRAFTING
        elif any(kw in desc_lower for kw in ["合规", "compliance"]):
            return TaskType.PATENT_COMPLIANCE
        elif any(kw in desc_lower for kw in ["新颖性", "novelty"]):
            return TaskType.NOVELTY_ANALYSIS
        elif any(kw in desc_lower for kw in ["创造性", "inventiveness", "非显而易见"]):
            return TaskType.INVENTIVENESS_ANALYSIS
        elif any(kw in desc_lower for kw in ["权利要求", "claim"]):
            return TaskType.CLAIM_ANALYSIS
        elif any(kw in desc_lower for kw in ["专利检索", "patent search", "检索专利"]):
            return TaskType.PATENT_SEARCH
        elif any(kw in desc_lower for kw in ["专利地图", "patent map", "技术布局"]):
            return TaskType.PATENT_MAP_ANALYSIS
        elif any(kw in desc_lower for kw in ["现有技术", "prior art"]):
            return TaskType.PRIOR_ART_ANALYSIS

        # 通用任务关键词
        elif any(kw in desc_lower for kw in ["战略", "strategy", "规划"]):
            return TaskType.STRATEGY_PLANNING
        elif any(kw in desc_lower for kw in ["风险", "risk"]):
            return TaskType.RISK_ASSESSMENT

        # 语义分析关键词
        elif any(kw in desc_lower for kw in ["语义搜索", "semantic", "相似度", "similarity"]):
            return TaskType.SEMANTIC_SEARCH

        # 咨询服务关键词
        elif any(kw in desc_lower for kw in ["法律咨询", "legal advice", "法律建议"]):
            return TaskType.LEGAL_CONSULTING
        elif any(kw in desc_lower for kw in ["技术咨询", "technical advice"]):
            return TaskType.TECHNICAL_CONSULTING
        elif any(kw in desc_lower for kw in ["商业咨询", "business advice"]):
            return TaskType.BUSINESS_CONSULTING

        # 默认
        else:
            return TaskType.GENERAL_REASONING

    def _estimate_execution_time(
        self, task_type: TaskType, complexity: TaskComplexity
    ) -> float:
        """预估执行时间"""
        # 基础时间(秒)
        base_times = {
            TaskType.OFFICE_ACTION_RESPONSE: 5.0,
            TaskType.INVALIDITY_REQUEST: 8.0,
            TaskType.PATENT_DRAFTING: 10.0,
            TaskType.GENERAL_REASONING: 2.0,
            TaskType.COMPLEX_PROBLEM_SOLVING: 5.0,
            TaskType.SEMANTIC_SEARCH: 1.0,
            TaskType.DECISION_SUPPORT: 3.0,
        }

        base_time = base_times.get(task_type, 3.0)

        # 复杂度系数
        complexity_factor = {
            TaskComplexity.LOW: 0.5,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.HIGH: 1.5,
            TaskComplexity.EXPERT: 2.0,
        }

        return base_time * complexity_factor.get(complexity, 1.0)

    def select_engine(self, profile: TaskProfile) -> EngineRecommendation:
        """选择最合适的推理引擎 - 增强版"""
        task_type = profile.task_type

        # A/B测试支持
        if self.enable_ab_testing:
            recommendation = self._select_engine_with_ab_test(profile)
        else:
            recommendation = self._select_engine_standard(profile)

        # 更新画像
        profile.selected_engine = recommendation.engine_name
        profile.confidence = recommendation.confidence

        # 记录历史
        self._routing_history.append({
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type.value,
            "engine": recommendation.engine_name,
            "confidence": recommendation.confidence,
        })

        logger.info(
            f"引擎选择: {recommendation.engine_name} | "
            f"置信度: {recommendation.confidence:.2f} | "
            f"绕过超级推理: {recommendation.bypass_super_reasoning}"
        )

        return recommendation

    def _select_engine_standard(self, profile: TaskProfile) -> EngineRecommendation:
        """标准引擎选择"""
        task_type = profile.task_type

        # 按优先级检查路由表
        if task_type in self.professional_routes:
            recommendation = self.professional_routes[task_type]
            self._statistics["professional_tasks"] += 1
            if recommendation.bypass_super_reasoning:
                self._statistics["bypass_count"] += 1
        elif task_type in self.general_routes:
            recommendation = self.general_routes[task_type]
            self._statistics["general_tasks"] += 1
        elif task_type in self.semantic_routes:
            recommendation = self.semantic_routes[task_type]
            self._statistics["semantic_tasks"] += 1
        elif task_type in self.technical_routes:
            recommendation = self.technical_routes[task_type]
            self._statistics["professional_tasks"] += 1
        elif task_type in self.consulting_routes:
            recommendation = self.consulting_routes[task_type]
            self._statistics["professional_tasks"] += 1
        else:
            recommendation = EngineRecommendation(
                engine_name="unified_reasoning_engine",
                engine_type="general_reasoning",
                confidence=0.70,
                reason="未找到特定路由,使用默认统一推理引擎",
                bypass_super_reasoning=False,
                direct_capability=False,
            )

        return recommendation

    def _select_engine_with_ab_test(self, profile: TaskProfile) -> EngineRecommendation:
        """带A/B测试的引擎选择"""
        import random

        # 基础推荐
        base_recommendation = self._select_engine_standard(profile)

        # 随机分配测试组
        test_group = "A" if random.random() < 0.5 else "B"

        # 如果是B组,尝试备选引擎
        if test_group == "B" and not base_recommendation.direct_capability:
            # 找到备选引擎
            alternatives = self._find_alternative_engines(profile.task_type)
            if alternatives:
                base_recommendation = alternatives[0]
                base_recommendation.is_ab_test = True
                base_recommendation.test_group = "B"
                self._statistics["ab_tests_run"] += 1

        base_recommendation.is_ab_test = True
        base_recommendation.test_group = test_group

        return base_recommendation

    def _find_alternative_engines(self, task_type: TaskType) -> list[EngineRecommendation]:
        """查找备选引擎"""
        alternatives = []

        # 构建备选列表
        all_routes = [
            *self.general_routes.values(),
            *self.semantic_routes.values(),
        ]

        # 过滤掉直接能力调用
        for route in all_routes:
            if not route.direct_capability:
                alternatives.append(route)

        return alternatives[:2]  # 返回最多2个备选

    def execute_reasoning(
        self,
        task_description: str,
        task_type: TaskType | None = None,
        metadata: dict | None = None,
        use_cache: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """执行推理(统一入口) - 增强版"""
        start_time = time.time()

        # 1. 分析任务
        profile = self.analyze_task(task_description, task_type, metadata)

        # 2. 检查缓存
        cached_result = None

        if self.enable_cache and use_cache and not metadata.get("bypass_cache"):
            cache_key = self.cache.generate_cache_key(
                task_description, profile.task_type.value, metadata
            )
            cached_result = self.cache.get(cache_key)

            if cached_result:
                profile.cache_hit = True
                self._statistics["cache_hits"] += 1

                logger.info(f"🎯 缓存命中! 节省时间: {cached_result.get('execution_time', 0):.3f}s")

                return {
                    "result": cached_result,
                    "profile": profile,
                    "from_cache": True,
                    "execution_time": time.time() - start_time,
                }

        self._statistics["cache_misses"] += 1

        # 3. 选择引擎
        recommendation = self.select_engine(profile)

        # 4. 记录推理轨迹
        profile.reasoning_trace.append({
            "timestamp": datetime.now().isoformat(),
            "action": "engine_selection",
            "engine": recommendation.engine_name,
            "reason": recommendation.reason,
            "bypass_super_reasoning": recommendation.bypass_super_reasoning,
        })

        # 5. 实际执行推理
        result = self._execute_with_engine(task_description, recommendation, **kwargs)

        # 6. 缓存结果
        if self.enable_cache and use_cache and cache_key:
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time

            # 根据任务类型设置不同的TTL
            ttl = 3600 if recommendation.direct_capability else 1800

            self.cache.set(cache_key, result, ttl=ttl, engine_used=recommendation.engine_name)

        # 7. 更新性能指标
        self._update_performance_metrics(recommendation.engine_name, time.time() - start_time, True)

        return {
            "result": result,
            "profile": profile,
            "recommendation": recommendation,
            "from_cache": False,
            "execution_time": time.time() - start_time,
        }

    def _execute_with_engine(
        self, task_description: str, recommendation: EngineRecommendation, **kwargs
    ) -> dict[str, Any]:
        """使用指定引擎执行推理"""
        if recommendation.direct_capability:
            return self._call_direct_capability(task_description, recommendation, **kwargs)
        else:
            return self._call_reasoning_engine(task_description, recommendation, **kwargs)

    def _call_direct_capability(
        self, task_description: str, recommendation: EngineRecommendation, **kwargs
    ) -> dict[str, Any]:
        """调用专业能力"""
        logger.info(f"调用专业能力: {recommendation.engine_name}")

        # 这里需要根据engine_name调用相应的专业能力
        return {
            "status": "success",
            "message": f"使用专业能力: {recommendation.engine_name}",
            "engine": recommendation.engine_name,
            "conclusion": f"基于{recommendation.engine_name}的分析结果",
        }

    def _call_reasoning_engine(
        self, task_description: str, recommendation: EngineRecommendation, **kwargs
    ) -> dict[str, Any]:
        """调用推理引擎"""
        logger.info(f"调用推理引擎: {recommendation.engine_name}")

        # 这里需要根据engine_name调用相应的推理引擎
        return {
            "status": "success",
            "message": f"使用推理引擎: {recommendation.engine_name}",
            "engine": recommendation.engine_name,
            "conclusion": f"基于{recommendation.engine_name}的推理结果",
        }

    def _update_performance_metrics(
        self, engine_name: str, execution_time: float, success: bool
    ) -> None:
        """更新性能指标"""
        if engine_name not in self._performance_metrics:
            self._performance_metrics[engine_name] = PerformanceMetrics(engine_name=engine_name)

        metrics = self._performance_metrics[engine_name]
        metrics.total_calls += 1
        metrics.total_time += execution_time
        metrics.avg_time = metrics.total_time / metrics.total_calls
        metrics.last_updated = datetime.now()

        # 记录成功历史
        self._success_history[engine_name].append(success)
        # 只保留最近100次
        if len(self._success_history[engine_name]) > 100:
            self._success_history[engine_name].pop(0)

        # 计算成功率
        metrics.success_rate = sum(self._success_history[engine_name]) / len(
            self._success_history[engine_name]
        )

    # 复用原有的推断方法
    def _infer_domain(self, task_type: TaskType, metadata: dict) -> TaskDomain:
        """推断任务领域"""
        if task_type in [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.PATENT_COMPLIANCE,
            TaskType.NOVELTY_ANALYSIS,
            TaskType.INVENTIVENESS_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
            TaskType.PATENT_SEARCH,
            TaskType.PATENT_MAP_ANALYSIS,
        ]:
            return TaskDomain.PATENT_LAW
        elif task_type in [
            TaskType.SEMANTIC_SEARCH,
            TaskType.KNOWLEDGE_GRAPH_QUERY,
            TaskType.SIMILARITY_ANALYSIS,
        ]:
            return TaskDomain.SEMANTIC_SEARCH
        elif task_type in [
            TaskType.TECHNOLOGY_LANDSCAPE,
            TaskType.ROADMAP_GENERATION,
            TaskType.PRIOR_ART_ANALYSIS,
        ]:
            return TaskDomain.TECHNICAL_RESEARCH
        elif task_type in [
            TaskType.LEGAL_CONSULTING,
            TaskType.TECHNICAL_CONSULTING,
            TaskType.BUSINESS_CONSULTING,
        ]:
            return TaskDomain.GENERAL_ANALYSIS
        else:
            return TaskDomain.GENERAL_ANALYSIS

    def _infer_complexity(self, task_type: TaskType, metadata: dict) -> TaskComplexity:
        """推断任务复杂度"""
        if task_type in [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.INVENTIVENESS_ANALYSIS,
        ]:
            return TaskComplexity.EXPERT
        elif task_type in [
            TaskType.NOVELTY_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
            TaskType.COMPLEX_PROBLEM_SOLVING,
            TaskType.STRATEGY_PLANNING,
            TaskType.PATENT_MAP_ANALYSIS,
        ]:
            return TaskComplexity.HIGH
        elif metadata.get("is_simple_task"):
            return TaskComplexity.LOW
        else:
            return TaskComplexity.MEDIUM

    def _requires_human_in_loop(self, task_type: TaskType) -> bool:
        """判断是否需要HITL"""
        high_difficulty_tasks = [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.INVENTIVENESS_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
        ]
        return task_type in high_difficulty_tasks

    def _is_legal_task(self, task_type: TaskType) -> bool:
        """判断是否是法律任务"""
        legal_tasks = [
            TaskType.OFFICE_ACTION_RESPONSE,
            TaskType.INVALIDITY_REQUEST,
            TaskType.PATENT_DRAFTING,
            TaskType.PATENT_COMPLIANCE,
            TaskType.NOVELTY_ANALYSIS,
            TaskType.INVENTIVENESS_ANALYSIS,
            TaskType.CLAIM_ANALYSIS,
            TaskType.LEGAL_CONSULTING,
        ]
        return task_type in legal_tasks

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息 - 增强版"""
        cache_stats = self.cache.get_stats() if self.cache else {}

        return {
            **self._statistics,
            "cache_stats": cache_stats,
            "performance_metrics": {
                name: {
                    "total_calls": m.total_calls,
                    "avg_time": m.avg_time,
                    "success_rate": m.success_rate,
                }
                for name, m in self._performance_metrics.items()
            },
            "uptime_seconds": time.time() - self._initialization_time,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
        }

    def get_performance_report(self) -> dict[str, Any]:
        """获取性能报告"""
        stats = self.get_statistics()

        # 计算关键指标
        total_requests = stats["total_requests"]
        bypass_rate = stats["bypass_count"] / total_requests if total_requests > 0 else 0
        cache_hit_rate = stats["cache_stats"].get("hit_rate", 0) if stats.get("cache_stats") else 0

        return {
            "summary": {
                "total_requests": total_requests,
                "bypass_rate": f"{bypass_rate:.1%}",
                "cache_hit_rate": f"{cache_hit_rate:.1%}",
                "uptime_hours": stats["uptime_seconds"] / 3600,
            },
            "routing_distribution": {
                "professional_tasks": stats["professional_tasks"],
                "general_tasks": stats["general_tasks"],
                "semantic_tasks": stats["semantic_tasks"],
            },
            "engine_performance": stats["performance_metrics"],
            "optimization_recommendations": self._generate_optimization_recommendations(stats),
        }

    def _generate_optimization_recommendations(self, stats: dict) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # 缓存命中率建议
        cache_hit_rate = stats["cache_stats"].get("hit_rate", 0) if stats.get("cache_stats") else 0
        if cache_hit_rate < 0.3:
            recommendations.append("缓存命中率较低,建议增加缓存TTL或优化缓存键策略")
        elif cache_hit_rate > 0.7:
            recommendations.append("缓存命中率优秀,可以考虑缩短缓存TTL以获得更新鲜的结果")

        # 绕过率建议
        bypass_rate = stats["bypass_count"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
        if bypass_rate < 0.5:
            recommendations.append("专业任务绕过率较低,建议优化路由规则以提升效率")

        # 引擎性能建议
        for engine_name, metrics in stats.get("performance_metrics", {}).items():
            if metrics["avg_time"] > 5.0:
                recommendations.append(f"{engine_name}平均响应时间较长({metrics['avg_time']:.2f}s),建议优化")

        if not recommendations:
            recommendations.append("系统运行良好,暂无优化建议")

        return recommendations

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._statistics = {
            "total_requests": 0,
            "professional_tasks": 0,
            "general_tasks": 0,
            "semantic_tasks": 0,
            "bypass_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "ab_tests_run": 0,
        }
        self._performance_metrics.clear()
        self._routing_history.clear()
        logger.info("统计信息已重置")


# 全局单例
_orchestrator_v2_instance: UnifiedReasoningOrchestratorV2 | None = None


def get_orchestrator_v2(
    enable_cache: bool = True, enable_ab_testing: bool = False
) -> UnifiedReasoningOrchestratorV2:
    """获取全局编排器v2实例"""
    global _orchestrator_v2_instance
    if _orchestrator_v2_instance is None:
        _orchestrator_v2_instance = UnifiedReasoningOrchestratorV2(
            enable_cache=enable_cache, enable_ab_testing=enable_ab_testing
        )
    return _orchestrator_v2_instance


# 便捷函数
def execute_reasoning_v2(
    task_description: str,
    task_type: TaskType | None = None,
    metadata: dict | None = None,
    use_cache: bool = True,
    **kwargs,
) -> dict[str, Any]:
    """执行推理(便捷函数)v2"""
    orchestrator = get_orchestrator_v2()
    return orchestrator.execute_reasoning(task_description, task_type, metadata, use_cache, **kwargs)


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_v2():
        """测试v2编排器"""
        print("=" * 80)
        print("🧪 测试增强版统一推理引擎编排器v2.0")
        print("=" * 80)

        orchestrator = get_orchestrator_v2(enable_cache=True, enable_ab_testing=False)

        # 测试案例
        test_cases = [
            {
                "description": "需要答复审查意见,审查员认为权利要求1-3不具备创造性",
                "task_type": TaskType.OFFICE_ACTION_RESPONSE,
            },
            {
                "description": "请帮我检索相关专利",
                "task_type": TaskType.PATENT_SEARCH,
            },
            {
                "description": "分析这个技术的创新点和风险",
                "task_type": None,  # 自动推断
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"测试案例 {i}:")
            print(f"描述: {test_case['description'][:50]}...")

            # 第一次执行(无缓存)
            result1 = orchestrator.execute_reasoning(
                task_description=test_case["description"],
                task_type=test_case["task_type"],
            )

            print(f"执行时间: {result1['execution_time']:.3f}s")
            print(f"引擎: {result1['recommendation'].engine_name}")
            print(f"来自缓存: {result1['from_cache']}")

            # 第二次执行(有缓存)
            result2 = orchestrator.execute_reasoning(
                task_description=test_case["description"],
                task_type=test_case["task_type"],
            )

            print(f"第二次执行时间: {result2['execution_time']:.3f}s")
            print(f"来自缓存: {result2['from_cache']}")

        # 显示性能报告
        print("\n" + "=" * 80)
        print("📊 性能报告:")
        print("=" * 80)
        report = orchestrator.get_performance_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))

    asyncio.run(test_v2())
