#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查平台知识图谱状态
扫描所有知识图谱资源并验证JanusGraph服务
"""

import os
import json
import sqlite3
import logging
import requests
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeGraphChecker:
    """知识图谱检查器"""

    def __init__(self):
        self.project_root = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.project_root / "data"
        self.knowledge_graphs = {}

    def check_janusgraph_status(self):
        """检查JanusGraph服务状态"""
        logger.info("🔍 检查JanusGraph服务状态...")
        logger.info("-" * 50)

        janusgraph_status = {
            "gremlin_port": False,
            "web_interface": False,
            "storage_backend": False
        }

        # 1. 检查Gremlin端口
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8182))
            sock.close()

            if result == 0:
                janusgraph_status["gremlin_port"] = True
                logger.info("✅ Gremlin端口 (8182) 正在监听")
            else:
                logger.error("❌ Gremlin端口 (8182) 未监听")
        except Exception as e:
            logger.error(f"❌ Gremlin端口检查失败: {e}")

        # 2. 检查Web接口
        try:
            response = requests.get("http://localhost:8182/", timeout=5)
            if response.status_code == 200:
                janusgraph_status["web_interface"] = True
                logger.info("✅ Web接口响应正常")
            else:
                logger.warning(f"⚠️ Web接口状态码: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Web接口检查失败: {e}")

        # 3. 检查存储后端
        storage_paths = [
            self.project_root / "storage-system" / "janusgraph" / "db",
            self.project_root / "data" / "janusgraph",
            self.project_root / "misc" / "janusgraph"
        ]

        for storage_path in storage_paths:
            if storage_path.exists():
                janusgraph_status["storage_backend"] = True
                logger.info(f"✅ 找到存储目录: {storage_path}")
                break
        else:
            logger.warning("⚠️ 未找到JanusGraph存储目录")

        return janusgraph_status

    def scan_knowledge_graph_sources(self):
        """扫描所有知识图谱数据源"""
        logger.info("\n📚 扫描知识图谱数据源...")
        logger.info("-" * 50)

        # 1. SQLite知识图谱
        sqlite_graphs = self._scan_sqlite_graphs()
        if sqlite_graphs:
            self.knowledge_graphs["sqlite"] = sqlite_graphs

        # 2. Neo4j知识图谱
        neo4j_graphs = self._scan_neo4j_graphs()
        if neo4j_graphs:
            self.knowledge_graphs["neo4j"] = neo4j_graphs

        # 3. JSON知识图谱数据
        json_graphs = self._scan_json_graphs()
        if json_graphs:
            self.knowledge_graphs["json"] = json_graphs

        # 4. CSV知识图谱数据
        csv_graphs = self._scan_csv_graphs()
        if csv_graphs:
            self.knowledge_graphs["csv"] = csv_graphs

        # 5. JanusGraph配置
        janusgraph_configs = self._scan_janusgraph_configs()
        if janusgraph_configs:
            self.knowledge_graphs["janusgraph_configs"] = janusgraph_configs

        # 统计汇总
        total_graphs = sum(len(graphs) for graphs in self.knowledge_graphs.values() if isinstance(graphs, dict))
        logger.info(f"\n📊 总计发现 {total_graphs} 个知识图谱资源")

        return self.knowledge_graphs

    def _scan_sqlite_graphs(self):
        """扫描SQLite知识图谱"""
        sqlite_graphs = {}
        sqlite_paths = [
            self.data_dir / "knowledge_graph_sqlite",
            self.data_dir / "athena_knowledge_graph.db",
            self.data_dir / "yunpat.db"
        ]

        for path in sqlite_paths:
            if path.exists():
                if path.is_dir():
                    # 扫描目录中的.db文件
                    for db_file in path.glob("**/*.db"):
                        try:
                            conn = sqlite3.connect(db_file)
                            cursor = conn.cursor()

                            # 获取表信息
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                            tables = cursor.fetchall()

                            # 获取记录数
                            total_records = 0
                            for table in tables:
                                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                                total_records += cursor.fetchone()[0]

                            sqlite_graphs[str(db_file.relative_to(self.project_root))] = {
                                "type": "sqlite",
                                "tables": len(tables),
                                "records": total_records,
                                "size_mb": db_file.stat().st_size / (1024*1024)
                            }

                            conn.close()
                            logger.info(f"  📄 SQLite: {db_file.name} ({len(tables)}表, {total_records}记录)")

                        except Exception as e:
                            logger.warning(f"    ⚠️ 读取失败 {db_file}: {e}")

                elif path.suffix == '.db':
                    # 单个DB文件
                    try:
                        size_mb = path.stat().st_size / (1024*1024)
                        sqlite_graphs[str(path.relative_to(self.project_root))] = {
                            "type": "sqlite",
                            "size_mb": size_mb
                        }
                        logger.info(f"  📄 SQLite: {path.name} ({size_mb:.2f}MB)")
                    except Exception as e:
                        logger.warning(f"    ⚠️ 获取信息失败 {path}: {e}")

        return sqlite_graphs

    def _scan_neo4j_graphs(self):
        """扫描Neo4j知识图谱"""
        neo4j_graphs = {}

        # 检查Neo4j数据目录
        neo4j_paths = [
            self.data_dir / "neo4j",
            self.project_root / "misc" / "neo4j"
        ]

        for neo4j_path in neo4j_paths:
            if neo4j_path.exists():
                # 扫描Neo4j数据文件
                for db_dir in neo4j_path.glob("**/databases/*"):
                    if db_dir.is_dir():
                        neo4j_graphs[str(db_dir.relative_to(self.project_root))] = {
                            "type": "neo4j",
                            "path": str(db_dir),
                            "data_files": len(list(db_dir.glob("*")))
                        }
                        logger.info(f"  🔵 Neo4j: {db_dir.name}")

        # 检查导出的Neo4j数据
        neo4j_exports = [
            self.data_dir / "neo4j_export",
            self.project_root / "backup" / "neo4j_backup"
        ]

        for export_path in neo4j_exports:
            if export_path.exists():
                export_files = list(export_path.glob("**/*.json"))
                if export_files:
                    neo4j_graphs[f"export_{export_path.name}"] = {
                        "type": "neo4j_export",
                        "files": len(export_files),
                        "path": str(export_path)
                    }
                    logger.info(f"  📤 Neo4j导出: {export_path.name} ({len(export_files)}文件)")

        return neo4j_graphs

    def _scan_json_graphs(self):
        """扫描JSON格式的知识图谱数据"""
        json_graphs = {}
        json_patterns = [
            "**/knowledge_graph*.json",
            "**/patent_kg*.json",
            "**/legal_kg*.json",
            "**/*triples*.json",
            "**/*graph*.json"
        ]

        for pattern in json_patterns:
            for json_file in self.data_dir.glob(pattern):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    size_mb = json_file.stat().st_size / (1024*1024)

                    # 分析数据结构
                    if isinstance(data, list):
                        record_count = len(data)
                    elif isinstance(data, dict):
                        record_count = sum(len(v) if isinstance(v, list) else 1 for v in data.values())
                    else:
                        record_count = 1

                    json_graphs[str(json_file.relative_to(self.project_root))] = {
                        "type": "json",
                        "size_mb": size_mb,
                        "records": record_count,
                        "structure": type(data).__name__
                    }

                    logger.info(f"  📋 JSON: {json_file.name} ({record_count}记录, {size_mb:.2f}MB)")

                except Exception as e:
                    logger.warning(f"    ⚠️ 读取失败 {json_file}: {e}")

        return json_graphs

    def _scan_csv_graphs(self):
        """扫描CSV格式的知识图谱数据"""
        csv_graphs = {}
        csv_patterns = [
            "**/knowledge_graph*.csv",
            "**/patent_kg*.csv",
            "**/legal_kg*.csv",
            "**/*triples*.csv",
            "**/*nodes*.csv",
            "**/*edges*.csv"
        ]

        for pattern in csv_patterns:
            for csv_file in self.data_dir.glob(pattern):
                try:
                    size_mb = csv_file.stat().st_size / (1024*1024)

                    # 简单估算行数
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        sample_lines = sum(1 for _ in islice(f, 1000))

                    csv_graphs[str(csv_file.relative_to(self.project_root))] = {
                        "type": "csv",
                        "size_mb": size_mb,
                        "sample_lines": sample_lines
                    }

                    logger.info(f"  📊 CSV: {csv_file.name} (~{sample_lines}行, {size_mb:.2f}MB)")

                except Exception as e:
                    logger.warning(f"    ⚠️ 读取失败 {csv_file}: {e}")

        return csv_graphs

    def _scan_janusgraph_configs(self):
        """扫描JanusGraph配置"""
        janusgraph_configs = {}
        config_dir = self.project_root / "storage-system" / "janusgraph" / "conf"

        if config_dir.exists():
            for config_file in config_dir.glob("*.properties"):
                janusgraph_configs[config_file.name] = {
                    "type": "janusgraph_config",
                    "path": str(config_file),
                    "size_bytes": config_file.stat().st_size
                }
                logger.info(f"  ⚙️ JanusGraph配置: {config_file.name}")

        return janusgraph_configs

    def generate_report(self):
        """生成检查报告"""
        logger.info("\n📋 生成知识图谱检查报告...")

        report = {
            "check_time": datetime.now().isoformat(),
            "janusgraph_status": self.check_janusgraph_status(),
            "knowledge_graphs": self.knowledge_graphs
        }

        # 保存报告
        report_path = self.data_dir / "knowledge_graph_check_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 报告已保存: {report_path}")
        return report


def main():
    """主函数"""
    logger.info("🚀 开始检查平台知识图谱状态")
    logger.info("=" * 60)

    checker = KnowledgeGraphChecker()

    # 1. 检查JanusGraph状态
    janusgraph_status = checker.check_janusgraph_status()

    # 2. 扫描知识图谱数据源
    knowledge_graphs = checker.scan_knowledge_graph_sources()

    # 3. 生成报告
    report = checker.generate_report()

    # 4. 输出汇总
    logger.info("\n" + "=" * 60)
    logger.info("📊 检查结果汇总:")
    logger.info(f"  JanusGraph服务: {'✅ 正常' if janusgraph_status.get('gremlin_port') else '❌ 未运行'}")

    total_sources = sum(len(sources) for source_type, sources in knowledge_graphs.items()
                        if isinstance(sources, dict))
    logger.info(f"  知识图谱源: {total_sources} 个")

    # 分类统计
    for source_type, sources in knowledge_graphs.items():
        if isinstance(sources, dict) and sources:
            logger.info(f"    - {source_type}: {len(sources)} 个")


if __name__ == "__main__":
    main()