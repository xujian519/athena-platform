#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强专利知识图谱管理器
Enhanced Patent Knowledge Graph Manager

处理大规模专利知识图谱数据的SQLite管理和导入系统
"""

import json
import logging
import multiprocessing as mp
import os
import queue
import sqlite3
import threading
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/documentation/logs/import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedPatentKnowledgeManager:
    """增强专利知识图谱管理器"""

    def __init__(self, db_path: str = None):
        """
        初始化专利知识图谱管理器

        Args:
            db_path: 数据库路径，默认为项目目录下的databases文件夹
        """
        if db_path is None:
            self.db_path = '/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db'
        else:
            self.db_path = db_path

        self.connection = None
        self.lock = threading.Lock()
        self.import_stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_entities': 0,
            'imported_entities': 0,
            'total_relations': 0,
            'imported_relations': 0,
            'errors': 0,
            'start_time': None,
            'processing_time': 0
        }

        # 确保目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        logger.info(f"🗄️ 初始化增强专利知识图谱管理器: {self.db_path}")

    def connect(self):
        """连接到数据库"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # 自动提交模式
            )

            # 性能优化设置
            self.connection.execute('PRAGMA journal_mode=WAL')
            self.connection.execute('PRAGMA synchronous=NORMAL')
            self.connection.execute('PRAGMA cache_size=100000')  # 100MB缓存
            self.connection.execute('PRAGMA temp_store=MEMORY')
            self.connection.execute('PRAGMA mmap_size=268435456')  # 256MB内存映射
            self.connection.execute('PRAGMA locking_mode=NORMAL')

            logger.info('✅ SQLite专利知识图谱数据库连接成功')
            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def initialize_schema(self):
        """初始化专利知识图谱数据库结构"""
        with self.lock:
            try:
                cursor = self.connection.cursor()

                # 创建增强实体表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS patent_entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id TEXT NOT NULL,  -- 原始实体ID
                        patent_id TEXT,  -- 专利ID
                        application_number TEXT,  -- 申请号
                        entity_type TEXT NOT NULL,
                        name TEXT,
                        value TEXT,
                        confidence REAL DEFAULT 1.0,
                        quality_level TEXT,  -- basic, high_quality, elite, rejected
                        layer TEXT,  -- 数据层级
                        source_file TEXT,
                        properties TEXT,  -- JSON格式存储额外属性
                        batch_number INTEGER,
                        processing_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建增强关系表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS patent_relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        relation_id TEXT,  -- 原始关系ID
                        source_entity_id TEXT NOT NULL,
                        target_entity_id TEXT NOT NULL,
                        source_patent_id TEXT,
                        target_patent_id TEXT,
                        relation_type TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        quality_level TEXT,
                        layer TEXT,
                        source_file TEXT,
                        properties TEXT,  -- JSON格式存储额外属性
                        weight REAL DEFAULT 1.0,
                        batch_number INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建专利元数据表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS patent_metadata (
                        patent_id TEXT PRIMARY KEY,
                        application_number TEXT UNIQUE,
                        title TEXT,
                        abstract TEXT,
                        quality_level TEXT,
                        file_path TEXT,
                        batch_number INTEGER,
                        entity_count INTEGER DEFAULT 0,
                        relation_count INTEGER DEFAULT 0,
                        processing_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 创建批次信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_info (
                        batch_number INTEGER PRIMARY KEY,
                        batch_size INTEGER,
                        file_path TEXT,
                        layer_stats TEXT,  -- JSON格式
                        processing_time REAL,
                        entity_count INTEGER DEFAULT 0,
                        relation_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'pending',  -- pending, processing, completed, error
                        error_message TEXT,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP
                    )
                """)

                # 创建索引
                indexes = [
                    'CREATE INDEX IF NOT EXISTS idx_patent_entities_entity_id ON patent_entities (entity_id)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_entities_patent_id ON patent_entities (patent_id)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_entities_type ON patent_entities (entity_type)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_entities_quality ON patent_entities (quality_level)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_entities_batch ON patent_entities (batch_number)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_relations_source ON patent_relations (source_entity_id)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_relations_target ON patent_relations (target_entity_id)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_relations_type ON patent_relations (relation_type)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_relations_batch ON patent_relations (batch_number)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_metadata_batch ON patent_metadata (batch_number)',
                    'CREATE INDEX IF NOT EXISTS idx_patent_metadata_quality ON patent_metadata (quality_level)'
                ]

                for index_sql in indexes:
                    cursor.execute(index_sql)

                # 创建全文搜索索引
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS patent_entities_fts USING fts5(
                        name, value, properties,
                        content='patent_entities',
                        content_rowid='id'
                    )
                """)

                # 创建统计信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS import_statistics (
                        id INTEGER PRIMARY KEY,
                        total_files INTEGER DEFAULT 0,
                        processed_files INTEGER DEFAULT 0,
                        total_entities INTEGER DEFAULT 0,
                        imported_entities INTEGER DEFAULT 0,
                        total_relations INTEGER DEFAULT 0,
                        imported_relations INTEGER DEFAULT 0,
                        errors INTEGER DEFAULT 0,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        processing_time REAL
                    )
                """)

                self.connection.commit()
                logger.info('✅ 增强专利知识图谱数据库结构初始化完成')
                return True

            except Exception as e:
                logger.error(f"❌ 数据库结构初始化失败: {e}")
                return False

    def process_json_file(self, file_path: str, batch_number: int = None) -> Dict[str, Any]:
        """
        处理单个JSON文件

        Args:
            file_path: JSON文件路径
            batch_number: 批次号

        Returns:
            处理结果统计
        """
        start_time = time.time()
        stats = {
            'file_path': file_path,
            'batch_number': batch_number,
            'entities_processed': 0,
            'relations_processed': 0,
            'patents_processed': 0,
            'errors': 0,
            'processing_time': 0
        }

        try:
            logger.info(f"📁 处理文件: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新批次信息
            if isinstance(data, dict) and 'batch_number' in data:
                batch_number = data['batch_number']
                batch_size = data.get('batch_size', len(data.get('results', [])))
                layer_stats = json.dumps(data.get('layer_stats', {}))

                self._update_batch_info(batch_number, batch_size, file_path, layer_stats, 'processing')

            # 处理结果
            if isinstance(data, dict) and 'results' in data:
                results = data['results']
                logger.info(f"   📊 处理 {len(results)} 个专利结果")

                for i, result in enumerate(results):
                    try:
                        self._process_patent_result(result, batch_number, file_path)
                        stats['patents_processed'] += 1

                        # 每100个专利提交一次，避免内存过大
                        if i % 100 == 0:
                            self.connection.commit()

                    except Exception as e:
                        logger.error(f"❌ 处理专利结果失败 (文件: {file_path}, 索引: {i}): {e}")
                        stats['errors'] += 1

            elif isinstance(data, list):
                # 处理列表格式数据
                logger.info(f"   📊 处理 {len(data)} 个结果")
                for i, result in enumerate(data):
                    try:
                        self._process_patent_result(result, batch_number, file_path)
                        stats['patents_processed'] += 1

                        if i % 100 == 0:
                            self.connection.commit()

                    except Exception as e:
                        logger.error(f"❌ 处理结果失败 (文件: {file_path}, 索引: {i}): {e}")
                        stats['errors'] += 1

            self.connection.commit()

            # 更新批次完成状态
            if batch_number:
                self._update_batch_info(batch_number, None, file_path, None, 'completed')

        except Exception as e:
            logger.error(f"❌ 处理文件失败 {file_path}: {e}")
            stats['errors'] += 1

            if batch_number:
                self._update_batch_info(batch_number, None, file_path, None, 'error', str(e))

        stats['processing_time'] = time.time() - start_time
        return stats

    def _process_patent_result(self, result: Dict[str, Any], batch_number: int, file_path: str):
        """处理单个专利结果"""
        patent_id = result.get('patent_id') or result.get('application_number')
        application_number = result.get('application_number')

        # 确保patent_id和application_number是字符串类型
        if patent_id is not None:
            patent_id = str(patent_id)
        if application_number is not None:
            application_number = str(application_number)

        # 处理quality字段 - 可能是字典或字符串
        quality_data = result.get('quality', 'unknown')
        if isinstance(quality_data, dict):
            quality_level = quality_data.get('quality_layer', 'unknown')
        else:
            quality_level = str(quality_data) if quality_data else 'unknown'

        file_info = result.get('file', {})
        # 处理layer字段 - 可能是字典或字符串
        layer_data = result.get('layer', 'unknown')
        if isinstance(layer_data, dict):
            layer = layer_data.get('layer_name', 'unknown')
        else:
            layer = str(layer_data) if layer_data else 'unknown'

        # 处理实体
        if 'entities' in result:
            entities = result['entities']
            if isinstance(entities, list):
                for entity in entities:
                    self._import_entity(entity, patent_id, application_number, quality_level, layer, file_path, batch_number)
                    self.import_stats['imported_entities'] += 1

        # 处理关系
        if 'relations' in result:
            relations = result['relations']
            if isinstance(relations, list):
                for relation in relations:
                    self._import_relation(relation, patent_id, quality_level, layer, file_path, batch_number)
                    self.import_stats['imported_relations'] += 1

        # 更新专利元数据
        if patent_id:
            self._update_patent_metadata(
                patent_id=patent_id,
                application_number=application_number,
                title=result.get('title'),
                abstract=result.get('abstract'),
                quality_level=quality_level,
                file_path=file_info.get('path'),
                batch_number=batch_number,
                processing_time=result.get('processing_time', 0)
            )

    def _import_entity(self, entity: Dict[str, Any], patent_id: str = None,
                      application_number: str = None, quality_level: str = 'unknown',
                      layer: str = 'unknown', file_path: str = None, batch_number: int = None):
        """导入单个实体"""
        try:
            cursor = self.connection.cursor()

            entity_id = entity.get('id') or str(entity.get('name', ''))
            entity_type = entity.get('type', 'unknown')
            name = entity.get('name') or entity.get('text') or ''
            value = entity.get('value') or entity.get('description') or ''
            confidence = entity.get('confidence', 1.0)

            # 序列化属性
            properties_to_save = {k: v for k, v in entity.items()
                                   if k not in ['id', 'type', 'name', 'value', 'confidence', 'text', 'description']}
            # 确保所有值都是JSON可序列化的
            for k, v in properties_to_save.items():
                if isinstance(v, (dict, list, tuple)):
                    properties_to_save[k] = str(v)  # 转换复杂对象为字符串
                elif v is None:
                    properties_to_save[k] = None

            properties = json.dumps(properties_to_save, ensure_ascii=False)

            cursor.execute("""
                INSERT OR REPLACE INTO patent_entities
                (entity_id, patent_id, application_number, entity_type, name, value,
                 confidence, quality_level, layer, source_file, properties, batch_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entity_id, patent_id, application_number, entity_type, name, value,
                  confidence, quality_level, layer, str(file_path), properties, batch_number))

            # 更新全文搜索索引
            cursor.execute("""
                INSERT INTO patent_entities_fts (rowid, name, value, properties)
                VALUES (last_insert_rowid(), ?, ?, ?)
            """, (name, value, properties))

        except Exception as e:
            logger.error(f"❌ 导入实体失败: {e}")
            raise

    def _import_relation(self, relation: Dict[str, Any], patent_id: str = None,
                        quality_level: str = 'unknown', layer: str = 'unknown',
                        file_path: str = None, batch_number: int = None):
        """导入单个关系"""
        try:
            cursor = self.connection.cursor()

            relation_id = relation.get('id') or ''
            source_entity_id = relation.get('source') or relation.get('source_id') or ''
            target_entity_id = relation.get('target') or relation.get('target_id') or ''
            relation_type = relation.get('type') or relation.get('relation_type') or 'related_to'
            confidence = relation.get('confidence', 1.0)
            weight = relation.get('weight', 1.0)

            # 序列化属性
            properties_to_save = {k: v for k, v in relation.items()
                                   if k not in ['id', 'source', 'target', 'source_id', 'target_id',
                                            'type', 'relation_type', 'confidence', 'weight']}
            # 确保所有值都是JSON可序列化的
            for k, v in properties_to_save.items():
                if isinstance(v, (dict, list, tuple)):
                    properties_to_save[k] = str(v)  # 转换复杂对象为字符串
                elif v is None:
                    properties_to_save[k] = None

            properties = json.dumps(properties_to_save, ensure_ascii=False)

            cursor.execute("""
                INSERT OR REPLACE INTO patent_relations
                (relation_id, source_entity_id, target_entity_id, source_patent_id,
                 relation_type, confidence, quality_level, layer, source_file,
                 properties, weight, batch_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (relation_id, source_entity_id, target_entity_id, patent_id,
                  relation_type, confidence, quality_level, layer, str(file_path),
                  properties, weight, batch_number))

        except Exception as e:
            logger.error(f"❌ 导入关系失败: {e}")
            raise

    def _update_patent_metadata(self, patent_id: str, application_number: str = None,
                               title: str = None, abstract: str = None, quality_level: str = 'unknown',
                               file_path: str = None, batch_number: int = None, processing_time: float = 0):
        """更新专利元数据"""
        try:
            cursor = self.connection.cursor()

            # 获取当前实体的关系数量
            cursor.execute("""
                SELECT COUNT(*) FROM patent_entities WHERE patent_id = ?
            """, (patent_id,))
            entity_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM patent_relations WHERE source_patent_id = ? OR target_patent_id = ?
            """, (patent_id, patent_id))
            relation_count = cursor.fetchone()[0]

            cursor.execute("""
                INSERT OR REPLACE INTO patent_metadata
                (patent_id, application_number, title, abstract, quality_level,
                 file_path, batch_number, entity_count, relation_count, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (patent_id, application_number, title, abstract, quality_level,
                  file_path, batch_number, entity_count, relation_count, processing_time))

        except Exception as e:
            logger.error(f"❌ 更新专利元数据失败: {e}")

    def _update_batch_info(self, batch_number: int, batch_size: int = None,
                          file_path: str = None, layer_stats: str = None,
                          status: str = 'pending', error_message: str = None):
        """更新批次信息"""
        try:
            cursor = self.connection.cursor()

            if status == 'processing':
                cursor.execute("""
                    INSERT OR REPLACE INTO batch_info
                    (batch_number, batch_size, file_path, layer_stats, status, started_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (batch_number, batch_size, str(file_path), layer_stats, status, datetime.now()))

            elif status == 'completed':
                # 统计该批次的实体和关系数量
                cursor.execute("""
                    SELECT COUNT(*) FROM patent_entities WHERE batch_number = ?
                """, (batch_number,))
                entity_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM patent_relations WHERE batch_number = ?
                """, (batch_number,))
                relation_count = cursor.fetchone()[0]

                cursor.execute("""
                    UPDATE batch_info
                    SET entity_count = ?, relation_count = ?, status = ?, completed_at = ?
                    WHERE batch_number = ?
                """, (entity_count, relation_count, status, datetime.now(), batch_number))

            elif status == 'error':
                cursor.execute("""
                    UPDATE batch_info
                    SET status = ?, error_message = ?, completed_at = ?
                    WHERE batch_number = ?
                """, (status, error_message, datetime.now(), batch_number))

        except Exception as e:
            logger.error(f"❌ 更新批次信息失败: {e}")

    def get_import_statistics(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        try:
            cursor = self.connection.cursor()

            # 基本统计
            cursor.execute('SELECT COUNT(*) FROM patent_entities')
            total_entities = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM patent_relations')
            total_relations = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(DISTINCT patent_id) FROM patent_entities WHERE patent_id IS NOT NULL')
            total_patents = cursor.fetchone()[0]

            # 质量分布
            cursor.execute("""
                SELECT quality_level, COUNT(*) FROM patent_entities GROUP BY quality_level
            """)
            quality_distribution = dict(cursor.fetchall())

            # 批次状态
            cursor.execute("""
                SELECT status, COUNT(*) FROM batch_info GROUP BY status
            """)
            batch_status = dict(cursor.fetchall())

            # 实体类型分布
            cursor.execute("""
                SELECT entity_type, COUNT(*) FROM patent_entities
                GROUP BY entity_type ORDER BY COUNT(*) DESC LIMIT 10
            """)
            entity_types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]

            # 关系类型分布
            cursor.execute("""
                SELECT relation_type, COUNT(*) FROM patent_relations
                GROUP BY relation_type ORDER BY COUNT(*) DESC LIMIT 10
            """)
            relation_types = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]

            return {
                'database_path': self.db_path,
                'total_patents': total_patents,
                'total_entities': total_entities,
                'total_relations': total_relations,
                'quality_distribution': quality_distribution,
                'batch_status': batch_status,
                'entity_types': entity_types,
                'relation_types': relation_types,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}

    def batch_import_from_directory(self, directory: str, pattern: str = '*.json',
                                   max_workers: int = 4) -> Dict[str, Any]:
        """
        批量导入目录中的JSON文件

        Args:
            directory: JSON文件目录
            pattern: 文件名模式
            max_workers: 最大工作线程数

        Returns:
            导入结果统计
        """
        start_time = time.time()
        self.import_stats['start_time'] = start_time

        # 查找所有JSON文件
        import glob
        json_files = glob.glob(os.path.join(directory, pattern))

        # 过滤掉处理摘要等小文件
        json_files = [f for f in json_files if os.path.getsize(f) > 1024 * 1024]  # 大于1MB

        self.import_stats['total_files'] = len(json_files)
        logger.info(f"📁 找到 {len(json_files)} 个JSON文件准备导入")

        # 按文件大小排序，先处理大文件
        json_files.sort(key=lambda x: os.path.getsize(x), reverse=True)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for i, file_path in enumerate(json_files):
                # 从文件名提取批次号
                batch_number = i + 1

                future = executor.submit(self.process_json_file, file_path, batch_number)
                futures.append(future)

                # 限制同时进行的任务数量
                if len(futures) >= max_workers * 2:
                    # 等待一些任务完成
                    completed = []
                    for future in futures:
                        if future.done():
                            completed.append(future.result())
                    futures = [f for f in futures if not f.done()]

            # 等待所有任务完成
            for future in futures:
                try:
                    result = future.result()
                    self.import_stats['processed_files'] += 1
                    self.import_stats['entities_processed'] += result['entities_processed']
                    self.import_stats['relations_processed'] += result['relations_processed']
                    self.import_stats['errors'] += result['errors']
                except Exception as e:
                    logger.error(f"❌ 批量导入任务失败: {e}")
                    self.import_stats['errors'] += 1

        self.import_stats['processing_time'] = time.time() - start_time

        # 保存导入统计
        self._save_import_statistics()

        return self.import_stats

    def _save_import_statistics(self):
        """保存导入统计信息"""
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO import_statistics
                (id, total_files, processed_files, total_entities, imported_entities,
                 total_relations, imported_relations, errors, start_time, end_time, processing_time)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.import_stats['total_files'],
                self.import_stats['processed_files'],
                self.import_stats.get('total_entities', 0),
                self.import_stats['imported_entities'],
                self.import_stats.get('total_relations', 0),
                self.import_stats['imported_relations'],
                self.import_stats['errors'],
                datetime.fromtimestamp(self.import_stats['start_time']),
                datetime.now(),
                self.import_stats['processing_time']
            ))

        except Exception as e:
            logger.error(f"❌ 保存导入统计失败: {e}")

    def optimize_database(self):
        """优化数据库性能"""
        try:
            cursor = self.connection.cursor()
            logger.info('🔧 开始数据库优化...')

            # 重建索引
            cursor.execute('REINDEX')
            logger.info('   ✅ 重建索引完成')

            # 分析表统计信息
            cursor.execute('ANALYZE')
            logger.info('   ✅ 分析统计信息完成')

            # 清理数据库
            cursor.execute('VACUUM')
            logger.info('   ✅ 数据库清理完成')

            logger.info('✅ 数据库优化完成')
            return True

        except Exception as e:
            logger.error(f"❌ 数据库优化失败: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        if not self.connection:
            logger.warning('⚠️ 数据库未连接')
            return {}

        try:
            cursor = self.connection.cursor()

            # 获取实体统计
            cursor.execute('SELECT COUNT(*) FROM patent_entities')
            total_entities = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(DISTINCT patent_id) FROM patent_entities WHERE patent_id IS NOT NULL')
            total_patents = cursor.fetchone()[0]

            cursor.execute('SELECT entity_type, COUNT(*) FROM patent_entities GROUP BY entity_type')
            entity_types = dict(cursor.fetchall())

            # 获取关系统计
            cursor.execute('SELECT COUNT(*) FROM patent_relations')
            total_relations = cursor.fetchone()[0]

            cursor.execute('SELECT relation_type, COUNT(*) FROM patent_relations GROUP BY relation_type')
            relation_types = dict(cursor.fetchall())

            # 获取批次统计
            cursor.execute('SELECT COUNT(*) FROM batch_info')
            total_batches = cursor.fetchone()[0]

            cursor.execute('SELECT status, COUNT(*) FROM batch_info GROUP BY status')
            batch_status = dict(cursor.fetchall())

            return {
                'total_entities': total_entities,
                'total_patents': total_patents,
                'total_relations': total_relations,
                'total_batches': total_batches,
                'entity_types': entity_types,
                'relation_types': relation_types,
                'batch_status': batch_status,
                'import_stats': self.import_stats
            }

        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info('🔒 数据库连接已关闭')

def main():
    """主函数 - 执行批量导入"""
    manager = EnhancedPatentKnowledgeManager()

    if not manager.connect():
        logger.info('❌ 数据库连接失败')
        return

    if not manager.initialize_schema():
        logger.info('❌ 数据库初始化失败')
        return

    logger.info('🚀 开始批量导入专利知识图谱数据...')

    # 导入专利批次数据
    stats = manager.batch_import_from_directory(
        directory='/private/tmp/patent_full_layered_output',
        pattern='patent_layered_batch_*.json',
        max_workers=2  # 由于文件较大，使用较少的线程
    )

    logger.info("\n📊 导入完成统计:")
    logger.info(f"   总文件数: {stats['total_files']}")
    logger.info(f"   已处理文件: {stats['processed_files']}")
    logger.info(f"   导入实体数: {stats['imported_entities']:,}")
    logger.info(f"   导入关系数: {stats['imported_relations']:,}")
    logger.info(f"   错误数量: {stats['errors']}")
    logger.info(f"   处理时间: {stats['processing_time']:.2f} 秒")

    # 获取最终统计
    final_stats = manager.get_statistics()
    logger.info(f"\n🎯 数据库最终状态:")
    logger.info(f"   专利总数: {final_stats.get('total_patents', 0):,}")
    logger.info(f"   实体总数: {final_stats.get('total_entities', 0):,}")
    logger.info(f"   关系总数: {final_stats.get('total_relations', 0):,}")

    # 优化数据库
    manager.optimize_database()

    manager.close()

if __name__ == '__main__':
    main()