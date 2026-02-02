#!/usr/bin/env python3
"""
知识图谱数据导入脚本
支持多种数据源和导入方式
"""

import csv
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class KnowledgeGraphImporter:
    def __init__(self, neo4j_uri: str = 'bolt://localhost:7687',
                 username: str = 'neo4j', password: str = 'password'):
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password
        self.data_dir = Path('/Users/xujian/Athena工作平台/data/knowledge_graph_neo4j')

    def check_neo4j_status(self) -> bool:
        """检查Neo4j是否运行"""
        try:
            result = subprocess.run(['neo4j', 'status'],
                                  capture_output=True, text=True)
            return 'running' in result.stdout.lower()
        except Exception as e:
            logger.info(f"检查Neo4j状态失败: {e}")
            return False

    def import_cypher_script(self, script_path: Path) -> bool:
        """导入Cypher脚本"""
        if not script_path.exists():
            logger.info(f"脚本文件不存在: {script_path}")
            return False

        logger.info(f"正在导入: {script_path}")
        try:
            cmd = f'cypher-shell -u {self.username} -p {self.password} < '{script_path}''
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ 成功导入: {script_path}")
                return True
            else:
                logger.info(f"❌ 导入失败: {script_path}")
                logger.info(f"错误信息: {result.stderr}")
                return False
        except Exception as e:
            logger.info(f"导入异常: {e}")
            return False

    def import_json_knowledge_graph(self, json_path: Path, graph_name: str) -> bool:
        """从JSON文件导入知识图谱"""
        if not json_path.exists():
            logger.info(f"JSON文件不存在: {json_path}")
            return False

        logger.info(f"正在导入JSON知识图谱: {json_path}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 生成Cypher脚本
            cypher_script = self.generate_cypher_from_json(data, graph_name)

            # 写入临时文件
            temp_script = f"/tmp/{graph_name}_import.cypher"
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(cypher_script)

            # 执行导入
            return self.import_cypher_script(Path(temp_script))

        except Exception as e:
            logger.info(f"JSON导入异常: {e}")
            return False

    def generate_cypher_from_json(self, data: Dict, graph_name: str) -> str:
        """从JSON数据生成Cypher脚本"""
        cypher_commands = []

        # 清理现有数据
        cypher_commands.append(f"MATCH (n:{graph_name}) DETACH DELETE n;")

        # 创建约束
        cypher_commands.append(f"CREATE CONSTRAINT FOR (n:{graph_name}) REQUIRE n.name IS UNIQUE;")

        # 导入实体
        entities = data.get('entities', [])
        for entity in entities:
            name = entity.get('name', '').replace('"', '\\"')
            entity_type = entity.get('entity_type', 'Unknown')
            confidence = entity.get('confidence', 0.8)
            source = entity.get('source', '')

            cypher_commands.append(
                f'MERGE (n:{graph_name} {{name: '{name}', entity_type: '{entity_type}', '
                f'confidence: {confidence}, source: '{source}'}});'
            )

        # 导入关系
        relations = data.get('relations', [])
        for relation in relations:
            source = relation.get('source', '').replace('"', '\\"')
            target = relation.get('target', '').replace('"', '\\"')
            rel_type = relation.get('relation_type', 'RELATED_TO')

            cypher_commands.append(
                f'MATCH (a:{graph_name} {{name: '{source}'}}) '
                f'MATCH (b:{graph_name} {{name: '{target}'}}) '
                f'MERGE (a)-[r:{rel_type}]->(b);'
            )

        return '\n'.join(cypher_commands)

    def import_csv_data(self, csv_dir: Path) -> bool:
        """导入CSV格式的知识图谱数据"""
        if not csv_dir.exists():
            logger.info(f"CSV目录不存在: {csv_dir}")
            return False

        # 复制CSV文件到Neo4j import目录
        neo4j_import_dir = '/opt/homebrew/var/neo4j/import/'

        try:
            # 查找CSV文件
            csv_files = list(csv_dir.glob('*.csv'))
            if not csv_files:
                logger.info('未找到CSV文件')
                return False

            for csv_file in csv_files:
                dest = Path(neo4j_import_dir) / csv_file.name
                subprocess.run(['cp', str(csv_file), str(dest)], check=True)
                logger.info(f"复制CSV文件: {csv_file.name}")

            # 执行CSV导入Cypher
            csv_import_cypher = """
            // 导入专利节点
            LOAD CSV WITH HEADERS FROM 'file:///patents.csv' AS row
            MERGE (p:Patent {id: row.id})
            SET p.name = row.name,
                p.type = row.type,
                p.description = row.description,
                p.source = row.source;

            // 导入关系
            LOAD CSV WITH HEADERS FROM 'file:///relations.csv' AS row
            MATCH (a:Patent {id: row.source_id})
            MATCH (b:Patent {id: row.target_id})
            MERGE (a)-[r:RELATED {type: row.relation_type, weight: toFloat(row.weight)}]->(b);
            """

            temp_script = '/tmp/csv_import.cypher'
            with open(temp_script, 'w') as f:
                f.write(csv_import_cypher)

            return self.import_cypher_script(Path(temp_script))

        except Exception as e:
            logger.info(f"CSV导入异常: {e}")
            return False

    def run_full_import(self):
        """执行完整的知识图谱导入"""
        logger.info('🚀 开始知识图谱数据导入...')

        # 检查Neo4j状态
        if not self.check_neo4j_status():
            logger.info('❌ Neo4j未运行，请先启动Neo4j')
            return False

        success_count = 0
        total_count = 0

        # 1. 导入统一法律知识图谱
        legal_script = self.data_dir / 'processed_data' / 'unified_legal_kg_import.cypher'
        if legal_script.exists():
            total_count += 1
            if self.import_cypher_script(legal_script):
                success_count += 1

        # 2. 导入专利知识图谱
        patent_script = self.data_dir / 'processed_data' / 'unified_patent_kg' / 'patent_kg_unified_import.cypher'
        if patent_script.exists():
            total_count += 1
            if self.import_cypher_script(patent_script):
                success_count += 1

        # 3. 导入生产法律知识图谱
        legal_json = self.data_dir / 'raw_data' / 'production_legal_knowledge_graph' / 'production_legal_knowledge_graph.json'
        if legal_json.exists():
            total_count += 1
            if self.import_json_knowledge_graph(legal_json, 'ProductionLegal'):
                success_count += 1

        # 4. 导入CSV数据
        csv_dir = self.data_dir / 'raw_data' / 'neo4j_import'
        if csv_dir.exists():
            total_count += 1
            if self.import_csv_data(csv_dir):
                success_count += 1

        # 5. 导入其他JSON知识图谱
        json_graphs = [
            ('patent_judgment_kg', 'enhanced_patent_judgment_entities'),
            ('patent_kg', 'patent_kg'),
            ('technical_terms_knowledge_graph', 'technical_knowledge_graph')
        ]

        for graph_dir, entity_file in json_graphs:
            json_path = self.data_dir / 'raw_data' / graph_dir
            if json_path.exists():
                entity_files = list(json_path.glob(f"{entity_file}*.json"))
                if entity_files:
                    total_count += 1
                    if self.import_json_knowledge_graph(entity_files[0], graph_dir.replace('_kg', '')):
                        success_count += 1

        logger.info(f"\n📊 导入完成: {success_count}/{total_count} 个数据源成功导入")

        if success_count == total_count:
            logger.info('🎉 所有知识图谱数据导入成功！')
            return True
        else:
            logger.info('⚠️ 部分数据导入失败，请检查错误信息')
            return False

def main():
    """主函数"""
    logger.info(str('=' * 60))
    logger.info('🏛️  Athena知识图谱数据导入工具')
    logger.info(str('=' * 60))

    # 配置导入器
    importer = KnowledgeGraphImporter()

    # 询问密码
    import getpass
    password = getpass.getpass('请输入Neo4j密码: ')
    importer.password = password

    # 执行导入
    start_time = time.time()
    success = importer.run_full_import()
    end_time = time.time()

    logger.info(f"\n⏱️ 总耗时: {end_time - start_time:.2f}秒")

    if success:
        logger.info("\n✅ 知识图谱导入完成！")
        logger.info("\n🔍 您可以使用以下命令验证导入结果:")
        logger.info('cypher-shell -u neo4j -p')
        logger.info('MATCH (n) RETURN count(n) as 总节点数;')
        logger.info('MATCH ()-[r]->() RETURN count(r) as 总关系数;')
    else:
        logger.info("\n❌ 导入过程中遇到错误，请检查日志")

if __name__ == '__main__':
    main()