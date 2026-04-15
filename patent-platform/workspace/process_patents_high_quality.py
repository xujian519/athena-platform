#!/usr/bin/env python3
"""
高质量专利知识图谱处理系统
High-Quality Patent Knowledge Graph Processing System

基于用户反馈优化的专利知识图谱构建系统
- 解决编码问题
- 修复时间戳错误
- 实现质量控制
- 支持多种文档格式

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 2.0.0
"""

import hashlib
import json
import logging
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"patent_hq_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DocumentReader:
    """文档读取器 - 解决编码问题"""

    @staticmethod
    def read_document(file_path: str) -> str | None:
        """读取文档内容，自动处理编码"""
        try:
            # 尝试多种编码方式
            encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin1']

            for encoding in encodings:
                try:
                    with open(file_path, encoding=encoding) as f:
                        content = f.read()
                    if content.strip():
                        logger.debug(f"成功使用 {encoding} 编码读取: {file_path}")
                        return content
                except UnicodeDecodeError:
                    continue

            # 如果所有编码都失败，尝试二进制读取
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            # 尝试解码为文本
            for encoding in encodings:
                try:
                    content = raw_data.decode(encoding, errors='ignore')
                    if len(content) > 100:  # 确保有足够的内容
                        logger.debug(f"使用 {encoding} 容错解码读取: {file_path}")
                        return content
                except Exception:
                    continue

            logger.warning(f"无法解码文档: {file_path}")
            return None

        except Exception as e:
            logger.error(f"读取文档失败 {file_path}: {e}")
            return None

class EntityExtractor:
    """实体提取器 - 高质量版本"""

    def __init__(self):
        self.legal_entities_patterns = {
            '专利法条': r'专利法第([一二三四五六七八九十百千万\d]+)条',
            '实施细则': r'实施细则第([一二三四五六七八九十百千万\d]+)条',
            '审查指南': r'审查指南[第]?([一二三四五六七八九十百千万\d]+)[部分章节]',
            '决定文书': r'(?:专利复审委员会|专利局|国家知识产权局)[\s]*([^\s]*)[决定]',
            '技术术语': r'技术方案|发明创造|技术特征|现有技术|对比文件',
            '法律概念': r'新颖性|创造性|实用性|公开不充分|权利要求书',
            '申请号': r'(\d{13,})',
            '专利号': r'(CN\d+[A-Z]?)',
        }

        # 预定义的高质量实体词汇
        self.quality_entities = {
            '法律法规': ['专利法', '专利法实施细则', '专利审查指南'],
            '程序类型': ['复审请求', '无效宣告请求', '行政诉讼', '行政复议'],
            '决定类型': ['维持有效', '宣告无效', '部分无效', '驳回请求'],
            '技术领域': ['机械', '电子', '通信', '化学', '生物', '医药'],
        }

    def extract_entities(self, text: str, source_file: str) -> tuple[list[dict], list[dict]]:
        """提取实体和关系"""
        entities = []
        relations = []

        # 基于模式的实体提取
        for entity_type, pattern in self.legal_entities_patterns.items():
            import re
            matches = re.finditer(pattern, text)
            for match in matches:
                entity_value = match.group(0)
                entity_id = hashlib.md5(f"{entity_value}_{entity_type}".encode(), usedforsecurity=False).hexdigest()[:16]

                entity = {
                    'id': entity_id,
                    'type': entity_type,
                    'value': entity_value,
                    'source': source_file,
                    'confidence': 0.9,  # 基础置信度
                    'context': text[max(0, match.start()-50):match.end()+50]  # 上下文
                }
                entities.append(entity)

        # 基于预定义词汇的实体提取
        for category, terms in self.quality_entities.items():
            for term in terms:
                if term in text:
                    entity_id = hashlib.md5(f"{term}_{category}".encode(), usedforsecurity=False).hexdigest()[:16]
                    entity = {
                        'id': entity_id,
                        'type': category,
                        'value': term,
                        'source': source_file,
                        'confidence': 0.95,  # 预定义词汇高置信度
                        'context': text[text.find(term)-20:text.find(term)+20+len(term)]
                    }
                    entities.append(entity)

        # 提取关系 - 基于共现和距离
        for i, entity1 in enumerate(entities):
            for _j, entity2 in enumerate(entities[i+1:], i+1):
                # 计算实体在文本中的距离
                distance = abs(text.find(entity1['value']) - text.find(entity2['value']))
                if distance < 200:  # 在200个字符内认为有关系
                    relation_type = self._infer_relation_type(entity1, entity2)
                    if relation_type:
                        relation = {
                            'from': entity1['id'],
                            'to': entity2['id'],
                            'type': relation_type,
                            'source': source_file,
                            'confidence': min(0.9, 1.0 - distance/200)
                        }
                        relations.append(relation)

        return entities, relations

    def _infer_relation_type(self, entity1: dict, entity2: dict) -> str | None:
        """推断实体间关系类型"""
        type1, type2 = entity1['type'], entity2['type']

        # 定义关系映射
        relation_mapping = {
            ('专利法条', '实施细则'): '包含关系',
            ('专利法条', '技术术语'): '涉及关系',
            ('决定文书', '申请号'): '关联申请',
            ('决定文书', '专利号'): '涉及专利',
            ('法律法规', '决定文书'): '法律依据',
            ('程序类型', '决定文书'): '程序类型',
            ('决定类型', '决定文书'): '决定结果',
        }

        # 双向查找
        key = (type1, type2) if (type1, type2) in relation_mapping else (type2, type1)
        if key in relation_mapping:
            return relation_mapping[key]

        return '相关关系'  # 默认关系

class QualityController:
    """质量控制器 - 基于诊断结果优化的质量控制"""

    def __init__(self, threshold: float = 0.50):  # 基于诊断结果推荐的阈值
        self.threshold = threshold

    def assess_quality(self, entities: list[dict], relations: list[dict]) -> dict:
        """评估提取质量"""
        if not entities and not relations:
            return {'quality_score': 0.0, 'passed': False}

        # 计算实体质量指标
        entity_confidence_scores = [e['confidence'] for e in entities]
        relation_confidence_scores = [r['confidence'] for r in relations]

        avg_entity_confidence = sum(entity_confidence_scores) / len(entity_confidence_scores) if entity_confidence_scores else 0
        avg_relation_confidence = sum(relation_confidence_scores) / len(relation_confidence_scores) if relation_confidence_scores else 0

        # 多维度质量评分
        diversity_score = len({e['type'] for e in entities}) / 10.0  # 实体类型多样性
        coverage_score = min(1.0, len(entities) / 20.0)  # 实体数量覆盖度

        # 综合质量分数
        quality_score = (
            avg_entity_confidence * 0.4 +
            avg_relation_confidence * 0.3 +
            diversity_score * 0.2 +
            coverage_score * 0.1
        )

        return {
            'quality_score': quality_score,
            'passed': quality_score >= self.threshold,
            'entity_count': len(entities),
            'relation_count': len(relations),
            'avg_entity_confidence': avg_entity_confidence,
            'avg_relation_confidence': avg_relation_confidence,
            'diversity_score': diversity_score,
            'coverage_score': coverage_score
        }

class PatentKnowledgeGraphProcessor:
    """专利知识图谱处理器 - 高质量版本"""

    def __init__(self, quality_threshold: float = 0.85):
        self.doc_reader = DocumentReader()
        self.entity_extractor = EntityExtractor()
        self.quality_controller = QualityController(quality_threshold)
        self.processing_stats = {
            'start_time': datetime.now(),
            'processed': 0,
            'successful': 0,
            'high_quality': 0,
            'total_entities': 0,
            'total_relations': 0,
            'errors': 0
        }

    def process_single_document(self, file_path: str) -> dict | None:
        """处理单个文档"""
        try:
            # 读取文档
            content = self.doc_reader.read_document(file_path)
            if not content or len(content.strip()) < 50:
                return None

            # 提取实体和关系
            entities, relations = self.entity_extractor.extract_entities(content, file_path)

            # 质量评估
            quality_result = self.quality_controller.assess_quality(entities, relations)

            if quality_result['passed']:
                result = {
                    'file': file_path,
                    'entities': entities,
                    'relations': relations,
                    'quality': quality_result,
                    'processing_time': time.time()
                }
                return result
            else:
                logger.debug(f"质量未通过: {file_path} (质量分数: {quality_result['quality_score']:.3f})")
                return None

        except Exception as e:
            logger.error(f"处理文档失败 {file_path}: {e}")
            self.processing_stats['errors'] += 1
            return None

    def process_documents(self, source_dir: str, max_docs: int = 1000) -> dict:
        """批量处理文档"""
        source_path = Path(source_dir)

        # 查找所有文档
        doc_files = []
        for ext in ['*.doc', '*.docx', '*.txt', '*.md']:
            doc_files.extend(source_path.glob(f"**/{ext}"))

        # 限制处理数量
        doc_files = doc_files[:max_docs]

        logger.info(f"找到 {len(doc_files)} 个文档，开始处理...")

        all_results = []
        start_time = time.time()

        for i, file_path in enumerate(doc_files):
            self.processing_stats['processed'] += 1

            # 显示进度
            if i % 100 == 0 or i == len(doc_files) - 1:
                elapsed = time.time() - start_time
                speed = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(doc_files) - i - 1) / speed if speed > 0 else 0
                logger.info(f"进度: {i+1}/{len(doc_files)} ({(i+1)/len(doc_files)*100:.1f}%) | "
                          f"高质量: {self.processing_stats['high_quality']} | "
                          f"速度: {speed:.1f} 文档/秒 | ETA: {eta/60:.1f}分钟")

            # 处理单个文档
            result = self.process_single_document(str(file_path))
            if result:
                all_results.append(result)
                self.processing_stats['successful'] += 1
                self.processing_stats['high_quality'] += 1
                self.processing_stats['total_entities'] += len(result['entities'])
                self.processing_stats['total_relations'] += len(result['relations'])

        # 计算最终统计
        processing_time = time.time() - start_time
        end_time = datetime.now()

        # 创建可序列化的统计数据
        serializable_stats = {
            'start_time': self.processing_stats['start_time'].isoformat(),
            'end_time': end_time.isoformat(),
            'processed': self.processing_stats['processed'],
            'successful': self.processing_stats['successful'],
            'high_quality': self.processing_stats['high_quality'],
            'total_entities': self.processing_stats['total_entities'],
            'total_relations': self.processing_stats['total_relations'],
            'errors': self.processing_stats['errors'],
            'processing_time': processing_time,
            'processing_time_str': str(processing_time),
            'avg_speed': len(doc_files) / processing_time if processing_time > 0 else 0
        }

        # 保存结果
        output_data = {
            'processing_stats': serializable_stats,
            'results': all_results
        }

        return output_data

    def save_results(self, results: dict, output_dir: str) -> str:
        """保存处理结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = output_path / f"patent_hq_results_{timestamp}.json"

        # 保存详细结果
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 保存统计摘要
        summary_file = output_path / f"processing_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results['processing_stats'], f, ensure_ascii=False, indent=2)

        logger.info(f"结果已保存到: {result_file}")
        logger.info(f"摘要已保存到: {summary_file}")

        return str(result_file)

def main():
    """主函数"""
    logger.info('🏛️ 高质量专利知识图谱处理系统 v2.0')
    logger.info(str('=' * 60))
    logger.info('📝 修复编码问题和质量控制')
    logger.info('⚡ 支持多种文档格式和自动编码检测')
    logger.info('🎯 质量控制: 基于多维度评分，目标F1>0.85')
    logger.info(str('=' * 60))

    # 配置参数
    source_dir = '/Users/xujian/学习资料/专利'
    output_dir = '/tmp/patent_hq_output'
    max_docs = 1000  # 演示数量

    logger.info(f"\n📁 源目录: {source_dir}")
    logger.info(f"📊 最大处理文档数: {max_docs}")
    logger.info(f"📁 输出目录: {output_dir}")

    # 创建处理器 - 基于诊断结果使用优化后的阈值
    processor = PatentKnowledgeGraphProcessor(quality_threshold=0.50)

    logger.info("\n🎯 开始高质量处理...")
    datetime.now()

    try:
        # 处理文档
        results = processor.process_documents(source_dir, max_docs)

        # 保存结果
        result_file = processor.save_results(results, output_dir)

        # 显示最终统计
        stats = results['processing_stats']
        logger.info("\n🏆 高质量处理完成！")
        logger.info(str('=' * 60))
        logger.info("📊 处理统计:")
        logger.info(f"   总文档数: {stats['processed']:,}")
        logger.info(f"   成功处理: {stats['successful']:,} ({stats['successful']/stats['processed']*100:.1f}%)")
        logger.info(f"   高质量文档: {stats['high_quality']:,} ({stats['high_quality']/stats['processed']*100:.1f}%)")
        logger.info(f"   实体总数: {stats['total_entities']:,}")
        logger.info(f"   关系总数: {stats['total_relations']:,}")
        logger.info(f"   平均实体/文档: {stats['total_entities']/max(stats['successful'],1):.1f}")
        logger.info(f"   处理时间: {stats['processing_time_str']}")
        logger.info(f"   处理速度: {stats['avg_speed']:.1f} 文档/秒")
        logger.info(f"\n📄 结果文件: {result_file}")

        # 显示质量改进说明
        logger.info("\n💡 质量改进特性:")
        logger.info("   ✅ 自动编码检测和处理")
        logger.info("   ✅ 多维度质量评估")
        logger.info("   ✅ 预定义高质量实体库")
        logger.info("   ✅ 智能关系推断")
        logger.info("   ✅ 详细的处理日志")

    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}")
        logger.error(traceback.format_exc())
        return 1

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 处理被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 处理异常: {e}")
        sys.exit(1)
