#!/usr/bin/env python3
"""
专利规则构建系统 - 性能分析器
Patent Rules Builder - Performance Profiler

分析系统性能瓶颈并提供优化建议

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import io
import json
import logging
import pstats
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import c_profile
import psutil

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "patent_rules_system"))

from bert_extractor_simple import PatentEntityRelationExtractor
from nebula_graph_builder import NebulaGraphBuilder
from ollama_rag_system import OllamaRAGSystem
from qdrant_vector_store_simple import QdrantVectorStoreSimple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.baseline_metrics = self._get_baseline_metrics()

    def _get_baseline_metrics(self) -> dict:
        """获取基线指标"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters()._asdict(),
            "network_io": psutil.net_io_counters()._asdict()
        }

    @asynccontextmanager
    async def profile_section(self, section_name: str):
        """性能分析上下文管理器"""
        logger.info(f"开始性能分析: {section_name}")

        # 记录开始时间
        start_time = time.time()
        start_metrics = self._get_baseline_metrics()

        # 生成性能报告
        profile = c_profile.Profile()

        try:
            profile.enable()
            yield profile
            profile.disable()
        finally:
            # 记录结束时间和指标
            end_time = time.time()
            end_metrics = self._get_baseline_metrics()

            # 创建性能统计
            s = io.StringIO()
            ps = pstats.Stats(profile, stream=s)
            ps.sort_stats('cumulative')
            profile_stats = s.getvalue()

            # 保存结果
            self.results[section_name] = {
                "duration": end_time - start_time,
                "start_metrics": start_metrics,
                "end_metrics": end_metrics,
                "profile_stats": profile_stats,
                "performance_impact": self._calculate_impact(start_metrics, end_metrics)
            }

            # 输出简要报告
            self._print_summary(section_name, self.results[section_name])

    def _calculate_impact(self, start: dict, end: dict) -> dict:
        """计算性能影响"""
        return {
            "cpu_delta": end["cpu_percent"] - start["cpu_percent"],
            "memory_delta": end["memory_percent"] - start["memory_percent"],
            "disk_read_delta": end["disk_io"]["read_bytes"] - start["disk_io"]["read_bytes"],
            "disk_write_delta": end["disk_io"]["write_bytes"] - start["disk_io"]["write_bytes"]
        }

    def _print_summary(self, section_name: str, result: dict) -> Any:
        """打印性能摘要"""
        logger.info(f"\n性能分析 - {section_name}")
        logger.info("=" * 50)
        logger.info(f"耗时: {result['duration']:.3f}s")

        impact = result['performance_impact']
        if abs(impact['cpu_delta']) > 5:
            logger.warning(f"CPU使用率变化: {impact['cpu_delta']:.1f}%")
        if abs(impact['memory_delta']) > 5:
            logger.warning(f"内存使用率变化: {impact['memory_delta']:.1f}%")

        # 分析profile统计
        profile_lines = result['profile_stats'].split('\n')
        for line in profile_lines[:5]:
            if 'ncalls' in line and 'tottime' in line:
                logger.info(f"  {line}")

    async def analyze_system_performance(self):
        """分析系统整体性能"""
        logger.info("\n" + "="*60)
        logger.info("开始系统性能分析")
        logger.info("="*60)

        # 1. 初始化性能分析
        async with self.profile_section("系统初始化"):
            vector_store = QdrantVectorStoreSimple()
            await vector_store.create_collection()

        # 2. 向量生成性能
        async with self.profile_section("向量生成"):
            test_text = "专利法第一条为了保护专利权人的合法权益，鼓励发明创造"
            embedding = await vector_store.generate_embedding(test_text, "专利法")

        # 3. 文档索引性能
        async with self.profile_section("文档索引"):
            from qdrant_vector_store_simple import DocumentType, VectorDocument
            doc = VectorDocument(
                doc_id="perf_test_doc",
                content="测试文档内容，用于性能分析",
                doc_type=DocumentType.PATENT_LAW,
                metadata={"test": True}
            )
            await vector_store.index_document(doc)

        # 4. 向量搜索性能
        async with self.profile_section("向量搜索"):
            results = await vector_store.search(
                query="专利权",
                top_k=10,
                search_mode="semantic"
            )

        # 5. 实体提取性能
        async with self.profile_section("实体提取"):
            extractor = PatentEntityRelationExtractor()
            test_text = """
            中华人民共和国专利法
            第一条 为了保护专利权人的合法权益，鼓励发明创造，制定本法。
            第二条 本法所称的发明创造是指发明、实用新型和外观设计。
            """
            entities = await extractor.extract_entities(test_text, "test_doc")

        # 6. 知识图谱构建性能
        async with self.profile_section("知识图谱构建"):
            graph_builder = NebulaGraphBuilder()
            await graph_builder.initialize_space()

        # 7. RAG系统性能
        async with self.profile_section("RAG问答"):
            rag = OllamaRAGSystem()
            queries = [
                "专利的保护期限是多久？",
                "如何申请发明专利？",
                "2025年有什么新规定？"
            ]
            for query in queries:
                await rag.process_query(query)

        # 生成综合报告
        self._generate_comprehensive_report()

    def _generate_comprehensive_report(self) -> Any:
        """生成综合性能报告"""
        logger.info("\n" + "="*60)
        logger.info("性能瓶颈分析报告")
        logger.info("="*60)

        # 找出最慢的操作
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]['duration'],
            reverse=True
        )

        logger.info("\n📊 耗时排名（慢到快）：")
        for i, (name, result) in enumerate(sorted_results, 1):
            status = "🔴" if result['duration'] > 1.0 else "🟡" if result['duration'] > 0.5 else "🟢"
            logger.info(f"{i}. {status} {name}: {result['duration']:.3f}s")

        # 性能瓶颈分析
        bottlenecks = [
            name for name, result in self.results.items()
            if result['duration'] > 1.0
        ]

        logger.info(f"\n⚠️  性能瓶颈（>1s）：{len(bottlenecks)}个")
        for bottleneck in bottlenecks:
            logger.info(f"  - {bottleneck}")

        # 优化建议
        logger.info("\n💡 优化建议：")
        self._provide_optimization_suggestions(sorted_results)

        # 保存详细报告
        report_file = Path("/Users/xujian/Athena工作平台/production/test_reports/performance_analysis_report.json")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        # 准备报告数据
        report_data = {
            "analysis_time": datetime.now().isoformat(),
            "baseline_metrics": self.baseline_metrics,
            "performance_results": self.results,
            "bottlenecks": bottlenecks,
            "optimization_suggestions": self._get_optimization_suggestions()
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 详细报告已保存: {report_file}")

    def _provide_optimization_suggestions(self, sorted_results) -> None:
        """提供优化建议"""
        suggestions = [
            ("🚀 启用本地NLP系统", [
                "当前使用规则方法提取实体，速度较慢",
                "启用本地NLP服务可以显著提升性能",
                "修改配置文件使用专业NLP适配器"
            ]),
            ("💾 批量处理优化", [
                "避免逐个处理文档，使用批量操作",
                "VectorStore支持batch_index方法",
                "设置合理的批量大小（如50-100）"
            ]),
            ("🔄 缓存机制", [
                "增加查询结果缓存",
                "实现向量生成缓存",
                "使用Redis缓存热门查询"
            ]),
            ("📊 异步处理", [
                "使用asyncio并发处理",
                "I/O密集操作使用异步",
                "避免同步阻塞操作"
            ]),
            ("🗂️️ 数据结构优化", [
                "使用更高效的数据结构",
                "减少不必要的数据转换",
                "优化JSON序列化"
            ]),
            ("⚡ 向量搜索优化", [
                "使用近似最近邻搜索",
                "实现索引优化",
                "限制搜索范围和返回数量"
            ])
        ]

        for suggestion, details in suggestions:
            logger.info(f"\n{suggestion}")
            for detail in details:
                logger.info(f"  • {detail}")

    def _get_optimization_suggestions(self) -> list[dict]:
        """获取优化建议列表"""
        return [
            {
                "title": "启用本地NLP系统",
                "priority": "高",
                "impact": "显著",
                "description": "启用本地NLP服务可以显著提升实体提取性能"
            },
            {
                "title": "批量处理优化",
                "priority": "高",
                "impact": "高",
                "description": "使用批量操作替代逐个处理，可提升10-50倍性能"
            },
            {
                "title": "实现查询缓存",
                "priority": "中",
                "impact": "中",
                "description": "缓存查询结果可减少重复计算，提升响应速度"
            },
            {
                "title": "使用更快的向量搜索算法",
                "priority": "中",
                "impact": "中",
                "description": "实现近似搜索算法，在保证精度的同时提升速度"
            }
        ]

async def main():
    """主函数"""
    profiler = PerformanceProfiler()

    try:
        await profiler.analyze_system_performance()
    except Exception as e:
        logger.error(f"性能分析失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
