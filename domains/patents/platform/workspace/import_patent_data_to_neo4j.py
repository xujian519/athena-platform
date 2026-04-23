#!/usr/bin/env python3
"""
专利知识图谱数据导入Neo4j系统
Patent Knowledge Graph Data Import to Neo4j

将已处理的专利数据批量导入到Neo4j图数据库

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from neo4j import Driver, GraphDatabase, Session

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'patent_neo4j_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PatentNeo4jImporter:
    """专利知识图谱Neo4j导入器"""

    def __init__(self, uri: str = 'bolt://localhost:7687',
                 username: str = 'neo4j', password: str = 'password'):
        """
        初始化Neo4j连接

        Args:
            uri: Neo4j数据库URI
            username: 用户名
            password: 密码
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver: Driver | None = None
        self.lock = threading.Lock()
        self.stats = {
            'total_nodes': 0,
            'total_relationships': 0,
            'import_errors': 0,
            'import_time': 0,
            'files_processed': 0
        }

    def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # 测试连接
            with self.driver.session() as session:
                session.run('RETURN 1')
            logger.info('✅ 成功连接到Neo4j数据库')
            return True
        except Exception as e:
            logger.error(f"❌ 连接Neo4j失败: {e}")
            return False

    def create_constraints_and_indexes(self) -> None:
        """创建数据库约束和索引"""
        constraints_queries = [
            # 创建唯一性约束
            'CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patent) REQUIRE p.patent_id IS UNIQUE',
            'CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE',
            'CREATE CONSTRAINT IF NOT EXISTS FOR (c:Claim) REQUIRE c.claim_id IS UNIQUE',

            # 创建索引
            'CREATE INDEX IF NOT EXISTS FOR (p:Patent) ON (p.title)',
            'CREATE INDEX IF NOT EXISTS FOR (p:Patent) ON (p.application_number)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.category)',
            'CREATE INDEX IF NOT EXISTS FOR (t:Technology) ON (t.field)',
            'CREATE INDEX IF NOT EXISTS FOR (t:Technology) ON (t.subfield)'
        ]

        with self.driver.session() as session:
            for query in constraints_queries:
                try:
                    session.run(query)
                    logger.info(f"✅ 成功执行: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"⚠️ 约束/索引创建警告: {e}")

    def import_patent_document(self, patent_data: dict, session: Session) -> dict[str, int]:
        """
        导入单个专利文档

        Returns:
            Dict: 导入统计 {nodes: 节点数, relationships: 关系数}
        """
        stats = {'nodes': 0, 'relationships': 0}

        try:
            # 1. 导入专利主节点
            patent_id = patent_data.get('patent_id', '')
            self._create_patent_node(session, patent_data)
            stats['nodes'] += 1

            # 2. 导入实体节点
            entities = patent_data.get('entities', [])
            entity_nodes = {}
            for entity in entities:
                # 生成并存储实体ID映射
                original_id = entity.get('entity_id', entity.get('name', ''))
                generated_id = self._create_entity_node(session, entity)
                entity_nodes[original_id] = generated_id  # 使用原始ID映射到生成的ID
                stats['nodes'] += 1

                # 创建专利与实体的关系
                session.run(
                    """
                    MATCH (p:Patent {patent_id: $patent_id}), (e:Entity {entity_id: $entity_id})
                    MERGE (p)-[r:CONTAINS]->(e)
                    SET r.confidence = $confidence, r.context = $context
                    """,
                    patent_id=patent_id,
                    entity_id=generated_id,
                    confidence=entity.get('confidence', 0.0),
                    context=entity.get('context', '')
                )
                stats['relationships'] += 1

            # 3. 导入关系
            relations = patent_data.get('relations', [])
            for relation in relations:
                self._create_relationship(session, relation, entity_nodes)
                stats['relationships'] += 1

            # 4. 导入权利要求
            claims = patent_data.get('claims', [])
            for claim in claims:
                self._create_claim_node(session, claim, patent_id)
                stats['nodes'] += 1

                # 创建权利要求与实体的关系
                claim_entities = claim.get('entities', [])
                for claim_entity in claim_entities:
                    original_id = claim_entity.get('entity_id', claim_entity.get('name', ''))
                    if original_id in entity_nodes:
                        generated_id = entity_nodes[original_id]
                        session.run(
                            """
                            MATCH (c:Claim {claim_id: $claim_id}), (e:Entity {entity_id: $entity_id})
                            MERGE (c)-[r:REFERENCES]->(e)
                            SET r.context = $context
                            """,
                            claim_id=claim.get('claim_id', ''),
                            entity_id=generated_id,
                            context=claim_entity.get('context', '')
                        )
                        stats['relationships'] += 1

        except Exception as e:
            logger.error(f"导入专利 {patent_id} 时出错: {e}")
            raise

        return stats

    def _create_patent_node(self, session: Session, patent_data: dict) -> None:
        """创建专利节点"""
        query = """
        MERGE (p:Patent {patent_id: $patent_id})
        SET p.title = $title,
            p.abstract = $abstract,
            p.application_number = $application_number,
            p.publication_number = $publication_number,
            p.inventor = $inventor,
            p.assignee = $assignee,
            p.filing_date = $filing_date,
            p.publication_date = $publication_date,
            p.patent_type = $patent_type,
            p.status = $status,
            p.quality_score = $quality_score,
            p.layer = $layer,
            p.created_at = datetime()
        """

        session.run(query,
            patent_id=patent_data.get('patent_id', ''),
            title=patent_data.get('title', ''),
            abstract=patent_data.get('abstract', ''),
            application_number=patent_data.get('application_number', ''),
            publication_number=patent_data.get('publication_number', ''),
            inventor=', '.join(patent_data.get('inventor', [])),
            assignee=', '.join(patent_data.get('assignee', [])),
            filing_date=patent_data.get('filing_date', ''),
            publication_date=patent_data.get('publication_date', ''),
            patent_type=patent_data.get('patent_type', ''),
            status=patent_data.get('status', ''),
            quality_score=patent_data.get('quality_score', 0.0),
            layer=patent_data.get('layer', 'basic')
        )

    def _create_entity_node(self, session: Session, entity: dict) -> str:
        """创建实体节点"""
        entity_type = entity.get('type', 'Unknown').replace(' ', '_').replace('-', '_')

        # 处理空的entity_id - 生成唯一标识符
        entity_id = entity.get('entity_id', '') or entity.get('id', '')
        entity_name = entity.get('name', '') or entity.get('value', '').strip()

        if not entity_id:
            if entity_name:
                # 使用名称生成ID，替换特殊字符
                entity_id = f"entity_{hash(entity_name)}_{len(entity_name)}"
            else:
                # 使用实体类型和计数器生成ID
                import uuid
                entity_id = f"entity_{entity_type}_{str(uuid.uuid4())[:8]}"

        # 根据实体类型使用不同的标签
        if entity_type.lower() in ['technology', 'tech', 'method', 'system']:
            labels = ['Entity', 'Technology']
        elif entity_type.lower() in ['component', 'part', 'device']:
            labels = ['Entity', 'Component']
        elif entity_type.lower() in ['material', 'substance']:
            labels = ['Entity', 'Material']
        elif entity_type.lower() in ['process', 'procedure', 'method']:
            labels = ['Entity', 'Process']
        else:
            labels = ['Entity']

        labels.append(f'{entity_type}')

        query = f"""
        MERGE (e:{':'.join(labels)} {{entity_id: $entity_id}})
        SET e.name = $name,
            e.type = $type,
            e.category = $category,
            e.confidence = $confidence,
            e.description = $description,
            e.properties = $properties,
            e.created_at = datetime()
        """

        session.run(query,
            entity_id=entity_id,
            name=entity_name,
            type=entity.get('type', ''),
            category=entity.get('category', ''),
            confidence=entity.get('confidence', 0.0),
            description=entity.get('description', ''),
            properties=json.dumps(entity.get('properties', {})) if entity.get('properties') else '{}'
        )

        return entity_id

    def _create_claim_node(self, session: Session, claim: dict, patent_id: str) -> None:
        """创建权利要求节点"""
        query = """
        MERGE (c:Claim {claim_id: $claim_id})
        SET c.text = $text,
            c.claim_number = $claim_number,
            c.claim_type = $claim_type,
            c.patent_id = $patent_id,
            c.created_at = datetime()
        WITH c, $patent_id AS pid
        MATCH (p:Patent {patent_id: pid})
        MERGE (p)-[r:HAS_CLAIM]->(c)
        """

        session.run(query,
            claim_id=claim.get('claim_id', ''),
            text=claim.get('text', ''),
            claim_number=claim.get('claim_number', 0),
            claim_type=claim.get('claim_type', ''),
            patent_id=patent_id
        )

    def _create_relationship(self, session: Session, relation: dict, entity_nodes: dict) -> None:
        """创建关系"""
        source_id = relation.get('source', '')
        target_id = relation.get('target', '')
        relation_type = relation.get('type', 'RELATED_TO').replace(' ', '_').upper()

        if source_id not in entity_nodes or target_id not in entity_nodes:
            return

        query = f"""
        MATCH (source {{entity_id: $source_id}}), (target {{entity_id: $target_id}})
        MERGE (source)-[r:{relation_type}]->(target)
        SET r.confidence = $confidence,
            r.description = $description,
            r.context = $context,
            r.properties = $properties
        """

        session.run(query,
            source_id=source_id,
            target_id=target_id,
            confidence=relation.get('confidence', 0.0),
            description=relation.get('description', ''),
            context=relation.get('context', ''),
            properties=json.dumps(relation.get('properties', {}))
        )

    def import_json_file(self, file_path: Path) -> dict[str, Any]:
        """导入JSON文件"""
        start_time = time.time()
        file_stats = {
            'file_path': str(file_path),
            'patents_count': 0,
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': 0,
            'processing_time': 0
        }

        try:
            logger.info(f"📄 开始导入文件: {file_path}")

            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            # 处理不同的数据格式
            if 'results' in data:
                patents = data['results']
            elif 'patents' in data:
                patents = data['patents']
            else:
                patents = [data] if 'patent_id' in data else []

            file_stats['patents_count'] = len(patents)

            with self.driver.session() as session:
                for patent in patents:
                    try:
                        patent_stats = self.import_patent_document(patent, session)
                        file_stats['nodes_created'] += patent_stats['nodes']
                        file_stats['relationships_created'] += patent_stats['relationships']
                    except Exception as e:
                        file_stats['errors'] += 1
                        logger.error(f"导入专利出错: {e}")

            file_stats['processing_time'] = time.time() - start_time

            logger.info(f"✅ 文件导入完成: {file_path}")
            logger.info(f"   专利数: {file_stats['patents_count']}, "
                       f"节点: {file_stats['nodes_created']}, "
                       f"关系: {file_stats['relationships_created']}, "
                       f"错误: {file_stats['errors']}")

        except Exception as e:
            logger.error(f"❌ 导入文件失败 {file_path}: {e}")
            file_stats['errors'] += 1

        return file_stats

    def import_batch_files(self, input_dir: str, pattern: str = '*.json',
                          max_workers: int = 4) -> dict[str, Any]:
        """批量导入文件"""
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")

        json_files = list(input_path.glob(pattern))
        if not json_files:
            logger.warning(f"在 {input_dir} 中没有找到匹配 {pattern} 的文件")
            return {'total_files': 0, 'results': []}

        logger.info(f"📂 找到 {len(json_files)} 个文件待导入")

        results = []
        total_start_time = time.time()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.import_json_file, file): file
                            for file in json_files}

            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)

                    # 更新总体统计
                    with self.lock:
                        self.stats['total_nodes'] += result['nodes_created']
                        self.stats['total_relationships'] += result['relationships_created']
                        self.stats['import_errors'] += result['errors']
                        self.stats['files_processed'] += 1

                except Exception as e:
                    logger.error(f"导入文件 {file} 时发生异常: {e}")
                    with self.lock:
                        self.stats['import_errors'] += 1

        self.stats['import_time'] = time.time() - total_start_time

        return {
            'total_files': len(json_files),
            'results': results,
            'stats': self.stats
        }

    def get_database_statistics(self) -> dict[str, Any]:
        """获取数据库统计信息"""
        with self.driver.session() as session:
            # 节点统计
            node_stats = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """).data()

            # 关系统计
            rel_stats = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """).data()

            # 总计
            total_nodes = session.run('MATCH (n) RETURN count(n) as count').single()['count']
            total_rels = session.run('MATCH ()-[r]->() RETURN count(r) as count').single()['count']

            return {
                'total_nodes': total_nodes,
                'total_relationships': total_rels,
                'node_types': node_stats,
                'relationship_types': rel_stats
            }

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info('🔌 已关闭Neo4j连接')

def main():
    """主函数"""
    logger.info('🚀 专利知识图谱Neo4j导入系统')
    logger.info(str('=' * 50))

    # 初始化导入器
    importer = PatentNeo4jImporter()

    try:
        # 连接数据库
        if not importer.connect():
            logger.info('❌ 无法连接到Neo4j数据库')
            return

        # 创建约束和索引
        logger.info('📋 创建数据库约束和索引...')
        importer.create_constraints_and_indexes()

        # 导入数据目录
        import_dirs = [
            '/tmp/patent_layered_output',
            '/tmp/patent_hq_output',
            '/tmp/patent_premium_output',
            '/tmp/patent_full_layered_output'
        ]

        all_results = []

        for import_dir in import_dirs:
            if Path(import_dir).exists():
                logger.info(f"\n📁 导入目录: {import_dir}")
                result = importer.import_batch_files(
                    input_dir=import_dir,
                    pattern='*.json',
                    max_workers=2  # 控制并发数
                )
                all_results.append(result)

        # 显示导入统计
        logger.info("\n📊 导入完成统计")
        logger.info(str('=' * 50))

        total_files = sum(r['total_files'] for r in all_results)
        total_nodes = importer.stats['total_nodes']
        total_rels = importer.stats['total_relationships']
        total_errors = importer.stats['import_errors']
        import_time = importer.stats['import_time']

        logger.info(f"📄 处理文件数: {total_files}")
        logger.info(f"🔗 创建节点数: {total_nodes:,}")
        logger.info(f"🔗 创建关系数: {total_rels:,}")
        logger.info(f"❌ 错误数量: {total_errors}")
        logger.info(f"⏱️ 导入耗时: {import_time:.2f}秒")

        # 获取数据库统计
        logger.info("\n📈 数据库统计")
        logger.info(str('-' * 30))
        db_stats = importer.get_database_statistics()

        logger.info(f"总节点数: {db_stats['total_nodes']:,}")
        logger.info(f"总关系数: {db_stats['total_relationships']:,}")

        logger.info("\n节点类型分布:")
        for node_type in db_stats['node_types'][:10]:  # 显示前10种
            labels = ', '.join(node_type['labels'])
            logger.info(f"  {labels}: {node_type['count']:,}")

        logger.info("\n关系类型分布:")
        for rel_type in db_stats['relationship_types'][:10]:  # 显示前10种
            logger.info(f"  {rel_type['type']}: {rel_type['count']:,}")

        logger.info("\n✅ 专利知识图谱数据导入完成！")
        logger.info("🌐 Neo4j Web界面: http://localhost:7474")
        logger.info("🔍 Bolt连接: bolt://localhost:7687")

    except Exception as e:
        logger.error(f"❌ 导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        importer.close()

if __name__ == '__main__':
    main()
