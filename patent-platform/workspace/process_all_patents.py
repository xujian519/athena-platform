#!/usr/bin/env python3
"""
处理全部专利文档脚本
Process All Patent Documents Script

处理全部57,218个专利文档并构建完整知识图谱
Process all 57,218 patent documents and build complete knowledge graph

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# 全局变量
processing_stats = {
    'total_files': 0,
    'processed_files': 0,
    'total_entities': 0,
    'total_relations': 0,
    'errors': 0,
    'start_time': None,
    'current_file': '',
    'eta': None
}

# 停止标志
stop_processing = threading.Event()

# 初始化logger
logger = logging.getLogger(__name__)

def print_status(message, status='INFO'):
    """打印状态信息"""
    icons = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'PROGRESS': '🔄',
        'MILESTONE': '🎯'
    }
    timestamp = datetime.now().strftime('%H:%M:%S')
    logger.info(f"[{timestamp}] {icons.get(status, 'ℹ️')} {message}")

def signal_handler(signum, frame):
    """信号处理器"""
    print_status('收到停止信号，正在安全退出...', 'WARNING')
    stop_processing.set()

def setup_logging():
    """设置日志"""
    log_file = f"patent_full_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class ProgressMonitor:
    """进度监控器"""

    def __init__(self, update_interval=5):
        self.update_interval = update_interval
        self.running = False
        self.thread = None

    def start_monitoring(self):
        """开始监控"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.daemon = True
        self.thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _monitor(self):
        """监控函数"""
        while self.running and not stop_processing.is_set():
            self._print_progress()
            time.sleep(self.update_interval)

    def _print_progress(self):
        """打印进度"""
        if processing_stats['total_files'] == 0:
            return

        progress = (processing_stats['processed_files'] / processing_stats['total_files']) * 100
        elapsed = time.time() - processing_stats['start_time']

        if processing_stats['processed_files'] > 0:
            avg_time = elapsed / processing_stats['processed_files']
            remaining_files = processing_stats['total_files'] - processing_stats['processed_files']
            eta_seconds = remaining_files * avg_time
            eta = str(timedelta(seconds=int(eta_seconds)))
            processing_stats['eta'] = eta
        else:
            eta = '计算中...'

        entities_per_file = processing_stats['total_entities'] / max(1, processing_stats['processed_files'])

        print_status(
            f"进度: {processing_stats['processed_files']:,}/{processing_stats['total_files']:,} "
            f"({progress:.1f}%) | "
            f"实体: {processing_stats['total_entities']:,} "
            f"({entities_per_file:.1f}/文件) | "
            f"错误: {processing_stats['errors']} | "
            f"ETA: {eta} | "
            f"当前: {Path(processing_stats['current_file']).name[:30]}...",
            'PROGRESS'
        )

def find_all_patent_documents(source_dir):
    """查找所有专利文档"""
    print_status('开始扫描所有专利文档...', 'INFO')

    source_path = Path(source_dir)
    if not source_path.exists():
        print_status(f"源目录不存在: {source_dir}', 'ERROR")
        return []

    # 查找所有Word文档
    doc_files = list(source_path.rglob('*.doc*'))

    print_status(f"找到 {len(doc_files):,} 个专利文档', 'SUCCESS")

    # 按类型统计
    doc_types = {}
    for doc_file in doc_files:
        suffix = doc_file.suffix.lower()
        doc_types[suffix] = doc_types.get(suffix, 0) + 1

    logger.info('📄 文档类型分布:')
    for suffix, count in sorted(doc_types.items()):
        logger.info(f"   {suffix}: {count:,}个")

    return doc_files

def create_enhanced_extractor():
    """创建增强的知识抽取器"""
    import re

    class EnhancedPatentExtractor:
        """增强的专利知识抽取器"""

        def __init__(self):
            # 更全面的识别模式
            self.patterns = {
                # 法条识别
                'legal_article': r'第([一二三四五六七八九十百千万零0-9]+)条[，。]?(?:第([一二三四五六七八九十百千万零0-9]+)款[，。]?)?(?:第([一二三四五六七八九十百千万零0-9]+)项[，。]?)?',

                # 案例编号
                'case_number': r'([A-Z]{1,4})(\d{4,8})[号]',

                # 专利号（更准确）
                'patent_number': r'(?:ZL\s*)?([A-Z]{1,2})(\d{8,12})([.A-Z]?\d{0,2})',

                # 申请号
                'application_number': r'([0-9]{13,22})',

                # 日期识别
                'date': r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})[日]?',

                # 金额
                'amount': r'([一二三四五六七八九十百千万零\d]+万?[元元千百拾])',

                # 法律名称
                'law_names': [
                    '专利法', '专利法实施细则', '专利审查指南', '专利条例',
                    '最高人民法院', '最高法院', '知识产权法', '商标法',
                    '著作权法', '反不正当竞争法', '技术合同法'
                ],

                # 技术领域
                'technical_fields': [
                    '电子技术', '通信技术', '计算机技术', '机械技术', '化工技术',
                    '生物技术', '医疗技术', '材料技术', '能源技术', '建筑技术'
                ],

                # 专利类型
                'patent_types': ['发明', '实用新型', '外观设计', '发明专利', '实用新型专利', '外观设计专利']
            }

        def extract_from_text(self, text, file_path):
            """从文本中抽取实体和关系"""
            entities = []
            relations = []

            try:
                # 抽取法条
                articles = re.findall(self.patterns['legal_article'], text)
                for i, (article, clause, item) in enumerate(articles):
                    name = f"第{article}条"
                    if clause:
                        name += f"第{clause}款"
                    if item:
                        name += f"第{item}项"

                    entity = {
                        'id': f"article_{file_path.stem}_{i}",
                        'type': 'legal_article',
                        'name': name,
                        'source': str(file_path)
                    }
                    entities.append(entity)

                # 抽取案例编号
                cases = re.findall(self.patterns['case_number'], text)
                for i, (prefix, number) in enumerate(cases):
                    entity = {
                        'id': f"case_{file_path.stem}_{i}",
                        'type': 'case',
                        'name': f"{prefix}{number}号",
                        'source': str(file_path)
                    }
                    entities.append(entity)

                # 抽取专利号
                patents = re.findall(self.patterns['patent_number'], text)
                for i, (prefix, number, suffix) in enumerate(patents):
                    patent_num = f"{prefix}{number}{suffix}"
                    entity = {
                        'id': f"patent_{file_path.stem}_{i}",
                        'type': 'patent',
                        'name': patent_num,
                        'source': str(file_path)
                    }
                    entities.append(entity)

                # 抽取申请号
                applications = re.findall(self.patterns['application_number'], text)
                for i, app_num in enumerate(applications):
                    if len(app_num) >= 13:  # 确保是有效的申请号
                        entity = {
                            'id': f"app_{file_path.stem}_{i}",
                            'type': 'application',
                            'name': app_num,
                            'source': str(file_path)
                        }
                        entities.append(entity)

                # 抽取日期
                dates = re.findall(self.patterns['date'], text)
                for i, (year, month, day) in enumerate(dates):
                    # 验证日期合理性
                    year = int(year)
                    month = int(month)
                    day = int(day)
                    if 1900 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                        entity = {
                            'id': f"date_{file_path.stem}_{i}",
                            'type': 'date',
                            'name': f"{year}-{month:02d}-{day:02d}",
                            'source': str(file_path)
                        }
                        entities.append(entity)

                # 抽取法律名称
                for law_name in self.patterns['law_names']:
                    if law_name in text:
                        entity = {
                            'id': f"law_{file_path.stem}_{law_name}",
                            'type': 'law',
                            'name': law_name,
                            'source': str(file_path)
                        }
                        entities.append(entity)

                # 抽取技术领域
                for tech_field in self.patterns['technical_fields']:
                    if tech_field in text:
                        entity = {
                            'id': f"tech_{file_path.stem}_{tech_field}",
                            'type': 'technical_field',
                            'name': tech_field,
                            'source': str(file_path)
                        }
                        entities.append(entity)

                # 抽取专利类型
                for patent_type in self.patterns['patent_types']:
                    if patent_type in text:
                        entity = {
                            'id': f"ptype_{file_path.stem}_{patent_type}",
                            'type': 'patent_type',
                            'name': patent_type,
                            'source': str(file_path)
                        }
                        entities.append(entity)

                # 简单关系推断
                case_entities = [e for e in entities if e['type'] == 'case']
                article_entities = [e for e in entities if e['type'] == 'legal_article']
                patent_entities = [e for e in entities if e['type'] == 'patent']

                # 案例解释法条
                for case in case_entities:
                    for article in article_entities:
                        relations.append({
                            'source': case['id'],
                            'target': article['id'],
                            'type': 'INTERPRETS',
                            'source_file': str(file_path)
                        })

                # 专利引用法条
                for patent in patent_entities:
                    for article in article_entities:
                        relations.append({
                            'source': patent['id'],
                            'target': article['id'],
                            'type': 'REFERENCES',
                            'source_file': str(file_path)
                        })

            except Exception as e:
                logger.error(f"抽取错误 {file_path}: {e}")

            return {'entities': entities, 'relations': relations}

    return EnhancedPatentExtractor()

def process_document_batch(doc_files, extractor, batch_size=50):
    """批量处理文档"""
    results = []

    for doc_file in doc_files:
        if stop_processing.is_set():
            break

        try:
            processing_stats['current_file'] = str(doc_file)

            # 读取文档内容
            if doc_file.suffix.lower() in ['.doc', '.docx']:
                try:
                    from docx import Document
                    doc = Document(doc_file)
                    text = '\n'.join([para.text for para in doc.paragraphs])
                except Exception:
                    # 回退到二进制读取
                    with open(doc_file, 'rb') as f:
                        text = f.read().decode('utf-8', errors='ignore')
            else:
                with open(doc_file, encoding='utf-8') as f:
                    text = f.read()

            # 抽取知识
            result = extractor.extract_from_text(text, doc_file)
            result['document_name'] = doc_file.name
            results.append(result)

            # 更新统计
            processing_stats['processed_files'] += 1
            processing_stats['total_entities'] += len(result['entities'])
            processing_stats['total_relations'] += len(result['relations'])

        except Exception as e:
            logger.error(f"处理文档失败 {doc_file}: {e}")
            processing_stats['errors'] += 1

    return results

def process_all_documents_parallel(doc_files, num_threads=4, batch_size=50):
    """并行处理所有文档"""
    print_status(f"开始并行处理 {len(doc_files):,} 个文档...', 'MILESTONE")

    extractor = create_enhanced_extractor()
    all_results = []

    # 分批处理
    for i in range(0, len(doc_files), batch_size):
        if stop_processing.is_set():
            break

        batch = doc_files[i:i + batch_size]

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # 将批次进一步分割给线程处理
            sub_batch_size = max(1, len(batch) // num_threads)
            futures = []

            for j in range(0, len(batch), sub_batch_size):
                sub_batch = batch[j:j + sub_batch_size]
                future = executor.submit(process_document_batch, sub_batch, extractor)
                futures.append(future)

            # 收集结果
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                except Exception as e:
                    logger.error(f"批处理错误: {e}")

        # 每完成一个大批次，检查内存使用
        if i % (batch_size * 10) == 0:
            print_status(f"已完成 {min(i + batch_size, len(doc_files)):,}/{len(doc_files):,} 个文档', 'PROGRESS")

    return all_results

def save_large_dataset(results, output_dir):
    """保存大数据集"""
    print_status('保存处理结果...', 'INFO')

    # 分离实体和关系
    all_entities = []
    all_relations = []

    for doc_result in results:
        all_entities.extend(doc_result.get('entities', []))
        all_relations.extend(doc_result.get('relations', []))

    print_status(f"原始数据: 实体{len(all_entities):,}个, 关系{len(all_relations):,}个', 'INFO")

    # 去重
    print_status('开始数据去重...', 'PROGRESS')

    # 实体去重
    unique_entities = {}
    for entity in all_entities:
        # 使用名称+类型作为去重键
        dedupe_key = f"{entity['type']}_{entity['name']}"
        if dedupe_key not in unique_entities:
            unique_entities[dedupe_key] = entity
        else:
            # 保留源信息
            if 'source' in entity:
                if 'sources' not in unique_entities[dedupe_key]:
                    unique_entities[dedupe_key]['sources'] = [unique_entities[dedupe_key]['source']]
                if entity['source'] not in unique_entities[dedupe_key]['sources']:
                    unique_entities[dedupe_key]['sources'].append(entity['source'])

    # 关系去重
    unique_relations = {}
    for relation in all_relations:
        rel_key = f"{relation['source']}_{relation['type']}_{relation['target']}"
        if rel_key not in unique_relations:
            unique_relations[rel_key] = relation

    unique_entities_list = list(unique_entities.values())
    unique_relations_list = list(unique_relations.values())

    print_status(f"去重后: 实体{len(unique_entities_list):,}个, 关系{len(unique_relations_list):,}个', 'SUCCESS")

    # 分文件保存（避免单文件过大）
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存元数据
    metadata = {
        'processing_summary': {
            'total_documents': len(results),
            'total_entities_raw': len(all_entities),
            'total_relations_raw': len(all_relations),
            'unique_entities': len(unique_entities_list),
            'unique_relations': len(unique_relations_list),
            'processing_time': str(timedelta(seconds=time.time() - float(processing_stats['start_time']))),
            'errors': processing_stats['errors'],
            'processing_timestamp': timestamp
        },
        'entity_type_distribution': {},
        'relation_type_distribution': {}
    }

    # 统计实体类型分布
    entity_type_counts = {}
    for entity in unique_entities_list:
        entity_type = entity['type']
        entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1
    metadata['entity_type_distribution'] = entity_type_counts

    # 统计关系类型分布
    relation_type_counts = {}
    for relation in unique_relations_list:
        relation_type = relation['type']
        relation_type_counts[relation_type] = relation_type_counts.get(relation_type, 0) + 1
    metadata['relation_type_distribution'] = relation_type_counts

    # 保存元数据
    metadata_file = output_path / f'processing_metadata_{timestamp}.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

    # 分批保存实体（每批10000个）
    entity_batch_size = 10000
    for i in range(0, len(unique_entities_list), entity_batch_size):
        batch_entities = unique_entities_list[i:i + entity_batch_size]
        entity_file = output_path / f'entities_batch_{i//entity_batch_size}_{timestamp}.json'

        with open(entity_file, 'w', encoding='utf-8') as f:
            json.dump(batch_entities, f, ensure_ascii=False, indent=2)

    # 分批保存关系
    relation_batch_size = 10000
    for i in range(0, len(unique_relations_list), relation_batch_size):
        batch_relations = unique_relations_list[i:i + relation_batch_size]
        relation_file = output_path / f'relations_batch_{i//relation_batch_size}_{timestamp}.json'

        with open(relation_file, 'w', encoding='utf-8') as f:
            json.dump(batch_relations, f, ensure_ascii=False, indent=2)

    print_status(f"数据已保存到: {output_path}', 'SUCCESS")
    return unique_entities_list, unique_relations_list

def import_to_neo4j_batch(entities, relations, batch_size=1000):
    """批量导入到Neo4j"""
    print_status(f"开始导入{len(entities):,}个实体和{len(relations):,}个关系到Neo4j...', 'MILESTONE")

    try:
        from neo4j import GraphDatabase

        # 连接数据库
        uri = 'bolt://localhost:7687'
        username = 'neo4j'
        password = 'password'

        driver = GraphDatabase.driver(uri, auth=(username, password))
        session = driver.session()

        # 创建约束（如果不存在）
        print_status('创建数据库约束...', 'PROGRESS')
        try:
            session.run('CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE')
            session.run('CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)')
        except Exception as e:
            logger.warning(f"创建约束失败: {e}")

        # 分批导入实体
        print_status('批量导入实体...', 'PROGRESS')
        entity_count = 0

        for i in range(0, len(entities), batch_size):
            if stop_processing.is_set():
                break

            batch = entities[i:i + batch_size]

            for entity in batch:
                try:
                    # 动态创建节点类型
                    label = entity['type'].title()
                    cypher = f"""
                    CREATE (n:{label} {{
                        id: $id,
                        name: $name,
                        type: $type,
                        source: $source
                    }})
                    """

                    params = {
                        'id': entity['id'],
                        'name': entity['name'],
                        'type': entity['type'],
                        'source': entity.get('source', '')
                    }

                    session.run(cypher, params)
                    entity_count += 1

                except Exception as e:
                    # 忽略重复错误
                    if 'already exists' not in str(e):
                        logger.warning(f"创建实体失败 {entity['id']}: {e}")

            if i % (batch_size * 10) == 0:
                print_status(f"已导入实体: {entity_count:,}/{len(entities):,}', 'PROGRESS")

        print_status(f"实体导入完成: {entity_count:,}个', 'SUCCESS")

        # 分批导入关系
        print_status('批量导入关系...', 'PROGRESS')
        relation_count = 0

        for i in range(0, len(relations), batch_size):
            if stop_processing.is_set():
                break

            batch = relations[i:i + batch_size]

            for relation in batch:
                try:
                    cypher = f"""
                    MATCH (a), (b)
                    WHERE a.id = $source AND b.id = $target
                    CREATE (a)-[r:{relation['type']}]->(b)
                    SET r.source_file = $source_file
                    """

                    session.run(cypher, {
                        'source': relation['source'],
                        'target': relation['target'],
                        'source_file': relation.get('source_file', '')
                    })
                    relation_count += 1

                except Exception as e:
                    logger.warning(f"创建关系失败: {e}")

            if i % (batch_size * 10) == 0:
                print_status(f"已导入关系: {relation_count:,}/{len(relations):,}', 'PROGRESS")

        # 验证导入结果
        node_count = session.run('MATCH (n) RETURN count(n) as count').single()['count']
        rel_count = session.run('MATCH ()-[r]->() RETURN count(r) as count').single()['count']

        session.close()
        driver.close()

        print_status(f"Neo4j导入完成: 节点{node_count:,}个, 关系{rel_count:,}个', 'SUCCESS")
        return True

    except Exception as e:
        print_status(f"Neo4j导入失败: {str(e)}', 'ERROR")
        return False

def generate_final_report(output_dir, results):
    """生成最终报告"""
    print_status('生成最终处理报告...', 'INFO')

    try:
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 计算详细统计
        total_docs = len(results)
        total_entities = sum(len(r.get('entities', [])) for r in results)
        total_relations = sum(len(r.get('relations', [])) for r in results)

        # 实体类型分布
        entity_types = {}
        for result in results:
            for entity in result.get('entities', []):
                entity_type = entity['type']
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

        # 关系类型分布
        relation_types = {}
        for result in results:
            for relation in result.get('relations', []):
                relation_type = relation['type']
                relation_types[relation_type] = relation_types.get(relation_type, 0) + 1

        # 性能统计
        processing_time = time.time() - processing_stats['start_time']
        docs_per_second = total_docs / processing_time if processing_time > 0 else 0
        entities_per_second = total_entities / processing_time if processing_time > 0 else 0

        # 生成报告
        report = {
            'patent_knowledge_graph_final_report': {
                'processing_timestamp': datetime.now().isoformat(),
                'execution_summary': {
                    'total_documents_processed': total_docs,
                    'processing_duration_seconds': processing_time,
                    'processing_duration_formatted': str(timedelta(seconds=int(processing_time))),
                    'processing_speed_docs_per_second': docs_per_second,
                    'errors_encountered': processing_stats['errors']
                },
                'knowledge_extraction_results': {
                    'total_entities_extracted': total_entities,
                    'total_relations_extracted': total_relations,
                    'average_entities_per_document': total_entities / total_docs if total_docs > 0 else 0,
                    'average_relations_per_document': total_relations / total_docs if total_docs > 0 else 0,
                    'extraction_speed_entities_per_second': entities_per_second
                },
                'entity_type_distribution': dict(sorted(entity_types.items(), key=lambda x: x[1], reverse=True)),
                'relation_type_distribution': dict(sorted(relation_types.items(), key=lambda x: x[1], reverse=True)),
                'database_import_results': {
                    'neo4j_nodes_count': None,  # 将在导入后更新
                    'neo4j_relations_count': None  # 将在导入后更新
                },
                'quality_metrics': {
                    'documents_with_entities': sum(1 for r in results if r.get('entities')),
                    'documents_with_relations': sum(1 for r in results if r.get('relations')),
                    'empty_documents': sum(1 for r in results if not r.get('entities') and not r.get('relations'))
                }
            }
        }

        # 保存报告
        report_file = output_path / f'patent_knowledge_graph_final_report_{timestamp}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        # 打印摘要
        logger.info("\n🎉 专利知识图谱构建完成！")
        logger.info(str('='*80))
        logger.info("📊 处理统计:")
        logger.info(f"   处理文档: {total_docs:,}个")
        logger.info(f"   处理时间: {str(timedelta(seconds=int(processing_time)))}")
        logger.info(f"   处理速度: {docs_per_second:.1f}文档/秒")
        logger.info(f"   错误数量: {processing_stats['errors']}")

        logger.info("\n🏷️ 知识抽取:")
        logger.info(f"   抽取实体: {total_entities:,}个")
        logger.info(f"   抽取关系: {total_relations:,}个")
        logger.info(f"   实体密度: {total_entities/total_docs:.1f}实体/文档")

        logger.info("\n📈 实体类型分布:")
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"   {entity_type}: {count:,}个")

        logger.info("\n🔗 关系类型分布:")
        for relation_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {relation_type}: {count:,}个")

        logger.info("\n📁 输出文件:")
        logger.info(f"   主报告: {report_file}")
        logger.info(f"   输出目录: {output_path}")

        logger.info("\n🌐 Neo4j访问:")
        logger.info("   Web界面: http://localhost:7474")
        logger.info("   用户名: neo4j")
        logger.info("   密码: password")

        print_status(f"完整报告已保存到: {report_file}', 'SUCCESS")
        return report_file

    except Exception as e:
        print_status(f"生成报告失败: {str(e)}', 'ERROR")
        return None

def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info('🏛️ 处理全部57,218个专利文档')
    logger.info(str('='*80))
    logger.info('📝 目标: 构建完整的专利知识图谱')
    logger.info('⏰ 预计时间: 5-8小时')
    logger.info('💾 预期输出: 50万+实体，100万+关系')
    logger.info(str('='*80))

    # 配置参数
    source_dir = '/Users/xujian/学习资料/专利'
    output_dir = '/tmp/patent_full_output'
    num_threads = 4  # 根据CPU核心数调整
    batch_size = 100  # 每批处理的文档数

    # 初始化统计
    processing_stats['start_time'] = time.time()

    # 设置日志
    logger = setup_logging()

    try:
        # 1. 查找所有文档
        doc_files = find_all_patent_documents(source_dir)
        if not doc_files:
            print_status('没有找到要处理的文档', 'ERROR')
            return 1

        processing_stats['total_files'] = len(doc_files)

        # 2. 启动进度监控
        monitor = ProgressMonitor(update_interval=10)
        monitor.start_monitoring()

        # 3. 处理所有文档
        logger.info(f"\n🚀 开始处理 {len(doc_files):,} 个文档...")
        results = process_all_documents_parallel(doc_files, num_threads, batch_size)

        # 4. 停止监控
        monitor.stop_monitoring()

        if stop_processing.is_set():
            print_status('处理被用户中断', 'WARNING')

        # 5. 保存结果
        entities, relations = save_large_dataset(results, output_dir)

        # 6. 导入Neo4j
        if not stop_processing.is_set():
            success = import_to_neo4j_batch(entities, relations)
            if not success:
                print_status('Neo4j导入失败，但原始数据已保存', 'WARNING')

        # 7. 生成最终报告
        generate_final_report(output_dir, results)

        # 8. 完成
        logger.info(f"\n🎉 专利知识图谱构建{'完成' if not stop_processing.is_set() else '部分完成'}！")

        if stop_processing.is_set():
            logger.info('💡 您可以使用保存的数据继续处理')

        return 0 if not stop_processing.is_set() else 1

    except Exception as e:
        print_status(f"处理过程中发生异常: {str(e)}', 'ERROR")
        logger.exception('Processing failed')
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n👋 处理被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"❌ 程序异常: {str(e)}")
        sys.exit(1)
