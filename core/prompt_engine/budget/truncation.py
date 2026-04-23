"""证据裁剪算法 — 按相关性排序并动态移除低优先级证据。"""

from dataclasses import dataclass, field

from .utils import TokenEstimator


@dataclass
class EvidenceItem:
    """单条检索证据。"""

    content: str
    relevance_score: float = 0.0  # 越高越重要，建议范围 0.0 ~ 1.0
    source: str = "unknown"
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.metadata, dict):
            object.__setattr__(self, "metadata", dict(self.metadata) if self.metadata else {})


@dataclass
class TruncationResult:
    """裁剪结果。"""

    kept: list[EvidenceItem]
    dropped: list[EvidenceItem]
    tokens_before: int
    tokens_after: int
    target_budget: int


class EvidenceTruncator:
    """在 token budget 约束下裁剪证据列表。

    策略：
    1. 按 relevance_score 降序排列（同分按内容长度升序，优先保留短的）。
    2. 累加 token 直到达到 target_budget。
    3. 剩余证据放入 dropped。
    4. 保证至少保留 min_core_count 条（即使超限也由上层 RollbackTrigger 处理）。
    """

    def __init__(self, estimator: TokenEstimator | None = None) -> None:
        self._estimator = estimator or TokenEstimator()

    def truncate(
        self,
        evidence_list: list[EvidenceItem],
        target_budget: int,
        min_core_count: int = 1,
    ) -> TruncationResult:
        """裁剪证据至目标 budget 内。

        Args:
            evidence_list: 原始证据列表。
            target_budget: 证据部分允许的最大 token 数。
            min_core_count: 至少保留的核心证据条数（默认 1）。

        Returns:
            TruncationResult，包含保留/丢弃的证据及 token 统计。
        """
        if not evidence_list:
            return TruncationResult(
                kept=[], dropped=[], tokens_before=0, tokens_after=0, target_budget=target_budget
            )

        # 排序：相关性降序，同分则内容短的优先
        sorted_evidence = sorted(
            evidence_list,
            key=lambda e: (-e.relevance_score, self._estimator.estimate(e.content)),
        )

        tokens_before = sum(self._estimator.estimate(e.content) for e in sorted_evidence)

        kept: list[EvidenceItem] = []
        dropped: list[EvidenceItem] = []
        used_tokens = 0

        for idx, item in enumerate(sorted_evidence):
            item_tokens = self._estimator.estimate(item.content)

            # 优先满足 min_core_count
            if idx < min_core_count:
                kept.append(item)
                used_tokens += item_tokens
                continue

            # 预算检查
            if used_tokens + item_tokens <= target_budget:
                kept.append(item)
                used_tokens += item_tokens
            else:
                dropped.append(item)

        tokens_after = sum(self._estimator.estimate(e.content) for e in kept)

        return TruncationResult(
            kept=kept,
            dropped=dropped,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            target_budget=target_budget,
        )
