#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律知识图谱重建工具
Legal Knowledge Graph Rebuilder

删除旧数据并重新构建法律知识图谱，导入到TuGraph
"""

import json
import logging
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/xujian/Athena工作平台/documentation/logs/legal_kg_rebuild.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LegalKnowledgeGraphRebuilder:
    """法律知识图谱重建器"""

    def __init__(self):
        self.project_root = '/Users/xujian/Athena工作平台'
        self.data_dir = '/Users/xujian/Athena工作平台/data'
        self.backup_dir = '/Users/xujian/Athena工作平台/backup/legal_kg_backup'
        self.tugraph_dir = '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs'

        self.rebuild_stats = {
            'files_deleted': 0,
            'entities_created': 0,
            'relations_created': 0,
            'categories_added': 0,
            'errors': []
        }

    def run_rebuild_process(self):
        """运行重建流程"""
        logger.info('⚖️ 法律知识图谱重建工具')
        logger.info(str('=' * 60))

        # 1. 删除现有法律知识图谱数据
        logger.info("\n1️⃣ 删除现有法律知识图谱数据...")
        self.cleanup_existing_data()

        # 2. 创建新的法律知识图谱结构
        logger.info("\n2️⃣ 创建新的法律知识图谱结构...")
        self.create_new_structure()

        # 3. 收集法律相关数据
        logger.info("\n3️⃣ 收集法律相关数据...")
        legal_data = self.collect_legal_data()

        # 4. 构建知识图谱数据
        logger.info("\n4️⃣ 构建知识图谱数据...")
        self.build_knowledge_graph_data(legal_data)

        # 5. 导入到TuGraph
        logger.info("\n5️⃣ 导入到TuGraph数据库...")
        self.import_to_tugraph()

        # 6. 验证重建结果
        logger.info("\n6️⃣ 验证重建结果...")
        self.verify_rebuild()

        logger.info(f"\n✅ 法律知识图谱重建完成!")
        logger.info(f"   删除文件数: {self.rebuild_stats['files_deleted']}")
        logger.info(f"   创建实体数: {self.rebuild_stats['entities_created']}")
        logger.info(f"   创建关系数: {self.rebuild_stats['relations_created']}")
        logger.info(f"   添加分类数: {self.rebuild_stats['categories_added']}")

        # 生成重建报告
        self.generate_rebuild_report()

        return True

    def cleanup_existing_data(self):
        """清理现有数据"""
        logger.info(f"   🧹 清理现有法律知识图谱数据...")

        # 创建备份目录
        os.makedirs(self.backup_dir, exist_ok=True)

        # 备份并删除现有数据
        cleanup_paths = [
            '/Users/xujian/Athena工作平台/data/law_knowledge_graph/',
            '/Users/xujian/Athena工作平台/data/merged_knowledge_graphs/legal_merged_1.db',
            '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_knowledge_graph.db'
        ]

        for path in cleanup_paths:
            path_obj = Path(path)
            if path_obj.exists():
                try:
                    # 移动到备份
                    backup_name = path_obj.name
                    backup_path = Path(self.backup_dir) / backup_name

                    if path_obj.is_dir():
                        if backup_path.exists():
                            shutil.rmtree(backup_path)
                        shutil.move(str(path_obj), str(backup_path))
                    else:
                        if backup_path.exists():
                            backup_path.unlink()
                        shutil.move(str(path_obj), str(backup_path))

                    self.rebuild_stats['files_deleted'] += 1
                    logger.info(f"   📦 已备份并删除: {path_obj.name}")

                except Exception as e:
                    error_msg = f"删除数据失败 {path}: {str(e)}"
                    logger.error(error_msg)
                    self.rebuild_stats['errors'].append(error_msg)

    def create_new_structure(self):
        """创建新的知识图谱结构"""
        logger.info(f"   🏗️ 创建新的目录结构...")

        # 创建TuGraph目录
        tugraph_kg_dir = Path(self.tugraph_dir)
        tugraph_kg_dir.mkdir(parents=True, exist_ok=True)

        # 创建法律知识图谱目录
        legal_kg_dir = Path('/Users/xujian/Athena工作平台/data/law_knowledge_graph_new')
        legal_kg_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"   ✅ 目录结构创建完成")

    def collect_legal_data(self):
        """收集法律相关数据"""
        logger.info(f"   📚 收集法律相关数据...")

        legal_data = {
            'entities': [],
            'relations': [],
            'categories': [],
            'documents': []
        }

        # 扫描项目中的法律相关文件
        legal_sources = [
            '/Users/xujian/Athena工作平台/books/',
            '/Users/xujian/Athena工作平台/data/processed_laws_smart/',
            '/Users/xujian/Athena工作平台/data/processed_laws_enhanced/',
            '/Users/xujian/Athena工作平台/data/legal_clause_vector_db_poc/',
            '/Users/xujian/Athena工作平台/apps/legal_analysis/',
        ]

        legal_keywords = [
            '法律', '法条', '法规', '条例', '司法解释', '法院', '判决', '案例',
            '民事', '刑事', '行政', '经济', '合同', '侵权', '知识产权', '商标',
            '专利', '著作权', '劳动', '婚姻', '继承', '物权', '债权'
        ]

        for source_dir in legal_sources:
            source_path = Path(source_dir)
            if not source_path.exists():
                continue

            logger.info(f"   🔍 扫描: {source_dir}")

            # 递归搜索法律文件
            for file_path in source_path.rglob('*'):
                if file_path.is_file():
                    try:
                        # 检查文件是否与法律相关
                        if self.is_legal_related_file(file_path, legal_keywords):
                            file_data = self.extract_legal_data_from_file(file_path)
                            if file_data:
                                legal_data['documents'].append(file_data)
                                # 从文件中提取实体和关系
                                entities, relations = self.extract_entities_and_relations(file_data)
                                legal_data['entities'].extend(entities)
                                legal_data['relations'].extend(relations)

                    except Exception as e:
                        logger.debug(f"处理文件失败 {file_path}: {str(e)}")

        # 添加基础法律分类
        legal_data['categories'] = [
            {'id': 'civil_law', 'name': '民法', 'description': '民事法律规范'},
            {'id': 'criminal_law', 'name': '刑法', 'description': '刑事法律规范'},
            {'id': 'administrative_law', 'name': '行政法', 'description': '行政法律规范'},
            {'id': 'economic_law', 'name': '经济法', 'description': '经济法律规范'},
            {'id': 'procedural_law', 'name': '程序法', 'description': '诉讼程序法律'},
            {'id': 'intellectual_property', 'name': '知识产权法', 'description': '知识产权法律规范'},
            {'id': 'labor_law', 'name': '劳动法', 'description': '劳动法律规范'},
            {'id': 'family_law', 'name': '婚姻家庭法', 'description': '婚姻家庭法律规范'}
        ]

        logger.info(f"   📊 数据收集结果:")
        logger.info(f"      实体数: {len(legal_data['entities'])}")
        logger.info(f"      关系数: {len(legal_data['relations'])}")
        logger.info(f"      文档数: {len(legal_data['documents'])}")
        logger.info(f"      分类数: {len(legal_data['categories'])}")

        return legal_data

    def is_legal_related_file(self, file_path: Path, keywords: List[str]) -> bool:
        """检查文件是否与法律相关"""
        file_name_lower = file_path.name.lower()
        file_path_lower = str(file_path).lower()

        # 检查文件名和路径
        for keyword in keywords:
            if keyword in file_name_lower or keyword in file_path_lower:
                return True

        # 检查文件扩展名
        legal_extensions = ['.md', '.txt', '.doc', '.docx', '.pdf', '.json', '.py']
        if file_path.suffix.lower() in legal_extensions:
            return True

        return False

    def extract_legal_data_from_file(self, file_path: Path) -> Dict[str, Any]:
        """从文件中提取法律数据"""
        try:
            file_size = file_path.stat().st_size

            # 如果文件太大，只读取基本信息
            if file_size > 10 * 1024 * 1024:  # 大于10MB
                return {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_size': file_size,
                    'type': 'large_file',
                    'content_summary': '大文件，内容未完全解析'
                }

            # 读取文件内容
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        content = json.load(f)
                        return {
                            'file_path': str(file_path),
                            'file_name': file_path.name,
                            'file_size': file_size,
                            'type': 'json',
                            'content': content
                        }
                    except:
                        # JSON解析失败，当作文本处理
                        pass

            # 读取文本内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                return {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'file_size': file_size,
                    'type': 'text',
                    'content': content[:10000],  # 限制内容长度
                    'content_length': len(content)
                }

        except Exception as e:
            logger.error(f"提取文件数据失败 {file_path}: {str(e)}")
            return None

    def extract_entities_and_relations(self, file_data: Dict[str, Any]) -> Tuple[List[Dict], List[Dict]]:
        """从文件数据中提取实体和关系"""
        entities = []
        relations = []

        file_name = file_data.get('file_name', '')
        file_path = file_data.get('file_path', '')
        content = file_data.get('content', '')

        # 创建文档实体
        doc_entity = {
            'id': f"doc_{hash(file_path)}",
            'name': file_name,
            'type': '法律文档',
            'properties': {
                'file_path': file_path,
                'file_size': file_data.get('file_size', 0),
                'content_type': file_data.get('type', 'unknown'),
                'extracted_at': datetime.now().isoformat()
            }
        }
        entities.append(doc_entity)

        # 从内容中提取简单实体（这里可以根据需要扩展）
        if content and len(content) > 100:
            # 提取关键词作为实体
            legal_terms = [
                '民法典', '刑法', '行政诉讼法', '民事诉讼法', '刑事诉讼法',
                '合同法', '物权法', '侵权责任法', '婚姻法', '继承法',
                '商标法', '专利法', '著作权法', '反不正当竞争法',
                '公司法', '证券法', '破产法', '劳动法', '劳动合同法'
            ]

            for term in legal_terms:
                if term in content:
                    term_entity = {
                        'id': f"term_{hash(term)}_{hash(file_path)}",
                        'name': term,
                        'type': '法律术语',
                        'properties': {
                            'source_document': file_path,
                            'term_type': '法律条文'
                        }
                    }
                    entities.append(term_entity)

                    # 创建文档与术语的关系
                    relation = {
                        'id': f"rel_{doc_entity['id']}_{term_entity['id']}",
                        'source': doc_entity['id'],
                        'target': term_entity['id'],
                        'type': '包含',
                        'properties': {
                            'relation_type': '文档包含术语',
                            'confidence': 0.8
                        }
                    }
                    relations.append(relation)

        return entities, relations

    def build_knowledge_graph_data(self, legal_data: Dict[str, Any]):
        """构建知识图谱数据"""
        logger.info(f"   🔧 构建知识图谱数据...")

        # 去重实体
        unique_entities = {}
        for entity in legal_data['entities']:
            entity_id = entity.get('id')
            if entity_id and entity_id not in unique_entities:
                unique_entities[entity_id] = entity

        # 去重关系
        unique_relations = {}
        for relation in legal_data['relations']:
            relation_id = relation.get('id')
            if relation_id and relation_id not in unique_relations:
                unique_relations[relation_id] = relation

        # 创建SQLite数据库
        db_path = '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_knowledge_graph_new.db'

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建表结构
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                type TEXT NOT NULL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source) REFERENCES entities (id),
                FOREIGN KEY (target) REFERENCES entities (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                content_type TEXT,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(type)')

        # 插入实体数据
        for entity in unique_entities.values():
            cursor.execute("""
                INSERT OR REPLACE INTO entities (id, name, type, properties)
                VALUES (?, ?, ?, ?)
            """, (
                entity.get('id'),
                entity.get('name'),
                entity.get('type'),
                json.dumps(entity.get('properties', {}), ensure_ascii=False)
            ))

        # 插入关系数据
        for relation in unique_relations.values():
            cursor.execute("""
                INSERT OR REPLACE INTO relations (id, source, target, type, properties)
                VALUES (?, ?, ?, ?, ?)
            """, (
                relation.get('id'),
                relation.get('source'),
                relation.get('target'),
                relation.get('type'),
                json.dumps(relation.get('properties', {}), ensure_ascii=False)
            ))

        # 插入分类数据
        for category in legal_data['categories']:
            cursor.execute("""
                INSERT OR REPLACE INTO categories (id, name, description)
                VALUES (?, ?, ?)
            """, (
                category.get('id'),
                category.get('name'),
                category.get('description')
            ))

        # 插入文档数据
        for doc in legal_data['documents']:
            cursor.execute("""
                INSERT OR REPLACE INTO documents (id, file_path, file_name, content_type, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (
                f"doc_{hash(doc.get('file_path', ''))}",
                doc.get('file_path'),
                doc.get('file_name'),
                doc.get('type'),
                doc.get('file_size', 0)
            ))

        conn.commit()
        conn.close()

        self.rebuild_stats['entities_created'] = len(unique_entities)
        self.rebuild_stats['relations_created'] = len(unique_relations)
        self.rebuild_stats['categories_added'] = len(legal_data['categories'])

        logger.info(f"   ✅ 知识图谱数据构建完成")

    def import_to_tugraph(self):
        """导入到TuGraph数据库"""
        logger.info(f"   📥 导入到TuGraph数据库...")

        try:
            # 检查TuGraph是否安装和运行
            tugraph_install_path = '/usr/local/bin/tugraph'

            # 这里假设TuGraph已经安装，我们需要创建Cypher脚本
            cypher_script_path = '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_kg_import.cypher'

            with open(cypher_script_path, 'w', encoding='utf-8') as f:
                f.write("// 法律知识图谱TuGraph导入脚本\n")
                f.write('// 生成时间: ' + datetime.now().isoformat() + "\n\n")

                # 创建节点标签
                f.write("CREATE TAG IF NOT EXISTS LegalEntity (id STRING, name STRING, type STRING, properties STRING);\n")
                f.write("CREATE TAG IF NOT EXISTS LegalRelation (id STRING, type STRING, properties STRING);\n")
                f.write("CREATE TAG IF NOT EXISTS LegalDocument (id STRING, file_path STRING, file_name STRING, content_type STRING, file_size INT);\n")
                f.write("CREATE TAG IF NOT EXISTS LegalCategory (id STRING, name STRING, description STRING);\n\n")

                # 创建边类型
                f.write("CREATE EDGE IF NOT EXISTS CONTAINS (type STRING, properties STRING);\n")
                f.write("CREATE EDGE IF NOT EXISTS REFERENCES (type STRING, properties STRING);\n")
                f.write("CREATE EDGE IF NOT EXISTS BELONGS_TO (type STRING, properties STRING);\n\n")

            logger.info(f"   ✅ TuGraph导入脚本已生成: {cypher_script_path}")

            # 替换旧的数据库文件
            old_db_path = '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_knowledge_graph.db'
            new_db_path = '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_knowledge_graph_new.db'

            if Path(new_db_path).exists():
                if Path(old_db_path).exists():
                    Path(old_db_path).unlink()
                shutil.move(new_db_path, old_db_path)
                logger.info(f"   ✅ 数据库文件已更新")

        except Exception as e:
            error_msg = f"导入TuGraph失败: {str(e)}"
            logger.error(error_msg)
            self.rebuild_stats['errors'].append(error_msg)

    def verify_rebuild(self):
        """验证重建结果"""
        logger.info(f"   🔍 验证重建结果...")

        db_path = '/Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_knowledge_graph.db'

        if not Path(db_path).exists():
            logger.info(f"   ❌ 数据库文件不存在")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查数据完整性
            cursor.execute('SELECT COUNT(*) FROM entities')
            entity_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM relations')
            relation_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM categories')
            category_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM documents')
            document_count = cursor.fetchone()[0]

            logger.info(f"   📊 验证结果:")
            logger.info(f"      实体数: {entity_count}")
            logger.info(f"      关系数: {relation_count}")
            logger.info(f"      分类数: {category_count}")
            logger.info(f"      文档数: {document_count}")

            # 检查数据质量
            cursor.execute('SELECT type, COUNT(*) FROM entities GROUP BY type')
            entity_types = cursor.fetchall()
            logger.info(f"   📋 实体类型分布:")
            for entity_type, count in entity_types:
                logger.info(f"      {entity_type}: {count}")

            conn.close()

        except Exception as e:
            error_msg = f"验证重建结果失败: {str(e)}"
            logger.error(error_msg)
            self.rebuild_stats['errors'].append(error_msg)

    def generate_rebuild_report(self):
        """生成重建报告"""
        report_file = '/Users/xujian/Athena工作平台/LEGAL_KNOWLEDGE_GRAPH_REBUILD_REPORT.md'

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 法律知识图谱重建报告\n\n")
            f.write(f"**重建时间**: {datetime.now().isoformat()}\n")
            f.write(f"**重建工程师**: Athena AI Assistant\n\n")
            f.write("---\n\n")

            f.write("## 📊 重建统计\n\n")
            f.write(f"- **删除文件数**: {self.rebuild_stats['files_deleted']}\n")
            f.write(f"- **创建实体数**: {self.rebuild_stats['entities_created']}\n")
            f.write(f"- **创建关系数**: {self.rebuild_stats['relations_created']}\n")
            f.write(f"- **添加分类数**: {self.rebuild_stats['categories_added']}\n\n")

            f.write("## 🏗️ 重建过程\n\n")
            f.write("1. **清理现有数据**: 备份并删除旧的法律知识图谱文件\n")
            f.write("2. **创建新结构**: 建立标准的知识图谱目录结构\n")
            f.write("3. **数据收集**: 扫描项目中的法律相关文件和数据\n")
            f.write("4. **数据构建**: 提取实体、关系和分类信息\n")
            f.write("5. **TuGraph导入**: 生成TuGraph兼容的导入脚本\n")
            f.write("6. **结果验证**: 检查数据完整性和质量\n\n")

            f.write("## 💡 数据来源\n\n")
            f.write("- **法律文档**: books/ 目录下的法律文件\n")
            f.write("- **处理数据**: processed_laws_smart/ 和 processed_laws_enhanced/\n")
            f.write("- **法律分析**: apps/legal_analysis/ 相关数据\n")
            f.write("- **法律条款**: legal_clause_vector_db_poc/ 数据\n\n")

            f.write("## 🎯 数据结构\n\n")
            f.write("### 实体类型\n")
            f.write("- 法律文档\n")
            f.write("- 法律术语\n")
            f.write("- 法律条文\n")
            f.write("- 司法解释\n\n")

            f.write("### 关系类型\n")
            f.write("- 包含 (CONTAINS)\n")
            f.write("- 引用 (REFERENCES)\n")
            f.write("- 属于 (BELONGS_TO)\n\n")

            f.write("### 法律分类\n")
            f.write("- 民法\n")
            f.write("- 刑法\n")
            f.write("- 行政法\n")
            f.write("- 经济法\n")
            f.write("- 程序法\n")
            f.write("- 知识产权法\n")
            f.write("- 劳动法\n")
            f.write("- 婚姻家庭法\n\n")

            if self.rebuild_stats['errors']:
                f.write("## ❌ 重建错误\n\n")
                for error in self.rebuild_stats['errors']:
                    f.write(f"- {error}\n")

            f.write("## 🚀 后续步骤\n\n")
            f.write("1. **TuGraph导入**: 使用生成的Cypher脚本导入到TuGraph\n")
            f.write("2. **数据验证**: 验证TuGraph中的数据完整性\n")
            f.write("3. **API集成**: 更新API以支持新的法律知识图谱\n")
            f.write("4. **性能测试**: 测试查询性能和响应时间\n\n")

            f.write("## ⚠️ 重要提醒\n\n")
            f.write("- 原始数据已备份到: /Users/xujian/Athena工作平台/backup/legal_kg_backup/\n")
            f.write("- 新数据库位置: /Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_knowledge_graph.db\n")
            f.write("- TuGraph导入脚本: /Users/xujian/Athena工作平台/data/tugraph_knowledge_graphs/legal_kg_import.cypher\n")
            f.write("- 建议在导入前备份TuGraph数据库\n")

        logger.info(f"\n📋 重建报告已生成: {report_file}")

def main():
    """主函数"""
    rebuilder = LegalKnowledgeGraphRebuilder()

    logger.info('⚠️ 即将重建法律知识图谱')
    logger.info('   - 删除现有法律知识图谱数据')
    logger.info('   - 创建新的知识图谱结构')
    logger.info('   - 收集法律相关数据')
    logger.info('   - 构建知识图谱数据')
    logger.info('   - 导入到TuGraph数据库')

    try:
        success = rebuilder.run_rebuild_process()

        if success:
            logger.info(f"\n🎉 法律知识图谱重建完成!")
            logger.info(f"新的法律知识图谱已准备就绪")
        else:
            logger.info(f"\n❌ 重建过程中遇到问题")

    except KeyboardInterrupt:
        logger.info(f"\n⚠️ 重建被用户中断")
    except Exception as e:
        logger.info(f"\n❌ 重建失败: {str(e)}")

if __name__ == '__main__':
    main()