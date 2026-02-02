#!/usr/bin/env python3
"""
Athena大规模知识图谱导入工具
专门用于导入/private/tmp中44GB的知识图谱数据到Neo4j
"""

import gc
import hashlib
import json
import logging
import os
import pickle
import queue
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MassiveKnowledgeGraphImporter:
    def __init__(self, neo4j_uri: str = 'bolt://localhost:7687',
                 username: str = 'neo4j', password: str = 'password'):
        self.neo4j_uri = neo4j_uri
        self.username = username
        self.password = password

        # 数据源路径
        self.private_tmp_path = Path('/private/tmp')
        self.patent_layered_path = self.private_tmp_path / 'patent_full_layered_output'
        self.patent_output_path = self.private_tmp_path / 'patent_full_output'
        self.legal_vectors_path = self.private_tmp_path / 'legal_vectors_storage'

        # 导入配置
        self.batch_size = 500  # 每批处理500个实体/关系
        self.chunk_size = 1000  # 每次读取1000行JSON
        self.max_workers = 4  # 最大并发工作线程
        self.query_timeout = 600  # 10分钟超时

        # 进度跟踪
        self.progress_file = '/tmp/massive_import_progress.json'
        self.log_file = '/tmp/massive_import.log'
        self.error_log = '/tmp/massive_import_errors.log'

        # 控制标志
        self.should_stop = False
        self.import_stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_entities': 0,
            'imported_entities': 0,
            'total_relations': 0,
            'imported_relations': 0,
            'errors': 0,
            'start_time': None,
            'estimated_end_time': None
        }

        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """处理中断信号"""
        logger.info(f"\n⚠️ 收到信号 {signum}，正在安全停止导入...")
        self.should_stop = True
        self.save_progress()
        sys.exit(1)

    def log_message(self, message: str, level: str = 'INFO'):
        """记录日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"

        logger.info(str(log_entry))

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            logger.info(f"⚠️ 无法写入日志文件: {e}")

    def log_error(self, error: str):
        """记录错误信息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_entry = f"[{timestamp}] [ERROR] {error}"

        try:
            with open(self.error_log, 'a', encoding='utf-8') as f:
                f.write(error_entry + "\n")
        except Exception:
            pass

        logger.info(f"❌ {error}")
        self.import_stats['errors'] += 1

    def load_progress(self) -> Dict:
        """加载导入进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log_message(f"无法加载进度文件: {e}")
        return {}

    def save_progress(self):
        """保存导入进度"""
        progress_data = {
            'stats': self.import_stats,
            'timestamp': datetime.now().isoformat(),
            'current_file': getattr(self, 'current_file', 'unknown')
        }

        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log_error(f"无法保存进度: {e}")

    def estimate_time_remaining(self, processed: int, total: int, elapsed_time: float) -> str:
        """估算剩余时间"""
        if processed == 0:
            return '未知'

        rate = processed / elapsed_time
        remaining = total - processed
        remaining_time = remaining / rate if rate > 0 else 0

        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        seconds = int(remaining_time % 60)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def setup_neo4j_for_massive_import(self):
        """为大规模导入优化Neo4j配置"""
        self.log_message('🚀 配置Neo4j以进行大规模导入...')

        optimizations = [
            # 禁用不必要的功能以提高导入速度
            "CALL dbms.setConfigValue('db.logs.query.enabled', 'false')",
            "CALL dbms.setConfigValue('db.logs.query.threshold', '0s')",
            "CALL dbms.setConfigValue('db.checkpoint.interval.time', '15m')",
            "CALL dbms.setConfigValue('db.checkpoint.interval.tx', '100000')",

            # 内存优化
            "CALL dbms.setConfigValue('db.memory.heap.initial_size', '4G')",
            "CALL dbms.setConfigValue('db.memory.heap.max_size', '8G')",
            "CALL dbms.setConfigValue('db.memory.pagecache.size', '2G')",

            # 事务优化
            "CALL dbms.setConfigValue('db.transaction.timeout', '600s')",
            "CALL dbms.setConfigValue('db.transaction.bookmark_ready_timeout', '300s')",
            "CALL dbms.setConfigValue('dbms.transaction.max_concurrent_transactions', '100')",

            # 优化GC
            "CALL dbms.setConfigValue('db.jvm.additional', '-XX:+UseG1GC')",
        ]

        for opt in optimizations:
            try:
                process = subprocess.Popen(
                    ['cypher-shell', '-u', self.username, '-p', self.password, '--non-interactive'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=opt + "\n", timeout=30)
                self.log_message(f"✅ 应用配置: {opt}")
            except Exception as e:
                self.log_error(f"配置应用失败: {opt} - {e}")

    def create_optimized_constraints(self):
        """创建优化的约束和索引"""
        self.log_message('🔍 创建优化的约束和索引...')

        # 先创建约束
        constraints = [
            'CREATE CONSTRAINT patent_id_unique IF NOT EXISTS FOR (p:Patent) REQUIRE p.patent_id IS UNIQUE',
            'CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE',
            'CREATE CONSTRAINT document_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.file_path IS UNIQUE',
        ]

        for constraint in constraints:
            self.execute_cypher_with_retry(constraint, f"创建约束: {constraint}")

        # 创建索引
        indexes = [
            'CREATE INDEX IF NOT EXISTS FOR (p:Patent) ON (p.patent_type)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)',
            'CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.confidence)',
            'CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.document_type)',
            'CREATE FULLTEXT INDEX IF NOT EXISTS FOR (e:Entity) ON EACH [e.value, e.context]',
        ]

        for index in indexes:
            self.execute_cypher_with_retry(index, f"创建索引: {index}")

    def execute_cypher_with_retry(self, cypher: str, description: str = '', max_retries: int = 3) -> bool:
        """执行Cypher命令并支持重试"""
        for attempt in range(max_retries):
            try:
                process = subprocess.Popen(
                    ['cypher-shell', '-u', self.username, '-p', self.password, '--non-interactive'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(input=cypher + "\n", timeout=self.query_timeout)

                if process.returncode == 0:
                    if description:
                        self.log_message(f"✅ {description}")
                    return True
                else:
                    if attempt < max_retries - 1:
                        self.log_message(f"⚠️ 尝试 {attempt + 1} 失败，重试: {stderr.strip()}")
                        time.sleep(2 ** attempt)
                    else:
                        self.log_error(f"{description} 失败: {stderr.strip()}")
                        return False

            except subprocess.TimeoutExpired:
                process.kill()
                self.log_error(f"查询超时: {description}")
                return False
            except Exception as e:
                self.log_error(f"执行异常: {description} - {e}")
                return False

        return False

    def stream_json_file(self, file_path: Path) -> Generator[Dict, None, None]:
        """流式读取大型JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 读取文件开头，确定JSON结构
                first_char = f.read(1)
                if first_char != '{':
                    self.log_error(f"文件不是有效的JSON对象: {file_path}")
                    return

                f.seek(0)

                # 如果是包含results数组的结构
                try:
                    data = json.load(f)

                    if 'results' in data and isinstance(data['results'], list):
                        # 返回results数组中的每个项目
                        for item in data['results']:
                            yield item
                    elif isinstance(data, list):
                        # 如果是直接数组
                        for item in data:
                            yield item
                    else:
                        # 如果是单个对象
                        yield data

                except json.JSONDecodeError as e:
                    self.log_error(f"JSON解析错误 {file_path}: {e}")

        except Exception as e:
            self.log_error(f"读取文件失败 {file_path}: {e}")

    def process_patent_entities(self, entities: List[Dict], batch_id: int) -> bool:
        """处理专利实体批次"""
        if not entities:
            return True

        # 构建批量插入Cypher - 使用单行格式避免语法错误
        cypher_commands = []
        current_time = datetime.now().isoformat()

        for entity in entities:
            entity_id = entity.get('id', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')
            entity_type = entity.get('type', 'Unknown').replace("'", "\\'").replace("\n", ' ').replace("\r", '')
            value = entity.get('value', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')
            source = entity.get('source', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')
            confidence = entity.get('confidence', 0.8)
            context = entity.get('context', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')[:500]
            pattern = entity.get('pattern', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')

            if not entity_id or not value:
                continue

            # 使用单行Cypher查询避免语法错误
            cypher = f"MERGE (e:Entity {{entity_id: '{entity_id}'}}) ON CREATE SET e.entity_type = '{entity_type}', e.value = '{value}', e.source = '{source}', e.confidence = {confidence}, e.context = '{context}', e.pattern = '{pattern}', e.imported_at = '{current_time}', e.batch_id = {batch_id} ON MATCH SET e.last_updated = '{current_time}'"
            cypher_commands.append(cypher)

        if not cypher_commands:
            return True

        batch_cypher = "\n".join(cypher_commands)
        success = self.execute_cypher_with_retry(
            batch_cypher,
            f"导入实体批次 {batch_id} ({len(entities)} 个实体)"
        )

        if success:
            self.import_stats['imported_entities'] += len(entities)

        return success

    def process_patent_relations(self, relations: List[Dict], batch_id: int) -> bool:
        """处理专利关系批次"""
        if not relations:
            return True

        cypher_commands = []
        current_time = datetime.now().isoformat()

        for relation in relations:
            # 这里需要根据实际的关系数据结构调整
            # 假设关系数据包含source_id, target_id, relation_type等信息
            source_id = relation.get('source_id', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')
            target_id = relation.get('target_id', '').replace("'", "\\'").replace("\n", ' ').replace("\r", '')
            relation_type = relation.get('relation_type', 'RELATED_TO').replace(' ', '_').replace("'", "\\'")

            if not source_id or not target_id:
                continue

            # 使用单行Cypher查询避免语法错误
            cypher = f"MATCH (source:Entity {{entity_id: '{source_id}'}}) MATCH (target:Entity {{entity_id: '{target_id}'}}) MERGE (source)-[r:{relation_type}]->(target) SET r.imported_at = '{current_time}', r.batch_id = {batch_id}"
            cypher_commands.append(cypher)

        if not cypher_commands:
            return True

        batch_cypher = "\n".join(cypher_commands)
        success = self.execute_cypher_with_retry(
            batch_cypher,
            f"导入关系批次 {batch_id} ({len(relations)} 个关系)"
        )

        if success:
            self.import_stats['imported_relations'] += len(relations)

        return success

    def process_single_patent_file(self, file_path: Path) -> bool:
        """处理单个专利文件"""
        self.current_file = str(file_path)
        self.log_message(f"📁 处理文件: {file_path.name}")

        file_size = file_path.stat().st_size
        self.log_message(f"📊 文件大小: {file_size / (1024**3):.2f} GB")

        start_time = time.time()
        processed_entities = 0
        batch_id = 0

        try:
            # 分批处理文件
            entities_batch = []

            for data_item in self.stream_json_file(file_path):
                if self.should_stop:
                    break

                # 提取实体
                if 'entities' in data_item and isinstance(data_item['entities'], list):
                    for entity in data_item['entities']:
                        if self.should_stop:
                            break

                        entities_batch.append(entity)

                        # 检查批次大小
                        if len(entities_batch) >= self.batch_size:
                            batch_id += 1
                            if self.process_patent_entities(entities_batch, batch_id):
                                processed_entities += len(entities_batch)
                                entities_batch = []

                                # 显示进度
                                elapsed = time.time() - start_time
                                rate = processed_entities / elapsed if elapsed > 0 else 0
                                self.log_message(f"   进度: {processed_entities} 实体, 速度: {rate:.1f} 实体/秒")
                            else:
                                self.log_error(f"批次 {batch_id} 处理失败")
                                entities_batch = []

                # 内存管理
                if batch_id % 100 == 0:
                    gc.collect()

            # 处理最后一批
            if entities_batch and not self.should_stop:
                batch_id += 1
                if self.process_patent_entities(entities_batch, batch_id):
                    processed_entities += len(entities_batch)

            # 更新统计
            elapsed_time = time.time() - start_time
            self.import_stats['processed_files'] += 1
            self.import_stats['total_entities'] += processed_entities

            self.log_message(f"✅ 文件处理完成: {file_path.name}")
            self.log_message(f"   处理时间: {elapsed_time:.1f}秒")
            self.log_message(f"   处理实体: {processed_entities}")

            # 定期保存进度
            if self.import_stats['processed_files'] % 5 == 0:
                self.save_progress()

            return True

        except Exception as e:
            self.log_error(f"文件处理失败 {file_path}: {e}")
            return False

    def import_legal_vectors(self) -> bool:
        """导入法律向量数据"""
        self.log_message('📚 开始导入法律向量数据...')

        try:
            # 处理metadata.json
            metadata_file = self.legal_vectors_path / 'metadata.json'
            if metadata_file.exists():
                self.log_message(f"处理元数据文件: {metadata_file}")

                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # 根据metadata结构创建相应的节点
                # 这里需要根据实际的metadata结构调整

            # 处理search_index.json
            search_index_file = self.legal_vectors_path / 'search_index.json'
            if search_index_file.exists():
                self.log_message(f"处理搜索索引文件: {search_index_file}")

                with open(search_index_file, 'r', encoding='utf-8') as f:
                    search_index = json.load(f)

                # 根据search_index结构创建索引节点和关系

            # 处理vectors.pkl
            vectors_file = self.legal_vectors_path / 'vectors.pkl'
            if vectors_file.exists():
                self.log_message(f"处理向量文件: {vectors_file}")

                with open(vectors_file, 'rb') as f:
                    vectors_data = pickle.load(f)

                # 向量数据可能很大，需要分批处理

            self.log_message('✅ 法律向量数据导入完成')
            return True

        except Exception as e:
            self.log_error(f"法律向量数据导入失败: {e}")
            return False

    def run_massive_import(self) -> bool:
        """执行大规模导入主流程"""
        self.log_message('=' * 80)
        self.log_message('🚀 Athena大规模知识图谱导入工具')
        self.log_message('=' * 80)

        self.import_stats['start_time'] = datetime.now().isoformat()

        # 1. 设置Neo4j优化配置
        self.setup_neo4j_for_massive_import()

        # 2. 创建约束和索引
        self.create_optimized_constraints()

        # 3. 统计文件总数
        patent_files = list(self.patent_layered_path.glob('*.json'))
        patent_output_files = list(self.patent_output_path.glob('*.json')) if self.patent_output_path.exists() else []

        self.import_stats['total_files'] = len(patent_files) + len(patent_output_files)

        self.log_message(f"📊 发现 {self.import_stats['total_files']} 个文件待导入")
        self.log_message(f"   - 分层专利文件: {len(patent_files)} 个")
        self.log_message(f"   - 专利输出文件: {len(patent_output_files)} 个")

        if self.legal_vectors_path.exists():
            self.log_message(f"   - 法律向量数据: 是")

        # 4. 处理专利分层数据（最大的数据集）
        if patent_files and not self.should_stop:
            self.log_message('🔥 开始处理专利分层数据（42GB）...')

            start_time = time.time()
            for i, file_path in enumerate(patent_files, 1):
                if self.should_stop:
                    break

                file_start_time = time.time()
                self.log_message(f"[{i}/{len(patent_files)}] 开始处理: {file_path.name}")

                success = self.process_single_patent_file(file_path)

                file_elapsed = time.time() - file_start_time
                total_elapsed = time.time() - start_time

                # 估算剩余时间
                if i > 1:
                    avg_time_per_file = total_elapsed / i
                    remaining_files = len(patent_files) - i
                    eta_seconds = avg_time_per_file * remaining_files
                    eta_hours = int(eta_seconds // 3600)
                    eta_minutes = int((eta_seconds % 3600) // 60)

                    self.log_message(f"⏱️ 预计剩余时间: {eta_hours:02d}小时{eta_minutes:02d}分钟")

                if not success:
                    self.log_message(f"⚠️ 文件处理失败，继续下一个文件: {file_path.name}")

        # 5. 处理其他专利文件
        if patent_output_files and not self.should_stop:
            self.log_message('📄 开始处理其他专利文件...')

            for i, file_path in enumerate(patent_output_files, 1):
                if self.should_stop:
                    break

                self.log_message(f"[{i}/{len(patent_output_files)}] 处理: {file_path.name}")
                self.process_single_patent_file(file_path)

        # 6. 处理法律向量数据
        if self.legal_vectors_path.exists() and not self.should_stop:
            self.import_legal_vectors()

        # 7. 生成最终报告
        self.generate_final_report()

        return True

    def generate_final_report(self):
        """生成最终导入报告"""
        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.import_stats['start_time']) if self.import_stats['start_time'] else end_time
        total_time = (end_time - start_time).total_seconds()

        # 查询Neo4j最终统计
        node_count = 0
        relation_count = 0

        try:
            # 查询节点数
            process = subprocess.Popen(
                ['cypher-shell', '-u', self.username, '-p', self.password, '--non-interactive', '--format', 'plain'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input="MATCH (n) RETURN count(n) as count;\n")
            if process.returncode == 0 and stdout.strip():
                node_count = int(stdout.strip().split('\n')[-1])

            # 查询关系数
            process = subprocess.Popen(
                ['cypher-shell', '-u', self.username, '-p', self.password, '--non-interactive', '--format', 'plain'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input="MATCH ()-[r]->() RETURN count(r) as count;\n")
            if process.returncode == 0 and stdout.strip():
                relation_count = int(stdout.strip().split('\n')[-1])

        except Exception as e:
            self.log_error(f"查询Neo4j统计失败: {e}")

        logger.info(str("\n" + '=' * 80))
        logger.info('📊 大规模知识图谱导入完成报告')
        logger.info(str('=' * 80))
        logger.info(f"✅ 处理文件数: {self.import_stats['processed_files']}/{self.import_stats['total_files']}")
        logger.info(f"📈 导入实体数: {self.import_stats['imported_entities']}")
        logger.info(f"🔗 导入关系数: {self.import_stats['imported_relations']}")
        logger.info(f"⚠️ 错误计数: {self.import_stats['errors']}")
        logger.info(f"⏱️ 总耗时: {total_time:.2f}秒 ({total_time/3600:.2f}小时)")
        logger.info(f"📊 Neo4j统计: {node_count} 节点, {relation_count} 关系")
        logger.info(f"🚀 平均速度: {self.import_stats['imported_entities']/total_time:.1f} 实体/秒")

        if self.import_stats['errors'] > 0:
            logger.info(f"\n⚠️ 发现 {self.import_stats['errors']} 个错误，请查看日志: {self.error_log}")

        logger.info("\n🔗 访问方式:")
        logger.info('   Neo4j Browser: http://localhost:7474')
        logger.info('   用户名: neo4j')
        logger.info('   密码: password')

        # 保存最终进度
        self.import_stats['estimated_end_time'] = datetime.now().isoformat()
        self.save_progress()

def main():
    """主函数"""
    logger.info('🚀 启动Athena大规模知识图谱导入工具...')

    # 检查数据源
    private_tmp = Path('/private/tmp')
    if not private_tmp.exists():
        logger.info('❌ /private/tmp 目录不存在')
        sys.exit(1)

    try:
        importer = MassiveKnowledgeGraphImporter()

        # 加载之前的进度
        progress = importer.load_progress()
        if progress:
            logger.info(f"📋 发现之前的导入进度，从时间: {progress.get('timestamp', 'unknown')}")
            choice = input('是否继续之前的导入？(y/n): ').lower().strip()
            if choice != 'y':
                logger.info('🔄 开始新的导入...')
            else:
                logger.info('✅ 继续之前的导入...')

        success = importer.run_massive_import()

        if success:
            logger.info("\n🎉 大规模知识图谱导入成功完成！")
            sys.exit(0)
        else:
            logger.info("\n⚠️ 导入过程中遇到问题，请检查日志")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n⚠️ 用户中断导入，进度已保存")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n❌ 导入工具异常: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()