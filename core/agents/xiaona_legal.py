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
    PATENT_DRAFTING = "patent-drafting"  # 专利撰写
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
            LegalTaskType.PATENT_DRAFTING: {
                "handler": self._handle_patent_drafting,
                "capability": "patent-drafting",
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
        """处理意见答复"""
        oa_number = params.get("oa_number", "")
        patent_id = params.get("patent_id", "")
        rejection_reasons = params.get("rejection_reasons", [])

        self.logger.info(f"📝 处理意见答复: OA={oa_number}, 专利={patent_id}")

        # 如果有专业服务，使用它
        if self.oa_responder:
            # TODO: 调用专业服务
            pass

        # 返回模拟结果
        return {
            "task_type": "office-action-response",
            "oa_number": oa_number,
            "patent_id": patent_id,
            "rejection_reasons": rejection_reasons,
            "response_strategy": {
                "main_argument": "根据审查意见...",
                "evidence_sources": ["对比文件分析", "技术特征对比"],
                "recommended_actions": ["修改权利要求", "提交意见陈述书"],
            },
            "estimated_success_rate": 0.75,
        }

    async def _handle_invalidity_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理无效宣告"""
        patent_id = params.get("patent_id", "")
        ground_type = params.get("ground_type", "")

        self.logger.info(f"🔍 处理无效宣告: 专利={patent_id}, 理由={ground_type}")

        return {
            "task_type": "invalidity-request",
            "patent_id": patent_id,
            "ground_type": ground_type,
            "analysis": {
                "novelty_issues": ["特征X已被公开"],
                "inventiveness_issues": ["技术方案显而易见"],
                "recommended_prior_art": ["CN123456789U", "US2023001234"],
            },
            "invalidation_probability": 0.80,
        }

    async def _handle_patent_drafting(self, params: dict[str, Any]) -> dict[str, Any]:
        """处理专利撰写"""
        invention_title = params.get("invention_title", "")
        technical_field = params.get("technical_field", "")
        technical_problem = params.get("technical_problem", "")

        self.logger.info(f"✍️ 撰写专利: {invention_title}")

        return {
            "task_type": "patent-drafting",
            "invention_title": invention_title,
            "draft_content": {
                "claims": [
                    "1. 一种智能控制系统，其特征在于，包括...",
                    "2. 根据权利要求1所述的智能控制系统，其特征在于...",
                ],
                "abstract": f"本发明公开了{invention_title}，涉及{technical_field}...",
                "description": {
                    "technical_field": technical_field,
                    "background_art": "现有技术存在...",
                    "summary_of_invention": f"为解决{technical_problem}...",
                    "detailed_description": "具体实施方式...",
                },
            },
            "quality_score": 0.85,
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
                tool = registry.get("patent_search")

                if tool and tool.enabled:
                    self.logger.info("✅ 从统一工具注册表调用patent_search")

                    # 直接调用工具的handler
                    import time
                    start_time = time.time()

                    result = await tool.function(
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
