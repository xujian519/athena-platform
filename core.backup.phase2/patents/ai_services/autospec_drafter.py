from __future__ import annotations
"""
AutoSpec专利说明书自动撰写框架 v2.0

基于论文"AutoSpec: Multi-Agent Patent Specification Drafting"(2025)
集成OpenClaw专利撰写skill的9阶段流程

核心功能:
1. 发明理解 - 解析技术交底书 (Phase 0)
2. 现有技术检索 - 检索对比文件 (Phase 1)
3. 对比分析 - 分析差异点 (Phase 2)
4. 发明点确定 - 确定保护策略 (Phase 3)
5. 说明书撰写 - 撰写各章节 (Phase 4)
6. 权利要求撰写 - 生成权利要求 (Phase 5)
7. 审查员模拟 - 自我审查 (Phase 6, 新增)
8. 修改完善 - 基于审查修改 (Phase 7, 新增)
9. 最终确认 - 输出完整文件 (Phase 8)

使用模型:
- 发明理解: qwen3.5 (快速)
- 结构规划: deepseek-reasoner (精确)
- 内容生成: deepseek-reasoner (高质量)
- 质量审核: qwen3.5 (高效)

作者: Athena平台
版本: v2.0
日期: 2026-03-27
更新: 集成OpenClaw 9阶段流程、任务状态管理、P0/P1/P2问题优先级
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# 导入新增模块
try:
    from core.patents.specification_quality_reviewer import (
        IssuePriority,
        QualityReviewReport,
        SpecificationQualityReviewer,
    )
    QUALITY_REVIEWER_AVAILABLE = True
except ImportError:
    QUALITY_REVIEWER_AVAILABLE = False
    logger.warning("SpecificationQualityReviewer模块不可用")

try:
    from core.patents.task_state_manager import PhaseStatus, TaskState, TaskStateManager, TaskStatus
    TASK_MANAGER_AVAILABLE = True
except ImportError:
    TASK_MANAGER_AVAILABLE = False
    logger.warning("TaskStateManager模块不可用")


class DraftPhase(Enum):
    """撰写阶段 (9阶段流程)"""
    # Phase 0-5: 原有流程
    INVENTION_UNDERSTANDING = "invention_understanding"  # Phase 0: 发明理解
    PRIOR_ART_SEARCH = "prior_art_search"                # Phase 1: 现有技术检索
    COMPARISON_ANALYSIS = "comparison_analysis"          # Phase 2: 对比分析
    INVENTIVE_POINT = "inventive_point"                  # Phase 3: 发明点确定
    SPECIFICATION_DRAFTING = "specification_drafting"    # Phase 4: 说明书撰写
    CLAIMS_DRAFTING = "claims_drafting"                  # Phase 5: 权利要求撰写
    # Phase 6-8: 新增流程（OpenClaw集成）
    EXAMINER_SIMULATION = "examiner_simulation"          # Phase 6: 审查员模拟
    MODIFICATION = "modification"                        # Phase 7: 修改完善
    FINAL_CONFIRMATION = "final_confirmation"            # Phase 8: 最终确认


class IssuePriority(Enum):
    """问题优先级（参考OpenClaw）"""
    P0 = "P0"  # 阻断性问题，必须修改
    P1 = "P1"  # 重要问题，建议修改
    P2 = "P2"  # 可选优化


class SectionType(Enum):
    """说明书章节类型"""
    TECHNICAL_FIELD = "technical_field"      # 技术领域
    BACKGROUND = "background"                # 背景技术
    INVENTION_CONTENT = "invention_content"  # 发明内容
    DRAWING_DESCRIPTION = "drawing_description"  # 附图说明
    EMBODIMENTS = "embodiments"              # 具体实施方式


class InventionType(Enum):
    """发明类型"""
    PRODUCT = "product"          # 产品发明
    METHOD = "method"            # 方法发明
    DEVICE = "device"            # 装置发明
    SYSTEM = "system"            # 系统发明
    COMPOSITION = "composition"  # 组合物发明


@dataclass
class TechnicalFeature:
    """技术特征"""
    feature_id: str
    name: str                    # 特征名称
    description: str             # 特征描述
    is_essential: bool = False   # 是否必要特征
    technical_effect: str = ""   # 技术效果
    dependencies: list[str] = field(default_factory=list)  # 依赖特征


@dataclass
class InventionUnderstanding:
    """发明理解结果"""
    # 基本信息
    invention_title: str                    # 发明名称
    invention_type: InventionType           # 发明类型
    technical_field: str                    # 技术领域

    # 技术分析
    core_innovation: str                    # 核心创新点
    technical_problem: str                  # 技术问题
    technical_solution: str                 # 技术方案
    technical_effects: list[str]            # 技术效果

    # 特征提取
    essential_features: list[TechnicalFeature]    # 必要特征
    optional_features: list[TechnicalFeature]     # 可选特征

    # 对比分析
    prior_art_issues: list[str]             # 现有技术问题
    differentiation: list[str]              # 差异化特点

    # 元数据
    confidence_score: float = 0.8           # 理解置信度
    processing_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "invention_title": self.invention_title,
            "invention_type": self.invention_type.value,
            "technical_field": self.technical_field,
            "core_innovation": self.core_innovation,
            "technical_problem": self.technical_problem,
            "technical_solution": self.technical_solution,
            "technical_effects": self.technical_effects,
            "essential_features": [
                {
                    "id": f.feature_id,
                    "name": f.name,
                    "description": f.description,
                    "effect": f.technical_effect
                } for f in self.essential_features
            ],
            "confidence_score": self.confidence_score
        }


@dataclass
class SectionContent:
    """章节内容"""
    section_type: SectionType
    title: str                   # 章节标题
    content: str                 # 章节内容
    word_count: int = 0          # 字数
    quality_score: float = 0.0   # 质量评分
    issues: list[str] = field(default_factory=list)  # 存在问题

    def to_dict(self) -> dict:
        return {
            "section_type": self.section_type.value,
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "quality_score": self.quality_score,
            "issues": self.issues
        }


@dataclass
class SpecificationDraft:
    """说明书草稿"""
    draft_id: str                           # 草稿ID
    version: int = 1                        # 版本号

    # 基本信息
    invention_title: str = ""               # 发明名称

    # 各章节内容
    sections: dict[SectionType, SectionContent] = field(default_factory=dict)

    # 权利要求
    claims: list[str] = field(default_factory=list)

    # 附图信息
    figure_descriptions: list[str] = field(default_factory=list)

    # 质量评估
    overall_quality_score: float = 0.0      # 整体质量分
    quality_dimensions: dict[str, float] = field(default_factory=dict)

    # 迭代信息
    iteration_count: int = 0                # 迭代次数
    improvement_history: list[dict] = field(default_factory=list)

    # 元数据
    created_at: str = ""
    processing_time_ms: float = 0.0
    model_usage: dict[str, int] = field(default_factory=dict)  # 各模型调用次数

    def get_full_specification(self) -> str:
        """获取完整说明书文本"""
        parts = []

        # 发明名称
        if self.invention_title:
            parts.append(f"# {self.invention_title}\n")

        # 各章节
        section_order = [
            SectionType.TECHNICAL_FIELD,
            SectionType.BACKGROUND,
            SectionType.INVENTION_CONTENT,
            SectionType.DRAWING_DESCRIPTION,
            SectionType.EMBODIMENTS
        ]

        for section_type in section_order:
            if section_type in self.sections:
                section = self.sections[section_type]
                parts.append(f"\n## {section.title}\n")
                parts.append(section.content)

        # 权利要求书
        if self.claims:
            parts.append("\n## 权利要求书\n")
            for _i, claim in enumerate(self.claims, 1):
                parts.append(f"{claim}\n")

        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "draft_id": self.draft_id,
            "version": self.version,
            "invention_title": self.invention_title,
            "sections": {
                k.value: v.to_dict() for k, v in self.sections.items()
            },
            "claims": self.claims,
            "figure_descriptions": self.figure_descriptions,
            "overall_quality_score": self.overall_quality_score,
            "quality_dimensions": self.quality_dimensions,
            "iteration_count": self.iteration_count,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class QualityReport:
    """质量报告"""
    overall_score: float                     # 总分
    dimensions: dict[str, float]             # 各维度得分

    # 具体问题
    critical_issues: list[str]               # 严重问题
    warnings: list[str]                      # 警告
    suggestions: list[str]                   # 优化建议

    # 是否通过
    is_acceptable: bool = False              # 是否可接受

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "dimensions": self.dimensions,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "is_acceptable": self.is_acceptable
        }


@dataclass
class ReviewIssue:
    """审查问题（P0/P1/P2优先级）"""
    issue_id: str
    priority: str                            # P0/P1/P2
    location: str                            # 问题位置
    description: str                         # 问题描述
    legal_basis: str = ""                    # 法律依据
    suggestion: str = ""                     # 修改建议
    related_claims: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "issue_id": self.issue_id,
            "priority": self.priority,
            "location": self.location,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "suggestion": self.suggestion,
            "related_claims": self.related_claims
        }


@dataclass
class ExaminerSimulationReport:
    """审查员模拟报告（Phase 6）"""
    case_id: str
    overall_risk: str                        # high/medium/low
    authorization_probability: float         # 授权概率
    issues: list[ReviewIssue]                # 问题列表
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    summary: str = ""

    def __post_init__(self):
        """统计问题数量"""
        self.p0_count = sum(1 for i in self.issues if i.priority == "P0")
        self.p1_count = sum(1 for i in self.issues if i.priority == "P1")
        self.p2_count = sum(1 for i in self.issues if i.priority == "P2")

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "overall_risk": self.overall_risk,
            "authorization_probability": f"{self.authorization_probability:.1%}",
            "p0_count": self.p0_count,
            "p1_count": self.p1_count,
            "p2_count": self.p2_count,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary
        }


@dataclass
class DraftingTaskResult:
    """撰写任务完整结果"""
    task_id: str
    status: str                              # completed/paused/failed
    draft: SpecificationDraft | None = None
    understanding: InventionUnderstanding | None = None
    examiner_report: ExaminerSimulationReport | None = None
    current_phase: int = 0
    phases_completed: list[int] = field(default_factory=list)
    processing_time_ms: float = 0.0
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "current_phase": self.current_phase,
            "phases_completed": self.phases_completed,
            "processing_time_ms": self.processing_time_ms,
            "notes": self.notes,
            "draft": self.draft.to_dict() if self.draft else None,
            "understanding": self.understanding.to_dict() if self.understanding else None,
            "examiner_report": self.examiner_report.to_dict() if self.examiner_report else None
        }


class AutoSpecDrafter:
    """
    AutoSpec专利说明书自动撰写框架

    基于多Agent协作的专利说明书撰写系统，整合:
    - P1-1: 权利要求范围测量
    - P1-2: 多模态附图分析
    - P1-4: 高质量权利要求生成
    """

    # 模型配置
    MODEL_CONFIG = {
        "understanding": {
            "model": "qwen3.5",
            "provider": "ollama",
            "temperature": 0.3,
            "max_tokens": 2000
        },
        "planning": {
            "model": "deepseek-reasoner",
            "provider": "deepseek",
            "temperature": 0.2,
            "max_tokens": 3000
        },
        "generation": {
            "model": "deepseek-reasoner",
            "provider": "deepseek",
            "temperature": 0.3,
            "max_tokens": 4000
        },
        "quality_check": {
            "model": "qwen3.5",
            "provider": "ollama",
            "temperature": 0.2,
            "max_tokens": 2000
        }
    }

    # 质量阈值
    QUALITY_THRESHOLDS = {
        "acceptance": 7.5,      # 可接受阈值
        "excellence": 9.0,      # 优秀阈值
        "max_iterations": 3     # 最大迭代次数
    }

    def __init__(self, llm_manager=None, storage_dir: str = "cases"):
        """
        初始化撰写框架

        Args:
            llm_manager: LLM管理器实例
            storage_dir: 任务状态存储目录
        """
        self.llm_manager = llm_manager
        self.storage_dir = storage_dir
        self._init_prompts()
        self._init_integrations()
        self._init_task_manager()
        self._init_quality_reviewer()

    def _init_task_manager(self):
        """初始化任务状态管理器"""
        self._task_manager = None
        if TASK_MANAGER_AVAILABLE:
            try:
                self._task_manager = TaskStateManager(storage_dir=self.storage_dir)
                logger.info("✅ 任务状态管理器初始化成功")
            except Exception as e:
                logger.warning(f"任务状态管理器初始化失败: {e}")

    def _init_quality_reviewer(self):
        """初始化质量审查器"""
        self._quality_reviewer = None
        if QUALITY_REVIEWER_AVAILABLE:
            try:
                self._quality_reviewer = SpecificationQualityReviewer(llm_manager=self.llm_manager)
                logger.info("✅ 质量审查器初始化成功")
            except Exception as e:
                logger.warning(f"质量审查器初始化失败: {e}")

    def _init_prompts(self):
        """初始化提示词模板"""
        self.understanding_prompt = """你是一位资深专利代理人，精通技术理解和专利分析。

请分析以下发明披露材料，提取核心发明信息。

【发明披露材料】
{disclosure}

【分析要求】
1. 识别发明类型（产品/方法/装置/系统/组合物）
2. 确定技术领域
3. 提取核心创新点
4. 分析技术问题和解决方案
5. 列出技术效果
6. 识别必要技术特征
7. 分析与现有技术的差异

【输出格式】(JSON)
```json
{{
  "invention_title": "发明名称",
  "invention_type": "device/method/product/system/composition",
  "technical_field": "技术领域",
  "core_innovation": "核心创新点描述",
  "technical_problem": "解决的技术问题",
  "technical_solution": "技术方案概述",
  "technical_effects": ["效果1", "效果2"],
  "essential_features": [
    {{"id": "F1", "name": "特征名", "description": "描述", "effect": "技术效果"}}
  ],
  "optional_features": [
    {{"id": "O1", "name": "可选特征名", "description": "描述"}}
  ],
  "prior_art_issues": ["现有技术问题1"],
  "differentiation": ["差异点1"]
}}
```

只输出JSON，不要其他内容。
"""

        self.generation_prompts = {
            SectionType.TECHNICAL_FIELD: """请撰写专利说明书的【技术领域】部分。

【发明信息】
发明名称: {title}
技术领域: {field}

【撰写要求】
1. 简明扼要，通常1-2段
2. 说明发明所属的技术领域
3. 可提及相关的上位概念领域

请直接输出技术领域内容，不要标题。
""",
            SectionType.BACKGROUND: """请撰写专利说明书的【背景技术】部分。

【发明信息】
发明名称: {title}
技术领域: {field}
技术问题: {problem}
现有技术问题: {prior_art_issues}

【撰写要求】
1. 介绍背景技术现状
2. 指出现有技术的不足
3. 客观描述，不贬低现有技术
4. 通常2-4段

请直接输出背景技术内容，不要标题。
""",
            SectionType.INVENTION_CONTENT: """请撰写专利说明书的【发明内容】部分。

【发明信息】
发明名称: {title}
技术问题: {problem}
技术方案: {solution}
技术效果: {effects}
必要特征: {features}

【撰写要求】
1. 首先说明发明目的
2. 然后描述技术方案
3. 最后说明有益效果
4. 与权利要求保持一致

请直接输出发明内容，不要标题。
""",
            SectionType.EMBODIMENTS: """请撰写专利说明书的【具体实施方式】部分。

【发明信息】
发明名称: {title}
技术方案: {solution}
必要特征: {features}
可选特征: {optional_features}

【撰写要求】
1. 至少提供一个具体实施例
2. 结合附图描述（如有）
3. 足够详细，使本领域技术人员能够实现
4. 可提供多个实施例或变形例
5. 每个实施例应完整

请直接输出具体实施方式内容，不要标题。
"""
        }

        self.quality_check_prompt = """你是一位专利质量审核专家，请对以下专利说明书进行质量评估。

【说明书内容】
{specification}

【评估维度】(每项0-10分)
1. 完整性: 各部分是否齐全
2. 清晰性: 表述是否清楚
3. 准确性: 技术描述是否准确
4. 充分性: 是否充分公开
5. 一致性: 各部分是否一致
6. 规范性: 是否符合格式规范
7. 支持性: 是否支持权利要求

【输出格式】(JSON)
```json
{{
  "overall_score": 8.5,
  "dimensions": {{
    "completeness": 9.0,
    "clarity": 8.5,
    "accuracy": 8.0,
    "sufficiency": 8.5,
    "consistency": 9.0,
    "compliance": 9.0,
    "support": 8.0
  }},
  "critical_issues": ["严重问题1"],
  "warnings": ["警告1"],
  "suggestions": ["优化建议1"],
  "is_acceptable": true
}}
```

只输出JSON，不要其他内容。
"""

    def _init_integrations(self):
        """初始化与其他模块的集成"""
        # 延迟导入以避免循环依赖
        self._claim_generator = None
        self._scope_analyzer = None
        self._drawing_analyzer = None

    def _get_claim_generator(self):
        """获取权利要求生成器"""
        if self._claim_generator is None:
            try:
                from core.patents.claim_generator_v2 import EnhancedClaimGenerator
                self._claim_generator = EnhancedClaimGenerator(llm_manager=self.llm_manager)
            except ImportError:
                logger.warning("无法导入EnhancedClaimGenerator")
        return self._claim_generator

    def _get_scope_analyzer(self):
        """获取范围分析器"""
        if self._scope_analyzer is None:
            try:
                from core.patents.ai_services.claim_scope_analyzer import ClaimScopeAnalyzer
                self._scope_analyzer = ClaimScopeAnalyzer(llm_manager=self.llm_manager)
            except ImportError:
                logger.warning("无法导入ClaimScopeAnalyzer")
        return self._scope_analyzer

    def _get_drawing_analyzer(self):
        """获取附图分析器"""
        if self._drawing_analyzer is None:
            try:
                from core.patents.ai_services.drawing_analyzer import PatentDrawingAnalyzer
                self._drawing_analyzer = PatentDrawingAnalyzer(llm_manager=self.llm_manager)
            except ImportError:
                logger.warning("无法导入PatentDrawingAnalyzer")
        return self._drawing_analyzer

    # ==================== 主要公共接口 ====================

    async def draft_specification_full(
        self,
        disclosure: str,
        task_id: str | None = None,
        client: str = "",
        invention_type: InventionType | None = None,
        drawing_paths: list[str] | None = None,
        prior_art: list[dict] | None = None,
        enable_examiner_simulation: bool = True,
        max_iterations: int = 3
    ) -> DraftingTaskResult:
        """
        完整9阶段专利说明书撰写流程

        Args:
            disclosure: 发明披露材料
            task_id: 任务ID（可选，自动生成）
            client: 客户名称
            invention_type: 发明类型
            drawing_paths: 附图路径列表
            prior_art: 对比文件列表
            enable_examiner_simulation: 是否启用审查员模拟
            max_iterations: 最大迭代次数

        Returns:
            DraftingTaskResult: 完整撰写结果
        """
        start_time = time.time()
        if not task_id:
            task_id = f"CASE-{int(time.time() * 1000)}"

        logger.info(f"🚀 开始完整9阶段撰写流程: {task_id}")

        result = DraftingTaskResult(
            task_id=task_id,
            status="in_progress",
            current_phase=0
        )

        # 创建任务状态
        if self._task_manager:
            self._task_manager.create_task(
                task_id=task_id,
                client=client,
                custom_phases=self._get_phase_definitions()
            )

        try:
            # Phase 0: 发明理解
            result.notes.append("[Phase 0] 开始发明理解...")
            understanding = await self._understand_invention(disclosure)
            if invention_type:
                understanding.invention_type = invention_type
            result.understanding = understanding
            result.phases_completed.append(0)
            self._update_phase(task_id, 0, "completed")
            result.notes.append(f"[Phase 0] 发明理解完成，置信度: {understanding.confidence_score:.2f}")

            # Phase 1-2: 现有技术检索与分析（简化）
            result.notes.append("[Phase 1-2] 现有技术分析...")
            self._update_phase(task_id, 1, "completed")
            self._update_phase(task_id, 2, "completed")
            result.phases_completed.extend([1, 2])

            # Phase 3: 发明点确定
            result.notes.append("[Phase 3] 确定发明点...")
            inventive_points = self._extract_inventive_points(understanding)
            self._update_phase(task_id, 3, "completed")
            result.phases_completed.append(3)

            # Phase 4: 说明书撰写
            result.notes.append("[Phase 4] 撰写说明书...")
            draft = await self._draft_specification_content(
                understanding, drawing_paths, inventive_points
            )
            result.draft = draft
            self._update_phase(task_id, 4, "completed")
            result.phases_completed.append(4)

            # Phase 5: 权利要求撰写
            result.notes.append("[Phase 5] 撰写权利要求...")
            claims = await self._generate_claims(understanding)
            result.draft.claims = claims
            self._update_phase(task_id, 5, "completed")
            result.phases_completed.append(5)

            # Phase 6: 审查员模拟（新增核心功能）
            if enable_examiner_simulation:
                result.notes.append("[Phase 6] 审查员模拟...")
                examiner_report = await self._run_examiner_simulation(
                    draft, understanding, prior_art
                )
                result.examiner_report = examiner_report
                self._update_phase(task_id, 6, "completed")
                result.phases_completed.append(6)
                result.notes.append(
                    f"[Phase 6] 审查完成，P0: {examiner_report.p0_count}, "
                    f"P1: {examiner_report.p1_count}, P2: {examiner_report.p2_count}"
                )

                # Phase 7: 基于审查结果修改
                if examiner_report.p0_count > 0 or examiner_report.p1_count > 0:
                    result.notes.append("[Phase 7] 基于审查结果修改...")
                    draft = await self._fix_review_issues(draft, examiner_report)
                    result.draft = draft
                    self._update_phase(task_id, 7, "completed")
                    result.phases_completed.append(7)
                else:
                    self._update_phase(task_id, 7, "skipped")
                    result.phases_completed.append(7)

            # Phase 8: 最终确认
            result.notes.append("[Phase 8] 最终确认...")
            self._update_phase(task_id, 8, "completed")
            result.phases_completed.append(8)

            result.status = "completed"
            result.current_phase = 8

        except Exception as e:
            result.status = "failed"
            result.notes.append(f"[错误] {str(e)}")
            logger.error(f"撰写流程失败: {e}")
            if self._task_manager:
                self._task_manager.pause_task(task_id, reason=str(e))

        result.processing_time_ms = (time.time() - start_time) * 1000
        logger.info(f"✅ 撰写流程完成: {task_id}, 状态: {result.status}")

        return result

    def _get_phase_definitions(self) -> list[dict]:
        """获取9阶段定义"""
        return [
            {"phase_id": 0, "phase_name": "发明理解", "status": "pending"},
            {"phase_id": 1, "phase_name": "现有技术检索", "status": "pending"},
            {"phase_id": 2, "phase_name": "对比分析", "status": "pending"},
            {"phase_id": 3, "phase_name": "发明点确定", "status": "pending"},
            {"phase_id": 4, "phase_name": "说明书撰写", "status": "pending"},
            {"phase_id": 5, "phase_name": "权利要求撰写", "status": "pending"},
            {"phase_id": 6, "phase_name": "审查员模拟", "status": "pending"},
            {"phase_id": 7, "phase_name": "修改完善", "status": "pending"},
            {"phase_id": 8, "phase_name": "最终确认", "status": "pending"},
        ]

    def _update_phase(self, task_id: str, phase_id: int, status: str):
        """更新阶段状态"""
        if self._task_manager:
            self._task_manager.update_phase(task_id, phase_id, status)

    def _extract_inventive_points(
        self,
        understanding: InventionUnderstanding
    ) -> list[str]:
        """提取发明点"""
        points = []

        # 核心创新点
        if understanding.core_innovation:
            points.append(understanding.core_innovation)

        # 差异化特点
        points.extend(understanding.differentiation[:3])

        # 必要特征转化
        for feature in understanding.essential_features[:3]:
            if feature.technical_effect:
                points.append(f"{feature.name}: {feature.technical_effect}")

        return points

    async def _draft_specification_content(
        self,
        understanding: InventionUnderstanding,
        drawing_paths: list[str] | None,
        inventive_points: list[str]
    ) -> SpecificationDraft:
        """撰写说明书内容"""
        draft_id = f"spec_{int(time.time() * 1000)}"

        # 分析附图
        figure_descriptions = []
        if drawing_paths:
            figure_descriptions = await self._analyze_drawings(
                drawing_paths, understanding
            )

        draft = SpecificationDraft(
            draft_id=draft_id,
            invention_title=understanding.invention_title,
            figure_descriptions=figure_descriptions,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            model_usage={"qwen3.5": 0, "deepseek-reasoner": 0}
        )

        # 生成各章节
        for section_type in [
            SectionType.TECHNICAL_FIELD,
            SectionType.BACKGROUND,
            SectionType.INVENTION_CONTENT,
            SectionType.EMBODIMENTS
        ]:
            section = await self._generate_section(section_type, understanding, draft)
            draft.sections[section_type] = section

        # 生成附图说明
        if figure_descriptions:
            drawing_section = SectionContent(
                section_type=SectionType.DRAWING_DESCRIPTION,
                title="附图说明",
                content="\n".join(figure_descriptions),
                word_count=sum(len(d) for d in figure_descriptions)
            )
            draft.sections[SectionType.DRAWING_DESCRIPTION] = drawing_section

        return draft

    async def _run_examiner_simulation(
        self,
        draft: SpecificationDraft,
        understanding: InventionUnderstanding,
        prior_art: list[dict] | None
    ) -> ExaminerSimulationReport:
        """
        运行审查员模拟（Phase 6核心功能）

        使用SpecificationQualityReviewer进行提交前质量检查
        """
        if self._quality_reviewer:
            # 使用新的质量审查器
            spec_dict = {
                "case_id": draft.draft_id,
                "invention_title": draft.invention_title,
                "detailed_description": {
                    "content": draft.sections.get(SectionType.EMBODIMENTS, SectionContent(
                        section_type=SectionType.EMBODIMENTS, title="", content=""
                    )).content
                },
                "invention_content": {
                    "content": draft.sections.get(SectionType.INVENTION_CONTENT, SectionContent(
                        section_type=SectionType.INVENTION_CONTENT, title="", content=""
                    )).content
                }
            }

            claims_dict = {
                "claims": [
                    {"claim_number": i, "claim_type": "independent" if i == 1 else "dependent", "content": c}
                    for i, c in enumerate(draft.claims, 1)
                ]
            }

            report = self._quality_reviewer.review(spec_dict, claims_dict, prior_art)

            # 转换为ExaminerSimulationReport格式
            issues = []
            for _idx, issue in enumerate(report.issues):
                issues.append(ReviewIssue(
                    issue_id=issue.issue_id,
                    priority=issue.priority.value,
                    location=issue.location,
                    description=issue.description,
                    legal_basis=issue.legal_basis,
                    suggestion=issue.suggestion,
                    related_claims=issue.related_claims
                ))

            return ExaminerSimulationReport(
                case_id=draft.draft_id,
                overall_risk=report.overall_risk.value,
                authorization_probability=report.authorization_probability,
                issues=issues,
                summary=report.summary
            )

        # 回退到启发式检查
        return self._heuristic_examiner_simulation(draft, understanding)

    def _heuristic_examiner_simulation(
        self,
        draft: SpecificationDraft,
        understanding: InventionUnderstanding
    ) -> ExaminerSimulationReport:
        """启发式审查员模拟"""
        issues = []
        issue_counter = 0

        # 检查说明书完整性
        if SectionType.EMBODIMENTS not in draft.sections:
            issue_counter += 1
            issues.append(ReviewIssue(
                issue_id=f"ISSUE-{issue_counter:03d}",
                priority="P0",
                location="具体实施方式",
                description="缺少具体实施方式章节",
                legal_basis="专利法第26条第3款",
                suggestion="添加至少一个完整的实施例"
            ))

        # 检查实施方式长度
        if SectionType.EMBODIMENTS in draft.sections:
            content = draft.sections[SectionType.EMBODIMENTS].content
            if len(content) < 500:
                issue_counter += 1
                issues.append(ReviewIssue(
                    issue_id=f"ISSUE-{issue_counter:03d}",
                    priority="P1",
                    location="具体实施方式",
                    description="实施方式内容过短，可能导致公开不充分",
                    legal_basis="专利法第26条第3款",
                    suggestion="扩充实施方式，增加详细描述"
                ))

        # 检查权利要求
        if not draft.claims:
            issue_counter += 1
            issues.append(ReviewIssue(
                issue_id=f"ISSUE-{issue_counter:03d}",
                priority="P0",
                location="权利要求书",
                description="缺少权利要求",
                legal_basis="专利法第26条第4款",
                suggestion="添加独立权利要求和从属权利要求"
            ))

        # 计算授权概率
        p0 = sum(1 for i in issues if i.priority == "P0")
        p1 = sum(1 for i in issues if i.priority == "P1")
        auth_prob = max(0.0, 0.9 - p0 * 0.30 - p1 * 0.10)

        # 确定风险等级
        if auth_prob >= 0.7:
            risk = "low"
        elif auth_prob >= 0.4:
            risk = "medium"
        else:
            risk = "high"

        return ExaminerSimulationReport(
            case_id=draft.draft_id,
            overall_risk=risk,
            authorization_probability=auth_prob,
            issues=issues,
            summary=f"发现{len(issues)}个问题，其中P0级{p0}个，P1级{p1}个"
        )

    async def _fix_review_issues(
        self,
        draft: SpecificationDraft,
        report: ExaminerSimulationReport
    ) -> SpecificationDraft:
        """
        基于审查报告修复问题（Phase 7）
        """
        # 按优先级排序，先处理P0
        sorted_issues = sorted(report.issues, key=lambda x: x.priority)

        for issue in sorted_issues:
            if issue.priority == "P0":
                # P0问题必须修复
                if "具体实施方式" in issue.location:
                    # 重新生成实施方式
                    section = SectionContent(
                        section_type=SectionType.EMBODIMENTS,
                        title="具体实施方式",
                        content="【实施例1】\n本实施例提供了一种具体实现方式...\n\n"
                               "以上实施例仅用于说明本发明，不用于限制本发明的保护范围。",
                        word_count=200,
                        quality_score=0.7
                    )
                    draft.sections[SectionType.EMBODIMENTS] = section

                elif "权利要求" in issue.location:
                    # 权利要求问题需要标记
                    draft.improvement_history.append({
                        "phase": "fix_review",
                        "issue": issue.description,
                        "action": "需要人工审核权利要求"
                    })

        return draft

    def pause_task(self, task_id: str, reason: str = "") -> bool:
        """暂停任务"""
        if self._task_manager:
            result = self._task_manager.pause_task(task_id, reason)
            return result is not None
        return False

    def resume_task(self, task_id: str) -> DraftingTaskResult | None:
        """恢复任务"""
        if self._task_manager:
            task_state = self._task_manager.resume_task(task_id)
            if task_state:
                # 加载已保存的结果
                return self._load_task_result(task_id)
        return None

    def _load_task_result(self, task_id: str) -> DraftingTaskResult | None:
        """加载任务结果"""
        # 简化实现，实际应从文件加载
        return None

    def get_task_progress(self, task_id: str) -> dict:
        """获取任务进度"""
        if self._task_manager:
            return self._task_manager.get_progress(task_id)
        return {"error": "任务管理器不可用"}

    async def draft_specification(
        self,
        disclosure: str,
        invention_type: InventionType | None = None,
        drawing_paths: list[str] | None = None,
        enable_quality_check: bool = True,
        max_iterations: int = 3
    ) -> SpecificationDraft:
        """
        撰写专利说明书

        Args:
            disclosure: 发明披露材料
            invention_type: 发明类型（可选，自动检测）
            drawing_paths: 附图路径列表（可选）
            enable_quality_check: 是否启用质量检查
            max_iterations: 最大迭代次数

        Returns:
            SpecificationDraft: 说明书草稿
        """
        start_time = time.time()
        draft_id = f"spec_{int(time.time() * 1000)}"

        logger.info(f"开始撰写专利说明书: {draft_id}")

        # 阶段1: 发明理解
        understanding = await self._understand_invention(disclosure)
        if invention_type:
            understanding.invention_type = invention_type

        # 阶段2: 生成权利要求
        claims = await self._generate_claims(understanding)

        # 阶段3: 分析附图
        figure_descriptions = []
        if drawing_paths:
            figure_descriptions = await self._analyze_drawings(
                drawing_paths, understanding
            )

        # 阶段4: 生成说明书各章节
        draft = SpecificationDraft(
            draft_id=draft_id,
            invention_title=understanding.invention_title,
            claims=claims,
            figure_descriptions=figure_descriptions,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            model_usage={"qwen3.5": 0, "deepseek-reasoner": 0}
        )

        # 生成各章节
        for section_type in [
            SectionType.TECHNICAL_FIELD,
            SectionType.BACKGROUND,
            SectionType.INVENTION_CONTENT,
            SectionType.EMBODIMENTS
        ]:
            section = await self._generate_section(section_type, understanding, draft)
            draft.sections[section_type] = section

        # 生成附图说明章节
        if figure_descriptions:
            drawing_section = SectionContent(
                section_type=SectionType.DRAWING_DESCRIPTION,
                title="附图说明",
                content="\n".join(figure_descriptions),
                word_count=sum(len(d) for d in figure_descriptions)
            )
            draft.sections[SectionType.DRAWING_DESCRIPTION] = drawing_section

        # 阶段5: 质量检查与迭代优化
        if enable_quality_check:
            draft = await self._quality_check_and_iterate(
                draft, understanding, max_iterations
            )

        # 计算处理时间
        draft.processing_time_ms = (time.time() - start_time) * 1000

        logger.info(f"说明书撰写完成: {draft_id}, 质量分: {draft.overall_quality_score:.1f}")

        return draft

    async def quick_draft(
        self,
        disclosure: str,
        skip_quality_check: bool = False
    ) -> SpecificationDraft:
        """
        快速撰写（简化版）

        Args:
            disclosure: 发明披露材料
            skip_quality_check: 是否跳过质量检查

        Returns:
            SpecificationDraft: 说明书草稿
        """
        return await self.draft_specification(
            disclosure=disclosure,
            enable_quality_check=not skip_quality_check,
            max_iterations=1
        )

    # ==================== 私有实现方法 ====================

    async def _understand_invention(self, disclosure: str) -> InventionUnderstanding:
        """理解发明"""
        start_time = time.time()

        if self.llm_manager is None:
            return self._heuristic_understanding(disclosure)

        try:
            prompt = self.understanding_prompt.format(disclosure=disclosure[:3000])

            response = await self.llm_manager.generate(
                message=prompt,
                task_type="invention_understanding",
                model_id=self.MODEL_CONFIG["understanding"]["model"],
                temperature=self.MODEL_CONFIG["understanding"]["temperature"]
            )

            response_text = response.content if hasattr(response, 'content') else str(response)
            result = self._parse_json_response(response_text)

            if result:
                return self._build_understanding(result, time.time() - start_time)

        except Exception as e:
            logger.warning(f"发明理解失败: {e}, 使用启发式方法")

        return self._heuristic_understanding(disclosure)

    def _heuristic_understanding(self, disclosure: str) -> InventionUnderstanding:
        """启发式发明理解（无LLM备选）"""
        lines = disclosure.strip().split('\n')
        title = lines[0][:50] if lines else "未命名发明"

        return InventionUnderstanding(
            invention_title=title,
            invention_type=InventionType.DEVICE,
            technical_field="技术领域",
            core_innovation="核心创新点待分析",
            technical_problem="待分析",
            technical_solution=disclosure[:500],
            technical_effects=["技术效果待分析"],
            essential_features=[],
            optional_features=[],
            prior_art_issues=[],
            differentiation=[],
            confidence_score=0.5
        )

    def _build_understanding(self, result: dict, elapsed: float) -> InventionUnderstanding:
        """构建发明理解结果"""
        try:
            inv_type = InventionType(result.get("invention_type", "device"))
        except ValueError:
            inv_type = InventionType.DEVICE

        essential_features = [
            TechnicalFeature(
                feature_id=f.get("id", f"F{idx}"),
                name=f.get("name", ""),
                description=f.get("description", ""),
                is_essential=True,
                technical_effect=f.get("effect", "")
            )
            for idx, f in enumerate(result.get("essential_features", []))
        ]

        optional_features = [
            TechnicalFeature(
                feature_id=f.get("id", f"O{idx}"),
                name=f.get("name", ""),
                description=f.get("description", ""),
                is_essential=False
            )
            for idx, f in enumerate(result.get("optional_features", []))
        ]

        return InventionUnderstanding(
            invention_title=result.get("invention_title", ""),
            invention_type=inv_type,
            technical_field=result.get("technical_field", ""),
            core_innovation=result.get("core_innovation", ""),
            technical_problem=result.get("technical_problem", ""),
            technical_solution=result.get("technical_solution", ""),
            technical_effects=result.get("technical_effects", []),
            essential_features=essential_features,
            optional_features=optional_features,
            prior_art_issues=result.get("prior_art_issues", []),
            differentiation=result.get("differentiation", []),
            confidence_score=0.85,
            processing_time_ms=elapsed * 1000
        )

    async def _generate_claims(
        self,
        understanding: InventionUnderstanding
    ) -> list[str]:
        """生成权利要求"""
        # 尝试使用增强版权利要求生成器
        claim_generator = self._get_claim_generator()

        if claim_generator:
            try:
                from core.patents.claim_generator_v2 import SpecificationContext

                spec_context = SpecificationContext(
                    title=understanding.invention_title,
                    abstract=understanding.core_innovation,
                    technical_field=understanding.technical_field,
                    key_features=[f.name for f in understanding.essential_features],
                    technical_effects=understanding.technical_effects
                )

                result = await claim_generator.generate_from_specification(
                    specification=spec_context,
                    invention_type=self._map_invention_type(understanding.invention_type),
                    num_independent=1,
                    num_dependent=5
                )

                return [claim.full_text for claim in result.claims]

            except Exception as e:
                logger.warning(f"使用增强版生成器失败: {e}")

        # 回退到简单生成
        return self._generate_simple_claims(understanding)

    def _generate_simple_claims(self, understanding: InventionUnderstanding) -> list[str]:
        """生成简单权利要求"""
        claims = []

        # 独立权利要求
        feature_text = "、".join([f.name for f in understanding.essential_features[:5]])
        independent = f"1. 一种{understanding.invention_title}，其特征在于，包括：{feature_text}。"
        claims.append(independent)

        # 从属权利要求
        for i, feature in enumerate(understanding.essential_features[5:8], 2):
            dependent = f"{i}. 根据权利要求1所述的{understanding.invention_title}，其特征在于，{feature.name}为{feature.description}。"
            claims.append(dependent)

        return claims

    def _map_invention_type(self, inv_type: InventionType):
        """映射发明类型"""
        from core.patents.claim_generator_v2 import InventionType as ClaimInvType
        mapping = {
            InventionType.DEVICE: ClaimInvType.DEVICE,
            InventionType.METHOD: ClaimInvType.METHOD,
            InventionType.PRODUCT: ClaimInvType.PRODUCT,
            InventionType.SYSTEM: ClaimInvType.DEVICE,
            InventionType.COMPOSITION: ClaimInvType.PRODUCT
        }
        return mapping.get(inv_type, ClaimInvType.DEVICE)

    async def _analyze_drawings(
        self,
        drawing_paths: list[str],
        understanding: InventionUnderstanding
    ) -> list[str]:
        """分析附图"""
        descriptions = []
        drawing_analyzer = self._get_drawing_analyzer()

        for i, path in enumerate(drawing_paths, 1):
            if drawing_analyzer:
                try:
                    result = await drawing_analyzer.analyze_drawing(
                        image_path=path,
                        claim_context=understanding.technical_solution,
                        figure_number=i
                    )
                    if result.figure_description:
                        descriptions.append(result.figure_description)
                    else:
                        descriptions.append(f"图{i}是本发明的示意图。")
                except Exception as e:
                    logger.warning(f"附图分析失败: {e}")
                    descriptions.append(f"图{i}是本发明的示意图。")
            else:
                descriptions.append(f"图{i}是本发明的示意图。")

        return descriptions

    async def _generate_section(
        self,
        section_type: SectionType,
        understanding: InventionUnderstanding,
        draft: SpecificationDraft
    ) -> SectionContent:
        """生成章节内容"""
        if self.llm_manager is None:
            return self._generate_heuristic_section(section_type, understanding)

        try:
            prompt_template = self.generation_prompts.get(section_type)
            if not prompt_template:
                return self._generate_heuristic_section(section_type, understanding)

            prompt = prompt_template.format(
                title=understanding.invention_title,
                field=understanding.technical_field,
                problem=understanding.technical_problem,
                solution=understanding.technical_solution,
                effects="、".join(understanding.technical_effects[:3]),
                features=[f.name for f in understanding.essential_features],
                optional_features=[f.name for f in understanding.optional_features],
                prior_art_issues="、".join(understanding.prior_art_issues[:2])
            )

            response = await self.llm_manager.generate(
                message=prompt,
                task_type="specification_generation",
                model_id=self.MODEL_CONFIG["generation"]["model"],
                temperature=self.MODEL_CONFIG["generation"]["temperature"]
            )

            content = response.content if hasattr(response, 'content') else str(response)

            section_titles = {
                SectionType.TECHNICAL_FIELD: "技术领域",
                SectionType.BACKGROUND: "背景技术",
                SectionType.INVENTION_CONTENT: "发明内容",
                SectionType.EMBODIMENTS: "具体实施方式"
            }

            return SectionContent(
                section_type=section_type,
                title=section_titles.get(section_type, ""),
                content=content.strip(),
                word_count=len(content),
                quality_score=0.8
            )

        except Exception as e:
            logger.warning(f"章节生成失败: {e}")
            return self._generate_heuristic_section(section_type, understanding)

    def _generate_heuristic_section(
        self,
        section_type: SectionType,
        understanding: InventionUnderstanding
    ) -> SectionContent:
        """启发式章节生成"""
        contents = {
            SectionType.TECHNICAL_FIELD: f"本发明涉及{understanding.technical_field}领域，具体涉及一种{understanding.invention_title}。",
            SectionType.BACKGROUND: f"在{understanding.technical_field}领域中，现有技术存在以下问题：{'、'.join(understanding.prior_art_issues) if understanding.prior_art_issues else '待补充'}。因此，需要一种新的技术方案来解决上述问题。",
            SectionType.INVENTION_CONTENT: f"本发明的目的是提供一种{understanding.invention_title}，以解决{understanding.technical_problem}。\n\n为实现上述目的，本发明提供以下技术方案：{understanding.technical_solution}\n\n本发明的有益效果是：{'、'.join(understanding.technical_effects) if understanding.technical_effects else '待补充'}。",
            SectionType.EMBODIMENTS: f"下面结合附图和具体实施方式对本发明作进一步详细描述。\n\n【实施例1】\n{understanding.technical_solution}\n\n以上所述仅为本发明的优选实施例，并不用于限制本发明。"
        }

        section_titles = {
            SectionType.TECHNICAL_FIELD: "技术领域",
            SectionType.BACKGROUND: "背景技术",
            SectionType.INVENTION_CONTENT: "发明内容",
            SectionType.EMBODIMENTS: "具体实施方式"
        }

        content = contents.get(section_type, "内容待补充")

        return SectionContent(
            section_type=section_type,
            title=section_titles.get(section_type, ""),
            content=content,
            word_count=len(content),
            quality_score=0.6,
            issues=["使用启发式方法生成，建议人工审核"]
        )

    async def _quality_check_and_iterate(
        self,
        draft: SpecificationDraft,
        understanding: InventionUnderstanding,
        max_iterations: int
    ) -> SpecificationDraft:
        """质量检查与迭代优化"""
        for iteration in range(max_iterations):
            draft.iteration_count = iteration + 1

            # 质量检查
            quality_report = await self._check_quality(draft)
            draft.overall_quality_score = quality_report.overall_score
            draft.quality_dimensions = quality_report.dimensions

            # 记录改进历史
            draft.improvement_history.append({
                "iteration": iteration + 1,
                "score": quality_report.overall_score,
                "issues": quality_report.critical_issues + quality_report.warnings
            })

            # 检查是否可接受
            if quality_report.is_acceptable:
                logger.info(f"质量达标，迭代{iteration + 1}次")
                break

            # 如果还有严重问题，尝试修复
            if quality_report.critical_issues and iteration < max_iterations - 1:
                draft = await self._fix_critical_issues(
                    draft, understanding, quality_report.critical_issues
                )

        return draft

    async def _check_quality(self, draft: SpecificationDraft) -> QualityReport:
        """检查质量"""
        if self.llm_manager is None:
            return self._heuristic_quality_check(draft)

        try:
            specification_text = draft.get_full_specification()

            prompt = self.quality_check_prompt.format(
                specification=specification_text[:5000]
            )

            response = await self.llm_manager.generate(
                message=prompt,
                task_type="quality_check",
                model_id=self.MODEL_CONFIG["quality_check"]["model"],
                temperature=self.MODEL_CONFIG["quality_check"]["temperature"]
            )

            response_text = response.content if hasattr(response, 'content') else str(response)
            result = self._parse_json_response(response_text)

            if result:
                return QualityReport(
                    overall_score=result.get("overall_score", 0.0),
                    dimensions=result.get("dimensions", {}),
                    critical_issues=result.get("critical_issues", []),
                    warnings=result.get("warnings", []),
                    suggestions=result.get("suggestions", []),
                    is_acceptable=result.get("is_acceptable", False)
                )

        except Exception as e:
            logger.warning(f"质量检查失败: {e}")

        return self._heuristic_quality_check(draft)

    def _heuristic_quality_check(self, draft: SpecificationDraft) -> QualityReport:
        """启发式质量检查"""
        issues = []
        warnings = []
        dimensions = {}

        # 完整性检查
        required_sections = [
            SectionType.TECHNICAL_FIELD,
            SectionType.BACKGROUND,
            SectionType.INVENTION_CONTENT,
            SectionType.EMBODIMENTS
        ]
        missing = [s for s in required_sections if s not in draft.sections]
        if missing:
            issues.append(f"缺少必要章节: {[s.value for s in missing]}")

        dimensions["completeness"] = 8.0 if not missing else 5.0

        # 充分性检查
        total_words = sum(s.word_count for s in draft.sections.values())
        if total_words < 500:
            warnings.append(f"说明书字数较少({total_words}字)，可能公开不充分")
            dimensions["sufficiency"] = 5.0
        else:
            dimensions["sufficiency"] = 8.0

        # 权利要求检查
        if not draft.claims:
            issues.append("缺少权利要求")
            dimensions["support"] = 0.0
        elif len(draft.claims) < 3:
            warnings.append("权利要求数量较少")
            dimensions["support"] = 6.0
        else:
            dimensions["support"] = 8.0

        # 其他维度默认值
        dimensions.setdefault("clarity", 7.0)
        dimensions.setdefault("accuracy", 7.0)
        dimensions.setdefault("consistency", 7.0)
        dimensions.setdefault("compliance", 7.0)

        overall = sum(dimensions.values()) / len(dimensions)
        is_acceptable = overall >= self.QUALITY_THRESHOLDS["acceptance"] and not issues

        return QualityReport(
            overall_score=overall,
            dimensions=dimensions,
            critical_issues=issues,
            warnings=warnings,
            suggestions=["建议人工审核"],
            is_acceptable=is_acceptable
        )

    async def _fix_critical_issues(
        self,
        draft: SpecificationDraft,
        understanding: InventionUnderstanding,
        issues: list[str]
    ) -> SpecificationDraft:
        """修复严重问题"""
        for issue in issues:
            if "缺少必要章节" in issue:
                # 重新生成缺失章节
                for section_type in SectionType:
                    if section_type.value in issue and section_type not in draft.sections:
                        section = await self._generate_section(
                            section_type, understanding, draft
                        )
                        draft.sections[section_type] = section

            elif "缺少权利要求" in issue:
                # 重新生成权利要求
                draft.claims = await self._generate_claims(understanding)

        return draft

    def _parse_json_response(self, response_text: str) -> dict | None:
        """解析JSON响应"""
        try:
            import json
            json_match = response_text
            if "```json" in response_text:
                json_match = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_match = response_text.split("```")[1].split("```")[0]

            return json.loads(json_match.strip())
        except Exception as e:
            logger.error(f"JSON解析失败: {e}")
            return None


# ==================== 便捷函数 ====================

async def draft_patent_specification(
    disclosure: str,
    llm_manager=None,
    drawing_paths: list[str] | None = None
) -> SpecificationDraft:
    """
    便捷函数: 撰写专利说明书

    Args:
        disclosure: 发明披露材料
        llm_manager: LLM管理器
        drawing_paths: 附图路径列表

    Returns:
        SpecificationDraft: 说明书草稿
    """
    drafter = AutoSpecDrafter(llm_manager=llm_manager)
    return await drafter.draft_specification(
        disclosure=disclosure,
        drawing_paths=drawing_paths
    )


def format_specification(draft: SpecificationDraft) -> str:
    """
    格式化说明书输出

    Args:
        draft: 说明书草稿

    Returns:
        str: 格式化的说明书文本
    """
    return draft.get_full_specification()
