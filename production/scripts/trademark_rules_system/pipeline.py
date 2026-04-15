#!/usr/bin/env python3
"""
商标规则数据库主管道
Trademark Rules Database Main Pipeline

整合所有组件，构建完整的商标规则数据库：
1. 处理大PDF文件（分割）
2. 处理MD文件
3. 存储到PostgreSQL
4. 向量化到Qdrant
5. 构建知识图谱到NebulaGraph

作者: Athena AI系统
创建时间: 2025-01-15
版本: 1.0.0
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .database_manager import TrademarkDatabaseManager
from .graph_builder import TrademarkGraphBuilder
from .markdown_processor import MarkdownProcessor

# 本地导入
from .pdf_splitter import LargePDFSplitter
from .vector_store import TrademarkVectorStore

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrademarkRulesPipeline:
    """商标规则数据库主管道"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化管道

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 数据路径
        self.data_dir = Path(self.config.get('data_dir', './data/商标'))
        self.output_dir = Path(self.config.get('output_dir', './data/trademark_rules'))
        self.temp_dir = self.output_dir / 'temp'

        # 创建目录
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 数据库配置
        self.db_config = self.config.get('database', {})

        # 初始化组件
        self.pdf_splitter = None
        self.md_processor = None
        self.db_manager = None
        self.vector_store = None
        self.graph_builder = None

        # 统计信息
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'processed_files': 0,
            'total_norms': 0,
            'total_articles': 0,
            'total_vectors': 0,
            'total_graph_nodes': 0,
            'total_graph_edges': 0,
            'errors': []
        }

    async def initialize(self):
        """初始化所有组件"""
        logger.info("🚀 初始化商标规则数据库管道")

        # 1. 初始化数据库管理器
        self.db_manager = TrademarkDatabaseManager(self.db_config)

        # 连接PostgreSQL
        pg_config = {
            'host': self.db_config.get('pg_host', 'localhost'),
            'port': self.db_config.get('pg_port', 5441),
            'database': self.db_config.get('pg_database', 'trademark_database'),
            'user': self.db_config.get('pg_user', 'postgres'),
            'password': self.db_config.get('pg_password', 'your_password')
        }

        if not self.db_manager.connect_postgresql(pg_config):
            raise Exception("PostgreSQL连接失败")

        # 连接Qdrant
        qdrant_url = self.db_config.get('qdrant_url', 'http://localhost:6333')
        if not self.db_manager.connect_qdrant(qdrant_url):
            logger.warning("⚠️  Qdrant连接失败，向量化功能将不可用")

        # 连接NebulaGraph
        nebula_config = {
            'hosts': self.db_config.get('nebula_hosts', ['127.0.0.1']),
            'port': self.db_config.get('nebula_port', 9669),
            'username': self.db_config.get('nebula_user', 'root'),
            'password': self.db_config.get('nebula_password', 'nebula'),
            'space_name': self.db_config.get('nebula_space', 'trademark_graph')
        }

        if not self.db_manager.connect_nebula(nebula_config):
            logger.warning("⚠️  NebulaGraph连接失败，知识图谱功能将不可用")

        # 2. 初始化向量存储（使用BGE-M3和Reranker）
        if self.db_manager.qdrant_client:
            vector_config = {
                'qdrant_url': qdrant_url,
                'collection_name': 'trademark_rules',
                'model_name': 'bge-m3',
                'device': 'mps',  # 使用MPS加速
                'enable_reranker': True,
                'embedding_batch_size': 32,
                'upload_batch_size': 100
            }
            self.vector_store = TrademarkVectorStore(vector_config)
            await self.vector_store.initialize()

        # 3. 初始化知识图谱构建器
        if self.db_manager.nebula_client:
            self.graph_builder = TrademarkGraphBuilder(
                self.db_manager.nebula_client,
                {'space_name': 'trademark_graph'}
            )
            await self.graph_builder.create_schema()

        logger.info("✅ 管道初始化完成")

    async def process_pdf_file(self, pdf_path: str) -> dict[str, Any | None]:
        """
        处理大PDF文件

        Args:
            pdf_path: PDF文件路径

        Returns:
            处理结果
        """
        try:
            logger.info(f"📄 处理PDF文件: {pdf_path}")

            # 初始化分割器
            config = {
                'pdf_path': pdf_path,
                'output_dir': str(self.temp_dir),
                'chunk_size': 50,
                'enable_ocr': False,
                'progress_file': str(self.temp_dir / 'pdf_progress.json')
            }

            splitter = LargePDFSplitter(config)
            result = await splitter.process_single_pass()

            return result

        except Exception as e:
            logger.error(f"❌ 处理PDF失败: {e}")
            self.stats['errors'].append(f"PDF处理失败: {str(e)}")
            return None

    async def process_markdown_files(self) -> list[dict[str, Any]]:
        """
        处理所有Markdown文件

        Returns:
            处理结果列表
        """
        try:
            logger.info("📁 处理Markdown文件")

            config = {
                'data_dir': str(self.data_dir),
                'output_dir': str(self.temp_dir),
                'chunk_size': 1000,
                'chunk_overlap': 200
            }

            processor = MarkdownProcessor(config)
            result = await processor.process_directory()

            return result.get('documents', [])

        except Exception as e:
            logger.error(f"❌ 处理MD文件失败: {e}")
            self.stats['errors'].append(f"MD处理失败: {str(e)}")
            return []

    async def import_to_database(
        self,
        documents: list[dict[str, Any]]
    ) -> bool:
        """
        导入数据到数据库

        Args:
            documents: 文档列表

        Returns:
            是否成功
        """
        try:
            logger.info("💾 导入数据到PostgreSQL")

            for doc in tqdm(documents, desc="导入法规"):
                # 生成法规ID
                norm_id = hashlib.md5(doc['file_name'].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

                # 插入法规
                norm_data = {
                    'id': norm_id,
                    'name': doc['file_name'],
                    'document_number': doc['metadata'].get('document_number'),
                    'issuing_authority': doc['metadata'].get('issuing_authority'),
                    'issue_date': doc['metadata'].get('issue_date'),
                    'status': '现行有效',
                    'document_type': doc['metadata'].get('document_type'),
                    'file_path': doc['file_path'],
                    'full_text': ' '.join([c['text'] for c in doc.get('chunks', [])])
                }

                if self.db_manager.insert_norm(norm_data):
                    self.stats['total_norms'] += 1

                # 插入条款
                structure = doc.get('structure', {})
                articles = structure.get('articles', [])

                if articles:
                    articles_data = []
                    for _idx, article in enumerate(articles):
                        article_id = hashlib.md5(f"{norm_id}_{article['number']}".encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

                        articles_data.append({
                            'id': article_id,
                            'norm_id': norm_id,
                            'book_name': None,
                            'chapter_name': article.get('chapter'),
                            'section_name': None,
                            'article_number': article['number'],
                            'clause_number': None,
                            'item_number': None,
                            'original_text': article.get('content', ''),
                            'hierarchy_path': article.get('chapter')
                        })

                    count = self.db_manager.insert_articles_batch(articles_data)
                    self.stats['total_articles'] += count

            logger.info(f"✅ 导入完成: {self.stats['total_norms']} 法规, {self.stats['total_articles']} 条款")
            return True

        except Exception as e:
            logger.error(f"❌ 导入数据库失败: {e}")
            self.stats['errors'].append(f"数据库导入失败: {str(e)}")
            return False

    async def vectorize_and_store(
        self,
        documents: list[dict[str, Any]]
    ) -> bool:
        """
        向量化并存储到Qdrant

        Args:
            documents: 文档列表

        Returns:
            是否成功
        """
        if not self.vector_store:
            logger.warning("⚠️  向量存储未初始化，跳过")
            return False

        try:
            logger.info("🔢 向量化并存储到Qdrant")

            for doc in tqdm(documents, desc="向量化处理"):
                norm_id = hashlib.md5(doc['file_name'].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]
                chunks = doc.get('chunks', [])

                if chunks:
                    count = await self.vector_store.store_chunks(chunks, norm_id)
                    self.stats['total_vectors'] += count

            logger.info(f"✅ 向量化完成: {self.stats['total_vectors']} 向量")
            return True

        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}")
            self.stats['errors'].append(f"向量化失败: {str(e)}")
            return False

    async def build_knowledge_graph(
        self,
        documents: list[dict[str, Any]]
    ) -> bool:
        """
        构建知识图谱

        Args:
            documents: 文档列表

        Returns:
            是否成功
        """
        if not self.graph_builder:
            logger.warning("⚠️  知识图谱构建器未初始化，跳过")
            return False

        try:
            logger.info("🕸️ 构建知识图谱")

            for doc in tqdm(documents, desc="构建图谱"):
                norm_id = hashlib.md5(doc['file_name'].encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

                # 插入法规节点
                norm_data = {
                    'id': norm_id,
                    'name': doc['file_name'],
                    'document_type': doc['metadata'].get('document_type', 'unknown'),
                    'status': '现行有效'
                }

                norm_vid = await self.graph_builder.insert_norm_node(norm_data)
                if norm_vid:
                    self.stats['total_graph_nodes'] += 1

                # 插入条款节点
                structure = doc.get('structure', {})
                articles = structure.get('articles', [])

                if articles:
                    articles_data = []
                    for article in articles:
                        articles_data.append({
                            'article_number': article['number'],
                            'original_text': article.get('content', ''),
                            'chapter_name': article.get('chapter')
                        })

                    node_ids = await self.graph_builder.insert_article_nodes_batch(
                        articles_data,
                        norm_vid
                    )
                    self.stats['total_graph_nodes'] += len(node_ids)

                    # 提取概念
                    await self.graph_builder.extract_and_insert_concepts(articles_data)

            logger.info(f"✅ 知识图谱构建完成: {self.stats['total_graph_nodes']} 节点")
            return True

        except Exception as e:
            logger.error(f"❌ 构建知识图谱失败: {e}")
            self.stats['errors'].append(f"知识图谱构建失败: {str(e)}")
            return False

    async def run(self) -> dict[str, Any]:
        """
        运行完整管道

        Returns:
            处理结果
        """
        try:
            # 初始化
            await self.initialize()

            # 1. 处理大PDF文件
            pdf_files = list(self.data_dir.glob('*.pdf'))
            if pdf_files:
                for pdf_file in pdf_files:
                    if pdf_file.stat().st_size > 10 * 1024 * 1024:  # >10MB
                        await self.process_pdf_file(str(pdf_file))

            # 2. 处理Markdown文件
            documents = await self.process_markdown_files()
            self.stats['processed_files'] = len(documents)

            # 3. 导入到PostgreSQL
            await self.import_to_database(documents)

            # 4. 向量化到Qdrant
            await self.vectorize_and_store(documents)

            # 5. 构建知识图谱
            await self.build_knowledge_graph(documents)

            # 完成
            self.stats['end_time'] = datetime.now().isoformat()

            # 保存统计信息
            stats_file = self.output_dir / 'pipeline_stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)

            logger.info("✅ 管道执行完成！")
            logger.info(f"📊 统计信息: {json.dumps(self.stats, ensure_ascii=False, indent=2)}")

            return self.stats

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            self.stats['errors'].append(f"管道执行失败: {str(e)}")
            return self.stats

        finally:
            # 清理资源
            if self.db_manager:
                self.db_manager.close()

    async def cleanup(self):
        """清理临时文件"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                logger.info("🧹 临时文件已清理")
        except Exception as e:
            logger.warning(f"⚠️  清理临时文件失败: {e}")


async def main():
    """主函数"""
    # 配置管道
    config = {
        'data_dir': './data/商标',
        'output_dir': './data/trademark_rules',
        'database': {
            'pg_host': 'localhost',
            'pg_port': 5441,
            'pg_database': 'trademark_database',
            'pg_user': 'postgres',
            'pg_password': 'your_password',  # 请修改为实际密码
            'qdrant_url': 'http://localhost:6333',
            'nebula_hosts': ['127.0.0.1'],
            'nebula_port': 9669,
            'nebula_user': 'root',
            'nebula_password': 'nebula',
            'nebula_space': 'trademark_graph'
        }
    }

    # 创建并运行管道
    pipeline = TrademarkRulesPipeline(config)
    result = await pipeline.run()

    # 清理
    await pipeline.cleanup()

    print("\n" + "="*50)
    print("📊 商标规则数据库构建完成！")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
