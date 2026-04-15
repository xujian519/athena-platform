"""
专利AI服务API路由
Patent AI Services API Routes

基于论文研究的专利智能服务API:
- POST /api/v2/patent/classify - 专利分类 (CPC/IPC)
- POST /api/v2/patent/claims/revise - 权利要求修订
- POST /api/v2/patent/invalidity/predict - 无效性预测
- POST /api/v2/patent/quality/score - 质量评分
- POST /api/v2/patent/search/semantic - 语义搜索
- GET  /api/v2/patent/risk/assess - 风险评估

OpenClaw集成 (v2.1.0):
- POST /api/v2/patent/draft/full - 完整9阶段说明书撰写
- POST /api/v2/patent/draft/review - 说明书质量审查
- GET  /api/v2/patent/tasks - 任务列表
- GET  /api/v2/patent/tasks/{task_id} - 任务详情
- POST /api/v2/patent/tasks/{task_id}/pause - 暂停任务
- POST /api/v2/patent/tasks/{task_id}/resume - 恢复任务

作者: 小娜·天秤女神
创建时间: 2026-03-20
更新时间: 2026-03-27 (OpenClaw集成)
"""

from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/patent", tags=["Patent AI Services"])


# ========== 请求/响应模型 ==========

class ClassifyRequest(BaseModel):
    """专利分类请求"""
    patent_text: str = Field(..., description="专利文本 (标题+摘要+权利要求)")
    classification_type: str = Field(default="CPC", description="分类体系 (CPC/IPC)")
    top_k: int = Field(default=3, ge=1, le=10, description="返回前K个候选分类")


class ClassificationCode(BaseModel):
    """分类代码"""
    code: str
    confidence: float
    description: str | None = None


class ClassifyResponse(BaseModel):
    """专利分类响应"""
    codes: list[ClassificationCode]
    method: str
    processing_time_ms: float


class ClaimRevisionRequest(BaseModel):
    """权利要求修订请求"""
    claims: list[str] = Field(..., description="原始权利要求列表")
    office_action: str = Field(..., description="审查意见文本")
    prior_art: list[str] | None = Field(default=None, description="对比文件列表")
    revision_mode: str = Field(default="conservative", description="修订模式 (conservative/balanced/aggressive)")


class RevisedClaim(BaseModel):
    """修订后的权利要求"""
    claim_number: int
    original: str
    revised: str
    changes: list[str]


class ClaimRevisionResponse(BaseModel):
    """权利要求修订响应"""
    revised_claims: list[RevisedClaim]
    explanation: str
    strategies_applied: list[str]
    quality_score: float
    alternatives: list[dict]


class InvalidityPredictionRequest(BaseModel):
    """无效性预测请求"""
    patent_no: str = Field(..., description="专利号")
    claims: list[str] = Field(..., description="权利要求列表")
    examination_history: dict | None = Field(default=None, description="审查历史数据")
    citations: list[dict] | None = Field(default=None, description="引用数据")


class WeakPoint(BaseModel):
    """薄弱点"""
    category: str
    issue: str
    impact: str
    suggestion: str | None = None


class InvalidityPredictionResponse(BaseModel):
    """无效性预测响应"""
    patent_no: str
    risk_score: float
    risk_level: str
    confidence: float
    weak_points: list[WeakPoint]
    strong_points: list[str]
    recommendations: list[str]
    processing_time_ms: float


class QualityScoringRequest(BaseModel):
    """质量评分请求"""
    patent_data: dict = Field(..., description="专利完整数据")
    assessment_scope: str = Field(default="full", description="评估范围 (full/quick/claims_only)")


class QualityScoringResponse(BaseModel):
    """质量评分响应"""
    patent_no: str
    overall_score: float
    quality_level: str
    base_quality: dict
    npe_risk: dict | None = None
    software_risk: dict | None = None
    recommendations: list[str]
    priority_actions: list[dict]
    processing_time_ms: float


class RiskAssessmentRequest(BaseModel):
    """风险评估请求"""
    claims: list[str] = Field(..., description="权利要求列表")
    cpc_code: str | None = Field(default=None, description="CPC分类代码")
    assignee_type: str | None = Field(default=None, description="权利人类型")


class RiskAssessmentResponse(BaseModel):
    """风险评估响应"""
    npe_risk: dict
    software_patent_risk: dict
    overall_risk_level: str
    mitigation_suggestions: list[str]


# ========== OpenClaw集成：9阶段撰写 ==========

class DraftFullSpecRequest(BaseModel):
    """完整9阶段说明书撰写请求"""
    disclosure: str = Field(..., description="技术交底书内容")
    client: str = Field(default="", description="客户名称")
    invention_type: str | None = Field(default=None, description="发明类型")
    drawing_paths: list[str] | None = Field(default=None, description="附图路径列表")
    prior_art: list[dict] | None = Field(default=None, description="对比文件列表")
    enable_examiner_simulation: bool = Field(default=True, description="启用审查员模拟")
    max_iterations: int = Field(default=3, ge=1, le=5, description="最大迭代次数")


class ReviewIssueResponse(BaseModel):
    """审查问题响应"""
    issue_id: str
    priority: str
    location: str
    description: str
    legal_basis: str
    suggestion: str


class ExaminerReportResponse(BaseModel):
    """审查报告响应"""
    overall_risk: str
    authorization_probability: float
    p0_count: int
    p1_count: int
    p2_count: int
    issues: list[ReviewIssueResponse]
    summary: str


class DraftFullSpecResponse(BaseModel):
    """完整9阶段说明书撰写响应"""
    task_id: str
    status: str
    current_phase: int
    phases_completed: list[int]
    processing_time_ms: float
    invention_title: str | None = None
    claims_count: int | None = None
    word_count: int | None = None
    examiner_report: ExaminerReportResponse | None = None
    full_specification: str | None = None
    notes: list[str] = []


class TaskProgressResponse(BaseModel):
    """任务进度响应"""
    task_id: str
    status: str
    current_phase: int
    current_phase_name: str
    completed_phases: int
    total_phases: int
    progress_percentage: str
    created: str
    updated: str


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: list[dict]
    total: int


# ========== API端点 ==========

@router.post("/classify", response_model=ClassifyResponse)
async def classify_patent(request: ClassifyRequest):
    """
    专利自动分类

    基于论文#16 PatentSBERTa实现:
    - Augmented SBERT数据增强
    - KNN分类: F1=66.48%
    - 46,800x加速

    **响应示例**:
    ```json
    {
        "codes": [
            {"code": "G06F16/33", "confidence": 0.85, "description": "信息检索"},
            {"code": "G06F40/30", "confidence": 0.72, "description": "语义分析"}
        ],
        "method": "PatentSBERTa+KNN+LLM",
        "processing_time_ms": 150.5
    }
    ```
    """
    try:
        from core.patent.ai_services import PatentClassifier

        classifier = PatentClassifier()
        result = await classifier.classify(
            patent_text=request.patent_text,
            classification_type=request.classification_type,
            top_k=request.top_k,
        )

        codes = [
            ClassificationCode(
                code=c.get("code", ""),
                confidence=c.get("confidence", 0.0),
                description=c.get("description"),
            )
            for c in result.codes
        ]

        return ClassifyResponse(
            codes=codes,
            method=result.method,
            processing_time_ms=result.processing_time_ms,
        )

    except Exception as e:
        logger.error(f"专利分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"专利分类失败: {str(e)}") from e


@router.post("/claims/revise", response_model=ClaimRevisionResponse)
async def revise_claims(request: ClaimRevisionRequest):
    """
    权利要求修订

    基于论文#18 Patent-CR实现:
    - 22,606对权利要求修订数据
    - GPT-4评估: Quality=6.8/10

    **修订模式**:
    - conservative: 最小修改
    - balanced: 平衡修改
    - aggressive: 较大改动
    """
    try:
        from core.patent.ai_services import ClaimReviser

        reviser = ClaimReviser()
        result = await reviser.revise_claims(
            claims=request.claims,
            office_action=request.office_action,
            prior_art=request.prior_art,
            revision_mode=request.revision_mode,
        )

        revised_claims = []
        for i, revised in enumerate(result.revised_claims):
            original = request.claims[i] if i < len(request.claims) else ""
            revised_claims.append(RevisedClaim(
                claim_number=i + 1,
                original=original,
                revised=revised,
                changes=[],  # TODO: 实现差异对比
            ))

        return ClaimRevisionResponse(
            revised_claims=revised_claims,
            explanation=result.revision_explanation,
            strategies_applied=result.strategies_applied,
            quality_score=result.quality_score,
            alternatives=result.alternative_revisions[:3],
        )

    except Exception as e:
        logger.error(f"权利要求修订失败: {e}")
        raise HTTPException(status_code=500, detail=f"权利要求修订失败: {str(e)}") from e


@router.post("/invalidity/predict", response_model=InvalidityPredictionResponse)
async def predict_invalidity(request: InvalidityPredictionRequest):
    """
    无效性风险预测

    基于论文#19实现:
    - Gradient Boosting: AUC=0.80
    - 审查历史特征最重要 (35%)

    **风险等级**:
    - low: < 20%
    - medium: 20-50%
    - high: 50-75%
    - critical: > 75%
    """
    try:
        from core.patent.ai_services import InvalidityPredictor

        predictor = InvalidityPredictor()
        result = await predictor.predict_invalidity_risk(
            patent_no=request.patent_no,
            claims=request.claims,
            examination_history=request.examination_history,
            citations=request.citations,
        )

        weak_points = [
            WeakPoint(
                category=wp.get("category", ""),
                issue=wp.get("issue", ""),
                impact=wp.get("impact", ""),
                suggestion=wp.get("suggestion"),
            )
            for wp in result.weak_points
        ]

        return InvalidityPredictionResponse(
            patent_no=result.patent_no,
            risk_score=result.risk_score,
            risk_level=result.risk_level.value,
            confidence=result.confidence,
            weak_points=weak_points,
            strong_points=result.strong_points,
            recommendations=result.recommendations,
            processing_time_ms=result.processing_time_ms,
        )

    except Exception as e:
        logger.error(f"无效性预测失败: {e}")
        raise HTTPException(status_code=500, detail=f"无效性预测失败: {str(e)}") from e


@router.post("/quality/score", response_model=QualityScoringResponse)
async def score_quality(request: QualityScoringRequest):
    """
    专利质量评分

    基于论文#20实现:
    - Random Forest: AUC=0.78
    - NPE专利坏专利比例55%
    - 软件/商业方法专利风险最高

    **评估范围**:
    - full: 完整评估 (基础六维 + NPE风险 + 软件专利风险 + 审查历史)
    - quick: 快速评估 (基础六维 + NPE风险 + 软件专利风险)
    - claims_only: 仅权利要求评估
    """
    try:
        from core.patent.ai_services import EnhancedPatentQualityScorer

        scorer = EnhancedPatentQualityScorer()
        result = await scorer.comprehensive_quality_assessment(
            patent_data=request.patent_data,
            assessment_scope=request.assessment_scope,
        )

        return QualityScoringResponse(
            patent_no=result.patent_no,
            overall_score=result.overall_score,
            quality_level=result.quality_level,
            base_quality=result.base_quality,
            npe_risk=result.npe_risk.to_dict() if result.npe_risk else None,
            software_risk=result.software_risk.to_dict() if result.software_risk else None,
            recommendations=result.recommendations,
            priority_actions=result.priority_actions,
            processing_time_ms=result.processing_time_ms,
        )

    except Exception as e:
        logger.error(f"质量评分失败: {e}")
        raise HTTPException(status_code=500, detail=f"质量评分失败: {str(e)}") from e


@router.get("/risk/assess", response_model=RiskAssessmentResponse)
async def assess_risk(
    claims: list[str] = Query(..., description="权利要求列表"),
    cpc_code: str | None = Query(None, description="CPC分类代码"),
    assignee_type: str | None = Query(None, description="权利人类型"),
):
    """
    风险评估 (快速)

    评估NPE专利风险和软件专利风险

    **返回**:
    - NPE风险评估
    - 软件专利风险评估
    - 综合风险等级
    - 缓解建议
    """
    try:
        from core.patent.ai_services.risk_assessment import (
            NPERiskDetector,
            SoftwarePatentRiskAnalyzer,
        )

        # NPE风险
        npe_detector = NPERiskDetector()
        npe_result = await npe_detector.detect(
            claims=claims,
            assignee_type=assignee_type or "unknown",
        )

        # 软件专利风险
        software_analyzer = SoftwarePatentRiskAnalyzer()
        software_result = await software_analyzer.analyze(
            claims=claims,
            cpc_code=cpc_code or "",
        )

        # 综合风险等级
        overall_risk = "low"
        if npe_result.risk_level == "high" or software_result.risk_level == "high":
            overall_risk = "high"
        elif npe_result.risk_level == "medium" or software_result.risk_level == "medium":
            overall_risk = "medium"

        # 合并缓解建议
        suggestions = list(dict.fromkeys(
            npe_result.mitigation_suggestions + software_result.suggestions
        ))[:5]

        return RiskAssessmentResponse(
            npe_risk=npe_result.to_dict(),
            software_patent_risk=software_result.to_dict(),
            overall_risk_level=overall_risk,
            mitigation_suggestions=suggestions,
        )

    except Exception as e:
        logger.error(f"风险评估失败: {e}")
        raise HTTPException(status_code=500, detail=f"风险评估失败: {str(e)}") from e


@router.get("/stats")
async def get_service_stats():
    """
    获取专利AI服务统计信息
    """
    try:
        from core.patent.ai_services import (
            ClaimReviser,
            EnhancedPatentQualityScorer,
            InvalidityPredictor,
            PatentClassifier,
        )

        classifier = PatentClassifier()
        reviser = ClaimReviser()
        predictor = InvalidityPredictor()
        scorer = EnhancedPatentQualityScorer()

        return {
            "classifier": classifier.get_stats(),
            "reviser": reviser.get_stats(),
            "predictor": predictor.get_stats(),
            "scorer": scorer.get_stats(),
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return {"error": str(e)}


# ========== OpenClaw 9阶段撰写API ==========

@router.post("/draft/full", response_model=DraftFullSpecResponse)
async def draft_full_specification(request: DraftFullSpecRequest):
    """
    完整9阶段专利说明书撰写（OpenClaw集成）

    **9阶段流程**:
    - Phase 0: 发明理解 - 解析技术交底书
    - Phase 1: 现有技术检索 - 检索对比文件
    - Phase 2: 对比分析 - 分析差异点
    - Phase 3: 发明点确定 - 确定保护策略
    - Phase 4: 说明书撰写 - 撰写各章节
    - Phase 5: 权利要求撰写 - 生成权利要求
    - Phase 6: 审查员模拟 - 自我审查
    - Phase 7: 修改完善 - 基于审查修改
    - Phase 8: 最终确认 - 输出完整文件

    **特性**:
    - 自动审查员模拟（Phase 6）
    - P0/P1/P2优先级问题分类
    - 授权概率估算
    - 长任务状态持久化

    **响应示例**:
    ```json
    {
        "task_id": "CASE-2026-001",
        "status": "completed",
        "current_phase": 8,
        "examiner_report": {
            "overall_risk": "low",
            "authorization_probability": 0.85,
            "p0_count": 0,
            "p1_count": 2,
            "p2_count": 3
        }
    }
    ```
    """
    import time

    time.time()
    task_id = f"CASE-{int(time.time() * 1000)}"

    try:
        from core.patent.ai_services.autospec_drafter import AutoSpecDrafter

        # 创建撰写器实例
        drafter = AutoSpecDrafter(
            llm_manager=None,  # 使用默认配置
            storage_dir="cases"
        )

        # 执行完整9阶段流程
        result = await drafter.draft_specification_full(
            disclosure=request.disclosure,
            task_id=task_id,
            client=request.client,
            invention_type=None,  # 自动检测
            drawing_paths=request.drawing_paths,
            prior_art=request.prior_art,
            enable_examiner_simulation=request.enable_examiner_simulation,
            max_iterations=request.max_iterations
        )

        # 构建响应
        response = DraftFullSpecResponse(
            task_id=result.task_id,
            status=result.status,
            current_phase=result.current_phase,
            phases_completed=result.phases_completed,
            processing_time_ms=result.processing_time_ms,
            notes=result.notes
        )

        if result.draft:
            response.invention_title = result.draft.invention_title
            response.claims_count = len(result.draft.claims) if result.draft.claims else 0
            full_spec = result.draft.get_full_specification()
            response.word_count = len(full_spec) if full_spec else 0
            response.full_specification = full_spec

        if result.examiner_report:
            response.examiner_report = ExaminerReportResponse(
                overall_risk=result.examiner_report.overall_risk,
                authorization_probability=result.examiner_report.authorization_probability,
                p0_count=result.examiner_report.p0_count,
                p1_count=result.examiner_report.p1_count,
                p2_count=result.examiner_report.p2_count,
                issues=[
                    ReviewIssueResponse(
                        issue_id=issue.issue_id,
                        priority=issue.priority,
                        location=issue.location,
                        description=issue.description,
                        legal_basis=issue.legal_basis,
                        suggestion=issue.suggestion
                    )
                    for issue in result.examiner_report.issues
                ],
                summary=result.examiner_report.summary
            )

        return response

    except Exception as e:
        logger.error(f"完整说明书撰写失败: {e}")
        raise HTTPException(status_code=500, detail=f"撰写失败: {str(e)}") from e


@router.post("/draft/review", response_model=ExaminerReportResponse)
async def review_specification_quality(
    specification: dict,
    claims: dict,
    prior_art: list[dict] | None = None
):
    """
    说明书质量审查（Phase 6独立调用）

    基于专利法条款进行质量审查：
    - A22.2 新颖性检查
    - A22.3 创造性检查
    - A26.3 公开充分性检查
    - A26.4 权利要求清楚性和支持性检查

    **问题优先级**:
    - P0: 阻断性问题，必须修改
    - P1: 重要问题，建议修改
    - P2: 可选优化
    """
    try:
        from core.patent.specification_quality_reviewer import SpecificationQualityReviewer

        reviewer = SpecificationQualityReviewer()
        report = reviewer.review(specification, claims, prior_art)

        return ExaminerReportResponse(
            overall_risk=report.overall_risk.value,
            authorization_probability=report.authorization_probability,
            p0_count=report.p0_count,
            p1_count=report.p1_count,
            p2_count=report.p2_count,
            issues=[
                ReviewIssueResponse(
                    issue_id=issue.issue_id,
                    priority=issue.priority.value,
                    location=issue.location,
                    description=issue.description,
                    legal_basis=issue.legal_basis,
                    suggestion=issue.suggestion
                )
                for issue in report.issues
            ],
            summary=report.summary
        )

    except Exception as e:
        logger.error(f"质量审查失败: {e}")
        raise HTTPException(status_code=500, detail=f"审查失败: {str(e)}") from e


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: str | None = Query(None, description="筛选状态"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    获取任务列表

    **状态筛选**:
    - pending: 待处理
    - in_progress: 进行中
    - paused: 已暂停
    - completed: 已完成
    - failed: 失败
    """
    try:
        from core.patent.task_state_manager import TaskStateManager

        manager = TaskStateManager()
        tasks = manager.list_tasks(status=status)

        return TaskListResponse(
            tasks=tasks[:limit],
            total=len(tasks)
        )

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}") from e


@router.get("/tasks/{task_id}", response_model=TaskProgressResponse)
async def get_task_progress(task_id: str):
    """
    获取任务进度详情

    返回任务当前状态、阶段进度、时间信息等
    """
    try:
        from core.patent.task_state_manager import TaskStateManager

        manager = TaskStateManager()
        progress = manager.get_progress(task_id)

        if "error" in progress:
            raise HTTPException(status_code=404, detail=progress["error"])

        return TaskProgressResponse(**progress)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务进度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}") from e


@router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str, reason: str = Query("", description="暂停原因")):
    """
    暂停任务

    任务状态将保存，可通过 /resume 恢复
    """
    try:
        from core.patent.task_state_manager import TaskStateManager

        manager = TaskStateManager()
        result = manager.pause_task(task_id, reason)

        if result is None:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "task_id": task_id,
            "status": "paused",
            "message": "任务已暂停",
            "resume_endpoint": f"/api/v2/patent/tasks/{task_id}/resume"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"暂停失败: {str(e)}") from e


@router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """
    恢复暂停的任务

    从上次中断的阶段继续执行
    """
    try:
        from core.patent.task_state_manager import TaskStateManager

        manager = TaskStateManager()
        result = manager.resume_task(task_id)

        if result is None:
            raise HTTPException(status_code=404, detail="任务不存在或无法恢复")

        return {
            "task_id": task_id,
            "status": "in_progress",
            "message": "任务已恢复",
            "current_phase": result.current_phase
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}") from e


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """
    删除任务

    **警告**: 此操作不可恢复
    """
    try:
        from core.patent.task_state_manager import TaskStateManager

        manager = TaskStateManager()
        success = manager.delete_task(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "task_id": task_id,
            "status": "deleted",
            "message": "任务已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}") from e


# ========== 注册函数 ==========

def register_patent_ai_routes(app):
    """注册专利AI服务路由"""
    app.include_router(router)
    logger.info("✅ 专利AI服务API已注册 (v2.0.0)")
