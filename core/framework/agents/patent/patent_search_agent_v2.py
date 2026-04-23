#!/usr/bin/env python3
"""
专利检索智能体 v2.0 - 符合统一接口标准
Patent Search Agent v2.0 - Compliant with Unified Agent Interface Standard

特性：
1. 继承自BaseXiaonaComponent（符合统一接口标准）
2. 保留专利检索能力
3. 支持多数据源检索
4. 结果合并和报告生成

作者: Athena平台团队
版本: v2.0.0
创建时间: 2026-04-21
迁移自: core/agents/patent_search_agent.py
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)

# 导入专利检索模块（可选）
try:
    from core.patents.retrieval.hybrid_retrieval_system import (
        PatentHybridRetrievalSystem,
    )
    PATENT_RETRIEVAL_AVAILABLE = True
except ImportError:
    PATENT_RETRIEVAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class PatentSearchAgentV2(BaseXiaonaComponent):
    """
    专利检索智能体 v2.0

    核心能力：
    1. 分析检索需求
    2. 提取关键词
    3. 检索中文专利
    4. 检索国外专利
    5. 检索专利家族
    6. 合并检索结果
    7. 生成检索报告

    架构说明：
    - 继承BaseXiaonaComponent（符合统一接口标准）
    - 检索系统通过组合方式集成（可选）
    - 支持模拟模式（当检索系统不可用时）
    """

    def __init__(
        self,
        agent_id: str = "patent_search_agent_v2",
        config: Optional[dict[str, Any]],
    ):
        """
        初始化专利检索Agent v2.0

        Args:
            agent_id: Agent唯一标识
            config: 配置参数，可包含：
                - enable_retrieval_system: 是否启用检索系统（默认True）
                - default_limit: 默认结果数量限制（默认50）
        """
        # 保存配置
        self.config = config or {}
        self.default_limit = self.config.get("default_limit", 50)
        self._enable_retrieval_system = self.config.get("enable_retrieval_system", True)

        # 检索系统
        self.retrieval_system = None

        # 调用父类初始化
        super().__init__(agent_id, self.config)

    def _initialize(self) -> str:
        """初始化专利检索Agent（统一接口标准要求）"""
        # 注册能力（符合统一接口标准）
        self._register_capabilities([

            AgentCapability(
                name="analyze_requirement",
                description="分析用户检索需求",
                input_types=["检索查询"],
                output_types=["需求分析结果"],
                estimated_time=2.0,
            ),
            AgentCapability(
                name="extract_keywords",
                description="从检索需求中提取关键词",
                input_types=["检索查询", "上下文信息"],
                output_types=["关键词列表"],
                estimated_time=3.0,
            ),
            AgentCapability(
                name="search_cn_patents",
                description="检索中文专利数据库",
                input_types=["关键词列表", "结果数量限制"],
                output_types=["专利列表"],
                estimated_time=10.0,
            ),
            AgentCapability(
                name="search_foreign_patents",
                description="检索国外专利数据库",
                input_types=["关键词列表", "结果数量限制"],
                output_types=["专利列表"],
                estimated_time=15.0,
            ),
            AgentCapability(
                name="search_patent_families",
                description="检索专利家族信息",
                input_types=["专利号列表"],
                output_types=["专利家族数据"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="merge_results",
                description="合并来自不同数据源的检索结果",
                input_types=["多个检索结果列表"],
                output_types=["合并后的结果"],
                estimated_time=2.0,
            ),
            AgentCapability(
                name="generate_report",
                description="生成检索报告",
                input_types=["检索结果", "报告格式"],
                output_types=["检索报告"],
                estimated_time=3.0,
            ),
        )

        # 尝试初始化检索系统
        if self._enable_retrieval_system and PATENT_RETRIEVAL_AVAILABLE:
            self.logger.info("✅ 专利检索模块可用，将在首次使用时初始化")

        self.logger.info(f"🔍 专利检索Agent v2.0初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词（统一接口标准要求）"""
        return """你是专利检索专家，负责专利检索和分析任务。

【核心能力】
1. 需求分析 - 理解用户的检索需求
2. 关键词提取 - 从技术描述中提取检索关键词
3. 多源检索 - 中文专利、国外专利、专利家族
4. 结果处理 - 去重、排序、合并
5. 报告生成 - Markdown/JSON格式报告

【检索策略】
- 中文专利：使用CNIPA数据库
- 国外专利：使用WIPO/EPO数据库
- 专利家族：关联同族专利
- 结果去重：基于专利号去重

【输出格式】
- 报告格式：Markdown或JSON
- 结果包含：专利号、标题、申请人、摘要
"""

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行任务（统一接口标准要求）

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        start_time = datetime.now()

        try:
            # 验证输入
            if not self.validate_input(context):
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message="输入验证失败：缺少session_id或task_id",
                    execution_time=0.0,
                )

            # 获取操作类型和参数
            action = context.input_data.get("action", "search_cn_patents")
            params = context.input_data.get("params", {})

            self.logger.info(f"[{self.agent_id}] 执行操作: {action}")

            # 初始化检索系统（如果需要）
            await self._ensure_retrieval_system()

            # 路由到对应的处理方法
            handler = self._get_handler(action)
            if not handler:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    output_data=None,
                    error_message=f"不支持的操作: {action}",
                    execution_time=0.0,
                )

            # 执行处理
            result = await handler(params)

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            # 构建输出数据
            output_data = {
                "action": action,
                "result": result,
                "agent_info": {
                    "agent_id": self.agent_id,
                    "retrieval_system_available": self.retrieval_system is not None,
                },
                "timestamp": datetime.now().isoformat(),
            }

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                execution_time=execution_time,
                metadata={"action": action},
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.exception(f"任务执行失败: {context.task_id}")

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
                execution_time=execution_time,
            )

    def _get_handler(self, action: str):
        """获取操作对应的处理方法"""
        handlers = {
            "analyze_requirement": self._handle_analyze_requirement,
            "extract_keywords": self._handle_extract_keywords,
            "search_cn_patents": self._handle_search_cn,
            "search_foreign_patents": self._handle_search_foreign,
            "search_patent_families": self._handle_search_families,
            "merge_results": self._handle_merge_results,
            "generate_report": self._handle_generate_report,
        }
        return handlers.get(action)

    async def _ensure_retrieval_system(self):
        """确保检索系统已初始化"""
        if self._enable_retrieval_system and PATENT_RETRIEVAL_AVAILABLE and self.retrieval_system is None:
            try:
                self.retrieval_system = PatentHybridRetrievalSystem()
                await self.retrieval_system.initialize()
                self.logger.info("✅ 专利检索系统已初始化")
            except Exception as e:
                self.logger.warning(f"⚠️ 专利检索系统初始化失败: {e}")
                self.retrieval_system = None

    # ==================== 处理方法 ====================

    async def _handle_analyze_requirement(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """分析检索需求"""
        query = params.get("query", "")

        # 基础分析
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
        context = params.get("context", "")

        # 简单关键词提取
        keywords = []

        # 分词
        words = query.replace("，", " ").replace("。", " ").split()
        keywords.extend([w for w in words if len(w) >= 2])

        # 去重
        keywords = list(set(keywords))

        return {
            "keywords": keywords,
            "query": query,
            "context": context,
            "count": len(keywords),
        }

    async def _handle_search_cn(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """检索中文专利"""
        keywords = params.get("keywords", [])
        limit = params.get("limit", self.default_limit)

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
        keywords = params.get("keywords", [])
        limit = params.get("limit", self.default_limit)

        # 如果有检索系统，使用它
        if self.retrieval_system:
            try:
                results = await self.retrieval_system.search(
                    query=" ".join(keywords),
                    limit=limit,
                    sources=["wipo", "epo"],
                )

                return {
                    "results": results.get("results", []) if isinstance(results, dict) else results,
                    "count": len(results.get("results", [])) if isinstance(results, dict) else len(results),
                    "source": "WIPO/EPO",
                }
            except Exception as e:
                self.logger.warning(f"国外检索失败: {e}")

        return {
            "results": Optional[[],]

            "count": 0,
            "source": "WIPO/EPO",
            "message": "国外检索功能开发中",
        }

    async def _handle_search_families(self, params: Optional[dict[str, Any])] -> dict[str, Any]:
        """检索专利家族"""
        patent_numbers = params.get("patent_numbers", [])

        if not patent_numbers:
            return {"families": {}, "count": 0, "message": "未提供专利号"}

        # 如果有检索系统，使用它
        if self.retrieval_system and hasattr(self.retrieval_system, 'search_families'):
            try:
                families = await self.retrieval_system.search_families(patent_numbers)
                return {
                    "families": families,
                    "count": len(families),
                    "source": "Patent Families",
                }
            except Exception as e:
                self.logger.warning(f"专利家族检索失败: {e}")

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
        return json.dumps({
            "generated_at": datetime.now().isoformat(),
            "result_count": len(results),
            "results": results,
        }, ensure_ascii=False, indent=2)

    async def get_overview(self) -> dict[str, Any]:
        """获取Agent概览"""
        capabilities = self.get_capabilities()

        return {
            "agent_name": "专利检索Agent v2.0",
            "agent_id": self.agent_id,
            "role": "专利检索专家",
            "version": "v2.0.0",
            "total_capabilities": len(capabilities),
            "capabilities": Optional[[c.name for c in capabilities],]

            "retrieval_system_available": PATENT_RETRIEVAL_AVAILABLE,
            "retrieval_system_enabled": self._enable_retrieval_system,
            "retrieval_system_ready": self.retrieval_system is not None,
        }


# ==================== 便捷工厂函数 ====================

def create_patent_search_agent_v2(
    agent_id: str = "patent_search_agent_v2",
    enable_retrieval_system: bool = True,
    **config
) -> str:
    """
    创建专利检索Agent v2.0实例

    Args:
        agent_id: Agent ID
        enable_retrieval_system: 是否启用检索系统
        **config: 其他配置

    Returns:
        PatentSearchAgentV2实例
    """
    config["enable_retrieval_system"] = enable_retrieval_system
    return PatentSearchAgentV2(agent_id=agent_id, config=config)


# ==================== 测试函数 ====================

async def test_patent_search_agent_v2():
    """测试专利检索Agent v2.0"""
    print("🔍 测试专利检索Agent v2.0...")

    from core.framework.agents.xiaona.base_component import AgentExecutionContext

    # 创建专利检索Agent
    agent = PatentSearchAgentV2(agent_id="patent_search_test")

    print("✅ 专利检索Agent v2.0初始化成功")

    # 测试各种能力
    print("\n🧪 能力测试...")

    test_cases = []

        {
            "name": "分析需求",
            "action": "analyze_requirement",
            "params": {"query": "人工智能在自动驾驶中的应用"},
        },
        {
            "name": "提取关键词",
            "action": "extract_keywords",
            "params": {"query": "深度学习图像识别技术"},
        },
        {
            "name": "检索中文专利",
            "action": "search_cn_patents",
            "params": {"keywords": ["人工智能", "自动驾驶"], "limit": 10},
        },
        {
            "name": "生成报告",
            "action": "generate_report",
            "params": {
                "results": []

                    {
                        "patent_number": "CN123456789A",
                        "title": "测试专利",
                        "applicant": "测试公司",
                        "date": "2024-01-01",
                        "abstract": "测试摘要",
                    }
                ,
                "format": "markdown",
            },
        },
    

    for test in test_cases:
        print(f"\n📝 测试: {test['name']}")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id=f"TASK_{test['name']}",
            input_data={
                "action": test["action"],
                "params": test["params"],
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        print(f"  状态: {result.status.value}")
        if result.status == AgentStatus.COMPLETED:
            print(f"  结果: {str(result.output_data['result'])[:100]}...")

        assert result.status == AgentStatus.COMPLETED, f"测试失败: {test['name']}"

    # 显示概览
    print("\n📊 Agent概览:")
    overview = await agent.get_overview()

    print(f"  名称: {overview['agent_name']}")
    print(f"  角色: {overview['role']}")
    print(f"  能力数: {overview['total_capabilities']}")
    print(f"  检索系统可用: {overview['retrieval_system_available']}")

    print("\n✅ 所有测试通过！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_patent_search_agent_v2())

