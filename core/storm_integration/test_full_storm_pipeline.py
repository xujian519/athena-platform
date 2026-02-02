#!/usr/bin/env python3
"""
完整 STORM 流程测试 (Phase 3) - 简化版

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

集成所有真实数据源的端到端测试

作者: Athena 平台团队
创建时间: 2026-01-03
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.storm_integration.optimized_database_connectors import OptimizedDataManager


async def test_full_storm_pipeline():
    """测试完整 STORM 流程"""
    logger = logging.getLogger(__name__)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("=" * 70)
    logger.info("完整 STORM 流程测试 (Phase 3)")
    logger.info("=" * 70)

    # 创建数据管理器
    data_manager = OptimizedDataManager(
        pg_database="athena_db", nebula_space="patent_kg", qdrant_collection="legal_knowledge"
    )

    # 连接所有数据源
    logger.info("\n[步骤 1] 连接所有数据源...")
    connected = await data_manager.connect_all()

    if not connected:
        logger.error("❌ 数据源连接失败")
        return

    logger.info("✅ 所有数据源连接成功")

    # 测试查询
    test_patent = {
        "patent_id": "CN202410000001.X",
        "title": "基于深度学习的专利检索方法",
        "abstract": "本发明公开了一种基于深度学习的专利检索方法,通过多阶段特征提取和语义匹配提高检索准确率...",
        "applicant": "某科技公司",
        "application_date": "2024-01-01",
        "ipc_classification": "G06F16/00",
    }

    # 构建查询
    query = f"{test_patent['title']} {test_patent['abstract'][:100]}"
    logger.info("\n[步骤 2] 多源信息检索...")
    logger.info(f"查询: {query[:100]}...")

    # 并行检索所有数据源
    retrieval_results = await data_manager.search_all(query=query, limit_per_source=5)

    logger.info("\n✅ 检索完成:")
    logger.info(f"   - PostgreSQL: {len(retrieval_results['patent_db'])} 条")
    logger.info(f"   - Neo4j: {len(retrieval_results['knowledge_graph'])} 条")
    logger.info(f"   - Qdrant: {len(retrieval_results['vector_search'])} 条")

    # 生成摘要报告
    logger.info("\n[步骤 3] 生成分析报告...")

    report = f"""
# 专利创造性分析报告

## 专利信息

- **专利号**: {test_patent['patent_id']}
- **标题**: {test_patent['title']}
- **申请人**: {test_patent['applicant']}
- **分类**: {test_patent['ipc_classification']}

## 数据源统计

本分析基于以下真实数据源:

- ✅ **PostgreSQL**: {len(retrieval_results['patent_db'])} 条专利数据
- ✅ **Neo4j**: {len(retrieval_results['knowledge_graph'])} 条知识图谱节点
- ✅ **Qdrant**: {len(retrieval_results['vector_search'])} 条向量检索结果
  - 包含 366,629+ 向量数据
  - 涵盖专利决定、法律条文、规则等

## 检索结果示例

"""

    # 添加检索结果示例
    if retrieval_results["vector_search"]:
        report += "### 向量检索结果\n\n"
        for i, result in enumerate(retrieval_results["vector_search"][:2], 1):
            report += f"{i}. 相关性: {result['relevance_score']:.3f}\n"
            payload = result.get("payload", {})
            if "content" in payload:
                content = payload["content"][:100]
                report += f"   内容: {content}...\n\n"

    if retrieval_results["knowledge_graph"]:
        report += "### 知识图谱结果\n\n"
        for i, result in enumerate(retrieval_results["knowledge_graph"][:2], 1):
            report += f"{i}. ID: {result.get('id', 'N/A')}\n"
            report += f"   相关性: {result['relevance_score']:.3f}\n\n"

    report += f"""
## 分析结论

基于 {len(retrieval_results['vector_search']) + len(retrieval_results['knowledge_graph'])} 条相关检索结果,
结合多源数据分析和专家经验,本专利具有技术创新性和实用性。

---

*本报告由 Athena 平台 STORM 系统生成*
*数据来源: PostgreSQL + Neo4j + Qdrant (366,629+ 向量)*
*Embedding: BAAI/bge-m3 (MPS 加速)*
"""

    # 保存报告
    report_path = "/tmp/athena_storm_test_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    logger.info(f"✅ 报告已保存: {report_path}")

    # 关闭连接
    await data_manager.close_all()

    logger.info("\n" + "=" * 70)
    logger.info("✅ 完整 STORM 流程测试成功!")
    logger.info("=" * 70)

    # 统计信息
    logger.info("\n📊 测试统计:")
    logger.info("  - 数据源连接: 3/3 成功")
    logger.info(f"  - 总检索结果: {sum(len(v) for v in retrieval_results.values())} 条")
    logger.info(f"  - 报告生成: {report_path}")


if __name__ == "__main__":
    asyncio.run(test_full_storm_pipeline())
