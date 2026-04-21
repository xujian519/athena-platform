from __future__ import annotations
"""
权利要求修订器 - 基于审查意见的智能修订

基于论文#18《Patent-CR: Patent Claim Revision using Large Language Models》
- 22,606对权利要求修订数据
- GPT-4评估: Quality=6.8/10
- 生成式方法 + 后处理排序

作者: 小娜·天秤女神
创建时间: 2026-03-20
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RevisionMode(Enum):
    """修订模式"""
    CONSERVATIVE = "conservative"  # 保守模式 - 最小修改
    BALANCED = "balanced"  # 平衡模式
    AGGRESSIVE = "aggressive"  # 激进模式 - 较大改动


class OfficeActionType(Enum):
    """审查意见类型"""
    NOVELTY = "novelty"  # 新颖性问题
    INVENTIVE_STEP = "inventive_step"  # 创造性问题
    CLARITY = "clarity"  # 清晰性问题
    SUPPORT = "support"  # 支持性问题
    SCOPE = "scope"  # 范围问题
    FORMAL = "formal"  # 形式问题


@dataclass
class RevisionResult:
    """修订结果数据类"""

    # 输入信息
    original_claims: list[str]
    office_action: str
    revision_mode: str

    # 修订结果
    revised_claims: list[str] = field(default_factory=list)
    revision_explanation: str = ""

    # 多候选方案
    alternative_revisions: list[dict] = field(default_factory=list)

    # 质量评估
    quality_score: float = 0.0
    quality_assessment: dict = field(default_factory=dict)

    # 元数据
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    # 修订策略
    strategies_applied: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "original_claims": self.original_claims,
            "revised_claims": self.revised_claims,
            "revision_explanation": self.revision_explanation,
            "alternative_revisions": self.alternative_revisions,
            "quality_score": self.quality_score,
            "strategies_applied": self.strategies_applied,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class OfficeActionAnalysis:
    """审查意见分析结果"""
    action_type: OfficeActionType
    issues: list[dict]
    affected_claims: list[int]
    severity: str
    suggested_strategies: list[str]


class ClaimReviser:
    """
    权利要求修订器

    基于论文#18 Patent-CR实现:
    - 审查意见分析
    - 修订策略生成
    - 多候选方案排序
    - 质量评估集成

    关键指标:
    - 修订数据: 22,606对
    - 质量评分: 6.8/10 (GPT-4评估)
    """

    # 修订策略
    REVISION_STRATEGIES = {
        "add_feature": "添加技术特征",
        "narrow_scope": "缩小保护范围",
        "clarify_language": "澄清模糊表述",
        "split_claim": "拆分独立权利要求",
        "add_dependency": "增加从属权利要求",
        "rephrase": "重新表述",
        "add_embodiment": "添加实施例引用",
    }

    # 质量评分标准 (论文#18)
    QUALITY_CRITERIA = {
        "clarity": 0.2,  # 清晰度
        "completeness": 0.2,  # 完整性
        "legal_compliance": 0.25,  # 法律合规
        "scope_appropriateness": 0.2,  # 范围恰当性
        "support": 0.15,  # 支持性
    }

    def __init__(
        self,
        llm_manager=None,
        quality_assessor=None,
        use_cache: bool = True,
    ):
        """
        初始化权利要求修订器

        Args:
            llm_manager: LLM管理器 (可选，自动获取)
            quality_assessor: 质量评估器 (可选)
            use_cache: 是否使用缓存
        """
        self.name = "权利要求修订器"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # 核心组件 (延迟加载)
        self._llm_manager = llm_manager
        self._quality_assessor = quality_assessor
        self._use_cache = use_cache

        # 缓存
        self._revision_cache: dict[str, RevisionResult] = {}

        # 统计信息
        self.stats = {
            "total_revisions": 0,
            "cache_hits": 0,
            "avg_quality_score": 0.0,
            "avg_processing_time_ms": 0.0,
        }

    @property
    def llm_manager(self):
        """延迟加载LLM管理器"""
        if self._llm_manager is None:
            try:
                from core.llm.unified_llm_manager import get_unified_llm_manager
                self._llm_manager = get_unified_llm_manager()
            except ImportError:
                self.logger.warning("LLM管理器未找到")
        return self._llm_manager

    @property
    def quality_assessor(self):
        """延迟加载质量评估器"""
        if self._quality_assessor is None:
            try:
                from core.patents.quality_assessor import ClaimQualityAssessor
                self._quality_assessor = ClaimQualityAssessor()
            except ImportError:
                self.logger.warning("质量评估器未找到")
        return self._quality_assessor

    async def revise_claims(
        self,
        claims: list[str],
        office_action: str,
        prior_art: list[str] | None = None,
        revision_mode: str = "conservative",
        num_alternatives: int = 2,
    ) -> RevisionResult:
        """
        根据审查意见修订权利要求

        Args:
            claims: 原始权利要求列表
            office_action: 审查意见文本
            prior_art: 对比文件列表 (可选)
            revision_mode: 修订模式 (conservative/balanced/aggressive)
            num_alternatives: 生成备选方案数量

        Returns:
            RevisionResult: 修订结果
        """
        start_time = datetime.now()
        self.stats["total_revisions"] += 1

        # 检查缓存
        cache_key = f"{hash(tuple(claims))}:{hash(office_action)}:{revision_mode}"
        if self._use_cache and cache_key in self._revision_cache:
            self.stats["cache_hits"] += 1
            return self._revision_cache[cache_key]

        try:
            # 1. 分析审查意见
            oa_analysis = await self._analyze_office_action(office_action, claims)

            # 2. 生成多个修订候选
            candidates = await self._generate_revision_candidates(
                claims=claims,
                oa_analysis=oa_analysis,
                prior_art=prior_art,
                revision_mode=RevisionMode(revision_mode),
                num_candidates=num_alternatives + 1,
            )

            # 3. 评估和排序候选方案
            scored_candidates = await self._score_and_rank_candidates(candidates, claims)

            # 4. 选择最佳方案
            best = scored_candidates[0] if scored_candidates else None

            if best is None:
                # 降级: 返回原始权利要求
                best = {"revised_claims": claims, "explanation": "无法生成修订方案", "quality_score": 0.0}

            # 5. 构建结果
            result = RevisionResult(
                original_claims=claims,
                office_action=office_action,
                revision_mode=revision_mode,
                revised_claims=best["revised_claims"],
                revision_explanation=best.get("explanation", ""),
                alternative_revisions=scored_candidates[1 : num_alternatives + 1],
                quality_score=best.get("quality_score", 0.0),
                strategies_applied=best.get("strategies", []),
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
            )

            # 缓存结果
            if self._use_cache:
                self._revision_cache[cache_key] = result

            # 更新统计
            self._update_stats(result.quality_score, result.processing_time_ms)

            return result

        except Exception as e:
            self.logger.error(f"权利要求修订失败: {e}")
            return RevisionResult(
                original_claims=claims,
                office_action=office_action,
                revision_mode=revision_mode,
                revised_claims=claims,
                revision_explanation=f"修订失败: {str(e)}",
            )

    async def _analyze_office_action(
        self,
        office_action: str,
        claims: list[str],
    ) -> OfficeActionAnalysis:
        """
        分析审查意见

        Args:
            office_action: 审查意见文本
            claims: 权利要求列表

        Returns:
            OfficeActionAnalysis: 分析结果
        """
        if self.llm_manager is None:
            return self._rule_based_oa_analysis(office_action, claims)

        try:
            prompt = f"""
作为专利审查专家，请分析以下审查意见：

审查意见:
{office_action}

涉及的权利要求:
{self._format_claims(claims)}

请分析:
1. 审查意见类型 (新颖性/创造性/清晰性/支持性/范围/形式)
2. 具体问题点
3. 涉及的权利要求编号
4. 问题严重程度 (critical/important/minor)
5. 建议的修订策略

请以JSON格式返回:
{{
    "action_type": "<类型>",
    "issues": [{{"claim": 1, "issue": "...", "severity": "..."}}],
    "affected_claims": [1, 2],
    "severity": "<严重程度>",
    "suggested_strategies": ["策略1", "策略2"]
}}
"""

            response = await self.llm_manager.generate(prompt)

            # 解析响应
            analysis = self._parse_oa_analysis(response, office_action, claims)
            return analysis

        except Exception as e:
            self.logger.error(f"审查意见分析失败: {e}")
            return self._rule_based_oa_analysis(office_action, claims)

    def _rule_based_oa_analysis(
        self,
        office_action: str,
        claims: list[str],
    ) -> OfficeActionAnalysis:
        """基于规则的审查意见分析 (降级方案)"""
        # 关键词检测
        action_type = OfficeActionType.FORMAL
        issues = []
        affected_claims = []
        severity = "minor"

        oa_lower = office_action.lower()

        # 新颖性
        if any(kw in oa_lower for kw in ["新颖性", "novelty", "x类", "对比文件"]):
            action_type = OfficeActionType.NOVELTY
            severity = "critical"
            issues.append({"issue": "新颖性问题", "severity": "critical"})

        # 创造性
        if any(kw in oa_lower for kw in ["创造性", "inventive", "y类", "显而易见"]):
            action_type = OfficeActionType.INVENTIVE_STEP
            severity = "critical"
            issues.append({"issue": "创造性问题", "severity": "critical"})

        # 清晰性
        if any(kw in oa_lower for kw in ["清楚", "clarity", "模糊", "不明确"]):
            action_type = OfficeActionType.CLARITY
            issues.append({"issue": "清晰性问题", "severity": "important"})

        # 提取涉及的权利要求编号
        import re
        claim_numbers = re.findall(r"权利要求\s*(\d+)", office_action)
        if not claim_numbers:
            claim_numbers = re.findall(r"claim\s*(\d+)", oa_lower)
        affected_claims = [int(n) for n in claim_numbers] if claim_numbers else [1]

        strategies = self._get_strategies_for_type(action_type)

        return OfficeActionAnalysis(
            action_type=action_type,
            issues=issues,
            affected_claims=affected_claims,
            severity=severity,
            suggested_strategies=strategies,
        )

    def _get_strategies_for_type(self, action_type: OfficeActionType) -> list[str]:
        """根据审查意见类型获取修订策略"""
        strategy_map = {
            OfficeActionType.NOVELTY: ["add_feature", "narrow_scope"],
            OfficeActionType.INVENTIVE_STEP: ["add_feature", "clarify_language", "add_embodiment"],
            OfficeActionType.CLARITY: ["clarify_language", "rephrase"],
            OfficeActionType.SUPPORT: ["add_embodiment", "rephrase"],
            OfficeActionType.SCOPE: ["narrow_scope", "add_dependency"],
            OfficeActionType.FORMAL: ["rephrase"],
        }
        return strategy_map.get(action_type, ["rephrase"])

    def _parse_oa_analysis(self, response: str, office_action: str, claims: list[str]) -> OfficeActionAnalysis:
        """解析LLM响应"""
        # TODO: 实现JSON解析
        # 当前使用规则分析作为降级
        return self._rule_based_oa_analysis(office_action, claims)

    async def _generate_revision_candidates(
        self,
        claims: list[str],
        oa_analysis: OfficeActionAnalysis,
        prior_art: list[str] | None,
        revision_mode: RevisionMode,
        num_candidates: int,
    ) -> list[dict]:
        """生成多个修订候选"""
        candidates = []

        for i in range(num_candidates):
            candidate = await self._generate_single_revision(
                claims=claims,
                oa_analysis=oa_analysis,
                prior_art=prior_art,
                revision_mode=revision_mode,
                variation_index=i,
            )
            if candidate:
                candidates.append(candidate)

        return candidates

    async def _generate_single_revision(
        self,
        claims: list[str],
        oa_analysis: OfficeActionAnalysis,
        prior_art: list[str] | None,
        revision_mode: RevisionMode,
        variation_index: int,
    ) -> dict | None:
        """生成单个修订方案"""
        if self.llm_manager is None:
            return self._rule_based_revision(claims, oa_analysis, revision_mode)

        try:
            mode_instruction = {
                RevisionMode.CONSERVATIVE: "请进行最小必要修改，保持权利要求的原有范围。",
                RevisionMode.BALANCED: "请在修改范围和保护力度之间取得平衡。",
                RevisionMode.AGGRESSIVE: "可以进行较大修改，以确保通过审查。",
            }

            prompt = f"""
作为专利代理人，请根据审查意见修订以下权利要求。

原始权利要求:
{self._format_claims(claims)}

审查意见分析:
- 类型: {oa_analysis.action_type.value}
- 问题: {oa_analysis.issues}
- 涉及权利要求: {oa_analysis.affected_claims}
- 建议策略: {oa_analysis.suggested_strategies}

{f"对比文件: {chr(10).join(prior_art[:2])}" if prior_art else ""}

修订要求:
{mode_instruction.get(revision_mode, "")}

这是第{variation_index + 1}个修订方案，请尝试不同的修订策略。

请以JSON格式返回:
{{
    "revised_claims": ["权利要求1...", "权利要求2..."],
    "explanation": "修订说明...",
    "strategies": ["使用的策略1", "使用的策略2"]
}}
"""

            response = await self.llm_manager.generate(prompt)
            return self._parse_revision_response(response, claims)

        except Exception as e:
            self.logger.error(f"生成修订方案失败: {e}")
            return self._rule_based_revision(claims, oa_analysis, revision_mode)

    def _rule_based_revision(
        self,
        claims: list[str],
        oa_analysis: OfficeActionAnalysis,
        revision_mode: RevisionMode,
    ) -> dict:
        """基于规则的修订 (降级方案)"""
        # 简单规则: 添加限定词
        revised = []
        strategies = []

        for i, claim in enumerate(claims):
            if i == 0:  # 独立权利要求
                if oa_analysis.action_type in [OfficeActionType.NOVELTY, OfficeActionType.INVENTIVE_STEP]:
                    # 添加技术特征
                    claim = claim.replace("一种", "一种改进的")
                    claim = claim.rstrip("。") + "，其特征在于还包括以下技术特征。"
                    strategies.append("add_feature")
                elif oa_analysis.action_type == OfficeActionType.CLARITY:
                    # 澄清表述
                    claim = claim.replace("所述", "上述具体")
                    strategies.append("clarify_language")

            revised.append(claim)

        return {
            "revised_claims": revised,
            "explanation": "基于规则的自动修订",
            "strategies": strategies,
            "quality_score": 5.0,  # 规则修订默认分数
        }

    def _parse_revision_response(self, response: str, original_claims: list[str]) -> dict:
        """解析修订响应"""
        # TODO: 实现JSON解析
        # 当前返回原始权利要求
        return {
            "revised_claims": original_claims,
            "explanation": "解析失败，返回原始权利要求",
            "strategies": [],
            "quality_score": 0.0,
        }

    async def _score_and_rank_candidates(
        self,
        candidates: list[dict],
        original_claims: list[str],
    ) -> list[dict]:
        """评估和排序候选方案"""
        if not candidates:
            return []

        scored = []
        for candidate in candidates:
            quality = await self._assess_revision_quality(
                candidate["revised_claims"],
                candidate.get("explanation", ""),
            )
            scored.append({
                **candidate,
                "quality_score": quality,
            })

        # 按质量分数排序
        scored.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        return scored

    async def _assess_revision_quality(
        self,
        revised_claims: list[str],
        explanation: str,
    ) -> float:
        """评估修订质量"""
        if self.quality_assessor is None:
            return 5.0  # 默认分数

        try:
            assessment = self.quality_assessor.assess(
                claim_text="\n".join(revised_claims),
                description=explanation,
            )
            return assessment.overall_score
        except Exception as e:
            self.logger.error(f"质量评估失败: {e}")
            return 5.0

    def _format_claims(self, claims: list[str]) -> str:
        """格式化权利要求列表"""
        lines = []
        for i, claim in enumerate(claims, 1):
            lines.append(f"权利要求{i}: {claim}")
        return "\n".join(lines)

    def _update_stats(self, quality_score: float, processing_time_ms: float):
        """更新统计信息"""
        n = self.stats["total_revisions"]
        old_avg_q = self.stats["avg_quality_score"]
        old_avg_t = self.stats["avg_processing_time_ms"]

        self.stats["avg_quality_score"] = old_avg_q + (quality_score - old_avg_q) / n
        self.stats["avg_processing_time_ms"] = old_avg_t + (processing_time_ms - old_avg_t) / n

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            "cache_hit_rate": (
                self.stats["cache_hits"] / self.stats["total_revisions"]
                if self.stats["total_revisions"] > 0
                else 0
            ),
        }


# 便捷函数
def get_claim_reviser() -> ClaimReviser:
    """获取权利要求修订器实例"""
    return ClaimReviser()
