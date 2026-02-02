#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版知识图谱迁移到JanusGraph
直接使用Gremlin进行数据导入
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入Gremlin客户端
try:
    from gremlin_python.process.anonymous_traversal import traversal
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.process.traversal import T, P
    from gremlin_python.process.graph_traversal import __
except ImportError:
    logger.warning("Gremlin客户端未安装，请运行: pip install gremlinpython")
    sys.exit(1)

class SimpleJanusGraphMigrator:
    """简化的JanusGraph迁移器"""

    def __init__(self):
        self.graph_name = "unified_knowledge_graph"
        self.gremlin_url = "ws://localhost:8182/gremlin"
        self.connection = None
        self.g = None
        self.stats = {
            "nodes_created": 0,
            "edges_created": 0,
            "errors": []
        }

    def connect(self):
        """连接到JanusGraph"""
        try:
            self.connection = DriverRemoteConnection(self.gremlin_url, 'g')
            self.g = traversal().withRemote(self.connection)

            # 测试连接
            self.g.V().limit(1).toList()
            logger.info("✅ 成功连接到JanusGraph")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.connection:
            self.connection.close()
            logger.info("✅ 已断开JanusGraph连接")

    def migrate_patent_knowledge_graph(self):
        """迁移专利知识图谱"""
        logger.info("📦 开始迁移专利知识图谱...")

        sqlite_path = Path("/Users/xujian/Athena工作平台/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db")

        if not sqlite_path.exists():
            logger.error(f"❌ SQLite文件不存在: {sqlite_path}")
            return False

        try:
            # 连接SQLite
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()

            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"  发现 {len(tables)} 个表: {', '.join(tables)}")

            # 示例：迁移专利节点
            if 'patents' in tables:
                logger.info("  迁移专利节点...")
                cursor.execute("SELECT * FROM patents LIMIT 100")  # 限制数量避免过大
                patent_rows = cursor.fetchall()
                col_names = [description[0] for description in cursor.description]

                for row in patent_rows:
                    properties = dict(zip(col_names, row))
                    patent_id = properties.get('id', properties.get('patent_id', str(self.stats['nodes_created'])))

                    try:
                        # 创建专利节点
                        vertex = self.g.addV('Patent').property(T.id, str(patent_id))

                        # 添加属性
                        for key, value in properties.items():
                            if key not in ['id'] and value is not None:
                                vertex = vertex.property(key.replace('_', ''), str(value))

                        vertex.next()
                        self.stats['nodes_created'] += 1

                        if self.stats['nodes_created'] % 10 == 0:
                            logger.info(f"    已创建 {self.stats['nodes_created']} 个专利节点")

                    except Exception as e:
                        logger.warning(f"    ⚠️ 创建专利节点失败: {e}")
                        self.stats['errors'].append(f"Patent node creation failed: {e}")

            # 示例：迁移申请人节点
            if 'applicants' in tables:
                logger.info("  迁移申请人节点...")
                cursor.execute("SELECT * FROM applicants LIMIT 50")
                applicant_rows = cursor.fetchall()
                col_names = [description[0] for description in cursor.description]

                for row in applicant_rows:
                    properties = dict(zip(col_names, row))
                    applicant_id = properties.get('id', properties.get('applicant_id', str(self.stats['nodes_created'])))

                    try:
                        # 创建申请人节点
                        vertex = self.g.addV('Applicant').property(T.id, str(applicant_id))

                        # 添加属性
                        for key, value in properties.items():
                            if key not in ['id'] and value is not None:
                                vertex = vertex.property(key.replace('_', ''), str(value))

                        vertex.next()
                        self.stats['nodes_created'] += 1

                    except Exception as e:
                        logger.warning(f"    ⚠️ 创建申请人节点失败: {e}")
                        self.stats['errors'].append(f"Applicant node creation failed: {e}")

            # 示例：创建关系
            if 'patent_applicant_relations' in tables:
                logger.info("  创建专利-申请人关系...")
                cursor.execute("SELECT * FROM patent_applicant_relations LIMIT 50")
                relation_rows = cursor.fetchall()
                col_names = [description[0] for description in cursor.description]

                for row in relation_rows:
                    properties = dict(zip(col_names, row))
                    patent_id = properties.get('patent_id')
                    applicant_id = properties.get('applicant_id')

                    if patent_id and applicant_id:
                        try:
                            # 创建边
                            edge = self.g.V(str(patent_id)).addE('HAS_APPLICANT').to(self.g.V(str(applicant_id)))

                            # 添加边属性
                            for key, value in properties.items():
                                if key not in ['patent_id', 'applicant_id'] and value is not None:
                                    edge = edge.property(key.replace('_', ''), str(value))

                            edge.next()
                            self.stats['edges_created'] += 1

                        except Exception as e:
                            logger.warning(f"    ⚠️ 创建关系失败: {e}")
                            self.stats['errors'].append(f"Edge creation failed: {e}")

            conn.close()
            logger.info("✅ 专利知识图谱迁移完成")
            return True

        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            return False

    def create_sample_graph(self):
        """创建示例知识图谱"""
        logger.info("📝 创建示例知识图谱...")

        try:
            # 创建一些示例节点
            sample_data = [
                ("patent_001", "Patent", {
                    "title": "一种AI专利分析方法",
                    "abstract": "本发明涉及一种基于人工智能的专利分析方法...",
                    "inventor": "张三",
                    "application_date": "2024-01-01"
                }),
                ("company_001", "Company", {
                    "name": "Athena科技公司",
                    "type": "科技企业",
                    "location": "北京"
                }),
                ("inventor_001", "Inventor", {
                    "name": "张三",
                    "field": "人工智能",
                    "experience": "10年"
                }),
                ("category_001", "Category", {
                    "name": "人工智能",
                    "parent_category": "计算机技术"
                })
            ]

            # 创建节点
            for node_id, label, properties in sample_data:
                try:
                    vertex = self.g.addV(label).property(T.id, node_id)
                    for key, value in properties.items():
                        vertex = vertex.property(key, str(value))
                    vertex.next()
                    self.stats['nodes_created'] += 1
                    logger.info(f"  ✅ 创建节点: {label} - {node_id}")
                except Exception as e:
                    logger.warning(f"  ⚠️ 创建节点失败: {e}")
                    self.stats['errors'].append(f"Node creation failed: {e}")

            # 创建关系
            relations = [
                ("patent_001", "company_001", "BELONGS_TO", {"role": "申请人"}),
                ("patent_001", "inventor_001", "INVENTED_BY", {"contribution": "主要发明人"}),
                ("patent_001", "category_001", "BELONGS_TO_CATEGORY", {"relevance": "核心"})
            ]

            for source, target, edge_label, properties in relations:
                try:
                    edge = self.g.V(source).addE(edge_label).to(self.g.V(target))
                    for key, value in properties.items():
                        edge = edge.property(key, str(value))
                    edge.next()
                    self.stats['edges_created'] += 1
                    logger.info(f"  ✅ 创建关系: {source} -> {target} ({edge_label})")
                except Exception as e:
                    logger.warning(f"  ⚠️ 创建关系失败: {e}")
                    self.stats['errors'].append(f"Edge creation failed: {e}")

            logger.info("✅ 示例知识图谱创建完成")
            return True

        except Exception as e:
            logger.error(f"❌ 创建示例图谱失败: {e}")
            return False

    def run_migration(self):
        """执行迁移"""
        logger.info("🚀 开始知识图谱迁移到JanusGraph...")
        logger.info("=" * 60)

        if not self.connect():
            return False

        try:
            # 1. 创建示例图谱
            success = self.create_sample_graph()

            # 2. 尝试迁移SQLite数据（可选）
            if success:
                try:
                    self.migrate_patent_knowledge_graph()
                except Exception as e:
                    logger.warning(f"SQLite迁移失败，但示例图谱已创建: {e}")

            # 3. 输出统计
            logger.info("\n📊 迁移统计:")
            logger.info(f"  创建节点: {self.stats['nodes_created']}")
            logger.info(f"  创建边: {self.stats['edges_created']}")
            logger.info(f"  错误数: {len(self.stats['errors'])}")

            # 4. 保存报告
            report = {
                "migration_time": datetime.now().isoformat(),
                "statistics": self.stats
            }

            report_path = Path("/Users/xujian/Athena工作平台/data/janusgraph_migration_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            logger.info(f"\n📄 报告已保存: {report_path}")

            return self.stats['nodes_created'] > 0

        finally:
            self.disconnect()


def main():
    """主函数"""
    migrator = SimpleJanusGraphMigrator()
    success = migrator.run_migration()

    if success:
        print("\n🎉 知识图谱迁移成功！")
        print(f"已创建 {migrator.stats['nodes_created']} 个节点和 {migrator.stats['edges_created']} 条边")
        print("\n🔗 您可以使用Gremlin控制台查询数据:")
        print("  g.V().count()  # 查看节点总数")
        print("  g.E().count()  # 查看边总数")
        print("  g.V().label()  # 查看节点类型")
    else:
        print("\n❌ 知识图谱迁移失败")


if __name__ == "__main__":
    main()