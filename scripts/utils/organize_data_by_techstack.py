#!/usr/bin/env python3
"""
按照技术栈整理数据目录
- Neo4j知识图谱数据
- Qdrant向量库数据
- 其他支撑数据

作者：小娜
日期：2025-12-07
"""

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataOrganizer:
    """数据整理器"""

    def __init__(self):
        self.base_dir = Path('/Users/xujian/Athena工作平台/data')
        self.backup_dir = self.base_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.neo4j_dir = self.base_dir / 'knowledge_graph_neo4j'
        self.qdrant_dir = self.base_dir / 'vectors_qdrant'
        self.support_dir = self.base_dir / 'support_data'

        # 创建新目录结构
        for dir_path in [self.backup_dir, self.neo4j_dir, self.qdrant_dir, self.support_dir]:
            dir_path.mkdir(exist_ok=True)

        # 数据分类映射
        self.neo4j_patterns = {
            # 知识图谱数据
            'kg': ['knowledge_graph', 'knowledge_graphs', 'patent_kg', 'merged_knowledge_graphs'],
            'legal': ['legal_knowledge_graph', 'fixed_legal_knowledge_graph'],
            'patent': ['patent_', '专利无效'],
            'professional': ['professional_knowledge_graphs'],
            'judgment': ['judgment_kg'],
            'neo4j': ['neo4j_', 'vertices_export.csv', '.cypher'],
        }

        self.qdrant_patterns = {
            # 向量库数据
            'vectors': ['vectors', 'vector_', '专利无效向量库'],
            'ai_terminology': ['ai_terminology'],
            'technical_terms': ['technical_terms'],
            'qdrant': ['qdrant'],
        }

        # 文件大小记录
        self.file_hash_map = {}
        self.duplicate_files = []

    def get_file_hash(self, file_path) -> Any | None:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def is_duplicate(self, file_path) -> bool:
        """检查文件是否重复"""
        file_hash = self.get_file_hash(file_path)
        if file_hash in self.file_hash_map:
            self.duplicate_files.append((file_path, self.file_hash_map[file_hash]))
            return True
        self.file_hash_map[file_hash] = file_path
        return False

    def categorize_file(self, file_path) -> Any:
        """分类文件"""
        file_path_str = str(file_path).lower()

        # 检查是否属于Neo4j知识图谱
        for category, patterns in self.neo4j_patterns.items():
            for pattern in patterns:
                if pattern in file_path_str:
                    return 'neo4j', category

        # 检查是否属于Qdrant向量库
        for category, patterns in self.qdrant_patterns.items():
            for pattern in patterns:
                if pattern in file_path_str:
                    return 'qdrant', category

        # 默认归类到支撑数据
        return 'support', 'other'

    def organize_directory(self, src_dir, dest_base) -> Any:
        """整理目录"""
        if not src_dir.exists():
            return

        for item in src_dir.iterdir():
            if item.is_file():
                # 跳过系统文件
                if item.name.startswith('.'):
                    continue

                # 检查重复
                if self.is_duplicate(item):
                    logger.info(f"跳过重复文件: {item}")
                    continue

                # 分类
                tech_stack, category = self.categorize_file(item)

                # 确定目标位置
                if tech_stack == 'neo4j':
                    dest_dir = dest_base / 'knowledge_graph_neo4j' / category
                elif tech_stack == 'qdrant':
                    dest_dir = dest_base / 'vectors_qdrant' / category
                else:
                    dest_dir = dest_base / 'support_data' / category

                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / item.name

                # 移动文件
                try:
                    shutil.move(str(item), str(dest_path))
                    logger.info(f"移动: {item.name} -> {tech_stack}/{category}/")
                except Exception as e:
                    logger.error(f"移动失败 {item}: {e}")

            elif item.is_dir() and item.name not in [
                'knowledge_graph_neo4j', 'vectors_qdrant', 'support_data',
                'backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
            ]:
                # 递归处理子目录
                self.organize_directory(item, dest_base)

    def organize_neo4j_data(self) -> Any:
        """整理Neo4j知识图谱数据"""
        logger.info('整理Neo4j知识图谱数据...')

        # 创建子目录
        subdirs = [
            'raw_data', 'import_scripts', 'processed_data',
            'schemas', 'queries', 'exports'
        ]
        for subdir in subdirs:
            (self.neo4j_dir / subdir).mkdir(exist_ok=True)

        # 移动和整理知识图谱相关文件
        neo4j_related = [
            'patent_kg_superfast',
            'patent_knowledge_graph',
            'neo4j_data',
            'neo4j_import',
            'knowledge_graph',
            'knowledge_graphs',
            'merged_knowledge_graphs',
            'fixed_legal_knowledge_graph',
            'production_legal_knowledge_graph',
            'professional_knowledge_graphs',
            'patent_judgment_kg',
            'patent_invalid_knowledge_graph',
            'patent_legal_knowledge_graph',
            'patent_reconsideration_knowledge_graph',
            'technical_terms_knowledge_graph'
        ]

        for item in neo4j_related:
            src = self.base_dir / item
            if src.exists():
                if src.is_file():
                    if not self.is_duplicate(src):
                        shutil.move(str(src), str(self.neo4j_dir / 'raw_data' / src.name))
                else:
                    dest = self.neo4j_dir / 'raw_data' / src.name
                    shutil.move(str(src), str(dest))
                    logger.info(f"移动目录: {item} -> neo4j/raw_data/")

        # 移动特定的Neo4j文件
        neo4j_files = [
            'unified_legal_kg_import.cypher',
            'unified_legal_kg_statistics.json',
            'unified_legal_knowledge_graph.json',
            'vertices_export.csv'
        ]

        for file_name in neo4j_files:
            src = self.base_dir / file_name
            if src.exists() and not self.is_duplicate(src):
                shutil.move(str(src), str(self.neo4j_dir / 'processed_data' / file_name))
                logger.info(f"移动文件: {file_name} -> neo4j/processed_data/")

    def organize_qdrant_data(self) -> Any:
        """整理Qdrant向量库数据"""
        logger.info('整理Qdrant向量库数据...')

        # 创建子目录
        subdirs = [
            'collections', 'embeddings', 'indexes',
            'metadata', 'models'
        ]
        for subdir in subdirs:
            (self.qdrant_dir / subdir).mkdir(exist_ok=True)

        # 移动向量和嵌入相关文件
        qdrant_related = [
            'ai_terminology_vectors_20251205_104422.json',
            'ai_terminology_enhanced_20251205_104422.json',
            'ai_terminology_all_parsed.json',
            'ai_terminology_A_parsed.json',
            'technical_terms_comprehensive.json',
            'technical_terms_raw.json',
            'vectors',
            'vector_indexes',
            'vectorization-stats',
            'qdrant',
            '专利无效向量库'
        ]

        for item in qdrant_related:
            src = self.base_dir / item
            if src.exists():
                if src.is_file():
                    if not self.is_duplicate(src):
                        dest = self.qdrant_dir / 'embeddings' / src.name
                        shutil.move(str(src), str(dest))
                        logger.info(f"移动文件: {item} -> qdrant/embeddings/")
                else:
                    dest = self.qdrant_dir / 'collections' / src.name
                    shutil.move(str(src), str(dest))
                    logger.info(f"移动目录: {item} -> qdrant/collections/")

    def organize_support_data(self) -> Any:
        """整理支撑数据"""
        logger.info('整理支撑数据...')

        # 创建子目录
        subdirs = [
            'databases', 'configs', 'logs', 'reports',
            'templates', 'workspace', 'cache', 'external'
        ]
        for subdir in subdirs:
            (self.support_dir / subdir).mkdir(exist_ok=True)

        # 移动支撑数据
        support_mapping = {
            'databases': ['databases', '.db'],
            'configs': ['configs', 'templates'],
            'logs': ['logs'],
            'reports': ['reports', 'optimization_reports'],
            'workspace': ['workspace', 'processed', 'raw'],
            'cache': ['cache', 'deprecated'],
            'external': ['external', 'agent_evaluations']
        }

        for subdir, patterns in support_mapping.items():
            for pattern in patterns:
                if pattern.startswith('.'):
                    # 文件扩展名模式
                    for file_path in self.base_dir.glob(f"*{pattern}"):
                        if file_path.is_file() and not self.is_duplicate(file_path):
                            shutil.move(str(file_path), str(self.support_dir / subdir / file_path.name))
                            logger.info(f"移动: {file_path.name} -> support/{subdir}/")
                else:
                    # 目录名模式
                    src = self.base_dir / pattern
                    if src.exists() and src.is_dir():
                        dest = self.support_dir / subdir / src.name
                        shutil.move(str(src), str(dest))
                        logger.info(f"移动目录: {pattern} -> support/{subdir}/")

        # 移动特定文件
        special_files = {
            'databases': ['legal_laws_database.db', 'patent_cache.db', 'patent_legal_database.db', 'memory_active.db'],
            'configs': ['knowledge_base.json'],
            'reports': ['ai_terminology_readme.md', 'ai_terminology_all.md']
        }

        for subdir, files in special_files.items():
            for file_name in files:
                src = self.base_dir / file_name
                if src.exists() and not self.is_duplicate(src):
                    shutil.move(str(src), str(self.support_dir / subdir / file_name))
                    logger.info(f"移动: {file_name} -> support/{subdir}/")

    def create_summary(self) -> Any:
        """创建整理总结"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'organization': {
                'neo4j_data': {
                    'path': str(self.neo4j_dir),
                    'description': 'Neo4j知识图谱数据',
                    'subdirectories': [d.name for d in self.neo4j_dir.iterdir() if d.is_dir()]
                },
                'qdrant_data': {
                    'path': str(self.qdrant_dir),
                    'description': 'Qdrant向量库数据',
                    'subdirectories': [d.name for d in self.qdrant_dir.iterdir() if d.is_dir()]
                },
                'support_data': {
                    'path': str(self.support_dir),
                    'description': '支撑数据（数据库、配置、日志等）',
                    'subdirectories': [d.name for d in self.support_dir.iterdir() if d.is_dir()]
                }
            },
            'statistics': {
                'total_files_processed': len(self.file_hash_map),
                'duplicate_files_found': len(self.duplicate_files),
                'duplicate_files': [(str(d[0]), str(d[1])) for d in self.duplicate_files[:10]  # 只显示前10个
            }
        }

        # 保存总结
        summary_path = self.base_dir / 'data_organization_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 打印总结
        logger.info("\n" + '='*60)
        logger.info('数据整理完成！')
        logger.info('='*60)
        logger.info(f"Neo4j知识图谱数据: {self.neo4j_dir}")
        logger.info(f"Qdrant向量库数据: {self.qdrant_dir}")
        logger.info(f"支撑数据: {self.support_dir}")
        logger.info(f"备份目录: {self.backup_dir}")
        logger.info(f"处理文件数: {summary['statistics']['total_files_processed']}")
        logger.info(f"发现重复: {summary['statistics']['duplicate_files_found']} 个")
        logger.info(f"总结报告: {summary_path}")

    def run(self) -> None:
        """执行整理"""
        logger.info('开始按技术栈整理数据目录...')

        # 备份重要配置
        config_files = ['README.md', 'manage_data.py']
        for file_name in config_files:
            src = self.base_dir / file_name
            if src.exists():
                shutil.copy2(str(src), str(self.backup_dir / file_name))

        # 执行整理
        self.organize_neo4j_data()
        self.organize_qdrant_data()
        self.organize_support_data()

        # 创建总结
        self.create_summary()

def main() -> None:
    """主函数"""
    organizer = DataOrganizer()
    organizer.run()

if __name__ == '__main__':
    main()
