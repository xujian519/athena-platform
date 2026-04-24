"""Context Budget Manager — 总 budget 分配、动态调整与观测指标。"""

from dataclasses import dataclass, field
from typing import Optional

from .rollback import RollbackDecision, RollbackReason, RollbackTrigger
from .truncation import EvidenceItem, EvidenceTruncator, TruncationResult
from .utils import TokenEstimator


@dataclass
class BudgetAllocation:
    """各组件的 token budget 分配（单位：token）。"""

    system_prompt: int = 1024
    user_query: int = 512
    evidence: int = 4096
    output_buffer: int = 1024
    # 预留的弹性空间（用于格式标记、换行等不可见开销）
    overhead: int = 256

    @property
    def total(self) -> int:
        return (
            self.system_prompt
            + self.user_query
            + self.evidence
            + self.output_buffer
            + self.overhead
        )


@dataclass
class BudgetMetrics:
    """Budget 使用观测指标。"""

    budget_total: int = 0
    budget_used: int = 0
    budget_usage_ratio: float = 0.0
    evidence_count_before: int = 0
    evidence_count_after: int = 0
    evidence_dropped_count: int = 0
    rollback_reason: Optional[str] = None
    target_mode: str = "multi_source"
    elapsed_ms: Optional[float] = None


class ContextBudgetManager:
    """管理 prompt 上下文的总体 token budget。

    生命周期：
    1. 初始化时接收 total_budget，按比例生成 BudgetAllocation。
    2. 接收 system_prompt / user_query / evidence_list 并估算 token。
    3. 若 evidence 超出分配，调用 EvidenceTruncator 裁剪。
    4. 调用 RollbackTrigger 检查是否需要降级。
    5. 返回裁剪后的证据 + metrics。

    动态调整：
    - 当 user_query 很短时，可将其剩余 budget 转移给 evidence。
    - 当 system_prompt 固定且已知长度时，自动校准 system_prompt 配额。
    """

    # 默认分配比例（对应 8K budget）
    DEFAULT_ALLOCATION_8K = BudgetAllocation(
        system_prompt=1024,
        user_query=512,
        evidence=4096,
        output_buffer=1024,
        overhead=512,
    )

    # 默认分配比例（对应 16K budget）
    DEFAULT_ALLOCATION_16K = BudgetAllocation(
        system_prompt=1536,
        user_query=1024,
        evidence=8192,
        output_buffer=2048,
        overhead=768,
    )

    # 默认分配比例（对应 32K budget）
    DEFAULT_ALLOCATION_32K = BudgetAllocation(
        system_prompt=2048,
        user_query=2048,
        evidence=18432,
        output_buffer=4096,
        overhead=1024,
    )

    def __init__(
        self,
        total_budget: int,
        allocation: Optional[BudgetAllocation] = None,
        min_core_evidence: int = 2,
        timeout_ms: float = 200.0,
        estimator: Optional[TokenEstimator] = None,
        enable_dynamic_shift: bool = True,
    ) -> None:
        """
        Args:
            total_budget: 总体 token budget（如 8192）。
            allocation: 自定义分配；None 时按 total_budget 自动选择默认模板。
            min_core_evidence: 最少保留核心证据数。
            timeout_ms: 超时阈值（毫秒）。
            estimator: 外部 TokenEstimator；None 时自动创建。
            enable_dynamic_shift: 是否允许从 user_query 向 evidence 动态转移剩余 budget。
        """
        self.total_budget = total_budget
        self.allocation = allocation or self._select_default_allocation(total_budget)
        self.min_core_evidence = max(0, min_core_evidence)
        self.timeout_ms = timeout_ms
        self.estimator = estimator or TokenEstimator()
        self.enable_dynamic_shift = enable_dynamic_shift

        self._truncator = EvidenceTruncator(estimator=self.estimator)
        self._rollback = RollbackTrigger(
            min_core_threshold=min_core_evidence,
            timeout_ms=timeout_ms,
        )

        # 内部状态（每次 build_context 后更新）
        self.last_metrics: Optional[BudgetMetrics] = None

    def _select_default_allocation(self, total: int) -> BudgetAllocation:
        if total >= 32768:
            return self.DEFAULT_ALLOCATION_32K
        if total >= 16384:
            return self.DEFAULT_ALLOCATION_16K
        return self.DEFAULT_ALLOCATION_8K

    def _recalculate_allocation(
        self,
        system_prompt_text: str,
        user_query_text: str,
    ) -> BudgetAllocation:
        """基于实际文本长度动态校准分配。

        逻辑：
        - system_prompt 按实际长度校准（但不超过原配额 2 倍）。
        - user_query 按实际长度校准；若有剩余且 enable_dynamic_shift=True，转移给 evidence。
        - evidence 与 output_buffer 按比例占用剩余空间。
        """
        alloc = BudgetAllocation(
            system_prompt=self.allocation.system_prompt,
            user_query=self.allocation.user_query,
            evidence=self.allocation.evidence,
            output_buffer=self.allocation.output_buffer,
            overhead=self.allocation.overhead,
        )

        actual_sys = self.estimator.estimate(system_prompt_text)
        actual_user = self.estimator.estimate(user_query_text)

        # system_prompt 校准（留 10% 缓冲）
        sys_needed = int(actual_sys * 1.1)
        alloc.system_prompt = min(sys_needed, self.allocation.system_prompt * 2)

        # user_query 校准
        user_needed = int(actual_user * 1.1)
        alloc.user_query = min(user_needed, self.allocation.user_query * 2)

        # 动态转移
        if self.enable_dynamic_shift:
            user_surplus = self.allocation.user_query - alloc.user_query
            if user_surplus > 0:
                alloc.evidence += user_surplus

        # evidence + output_buffer 不能超过剩余空间
        remaining = self.total_budget - alloc.system_prompt - alloc.user_query - alloc.overhead
        if alloc.evidence + alloc.output_buffer > remaining:
            ratio = alloc.evidence / max(1, alloc.evidence + alloc.output_buffer)
            alloc.evidence = int(remaining * ratio)
            alloc.output_buffer = remaining - alloc.evidence

        return alloc

    def build_context(
        self,
        system_prompt: str,
        user_query: str,
        evidence_list: list[EvidenceItem],
        elapsed_ms: Optional[float] = None,
    ) -> dict:
        """构建上下文，执行裁剪与回滚检查。

        Args:
            system_prompt: 系统提示词文本。
            user_query: 用户查询文本。
            evidence_list: 检索到的证据列表。
            elapsed_ms: 已耗时（毫秒），用于超时回滚判断。

        Returns:
            dict 包含：
            - system_prompt: str
            - user_query: str
            - evidence: list[EvidenceItem]  # 裁剪后
            - metrics: BudgetMetrics
            - rollback: RollbackDecision
            - target_mode: str  # 最终建议模式
        """
        alloc = self._recalculate_allocation(system_prompt, user_query)

        # 裁剪证据
        trunc_result = self._truncator.truncate(
            evidence_list=evidence_list,
            target_budget=alloc.evidence,
            min_core_count=self.min_core_evidence,
        )

        # 回滚检查
        rollback = self._rollback.check(
            evidence_kept_count=len(trunc_result.kept),
            evidence_tokens=trunc_result.tokens_after,
            evidence_budget=alloc.evidence,
            elapsed_ms=elapsed_ms,
            extra_context={
                "total_budget": self.total_budget,
                "allocation": {
                    "system_prompt": alloc.system_prompt,
                    "user_query": alloc.user_query,
                    "evidence": alloc.evidence,
                    "output_buffer": alloc.output_buffer,
                    "overhead": alloc.overhead,
                },
            },
        )

        # 计算总体使用量
        sys_tokens = self.estimator.estimate(system_prompt)
        user_tokens = self.estimator.estimate(user_query)
        total_used = sys_tokens + user_tokens + trunc_result.tokens_after + alloc.output_buffer

        metrics = BudgetMetrics(
            budget_total=self.total_budget,
            budget_used=total_used,
            budget_usage_ratio=round(total_used / max(1, self.total_budget), 4),
            evidence_count_before=len(evidence_list),
            evidence_count_after=len(trunc_result.kept),
            evidence_dropped_count=len(trunc_result.dropped),
            rollback_reason=rollback.reason.value if rollback.should_rollback else None,
            target_mode=rollback.target_mode,
            elapsed_ms=elapsed_ms,
        )
        self.last_metrics = metrics

        return {
            "system_prompt": system_prompt,
            "user_query": user_query,
            "evidence": trunc_result.kept,
            "metrics": metrics,
            "rollback": rollback,
            "target_mode": rollback.target_mode,
        }

    def get_metrics(self) -> Optional[BudgetMetrics]:
        """获取最近一次 build_context 的 metrics。"""
        return self.last_metrics