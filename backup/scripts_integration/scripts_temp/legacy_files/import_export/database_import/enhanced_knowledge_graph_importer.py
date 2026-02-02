#!/usr/bin/env python3
"""
Athena知识图谱增强导入工具
支持从SQLite迁移到Neo4j，以及增量更新和性能优化
"""

import hashlib
import json
import logging
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

class EnhancedKnowledgeGraphImporter:
    def __init__(self, neo4j_uri: str = 'bolt://localhost:7687',
                 username: str = 'neo4j', password: str = 'password'):
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password
        self.data_dir = Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j')
        self.sqlite_db_path = '/tmp/knowledge_graph.db'

        # 性能优化：批量处理大小
        self.batch_size = 1000
        self.query_timeout = 300  # 5分钟超时

        # 增量更新支持
        self.import_log_file = '/tmp/knowledge_graph_import_log.json'
        self.import_history = self.load_import_history()

    def load_import_history(self) -> Dict:
        """加载导入历史记录"""
        if os.path.exists(self.import_log_file):
            try:
                with open(self.import_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.info(f"⚠️ 无法加载导入历史: {e}")

        return {
            'last_import': None,
            'imported_files': {},
            'file_hashes': {},
            'total_entities': 0,
            'total_relations': 0
        }

    def save_import_history(self):
        """保存导入历史记录"""
        try:
            with open(self.import_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.import_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.info(f"⚠️ 无法保存导入历史: {e}")

    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值用于检测变更"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.info(f"⚠️ 计算文件哈希失败 {file_path}: {e}")
            return ''

    def file_has_changed(self, file_path: Path) -> bool:
        """检查文件是否已更改"""
        current_hash = self.calculate_file_hash(file_path)
        file_key = str(file_path)

        if file_key not in self.import_history['file_hashes']:
            return True

        return self.import_history['file_hashes'][file_key] != current_hash

    def execute_cypher_command(self, cypher: str, description: str = '') -> bool:
        """执行Cypher命令，增强错误处理和重试机制"""
        max_retries = 3

        for attempt in range(max_retries):
            try:
                # 使用管道方式传递命令
                process = subprocess.Popen(
                    ['cypher-shell', '-u', self.username, '-p', self.password, '--non-interactive'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(input=cypher, timeout=self.query_timeout)

                if process.returncode == 0:
                    if description:
                        logger.info(f"✅ {description}")
                    return True
                else:
                    if attempt < max_retries - 1:
                        logger.info(f"⚠️ 尝试 {attempt + 1} 失败，重试中... {stderr.strip()}")
                        time.sleep(2 ** attempt)  # 指数退避
                    else:
                        logger.info(f"❌ {description} 失败: {stderr.strip()}")
                        return False

            except subprocess.TimeoutExpired:
                process.kill()
                if attempt < max_retries - 1:
                    logger.info(f"⚠️ 查询超时，重试中... (尝试 {attempt + 1})")
                    time.sleep(5)
                else:
                    logger.info(f"❌ {description} 超时")
                    return False

            except Exception as e:
                logger.info(f"❌ {description} 异常: {e}")
                return False

        return False

    def setup_neo4j_performance_optimizations(self):
        """设置Neo4j性能优化"""
        logger.info('🚀 设置Neo4j性能优化...')

        optimizations = [
            # 增加内存配置
            "CALL dbms.setConfigValue('db.memory.heap.initial_size', '512m')",
            "CALL dbms.setConfigValue('db.memory.heap.max_size', '2G')",

            # 优化事务配置
            "CALL dbms.setConfigValue('db.transaction.timeout', '60s')",
            "CALL dbms.setConfigValue('db.transaction.bookmark_ready_timeout', '30s')",

            # 优化日志配置
            "CALL dbms.setConfigValue('db.logs.query.enabled', 'false')",
            "CALL dbms.setConfigValue('db.logs.query.threshold', '1s')",
        ]

        for opt in optimizations:
            self.execute_cypher_command(opt, f"应用优化: {opt}")

    def create_constraints_and_indexes(self):
        """创建约束和索引以优化性能"""
        logger.info('🔍 创建数据库约束和索引...')

        # 创建唯一性约束
        constraints = [
            'CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE',
            'CREATE CONSTRAINT legal_entity_unique IF NOT EXISTS FOR (e:LegalEntity) REQUIRE e.name IS UNIQUE',
            'CREATE CONSTRAINT patent_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.id IS UNIQUE',
        ]

        for constraint in constraints:
            self.execute_cypher_command(constraint, f"创建约束: {constraint}")

        # 创建性能索引
        indexes = [
            'CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)',
            'CREATE INDEX entity_source_index IF NOT EXISTS FOR (e:Entity) ON (e.source)',
            'CREATE INDEX entity_confidence_index IF NOT EXISTS FOR (e:Entity) ON (e.confidence)',
            'CREATE INDEX relation_type_index IF NOT EXISTS FOR ()-[r:RELATED_TO]->() ON (r.relation_type)',
            'CREATE INDEX relation_weight_index IF NOT EXISTS FOR ()-[r:RELATED_TO]->() ON (r.weight)',
            'CREATE FULLTEXT INDEX entity_fulltext_index IF NOT EXISTS FOR (e:Entity) ON EACH [e.name, e.description]',
        ]

        for index in indexes:
            self.execute_cypher_command(index, f"创建索引: {index}")

    def migrate_from_sqlite(self) -> bool:
        """从SQLite迁移数据到Neo4j"""
        if not os.path.exists(self.sqlite_db_path):
            logger.info(f"❌ SQLite数据库不存在: {self.sqlite_db_path}")
            return False

        logger.info('🔄 开始从SQLite迁移到Neo4j...')

        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()

            # 获取实体总数
            cursor.execute('SELECT COUNT(*) FROM entities')
            total_entities = cursor.fetchone()[0]
            logger.info(f"📊 发现 {total_entities} 个实体待迁移")

            # 分批迁移实体
            offset = 0
            migrated_entities = 0

            while offset < total_entities:
                cursor.execute('SELECT * FROM entities LIMIT ? OFFSET ?',
                             (self.batch_size, offset))
                rows = cursor.fetchall()

                if not rows:
                    break

                # 构建批量插入Cypher
                cypher_commands = []
                for row in rows:
                    id_, name, entity_type, confidence, source, properties, created_at = row

                    # 清理和转义数据
                    name = name.replace("'", "\\'") if name else ''
                    source = source.replace("'", "\\'") if source else ''

                    cypher = f"""
                    MERGE (e:Entity {{name: '{name}'}})
                    SET e.entity_type = '{entity_type or 'Unknown'}',
                        e.confidence = {confidence or 0.8},
                        e.source = '{source}',
                        e.sqlite_id = {id_},
                        e.created_at = '{created_at}'
                    """
                    cypher_commands.append(cypher)

                # 执行批量插入
                batch_cypher = "\n".join(cypher_commands)
                if self.execute_cypher_command(batch_cypher, f"迁移实体批次 {offset//self.batch_size + 1}"):
                    migrated_entities += len(rows)
                    logger.info(f"✅ 已迁移实体: {migrated_entities}/{total_entities}")

                offset += self.batch_size

            # 迁移关系
            cursor.execute('SELECT COUNT(*) FROM relations')
            total_relations = cursor.fetchone()[0]
            logger.info(f"📊 发现 {total_relations} 个关系待迁移")

            offset = 0
            migrated_relations = 0

            while offset < total_relations:
                cursor.execute("""
                    SELECT r.source_id, r.target_id, r.relation_type, r.properties
                    FROM relations r
                    LIMIT ? OFFSET ?
                """, (self.batch_size, offset))

                rows = cursor.fetchall()
                if not rows:
                    break

                # 构建批量关系插入
                cypher_commands = []
                for row in rows:
                    source_id, target_id, relation_type, properties = row

                    cypher = f"""
                    MATCH (source:Entity {{sqlite_id: {source_id}}})
                    MATCH (target:Entity {{sqlite_id: {target_id}}})
                    MERGE (source)-[r:RELATED_TO {{relation_type: '{relation_type or 'RELATED_TO'}'}}]->(target)
                    """
                    cypher_commands.append(cypher)

                batch_cypher = "\n".join(cypher_commands)
                if self.execute_cypher_command(batch_cypher, f"迁移关系批次 {offset//self.batch_size + 1}"):
                    migrated_relations += len(rows)
                    logger.info(f"✅ 已迁移关系: {migrated_relations}/{total_relations}")

                offset += self.batch_size

            conn.close()

            logger.info(f"🎉 SQLite到Neo4j迁移完成！")
            logger.info(f"   实体: {migrated_entities}/{total_entities}")
            logger.info(f"   关系: {migrated_relations}/{total_relations}")

            return True

        except Exception as e:
            logger.info(f"❌ SQLite迁移失败: {e}")
            return False

    def import_json_file_incremental(self, json_path: Path, graph_name: str) -> bool:
        """增量导入JSON文件"""
        if not json_path.exists():
            logger.info(f"⚠️ 文件不存在: {json_path}")
            return False

        # 检查文件是否有变更
        if not self.file_has_changed(json_path):
            logger.info(f"⏭️ 文件未变更，跳过: {json_path.name}")
            return True

        logger.info(f"📥 导入JSON文件: {json_path.name}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            entities = data.get('entities', [])
            relations = data.get('relations', [])

            logger.info(f"   包含 {len(entities)} 个实体, {len(relations)} 个关系")

            # 清理现有数据（仅此图）
            cleanup_cypher = f"""
            MATCH (n:{graph_name}) DETACH DELETE n
            """
            self.execute_cypher_command(cleanup_cypher, f"清理现有图数据: {graph_name}")

            # 分批导入实体
            for i in range(0, len(entities), self.batch_size):
                batch = entities[i:i + self.batch_size]
                self.import_entity_batch(batch, graph_name, i // self.batch_size + 1)

            # 分批导入关系
            for i in range(0, len(relations), self.batch_size):
                batch = relations[i:i + self.batch_size]
                self.import_relation_batch(batch, graph_name, i // self.batch_size + 1)

            # 更新导入历史
            file_key = str(json_path)
            self.import_history['imported_files'][file_key] = {
                'graph_name': graph_name,
                'entity_count': len(entities),
                'relation_count': len(relations),
                'last_import': datetime.now().isoformat()
            }
            self.import_history['file_hashes'][file_key] = self.calculate_file_hash(json_path)

            return True

        except Exception as e:
            logger.info(f"❌ JSON导入失败 {json_path}: {e}")
            return False

    def import_entity_batch(self, entities: List[Dict], graph_name: str, batch_num: int):
        """批量导入实体"""
        cypher_commands = []

        for entity in entities:
            name = entity.get('name', '').replace("'", "\\'")
            entity_type = entity.get('entity_type', 'Unknown')
            confidence = entity.get('confidence', 0.8)
            source = entity.get('source', '')

            # 转换属性为字符串
            properties_str = json.dumps(entity, ensure_ascii=False).replace("'", "\\'")

            cypher = f"""
            MERGE (n:{graph_name} {{name: '{name}'}})
            SET n.entity_type = '{entity_type}',
                n.confidence = {confidence},
                n.source = '{source}',
                n.properties = '{properties_str}',
                n.imported_at = '{datetime.now().isoformat()}'
            """
            cypher_commands.append(cypher)

        batch_cypher = "\n".join(cypher_commands)
        self.execute_cypher_command(batch_cypher, f"导入实体批次 {batch_num} ({len(entities)} 个)")

    def import_relation_batch(self, relations: List[Dict], graph_name: str, batch_num: int):
        """批量导入关系"""
        cypher_commands = []

        for relation in relations:
            source = relation.get('source', '').replace("'", "\\'")
            target = relation.get('target', '').replace("'", "\\'")
            relation_type = relation.get('relation_type', 'RELATED_TO').replace(' ', '_')

            # 转换属性为字符串
            properties_str = json.dumps(relation, ensure_ascii=False).replace("'", "\\'")

            cypher = f"""
            MATCH (a:{graph_name} {{name: '{source}'}})
            MATCH (b:{graph_name} {{name: '{target}'}})
            MERGE (a)-[r:{relation_type}]->(b)
            SET r.properties = '{properties_str}',
                r.imported_at = '{datetime.now().isoformat()}'
            """
            cypher_commands.append(cypher)

        batch_cypher = "\n".join(cypher_commands)
        self.execute_cypher_command(batch_cypher, f"导入关系批次 {batch_num} ({len(relations)} 个)")

    def run_full_enhanced_import(self) -> bool:
        """执行完整的增强导入流程"""
        logger.info(str('=' * 80))
        logger.info('🚀 Athena知识图谱增强导入工具')
        logger.info(str('=' * 80))

        start_time = time.time()

        # 1. 设置性能优化
        self.setup_neo4j_performance_optimizations()

        # 2. 创建约束和索引
        self.create_constraints_and_indexes()

        # 3. 从SQLite迁移（如果存在）
        if os.path.exists(self.sqlite_db_path):
            if not self.migrate_from_sqlite():
                logger.info('⚠️ SQLite迁移失败，继续其他导入')

        success_count = 0
        total_count = 0

        # 4. 导入核心JSON知识图谱文件
        json_files = [
            ('unified_legal_knowledge_graph.json', 'LegalKnowledge'),
            ('production_legal_knowledge_graph.json', 'ProductionLegal'),
        ]

        for filename, graph_name in json_files:
            file_path = self.data_dir / 'raw_data' / 'production_legal_knowledge_graph' / filename
            if file_path.exists():
                total_count += 1
                if self.import_json_file_incremental(file_path, graph_name):
                    success_count += 1

        # 5. 扫描并导入其他JSON文件
        json_pattern_files = [
            ('patent_judgment_kg', 'enhanced_patent_judgment_entities'),
            ('patent_kg', 'patent_kg'),
            ('technical_terms_knowledge_graph', 'technical_knowledge_graph')
        ]

        for dir_name, entity_pattern in json_pattern_files:
            json_dir = self.data_dir / 'raw_data' / dir_name
            if json_dir.exists():
                json_files = list(json_dir.glob(f"{entity_pattern}*.json"))
                for json_file in json_files:
                    total_count += 1
                    graph_name = dir_name.replace('_kg', '')
                    if self.import_json_file_incremental(json_file, graph_name):
                        success_count += 1

        # 6. 保存导入历史
        self.import_history['last_import'] = datetime.now().isoformat()
        self.save_import_history()

        end_time = time.time()

        # 7. 显示导入结果统计
        self.show_import_statistics(success_count, total_count, start_time, end_time)

        return success_count == total_count

    def show_import_statistics(self, success_count: int, total_count: int, start_time: float, end_time: float):
        """显示导入统计信息"""
        logger.info(str("\n" + '=' * 80))
        logger.info('📊 导入完成统计')
        logger.info(str('=' * 80))

        logger.info(f"✅ 成功导入: {success_count}/{total_count} 个文件")
        logger.info(f"⏱️ 总耗时: {end_time - start_time:.2f}秒")

        # 查询Neo4j统计信息
        stats_commands = [
            ('MATCH (n) RETURN count(n) as total_nodes', '总节点数'),
            ('MATCH ()-[r]->() RETURN count(r) as total_relations', '总关系数'),
            ('CALL db.indexes() YIELD name RETURN count(name) as total_indexes', '总索引数'),
        ]

        logger.info("\n📈 Neo4j数据库统计:")
        for command, description in stats_commands:
            try:
                process = subprocess.Popen(
                    ['cypher-shell', '-u', self.username, '-p', self.password, '--non-interactive', '--format', 'plain'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=command + "\n")

                if process.returncode == 0 and stdout.strip():
                    value = stdout.strip().split('\n')[-1]  # 获取最后一行（结果值）
                    logger.info(f"   {description}: {value}")
            except Exception as e:
                logger.info(f"   {description}: 查询失败 - {e}")

        logger.info("\n🔗 访问方式:")
        logger.info('   Neo4j Browser: http://localhost:7474')
        logger.info('   连接字符串: bolt://localhost:7687')
        logger.info('   用户名: neo4j')
        logger.info('   密码: password')

        logger.info("\n💡 增量更新已启用，下次运行将只导入变更的文件")

def main():
    """主函数"""
    importer = EnhancedKnowledgeGraphImporter()

    try:
        success = importer.run_full_enhanced_import()

        if success:
            logger.info("\n🎉 知识图谱导入成功完成！")
            sys.exit(0)
        else:
            logger.info("\n⚠️ 部分导入失败，请检查错误信息")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️ 用户中断导入")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n❌ 导入过程中发生异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()