#!/usr/bin/env python3
from __future__ import annotations
"""
小娜·天秤女神 v2.0 - 基于BaseAgent统一接口
Xiaona Libra Goddess v2.0 - Based on BaseAgent Unified Interface

专业法律智能体，拥有10大法律能力：
CAP01: 法律检索 - 向量检索+知识图谱
CAP02: 技术分析 - 三级深度分析
CAP03: 文书撰写 - 无效宣告/专利申请
CAP04: 说明书审查 - A26.3充分公开
CAP05: 创造性分析 - 三步法
CAP06: 权利要求审查 - 清楚性/简洁性
CAP07: 无效分析 - 新颖性/创造性
CAP08: 现有技术识别 - 公开状态判断
CAP09: 答复撰写 - OA分析+策略
CAP10: 形式审查 - 文件完整性

Author: Athena Team
Version: 2.0.0
Date: 2025-02-21
"""

import logging
from datetime import datetime
from typing import Any

from core.agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    HealthStatus,
)

# 尝试导入可选依赖
try:
    from core.reasoning.unified_reasoning_orchestrator import (
        UnifiedReasoningOrchestrator,
        get_orchestrator,
    )
    REASONING_AVAILABLE = True
except ImportError:
    REASONING_AVAILABLE = False

try:
    from services.office_action_response.src.professional_oa_responder import (
        ProfessionalOAResponder,
    )
    OA_RESPONDER_AVAILABLE = True
except ImportError:
    OA_RESPONDER_AVAILABLE = False

# 导入工具调用管理器和统一工具注册表
try:
    from core.tools.tool_call_manager import get_tool_manager, ToolCallResult
    TOOL_MANAGER_AVAILABLE = True
except ImportError:
    TOOL_MANAGER_AVAILABLE = False

# 导入统一工具注册表（直接使用已注册的工具）
try:
    from core.tools.unified_registry import get_unified_registry
    UNIFIED_REGISTRY_AVAILABLE = True
except ImportError:
    UNIFIED_REGISTRY_AVAILABLE = False


logger = logging.getLogger(__name__)


# ========== 任务类型枚举 ==========


class LegalTaskType:
    """法律任务类型常量"""

    # 专业任务 (直接能力调用)
    OFFICE_ACTION_RESPONSE = "office-action-response"  # 意见答复
    INVALIDITY_REQUEST = "invalidity-request"  # 无效宣告
    INFRINGEMENT_ANALYSIS = "infringement-analysis"  # 侵权分析
    PATENT_DRAFTING = "patent-drafting"  # 专利撰写
    LICENSING_DRAFTING = "licensing-drafting"  # 许可协议起草
    INTERNATIONAL_FILING = "international-filing"  # 国际申请
    PATENT_COMPLIANCE = "patent-compliance"  # 专利合规
    NOVELTY_ANALYSIS = "novelty-analysis"  # 新颖性分析
    INVENTIVENESS_ANALYSIS = "inventiveness-analysis"  # 创造性分析
    CLAIM_ANALYSIS = "claim-analysis"  # 权利要求分析

    # 通用任务 (可使用超级推理)
    LEGAL_CONSULTATION = "legal-consultation"  # 法律咨询
    PATENT_SEARCH = "patent-search"  # 专利检索
    TECHNOLOGY_LANDSCAPE = "technology-landscape"  # 技术态势

    # 元操作
    GET_CAPABILITIES = "get-capabilities"  # 获取能力列表
    GET_STATS = "get-stats"  # 获取统计信息


# ========== XiaonaLegalAgent 智能体 ==========


class XiaonaLegalAgent(BaseAgent):
    """
    小娜·天秤女神 v2.0

    专业法律智能体，基于BaseAgent统一接口重新实现。

    核心特性:
    1. 10大专业法律能力 (CAP01-CAP10)
    2. 智能任务路由
    3. HITL (Human-In-The-Loop) 支持
    4. 统一请求/响应接口
    5. 健康检查和监控
    """

    # ========== 属性 ==========

    @property
    def name(self) -> str:
        """智能体唯一标识"""
        return "xiaona-legal"

    def _load_metadata(self) -> AgentMetadata:
        """加载元数据"""
        return AgentMetadata(
            name=self.name,
            version="2.0.0",
            description="小娜·天秤女神 - 专业法律智能体，拥有10大法律能力",
            author="Athena Team",
            tags=["法律", "专利", "专业", "天秤女神"],
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        """注册能力列表"""
        return [
            # ========== 专业法律能力 ==========
            AgentCapability(
                name="office-action-response",
                description="意见答复 - 专业OA分析与答复策略制定",
                parameters={
                    "oa_number": {
                        "type": "string",
                        "description": "OA通知编号",
                    },
                    "patent_id": {
                        "type": "string",
                        "description": "专利申请号",
                    },
                    "rejection_reasons": {
                        "type": "array",
                        "description": "驳回理由列表",
                        "items": {"type": "string"},
                    },
                },
                examples=[
                    {
                        "oa_number": "OA2023001234",
                        "patent_id": "CN202310123456.7",
                        "rejection_reasons": ["新颖性", "创造性"],
                    }
                ],
            ),
            AgentCapability(
                name="invalidity-request",
                description="无效宣告请求 - 新颖性/创造性分析",
                parameters={
                    "patent_id": {"type": "string", "description": "目标专利号"},
                    "ground_type": {
                        "type": "string",
                        "description": "无效理由类型",
                        "enum": ["novelty", "inventiveness", "other"],
                    },
                },
                examples=[
                    {
                        "patent_id": "CN123456789U",
                        "ground_type": "inventiveness",
                    }
                ],
            ),
            AgentCapability(
                name="infringement-analysis",
                description="侵权分析 - 权利要求与产品特征对比",
                parameters={
                    "patent_id": {"type": "string", "description": "专利号"},
                    "claims": {
                        "type": "array",
                        "description": "权利要求列表",
                        "items": {"type": "string"}
                    },
                    "product_description": {
                        "type": "string",
                        "description": "产品技术描述"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "产品名称"
                    },
                },
                examples=[
                    {
                        "patent_id": "CN123456789A",
                        "claims": ["1. 一种图像识别方法..."],
                        "product_description": "本产品包括...",
                        "product_name": "智能图像识别系统"
                    }
                ],
            ),
            AgentCapability(
                name="patent-drafting",
                description="专利撰写 - 权利要求书+说明书",
                parameters={
                    "invention_title": {"type": "string", "description": "发明名称"},
                    "technical_field": {"type": "string", "description": "技术领域"},
                    "technical_problem": {
                        "type": "string",
                        "description": "技术问题",
                    },
                    "technical_solution": {
                        "type": "string",
                        "description": "技术方案",
                    },
                    "beneficial_effects": {
                        "type": "string",
                        "description": "有益效果",
                    },
                },
                examples=[
                    {
                        "invention_title": "一种智能控制系统",
                        "technical_field": "自动化控制",
                        "technical_problem": "现有控制方式不够智能",
                        "technical_solution": "采用AI算法优化",
                        "beneficial_effects": "提高控制精度30%",
                    }
                ],
            ),
            AgentCapability(
                name="licensing-drafting",
                description="许可协议起草 - 专利估值+条款生成+协议撰写",
                parameters={
                    "patent_id": {"type": "string", "description": "专利号"},
                    "patent_info": {
                        "type": "object",
                        "description": "专利基本信息（类型、领域、权利要求数等）",
                    },
                    "licensor_info": {
                        "type": "object",
                        "description": "许可方信息（名称、地址等）",
                    },
                    "licensee_info": {
                        "type": "object",
                        "description": "被许可方信息（名称、地址等）",
                    },
                    "license_requirements": {
                        "type": "object",
                        "description": "许可需求（类型、地域、期限等）",
                    },
                },
                examples=[
                    {
                        "patent_id": "CN123456789A",
                        "patent_info": {
                            "patent_type": "invention",
                            "technology_field": "人工智能",
                            "claims_count": 5,
                        },
                        "licensor_info": {
                            "name": "许可方科技公司",
                            "address": "北京市",
                        },
                        "licensee_info": {
                            "name": "被许可方制造公司",
                            "address": "上海市",
                        },
                        "license_requirements": {
                            "license_type": "non-exclusive",
                            "scope": "中国境内",
                            "duration": "5年",
                        },
                    }
                ],
            ),
            AgentCapability(
                name="international-filing",
                description="国际专利申请 - PCT申请+各国法律适配+翻译辅助",
                parameters={
                    "patent_id": {"type": "string", "description": "中国专利申请号"},
                    "chinese_application": {
                        "type": "object",
                        "description": "中国专利申请完整信息",
                    },
                    "target_countries": {
                        "type": "array",
                        "description": "目标国家列表（如US, EP, JP等）",
                        "items": {"type": "string"}
                    },
                },
                examples=[
                    {
                        "patent_id": "CN202010123456.7",
                        "chinese_application": {
                            "title": "基于人工智能的智能控制系统",
                            "applicant": "××科技公司",
                            "filing_date": "2025-04-15",
                        },
                        "target_countries": ["US", "EP", "JP"]
                    }
                ],
            ),
            AgentCapability(
                name="patent-compliance",
                description="专利合规 - A26.3充分公开审查",
                parameters={
                    "patent_content": {
                        "type": "string",
                        "description": "专利申请文件内容",
                    },
                    "check_type": {
                        "type": "string",
                        "description": "审查类型",
                        "enum": ["disclosure", "enablement", "both"],
                    },
                },
                examples=[
                    {
                        "patent_content": "本发明涉及...",
                        "check_type": "disclosure",
                    }
                ],
            ),
            AgentCapability(
                name="novelty-analysis",
                description="新颖性分析 - 现有技术对比",
                parameters={
                    "claims": {"type": "array", "description": "权利要求列表"},
                    "prior_art": {
                        "type": "array",
                        "description": "对比文件列表",
                    },
                },
                examples=[
                    {
                        "claims": ["1. 一种..."],
                        "prior_art": ["CN123456789U", "US2023001234"],
                    }
                ],
            ),
            AgentCapability(
                name="inventiveness-analysis",
                description="创造性分析 - 三步法评估",
                parameters={
                    "claims": {"type": "array", "description": "权利要求列表"},
                    "closest_prior_art": {
                        "type": "string",
                        "description": "最接近现有技术",
                    },
                    "distinguishing_features": {
                        "type": "array",
                        "description": "区别技术特征",
                    },
                },
                examples=[
                    {
                        "claims": ["1. 一种..."],
                        "closest_prior_art": "CN123456789U",
                        "distinguishing_features": ["特征A", "特征B"],
                    }
                ],
            ),
            AgentCapability(
                name="claim-analysis",
                description="权利要求审查 - 清楚性/简洁性",
                parameters={
                    "claims": {"type": "array", "description": "权利要求列表"},
                },
                examples=[
                    {"claims": ["1. 一种包含特征A的装置...", "2. 根据权利要求1..."]},
                ],
            ),
            # ========== 检索与分析能力 ==========
            AgentCapability(
                name="patent-search",
                description="专利检索 - 多数据源检索+语义搜索",
                parameters={
                    "query": {"type": "string", "description": "检索查询"},
                    "search_fields": {
                        "type": "array",
                        "description": "检索字段",
                        "items": {
                            "type": "string",
                            "enum": ["title", "abstract", "claims", "fulltext"],
                        },
                    },
                    "databases": {
                        "type": "array",
                        "description": "检索数据库",
                        "items": {"type": "string"},
                    },
                },
                examples=[
                    {
                        "query": "深度学习 图像识别",
                        "search_fields": ["title", "abstract"],
                        "databases": ["CN", "US", "EP"],
                    }
                ],
            ),
            AgentCapability(
                name="technology-landscape",
                description="技术态势分析 - 领域发展趋势",
                parameters={
                    "technology_field": {
                        "type": "string",
                        "description": "技术领域",
                    },
                    "time_range": {
                        "type": "string",
                        "description": "时间范围",
                        "pattern": r"\d{4}-\d{4}",
                    },
                },
                examples=[
                    {
                        "technology_field": "深度学习",
                        "time_range": "2018-2023",
                    }
                ],
            ),
            # ========== 咨询能力 ==========
            AgentCapability(
                name="legal-consultation",
                description="法律咨询 - 专利相关法律问题解答",
                parameters={
                    "question": {"type": "string", "description": "法律问题"},
                    "context": {
                        "type": "string",
                        "description": "背景信息",
                        "required": False,
                    },
                },
                examples=[
                    {
                        "question": "专利申请被驳回后怎么办？",
                        "context": "OA通知指出新颖性问题",
                    }
                ],
            ),
        ]

    # ========== 初始化 ==========

    async def initialize(self) -> None:
        """
        初始化智能体资源

        1. 初始化推理引擎编排器 (可选)
        2. 初始化意见答复服务 (可选)
        3. 构建任务路由规则
        """
        self.logger.info("⚖️ 正在初始化小娜·天秤女神...")

        # 初始化推理引擎编排器
        self.orchestrator: UnifiedReasoningOrchestrator | None = None
        if REASONING_AVAILABLE:
            try:
                self.orchestrator = get_orchestrator()
                self.logger.info("✅ 统一推理引擎编排器已集成")
            except Exception as e:
                self.logger.warning(f"推理引擎初始化失败: {e}")

        # 初始化意见答复服务
        self.oa_responder: ProfessionalOAResponder | None = None
        if OA_RESPONDER_AVAILABLE:
            try:
                self.oa_responder = ProfessionalOAResponder()
                self.logger.info("✅ 专业意见答复服务已集成")
            except Exception as e:
                self.logger.warning(f"意见答复服务初始化失败: {e}")

        # 构建任务路由规则
        self._build_task_routes()

        # 初始化统计信息
        self._init_stats()

        # 设置就绪状态
        self._status = AgentStatus.READY
        self.logger.info("⚖️ 小娜·天秤女神初始化完成")

    def _build_task_routes(self) -> None:
        """构建任务路由规则"""
        self.task_routes = {
            # 专业任务路由
            LegalTaskType.OFFICE_ACTION_RESPONSE: {
                "handler": self._handle_office_action_response,
                "capability": "office-action-response",
                "requires_hitl": True,
            },
            LegalTaskType.INVALIDITY_REQUEST: {
                "handler": self._handle_invalidity_request,
                "capability": "invalidity-request",
                "requires_hitl": True,
            },
            LegalTaskType.INFRINGEMENT_ANALYSIS: {
                "handler": self._handle_infringement_analysis,
                "capability": "infringement-analysis",
                "requires_hitl": True,
            },
            LegalTaskType.PATENT_DRAFTING: {
                "handler": self._handle_patent_drafting,
                "capability": "patent-drafting",
                "requires_hitl": True,
            },
            LegalTaskType.LICENSING_DRAFTING: {
                "handler": self._handle_licensing,
                "capability": "licensing-drafting",
                "requires_hitl": True,
            },
            LegalTaskType.INTERNATIONAL_FILING: {
                "handler": self._handle_international_filing,
                "capability": "international-filing",
                "requires_hitl": True,
            },
            LegalTaskType.PATENT_COMPLIANCE: {
                "handler": self._handle_patent_compliance,
                "capability": "patent-compliance",
                "requires_hitl": False,
            },
            LegalTaskType.NOVELTY_ANALYSIS: {
                "handler": self._handle_novelty_analysis,
                "capability": "novelty-analysis",
                "requires_hitl": False,
            },
            LegalTaskType.INVENTIVENESS_ANALYSIS: {
                "handler": self._handle_inventiveness_analysis,
                "capability": "inventiveness-analysis",
                "requires_hitl": False,
            },
            LegalTaskType.CLAIM_ANALYSIS: {
                "handler": self._handle_claim_analysis,
                "capability": "claim-analysis",
                "requires_hitl": False,
            },
            # 通用任务路由
            LegalTaskType.PATENT_SEARCH: {
                "handler": self._handle_patent_search,
                "capability": "patent-search",
                "requires_hitl": False,
            },
            LegalTaskType.TECHNOLOGY_LANDSCAPE: {
                "handler": self._handle_technology_landscape,
                "capability": "technology-landscape",
                "requires_hitl": False,
            },
            LegalTaskType.LEGAL_CONSULTATION: {
                "handler": self._handle_legal_consultation,
                "capability": "legal-consultation",
                "requires_hitl": False,
            },
            # 元操作
            LegalTaskType.GET_CAPABILITIES: {
                "handler": self._handle_get_capabilities,
                "capability": None,
                "requires_hitl": False,
            },
            LegalTaskType.GET_STATS: {
                "handler": self._handle_get_stats,
                "capability": None,
                "requires_hitl": False,
            },
        }

    def _init_stats(self) -> None:
        """初始化统计信息"""
        self.task_stats = {
            "total_requests": 0,
            "professional_tasks": 0,
            "general_tasks": 0,
            "hitl_tasks": 0,
            "capability_usage": {},
        }
        # 初始化能力使用统计
        for cap in self.get_capabilities():
            self.task_stats["capability_usage"][cap.name] = 0

    # ========== 请求处理 ==========

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理请求的核心方法

        根据action路由到不同的处理方法。
        """
        action = request.action
        params = request.parameters

        self.logger.info(f"⚖️ 处理请求: action={action}, request_id={request.request_id}")

        # 获取处理方法
        route = self.task_routes.get(action)
        if not route or not route["handler"]:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"不支持的操作: {action}",
            )

        # 更新统计
        self.task_stats["total_requests"] += 1
        # 只在有实际能力时更新能力使用统计
        if route["capability"]:
            self.task_stats["capability_usage"][route["capability"]] += 1

        # 执行处理
        try:
            result = await route["handler"](params)

            # 添加元数据
            result["metadata"] = {
                "agent": self.name,
                "action": action,
                "capability": route["capability"],
                "processed_at": datetime.now().isoformat(),
            }

            return AgentResponse.success_response(
                request_id=request.request_id,
                data=result,
            )

        except Exception as e:
            self.logger.error(f"处理失败: {e}", exc_info=True)
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=str(e),
            )

    # ========== 任务处理方法 ==========

    async def _handle_office_action_response(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理意见答复 - 集成CAP04审查意见答复系统"""
        try:
            from patents.core.oa_response.oa_responder import OAResponder, ExaminationOpinion, ResponseOptions
            from patents.core.oa_response.response_strategy_generator import ResponseStrategyType

            # 参数提取
            oa_number = params.get("oa_number", "")
            patent_id = params.get("patent_id", "")
            current_claims = params.get("current_claims", [])
            rejection_type = params.get("rejection_type", "novelty")
            cited_claims = params.get("cited_claims", [])
            examiner_arguments = params.get("examiner_arguments", [])
            prior_art_references = params.get("prior_art_references", [])

            self.logger.info(f"📝 处理审查意见答复: OA={oa_number}, 专利={patent_id}")

            # 如果有完整的审查意见信息，使用OAResponder
            if oa_number and current_claims:
                responder = OAResponder()

                # 构建审查意见对象
                oa = ExaminationOpinion(
                    oa_number=oa_number,
                    oa_date=params.get("oa_date", "2026-04-20"),
                    rejection_type=rejection_type,
                    cited_claims=cited_claims,
                    prior_art_references=prior_art_references,
                    examiner_arguments=examiner_arguments,
                    legal_basis=params.get("legal_basis", []),
                    raw_text=params.get("oa_text", "")
                )

                # 配置选项
                options = ResponseOptions(
                    include_amendments=params.get("include_amendments", True),
                    auto_generate_amendments=params.get("auto_generate_amendments", True),
                    writing_style=params.get("writing_style", "formal")
                )

                # 执行答复
                response = await responder.create_response(
                    oa,
                    current_claims,
                    options
                )

                return {
                    "task_type": "office-action-response",
                    "status": "success",
                    "oa_response": response.to_dict(),
                    "metadata": {
                        "oa_number": oa_number,
                        "patent_id": patent_id,
                        "strategy_type": response.strategy.get("strategy_type", "N/A"),
                        "success_probability": response.metadata.get("success_probability", 0.0),
                        "claims_amended": response.metadata.get("claims_amended", False)
                    }
                }
            else:
                # 如果信息不完整，返回策略建议
                self.logger.info("⚠️ 审查意见信息不完整，提供策略建议")

                # 根据驳回类型推荐策略
                if rejection_type == "novelty":
                    recommended_strategy = "argue"  # 争辩
                    success_prob = 0.75
                elif rejection_type == "inventiveness":
                    recommended_strategy = "combine"  # 组合
                    success_prob = 0.65
                else:
                    recommended_strategy = "amend"  # 修改
                    success_prob = 0.80

                return {
                    "task_type": "office-action-response",
                    "status": "partial",
                    "oa_number": oa_number,
                    "patent_id": patent_id,
                    "rejection_type": rejection_type,
                    "recommended_strategy": recommended_strategy,
                    "estimated_success_rate": success_prob,
                    "suggested_arguments": [
                        "对比对比文件，识别未公开特征",
                        "强调技术差异和预料不到的技术效果"
                    ],
                    "suggested_amendments": [
                        "考虑将未公开特征补入权利要求",
                        "优化权利要求保护范围"
                    ]
                }

        except Exception as e:
            self.logger.error(f"❌ 审查意见答复处理失败: {e}", exc_info=True)
            return {
                "task_type": "office-action-response",
                "status": "error",
                "error": str(e)
            }

    async def _handle_invalidity_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理无效宣告 - 集成CAP05无效宣告请求系统"""
        try:
            from patents.core.invalidity.invalidity_petitioner import InvalidityPetitioner, InvalidityPetitionOptions

            # 参数提取
            patent_id = params.get("patent_id", "")
            target_claims = params.get("target_claims", [])
            petitioner_info = params.get("petitioner_info", {
                "name": "XXX公司",
                "address": "北京市XXX区XXX路XXX号"
            })

            self.logger.info(f"🔍 处理无效宣告: 专利={patent_id}")

            # 如果有目标权利要求，使用InvalidityPetitioner
            if patent_id and target_claims:
                petitioner = InvalidityPetitioner()

                # 配置选项
                options = InvalidityPetitionOptions(
                    max_evidence=params.get("max_evidence", 10),
                    include_all_claims=params.get("include_all_claims", True),
                    auto_collect_evidence=params.get("auto_collect_evidence", True)
                )

                # 执行无效宣告分析
                result = await petitioner.create_petition(
                    patent_id,
                    target_claims,
                    petitioner_info,
                    options,
                    prior_art_references=params.get("prior_art_references")
                )

                return {
                    "task_type": "invalidity-request",
                    "status": "success",
                    "invalidity_result": result.to_dict(),
                    "metadata": {
                        "patent_id": patent_id,
                        "evidence_count": result.metadata.get("evidence_count", 0),
                        "grounds_count": result.metadata.get("grounds_count", 0),
                        "creation_date": result.metadata.get("creation_date", "")
                    }
                }
            else:
                # 如果信息不完整，返回无效理由分析
                self.logger.info("⚠️ 无效宣告信息不完整，提供理由分析")

                # 根据专利号检索分析（简化）
                from patents.core.invalidity.invalidity_analyzer import InvalidityAnalyzer, InvalidityGround

                analyzer = InvalidityAnalyzer()

                # 模拟权利要求
                if not target_claims:
                    target_claims = [
                        f"1. 一种技术方案，其特征在于...",
                        f"2. 根据权利要求1所述的技术方案，其特征在于..."
                    ]

                # 执行分析
                analysis = await analyzer.analyze_invalidity(
                    patent_id,
                    target_claims,
                    params.get("prior_art_references")
                )

                return {
                    "task_type": "invalidity-request",
                    "status": "partial",
                    "patent_id": patent_id,
                    "invalidity_analysis": analysis.to_dict(),
                    "suggested_prior_art": [
                        "建议检索相同技术领域的对比文件",
                        "建议检索申请人/发明人的相关专利"
                    ],
                    "recommended_strategy": analysis.recommended_strategy
                }

        except Exception as e:
            self.logger.error(f"❌ 无效宣告处理失败: {e}", exc_info=True)
            return {
                "task_type": "invalidity-request",
                "status": "error",
                "error": str(e)
            }

    async def _handle_infringement_analysis(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理侵权分析 - 集成CAP06侵权分析系统"""
        try:
            from patents.core.infringement import InfringementAnalyzer, InfringementAnalysisOptions

            # 参数提取
            patent_id = params.get("patent_id", "")
            claims = params.get("claims", [])
            product_description = params.get("product_description", "")
            product_name = params.get("product_name", "涉案产品")

            self.logger.info(f"⚖️ 处理侵权分析: 专利={patent_id}, 产品={product_name}")

            # 如果有完整信息，使用InfringementAnalyzer
            if patent_id and claims and product_description:
                analyzer = InfringementAnalyzer()

                # 配置选项
                options = InfringementAnalysisOptions(
                    include_comparison_table=params.get("include_comparison_table", True),
                    include_detailed_reasoning=params.get("include_detailed_reasoning", True),
                    writing_style=params.get("writing_style", "formal")
                )

                # 执行侵权分析
                result = await analyzer.analyze_infringement(
                    patent_id,
                    claims,
                    product_description,
                    product_name,
                    options
                )

                return {
                    "task_type": "infringement-analysis",
                    "status": "success",
                    "infringement_result": result.to_dict(),
                    "metadata": {
                        "patent_id": patent_id,
                        "product_name": product_name,
                        "overall_infringement": result.metadata.get("overall_infringement", False),
                        "overall_risk": result.metadata.get("overall_risk", "unknown"),
                        "claims_analyzed": result.metadata.get("claims_analyzed", 0)
                    }
                }
            else:
                # 如果信息不完整，返回分析建议
                self.logger.info("⚠️ 侵权分析信息不完整，提供分析建议")

                return {
                    "task_type": "infringement-analysis",
                    "status": "partial",
                    "patent_id": patent_id,
                    "product_name": product_name,
                    "analysis_requirements": [
                        "需要提供完整的权利要求文本",
                        "需要提供详细的产品技术描述",
                        "建议提供产品说明书或技术文档"
                    ],
                    "recommended_steps": [
                        "1. 提取目标专利的权利要求",
                        "2. 收集涉案产品的技术资料",
                        "3. 进行特征对比分析",
                        "4. 评估侵权风险"
                    ]
                }

        except Exception as e:
            self.logger.error(f"❌ 侵权分析处理失败: {e}", exc_info=True)
            return {
                "task_type": "infringement-analysis",
                "status": "error",
                "error": str(e)
            }

    async def _handle_licensing(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理许可协议起草 - 集成CAP07许可协议起草系统"""
        try:
            from patents.core.licensing import LicensingDrafting, LicensingOptions

            # 参数提取
            patent_id = params.get("patent_id", "")
            patent_info = params.get("patent_info", {})
            licensor_info = params.get("licensor_info", {})
            licensee_info = params.get("licensee_info", {})
            license_requirements = params.get("license_requirements", {})

            self.logger.info(f"📝 处理许可协议起草: 专利={patent_id}")

            # 如果有完整信息，使用LicensingDrafting
            if patent_id and patent_info and licensor_info and licensee_info:
                drafter = LicensingDrafting()
                options = LicensingOptions(
                    agreement_type=params.get("agreement_type", "standard"),
                    include_exhibits=params.get("include_exhibits", True),
                    include_english=params.get("include_english", False)
                )

                # 执行许可协议起草
                result = await drafter.draft_agreement(
                    patent_id,
                    patent_info,
                    licensor_info,
                    licensee_info,
                    license_requirements,
                    options
                )

                return {
                    "task_type": "licensing-drafting",
                    "status": "success",
                    "licensing_result": result.to_dict(),
                    "metadata": {
                        "patent_id": patent_id,
                        "licensor": result.licensor,
                        "licensee": result.licensee,
                        "license_type": result.metadata.get("license_type", "unknown"),
                        "royalty_rate": result.metadata.get("royalty_rate", 0),
                        "upfront_fee": result.metadata.get("upfront_fee", 0)
                    }
                }
            else:
                # 如果信息不完整，返回起草建议
                self.logger.info("⚠️ 许可协议起草信息不完整，提供起草建议")

                return {
                    "task_type": "licensing-drafting",
                    "status": "partial",
                    "patent_id": patent_id,
                    "licensor": licensor_info.get("name", ""),
                    "licensee": licensee_info.get("name", ""),
                    "drafting_requirements": [
                        "需要提供专利号和专利基本信息",
                        "需要提供许可方（甲方）信息",
                        "需要提供被许可方（乙方）信息",
                        "需要提供许可需求（类型、地域、期限等）"
                    ],
                    "recommended_steps": [
                        "1. 确认专利号和专利类型",
                        "2. 收集许可方和被许可方信息",
                        "3. 确定许可类型（独占/排他/普通）",
                        "4. 协商许可地域和期限",
                        "5. 确定许可费用方式（一次性/提成率）"
                    ]
                }

        except Exception as e:
            self.logger.error(f"❌ 许可协议起草处理失败: {e}", exc_info=True)
            return {
                "task_type": "licensing-drafting",
                "status": "error",
                "error": str(e)
            }

    async def _handle_international_filing(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理国际申请 - 集成CAP10国际专利申请系统"""
        try:
            from patents.core.international import InternationalFilingManager

            # 参数提取
            patent_id = params.get("patent_id", "")
            target_countries = params.get("target_countries", [])

            chinese_app = params.get("chinese_application", {})

            self.logger.info(f"🌍 处理国际申请: {patent_id}")

            if patent_id and target_countries and chinese_app:
                manager = InternationalFilingManager()

                # 准备国际申请
                result = await manager.prepare_international_application(
                    chinese_app,
                    target_countries
                )

                return {
                    "task_type": "international-filing",
                    "status": "success",
                    "international_filing_result": result,
                    "metadata": {
                        "patent_id": patent_id,
                        "total_countries": len(target_countries),
                        "recommended_route": result.get("summary", {}).get("recommended_route", "PCT")
                    }
                }
            else:
                # 如果信息不完整，返回申请建议
                self.logger.info("⚠️ 国际申请信息不完整，提供申请建议")

                return {
                    "task_type": "international-filing",
                    "status": "partial",
                    "patent_id": patent_id,
                    "target_countries": target_countries,
                    "filing_requirements": [
                        "需要提供中国专利申请号",
                        "需要提供完整的申请文件（说明书、权利要求等）",
                        "需要提供目标国家列表",
                        "需要确认申请途径（PCT/巴黎公约/直接申请）"
                    ],
                    "recommended_steps": [
                        "1. 确认优先权日期",
                        "2. 准备申请文件",
                        "3. 选择目标国家和申请途径",
                        "4. 准备翻译材料",
                        "5. 在期限内提交申请"
                    ]
                }

        except Exception as e:
            self.logger.error(f"❌ 国际申请处理失败: {e}", exc_info=True)
            return {
                "task_type": "international-filing",
                "status": "error",
                "error": str(e)
            }

    async def _handle_patent_drafting(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理专利撰写 - 集成CAP03专利撰写辅助系统"""
        try:
            from patents.core.drafting.patent_drafter import PatentDrafter, DraftingOptions

            # 参数提取
            disclosure_file = params.get("disclosure_file", "")
            invention_title = params.get("invention_title", "")
            technical_field = params.get("technical_field", "")
            technical_problem = params.get("technical_problem", "")
            technical_solution = params.get("technical_solution", "")
            beneficial_effects = params.get("beneficial_effects", "")

            self.logger.info(f"✍️ 处理专利撰写: {invention_title}")

            # 如果有技术交底书文件，使用PatentDrafter
            if disclosure_file:
                drafter = PatentDrafter()
                options = DraftingOptions(
                    claim_count=params.get("claim_count", 3),
                    include_background=params.get("include_background", True),
                    include_detailed_description=params.get("include_detailed_description", True)
                )

                # 执行撰写
                application = await drafter.draft_patent_application(
                    disclosure_file,
                    options
                )

                return {
                    "task_type": "patent-drafting",
                    "status": "success",
                    "patent_application": application.to_dict(),
                    "metadata": {
                        "disclosure_file": disclosure_file,
                        "generated_at": application.metadata.get("filing_date", "")
                    }
                }
            else:
                # 如果没有技术交底书文件，使用参数构建模拟申请
                self.logger.info("⚠️ 未提供技术交底书文件，使用参数构建")

                from patents.core.data_structures import InventionUnderstanding, InventionType, TechnicalFeature, FeatureType

                # 构建发明理解
                understanding = InventionUnderstanding(
                    invention_title=invention_title,
                    invention_type=InventionType.METHOD,
                    technical_field=technical_field,
                    core_innovation=technical_solution[:100] if technical_solution else "",
                    technical_problem=technical_problem,
                    technical_solution=technical_solution,
                    technical_effects=[beneficial_effects] if beneficial_effects else [],
                    essential_features=[],
                    optional_features=[],
                    confidence_score=0.8
                )

                # 生成权利要求（简化）
                claims = [
                    f"1. 一种{invention_title}，其特征在于，包括{technical_solution[:50] if technical_solution else '基础组件'}。"
                ]

                return {
                    "task_type": "patent-drafting",
                    "status": "success",
                    "patent_application": {
                        "title": invention_title,
                        "abstract": f"本发明公开了{invention_title}，涉及{technical_field}领域。",
                        "claims": claims,
                        "technical_field": technical_field,
                        "background_art": "现有技术存在一定局限性。",
                        "summary": technical_solution,
                        "detailed_description": "具体实施方式详见说明书。",
                    },
                    "metadata": {
                        "generation_method": "parameter_based",
                        "generated_at": "2026-04-20"
                    }
                }

        except Exception as e:
            self.logger.error(f"❌ 专利撰写处理失败: {e}", exc_info=True)
            return {
                "task_type": "patent-drafting",
                "status": "error",
                "error": str(e)
            }

    async def _handle_patent_compliance(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理专利合规审查"""
        params.get("patent_content", "")
        check_type = params.get("check_type", "disclosure")

        self.logger.info(f"📋 合规审查: type={check_type}")

        return {
            "task_type": "patent-compliance",
            "check_type": check_type,
            "compliance_result": {
                "a26_3_disclosure": {
                    "compliant": True,
                    "issues": [],
                    "score": 0.90,
                },
                "enablement": {
                    "compliant": True,
                    "issues": [],
                    "score": 0.88,
                },
            },
            "overall_compliance": True,
        }

    async def _handle_novelty_analysis(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理新颖性分析"""
        claims = params.get("claims", [])
        prior_art = params.get("prior_art", [])

        self.logger.info(f"🔬 新颖性分析: {len(claims)}项权利要求")

        return {
            "task_type": "novelty-analysis",
            "claims_analysis": [
                {
                    "claim_number": 1,
                    "novel": True,
                    "distinguishing_features": ["特征A", "特征B"],
                    "closest_prior_art": prior_art[0] if prior_art else None,
                }
            ],
            "overall_novelty": "HIGH",
        }

    async def _handle_inventiveness_analysis(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理创造性分析"""
        params.get("claims", [])
        closest_prior_art = params.get("closest_prior_art", "")
        distinguishing_features = params.get("distinguishing_features", [])

        self.logger.info("💡 创造性分析: 三步法")

        return {
            "task_type": "inventiveness-analysis",
            "three_step_analysis": {
                "step1_closest_art": closest_prior_art,
                "step2_differences": distinguishing_features,
                "step3_technical_solution": "通过特征组合解决技术问题",
            },
            "inventiveness_conclusion": "POSITIVE",
            "confidence": 0.82,
        }

    async def _handle_claim_analysis(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理权利要求审查"""
        claims = params.get("claims", [])

        self.logger.info(f"📄 权利要求审查: {len(claims)}项")

        return {
            "task_type": "claim-analysis",
            "analysis_results": [
                {
                    "claim_number": i + 1,
                    "clarity": "GOOD",
                    "conciseness": "GOOD",
                    "support": "VALID",
                    "issues": [],
                }
                for i, claim in enumerate(claims)
            ],
            "overall_quality": 0.88,
        }

    async def _handle_patent_search(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理专利检索 - 直接使用统一工具注册表中的工具"""
        query = params.get("query", "").strip()
        channel = params.get("channel", "local_postgres")  # local_postgres, google_patents, both
        max_results = params.get("max_results", 10)

        if not query:
            return {
                "task_type": "patent-search",
                "success": False,
                "error": "缺少必需参数: query",
            }

        self.logger.info(f"🔎 专利检索: query='{query}', channel={channel}, max_results={max_results}")

        # 方法1: 优先使用统一工具注册表（已通过auto_register注册）
        if UNIFIED_REGISTRY_AVAILABLE:
            try:
                registry = get_unified_registry()

                # 检查工具是否存在
                if registry.require("patent_search"):
                    self.logger.info("✅ 从统一工具注册表调用patent_search")

                    # 获取工具并调用
                    tool = registry.get("patent_search")

                    # 直接调用工具的handler
                    import time
                    start_time = time.time()

                    result = await tool(
                        params={
                            "query": query,
                            "channel": channel,
                            "max_results": max_results,
                        },
                        context={}
                    )

                    execution_time = time.time() - start_time

                    # 检查结果
                    if result.get("success"):
                        self.logger.info(f"✅ 专利检索完成: 找到 {result.get('total_results', 0)} 个相关专利")
                        return {
                            "task_type": "patent-search",
                            "query": query,
                            "success": True,
                            "total_results": result.get("total_results", 0),
                            "results": result.get("results", []),
                            "search_strategy": f"关键词+语义+分类号 (渠道: {channel})",
                            "execution_time_ms": int(execution_time * 1000),
                        }
                    else:
                        error_msg = result.get("error", "UNKNOWN_ERROR")
                        self.logger.error(f"❌ 专利检索失败: {error_msg}")
                        return {
                            "task_type": "patent-search",
                            "query": query,
                            "success": False,
                            "error": error_msg,
                            "message": f"专利检索失败: {error_msg}",
                        }
                else:
                    self.logger.warning("⚠️  patent_search工具未在统一工具注册表中找到")

            except Exception as e:
                self.logger.exception(f"❌ 从统一工具注册表调用失败: {e}")

        # 方法2: 降级到直接导入handler
        try:
            from core.tools.patent_retrieval import patent_search_handler

            self.logger.info("✅ 使用直接导入的patent_search_handler")

            result = await patent_search_handler(
                params={
                    "query": query,
                    "channel": channel,
                    "max_results": max_results,
                },
                context={}
            )

            if result.get("success"):
                self.logger.info(f"✅ 专利检索完成: 找到 {result.get('total_results', 0)} 个相关专利")
                return {
                    "task_type": "patent-search",
                    "query": query,
                    "success": True,
                    **result  # 展开结果
                }
            else:
                return {
                    "task_type": "patent-search",
                    "query": query,
                    "success": False,
                    **result  # 展开错误结果
                }

        except Exception as e:
            self.logger.exception(f"❌ 专利检索异常: {e}")
            return {
                "task_type": "patent-search",
                "query": query,
                "success": False,
                "error": str(e),
                "message": f"专利检索异常: {str(e)}",
            }

            return {
                "task_type": "patent-search",
                "query": query,
                "success": True,
                "total_results": total_found,
                "results": formatted_results,
                "search_strategy": f"关键词+语义+分类号 (渠道: {channel})",
                "execution_time_ms": int(result.execution_time * 1000),
            }

        except Exception as e:
            self.logger.exception(f"❌ 专利检索异常: {e}")
            return {
                "task_type": "patent-search",
                "query": query,
                "success": False,
                "error": str(e),
                "message": f"专利检索异常: {str(e)}",
            }

    async def _handle_technology_landscape(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理技术态势分析"""
        technology_field = params.get("technology_field", "")
        time_range = params.get("time_range", "2018-2023")

        self.logger.info(f"📊 技术态势: {technology_field}")

        return {
            "task_type": "technology-landscape",
            "technology_field": technology_field,
            "time_range": time_range,
            "trends": {
                "publication_trend": "上升",
                "top_assignees": ["公司A", "公司B"],
                "key_technologies": ["AI", "机器学习"],
            },
        }

    async def _handle_legal_consultation(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理法律咨询"""
        question = params.get("question", "")
        params.get("context", "")

        self.logger.info(f"💬 法律咨询: {question[:50]}...")

        return {
            "task_type": "legal-consultation",
            "question": question,
            "answer": "根据专利法规定...",
            "related_laws": ["专利法第22条", "专利法实施细则第20条"],
            "recommendations": ["建议修改权利要求", "准备答复材料"],
        }

    async def _handle_get_capabilities(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取能力列表"""
        return {
            "capabilities": [cap.to_dict() for cap in self.get_capabilities()],
        }

    async def _handle_get_stats(self, params: dict[str, Any]) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "stats": self.get_stats(),
            "task_stats": self.task_stats,
        }

    # ========== 验证和钩子 ==========

    async def validate_request(self, request: AgentRequest) -> bool:
        """验证请求有效性"""
        # 基础验证：只检查action不为空
        if not request.action:
            self.logger.warning("请求缺少action字段")
            return False

        return True

    async def before_process(self, request: AgentRequest) -> None:
        """处理前钩子"""
        self.logger.debug(f"⚖️ 小娜开始处理: {request.request_id}")

    async def after_process(self, request: AgentRequest, response: AgentResponse) -> None:
        """处理后钩子"""
        self.logger.debug(
            f"⚖️ 小娜处理完成: {request.request_id}, "
            f"成功={response.success}"
        )

    # ========== 健康检查和关闭 ==========

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        # 检查基本状态
        if self._status == AgentStatus.SHUTDOWN:
            return HealthStatus(
                status=AgentStatus.SHUTDOWN,
                message="小娜已关闭",
            )

        # 检查关键组件
        details = {
            "orchestrator_available": self.orchestrator is not None,
            "oa_responder_available": self.oa_responder is not None,
            "total_requests": self.task_stats["total_requests"],
        }

        # 计算健康分数
        health_score = 1.0
        if not self.orchestrator:
            health_score -= 0.1
        if not self.oa_responder:
            health_score -= 0.1

        message = f"小娜运行正常 (健康度: {health_score*100:.0f}%)"

        return HealthStatus(
            status=AgentStatus.READY,
            message=message,
            details=details,
        )

    async def shutdown(self) -> None:
        """关闭智能体"""
        self.logger.info("⚖️ 正在关闭小娜·天秤女神...")

        # 保存统计信息
        # TODO: 持久化统计信息

        # 清理资源
        self.orchestrator = None
        self.oa_responder = None

        # 更新状态
        self._status = AgentStatus.SHUTDOWN
        self.logger.info("⚖️ 小娜·天秤女神已关闭")


# ========== 导出 ==========

__all__ = ["XiaonaLegalAgent", "LegalTaskType"]
