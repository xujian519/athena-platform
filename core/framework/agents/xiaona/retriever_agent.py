"""
小娜·检索者

负责专利检索、关键词扩展、对比文件筛选等任务。
"""

import logging
from typing import Any, Dict, List, Optional

from core.ai.llm.unified_llm_manager import UnifiedLLMManager
from core.framework.agents.xiaona.base_component import (
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    BaseXiaonaComponent,
)
from core.tools.unified_registry import get_unified_registry

logger = logging.getLogger(__name__)


class RetrieverAgent(BaseXiaonaComponent):
    """
    小娜·检索者

    专注于专利检索任务，包括：
    - 关键词扩展和优化
    - 多数据库检索（CNIPA/WIPO/EPO等）
    - 对比文件筛选和排序
    - 检索策略制定
    """

    def _initialize(self) -> str:
        """初始化检索者智能体"""
        # 注册能力
        self._register_capabilities([

            AgentCapability(
                name="patent_search",
                description="专利检索",
                input_types=["查询关键词", "技术领域"],
                output_types=["专利列表", "检索报告"],
                estimated_time=15.0,
            ),
            AgentCapability(
                name="keyword_expansion",
                description="关键词扩展",
                input_types=["初始关键词"],
                output_types=["扩展关键词列表"],
                estimated_time=5.0,
            ),
            AgentCapability(
                name="document_filtering",
                description="对比文件筛选",
                input_types=["专利列表", "筛选标准"],
                output_types=["筛选后的专利列表"],
                estimated_time=10.0,
            ),
        ])

        # 初始化LLM
        self.llm_manager = UnifiedLLMManager()

        # 获取工具注册表
        self.tool_registry = get_unified_registry()

        self.logger.info(f"检索者智能体初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是小娜·检索者，专利检索领域的专家。

你的核心能力：
1. 关键词扩展：根据技术方案提取和扩展检索关键词
2. 专利检索：在多个专利数据库中进行检索
3. 结果筛选：根据相关性筛选和排序检索结果

工作原则：
- 全面性：确保检索覆盖所有相关技术领域
- 准确性：选择最相关的检索词和数据库
- 效率性：在合理时间内完成检索任务

输出格式：
- 检索关键词列表（含中英文）
- 检索式构建逻辑
- 检索结果（按相关性排序）
- 检索策略说明
"""

    async def execute(self, context: AgentExecutionContext) -> str:
        """
        执行检索任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        try:
            # 获取用户输入
            user_input = context.input_data.get("user_input", "")
            previous_results = context.input_data.get("previous_results", {})

            self.logger.info(f"开始检索任务: {context.task_id}")

            # 步骤1：关键词扩展
            keywords = await self._expand_keywords(user_input, previous_results)

            # 步骤2：构建检索式
            search_queries = await self._build_search_queries(keywords)

            # 步骤3：执行检索
            search_results = await self._execute_search(search_queries, context.config)

            # 步骤4：筛选和排序
            filtered_results = await self._filter_and_rank_results(search_results, context.config)

            # 构建输出
            output_data = {
                "keywords": keywords,
                "search_queries": search_queries,
                "patents": filtered_results,
                "total_count": len(search_results),
                "filtered_count": len(filtered_results),
            }

            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=output_data,
                metadata={"search_databases": context.config.get("databases", [])},
            )

        except Exception as e:
            self.logger.exception(f"检索任务失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
            )

    async def _expand_keywords(
        self,
        user_input: str,
        previous_results: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        扩展关键词

        Args:
            user_input: 用户输入
            previous_results: 前面步骤的结果

        Returns:
            关键词列表
        """
        # 如果有规划者的结果，使用其提供的关键词
        if "xiaona_planner" in previous_results:
            planner_output = previous_results["xiaona_planner"]
            if "keywords" in planner_output:
                return planner_output["keywords"]

        # 否则使用LLM扩展关键词
        prompt = f"""请根据以下技术方案，提取和扩展专利检索关键词。

技术方案：{user_input}

要求：
1. 提取核心技术特征
2. 提供中英文关键词
3. 包含同义词和近义词
4. 按重要性排序

输出格式：JSON
{{
    "core_keywords": ["核心关键词列表"],
    "extended_keywords": ["扩展关键词列表"],
    "english_keywords": ["英文关键词列表"]
}}
"""

        response = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",  # 使用Kimi模型
        )

        # 解析JSON响应
        import json
        try:
            result = json.loads(response)
            keywords = []
            keywords.extend(result.get("core_keywords", []))
            keywords.extend(result.get("extended_keywords", []))
            keywords.extend(result.get("english_keywords", []))
            return keywords
        except json.JSONDecodeError:
            self.logger.error("关键词扩展响应解析失败")
            return []

    async def _build_search_queries(self, keywords: Optional[List[str]] = None) -> List[str]:
        """
        构建检索式

        Args:
            keywords: 关键词列表

        Returns:
            检索式列表
        """
        # 简单实现：组合关键词
        # 实际应该根据数据库规则构建复杂检索式
        queries = []

        # 核心关键词组合
        core_keywords = keywords[:5]
        query = " AND ".join(core_keywords)
        queries.append(query)

        # 宽松检索（OR连接）
        loose_query = " OR ".join(keywords[:10])
        queries.append(loose_query)

        return queries

    async def _execute_search(
        self,
        queries: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """
        执行检索

        Args:
            queries: 检索式列表
            config: 配置参数

        Returns:
            检索结果列表
        """
        all_results = []
        databases = config.get("databases", ["cnipa"])

        for query in queries:
            for database in databases:
                # 调用专利检索工具
                try:
                    tool = self.tool_registry.get("patent_search")
                    if tool:
                        result = await tool.function(
                            query=query,
                            database=database,
                            limit=config.get("limit", 50),
                        )
                        all_results.extend(result.get("patents", []))
                except Exception as e:
                    self.logger.warning(f"检索失败: {database}, {query}, 错误: {e}")

        # 去重
        seen = set()
        unique_results = []
        for patent in all_results:
            patent_id = patent.get("patent_id", "")
            if patent_id and patent_id not in seen:
                seen.add(patent_id)
                unique_results.append(patent)

        return unique_results

    async def _filter_and_rank_results(
        self,
        results: Optional[list[Dict[str, Any]]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """
        筛选和排序结果

        Args:
            results: 检索结果
            config: 配置参数

        Returns:
            筛选排序后的结果
        """
        # 简单实现：根据相关性评分排序
        # 实际应该有更复杂的排序逻辑

        # 添加相关性评分（示例）
        for patent in results:
            # 简单评分：标题和摘要中关键词出现的次数
            score = 0
            # 这里可以添加更复杂的评分逻辑
            patent["relevance_score"] = score

        # 按评分排序
        sorted_results = sorted(
            results,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )

        # 限制返回数量
        limit = config.get("limit", 50)
        return sorted_results[:limit]
