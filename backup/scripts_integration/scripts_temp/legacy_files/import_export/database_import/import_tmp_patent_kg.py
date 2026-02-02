#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入/private/tmp下的专利知识图谱数据到Neo4j
包含:
1. patent_full_output: 实体和关系批次文件 (76个批次)
2. patent_full_layered_output: 层级化知识图谱 (25个批次，42GB)
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TempPatentKGImporter:
    def __init__(self, uri='bolt://localhost:7687', user=None, password=None):
        # 如果禁用了认证，使用None
        if user is None:
            self.driver = GraphDatabase.driver(uri)
        else:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.tmp_dir = Path('/private/tmp')

    def close(self):
        self.driver.close()

    def analyze_data(self):
        """分析所有数据目录的统计信息"""
        logger.info(str('=' * 80))
        logger.info('📊 /private/tmp 专利知识图谱数据分析')
        logger.info(str('=' * 80))

        # 1. patent_full_output分析
        full_output_dir = self.tmp_dir / 'patent_full_output'
        if full_output_dir.exists():
            entities_files = list(full_output_dir.glob('entities_batch_*.json'))
            relations_files = list(full_output_dir.glob('relations_batch_*.json'))

            logger.info(f"\n1️⃣ patent_full_output (标准格式):")
            logger.info(f"   - 实体批次文件: {len(entities_files)} 个")
            logger.info(f"   - 关系批次文件: {len(relations_files)} 个")

            # 统计实体总数
            total_entities = 0
            for ef in entities_files[:3]:  # 抽样统计
                with open(ef, 'r', encoding='utf-8') as f:
                    entities = json.load(f)
                    total_entities += len(entities)
            avg_entities = total_entities / min(3, len(entities_files))
            estimated_total_entities = avg_entities * len(entities_files)

            logger.info(f"   - 预估实体总数: {estimated_total_entities:,.0f}")

            # 统计关系总数
            total_relations = 0
            for rf in relations_files[:3]:  # 抽样统计
                with open(rf, 'r', encoding='utf-8') as f:
                    relations = json.load(f)
                    total_relations += len(relations)
            avg_relations = total_relations / min(3, len(relations_files))
            estimated_total_relations = avg_relations * len(relations_files)

            logger.info(f"   - 预估关系总数: {estimated_total_relations:,.0f}")

        # 2. patent_full_layered_output分析
        layered_dir = self.tmp_dir / 'patent_full_layered_output'
        if layered_dir.exists():
            layered_files = list(layered_dir.glob('patent_layered_batch_*.json'))
            logger.info(f"\n2️⃣ patent_full_layered_output (层级化格式):")
            logger.info(f"   - 批次文件数: {len(layered_files)} 个")
            logger.info(f"   - 总大小: 42GB")

            # 分析第一个文件的结构
            if layered_files:
                first_file = layered_files[0]
                with open(first_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    layer_stats = data.get('layer_stats', {})

                    logger.info(f"   - 批次大小: {data.get('batch_size', 0)} 个专利")
                    logger.info(f"   - 层级统计:")
                    for layer, stats in layer_stats.items():
                        if isinstance(stats, dict) and 'entities' in stats:
                            print(f"     {layer}: {stats['count']:,} 专利, "
                                  f"{stats['entities']:,} 实体, {stats['relations']:,} 关系")

        logger.info(str("\n" + '=' * 80))

    def setup_schema(self):
        """设置Neo4j数据库模式"""
        logger.info('设置数据库模式...')

        with self.driver.session() as session:
            # 删除现有数据（谨慎！）
            logger.warning('清理现有知识图谱数据...')
            session.run('MATCH (n) DETACH DELETE n')

            # 创建约束
            constraints = [
                'CREATE CONSTRAINT FOR (e:Entity) REQUIRE e.id IS UNIQUE',
                'CREATE CONSTRAINT FOR (p:Patent) REQUIRE p.id IS UNIQUE',
                'CREATE CONSTRAINT FOR (d:Document) REQUIRE d.path IS UNIQUE'
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.info(f"✅ 创建约束: {constraint}")
                except Exception as e:
                    logger.info(f"⚠️  约束已存在: {constraint}")

            # 创建索引
            indexes = [
                'CREATE INDEX FOR (e:Entity) ON (e.type)',
                'CREATE INDEX FOR (e:Entity) ON (e.name)',
                'CREATE INDEX FOR ()-[r:RELATES_TO]-() ON (r.type)'
            ]

            for idx in indexes:
                try:
                    session.run(idx)
                    logger.info(f"✅ 创建索引: {idx}")
                except Exception as e:
                    logger.info(f"⚠️  索引已存在: {idx}")

    def import_patent_full_output(self):
        """导入patent_full_output数据"""
        logger.info("\n开始导入 patent_full_output 数据...")

        full_output_dir = self.tmp_dir / 'patent_full_output'

        # 1. 先导入所有实体
        entities_files = sorted(full_output_dir.glob('entities_batch_*.json'))
        logger.info(f"找到 {len(entities_files)} 个实体批次文件")

        total_entities = 0
        for i, ef in enumerate(entities_files):
            logger.info(f"导入实体批次 {i+1}/{len(entities_files)}: {ef.name}")

            with open(ef, 'r', encoding='utf-8') as f:
                entities = json.load(f)

            with self.driver.session() as session:
                # 批量创建实体
                session.run("""
                    UNWIND $entities AS e
                    MERGE (ent:Entity {id: e.id})
                    SET ent.type = e.type,
                        ent.name = e.name,
                        ent.source = e.source,
                        ent.sources = e.sources,
                        ent.created_at = datetime()
                """, entities=entities)

            total_entities += len(entities)
            logger.info(f"  ✓ 创建 {len(entities)} 个实体")

        logger.info(f"✅ 实体导入完成，总计: {total_entities:,}")

        # 2. 导入关系
        relations_files = sorted(full_output_dir.glob('relations_batch_*.json'))
        logger.info(f"找到 {len(relations_files)} 个关系批次文件")

        total_relations = 0
        for i, rf in enumerate(relations_files):
            logger.info(f"导入关系批次 {i+1}/{len(relations_files)}: {rf.name}")

            with open(rf, 'r', encoding='utf-8') as f:
                relations = json.load(f)

            with self.driver.session() as session:
                # 批量创建关系
                session.run("""
                    UNWIND $relations AS r
                    MATCH (s:Entity {id: r.source})
                    MATCH (t:Entity {id: r.target})
                    MERGE (s)-[rel:RELATES_TO]->(t)
                    SET rel.type = r.type,
                        rel.source_file = r.source_file,
                        rel.created_at = datetime()
                """, relations=relations)

            total_relations += len(relations)
            logger.info(f"  ✓ 创建 {len(relations)} 个关系")

        logger.info(f"✅ 关系导入完成，总计: {total_relations:,}")

    def import_sample_layered_data(self, max_files=2):
        """导入部分层级化数据作为示例"""
        logger.info(f"\n开始导入前 {max_files} 个层级化批次数据...")

        layered_dir = self.tmp_dir / 'patent_full_layered_output'
        layered_files = sorted(layered_dir.glob('patent_layered_batch_*.json'))[:max_files]

        total_patents = 0
        total_entities = 0
        total_relations = 0

        for i, lf in enumerate(layered_files):
            logger.info(f"导入层级化批次 {i+1}: {lf.name}")

            with open(lf, 'r', encoding='utf-8') as f:
                data = json.load(f)

            batch_results = data.get('results', [])

            with self.driver.session() as session:
                for result in batch_results:
                    file_path = result.get('file', '')
                    entities = result.get('entities', [])
                    relations = result.get('relations', [])
                    quality = result.get('quality', 'basic')

                    # 创建文档节点
                    doc_id = file_path.replace('/', '_').replace('.', '_')
                    session.run("""
                        MERGE (d:Document {id: $doc_id})
                        SET d.path = $file_path,
                            d.quality = $quality,
                            d.created_at = datetime()
                    """, doc_id=doc_id, file_path=file_path, quality=quality)

                    # 创建实体并连接到文档
                    for ent in entities:
                        ent_id = ent.get('id', '')
                        ent_type = ent.get('type', '')
                        ent_value = ent.get('value', '')
                        ent_source = ent.get('source', '')

                        session.run("""
                            MERGE (e:Entity {id: $ent_id})
                            SET e.type = $ent_type,
                                e.value = $ent_value,
                                e.source = $ent_source,
                                e.created_at = datetime()
                            WITH e, $doc_id AS docId
                            MATCH (d:Document {id: docId})
                            MERGE (d)-[r:CONTAINS_ENTITY]->(e)
                        """, ent_id=ent_id, ent_type=ent_type, ent_value=ent_value,
                             ent_source=ent_source, doc_id=doc_id.replace('/', '_').replace('.', '_'))

                    # 创建关系
                    for rel in relations:
                        source = rel.get('source', '')
                        target = rel.get('target', '')
                        rel_type = rel.get('type', '')

                        # 简化处理：创建通用关系
                        session.run("""
                            MATCH (s:Entity {id: $source})
                            MATCH (t:Entity {id: $target})
                            MERGE (s)-[r:RELATES_TO]->(t)
                            SET r.type = $rel_type,
                                r.created_at = datetime()
                        """, source=source, target=target, rel_type=rel_type)

                    total_entities += len(entities)
                    total_relations += len(relations)

                total_patents += len(batch_results)

            logger.info(f"  ✓ 处理 {len(batch_results)} 个专利")

        logger.info(f"✅ 层级化数据导入完成:")
        logger.info(f"  - 专利文档: {total_patents:,}")
        logger.info(f"  - 实体: {total_entities:,}")
        logger.info(f"  - 关系: {total_relations:,}")

    def run_full_import(self):
        """执行完整导入流程"""
        start_time = time.time()

        try:
            # 1. 分析数据
            self.analyze_data()

            # 2. 设置模式
            self.setup_schema()

            # 3. 导入标准格式数据
            self.import_patent_full_output()

            # 4. 导入部分层级化数据作为示例
            self.import_sample_layered_data(max_files=2)

            # 5. 验证导入结果
            self.verify_import()

        except Exception as e:
            logger.error(f"导入过程中出错: {e}")
            raise
        finally:
            elapsed = time.time() - start_time
            logger.info(f"\n总耗时: {elapsed:.2f} 秒")

    def verify_import(self):
        """验证导入结果"""
        logger.info("\n验证导入结果...")

        with self.driver.session() as session:
            # 统计各类节点
            result = session.run('MATCH (e:Entity) RETURN count(e) as count')
            entity_count = result.single()['count']

            result = session.run('MATCH (d:Document) RETURN count(d) as count')
            doc_count = result.single()['count']

            result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
            rel_count = result.single()['count']

            # 统计实体类型分布
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(e) as count
                ORDER BY count DESC LIMIT 10
            """)
            entity_types = {record['type']: record['count'] for record in result}

            logger.info(str("\n" + '=' * 80))
            logger.info('📊 导入结果统计')
            logger.info(str('=' * 80))
            logger.info(f"✅ 实体节点数: {entity_count:,}")
            logger.info(f"✅ 文档节点数: {doc_count:,}")
            logger.info(f"✅ 关系数: {rel_count:,}")

            logger.info("\n📋 实体类型分布 (Top 10):")
            for ent_type, count in list(entity_types.items())[:10]:
                logger.info(f"  • {ent_type}: {count:,}")

            logger.info(str("\n" + '=' * 80))

def main():
    """主函数"""
    logger.info(str('=' * 80))
    logger.info('🚀 开始导入 /private/tmp 专利知识图谱数据到 Neo4j')
    logger.info(str('=' * 80))

    importer = TempPatentKGImporter()

    try:
        importer.run_full_import()
    except KeyboardInterrupt:
        logger.info("\n⚠️  用户中断导入")
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
    finally:
        importer.close()
        logger.info("\n🔚 导入任务结束")

if __name__ == '__main__':
    main()