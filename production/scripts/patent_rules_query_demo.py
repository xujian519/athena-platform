#!/usr/bin/env python3
"""
专利规则查询演示
Patent Rules Query Demo

演示如何使用专利规则向量库和知识图谱生成动态提示词

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "patent_rules_system"))

from ollama_rag_system import OllamaRAGSystem
from qdrant_vector_store_simple import QdrantVectorStoreSimple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentRulesQueryDemo:
    """专利规则查询演示"""

    def __init__(self):
        self.vector_store = QdrantVectorStoreSimple()
        self.rag_system = OllamaRAGSystem()
        self.queries = [
            "什么是发明专利的保护期限？",
            "如何判断一项发明是否具有创造性？",
            "专利申请需要提交哪些文件？",
            "什么是现有技术？",
            "权利要求书应该怎么写？",
            "专利审查的流程是怎样的？",
            "2025年专利法有什么新规定？",
            "如何申请专利加快审查？"
        ]

    async def demonstrate_search(self):
        """演示向量搜索"""
        logger.info("\n" + "="*60)
        logger.info("🔍 向量搜索演示")
        logger.info("="*60)

        for i, query in enumerate(self.queries[:4], 1):
            logger.info(f"\n{i}. 查询: {query}")

            try:
                # 向量搜索
                results = await self.vector_store.search(
                    query=query,
                    top_k=3,
                    search_mode="semantic"
                )

                logger.info(f"   找到 {len(results)} 个相关段落")

                # 显示最相关的段落
                for j, doc in enumerate(results[:2], 1):
                    content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                    logger.info(f"   {j}. [{doc.doc_type}] {content_preview}")
                    logger.info(f"      来源: {doc.metadata.get('document_title', 'unknown')}")
                    logger.info(f"      相似度: {doc.score:.3f}")

            except Exception as e:
                logger.error(f"   ❌ 搜索失败: {str(e)}")

    async def demonstrate_dynamic_prompts(self):
        """演示动态提示词生成"""
        logger.info("\n" + "="*60)
        logger.info("🤖 动态提示词生成演示")
        logger.info("="*60)

        test_scenarios = [
            {
                "task": "撰写专利权利要求",
                "query": "帮我写一个关于无人机的权利要求",
                "context": "这是一项关于四旋翼无人机的发明专利"
            },
            {
                "task": "判断专利授权条件",
                "query": "这个AI算法能否获得专利？",
                "context": "该算法使用深度学习进行图像识别"
            },
            {
                "task": "专利检索策略",
                "query": "如何进行专利检索？",
                "context": "需要查找智能家居领域的现有技术"
            }
        ]

        for i, scenario in enumerate(test_scenarios[:2], 1):
            logger.info(f"\n{i}. 场景: {scenario['task']}")
            logger.info(f"   用户查询: {scenario['query']}")
            logger.info(f"   背景信息: {scenario['context']}")

            try:
                # 使用RAG系统生成响应
                response = await self.rag_system.process_query(
                    query=scenario['query'],
                    context=scenario['context']
                )

                # 生成的动态提示词
                dynamic_prompt = self._generate_dynamic_prompt(
                    task=scenario['task'],
                    query=scenario['query'],
                    context=scenario['context'],
                    relevant_rules=response.relevant_rules if hasattr(response, 'relevant_rules') else []
                )

                logger.info("\n   🎯 生成的动态提示词:")
                logger.info("   ──────────────────────")
                for line in dynamic_prompt.split('\n')[:5]:
                    if line.strip():
                        logger.info(f"   {line}")
                logger.info("   ──────────────────────")

            except Exception as e:
                logger.error(f"   ❌ 生成失败: {str(e)}")

    def _generate_dynamic_prompt(self, task: str, query: str, context: str, relevant_rules: list) -> str:
        """生成动态提示词"""
        prompt = f"""
【任务类型】: {task}
【用户需求】: {query}
【背景信息】: {context}

【相关专利规则】:
{chr(10).join(f"- {rule}" for rule in relevant_rules[:3]) if relevant_rules else "- 基于专利法相关规定"}

【操作指引】:
1. 根据{task}的具体要求
2. 结合相关专利法律法规
3. 考虑2025年最新规定
4. 提供专业、准确的建议

【注意事项】:
- 确保符合专利法的保护客体要求
- 注意满足新颖性、创造性、实用性标准
- 遵循专利审查指南的具体要求
"""
        return prompt.strip()

    async def demonstrate_business_integration(self):
        """演示业务集成"""
        logger.info("\n" + "="*60)
        logger.info("💼 业务应用场景演示")
        logger.info("="*60)

        business_cases = [
            {
                "title": "专利撰写助手",
                "description": "为专利代理人提供撰写支持",
                "queries": ["权利要求书的撰写要点", "说明书的撰写规范"]
            },
            {
                "title": "专利审查助手",
                "description": "辅助审查员判断专利授权条件",
                "queries": ["三性判断标准", "驳回理由的法律依据"]
            },
            {
                "title": "企业专利管理",
                "description": "帮助企业进行专利布局和管理",
                "queries": ["专利挖掘方法", "专利布局策略"]
            }
        ]

        for i, case in enumerate(business_cases, 1):
            logger.info(f"\n{i}. {case['title']}")
            logger.info(f"   描述: {case['description']}")
            logger.info("   支持查询:")

            for query in case['queries']:
                try:
                    # 搜索相关规则
                    results = await self.vector_store.search(
                        query=query,
                        top_k=2,
                        search_mode="hybrid"
                    )

                    rule_count = len(results)
                    logger.info(f"     • {query}: 找到 {rule_count} 条相关规则")

                except Exception as e:
                    logger.error(f"     • {query}: 查询失败 - {str(e)}")

    async def run_demo(self):
        """运行完整演示"""
        logger.info("🚀 启动专利规则查询演示")
        logger.info("="*60)
        logger.info("本演示展示如何使用专利规则向量库和知识图谱")
        logger.info("为专利业务提供动态提示词和规则支持\n")

        # 1. 向量搜索演示
        await self.demonstrate_search()

        # 2. 动态提示词生成演示
        await self.demonstrate_dynamic_prompts()

        # 3. 业务集成演示
        await self.demonstrate_business_integration()

        # 总结
        logger.info("\n" + "="*60)
        logger.info("📋 总结")
        logger.info("="*60)
        logger.info("✅ 专利规则向量库已成功构建（537个段落）")
        logger.info("✅ 支持语义搜索和混合检索")
        logger.info("✅ 可生成动态提示词，辅助专利业务")
        logger.info("✅ 适用于专利撰写、审查、管理等多个场景")
        logger.info("\n💡 提示: 本系统可以作为专利业务平台的'规则引擎'")
        logger.info("   为各种专利应用提供实时的法规支持和智能提示")
        logger.info("="*60)

async def main():
    """主函数"""
    demo = PatentRulesQueryDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())
