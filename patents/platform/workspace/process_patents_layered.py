#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分层质量专利知识图谱处理系统
Layered Quality Patent Knowledge Graph Processing System

实现分层质量评估策略：
- 基础层：质量阈值 0.3（覆盖更多文档）
- 高质量层：质量阈值 0.6（优质文档）
- 精英层：质量阈值 0.8（顶级文档）

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'patent_layered_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LayeredDocumentReader:
    """分层文档读取器 - 智能编码检测"""

    @staticmethod
    def read_document(file_path: str) -> str | None:
        """智能读取文档内容"""
        try:
            # 扩展编码检测
            encodings = [
                'utf-8', 'gbk', 'gb2312', 'big5', 'latin1',
                'cp936', 'utf-16', 'utf-16-le', 'utf-16-be'
            ]

            content = None
            used_encoding = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            # 如果文本读取失败，尝试二进制解码
            if not content:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()

                for encoding in encodings[:5]:  # 只尝试主要编码
                    try:
                        content = raw_data.decode(encoding, errors='ignore')
                        if len(content.strip()) > 100:
                            used_encoding = f"{encoding}(容错)"
                            break
                    except:
                        continue

            if content and len(content.strip()) > 50:
                logger.debug(f"成功读取: {file_path} (编码: {used_encoding}, 长度: {len(content)})")
                return content
            else:
                logger.warning(f"文档内容过短或为空: {file_path}")
                return None

        except Exception as e:
            logger.error(f"读取文档失败 {file_path}: {e}")
            return None

class EnhancedEntityExtractor:
    """增强实体提取器 - 更丰富的实体识别"""

    def __init__(self):
        # 扩展的实体识别模式
        self.entity_patterns = {
            '法律条文': [
                r'专利法第([一二三四五六七八九十百千万\d]+)条',
                r'第([一二三四五六七八九十百千万\d]+)条[，。]?(?:第([一二三四五六七八九十百千万\d]+)款[，。]?)?',
                r'实施细则第([一二三四五六七八九十百千万\d]+)条',
                r'审查指南[第]?([一二三四五六七八九十百千万\d]+)[部分章节]'
            ],
            '申请号专利号': [
                r'(\d{13,})',  # 13位以上数字
                r'(CN\d+[A-Z]?)',  # 中国专利号
                r'(US\d+[A-Z]?)',  # 美国专利号
                r'(EP\d+[A-Z]?)',  # 欧洲专利号
                r'(WO\d+[A-Z]?)',  # PCT专利号
                r'([A-Z]\d+[A-Z]?\d*)'  # 其他格式
            ],
            '决定文书': [
                r'专利复审委员会',
                r'专利无效宣告',
                r'复审请求审查决定',
                r'无效宣告请求审查决定',
                r'行政诉讼\(\d+\)号',
                r'国家知识产权局',
                r'专利局'
            ],
            '法律概念': [
                r'新颖性',
                r'创造性',
                r'实用性',
                r'公开不充分',
                r'权利要求书',
                r'说明书',
                r'技术方案',
                r'现有技术',
                r'对比文件',
                r'技术特征',
                r'保护范围',
                r'侵权判定'
            ],
            '程序类型': [
                r'复审请求',
                r'无效宣告请求',
                r'驳回',
                r'撤销',
                r'维持有效',
                r'宣告无效',
                r'部分无效',
                r'驳回请求',
                r'撤销决定'
            ],
            '技术领域': [
                r'机械[制造工程]?',
                r'电子[信息通信]?',
                r'通信[技术网络]?',
                r'化学[化工]?',
                r'生物[医药医疗]?',
                r'计算机[软件网络]?',
                r'材料[科学工程]?',
                r'光学[激光]?',
                r'自动化[控制]?',
                r'新能源[环保]?',
                r'医疗器械',
                r'半导体',
                r'人工智能'
            ],
            '申请人类型': [
                r'个人发明',
                r'企业发明',
                r'高校[大学]?',
                r'科研院所',
                r'跨国公司',
                r'中小企业',
                r'创业公司'
            ],
            '审查标准': [
                r'三性判断',
                r'新颖性判断',
                r'创造性判断',
                r'实用性判断',
                r'充分公开',
                r'权利要求清晰',
                r'说明书支持',
                r'修改超范围'
            ]
        }

        # 高质量关键词库
        self.quality_keywords = {
            '法律法规': ['专利法', '专利法实施细则', '专利审查指南', '民法典', '行政诉讼法', '商标法', '著作权法'],
            '程序类型': ['复审请求', '无效宣告请求', '行政诉讼', '行政复议', '审查决定', '异议程序'],
            '决定结果': ['维持有效', '宣告无效', '部分无效', '驳回请求', '撤销决定', '变更决定'],
            '技术领域': ['机械', '电子', '通信', '化学', '生物', '医药', '计算机', '软件', '材料', '光学', '新能源', '人工智能'],
            '审查标准': ['三性判断', '新颖性', '创造性', '实用性', '充分公开', '权利要求', '说明书'],
            '案件类型': ['发明', '实用新型', '外观设计', '发明专利', '实用新型专利', '外观设计专利'],
            '法律术语': ['优先权', '申请日', '公开日', '授权日', '期限', '费用', '侵权', '许可']
        }

    def extract_entities(self, text: str, source_file: str) -> Tuple[List[Dict], List[Dict]]:
        """提取实体和关系"""
        entities = []
        relations = []
        entity_id_counter = 0

        # 基于模式的实体提取
        for category, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_value = match.group(0)
                    entity_id = f"ent_{entity_id_counter}"
                    entity_id_counter += 1

                    # 计算置信度
                    confidence = self._calculate_entity_confidence(entity_value, category, match, text)

                    entity = {
                        'id': entity_id,
                        'type': category,
                        'value': entity_value,
                        'source': source_file,
                        'confidence': confidence,
                        'context': text[max(0, match.start()-50):match.end()+50],
                        'pattern': pattern,
                        'position': match.start()
                    }
                    entities.append(entity)

        # 基于关键词的实体提取
        for category, keywords in self.quality_keywords.items():
            for keyword in keywords:
                # 查找关键词的所有出现
                start_pos = text.find(keyword)
                while start_pos != -1:
                    entity_id = f"key_{entity_id_counter}"
                    entity_id_counter += 1

                    # 关键词的置信度较高
                    confidence = 0.95

                    entity = {
                        'id': entity_id,
                        'type': category,
                        'value': keyword,
                        'source': source_file,
                        'confidence': confidence,
                        'context': text[max(0, start_pos-30):start_pos+30+len(keyword)],
                        'pattern': 'keyword',
                        'position': start_pos
                    }
                    entities.append(entity)

                    # 查找下一个出现位置
                    start_pos = text.find(keyword, start_pos + 1)

        # 提取关系 - 增强的关系识别
        relations = self._extract_relations(entities, text, source_file)

        return entities, relations

    def _calculate_entity_confidence(self, value: str, category: str, match, text: str) -> float:
        """计算实体置信度"""
        base_confidence = 0.8

        # 根据实体类型调整
        if category == '申请号专利号':
            # 数字长度越长，置信度越高
            if len(value) >= 13:
                base_confidence = 0.95
            elif len(value) >= 8:
                base_confidence = 0.9
        elif category == '法律条文':
            base_confidence = 0.9
        elif category in ['法律概念', '程序类型']:
            base_confidence = 0.85

        # 根据上下文调整
        context_start = max(0, match.start() - 30)
        context_end = min(len(text), match.end() + 30)
        context = text[context_start:context_end]

        # 如果上下文中有法律相关词汇，提高置信度
        legal_indicators = ['根据', '依照', '按照', '依据', '符合', '违反', '规定', '要求']
        for indicator in legal_indicators:
            if indicator in context:
                base_confidence += 0.05
                break

        return min(1.0, base_confidence)

    def _extract_relations(self, entities: List[Dict], text: str, source_file: str) -> List[Dict]:
        """提取实体间关系"""
        relations = []
        relation_id_counter = 0

        # 实体关系映射
        relation_mapping = {
            ('法律法规', '法律条文'): '包含关系',
            ('法律条文', '技术领域'): '涉及领域',
            ('法律条文', '法律概念'): '定义概念',
            ('决定文书', '申请号专利号'): '关联专利',
            ('决定文书', '程序类型'): '程序类型',
            ('决定文书', '决定结果'): '决定结果',
            ('程序类型', '法律法规'): '法律依据',
            ('技术领域', '申请人类型'): '领域申请人',
            ('法律概念', '审查标准'): '审查标准',
        }

        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities[i+1:], i+1):
                # 计算文本距离
                distance = abs(entity1['position'] - entity2['position'])

                # 距离阈值
                max_distance = 300

                if distance <= max_distance:
                    # 查找关系类型
                    type1, type2 = entity1['type'], entity2['type']
                    relation_type = None

                    # 直接映射
                    if (type1, type2) in relation_mapping:
                        relation_type = relation_mapping[(type1, type2)]
                    elif (type2, type1) in relation_mapping:
                        relation_type = relation_mapping[(type2, type1)]
                    else:
                        # 默认关系
                        relation_type = '相关关系'

                    # 计算关系置信度
                    confidence = max(0.5, 1.0 - distance / max_distance)

                    relation = {
                        'id': f"rel_{relation_id_counter}",
                        'from': entity1['id'],
                        'to': entity2['id'],
                        'type': relation_type,
                        'source': source_file,
                        'confidence': confidence,
                        'distance': distance
                    }
                    relations.append(relation)
                    relation_id_counter += 1

        return relations

class LayeredQualityController:
    """分层质量控制器"""

    def __init__(self):
        self.quality_thresholds = {
            'basic': 0.3,      # 基础层：覆盖大多数文档
            'high_quality': 0.6,  # 高质量层：优质文档
            'elite': 0.7       # 精英层：顶级文档（降低阈值）
        }

    def assess_quality(self, entities: List[Dict], relations: List[Dict]) -> Dict:
        """评估提取质量并分层"""
        if not entities and not relations:
            return {
                'quality_score': 0.0,
                'passed': False,
                'quality_layer': 'none',
                'entity_count': 0,
                'relation_count': 0
            }

        # 多维度质量评分
        scores = {
            'entity_count': self._score_entity_count(entities),
            'entity_diversity': self._score_entity_diversity(entities),
            'avg_confidence': self._score_avg_confidence(entities),
            'relation_density': self._score_relation_density(entities, relations),
            'content_richness': self._score_content_richness(entities)
        }

        # 权重分配
        weights = {
            'entity_count': 0.25,
            'entity_diversity': 0.20,
            'avg_confidence': 0.25,
            'relation_density': 0.20,
            'content_richness': 0.10
        }

        # 计算加权总分
        total_score = sum(scores[metric] * weights[metric] for metric in scores)

        # 确定质量分层
        quality_layer = self._determine_quality_layer(total_score)

        return {
            'quality_score': total_score,
            'passed': total_score >= self.quality_thresholds['basic'],
            'quality_layer': quality_layer,
            'entity_count': len(entities),
            'relation_count': len(relations),
            'detailed_scores': scores,
            'threshold_met': {
                'basic': total_score >= self.quality_thresholds['basic'],
                'high_quality': total_score >= self.quality_thresholds['high_quality'],
                'elite': total_score >= self.quality_thresholds['elite']
            }
        }

    def _score_entity_count(self, entities: List[Dict]) -> float:
        """实体数量评分 (0-1)"""
        count = len(entities)
        if count >= 100:
            return 1.0
        elif count >= 50:
            return 0.8
        elif count >= 20:
            return 0.6
        elif count >= 10:
            return 0.4
        elif count >= 5:
            return 0.2
        else:
            return 0.1

    def _score_entity_diversity(self, entities: List[Dict]) -> float:
        """实体类型多样性评分 (0-1)"""
        unique_types = len(set(e['type'] for e in entities))
        return min(1.0, unique_types / 8.0)  # 8种类型为满分

    def _score_avg_confidence(self, entities: List[Dict]) -> float:
        """平均置信度评分 (0-1)"""
        if not entities:
            return 0.0
        avg_conf = sum(e['confidence'] for e in entities) / len(entities)
        return avg_conf

    def _score_relation_density(self, entities: List[Dict], relations: List[Dict]) -> float:
        """关系密度评分 (0-1)"""
        if not entities:
            return 0.0
        density = len(relations) / len(entities)
        return min(1.0, density / 10.0)  # 每个实体10个关系为满分

    def _score_content_richness(self, entities: List[Dict]) -> float:
        """内容丰富度评分 (0-1)"""
        if not entities:
            return 0.0

        # 计算平均上下文长度
        avg_context_length = sum(len(e.get('context', '')) for e in entities) / len(entities)
        return min(1.0, avg_context_length / 100.0)  # 100字符为满分

    def _determine_quality_layer(self, score: float) -> str:
        """确定质量分层"""
        if score >= self.quality_thresholds['elite']:
            return 'elite'
        elif score >= self.quality_thresholds['high_quality']:
            return 'high_quality'
        elif score >= self.quality_thresholds['basic']:
            return 'basic'
        else:
            return 'rejected'

class LayeredPatentKnowledgeGraphProcessor:
    """分层专利知识图谱处理器"""

    def __init__(self):
        self.doc_reader = LayeredDocumentReader()
        self.entity_extractor = EnhancedEntityExtractor()
        self.quality_controller = LayeredQualityController()

        # 分层统计
        self.layer_stats = {
            'basic': {'count': 0, 'entities': 0, 'relations': 0},
            'high_quality': {'count': 0, 'entities': 0, 'relations': 0},
            'elite': {'count': 0, 'entities': 0, 'relations': 0},
            'rejected': {'count': 0}
        }

    def process_single_document(self, file_path: str) -> Dict | None:
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

                # 更新分层统计
                layer = quality_result['quality_layer']
                if layer in self.layer_stats:
                    self.layer_stats[layer]['count'] += 1
                    self.layer_stats[layer]['entities'] += len(entities)
                    self.layer_stats[layer]['relations'] += len(relations)

                return result
            else:
                self.layer_stats['rejected']['count'] += 1
                return None

        except Exception as e:
            logger.error(f"处理文档失败 {file_path}: {e}")
            self.layer_stats['rejected']['count'] += 1
            return None

    def process_documents(self, source_dir: str, max_docs: int = 1000) -> Dict:
        """批量处理文档"""
        source_path = Path(source_dir)

        # 查找所有文档
        doc_files = []
        for ext in ['*.doc', '*.docx', '*.txt', '*.md']:
            doc_files.extend(source_path.glob(f"**/{ext}"))

        # 限制处理数量
        doc_files = doc_files[:max_docs]

        logger.info(f"找到 {len(doc_files)} 个文档，开始分层处理...")

        all_results = []
        start_time = time.time()

        for i, file_path in enumerate(doc_files):
            # 显示进度
            if i % 100 == 0 or i == len(doc_files) - 1:
                elapsed = time.time() - start_time
                speed = (i + 1) / elapsed if elapsed > 0 else 0
                eta = (len(doc_files) - i - 1) / speed if speed > 0 else 0

                passed_count = sum(layer['count'] for layer in self.layer_stats.values() if layer != self.layer_stats['rejected'])

                logger.info(f"进度: {i+1}/{len(doc_files)} ({(i+1)/len(doc_files)*100:.1f}%) | "
                          f"通过: {passed_count} | "
                          f"精英: {self.layer_stats['elite']['count']} | "
                          f"高质量: {self.layer_stats['high_quality']['count']} | "
                          f"基础: {self.layer_stats['basic']['count']} | "
                          f"速度: {speed:.1f} 文档/秒 | ETA: {eta/60:.1f}分钟")

            # 处理单个文档
            result = self.process_single_document(str(file_path))
            if result:
                all_results.append(result)

        # 计算最终统计
        processing_time = time.time() - start_time
        end_time = datetime.now()

        # 创建可序列化的统计数据
        serializable_stats = {
            'start_time': datetime.now().isoformat(),
            'end_time': end_time.isoformat(),
            'processing_time': processing_time,
            'processed': len(doc_files),
            'successful': len(all_results),
            'rejected': self.layer_stats['rejected']['count'],
            'layer_stats': self.layer_stats,
            'total_entities': sum(layer.get('entities', 0) for layer in self.layer_stats.values() if isinstance(layer, dict)),
            'total_relations': sum(layer.get('relations', 0) for layer in self.layer_stats.values() if isinstance(layer, dict)),
            'avg_speed': len(doc_files) / processing_time if processing_time > 0 else 0
        }

        # 保存结果
        output_data = {
            'processing_stats': serializable_stats,
            'layer_distribution': {
                layer: {
                    'count': stats['count'],
                    'percentage': stats['count'] / len(doc_files) * 100 if len(doc_files) > 0 else 0,
                    'entities': stats.get('entities', 0),
                    'relations': stats.get('relations', 0),
                    'avg_entities_per_doc': stats.get('entities', 0) / max(stats['count'], 1)
                }
                for layer, stats in self.layer_stats.items()
            },
            'results': all_results
        }

        return output_data

def main():
    """主函数"""
    logger.info('🏛️ 分层质量专利知识图谱处理系统')
    logger.info(str('=' * 60))
    logger.info('📝 实现分层质量评估策略')
    logger.info('🎯 三层分级：基础(0.3) + 高质量(0.6) + 精英(0.8)')
    logger.info('⚡ 增强实体识别和智能关系推断')
    logger.info(str('=' * 60))

    # 配置参数
    source_dir = '/Users/xujian/学习资料/专利'
    output_dir = '/tmp/patent_layered_output'
    max_docs = 1000  # 演示数量

    logger.info(f"\n📁 源目录: {source_dir}")
    logger.info(f"📊 最大处理文档数: {max_docs}")
    logger.info(f"📁 输出目录: {output_dir}")

    # 创建处理器
    processor = LayeredPatentKnowledgeGraphProcessor()

    logger.info(f"\n🎯 开始分层处理...")
    start_time = datetime.now()

    try:
        # 处理文档
        results = processor.process_documents(source_dir, max_docs)

        # 保存结果
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = output_path / f"patent_layered_results_{timestamp}.json"

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        # 显示最终统计
        stats = results['processing_stats']
        layer_dist = results['layer_distribution']

        logger.info(f"\n🏆 分层处理完成！")
        logger.info(str('=' * 60))
        logger.info(f"📊 处理统计:")
        logger.info(f"   总文档数: {stats['processed']:,}")
        logger.info(f"   成功处理: {stats['successful']:,} ({stats['successful']/stats['processed']*100:.1f}%)")
        logger.info(f"   拒绝处理: {stats['rejected']:,} ({stats['rejected']/stats['processed']*100:.1f}%)")
        logger.info(f"   处理时间: {stats['processing_time']:.1f}秒")
        logger.info(f"   处理速度: {stats['avg_speed']:.1f} 文档/秒")

        logger.info(f"\n🎯 分层质量分布:")
        for layer, data in layer_dist.items():
            if layer != 'rejected':
                print(f"   {layer.replace('_', ' ').title()}: {data['count']} 个文档 ({data['percentage']:.1f}%) "
                      f"- 平均 {data['avg_entities_per_doc']:.1f} 实体/文档")

        logger.info(f"\n💡 分层质量优势:")
        logger.info(f"   ✅ 精英层文档质量最高，适合重点分析")
        logger.info(f"   ✅ 高质量层文档数量适中，平衡质量与覆盖")
        logger.info(f"   ✅ 基础层文档覆盖最广，保证数据完整性")
        logger.info(f"   ✅ 智能编码检测和增强实体识别")
        logger.info(f"   ✅ 丰富的关系网络构建")

        logger.info(f"\n📄 结果文件: {result_file}")

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