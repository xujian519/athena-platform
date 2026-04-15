#!/usr/bin/env python3
"""
处理100个专利文档测试脚本
Process 100 Patent Documents Test Script

处理前100个专利文档并构建知识图谱
Process first 100 patent documents and build knowledge graph

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('patent_100_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_status(message, status='INFO'):
    """打印状态信息"""
    icons = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'PROGRESS': '🔄'
    }
    logger.info(f"{icons.get(status, 'ℹ️')} {message}")

def find_sample_documents(source_dir, limit=100):
    """找到要处理的文档样本"""
    logger.info(f"📂 在 {source_dir} 中查找前{limit}个文档...")

    source_path = Path(source_dir)
    if not source_path.exists():
        print_status(f"源目录不存在: {source_dir}', 'ERROR")
        return []

    # 查找Word文档
    doc_files = list(source_path.rglob('*.doc*'))

    # 限制数量
    sample_files = doc_files[:limit]

    print_status(f"找到 {len(sample_files)} 个文档进行处理', 'SUCCESS")

    # 显示文档类型分布
    doc_types = {}
    for doc_file in sample_files:
        suffix = doc_file.suffix.lower()
        doc_types[suffix] = doc_types.get(suffix, 0) + 1

    logger.info('📄 文档类型分布:')
    for suffix, count in sorted(doc_types.items()):
        logger.info(f"   {suffix}: {count}个")

    return sample_files

def create_simple_extractor():
    """创建简化的知识抽取器"""
    import re

    class SimplePatentExtractor:
        """简化的专利知识抽取器"""

        def __init__(self):
            # 定义识别模式
            self.patterns = {
                'legal_article': r'第([一二三四五六七八九十百千万\d]+)条[，。]?(?:第([一二三四五六七八九十百千万\d]+)款[，。]?)?',
                'case_number': r'([A-Z]{1,4})(\d{4,8})[号]',
                'patent_number': r'([A-Z]{1,2})(\d{9,12})([.A-Z]?\d)',
                'date': r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})[日]?',
                'amount': r'([一二三四五六七八九十百千万\d]+)万?[元元]',
                'law_names': ['专利法', '专利法实施细则', '专利审查指南', '最高人民法院', '知识产权法']
            }

        def extract_from_text(self, text, file_path):
            """从文本中抽取实体和关系"""
            entities = []
            relations = []

            # 抽取法条
            articles = re.findall(self.patterns['legal_article'], text)
            for i, (article, clause) in enumerate(articles):
                entity = {
                    'id': f"article_{file_path.stem}_{i}",
                    'type': 'legal_article',
                    'name': f"第{article}条" + (f"第{clause}款" if clause else ""),
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
                entity = {
                    'id': f"patent_{file_path.stem}_{i}",
                    'type': 'patent',
                    'name': f"{prefix}{number}{suffix}",
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

            # 抽取日期
            dates = re.findall(self.patterns['date'], text)
            for i, (year, month, day) in enumerate(dates):
                entity = {
                    'id': f"date_{file_path.stem}_{i}",
                    'type': 'date',
                    'name': f"{year}-{month.zfill(2)}-{day.zfill(2)}",
                    'source': str(file_path)
                }
                entities.append(entity)

            # 简单关系推断
            for entity in entities:
                if entity['type'] == 'case' and any(e['type'] == 'legal_article' for e in entities):
                    relations.append({
                        'source': entity['id'],
                        'target': next(e['id'] for e in entities if e['type'] == 'legal_article'),
                        'type': 'INTERPRETS',
                        'source_file': str(file_path)
                    })

            return {'entities': entities, 'relations': relations}

    return SimplePatentExtractor()

def process_document(doc_file, extractor):
    """处理单个文档"""
    try:
        print_status(f"处理文档: {doc_file.name}', 'PROGRESS")

        # 读取文档内容
        if doc_file.suffix.lower() in ['.doc', '.docx']:
            try:
                # 尝试使用python-docx
                from docx import Document
                doc = Document(doc_file)
                text = '\n'.join([para.text for para in doc.paragraphs])
            except Exception:
                # 如果失败，尝试读取为文本
                with open(doc_file, 'rb') as f:
                    text = f.read().decode('utf-8', errors='ignore')
        else:
            with open(doc_file, encoding='utf-8') as f:
                text = f.read()

        # 抽取知识
        result = extractor.extract_from_text(text, doc_file)

        print_status(f"抽取实体: {len(result['entities'])}个, 关系: {len(result['relations'])}个', 'SUCCESS")

        return result

    except Exception as e:
        print_status(f"处理文档失败 {doc_file.name}: {str(e)}', 'ERROR")
        return {'entities': [], 'relations': []}

def save_results_to_json(results, output_file):
    """保存结果到JSON文件"""
    try:
        # 合并所有实体和关系
        all_entities = []
        all_relations = []

        for doc_result in results:
            all_entities.extend(doc_result['entities'])
            all_relations.extend(doc_result['relations'])

        # 去重（基于ID）
        unique_entities = {e['id']: e for e in all_entities}.values()
        unique_relations = {f"{r['source']}-{r['type']}-{r['target']}": r for r in all_relations}.values()

        # 保存到文件
        output_data = {
            'metadata': {
                'processed_documents': len(results),
                'total_entities': len(unique_entities),
                'total_relations': len(unique_relations),
                'processing_time': datetime.now().isoformat()
            },
            'entities': list(unique_entities),
            'relations': list(unique_relations)
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print_status(f"结果已保存到: {output_file}', 'SUCCESS")
        return True

    except Exception as e:
        print_status(f"保存结果失败: {str(e)}', 'ERROR")
        return False

def import_to_neo4j(entities, relations):
    """导入到Neo4j数据库"""
    try:
        from neo4j import GraphDatabase

        # 连接数据库
        uri = 'bolt://localhost:7687'
        username = 'neo4j'
        password = 'password'

        driver = GraphDatabase.driver(uri, auth=(username, password))
        session = driver.session()

        print_status('开始导入数据到Neo4j...', 'PROGRESS')

        # 创建实体
        entity_count = 0
        for entity in entities:
            try:
                cypher = f"""
                CREATE (n:{entity['type'].title()}
                {{id: $id, name: $name, source: $source}})
                """
                session.run(cypher, {
                    'id': entity['id'],
                    'name': entity['name'],
                    'source': entity.get('source', '')
                })
                entity_count += 1
            except Exception as e:
                logger.warning(f"创建实体失败 {entity['id']}: {e}")

        print_status(f"创建实体: {entity_count}个', 'SUCCESS")

        # 创建关系
        relation_count = 0
        for relation in relations:
            try:
                cypher = """
                MATCH (a), (b)
                WHERE a.id = $source AND b.id = $target
                CREATE (a)-[r:{}]->(b)
                """.format(relation['type'])

                session.run(cypher, {
                    'source': relation['source'],
                    'target': relation['target']
                })
                relation_count += 1
            except Exception as e:
                logger.warning(f"创建关系失败 {relation['source']}-{relation['type']}-{relation['target']}: {e}")

        print_status(f"创建关系: {relation_count}个', 'SUCCESS")

        # 验证导入结果
        node_count = session.run('MATCH (n) RETURN count(n) as count').single()['count']
        rel_count = session.run('MATCH ()-[r]->() RETURN count(r) as count').single()['count']

        session.close()
        driver.close()

        print_status(f"Neo4j数据库统计: 节点{node_count}个, 关系{rel_count}个', 'SUCCESS")
        return True

    except Exception as e:
        print_status(f"导入Neo4j失败: {str(e)}', 'ERROR")
        return False

def generate_processing_report(results, output_dir):
    """生成处理报告"""
    try:
        # 统计信息
        total_docs = len(results)
        total_entities = sum(len(r['entities']) for r in results)
        total_relations = sum(len(r['relations']) for r in results)

        # 实体类型统计
        entity_types = {}
        for result in results:
            for entity in result['entities']:
                entity_types[entity['type']] = entity_types.get(entity['type'], 0) + 1

        # 关系类型统计
        relation_types = {}
        for result in results:
            for relation in result['relations']:
                relation_types[relation['type']] = relation_types.get(relation['type'], 0) + 1

        report = {
            'processing_summary': {
                'processed_documents': total_docs,
                'total_entities_extracted': total_entities,
                'total_relations_extracted': total_relations,
                'average_entities_per_doc': total_entities / total_docs if total_docs > 0 else 0,
                'average_relations_per_doc': total_relations / total_docs if total_docs > 0 else 0
            },
            'entity_type_distribution': entity_types,
            'relation_type_distribution': relation_types,
            'processing_details': [
                {
                    'document': result.get('document_name', 'unknown'),
                    'entities_count': len(result['entities']),
                    'relations_count': len(result['relations'])
                }
                for result in results[:10]  # 只显示前10个
            ]
        }

        # 保存报告
        report_file = Path(output_dir) / 'processing_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        logger.info("\n📊 处理报告摘要:")
        logger.info(f"   处理文档数: {total_docs}")
        logger.info(f"   抽取实体数: {total_entities}")
        logger.info(f"   抽取关系数: {total_relations}")
        logger.info(f"   平均实体/文档: {total_entities / total_docs:.1f}")
        logger.info(f"   平均关系/文档: {total_relations / total_docs:.1f}")

        logger.info("\n🏷️ 实体类型分布:")
        for entity_type, count in sorted(entity_types.items()):
            logger.info(f"   {entity_type}: {count}个")

        logger.info("\n🔗 关系类型分布:")
        for relation_type, count in sorted(relation_types.items()):
            logger.info(f"   {relation_type}: {count}个")

        logger.info(f"\n📄 详细报告已保存到: {report_file}")
        return True

    except Exception as e:
        print_status(f"生成报告失败: {str(e)}', 'ERROR")
        return False

def main():
    """主函数"""
    logger.info('🏛️ 处理100个专利文档测试')
    logger.info(str('='*60))
    logger.info('📝 目标: 处理前100个专利文档并构建知识图谱')
    logger.info(str('='*60))

    start_time = time.time()

    # 配置参数
    source_dir = '/Users/xujian/学习资料/专利'
    output_dir = '/tmp/patent_100_output'
    limit = 100

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        # 1. 查找文档
        sample_docs = find_sample_documents(source_dir, limit)
        if not sample_docs:
            print_status('没有找到要处理的文档', 'ERROR')
            return 1

        # 2. 创建抽取器
        extractor = create_simple_extractor()
        print_status('知识抽取器创建完成', 'SUCCESS')

        # 3. 处理文档
        logger.info(f"\n🔄 开始处理 {len(sample_docs)} 个文档...")
        results = []

        for i, doc_file in enumerate(sample_docs, 1):
            logger.info(f"\n进度: {i}/{len(sample_docs)}")

            result = process_document(doc_file, extractor)
            result['document_name'] = doc_file.name
            results.append(result)

            # 简单的进度显示
            if i % 10 == 0:
                print_status(f"已处理 {i}/{len(sample_docs)} 个文档', 'PROGRESS")

        # 4. 保存结果
        output_file = Path(output_dir) / 'extraction_results.json'
        if save_results_to_json(results, output_file):
            print_status('抽取结果保存完成', 'SUCCESS')

        # 5. 生成报告
        if generate_processing_report(results, output_dir):
            print_status('处理报告生成完成', 'SUCCESS')

        # 6. 导入到Neo4j
        logger.info("\n🗄️ 导入数据到Neo4j...")
        all_entities = []
        all_relations = []
        for result in results:
            all_entities.extend(result['entities'])
            all_relations.extend(result['relations'])

        # 去重
        unique_entities = {e['id']: e for e in all_entities}.values()
        unique_relations = {f"{r['source']}-{r['type']}-{r['target']}": r for r in all_relations}.values()

        logger.info(f"去重后: 实体{len(unique_entities)}个, 关系{len(unique_relations)}个")

        if import_to_neo4j(list(unique_entities), list(unique_relations)):
            print_status('Neo4j导入完成', 'SUCCESS')

        # 7. 总结
        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"\n{'='*60}")
        logger.info('🎉 100个专利文档处理完成！')
        logger.info(str('='*60))
        logger.info(f"⏱️ 处理耗时: {duration:.2f}秒")
        logger.info(f"📊 处理文档: {len(sample_docs)}个")
        logger.info(f"🏷️ 抽取实体: {len(unique_entities)}个")
        logger.info(f"🔗 抽取关系: {len(unique_relations)}个")
        logger.info(f"📁 输出目录: {output_dir}")
        logger.info("🗄️ Neo4j Web界面: http://localhost:7474")

        logger.info("\n💡 下一步建议:")
        logger.info("   1. 访问Neo4j Web界面查看知识图谱")
        logger.info("   2. 运行复杂查询测试")
        logger.info("   3. 开始处理全部57,218个文档")

        return 0

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
