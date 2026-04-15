#!/usr/bin/env python3
"""
专利数据管道 - Athena工作平台专利数据处理和存储系统
Patent Data Pipeline - Patent Data Processing and Storage System for Athena Platform

优化专利数据从采集到知识图谱的完整处理流程

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

# Numpy兼容性导入
import asyncio
import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import redis

# 导入相关模块
from enhanced_patent_crawler import EnhancedPatentCrawler
from file_type_detector import FileTypeDetector
from multimodal_processor import MultimodalProcessor

from config.numpy_compatibility import random, sum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [PatentDataPipeline] %(message)s',
    handlers=[
        logging.FileHandler(f"patent_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentDataPipeline:
    """专利数据管道"""

    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path(__file__).parent

        # 目录结构
        self.dirs = {
            'raw_data': self.workspace_dir / 'data' / 'raw',
            'processed_data': self.workspace_dir / 'data' / 'processed',
            'vectors': self.workspace_dir / 'data' / 'vectors',
            'results': self.workspace_dir / 'results',
            'neo4j_data': self.workspace_dir / 'data' / 'neo4j_data',
            'cache': self.workspace_dir / 'cache'
        }

        # 确保目录存在
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        self.crawler = None
        self.file_detector = FileTypeDetector()
        self.multimodal_processor = MultimodalProcessor()

        # Redis连接
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
            self.redis_client.ping()
            logger.info('✅ Redis连接成功')
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {e}")

        # 数据库连接
        self.db_path = self.dirs['processed_data'] / 'patent_pipeline.db'
        self.init_database()

        # 管道统计
        self.stats = {
            'total_patents_processed': 0,
            'successful_processing': 0,
            'failed_processing': 0,
            'vectorized_patents': 0,
            'neo4j_imported': 0,
            'processing_start_time': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }

    def init_database(self):
        """初始化SQLite数据库"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS patent_processing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patent_id TEXT UNIQUE,
                        patent_number TEXT,
                        title TEXT,
                        processing_status TEXT,
                        processing_stage TEXT,
                        file_path TEXT,
                        vector_file_path TEXT,
                        neo4j_imported BOOLEAN DEFAULT FALSE,
                        quality_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS processing_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patent_id TEXT,
                        stage TEXT,
                        status TEXT,
                        message TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS pipeline_config (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
            logger.info('✅ 数据库初始化成功')

        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")

    async def start_pipeline(self):
        """启动专利数据管道"""
        logger.info('🚀 启动专利数据管道')

        # 初始化爬虫
        try:
            self.crawler = EnhancedPatentCrawler(use_distributed=False)
            await self.crawler.initialize()
            logger.info('✅ 专利爬虫初始化成功')
        except Exception as e:
            logger.error(f"❌ 专利爬虫初始化失败: {e}")
            return

        # 启动主处理循环
        await self.process_patent_pipeline()

    async def process_patent_pipeline(self):
        """处理专利数据管道主循环"""
        logger.info('🔄 开始专利数据处理流程')

        while True:
            try:
                # 获取待处理的专利
                pending_patents = await self.get_pending_patents()

                if not pending_patents:
                    logger.info('⏸️ 没有待处理的专利，等待30秒...')
                    await asyncio.sleep(30)
                    continue

                logger.info(f"📋 找到 {len(pending_patents)} 个待处理专利")

                # 批量处理专利
                for patent in pending_patents:
                    await self.process_single_patent(patent)

                # 更新统计信息
                await self.update_pipeline_stats()

                # 等待下一轮
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"❌ 专利处理流程出错: {e}")
                await asyncio.sleep(60)

    async def get_pending_patents(self) -> list[dict[str, Any]]:
        """获取待处理的专利"""
        pending_patents = []

        try:
            # 检查原始数据目录
            raw_files = list(self.dirs['raw_data'].glob('*.json'))

            for file_path in raw_files:
                # 检查是否已处理
                patent_id = file_path.stem

                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        'SELECT patent_id, processing_status FROM patent_processing WHERE patent_id = ?',
                        (patent_id,)
                    )
                    existing = cursor.fetchone()

                if not existing or existing[1] != 'completed':
                    # 加载专利数据
                    try:
                        with open(file_path, encoding='utf-8') as f:
                            patent_data = json.load(f)

                        patent_data['file_path'] = str(file_path)
                        patent_data['patent_id'] = patent_id
                        pending_patents.append(patent_data)

                    except Exception as e:
                        logger.error(f"❌ 读取专利文件失败 {file_path}: {e}")

            # 如果没有原始数据，可以运行爬虫获取
            if not pending_patents:
                logger.info('🔍 未找到原始专利数据，启动爬虫获取')
                crawled_patents = await self.crawl_patent_data()
                pending_patents.extend(crawled_patents)

        except Exception as e:
            logger.error(f"❌ 获取待处理专利失败: {e}")

        return pending_patents

    async def crawl_patent_data(self, search_queries: list[str] | None = None) -> list[dict[str, Any]]:
        """爬取专利数据"""
        if not search_queries:
            search_queries = [
                'artificial intelligence',
                'machine learning',
                'blockchain',
                'neural network',
                'big data'
            ]

        crawled_patents = []

        for query in search_queries:
            try:
                logger.info(f"🔍 搜索专利: {query}")

                # 使用爬虫搜索专利
                patents = await self.crawler.search_patents(query, limit=10)

                for patent in patents:
                    # 获取专利详情
                    details = await self.crawler.get_patent_details(patent['patent_url'])

                    if details:
                        # 保存到原始数据目录
                        patent_id = hashlib.md5(patent['patent_url'].encode('utf-8'), usedforsecurity=False).hexdigest()
                        file_path = self.dirs['raw_data'] / f"{patent_id}.json"

                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(details, f, indent=2, ensure_ascii=False)

                        details['patent_id'] = patent_id
                        details['file_path'] = str(file_path)
                        crawled_patents.append(details)

                await asyncio.sleep(2)  # 避免过快请求

            except Exception as e:
                logger.error(f"❌ 爬取专利数据失败 {query}: {e}")

        return crawled_patents

    async def process_single_patent(self, patent: dict[str, Any]) -> dict[str, Any]:
        """处理单个专利"""
        patent_id = patent.get('patent_id')
        processing_stages = [
            'validation',
            'content_extraction',
            'quality_assessment',
            'vectorization',
            'neo4j_preparation',
            'completion'
        ]

        logger.info(f"🔄 开始处理专利: {patent_id}")

        try:
            for stage in processing_stages:
                await self.process_patent_stage(patent, stage)

            # 标记处理完成
            await self.update_patent_status(patent_id, 'completed', 'completion')

            self.stats['successful_processing'] += 1
            logger.info(f"✅ 专利处理完成: {patent_id}")

        except Exception as e:
            await self.update_patent_status(patent_id, 'failed', stage, str(e))
            self.stats['failed_processing'] += 1
            logger.error(f"❌ 专利处理失败 {patent_id}: {e}")

        finally:
            self.stats['total_patents_processed'] += 1
            self.stats['last_update'] = datetime.now().isoformat()

    async def process_patent_stage(self, patent: dict[str, Any], stage: str):
        """处理专利特定阶段"""
        patent_id = patent.get('patent_id')

        try:
            await self.update_patent_status(patent_id, 'processing', stage)

            if stage == 'validation':
                await self.validate_patent_data(patent)
            elif stage == 'content_extraction':
                await self.extract_patent_content(patent)
            elif stage == 'quality_assessment':
                await self.assess_patent_quality(patent)
            elif stage == 'vectorization':
                await self.vectorize_patent(patent)
            elif stage == 'neo4j_preparation':
                await self.prepare_neo4j_data(patent)

            await self.log_processing_step(patent_id, stage, 'success', f"阶段 {stage} 处理成功")

        except Exception as e:
            await self.log_processing_step(patent_id, stage, 'error', str(e))
            raise

    async def validate_patent_data(self, patent: dict[str, Any]):
        """验证专利数据"""
        required_fields = ['patent_number', 'title', 'abstract']

        for field in required_fields:
            if field not in patent or not patent[field]:
                raise ValueError(f"缺少必需字段: {field}")

        # 验证专利号格式
        patent_number = patent['patent_number']
        if not isinstance(patent_number, str) or len(patent_number) < 5:
            raise ValueError(f"专利号格式无效: {patent_number}")

        logger.debug(f"✅ 专利数据验证通过: {patent['patent_id']}")

    async def extract_patent_content(self, patent: dict[str, Any]):
        """提取专利内容"""
        patent_id = patent['patent_id']

        # 使用多模态处理器提取文本内容
        file_path = patent.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                # 检测文件类型
                self.file_detector.detect_file_type(file_path)

                # 提取文本
                operations = ['extract_text', 'extract_metadata']
                result = await self.multimodal_processor.process_file(file_path, operations)

                if result['success']:
                    # 提取的内容添加到专利数据中
                    for op, op_result in result['results'].items():
                        if op_result['success']:
                            patent[f'extracted_{op}'] = op_result['result']

                logger.debug(f"✅ 专利内容提取完成: {patent_id}")

            except Exception as e:
                logger.warning(f"⚠️ 多模态处理失败，使用基础提取: {e}")

        # 确保有基本内容
        if 'content' not in patent and 'abstract' in patent:
            patent['content'] = patent['abstract']

        if 'content' not in patent and 'title' in patent:
            patent['content'] = patent['title']

    async def assess_patent_quality(self, patent: dict[str, Any]):
        """评估专利质量"""
        patent_id = patent['patent_id']

        quality_score = 0.0
        factors = {}

        # 标题质量 (20%)
        title = patent.get('title', '')
        title_length = len(title)
        if 10 <= title_length <= 200:
            factors['title_quality'] = 1.0
        elif title_length > 0:
            factors['title_quality'] = 0.5
        else:
            factors['title_quality'] = 0.0

        # 摘要质量 (30%)
        abstract = patent.get('abstract', '')
        abstract_length = len(abstract)
        if abstract_length >= 100:
            factors['abstract_quality'] = 1.0
        elif abstract_length >= 50:
            factors['abstract_quality'] = 0.7
        elif abstract_length > 0:
            factors['abstract_quality'] = 0.3
        else:
            factors['abstract_quality'] = 0.0

        # 内容完整性 (25%)
        required_fields = ['patent_number', 'title', 'abstract', 'inventors']
        complete_fields = sum(1 for field in required_fields if patent.get(field))
        factors['content_completeness'] = complete_fields / len(required_fields)

        # 技术相关性 (15%)
        content = patent.get('content', '').lower()
        tech_keywords = ['ai', 'machine learning', 'neural network', 'algorithm', 'data', 'software', 'system']
        tech_relevance = sum(1 for keyword in tech_keywords if keyword in content)
        factors['tech_relevance'] = min(tech_relevance / 3, 1.0)

        # 数据丰富度 (10%)
        extra_fields = ['filing_date', 'publication_date', 'claims', 'description']
        extra_field_count = sum(1 for field in extra_fields if patent.get(field))
        factors['data_richness'] = min(extra_field_count / len(extra_fields), 1.0)

        # 计算总分
        quality_score = (
            factors['title_quality'] * 0.2 +
            factors['abstract_quality'] * 0.3 +
            factors['content_completeness'] * 0.25 +
            factors['tech_relevance'] * 0.15 +
            factors['data_richness'] * 0.1
        )

        patent['quality_score'] = quality_score
        patent['quality_factors'] = factors

        logger.debug(f"✅ 专利质量评估完成: {patent_id}, 分数: {quality_score:.2f}")

    async def vectorize_patent(self, patent: dict[str, Any]):
        """向量化专利"""
        patent_id = patent['patent_id']

        try:
            # 准备向量化文本
            vector_text = patent.get('title', '') + ' ' + patent.get('abstract', '')

            if len(vector_text.strip()) < 10:
                raise ValueError('文本内容不足，无法向量化')

            # 生成向量 (这里使用简单的TF-IDF示例，实际应使用BERT等模型)
            vector = await self.generate_text_vector(vector_text)

            if vector is None:
                raise ValueError('向量生成失败')

            # 保存向量
            vector_file = self.dirs['vectors'] / f"{patent_id}.npy"
            np.save(vector_file, vector)

            # 保存向量元数据
            metadata_file = self.dirs['vectors'] / f"{patent_id}_metadata.json"
            metadata = {
                'patent_id': patent_id,
                'vector_file': str(vector_file),
                'vector_size': len(vector),
                'vectorization_method': 'tfidf_example',
                'created_at': datetime.now().isoformat(),
                'text_length': len(vector_text)
            }

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            patent['vector_file'] = str(vector_file)
            patent['vector_metadata'] = metadata

            # 缓存到Redis
            if self.redis_client:
                vector_key = f"patent_vector:{patent_id}"
                self.redis_client.setex(vector_key, 3600, vector.tobytes())

            self.stats['vectorized_patents'] += 1
            logger.debug(f"✅ 专利向量化完成: {patent_id}")

        except Exception as e:
            logger.error(f"❌ 专利向量化失败 {patent_id}: {e}")
            raise

    async def generate_text_vector(self, text: str) -> np.ndarray | None:
        """生成文本向量"""
        try:
            # 简单的TF-IDF向量化示例
            # 实际应用中应该使用预训练的BERT模型
            from sklearn.decomposition import TruncatedSVD
            from sklearn.feature_extraction.text import TfidfVectorizer

            # 使用预定义的词汇表和向量化器
            # 这里简化处理，实际应该训练或加载预训练模型
            vectorizer = TfidfVectorizer(
                max_features=768,  # BERT标准维度
                stop_words='english',
                ngram_range=(1, 2)
            )

            # 处理文本
            text_clean = text.lower().strip()

            # 生成TF-IDF向量
            try:
                tfidf_matrix = vectorizer.fit_transform([text_clean])

                # 使用SVD降维到768维
                svd = TruncatedSVD(n_components=768, random_state=42)
                vector = svd.fit_transform(tfidf_matrix)

                # 归一化
                vector = vector.flatten()
                vector = vector / np.linalg.norm(vector)

                return vector

            except Exception as e:
                logger.warning(f"TF-IDF向量化失败，使用随机向量: {e}")
                # 生成随机向量作为fallback
                return random(768)

        except ImportError:
            # 如果没有scikit-learn，生成随机向量
            logger.warning('scikit-learn未安装，使用随机向量')
            return random(768)

    async def prepare_neo4j_data(self, patent: dict[str, Any]):
        """准备Neo4j数据"""
        patent_id = patent['patent_id']

        try:
            # 准备节点数据
            node_data = {
                'patent_id': patent_id,
                'patent_number': patent.get('patent_number', ''),
                'title': patent.get('title', ''),
                'abstract': patent.get('abstract', ''),
                'quality_score': patent.get('quality_score', 0.0),
                'inventors': patent.get('inventors', []),
                'filing_date': patent.get('filing_date', ''),
                'publication_date': patent.get('publication_date', ''),
                'created_at': datetime.now().isoformat()
            }

            # 提取关键概念和关系
            concepts = await self.extract_concepts(patent)
            relationships = await self.extract_relationships(patent, concepts)

            # 准备完整的Neo4j数据
            neo4j_data = {
                'node': node_data,
                'concepts': concepts,
                'relationships': relationships,
                'metadata': {
                    'patent_id': patent_id,
                    'processing_date': datetime.now().isoformat(),
                    'data_version': '1.0'
                }
            }

            # 保存到Neo4j数据目录
            neo4j_file = self.dirs['neo4j_data'] / f"{patent_id}_neo4j.json"
            with open(neo4j_file, 'w', encoding='utf-8') as f:
                json.dump(neo4j_data, f, indent=2, ensure_ascii=False)

            patent['neo4j_file'] = str(neo4j_file)
            patent['neo4j_prepared'] = True

            self.stats['neo4j_imported'] += 1
            logger.debug(f"✅ Neo4j数据准备完成: {patent_id}")

        except Exception as e:
            logger.error(f"❌ Neo4j数据准备失败 {patent_id}: {e}")
            raise

    async def extract_concepts(self, patent: dict[str, Any]) -> list[dict[str, Any]]:
        """提取关键概念"""
        concepts = []

        # 从标题和摘要中提取关键词
        text = f"{patent.get('title', '')} {patent.get('abstract', '')}"

        # 简单的关键词提取 (实际应使用NLP库)
        tech_terms = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'algorithm', 'data processing', 'system', 'method', 'apparatus', 'device',
            'software', 'hardware', 'computer', 'network', 'database', 'security'
        ]

        for term in tech_terms:
            if term.lower() in text.lower():
                concepts.append({
                    'name': term,
                    'type': 'technical_term',
                    'confidence': 0.8,
                    'source': 'text_extraction'
                })

        # 从分类号中提取概念
        if 'classification' in patent:
            classification = patent['classification']
            if isinstance(classification, str):
                concepts.append({
                    'name': classification,
                    'type': 'classification',
                    'confidence': 1.0,
                    'source': 'patent_classification'
                })

        return concepts

    async def extract_relationships(self, patent: dict[str, Any],
                                   concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """提取关系"""
        relationships = []

        # 专利与概念的关系
        patent_id = patent['patent_id']
        for concept in concepts:
            relationships.append({
                'source': patent_id,
                'target': concept['name'],
                'relationship_type': 'HAS_CONCEPT',
                'confidence': concept['confidence']
            })

        # 发明人关系
        inventors = patent.get('inventors', [])
        if isinstance(inventors, list):
            for inventor in inventors:
                relationships.append({
                    'source': patent_id,
                    'target': inventor,
                    'relationship_type': 'INVENTED_BY',
                    'confidence': 1.0
                })

        return relationships

    async def update_patent_status(self, patent_id: str, status: str, stage: str,
                                  message: str = None):
        """更新专利处理状态"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO patent_processing
                    (patent_id, patent_number, title, processing_status, processing_stage, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (patent_id, '', '', status, stage))

                conn.commit()

        except Exception as e:
            logger.error(f"❌ 更新专利状态失败 {patent_id}: {e}")

    async def log_processing_step(self, patent_id: str, stage: str,
                                status: str, message: str):
        """记录处理步骤"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO processing_log (patent_id, stage, status, message)
                    VALUES (?, ?, ?, ?)
                ''', (patent_id, stage, status, message))

                conn.commit()

        except Exception as e:
            logger.error(f"❌ 记录处理步骤失败 {patent_id}: {e}")

    async def update_pipeline_stats(self):
        """更新管道统计信息"""
        try:
            # 保存统计到数据库
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO pipeline_config (key, value)
                    VALUES (?, ?)
                ''', ('pipeline_stats', json.dumps(self.stats)))

                conn.commit()

            # 保存统计到文件
            stats_file = self.dirs['results'] / 'pipeline_stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)

            # 缓存到Redis
            if self.redis_client:
                self.redis_client.setex('pipeline_stats', 300, json.dumps(self.stats))

            logger.info(f"📊 管道统计更新: 处理专利 {self.stats['total_patents_processed']} 个")

        except Exception as e:
            logger.error(f"❌ 更新管道统计失败: {e}")

    def get_pipeline_status(self) -> dict[str, Any]:
        """获取管道状态"""
        try:
            # 从数据库获取最新统计
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('SELECT value FROM pipeline_config WHERE key = ?', ('pipeline_stats',))
                row = cursor.fetchone()

                if row:
                    stats = json.loads(row[0])
                else:
                    stats = self.stats

            # 获取处理统计
            cursor = conn.execute('''
                SELECT processing_status, COUNT(*) as count
                FROM patent_processing
                GROUP BY processing_status
            ''')

            status_counts = dict(cursor.fetchall())

            # 获取阶段统计
            cursor = conn.execute('''
                SELECT processing_stage, COUNT(*) as count
                FROM patent_processing
                GROUP BY processing_stage
            ''')

            stage_counts = dict(cursor.fetchall())

            return {
                'stats': stats,
                'status_counts': status_counts,
                'stage_counts': stage_counts,
                'directory_status': self.get_directory_status(),
                'last_update': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 获取管道状态失败: {e}")
            return {'error': str(e), 'stats': self.stats}

    def get_directory_status(self) -> dict[str, Any]:
        """获取目录状态"""
        status = {}

        for name, path in self.dirs.items():
            if path.exists():
                files = list(path.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                dir_count = len([f for f in files if f.is_dir()])
                size = sum(f.stat().st_size for f in files if f.is_file())

                status[name] = {
                    'exists': True,
                    'file_count': file_count,
                    'directory_count': dir_count,
                    'total_size': size,
                    'total_size_human': self.format_size(size)
                }
            else:
                status[name] = {
                    'exists': False,
                    'file_count': 0,
                    'directory_count': 0,
                    'total_size': 0,
                    'total_size_human': '0 B'
                }

        return status

    def format_size(self, size_bytes: int) -> str:
        """格式化大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}PB"

    def export_processed_data(self, output_format: str = 'json') -> str:
        """导出处理后的数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if output_format == 'json':
            output_file = self.dirs['results'] / f'processed_patents_{timestamp}.json'

            processed_data = []
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute('''
                        SELECT patent_id, patent_number, title, processing_status,
                               processing_stage, quality_score, vector_file_path, neo4j_imported
                        FROM patent_processing
                        WHERE processing_status = 'completed'
                    ''')

                    for row in cursor.fetchall():
                        processed_data.append({
                            'patent_id': row[0],
                            'patent_number': row[1],
                            'title': row[2],
                            'processing_status': row[3],
                            'processing_stage': row[4],
                            'quality_score': row[5],
                            'vector_file_path': row[6],
                            'neo4j_imported': bool(row[7])
                        })

                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'total_patents': len(processed_data),
                    'pipeline_stats': self.get_pipeline_status(),
                    'patents': processed_data
                }

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                logger.info(f"💾 处理数据已导出到: {output_file}")
                return str(output_file)

            except Exception as e:
                logger.error(f"❌ 导出数据失败: {e}")
                raise

        else:
            raise ValueError(f"不支持的导出格式: {output_format}")

async def main():
    """主函数 - 启动专利数据管道"""
    logger.info('🚀 专利数据管道启动')
    logger.info(str('=' * 50))

    pipeline = PatentDataPipeline()

    try:
        # 显示管道状态
        status = pipeline.get_pipeline_status()
        logger.info("📊 管道状态:")
        logger.info(f"   总处理专利: {status['stats']['total_patents_processed']}")
        logger.info(f"   成功处理: {status['stats']['successful_processing']}")
        logger.info(f"   失败处理: {status['stats']['failed_processing']}")
        logger.info(f"   向量化专利: {status['stats']['vectorized_patents']}")
        logger.info(f"   Neo4j准备: {status['stats']['neo4j_imported']}")

        # 显示目录状态
        logger.info("\n📁 目录状态:")
        for name, dir_status in status['directory_status'].items():
            if dir_status['exists']:
                logger.info(f"   {name}: {dir_status['file_count']} 文件, {dir_status['total_size_human']}")
            else:
                logger.info(f"   {name}: ❌ 不存在")

        # 启动处理管道
        logger.info("\n🔄 启动专利数据处理管道...")
        await pipeline.start_pipeline()

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断，管道停止")
    except Exception as e:
        logger.error(f"❌ 管道运行错误: {e}")
    finally:
        logger.info('🔌 专利数据管道已关闭')

if __name__ == '__main__':
    asyncio.run(main())
