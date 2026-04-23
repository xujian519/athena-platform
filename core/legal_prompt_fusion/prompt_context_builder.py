
"""
法律提示词上下文构建器。
"""

from typing import Any

from .config import FusionConfig
from .hybrid_retriever import HybridLegalRetriever
from .models import (
    FusedPromptContext,
    KnowledgeSnippet,
    PromptGenerationRequest,
    PromptGenerationResult,
    RetrievalEvidence,
    SourceType,
)
from .sync_manager import WikiSyncManager


class LegalPromptContextBuilder:
    """把多源知识证据转换为提示词上下文。"""

    def __init__(
        self,
        retriever: HybridLegalRetriever | None = None,
        sync_manager: WikiSyncManager | None = None,
        config: FusionConfig | None = None,
    ):
        self.config = config or FusionConfig()
        self.retriever = retriever or HybridLegalRetriever(config=self.config)
        self.sync_manager = sync_manager or WikiSyncManager(config=self.config)

    def build(self, request: PromptGenerationRequest) -> PromptGenerationResult:
        evidence = self.retriever.retrieve(
            request.user_query,
            top_k_per_source=request.top_k_per_source or self.config.default_top_k_per_source,
        )
        sync_status = self.sync_manager.build_sync_status()

        context = FusedPromptContext(
            user_query=request.user_query,
            domain=request.domain,
            scenario=request.scenario,
            legal_articles=self._convert_to_snippets(evidence, SourceType.POSTGRES),
            graph_relations=self._convert_to_snippets(evidence, SourceType.NEO4J),
            wiki_background=self._convert_to_snippets(evidence, SourceType.WIKI),
            evidence=evidence,
            freshness={
                "wiki_revision": sync_status.wiki_revision,
                "indexed_documents": sync_status.indexed_documents,
                "verified_at": sync_status.verified_at,
            },
            diagnostics={
                "source_distribution": self.retriever.summarize_source_distribution(evidence),
                "source_degradation": self.retriever.last_source_degradation,
                "alerts": sync_status.alerts,
                "additional_context_keys": sorted(request.additional_context.keys()),
            },
        )
        return PromptGenerationResult(
            system_prompt=self._render_system_prompt(context),
            user_prompt=self._render_user_prompt(context, request.additional_context),
            context=context,
            template_version=sync_status.template_version,
        )

    def _render_system_prompt(self, context: FusedPromptContext) -> str:
        legal_block = self._format_snippets(context.legal_articles, "最新法律条文与结构化依据")
        graph_block = self._format_snippets(context.graph_relations, "图谱关系与案例关联")
        wiki_block = self._format_snippets(context.wiki_background, "LLM Wiki 背景知识与实务说明")
        return f"""# 法律知识增强系统提示词

你是一名面向高风险法律/专利场景的专业 AI 助手。回答时必须优先使用当前上下文中的法律条文、图谱关系和 wiki 背景知识。

## 任务约束
- 优先基于证据回答，不得编造法条、案例或关系。
- 若结构化法条与 wiki 背景冲突，优先提示冲突并请求人工确认。
- 若关键事实缺失，必须列出缺口并进行追问。
- 对高风险结论给出依据来源和适用边界。

## 上下文元信息
- 领域: {context.domain}
- 场景: {context.scenario}
- Wiki 修订版本: {context.freshness.get('wiki_revision', 'unknown')}
- 检索证据数: {len(context.evidence)}

## 证据编排
{legal_block}

{graph_block}

{wiki_block}

## 输出要求
- 明确区分: 法律依据 / 关系推理 / 背景解释 / 建议动作
- 引用依据时优先使用当前上下文中的标题与来源
- 当证据不足时显式说明“不足以得出确定结论”
"""

    def _render_user_prompt(self, context: FusedPromptContext, additional_context: dict[str, Any]) -> str:
        additional_lines = "\n".join(
            f"- {key}: {value}" for key, value in sorted(additional_context.items())
        ) or "- 无"
        return f"""## 用户问题
{context.user_query}

## 业务上下文
- 领域: {context.domain}
- 场景: {context.scenario}

## 额外上下文
{additional_lines}

请结合当前提供的结构化法律数据、图谱关系和 wiki 背景知识，输出:
1. 核心结论
2. 直接法律依据
3. 关系推理与关联案例
4. 背景解释与适用边界
5. 需要用户补充或确认的信息
"""

    @staticmethod
    def _convert_to_snippets(
        evidence: list[RetrievalEvidence], source_type: SourceType
    ) -> list[KnowledgeSnippet]:
        snippets: list[KnowledgeSnippet] = []
        for item in evidence:
            if item.source_type != source_type:
                continue
            snippets.append(
                KnowledgeSnippet(
                    headline=item.title,
                    summary=item.content[:400],
                    citation=item.source_id,
                    source_type=item.source_type,
                    freshness_token=str(item.metadata.get("version_hash") or item.metadata.get("modified_ts") or "na"),
                )
            )
        return snippets[:4]

    @staticmethod
    def _format_snippets(snippets: list[KnowledgeSnippet], title: str) -> str:
        if not snippets:
            return f"### {title}\n- 暂无"
        lines = [f"### {title}"]
        for snippet in snippets:
            lines.append(
                f"- {snippet.headline}: {snippet.summary} [来源: {snippet.citation}]"
            )
        return "\n".join(lines)
