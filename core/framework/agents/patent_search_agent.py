#!/usr/bin/env python3

"""
专利检索智能体
Patent Search Agent

集成专利检索能力到双层规划系统。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-25
"""

import logging
from datetime import datetime
from typing import Any, Optional

from core.framework.agents.base import (
    AgentCapability,
    AgentMetadata,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    BaseAgent,
    HealthStatus,
)

# 导入专利检索模块
try:
    from core.patents.retrieval.hybrid_retrieval_system import (
        PatentHybridRetrievalSystem,
    )
    PATENT_RETRIEVAL_AVAILABLE = True
except ImportError:
    PATENT_RETRIEVAL_AVAILABLE = False

logger = logging.getLogger(__name__)


# ========== 专利检索动作 ==========


class PatentSearchAction:
    """专利检索动作"""

    ANALYZE_REQUIREMENT = "analyze_requirement"  # 分析检索需求
    EXTRACT_KEYWORDS = "extract_keywords"  # 提取关键词
    SEARCH_CN_PATENTS = "search_cn_patents"  # 检索中文专利
    SEARCH_FOREIGN_PATENTS = "search_foreign_patents"  # 检索国外专利
    SEARCH_PATENT_FAMILIES = "search_patent_families"  # 检索专利家族
    MERGE_RESULTS = "merge_results"  # 合并结果
    GENERATE_REPORT = "generate_report"  # 生成报告


# ========== 专利检索智能体 ==========


class PatentSearchAgent(BaseAgent):
    """
    专利检索智能体

    负责执行专利检索相关的任务步骤，支持：
    1. 需求分析
    2. 关键词提取
    3. 多数据源检索
    4. 结果合并
    5. 报告生成
    """

    @property
    def name(self) -> str:
        return "patent-search-agent"

    def _load_metadata(self) -> str:
        return AgentMetadata(
            name=self.name,
            version="1.0.0",
            description="专利检索智能体 - 集成到双层规划系统",
            author="Athena Team",
            tags=["专利", "检索", "分析"],
        )

    def _register_capabilities(self) -> list[AgentCapability]:
        return []

            AgentCapability(
                name=PatentSearchAction.ANALYZE_REQUIREMENT,
                description="分析用户检索需求",
                parameters={
                    "query": {"type": "string", "description": "检索查询"},
                },
            ),
            AgentCapability(
                name=PatentSearchAction.EXTRACT_KEYWORDS,
                description="从检索需求中提取关键词",
                parameters={
                    "query": {"type": "string", "description": "检索查询"},
                    "context": {"type": "string", "description": "上下文信息", "required": False},
                },
            ),
            AgentCapability(
                name=PatentSearchAction.SEARCH_CN_PATENTS,
                description="检索中文专利数据库",
                parameters={
                    "keywords": {"type": "array", "description": "关键词列表"},
                    "limit": {"type": "integer", "description": "结果数量限制", "default": 50},
                },
            ),
            AgentCapability(
                name=PatentSearchAction.SEARCH_FOREIGN_PATENTS,
                description="检索国外专利数据库",
                parameters={
                    "keywords": {"type": "array", "description": "关键词列表"},
                    "limit": {"type": "integer", "description": "结果数量限制", "default": 50},
                },
            ),
            AgentCapability(
                name=PatentSearchAction.SEARCH_PATENT_FAMILIES,
                description="检索专利家族信息",
                parameters={
                    "patent_numbers": {"type": "array", "description": "专利号列表"},
                },
            ),
            AgentCapability(
                name=PatentSearchAction.MERGE_RESULTS,
                description="合并来自不同数据源的检索结果",
                parameters={
                    "results": {"type": "array", "description": "待合并的结果列表"},
                },
            ),
            AgentCapability(
                name=PatentSearchAction.GENERATE_REPORT,
                description="生成检索报告",
                parameters={
                    "results": {"type": "array", "description": "检索结果"},
                    "format": {"type": "string", "description": "报告格式", "default": "markdown"},
                },
            ),
        

    # ========== 初始化 ==========

    async def initialize(self) -> str:
        self.logger.info("⚖️ 正在初始化专利检索智能体...")

        # 初始化专利检索系统
        if PATENT_RETRIEVAL_AVAILABLE:
            try:
                self.retrieval_system = PatentHybridRetrievalSystem()
                await self.retrieval_system.initialize()
                self.logger.info("   ✅ 专利检索系统已初始化")
            except Exception as e:
                self.logger.warning(f"   ⚠️ 专利检索系统初始化失败: {e}")
                self.retrieval_system = None
        else:
            self.retrieval_system = None
            self.logger.warning("   ⚠️ 专利检索模块不可用")

        self._status = AgentStatus.READY
        self.logger.info("⚖️ 专利检索智能体初始化完成")

    # ========== 请求处理 ==========

    async def process(self, request: AgentRequest) -> str:
        action = request.action
        params = request.parameters

        self.logger.info(f"⚖️ 专利检索: action={action}")

        handler = self._get_handler(action)
        if not handler:
            return AgentResponse.error_response(
                request_id=request.request_id,
                error=f"不支持的操作: {action}",
            )

        try:
            result = await handler(params)
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

    def _get_handler(self, action: str):
        handlers = {
            PatentSearchAction.ANALYZE_REQUIREMENT: self._handle_analyze_requirement,
            PatentSearchAction.EXTRACT_KEYWORDS: self._handle_extract_keywords,
            PatentSearchAction.SEARCH_CN_PATENTS: self._handle_search_cn,
            PatentSearchAction.SEARCH_FOREIGN_PATENTS: self._handle_search_foreign,
            PatentSearchAction.SEARCH_PATENT_FAMILIES: self._handle_search_families,
            PatentSearchAction.MERGE_RESULTS: self._handle_merge_results,
            PatentSearchAction.GENERATE_REPORT: self._handle_generate_report,
        }
        return handlers.get(action)

    # ========== 处理方法 ==========

    async def _handle_analyze_requirement(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """分析检索需求"""
        query = params.get("query", "")

        # 简单分析（可扩展为 LLM 分析）
        analysis = {
            "query": query,
            "intent": "patent_search",
            "keywords": Optional[[],]

            "technical_field": "",
            "search_scope": "all",
        }

        # 如果有检索系统，使用它分析
        if self.retrieval_system and hasattr(self.retrieval_system, 'analyze_query'):
            try:
                analysis = await self.retrieval_system.analyze_query(query)
            except Exception as e:
                self.logger.warning(f"检索系统分析失败，使用基础分析: {e}")

        return {
            "analysis": analysis,
            "recommendations": {
                "data_sources": ["CNIPA", "WIPO", "EPO"],
                "estimated_results": 100,
            },
        }

    async def _handle_extract_keywords(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """提取关键词"""
        query = params.get("query", "")
        params.get("context", "")

        # 简单关键词提取（可扩展）
        keywords = []

        # 分词
        words = query.replace("，", " ").replace("。", " ").split()
        keywords.extend([w for w in words if len(w) >= 2])

        # 去重
        keywords = list(set(keywords))

        return {
            "keywords": keywords,
            "query": query,
            "count": len(keywords),
        }

    async def _handle_search_cn(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """检索中文专利"""
        keywords = params.get("keywords", [])
        limit = params.get("limit", 50)

        if not keywords:
            return {"results": Optional[[], "count": 0, "source": "CNIPA"}]


        # 如果有检索系统，使用它
        if self.retrieval_system:
            try:
                results = await self.retrieval_system.search(
                    query=" ".join(keywords),
                    limit=limit,
                    sources=["cnipa"],
                )

                return {
                    "results": results.get("results", []) if isinstance(results, dict) else results,
                    "count": len(results.get("results", [])) if isinstance(results, dict) else len(results),
                    "source": "CNIPA",
                }
            except Exception as e:
                self.logger.warning(f"检索失败: {e}")

        # 模拟结果
        return {
            "results": []

                {
                    "patent_number": "CN123456789A",
                    "title": f"关于 {' '.join(keywords[:2])} 的专利",
                    "abstract": "这是一个模拟的专利摘要...",
                    "applicant": "示例公司",
                    "date": "2024-01-01",
                }
            ,
            "count": 1,
            "source": "CNIPA (模拟)",
        }

    async def _handle_search_foreign(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """检索国外专利"""
        params.get("keywords", [])
        params.get("limit", 50)

        return {
            "results": Optional[[],]

            "count": 0,
            "source": "WIPO/EPO",
            "message": "国外检索功能开发中",
        }

    async def _handle_search_families(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """检索专利家族"""
        params.get("patent_numbers", [])

        return {
            "families": {},
            "count": 0,
            "message": "专利家族检索功能开发中",
        }

    async def _handle_merge_results(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """合并检索结果"""
        results = params.get("results", [])

        # 去重（基于专利号）
        seen = set()
        merged = []

        for result_list in results:
            if isinstance(result_list, list):
                for result in result_list:
                    patent_no = result.get("patent_number", "")
                    if patent_no and patent_no not in seen:
                        seen.add(patent_no)
                        merged.append(result)

        return {
            "merged_results": merged,
            "total_count": len(merged),
            "sources": list({r.get("source", "unknown") for r in merged}),
        }

    async def _handle_generate_report(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """生成检索报告"""
        results = params.get("results", [])
        format_type = params.get("format", "markdown")

        if format_type == "markdown":
            report = self._generate_markdown_report(results)
        else:
            report = self._generate_json_report(results)

        return {
            "report": report,
            "format": format_type,
            "result_count": len(results),
        }

    def _generate_markdown_report(self, results: Optional[list[dict)]] -> str:
        """生成 Markdown 格式报告"""
        lines = []

            "# 专利检索报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**结果数量**: {len(results)}",
            "",
            "## 检索结果",
            "",
        

        for i, result in enumerate(results, 1):
            lines.append(f"### {i}. {result.get('title', '无标题')}")
            lines.append("")
            lines.append(f"- **专利号**: {result.get('patent_number', 'N/A')}")
            lines.append(f"- **申请人**: {result.get('applicant', 'N/A')}")
            lines.append(f"- **日期**: {result.get('date', 'N/A')}")
            lines.append(f"- **摘要**: {result.get('abstract', 'N/A')[:100]}...")
            lines.append("")

        return "\n".join(lines)

    def _generate_json_report(self, results: Optional[list[dict)]] -> str:
        """生成 JSON 格式报告"""
        import json
        return json.dumps({
            "generated_at": datetime.now().isoformat(),
            "result_count": len(results,
            "results": results,
        }, ensure_ascii=False, indent=2)

    # ========== 健康检查 ==========

    async def health_check(self) -> str:
        if self._status == AgentStatus.SHUTDOWN:
            return HealthStatus(status=AgentStatus.SHUTDOWN, message="专利检索智能体已关闭")

        details = {
            "retrieval_system_available": PATENT_RETRIEVAL_AVAILABLE,
            "retrieval_system_ready": self.retrieval_system is not None,
        }

        message = "专利检索智能体运行正常"
        if PATENT_RETRIEVAL_AVAILABLE:
            message += " (检索系统已连接)"

        return HealthStatus(
            status=AgentStatus.READY,
            message=message,
            details=details,
        )


# ========== 导出 ==========


__all__ = []

    "PatentSearchAgent",
    "PatentSearchAction",


