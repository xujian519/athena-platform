from __future__ import annotations

"""
法律世界模型 + Wiki 提示词融合 API。
"""

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.legal_prompt_fusion.prompt_context_builder import LegalPromptContextBuilder
from core.legal_prompt_fusion.sync_manager import WikiSyncManager
from core.legal_prompt_fusion.models import PromptGenerationRequest


router = APIRouter(prefix="/api/v1/legal-prompt-fusion", tags=["法律提示词融合"])


class FusionGenerateRequest(BaseModel):
    user_query: str = Field(..., min_length=1, max_length=100000)
    domain: str = Field(default="patent")
    scenario: str = Field(default="general")
    additional_context: dict[str, Any] = Field(default_factory=dict)
    top_k_per_source: int = Field(default=5, ge=1, le=20)


class FusionGenerateResponse(BaseModel):
    system_prompt: str
    user_prompt: str
    template_version: str
    context: dict[str, Any]


class SyncStatusResponse(BaseModel):
    wiki_revision: str
    indexed_documents: int
    template_version: str
    verified_at: str
    alerts: list[str]


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "legal_prompt_fusion"}


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status():
    manager = WikiSyncManager()
    status = manager.build_sync_status()
    return SyncStatusResponse(
        wiki_revision=status.wiki_revision,
        indexed_documents=status.indexed_documents,
        template_version=status.template_version,
        verified_at=status.verified_at,
        alerts=status.alerts,
    )


@router.post("/context/generate", response_model=FusionGenerateResponse)
async def generate_context(request: FusionGenerateRequest):
    try:
        builder = LegalPromptContextBuilder()
        result = builder.build(
            PromptGenerationRequest(
                user_query=request.user_query,
                domain=request.domain,
                scenario=request.scenario,
                additional_context=request.additional_context,
                top_k_per_source=request.top_k_per_source,
            )
        )
        return FusionGenerateResponse(
            system_prompt=result.system_prompt,
            user_prompt=result.user_prompt,
            template_version=result.template_version,
            context={
                "domain": result.context.domain,
                "scenario": result.context.scenario,
                "freshness": result.context.freshness,
                "diagnostics": result.context.diagnostics,
                "legal_articles": [asdict(snippet) for snippet in result.context.legal_articles],
                "graph_relations": [asdict(snippet) for snippet in result.context.graph_relations],
                "wiki_background": [asdict(snippet) for snippet in result.context.wiki_background],
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成融合提示词上下文失败: {exc}") from exc
