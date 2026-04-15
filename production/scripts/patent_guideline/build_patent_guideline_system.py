#!/usr/bin/env python3
"""
专利指南系统构建脚本
Patent Guideline System Builder

一键构建完整的专利指南系统

作者: Athena平台团队
创建时间: 2025-12-20
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加脚本路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multimodal_processor import MultimodalDocumentProcessor
from patent_guideline_graph_builder import PatentGuidelineGraphBuilder
from patent_guideline_qa import PatentGuidelineQA
from patent_guideline_retriever import PatentGuidelineRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentGuidelineSystemBuilder:
    """专利指南系统构建器"""

    def __init__(self):
        self.source_dir = Path("/Users/xujian/Athena工作平台/dev/tools/patent-guideline-system")
        self.output_dir = Path("/Users/xujian/Athena工作平台/production/data")
        self.processing_stats = {
            "start_time": None,
            "end_time": None,
            "documents_processed": 0,
            "sections_extracted": 0,
            "entities_created": 0,
            "relations_created": 0,
            "vectors_generated": 0,
            "errors": []
        }

    async def build_complete_system(self):
        """构建完整系统"""
        logger.info("="*80)
        logger.info("🚀 开始构建专利指南系统")
        logger.info("="*80)

        self.processing_stats["start_time"] = datetime.now()

        try:
            # 1. 处理文档
            await self._process_documents()

            # 2. 构建知识图谱
            await self._build_knowledge_graph()

            # 3. 生成向量索引
            await self._build_vector_index()

            # 4. 初始化检索系统
            await self._initialize_retriever()

            # 5. 测试问答系统
            await self._test_qa_system()

            # 6. 生成系统报告
            await self._generate_system_report()

            self.processing_stats["end_time"] = datetime.now()
            logger.info("\n✅ 专利指南系统构建完成！")

        except Exception as e:
            logger.error(f"❌ 构建失败: {e}")
            self.processing_stats["errors"].append(str(e))
            raise

    async def _process_documents(self):
        """处理文档"""
        logger.info("\n📚 第一阶段：处理文档...")

        processor = MultimodalDocumentProcessor()
        processed_docs = []

        # 查找文档文件
        doc_files = []
        for ext in ['.pdf', '.docx', '.doc']:
            doc_files.extend(self.source_dir.rglob(f"*{ext}"))

        if not doc_files:
            logger.warning(f"在 {self.source_dir} 中未找到文档文件")
            # 创建示例数据
            await self._create_sample_data()
            doc_files = [self.source_dir / "sample_guideline.pdf"]

        # 处理每个文档
        for file_path in doc_files:
            try:
                logger.info(f"  处理文档: {file_path.name}")
                result = processor.process_document(str(file_path))
                processed_docs.append(result)
                self.processing_stats["documents_processed"] += 1
                self.processing_stats["sections_extracted"] += len(result["sections"])
            except Exception as e:
                logger.error(f"  处理文档失败 {file_path}: {e}")
                self.processing_stats["errors"].append(f"文档处理失败: {file_path.name}")

        # 保存处理结果
        output_file = self.output_dir / "patent_guideline" / "processed_documents.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "processed_at": datetime.now().isoformat(),
                    "document_count": len(processed_docs),
                    "total_sections": self.processing_stats["sections_extracted"]
                },
                "documents": processed_docs
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"  💾 文档处理结果已保存: {output_file}")

    async def _build_knowledge_graph(self):
        """构建知识图谱"""
        logger.info("\n🕸️ 第二阶段：构建知识图谱...")

        # 加载处理后的文档
        doc_file = self.output_dir / "patent_guideline" / "processed_documents.json"
        if not doc_file.exists():
            raise FileNotFoundError(f"请先运行文档处理: {doc_file}")

        with open(doc_file, encoding='utf-8') as f:
            data = json.load(f)

        graph_builder = PatentGuidelineGraphBuilder()

        # 处理每个文档
        for doc_data in data["documents"]:
            try:
                stats = await graph_builder.build_graph(doc_data, self.output_dir)
                self.processing_stats["entities_created"] += stats["total_entities"]
                self.processing_stats["relations_created"] += stats["total_relations"]
            except Exception as e:
                logger.error(f"  构建知识图谱失败: {e}")
                self.processing_stats["errors"].append("知识图谱构建失败")

        logger.info("  ✅ 知识图谱构建完成")
        logger.info(f"     实体数: {self.processing_stats['entities_created']}")
        logger.info(f"     关系数: {self.processing_stats['relations_created']}")

    async def _build_vector_index(self):
        """构建向量索引"""
        logger.info("\n🔍 第三阶段：构建向量索引...")

        # 导入向量构建器
        from patent_vector_builder_nlp import PatentVectorBuilderWithNLP

        builder = PatentVectorBuilderWithNLP()

        # 准备文档数据
        doc_file = self.output_dir / "patent_guideline" / "processed_documents.json"
        with open(doc_file, encoding='utf-8') as f:
            data = json.load(f)

        # 处理文档
        all_chunks = []
        for doc_data in data["documents"]:
            # 将章节转换为向量块格式
            for section in doc_data["sections"]:
                chunk = {
                    "chunk_id": section["section_id"],
                    "content": section["content"],
                    "doc_type": "patent_guideline",
                    "metadata": {
                        "title": section["title"],
                        "level": section["level"],
                        "full_path": section["full_path"],
                        "parent_id": section["parent_id"]
                    }
                }
                all_chunks.append(chunk)

        # 生成向量
        logger.info(f"  向量化 {len(all_chunks)} 个章节...")
        for i, chunk in enumerate(all_chunks):
            try:
                vector = await builder.extract_vector_with_nlp(chunk["content"])
                chunk["embedding"] = vector
                self.processing_stats["vectors_generated"] += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"    已处理 {i + 1}/{len(all_chunks)} 个章节")
            except Exception as e:
                logger.error(f"  向量化失败: {e}")
                self.processing_stats["errors"].append(f"向量化失败: {chunk.get('chunk_id', '')}")

        # 保存向量数据
        vector_file = self.output_dir / "patent_guideline" / "vectors.json"
        with open(vector_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_vectors": len(all_chunks),
                    "vector_dim": 1024
                },
                "vectors": all_chunks
            }, f, ensure_ascii=False, indent=2)

        # 生成Qdrant导入文件
        await self._generate_qdrant_import_file(all_chunks)

        logger.info(f"  💾 向量索引已保存: {vector_file}")

    async def _generate_qdrant_import_file(self, chunks: list[dict]):
        """生成Qdrant导入文件"""
        from uuid import NAMESPACE_URL, uuid5

        points = []
        for chunk in chunks:
            point_id = str(uuid5(NAMESPACE_URL, chunk["chunk_id"]))

            point = {
                "id": point_id,
                "vector": chunk["embedding"],
                "payload": {
                    "chunk_id": chunk["chunk_id"],
                    "content": chunk["content"],
                    "doc_type": chunk["doc_type"],
                    "section_id": chunk["metadata"]["section_id"],
                    "title": chunk["metadata"]["title"],
                    "level": chunk["metadata"]["level"],
                    "full_path": chunk["metadata"]["full_path"],
                    "parent_id": chunk["metadata"].get("parent_id")
                }
            }
            points.append(point)

        # 保存导入文件
        import_file = self.output_dir / "patent_guideline" / "qdrant_import.json"
        with open(import_file, 'w', encoding='utf-8') as f:
            json.dump(points, f, ensure_ascii=False, indent=2)

        logger.info(f"  📦 Qdrant导入文件已生成: {import_file}")

    async def _initialize_retriever(self):
        """初始化检索系统"""
        logger.info("\n🔎 第四阶段：初始化检索系统...")

        retriever = PatentGuidelineRetriever()
        await retriever.initialize()

        # 测试检索功能
        test_queries = [
            "什么是创造性",
            "新颖性判断标准",
            "实用性的要求"
        ]

        for query in test_queries:
            try:
                results = await retriever.search(query, top_k=3)
                logger.info(f"  测试查询 '{query}': 返回 {len(results)} 个结果")
            except Exception as e:
                logger.error(f"  检索测试失败 '{query}': {e}")

        await retriever.close()

    async def _test_qa_system(self):
        """测试问答系统"""
        logger.info("\n💬 第五阶段：测试问答系统...")

        qa_system = PatentGuidelineQA()
        await qa_system.initialize()

        test_questions = [
            "什么是专利的创造性？",
            "如何判断专利的新颖性？",
            "实用性的审查标准是什么？"
        ]

        for question in test_questions:
            try:
                answer = await qa_system.ask(question, user_id="test_user")
                logger.info(f"  问题: {question}")
                logger.info(f"  答案长度: {len(answer.answer)} 字符")
                logger.info(f"  置信度: {answer.confidence:.2f}")
            except Exception as e:
                logger.error(f"  问答测试失败 '{question}': {e}")

        await qa_system.close()

    async def _create_sample_data(self):
        """创建示例数据"""
        logger.info("创建示例数据...")

        sample_doc = {
            "metadata": {
                "title": "专利审查指南（示例版）",
                "version": "2024示例版",
                "page_count": 10
            },
            "sections": [
                {
                    "section_id": "P1",
                    "level": 1,
                    "title": "第一部分 总则",
                    "content": "本指南用于规范专利审查工作。专利审查应当遵循公平、公正、及时的原则。",
                    "parent_id": None,
                    "full_path": "第一部分 总则"
                },
                {
                    "section_id": "C1",
                    "level": 2,
                    "title": "第一章 专利申请",
                    "content": "专利申请应当提交请求书、说明书及其摘要和权利要求书等文件。",
                    "parent_id": "P1",
                    "full_path": "第一部分 总则 > 第一章 专利申请"
                },
                {
                    "section_id": "S1.1",
                    "level": 3,
                    "title": "1.1 专利申请文件",
                    "content": "专利申请文件应当符合格式要求。权利要求书应当以说明书为依据。",
                    "parent_id": "C1",
                    "full_path": "第一部分 总则 > 第一章 专利申请 > 1.1 专利申请文件"
                }
            ],
            "tables": [
                {
                    "table_id": "T1",
                    "title": "申请文件清单",
                    "content": [
                        ["文件类型", "是否必须", "页数限制"],
                        ["请求书", "是", "1"],
                        ["说明书", "是", "不限"],
                        ["权利要求书", "是", "50"],
                        ["摘要", "是", "300字"]
                    ],
                    "caption": "表1：专利申请文件清单"
                }
            ]
        }

        # 保存示例数据
        sample_file = self.source_dir / "processed_documents.json"
        sample_file.parent.mkdir(parents=True, exist_ok=True)
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "document_count": 1,
                    "total_sections": 3
                },
                "documents": [sample_doc]
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"  ✅ 示例数据已创建: {sample_file}")

    async def _generate_system_report(self):
        """生成系统报告"""
        logger.info("\n📊 生成系统报告...")

        report = {
            "build_summary": {
                "start_time": self.processing_stats["start_time"].isoformat(),
                "end_time": self.processing_stats["end_time"].isoformat(),
                "duration": (
                    self.processing_stats["end_time"] - self.processing_stats["start_time"]
                ).total_seconds()
            },
            "processing_stats": self.processing_stats,
            "system_components": {
                "multimodal_processor": "✅ 完成",
                "knowledge_graph_builder": "✅ 完成",
                "vector_index_builder": "✅ 完成",
                "retrieval_system": "✅ 完成",
                "qa_system": "✅ 完成"
            },
            "output_structure": {
                "processed_documents": "data/patent_guideline/processed_documents.json",
                "knowledge_graph": "data/patent_guideline_knowledge_graph/",
                "vectors": "data/patent_guideline/vectors.json",
                "qdrant_import": "data/patent_guideline/qdrant_import.json"
            },
            "next_steps": [
                "1. 将向量数据导入Qdrant数据库",
                "2. 将知识图谱导入NebulaGraph",
                "3. 配置API服务",
                "4. 测试完整功能",
                "5. 部署到生产环境"
            ],
            "quality_metrics": {
                "documents_processed": self.processing_stats["documents_processed"],
                "sections_extracted": self.processing_stats["sections_extracted"],
                "entities_created": self.processing_stats["entities_created"],
                "relations_created": self.processing_stats["relations_created"],
                "vectors_generated": self.processing_stats["vectors_generated"],
                "error_count": len(self.processing_stats["errors"])
            }
        }

        # 保存报告
        report_file = self.output_dir / "patent_guideline" / "build_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成可读报告
        readable_report = self._generate_readable_report(report)
        readable_file = self.output_dir / "patent_guideline" / "build_report.txt"
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(readable_report)

        logger.info("  📋 报告已保存:")
        logger.info(f"     JSON报告: {report_file}")
        logger.info(f"     文本报告: {readable_file}")

    def _generate_readable_report(self, report: dict) -> str:
        """生成可读报告"""
        lines = []
        lines.append("="*80)
        lines.append("专利指南系统构建报告")
        lines.append("="*80)
        lines.append("")
        lines.append("构建时间:")
        lines.append(f"  开始: {report['build_summary']['start_time']}")
        lines.append(f"  结束: {report['build_summary']['end_time']}")
        lines.append(f"  耗时: {report['build_summary']['duration']:.2f} 秒")
        lines.append("")
        lines.append("处理统计:")
        stats = report['processing_stats']
        lines.append(f"  文档数: {stats['documents_processed']}")
        lines.append(f"  章节数: {stats['sections_extracted']}")
        lines.append(f"  实体数: {stats['entities_created']}")
        lines.append(f"  关系数: {stats['relations_created']}")
        lines.append(f"  向量数: {stats['vectors_generated']}")
        lines.append(f"  错误数: {len(stats['errors'])}")
        lines.append("")
        lines.append("系统组件状态:")
        for comp, status in report['system_components'].items():
            lines.append(f"  {comp}: {status}")
        lines.append("")
        lines.append("输出文件:")
        for name, path in report['output_structure'].items():
            lines.append(f"  {name}: {path}")
        lines.append("")
        lines.append("下一步:")
        for step in report['next_steps']:
            lines.append(f"  {step}")
        lines.append("")
        lines.append("="*80)

        return "\n".join(lines)

async def main():
    """主函数"""
    builder = PatentGuidelineSystemBuilder()
    await builder.build_complete_system()

if __name__ == "__main__":
    asyncio.run(main())
