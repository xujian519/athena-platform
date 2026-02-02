#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据备份工具
为SQLite到Qdrant和Neo4j迁移创建完整备份
"""

import gzip
import json
import logging
import os
import pickle
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataBackupManager:
    """数据备份管理器"""

    def __init__(self):
        self.project_root = Path('/Users/xujian/Athena工作平台')
        self.backup_dir = self.project_root / 'backup' / f"migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # SQLite数据库路径
        self.sqlite_databases = {
            'knowledge_graph': self.project_root / 'data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db',
            'patent_cache': self.project_root / 'data/cache/patent_cache.db',
            'patent_index': self.project_root / 'data/patents/processed/indexed_patents.db',
            'patent_legal': self.project_root / 'data/support_data/databases/patent_legal_database.db',
            'legal_laws': self.project_root / 'data/support_data/databases/legal_laws_database.db',
            'athena_memory': self.project_root / 'data/support_data/databases/databases/memory_system/athena_memory.db',
            'memory_cold': self.project_root / 'data/memory/cold_tier.db',
            'vector_metadata': self.project_root / 'patent-platform/workspace/data/vector_metadata.db',
            'legal_knowledge': self.project_root / 'domains/legal-knowledge/db.sqlite3'
        }

        # 配置文件
        self.config_files = [
            self.project_root / 'config/database.yaml',
            self.project_root / 'config/storage_config.json',
            self.project_root / 'core/vector_db/hybrid_storage_manager.py'
        ]

    def backup_sqlite_databases(self):
        """备份所有SQLite数据库"""
        logger.info('📦 开始备份SQLite数据库...')

        backup_info = {}

        for db_name, db_path in self.sqlite_databases.items():
            if db_path.exists():
                try:
                    # 获取数据库信息
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()

                    # 获取表信息
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                    # 获取记录数
                    table_counts = {}
                    for table in tables:
                        try:
        # TODO: 检查SQL注入风险 - cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            table_counts[table] = cursor.fetchone()[0]
                        except:
                            table_counts[table] = 0

                    # 获取数据库大小
                    db_size = db_path.stat().st_size

                    backup_info[db_name] = {
                        'path': str(db_path),
                        'size_bytes': db_size,
                        'size_mb': round(db_size / 1024 / 1024, 2),
                        'tables': tables,
                        'table_counts': table_counts,
                        'backup_time': datetime.now().isoformat()
                    }

                    # 复制数据库文件
                    backup_path = self.backup_dir / f"{db_name}.db"
                    shutil.copy2(db_path, backup_path)

                    # 创建压缩备份
                    with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                        with open(db_path, 'rb') as f_in:
                            shutil.copyfileobj(f_in, f_out)

                    logger.info(f"✅ {db_name}: {len(tables)}个表, 总计{sum(table_counts.values())}条记录, {backup_info[db_name]['size_mb']}MB")

                    conn.close()

                except Exception as e:
                    logger.error(f"❌ 备份{db_name}失败: {e}")
                    backup_info[db_name] = {'error': str(e)}
            else:
                logger.warning(f"⚠️ 数据库不存在: {db_path}")
                backup_info[db_name] = {'status': 'not_found'}

        # 保存备份信息
        with open(self.backup_dir / 'sqlite_backup_info.json', 'w', encoding='utf-8') as f:
            json.dump(backup_info, f, ensure_ascii=False, indent=2)

        return backup_info

    def backup_config_files(self):
        """备份配置文件"""
        logger.info('📄 开始备份配置文件...')

        config_backup_info = {}

        for config_path in self.config_files:
            if config_path.exists():
                try:
                    backup_path = self.backup_dir / 'configs' / config_path.name
                    backup_path.parent.mkdir(exist_ok=True)
                    shutil.copy2(config_path, backup_path)

                    config_backup_info[config_path.name] = {
                        'original_path': str(config_path),
                        'backup_path': str(backup_path),
                        'size': config_path.stat().st_size,
                        'backup_time': datetime.now().isoformat()
                    }

                    logger.info(f"✅ 配置文件已备份: {config_path.name}")

                except Exception as e:
                    logger.error(f"❌ 备份配置文件失败 {config_path}: {e}")

        with open(self.backup_dir / 'config_backup_info.json', 'w', encoding='utf-8') as f:
            json.dump(config_backup_info, f, ensure_ascii=False, indent=2)

        return config_backup_info

    def export_qdrant_collections(self):
        """导出Qdrant集合信息"""
        logger.info('🔍 开始导出Qdrant集合信息...')

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter

# 导入标准化数据库工具
from shared.database.db_utils import DatabaseManager, build_safe_query

            client = QdrantClient('http://localhost:6333')

            collections_info = {
                'collections': [],
                'export_time': datetime.now().isoformat()
            }

            # 获取所有集合
            collections = client.get_collections().collections

            for collection in collections:
                collection_name = collection.name

                try:
                    # 获取集合信息
                    collection_info = client.get_collection(collection_name)

                    # 获取样本数据（最多10条）
                    sample_points = client.scroll(
                        collection_name=collection_name,
                        limit=10
                    )[0]

                    collections_info['collections'].append({
                        'name': collection_name,
                        'points_count': collection_info.points_count,
                        'vector_size': collection_info.config.params.vectors.size,
                        'distance': collection_info.config.params.vectors.distance.value,
                        'sample_data': [
                            {
                                'id': point.id,
                                'payload': point.payload,
                                'vector_dim': len(point.vector) if hasattr(point.vector, '__len__') else 'N/A'
                            }
                            for point in sample_points[:3]  # 只保存前3条样本
                        ]
                    })

                    logger.info(f"✅ 集合 {collection_name}: {collection_info.points_count} 条向量")

                except Exception as e:
                    logger.error(f"❌ 获取集合{collection_name}信息失败: {e}")
                    collections_info['collections'].append({
                        'name': collection_name,
                        'error': str(e)
                    })

            # 保存Qdrant信息
            with open(self.backup_dir / 'qdrant_collections_info.json', 'w', encoding='utf-8') as f:
                json.dump(collections_info, f, ensure_ascii=False, indent=2)

            return collections_info

        except Exception as e:
            logger.error(f"❌ 连接Qdrant失败: {e}")
            return {'error': str(e)}

    def create_migration_plan(self):
        """创建迁移计划"""
        logger.info('📋 创建迁移计划...')

        migration_plan = {
            'migration_id': f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'created_at': datetime.now().isoformat(),
            'phases': [
                {
                    'phase': 1,
                    'name': '向量数据迁移',
                    'description': '将SQLite中的向量数据迁移到Qdrant',
                    'target_databases': ['athena_memory', 'patent_index'],
                    'estimated_time': '2-3 days',
                    'priority': 'high'
                },
                {
                    'phase': 2,
                    'name': '知识图谱迁移',
                    'description': '将知识图谱数据迁移到Neo4j',
                    'target_databases': ['knowledge_graph'],
                    'estimated_time': '3-4 days',
                    'priority': 'high'
                },
                {
                    'phase': 3,
                    'name': '系统切换',
                    'description': '更新配置，切换到新的存储系统',
                    'target_databases': ['all'],
                    'estimated_time': '1-2 days',
                    'priority': 'medium'
                }
            ],
            'rollback_plan': {
                'enabled': True,
                'rollback_commands': [
                    '恢复SQLite数据库备份',
                    '回滚配置文件',
                    '重启相关服务'
                ]
            }
        }

        with open(self.backup_dir / 'migration_plan.json', 'w', encoding='utf-8') as f:
            json.dump(migration_plan, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 迁移计划已创建: {self.backup_dir / 'migration_plan.json'}")

        return migration_plan

    def run_full_backup(self):
        """执行完整备份"""
        logger.info('🚀 开始完整数据备份...')
        logger.info(f"备份目录: {self.backup_dir}")

        # 1. 备份SQLite数据库
        sqlite_info = self.backup_sqlite_databases()

        # 2. 备份配置文件
        config_info = self.backup_config_files()

        # 3. 导出Qdrant信息
        qdrant_info = self.export_qdrant_collections()

        # 4. 创建迁移计划
        migration_plan = self.create_migration_plan()

        # 5. 创建备份摘要
        backup_summary = {
            'backup_id': migration_plan['migration_id'],
            'backup_time': datetime.now().isoformat(),
            'backup_directory': str(self.backup_dir),
            'sqlite_databases': {
                'total': len(self.sqlite_databases),
                'backed_up': len([info for info in sqlite_info.values() if 'error' not in info]),
                'total_size_mb': sum(info.get('size_mb', 0) for info in sqlite_info.values() if 'size_mb' in info)
            },
            'config_files': len(self.config_files),
            'qdrant_collections': len(qdrant_info.get('collections', [])),
            'next_steps': [
                '1. 检查备份数据完整性',
                '2. 开始向量数据迁移',
                '3. 执行知识图谱迁移',
                '4. 系统测试和切换'
            ]
        }

        with open(self.backup_dir / 'backup_summary.json', 'w', encoding='utf-8') as f:
            json.dump(backup_summary, f, ensure_ascii=False, indent=2)

        # 打印备份摘要
        logger.info(str("\n" + '='*60))
        logger.info('📊 备份摘要')
        logger.info(str('='*60))
        logger.info(f"备份ID: {backup_summary['backup_id']}")
        logger.info(f"备份时间: {backup_summary['backup_time']}")
        logger.info(f"SQLite数据库: {backup_summary['sqlite_databases']['backed_up']}/{backup_summary['sqlite_databases']['total']}")
        logger.info(f"总数据大小: {backup_summary['sqlite_databases']['total_size_mb']:.2f} MB")
        logger.info(f"配置文件: {backup_summary['config_files']}")
        logger.info(f"Qdrant集合: {backup_summary['qdrant_collections']}")
        logger.info(f"\n备份目录: {self.backup_dir}")
        logger.info("\n下一步:")
        for step in backup_summary['next_steps']:
            logger.info(f"  {step}")
        logger.info(str('='*60))

        return backup_summary

def main():
    """主函数"""
    logger.info('🔄 Athena工作平台 - 数据备份工具')
    logger.info(str('='*60))

    # 创建备份管理器
    backup_manager = DataBackupManager()

    # 执行备份
    try:
        backup_summary = backup_manager.run_full_backup()

        logger.info("\n✅ 备份完成！")
        logger.info(f"📁 备份位置: {backup_summary['backup_directory']}")
        logger.info("\n⚠️ 请在开始迁移前验证备份完整性！")

    except Exception as e:
        logger.error(f"❌ 备份失败: {e}")
        logger.info(f"\n❌ 备份过程中出现错误: {e}")
        logger.info('请检查日志并重试。')

if __name__ == '__main__':
    main()