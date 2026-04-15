#!/usr/bin/env python3
"""
标准化知识库适配器
Standardized Knowledge System Adapter

将现有知识库系统适配为标准化API接口。

Created by Athena + AI团队
Date: 2025-12-05
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any

# 添加路径以导入common模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.api_standards import (
    APIAdapter,
    KnowledgeQuery,
    KnowledgeResponse,
    KnowledgeType,
    ModuleName,
    StandardError,
    StatusCode,
)
from patent_knowledge_tools_enhancer import PatentKnowledgeToolsEnhancer

logger = logging.getLogger(__name__)

class StandardizedKnowledgeAdapter(APIAdapter):
    """标准化知识库适配器"""

    def __init__(self):
        super().__init__(ModuleName.KNOWLEDGE_SYSTEM)
        self.knowledge_system = None
        self._initialized = False

    async def initialize(self):
        """初始化知识库系统"""
        if not self._initialized:
            try:
                self.knowledge_system = PatentKnowledgeToolsEnhancer()
                self._initialized = True
                self.logger.log_module_operation(
                    self.module_name,
                    'knowledge_system_initialized',
                    {'status': 'success'}
                )
                logger.info('标准化知识库适配器初始化完成')
            except Exception as e:
                error_msg = f"知识库系统初始化失败: {str(e)}"
                logger.error(error_msg)
                raise StandardError(
                    error_code='INITIALIZATION_ERROR',
                    error_message=error_msg,
                    module=self.module_name
                ) from e

    def _validate_query(self, query: KnowledgeQuery) -> list[str]:
        """验证知识查询格式"""
        errors = []

        # 基础验证
        base_errors = super()._validate_query(query)
        errors.extend(base_errors)

        # 知识查询特定验证
        if not query.query_text.strip():
            errors.append('query_text cannot be empty')

        if query.max_results < 1:
            errors.append('max_results must be at least 1')

        if query.max_results > 100:
            errors.append('max_results cannot exceed 100')

        if not (0.0 <= query.relevance_threshold <= 1.0):
            errors.append('relevance_threshold must be between 0.0 and 1.0')

        # 验证知识类型
        if query.knowledge_types:
            valid_types = [kt.value for kt in KnowledgeType]
            for kt in query.knowledge_types:
                if kt.value not in valid_types:
                    errors.append(f"invalid knowledge_type: {kt.value}")

        return errors

    async def _process_query(self, query: KnowledgeQuery) -> KnowledgeResponse:
        """处理知识查询"""
        if not self._initialized:
            await self.initialize()

        datetime.now()

        try:
            # 转换为内部查询格式
            internal_query = self._convert_to_internal_query(query)

            # 执行知识搜索
            search_results = await self.knowledge_system.search_knowledge(internal_query)

            # 转换为标准响应格式
            response = self._convert_to_standard_response(query, search_results)

            # 记录模块操作
            self.logger.log_module_operation(
                self.module_name,
                'knowledge_search_completed',
                {
                    'query_text': query.query_text,
                    'results_count': len(response.results),
                    'search_time': response.search_time
                }
            )

            return response

        except Exception as e:
            logger.error(f"知识查询处理失败: {str(e)}")
            raise StandardError(
                error_code='KNOWLEDGE_SEARCH_ERROR',
                error_message=f"知识搜索失败: {str(e)}",
                module=self.module_name,
                details={
                    'query_text': query.query_text,
                    'query_type': query.query_type
                }
            ) from e

    def _convert_to_internal_query(self, query: KnowledgeQuery) -> Any:
        """转换为内部查询格式"""
        # 使用正确的类名和导入路径
        from knowledge.patent_knowledge_tools_enhancer import (
            KnowledgeSearchQuery,
            KnowledgeType,
        )

        # 转换知识类型
        internal_knowledge_types = []
        for kt in query.knowledge_types:
            if kt == KnowledgeType.PATENT_RULE:
                internal_knowledge_types.append(KnowledgeType.PATENT_RULE)
            elif kt == KnowledgeType.CASE_LAW:
                internal_knowledge_types.append(KnowledgeType.CASE_LAW)
            elif kt == KnowledgeType.TECHNICAL_STANDARD:
                internal_knowledge_types.append(KnowledgeType.TECHNICAL_STANDARD)
            elif kt == KnowledgeType.EXAMINATION_GUIDE:
                internal_knowledge_types.append(KnowledgeType.EXAMINATION_GUIDE)
            elif kt == KnowledgeType.LEGAL_REGULATION:
                internal_knowledge_types.append(KnowledgeType.LEGAL_REGULATION)

        # 如果没有指定知识类型，默认使用PATENT_RULE
        if not internal_knowledge_types:
            internal_knowledge_types = [KnowledgeType.PATENT_RULE]

        return KnowledgeSearchQuery(
            query_id=query.query_id,
            query_text=query.query_text,
            knowledge_types=internal_knowledge_types,
            max_results=query.max_results,
            relevance_threshold=query.relevance_threshold,
            filters=query.filters
        )

    def _convert_to_standard_response(self, query: KnowledgeQuery,
                                     search_results: dict[str, Any]) -> KnowledgeResponse:
        """转换为标准响应格式"""
        # 提取结果列表
        results = search_results.get('results', [])
        total_found = search_results.get('total_found', len(results))

        # 提取相关性分数
        relevance_scores = []
        for result in results:
            if isinstance(result, dict) and 'relevance_score' in result:
                relevance_scores.append(result['relevance_score'])
            else:
                relevance_scores.append(0.0)

        # 计算搜索时间
        search_time = search_results.get('search_time', 0.0)

        return KnowledgeResponse(
            query_id=query.query_id,
            source_module=self.module_name,
            status=StatusCode.SUCCESS,
            success=True,
            data=search_results,
            message=f"知识搜索完成，找到 {total_found} 个结果",
            results=results,
            total_found=total_found,
            search_time=search_time,
            relevance_scores=relevance_scores,
            metadata={
                'query_text': query.query_text,
                'knowledge_types': [kt.value for kt in query.knowledge_types],
                'max_results': query.max_results,
                'relevance_threshold': query.relevance_threshold
            }
        )

    async def search_patent_knowledge(self, query_text: str,
                                    knowledge_types: list[str] | None = None,
                                    max_results: int = 10,
                                    relevance_threshold: float = 0.5) -> KnowledgeResponse:
        """搜索专利知识的便捷方法"""
        if not knowledge_types:
            knowledge_types = [KnowledgeType.PATENT_RULE]

        # 转换知识类型字符串为枚举
        kt_enums = []
        for kt_str in knowledge_types:
            try:
                kt_enums.append(KnowledgeType(kt_str))
            except ValueError:
                logger.warning(f"未知的知识类型: {kt_str}，将使用PATENT_RULE")
                kt_enums.append(KnowledgeType.PATENT_RULE)

        query = KnowledgeQuery(
            source_module=ModuleName.KNOWLEDGE_SYSTEM,
            target_module=ModuleName.KNOWLEDGE_SYSTEM,
            query_text=query_text,
            knowledge_types=kt_enums,
            max_results=max_results,
            relevance_threshold=relevance_threshold
        )

        return await self.handle_query(query)

    async def get_patent_tools(self) -> dict[str, Any]:
        """获取专利工具列表"""
        if not self._initialized:
            await self.initialize()

        try:
            # 使用正确的方法名：get_patent_tools 而不是 get_available_tools
            tools_result = await self.knowledge_system.get_patent_tools()
            tools = tools_result.get('tools', {})

            self.logger.log_module_operation(
                self.module_name,
                'patent_tools_retrieved',
                {'tools_count': len(tools)}
            )

            return {
                'success': True,
                'tools': tools,
                'count': len(tools)
            }

        except Exception as e:
            logger.error(f"获取专利工具失败: {str(e)}")
            raise StandardError(
                error_code='TOOLS_RETRIEVAL_ERROR',
                error_message=f"获取专利工具失败: {str(e)}",
                module=self.module_name
            ) from e

    async def use_patent_tool(self, tool_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """使用专利工具"""
        if not self._initialized:
            await self.initialize()

        try:
            result = self.knowledge_system.use_patent_tool(tool_id, parameters)

            self.logger.log_module_operation(
                self.module_name,
                'patent_tool_used',
                {
                    'tool_id': tool_id,
                    'parameters': parameters,
                    'success': result.get('success', False)
                }
            )

            return result

        except Exception as e:
            logger.error(f"使用专利工具失败: {str(e)}")
            raise StandardError(
                error_code='TOOL_USAGE_ERROR',
                error_message=f"使用专利工具失败: {str(e)}",
                module=self.module_name,
                details={'tool_id': tool_id, 'parameters': parameters}
            ) from e

    async def get_system_statistics(self) -> dict[str, Any]:
        """获取系统统计信息"""
        if not self._initialized:
            await self.initialize()

        try:
            stats = self.knowledge_system.get_statistics()

            self.logger.log_module_operation(
                self.module_name,
                'statistics_retrieved',
                stats
            )

            return stats

        except Exception as e:
            logger.error(f"获取系统统计失败: {str(e)}")
            raise StandardError(
                error_code='STATISTICS_ERROR',
                error_message=f"获取系统统计失败: {str(e)}",
                module=self.module_name
            ) from e


# 单例模式的全局适配器实例
_standardized_knowledge_adapter = None

async def get_knowledge_adapter() -> StandardizedKnowledgeAdapter:
    """获取标准化的知识库适配器单例"""
    global _standardized_knowledge_adapter
    if _standardized_knowledge_adapter is None:
        _standardized_knowledge_adapter = StandardizedKnowledgeAdapter()
        await _standardized_knowledge_adapter.initialize()
    return _standardized_knowledge_adapter


# 测试代码
async def test_standardized_knowledge_adapter():
    """测试标准化知识库适配器"""
    adapter = StandardizedKnowledgeAdapter()
    await adapter.initialize()

    logger.info(str('=' * 60))
    logger.info('标准化知识库适配器测试')
    logger.info(str('=' * 60))

    # 测试知识搜索
    logger.info("\n1. 测试专利知识搜索:")
    try:
        response = await adapter.search_patent_knowledge(
            query_text='专利审查指南',
            knowledge_types=['patent_rule'],
            max_results=5,
            relevance_threshold=0.3
        )
        logger.info(f"   搜索成功: {response.success}")
        logger.info(f"   找到结果: {response.total_found} 个")
        logger.info(f"   搜索时间: {response.search_time:.3f} 秒")
        logger.info(f"   状态: {response.status.value}")
    except Exception as e:
        logger.info(f"   搜索失败: {str(e)}")

    # 测试获取专利工具
    logger.info("\n2. 测试获取专利工具:")
    try:
        tools_result = await adapter.get_patent_tools()
        logger.info(f"   获取成功: {tools_result.get('success', False)}")
        logger.info(f"   工具数量: {tools_result.get('count', 0)}")
        if tools_result.get('tools'):
            logger.info(f"   示例工具: {list(tools_result['tools'].keys())[:3]}")
    except Exception as e:
        logger.info(f"   获取失败: {str(e)}")

    # 测试使用专利工具
    logger.info("\n3. 测试使用专利工具:")
    try:
        tool_result = await adapter.use_patent_tool(
            tool_id='cn_patent_search',
            parameters={'keyword': '深度学习', 'limit': 3}
        )
        logger.info(f"   使用成功: {tool_result.get('success', False)}")
        logger.info(f"   工具名称: {tool_result.get('tool_name', 'Unknown')}")
    except Exception as e:
        logger.info(f"   使用失败: {str(e)}")

    # 测试系统统计
    logger.info("\n4. 测试系统统计:")
    try:
        stats = await adapter.get_system_statistics()
        logger.info("   统计获取成功")
        logger.info(f"   知识条目总数: {stats.get('knowledge_items_count', 0)}")
        logger.info(f"   工具总数: {stats.get('tools_count', 0)}")
        logger.info(f"   搜索成功率: {stats.get('search_success_rate', 0):.2%}")
    except Exception as e:
        logger.info(f"   统计失败: {str(e)}")

    logger.info(str("\n" + '=' * 60))
    logger.info('标准化知识库适配器测试完成')
    logger.info(str('=' * 60))


if __name__ == '__main__':
    asyncio.run(test_standardized_knowledge_adapter())
