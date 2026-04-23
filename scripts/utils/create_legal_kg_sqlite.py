#!/usr/bin/env python3
"""
创建法律知识图谱SQLite数据库
Create Legal Knowledge Graph SQLite Database

将演示版法律知识图谱存储到SQLite数据库
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalKGSQLiteBuilder:
    """法律知识图谱SQLite构建器"""

    def __init__(self):
        self.project_root = Path('/Users/xujian/Athena工作平台')
        self.data_dir = self.project_root / 'data'
        self.db_path = self.data_dir / 'legal_knowledge_graph_demo.db'
        self.kg_json_path = self.data_dir / 'legal_knowledge_graph_demo' / 'legal_knowledge_graph_demo.json'

        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def create_database(self) -> Any:
        """创建数据库和表结构"""
        logger.info('创建SQLite数据库...')

        # 删除现有数据库
        if self.db_path.exists():
            self.db_path.unlink()
            logger.info('删除现有数据库')

        # 创建数据库连接
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 创建实体表
        cursor.execute('''
            CREATE TABLE legal_entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                properties TEXT,
                source TEXT,
                confidence REAL,
                created_time TEXT
            )
        ''')

        # 创建关系表
        cursor.execute('''
            CREATE TABLE legal_relations (
                id TEXT PRIMARY KEY,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                properties TEXT,
                confidence REAL,
                created_time TEXT,
                FOREIGN KEY (source_entity) REFERENCES legal_entities(id),
                FOREIGN KEY (target_entity) REFERENCES legal_entities(id)
            )
        ''')

        # 创建实体类型表
        cursor.execute('''
            CREATE TABLE entity_types (
                type_name TEXT PRIMARY KEY,
                description TEXT,
                entity_count INTEGER DEFAULT 0
            )
        ''')

        # 创建关系类型表
        cursor.execute('''
            CREATE TABLE relation_types (
                type_name TEXT PRIMARY KEY,
                description TEXT,
                relation_count INTEGER DEFAULT 0
            )
        ''')

        # 创建元数据表
        cursor.execute('''
            CREATE TABLE kg_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        conn.commit()
        conn.close()

        logger.info('✅ 数据库结构创建完成')

    def load_kg_data(self) -> Any | None:
        """加载知识图谱JSON数据"""
        if not self.kg_json_path.exists():
            logger.error(f"❌ 知识图谱JSON文件不存在: {self.kg_json_path}")
            return None, None

        with open(self.kg_json_path, encoding='utf-8') as f:
            kg_data = json.load(f)

        entities = kg_data.get('entities', [])
        relations = kg_data.get('relations', [])
        metadata = kg_data.get('metadata', {})

        logger.info(f"📊 加载数据: {len(entities)} 个实体, {len(relations)} 个关系")
        return entities, relations, metadata

    def import_entities(self, entities) -> Any:
        """导入实体数据"""
        logger.info('导入实体数据...')

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        entity_type_count = {}
        current_time = datetime.now().isoformat()

        for entity in entities:
            # 插入实体
            cursor.execute('''
                INSERT OR REPLACE INTO legal_entities
                (id, name, type, properties, source, confidence, created_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                entity['id'],
                entity['name'],
                entity['type'],
                json.dumps(entity['properties'], ensure_ascii=False),
                entity['source'],
                entity['confidence'],
                current_time
            ))

            # 统计实体类型
            entity_type = entity['type']
            entity_type_count[entity_type] = entity_type_count.get(entity_type, 0) + 1

        # 更新实体类型表
        for entity_type, count in entity_type_count.items():
            cursor.execute('''
                INSERT OR REPLACE INTO entity_types (type_name, entity_count)
                VALUES (?, ?)
            ''', (entity_type, count))

        conn.commit()
        conn.close()

        logger.info(f"✅ 导入 {len(entities)} 个实体完成")

    def import_relations(self, relations) -> Any:
        """导入关系数据"""
        logger.info('导入关系数据...')

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        relation_type_count = {}
        current_time = datetime.now().isoformat()

        for relation in relations:
            # 插入关系
            cursor.execute('''
                INSERT OR REPLACE INTO legal_relations
                (id, source_entity, target_entity, relation_type, properties, confidence, created_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                relation['id'],
                relation['source'],
                relation['target'],
                relation['type'],
                json.dumps(relation['properties'], ensure_ascii=False),
                relation['confidence'],
                current_time
            ))

            # 统计关系类型
            relation_type = relation['type']
            relation_type_count[relation_type] = relation_type_count.get(relation_type, 0) + 1

        # 更新关系类型表
        for relation_type, count in relation_type_count.items():
            cursor.execute('''
                INSERT OR REPLACE INTO relation_types (type_name, relation_count)
                VALUES (?, ?)
            ''', (relation_type, count))

        conn.commit()
        conn.close()

        logger.info(f"✅ 导入 {len(relations)} 个关系完成")

    def import_metadata(self, metadata) -> Any:
        """导入元数据"""
        logger.info('导入元数据...')

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 导入元数据
        for key, value in metadata.items():
            cursor.execute('''
                INSERT OR REPLACE INTO kg_metadata (key, value)
                VALUES (?, ?)
            ''', (key, json.dumps(value, ensure_ascii=False)))

        # 添加数据库创建信息
        cursor.execute('''
            INSERT OR REPLACE INTO kg_metadata (key, value)
            VALUES (?, ?)
        ''', ('sqlite_created_time', datetime.now().isoformat()))

        cursor.execute('''
            INSERT OR REPLACE INTO kg_metadata (key, value)
            VALUES (?, ?)
        ''', ('sqlite_version', 'SQLite Legal Knowledge Graph'))

        conn.commit()
        conn.close()

        logger.info('✅ 元数据导入完成')

    def create_indexes(self) -> Any:
        """创建索引优化查询性能"""
        logger.info('创建数据库索引...')

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 创建搜索索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_entities_name ON legal_entities(name)',
            'CREATE INDEX IF NOT EXISTS idx_entities_type ON legal_entities(type)',
            'CREATE INDEX IF NOT EXISTS idx_entities_confidence ON legal_entities(confidence)',
            'CREATE INDEX IF NOT EXISTS idx_relations_source ON legal_relations(source_entity)',
            'CREATE INDEX IF NOT EXISTS idx_relations_target ON legal_relations(target_entity)',
            'CREATE INDEX IF NOT EXISTS idx_relations_type ON legal_relations(relation_type)',
            'CREATE INDEX IF NOT EXISTS idx_relations_confidence ON legal_relations(confidence)'
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        conn.close()

        logger.info('✅ 索引创建完成')

    def verify_import(self) -> bool:
        """验证导入结果"""
        logger.info('验证导入结果...')

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 统计数据
        cursor.execute('SELECT COUNT(*) FROM legal_entities')
        entity_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM legal_relations')
        relation_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM entity_types')
        entity_type_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM relation_types')
        relation_type_count = cursor.fetchone()[0]

        logger.info("📊 数据库统计:")
        logger.info(f"  - 实体总数: {entity_count}")
        logger.info(f"  - 关系总数: {relation_count}")
        logger.info(f"  - 实体类型数: {entity_type_count}")
        logger.info(f"  - 关系类型数: {relation_type_count}")

        # 显示示例数据
        logger.info('📋 示例实体:')
        cursor.execute('SELECT name, type FROM legal_entities LIMIT 5')
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]} ({row[1]})")

        logger.info('🔗 示例关系:')
        cursor.execute("""
            SELECT e1.name as source, lr.relation_type, e2.name as target
            FROM legal_relations lr
            JOIN legal_entities e1 ON lr.source_entity = e1.id
            JOIN legal_entities e2 ON lr.target_entity = e2.id
            LIMIT 5
        """)
        for row in cursor.fetchall():
            logger.info(f"  - {row[0]} --{row[1]}--> {row[2]}")

        conn.close()

    def run(self) -> None:
        """运行完整的数据库构建流程"""
        logger.info('🚀 开始创建法律知识图谱SQLite数据库')
        logger.info('='*60)

        try:
            # 1. 创建数据库结构
            logger.info('1️⃣ 创建数据库结构...')
            self.create_database()

            # 2. 加载数据
            logger.info('2️⃣ 加载知识图谱数据...')
            entities, relations, metadata = self.load_kg_data()
            if entities is None:
                logger.error('❌ 无法加载知识图谱数据')
                return False

            # 3. 导入实体
            logger.info('3️⃣ 导入实体数据...')
            self.import_entities(entities)

            # 4. 导入关系
            logger.info('4️⃣ 导入关系数据...')
            self.import_relations(relations)

            # 5. 导入元数据
            logger.info('5️⃣ 导入元数据...')
            self.import_metadata(metadata)

            # 6. 创建索引
            logger.info('6️⃣ 创建数据库索引...')
            self.create_indexes()

            # 7. 验证导入
            logger.info('7️⃣ 验证导入结果...')
            self.verify_import()

            logger.info('='*60)
            logger.info('🎉 法律知识图谱SQLite数据库创建完成!')
            logger.info(f"📁 数据库文件: {self.db_path}")
            logger.info(f"📊 数据库大小: {self.db_path.stat().st_size / 1024:.1f} KB")

            return True

        except Exception as e:
            logger.error(f"❌ 数据库创建失败: {str(e)}")
            return False

def main() -> None:
    """主函数"""
    logger.info('💾 法律知识图谱SQLite数据库构建器')
    logger.info('将演示版法律知识图谱存储到SQLite数据库')
    logger.info(str('='*60))

    # 创建构建器
    builder = LegalKGSQLiteBuilder()

    # 运行构建流程
    success = builder.run()

    if success:
        logger.info("\n🎯 下一步操作建议:")
        logger.info('1. 使用SQLite客户端查看数据: sqlite3 data/legal_knowledge_graph_demo.db')
        logger.info('2. 执行SQL查询测试数据')
        logger.info('3. 创建API服务访问数据')
        logger.info('4. 集成到Athena知识图谱管理器')
        logger.info("\n✅ SQLite数据库创建成功！")
        logger.info('💡 数据库可以直接用于查询和API开发')
    else:
        logger.info("\n❌ 数据库创建失败，请检查日志获取详细信息")

if __name__ == '__main__':
    main()
