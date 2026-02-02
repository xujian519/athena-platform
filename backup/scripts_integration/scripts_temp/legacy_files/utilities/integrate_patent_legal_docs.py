#!/usr/bin/env python3
"""
整合专利法规文档到知识图谱
"""

import json
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库路径
KNOWLEDGE_GRAPH_DB = 'data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db'
LEGAL_DOCS_PATH = '/Volumes/xujian/开发项目备份/专利相关法律法规'

class PatentLegalDocIntegrator:
    """专利法规文档集成器"""

    def __init__(self):
        self.conn = None
        self.entity_id_counter = 1
        self.relation_id_counter = 1

    def connect_db(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(KNOWLEDGE_GRAPH_DB)
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA synchronous=NORMAL')

            # 获取当前最大的ID
            cursor = self.conn.cursor()
            cursor.execute('SELECT MAX(id) FROM patent_entities')
            max_entity_id = cursor.fetchone()[0] or 0
            self.entity_id_counter = max_entity_id + 1

            cursor.execute('SELECT MAX(id) FROM patent_relations')
            max_relation_id = cursor.fetchone()[0] or 0
            self.relation_id_counter = max_relation_id + 1

            logger.info(f"数据库连接成功，实体ID从{self.entity_id_counter}开始，关系ID从{self.relation_id_counter}开始")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False

    def close_db(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def add_entity(self, name, entity_type, properties=None, description=''):
        """添加实体"""
        try:
            cursor = self.conn.cursor()

            # 检查实体是否已存在
            cursor.execute(
                'SELECT id FROM patent_entities WHERE name = ? AND entity_type = ?',
                (name, entity_type)
            )
            existing = cursor.fetchone()

            if existing:
                return existing[0]

            # 生成实体ID
            generated_entity_id = f"LEGAL_{self.entity_id_counter:08d}"

            # 插入新实体
            cursor.execute(
                """
                INSERT INTO patent_entities
                (entity_id, name, entity_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    generated_entity_id,
                    name,
                    entity_type,
                    json.dumps(properties or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                )
            )

            self.entity_id_counter += 1

            # 更新全文搜索索引
            cursor.execute(
                'INSERT INTO patent_entities_fts (rowid, name, value) VALUES (?, ?, ?)',
                (self.entity_id_counter, name, description)
            )

            return generated_entity_id
        except Exception as e:
            logger.error(f"添加实体失败: {str(e)}")
            return None

    def add_relation(self, from_entity_id, to_entity_id, relation_type, properties=None):
        """添加关系"""
        try:
            cursor = self.conn.cursor()

            # 生成关系ID
            relation_id = f"REL_{self.relation_id_counter:08d}"

            # 插入关系
            cursor.execute(
                """
                INSERT INTO patent_relations
                (relation_id, source_entity_id, target_entity_id, relation_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    relation_id,
                    from_entity_id,
                    to_entity_id,
                    relation_type,
                    json.dumps(properties or {}, ensure_ascii=False),
                    datetime.now().isoformat()
                )
            )

            self.relation_id_counter += 1

            return relation_id
        except Exception as e:
            logger.error(f"添加关系失败: {str(e)}")
            return None

    def parse_markdown_file(self, file_path):
        """解析Markdown文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取标题
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else Path(file_path).stem

            # 提取章节
            sections = []
            section_pattern = r'^#{1,6}\s+(.+)$'
            current_section = None
            current_content = []

            for line in content.split('\n'):
                match = re.match(section_pattern, line)
                if match:
                    if current_section:
                        sections.append({
                            'title': current_section,
                            'content': '\n'.join(current_content)
                        })
                    current_section = match.group(1)
                    current_content = []
                else:
                    current_content.append(line)

            # 添加最后一个章节
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': '\n'.join(current_content)
                })

            return {
                'title': title,
                'sections': sections,
                'content': content
            }
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {str(e)}")
            return None

    def process_legal_document(self, file_path):
        """处理法规文档"""
        logger.info(f"处理文档: {file_path}")

        # 解析文档
        doc_data = self.parse_markdown_file(file_path)
        if not doc_data:
            return

        # 添加文档实体
        doc_entity_id = self.add_entity(
            name=doc_data['title'],
            entity_type='专利法规文档',
            properties={
                'file_path': str(file_path),
                'file_size': os.path.getsize(file_path),
                'sections_count': len(doc_data['sections'])
            },
            description=f"专利法规文档：{doc_data['title']}"
        )

        if not doc_entity_id:
            return

        # 添加章节实体和关系
        for section in doc_data['sections']:
            # 添加章节实体
            section_entity_id = self.add_entity(
                name=section['title'],
                entity_type='法规章节',
                properties={
                    'content_preview': section['content'][:200] + '...' if len(section['content']) > 200 else section['content'],
                    'word_count': len(section['content'])
                },
                description=f"法规章节：{section['title']}"
            )

            if section_entity_id:
                # 添加文档-章节关系
                self.add_relation(
                    from_entity_id=doc_entity_id,
                    to_entity_id=section_entity_id,
                    relation_type='包含章节'
                )

        # 提取法律条款
        self.extract_legal_clauses(doc_data, doc_entity_id)

    def extract_legal_clauses(self, doc_data, doc_entity_id):
        """提取法律条款"""
        content = doc_data['content']

        # 匹配条款编号（如：第1条、第二章、第三款等）
        clause_patterns = [
            r'第([一二三四五六七八九十百千万\d]+)条\s*([^\n]+)',
            r'第([一二三四五六七八九十百千万\d]+)章\s*([^\n]+)',
            r'第([一二三四五六七八九十百千万\d]+)节\s*([^\n]+)',
            r'([一二三四五六七八九十百千万\d]+)、\s*([^\n]+)',
            r'\((\d+)\)\s*([^\n]+)'
        ]

        clauses = []
        for pattern in clause_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                clause_id = match.group(1)
                clause_title = match.group(2).strip()

                # 获取条款内容
                start_pos = match.start()
                end_pos = match.end()

                # 寻找下一个条款或标题
                next_match = re.search(pattern, content[end_pos:])
                if next_match:
                    end_pos = end_pos + next_match.start()

                clause_content = content[start_pos:end_pos].strip()

                clauses.append({
                    'id': clause_id,
                    'title': clause_title,
                    'content': clause_content
                })

        # 添加条款实体
        for clause in clauses:
            clause_entity_id = self.add_entity(
                name=f"第{clause['id']}{clause['title'][:20]}",
                entity_type='法律条款',
                properties={
                    'clause_id': clause['id'],
                    'clause_title': clause['title'],
                    'clause_content': clause['content'][:500],
                    'content_length': len(clause['content'])
                },
                description=f"法律条款：第{clause['id']}条 {clause['title']}"
            )

            if clause_entity_id:
                # 添加文档-条款关系
                self.add_relation(
                    from_entity_id=doc_entity_id,
                    to_entity_id=clause_entity_id,
                    relation_type='包含条款'
                )

    def integrate_all_docs(self):
        """整合所有文档"""
        if not os.path.exists(LEGAL_DOCS_PATH):
            logger.error(f"法规文档路径不存在: {LEGAL_DOCS_PATH}")
            return False

        # 查找所有markdown文件
        md_files = list(Path(LEGAL_DOCS_PATH).glob('*.md'))
        logger.info(f"找到 {len(md_files)} 个markdown文件")

        # 处理每个文件
        processed_count = 0
        for file_path in md_files:
            if file_path.name.startswith('.'):  # 跳过隐藏文件
                continue

            self.process_legal_document(file_path)
            processed_count += 1

            if processed_count % 5 == 0:
                logger.info(f"已处理 {processed_count} 个文件...")
                self.conn.commit()

        # 提交所有更改
        self.conn.commit()

        # 记录导入统计
        self.record_import_stats(processed_count)

        logger.info(f"文档整合完成，共处理 {processed_count} 个文件")
        return True

    def record_import_stats(self, file_count):
        """记录导入统计信息"""
        try:
            cursor = self.conn.cursor()

            # 查看batch_info表结构
            cursor.execute('PRAGMA table_info(batch_info)')
            columns = cursor.fetchall()

            # 更新导入统计
            cursor.execute("""
                INSERT OR REPLACE INTO batch_info
                (batch_id, import_time, file_count, status)
                VALUES
                (?, ?, ?, ?)
            """, (f"LEGAL_DOCS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                  datetime.now().isoformat(),
                  file_count,
                  'success'))

            self.conn.commit()
        except Exception as e:
            logger.error(f"记录导入统计失败: {str(e)}")

def main():
    """主函数"""
    integrator = PatentLegalDocIntegrator()

    # 连接数据库
    if not integrator.connect_db():
        logger.error('无法连接数据库')
        return

    try:
        # 整合所有文档
        success = integrator.integrate_all_docs()

        if success:
            # 输出统计信息
            cursor = integrator.conn.cursor()

            # 统计新增实体
            cursor.execute("""
                SELECT entity_type, COUNT(*)
                FROM patent_entities
                WHERE entity_type IN ('专利法规文档', '法规章节', '法律条款')
                GROUP BY entity_type
            """)
            entity_stats = cursor.fetchall()

            # 统计新增关系
            cursor.execute("""
                SELECT relation_type, COUNT(*)
                FROM patent_relations
                WHERE relation_type IN ('包含章节', '包含条款')
                GROUP BY relation_type
            """)
            relation_stats = cursor.fetchall()

            logger.info("\n=== 导入统计 ===")
            logger.info('新增实体:')
            for entity_type, count in entity_stats:
                logger.info(f"  - {entity_type}: {count}")

            logger.info("\n新增关系:")
            for relation_type, count in relation_stats:
                logger.info(f"  - {relation_type}: {count}")

            logger.info("\n专利法规文档已成功整合到知识图谱中！")

    except Exception as e:
        logger.error(f"整合过程出错: {str(e)}")
    finally:
        integrator.close_db()

if __name__ == '__main__':
    main()