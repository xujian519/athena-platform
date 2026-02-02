#!/usr/bin/env python3
"""
分散式智能搜索架构 - 使用示例
Decentralized Intelligent Search Architecture - Usage Examples

展示如何使用新的智能搜索系统

作者: Athena AI系统
创建时间: 2025-12-05
版本: 1.0.0
"""

from datetime import datetime

from core.logging_config import setup_logging

# 设置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

# 导入系统组件
from ..athena.athena_smart_search import (
    SearchRequest,
    initialize_athena_smart_search,
)
from ..standards.base_search_tool import SearchType
from ..tools.adapted_patent_retriever import AdaptedPatentRetriever
from ..tools.adapted_web_search_manager import AdaptedWebSearchManager


class UsageExamples:
    """使用示例类"""

    def __init__(self):
        self.athena_smart_search = None

    async def setup(self):
        """设置系统"""
        logger.info("🔧 初始化智能搜索系统...")
        self.athena_smart_search = await initialize_athena_smart_search()

        # 注册搜索工具
        await self._register_search_tools()

    async def _register_search_tools(self):
        """注册搜索工具"""
        # 注册Web搜索工具
        web_tool = AdaptedWebSearchManager(
            {
                "web_search": {
                    "enable_tavily": True,
                    "enable_google_search": False,  # 需要API密钥
                    "enable_bocha": True,
                    "enable_metaso": True,
                    "enable_fallback": True,
                }
            }
        )
        await web_tool.initialize()
        await self.athena_smart_search.registry.register_tool(web_tool)

        # 注册专利搜索工具
        patent_tool = AdaptedPatentRetriever(
            {
                "patent_retrieval": {
                    "use_official_sources": True,
                    "use_dads_enhancement": True,
                    "guarantee_stability": True,
                }
            }
        )
        await patent_tool.initialize()
        await self.athena_smart_search.registry.register_tool(patent_tool)

        logger.info("✅ 搜索工具注册完成")

    async def example_1_basic_search(self):
        """示例1: 基础搜索"""
        logger.info("\n📚 示例1: 基础智能搜索")
        logger.info(str("-" * 40))

        # 简单搜索
        result = await self.athena_smart_search.search_simple(
            query_text="人工智能最新发展", max_results=10
        )

        logger.info(f"查询: {result.query}")
        logger.info(f"成功: {result.success}")
        logger.info(f"找到文档: {len(result.fused_documents)}")
        logger.info(f"使用工具: {', '.join(result.tools_used)}")
        logger.info(f"耗时: {result.total_time:.3f}秒")

        # 显示前3个结果
        logger.info("\n前3个搜索结果:")
        for i, doc in enumerate(result.fused_documents[:3]):
            logger.info(f"\n{i+1}. {doc.title}")
            logger.info(f"   来源: {doc.metadata.get('source_tool', 'unknown')}")
            logger.info(f"   相关性: {doc.relevance_score:.2f}")
            logger.info(f"   摘要: {doc.snippet[:100]}...")

    async def example_2_patent_search(self):
        """示例2: 专利搜索"""
        logger.info("\n📜 示例2: 智能专利搜索")
        logger.info(str("-" * 40))

        # 专利搜索
        result = await self.athena_smart_search.search_simple(
            query_text="机器学习算法专利", max_results=5
        )

        logger.info(f"查询: {result.query}")
        logger.info(f"找到专利: {len(result.fused_documents)}")
        logger.info(f"使用工具: {', '.join(result.tools_used)}")

        # 显示专利结果
        for i, doc in enumerate(result.fused_documents):
            logger.info(f"\n{i+1}. {doc.title}")
            logger.info(f"   专利号: {doc.metadata.get('patent_number', 'N/A')}")
            logger.info(f"   来源: {doc.metadata.get('source', 'unknown')}")
            logger.info(f"   摘要: {doc.content[:150]}...")

    async def example_3_advanced_search(self):
        """示例3: 高级搜索配置"""
        logger.info("\n⚙️ 示例3: 高级搜索配置")
        logger.info(str("-" * 40))

        # 创建高级搜索请求
        request = SearchRequest(
            query_text="深度学习在医疗领域的应用",
            search_type=SearchType.HYBRID,
            max_results=15,
            max_tools=3,
            timeout=30.0,
            enable_result_fusion=True,
            require_fallback=True,
            strategy="quality_optimized",
        )

        result = await self.athena_smart_search.search(request)

        logger.info("高级搜索完成:")
        logger.info(f"  查询: {result.query}")
        logger.info(f"  工具推荐: {len(result.tool_recommendations)}")
        logger.info(f"  使用工具: {', '.join(result.tools_used)}")
        logger.info(f"  文档总数: {result.total_documents}")
        logger.info(f"  唯一文档: {result.unique_documents}")

        # 显示工具推荐详情
        logger.info("\n工具推荐详情:")
        for i, rec in enumerate(result.tool_recommendations):
            logger.info(f"  {i+1}. {rec.tool_name} (评分: {rec.match_score:.2f})")
            logger.info(f"     理由: {'; '.join(rec.reasoning)}")

    async def example_4_session_search(self):
        """示例4: 会话搜索"""
        logger.info("\n💬 示例4: 会话化搜索")
        logger.info(str("-" * 40))

        # 创建会话
        session = self.athena_smart_search.create_session("research_session_001", "researcher_user")

        # 连续搜索
        search_queries = [
            "人工智能基础概念",
            "机器学习算法类型",
            "深度学习框架比较",
            "AI应用案例分析",
        ]

        logger.info("执行连续搜索...")

        for i, query in enumerate(search_queries, 1):
            result = await self.athena_smart_search.search_simple(
                query_text=query, max_results=3, session_id=session.session_id
            )

            logger.info(f"{i}. {query}: 找到 {len(result.fused_documents)} 个文档")

        # 显示会话统计
        logger.info("\n会话统计:")
        logger.info(f"  总搜索次数: {len(session.search_history)}")
        logger.info(f"  会话时长: {(datetime.now() - session.start_time).total_seconds():.1f}秒")

    async def example_5_feedback_learning(self):
        """示例5: 反馈学习"""
        logger.info("\n📚 示例5: 反馈学习")
        logger.info(str("-" * 40))

        # 模拟用户搜索和反馈
        search_scenarios = [
            {
                "query": "区块链技术在金融中的应用",
                "expected_tools": ["adapted_web_search_manager"],
                "success": True,
                "satisfaction": 0.9,
            },
            {
                "query": "US20230123456A1 patent details",
                "expected_tools": ["adapted_patent_retriever"],
                "success": True,
                "satisfaction": 0.8,
            },
            {
                "query": "人工智能专利检索方法",
                "expected_tools": ["adapted_patent_retriever", "adapted_web_search_manager"],
                "success": True,
                "satisfaction": 0.7,
            },
        ]

        logger.info("提供用户反馈...")

        for scenario in search_scenarios:
            # 执行搜索
            result = await self.athena_smart_search.search_simple(
                query_text=scenario["query"], max_results=5
            )

            # 添加反馈
            await self.athena_smart_search.add_search_feedback(
                query_text=scenario["query"],
                selected_tools=result.tools_used,
                success=scenario["success"],
                satisfaction=scenario["satisfaction"],
            )

            logger.info(f"  {scenario['query']}: 满意度 {scenario['satisfaction']:.1f}")

        # 显示学习统计
        selector_stats = self.athena_smart_search.selector.get_stats()
        logger.info("\n学习统计:")
        logger.info(f"  总选择次数: {selector_stats.get('total_selections', 0)}")
        logger.info(f"  成功率: {selector_stats.get('most_selected_tools', {})}")

    async def example_6_health_monitoring(self):
        """示例6: 健康监控"""
        logger.info("\n🏥 示例6: 系统健康监控")
        logger.info(str("-" * 40))

        # 执行健康检查
        health_status = await self.athena_smart_search.health_check()

        logger.info(f"系统状态: {health_status.get('status')}")
        logger.info(f"注册工具数: {health_status.get('registry_health', {})}")

        # 显示工具状态
        registry_health = health_status.get("registry_health", {})
        if isinstance(registry_health, dict):
            for tool_name, status in registry_health.items():
                if isinstance(status, dict):
                    logger.info(f"  {tool_name}: {status.get('status', 'unknown')}")

        # 获取系统统计
        stats = self.athena_smart_search.get_stats()
        logger.info("\n系统统计:")
        logger.info(f"  总搜索次数: {stats.get('total_searches', 0)}")
        logger.info(
            f"  成功率: {stats.get('successful_searches', 0)/max(stats.get('total_searches', 1), 1)*100:.1f}%"
        )
        logger.info(f"  活跃会话: {stats.get('active_sessions', 0)}")

    async def example_7_performance_optimization(self):
        """示例7: 性能优化"""
        logger.info("\n⚡ 示例7: 性能优化策略")
        logger.info(str("-" * 40))

        # 测试不同策略的性能
        strategies = ["speed_optimized", "quality_optimized", "comprehensive"]
        query = "云计算技术发展趋势"

        logger.info(f"测试查询: {query}")
        logger.info("不同策略性能对比:")

        for strategy in strategies:
            request = SearchRequest(
                query_text=query, max_results=10, strategy=strategy, enable_result_fusion=True
            )

            result = await self.athena_smart_search.search(request)

            logger.info(f"\n{strategy} 策略:")
            logger.info(f"  成功: {result.success}")
            logger.info(f"  工具数: {len(result.tools_used)}")
            logger.info(f"  文档数: {len(result.fused_documents)}")
            logger.info(f"  耗时: {result.total_time:.3f}秒")
            logger.info(f"  分析: {result.analysis_time:.3f}s")
            logger.info(f"  选择: {result.selection_time:.3f}s")
            logger.info(f"  搜索: {result.search_time:.3f}s")
            logger.info(f"  融合: {result.fusion_time:.3f}s")


async def main():
    """主函数"""
    logger.info("🚀 分散式智能搜索架构 - 使用示例")
    logger.info(str("=" * 60))

    examples = UsageExamples()

    try:
        # 初始化系统
        await examples.setup()

        # 运行所有示例
        await examples.example_1_basic_search()
        await examples.example_2_patent_search()
        await examples.example_3_advanced_search()
        await examples.example_4_session_search()
        await examples.example_5_feedback_learning()
        await examples.example_6_health_monitoring()
        await examples.example_7_performance_optimization()

        logger.info(str("\n" + "=" * 60))
        logger.info("✅ 所有使用示例执行完成!")

        logger.info("\n💡 系统特性总结:")
        logger.info("1. 🔍 智能查询分析 - 自动理解用户意图")
        logger.info("2. 🧠 智能工具选择 - 根据查询选择最佳工具")
        logger.info("3. ⚡ 并行搜索执行 - 同时使用多个工具")
        logger.info("4. 🔀 结果智能融合 - 合并和排序多工具结果")
        logger.info("5. 📚 会话管理 - 支持连续搜索上下文")
        logger.info("6. 🎯 反馈学习 - 基于用户反馈持续优化")
        logger.info("7. 🏥 健康监控 - 实时监控系统和工具状态")
        logger.info("8. ⚡ 性能优化 - 多种策略适应不同场景")

    except Exception as e:
        logger.error(f"❌ 示例执行失败: {e}")
        logger.info(f"\n❌ 执行失败: {e}")


# 入口点: @async_main装饰器已添加到main函数
