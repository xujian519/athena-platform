"""回滚触发器 — 在 budget 超限或证据不足时触发降级策略。"""

from dataclasses import dataclass, field
from enum import Enum


class RollbackReason(str, Enum):
    """回滚原因枚举。"""

    TOKEN_OVERFLOW = "token_overflow"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    TIMEOUT = "timeout"
    NONE = "none"


@dataclass
class RollbackDecision:
    """回滚决策结果。"""

    should_rollback: bool
    reason: RollbackReason = RollbackReason.NONE
    target_mode: str = "multi_source"  # 降级后模式: single_source | multi_source | aborted
    message: str = ""
    context: dict = field(default_factory=dict)


class RollbackTrigger:
    """根据预算与证据状态判断是否触发回滚（降级）。

    降级策略：
    - 多源融合 (multi_source) → 单源精简 (single_source) → 中止 (aborted)

    触发条件：
    1. TOKEN_OVERFLOW: 即使完成最小裁剪后 evidence 部分仍然超限。
    2. INSUFFICIENT_EVIDENCE: 保留的核心证据数 < min_core_threshold。
    3. TIMEOUT: 整体处理耗时超过 timeout_ms（默认 200ms，与 budget 联动）。
    """

    def __init__(
        self,
        min_core_threshold: int = 1,
        timeout_ms: float = 200.0,
    ) -> None:
        self.min_core_threshold = max(0, min_core_threshold)
        self.timeout_ms = max(0.0, timeout_ms)

    def check(
        self,
        evidence_kept_count: int,
        evidence_tokens: int,
        evidence_budget: int,
        elapsed_ms: float | None = None,
        extra_context: dict | None = None,
    ) -> RollbackDecision:
        """执行回滚检查。

        Args:
            evidence_kept_count: 裁剪后保留的证据条数。
            evidence_tokens: 裁剪后证据实际占用 token。
            evidence_budget: 证据部分分配到的 token budget。
            elapsed_ms: 已耗时（毫秒），None 表示未超时检测。
            extra_context: 额外诊断信息。

        Returns:
            RollbackDecision
        """
        context = dict(extra_context) if extra_context else {}
        context.update(
            {
                "evidence_kept_count": evidence_kept_count,
                "evidence_tokens": evidence_tokens,
                "evidence_budget": evidence_budget,
                "elapsed_ms": elapsed_ms,
                "min_core_threshold": self.min_core_threshold,
                "timeout_ms": self.timeout_ms,
            }
        )

        # 1. 超时回滚（最高优先级）
        if elapsed_ms is not None and elapsed_ms > self.timeout_ms:
            return RollbackDecision(
                should_rollback=True,
                reason=RollbackReason.TIMEOUT,
                target_mode="single_source",
                message=(
                    f"处理超时 ({elapsed_ms:.1f}ms > {self.timeout_ms:.1f}ms)，"
                    "降级为单源模式。"
                ),
                context=context,
            )

        # 2. Token 超限回滚：即使裁剪后仍超限
        if evidence_tokens > evidence_budget:
            return RollbackDecision(
                should_rollback=True,
                reason=RollbackReason.TOKEN_OVERFLOW,
                target_mode="single_source",
                message=(
                    f"证据 token ({evidence_tokens}) 超出 budget ({evidence_budget})，"
                    "即使裁剪后仍超限，降级为单源模式。"
                ),
                context=context,
            )

        # 3. 证据不足回滚
        if evidence_kept_count < self.min_core_threshold:
            return RollbackDecision(
                should_rollback=True,
                reason=RollbackReason.INSUFFICIENT_EVIDENCE,
                target_mode="single_source",
                message=(
                    f"保留证据数 ({evidence_kept_count}) 低于阈值 "
                    f"({self.min_core_threshold})，降级为单源模式。"
                ),
                context=context,
            )

        return RollbackDecision(
            should_rollback=False,
            reason=RollbackReason.NONE,
            target_mode="multi_source",
            message="预算与证据状态正常，无需回滚。",
            context=context,
        )
