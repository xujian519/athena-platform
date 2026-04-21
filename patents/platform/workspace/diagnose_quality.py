#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱质量诊断工具
Patent Knowledge Graph Quality Diagnosis Tool

分析高质量系统为什么没有提取到实体的原因
并调优质量评分机制

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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """文档分析器 - 诊断实体提取问题"""

    def __init__(self):
        # 扩展实体识别模式
        self.entity_patterns = {
            '法律条文': [
                r'专利法第([一二三四五六七八九十百千万\d]+)条',
                r'第([一二三四五六七八九十百千万\d]+)条[，。]?(?:第([一二三四五六七八九十百千万\d]+)款[，。]?)?',
                r'实施细则第([一二三四五六七八九十百千万\d]+)条',
                r'审查指南[第]?([一二三四五六七八九十百千万\d]+)[部分章节]'
            ],
            '申请号专利号': [
                r'(\d{13,})',  # 13位以上数字作为申请号
                r'(CN\d+[A-Z]?)',  # 专利号格式
                r'([A-Z]\d+[A-Z]?\d*)'  # 其他专利编号格式
            ],
            '决定文书': [
                r'专利复审委员会',
                r'专利无效宣告',
                r'复审请求审查决定',
                r'无效宣告请求审查决定',
                r'行政诉讼',
                r'国家知识产权局'
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
                r'技术特征'
            ],
            '程序类型': [
                r'复审请求',
                r'无效宣告请求',
                r'驳回',
                r'撤销',
                r'维持有效',
                r'宣告无效',
                r'部分无效'
            ]
        }

        # 预定义高质量词汇
        self.quality_keywords = {
            '法律法规': ['专利法', '专利法实施细则', '专利审查指南', '民法典', '行政诉讼法'],
            '程序类型': ['复审请求', '无效宣告请求', '行政诉讼', '行政复议', '审查决定'],
            '决定结果': ['维持有效', '宣告无效', '部分无效', '驳回请求', '撤销决定'],
            '技术领域': ['机械', '电子', '通信', '化学', '生物', '医药', '计算机', '软件'],
            '审查标准': ['三性判断', '新颖性', '创造性', '实用性', '充分公开']
        }

    def analyze_single_document(self, file_path: str) -> Dict:
        """分析单个文档"""
        result = {
            'file': file_path,
            'readable': False,
            'content_length': 0,
            'encoding': 'unknown',
            'entities': [],
            'quality_score': 0.0,
            'issues': []
        }

        try:
            # 尝试读取文档
            encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin1']
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    result['encoding'] = encoding
                    result['readable'] = True
                    break
                except UnicodeDecodeError:
                    continue

            if not content:
                result['issues'].append('无法解码文档')
                return result

            result['content_length'] = len(content)
            if len(content.strip()) < 50:
                result['issues'].append('文档内容过短')
                return result

            # 提取实体
            entities = []
            entity_id_counter = 0

            # 基于模式的实体提取
            for category, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        entity_value = match.group(0)
                        entity_id = f"ent_{entity_id_counter}"
                        entity_id_counter += 1

                        entity = {
                            'id': entity_id,
                            'type': category,
                            'value': entity_value,
                            'confidence': 0.9,
                            'context': content[max(0, match.start()-30):match.end()+30],
                            'pattern': pattern
                        }
                        entities.append(entity)

            # 基于关键词的实体提取
            for category, keywords in self.quality_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        entity_id = f"key_{entity_id_counter}"
                        entity_id_counter += 1

                        # 找到关键词的所有出现位置
                        start_pos = content.find(keyword)
                        entity = {
                            'id': entity_id,
                            'type': category,
                            'value': keyword,
                            'confidence': 0.95,  # 关键词高置信度
                            'context': content[max(0, start_pos-20):start_pos+20+len(keyword)],
                            'pattern': 'keyword'
                        }
                        entities.append(entity)

            result['entities'] = entities
            result['quality_score'] = self.calculate_quality_score(entities, len(content))

        except Exception as e:
            result['issues'].append(f"分析异常: {e}")

        return result

    def calculate_quality_score(self, entities: List[Dict], content_length: int) -> float:
        """计算质量分数 - 调优后的评分机制"""
        if not entities:
            return 0.0

        # 实体数量分数 (0-30分)
        entity_count_score = min(30.0, len(entities) * 2.0)

        # 实体类型多样性 (0-25分)
        unique_types = len(set(e['type'] for e in entities))
        diversity_score = min(25.0, unique_types * 5.0)

        # 平均置信度 (0-25分)
        avg_confidence = sum(e['confidence'] for e in entities) / len(entities)
        confidence_score = avg_confidence * 25.0

        # 内容覆盖度 (0-20分)
        coverage_score = min(20.0, len(entities) / max(1, content_length / 1000))

        # 总分
        total_score = entity_count_score + diversity_score + confidence_score + coverage_score

        # 归一化到0-1范围
        normalized_score = min(1.0, total_score / 100.0)

        return normalized_score

    def analyze_batch(self, source_dir: str, sample_size: int = 20) -> Dict:
        """批量分析文档样本"""
        source_path = Path(source_dir)

        # 查找所有文档
        doc_files = []
        for ext in ['*.doc', '*.docx', '*.txt', '*.md']:
            doc_files.extend(source_path.glob(f"**/{ext}"))

        # 随机采样
        import random
        if len(doc_files) > sample_size:
            doc_files = random.sample(doc_files, sample_size)

        logger.info(f"📊 分析 {len(doc_files)} 个文档样本...")

        all_results = []
        stats = {
            'total': len(doc_files),
            'readable': 0,
            'with_entities': 0,
            'high_quality': 0,  # 质量分数 >= 0.6
            'excellent_quality': 0,  # 质量分数 >= 0.8
            'total_entities': 0,
            'avg_quality_score': 0.0,
            'entity_types': set(),
            'common_issues': {}
        }

        for file_path in doc_files:
            result = self.analyze_single_document(str(file_path))
            all_results.append(result)

            # 更新统计
            if result['readable']:
                stats['readable'] += 1

            if result['entities']:
                stats['with_entities'] += 1
                stats['total_entities'] += len(result['entities'])
                stats['entity_types'].update(e['type'] for e in result['entities'])

            if result['quality_score'] >= 0.6:
                stats['high_quality'] += 1
            if result['quality_score'] >= 0.8:
                stats['excellent_quality'] += 1

            # 收集常见问题
            for issue in result['issues']:
                stats['common_issues'][issue] = stats['common_issues'].get(issue, 0) + 1

        # 计算平均质量分数
        quality_scores = [r['quality_score'] for r in all_results if r['quality_score'] > 0]
        if quality_scores:
            stats['avg_quality_score'] = sum(quality_scores) / len(quality_scores)

        stats['entity_types'] = list(stats['entity_types'])

        return {
            'stats': stats,
            'results': all_results,
            'recommendations': self.generate_recommendations(stats)
        }

    def generate_recommendations(self, stats: Dict) -> List[str]:
        """生成调优建议"""
        recommendations = []

        if stats['readable'] / stats['total'] < 0.8:
            recommendations.append('🔧 文档编码问题：建议增强编码检测机制')

        if stats['with_entities'] / stats['readable'] < 0.5:
            recommendations.append('🔧 实体提取效率低：建议优化实体识别模式')

        if stats['avg_quality_score'] < 0.6:
            recommendations.append(f"🎯 建议降低质量阈值到 {stats['avg_quality_score']:.2f}")

        if stats['total_entities'] / stats['with_entities'] < 10:
            recommendations.append('🔧 实体数量偏少：建议扩展实体识别模式')

        if '常见问题' in stats and stats['common_issues']:
            most_common = max(stats['common_issues'].items(), key=lambda x: x[1])
            recommendations.append(f"🔧 主要问题：{most_common[0]} (出现{most_common[1]}次)")

        return recommendations

def main():
    """主函数"""
    logger.info('🔍 专利知识图谱质量诊断工具')
    logger.info(str('=' * 50))
    logger.info('📝 分析实体提取问题并优化质量评分机制')
    logger.info(str('=' * 50))

    source_dir = '/Users/xujian/学习资料/专利'

    if not os.path.exists(source_dir):
        logger.info(f"❌ 源目录不存在: {source_dir}")
        return 1

    analyzer = DocumentAnalyzer()

    logger.info(f"\n🎯 开始分析文档样本...")
    logger.info(f"📁 源目录: {source_dir}")

    try:
        # 分析样本
        result = analyzer.analyze_batch(source_dir, sample_size=50)
        stats = result['stats']

        logger.info(f"\n📊 分析结果:")
        logger.info(f"   总文档数: {stats['total']}")
        logger.info(f"   可读取: {stats['readable']} ({stats['readable']/stats['total']*100:.1f}%)")
        logger.info(f"   有实体: {stats['with_entities']} ({stats['with_entities']/max(stats['readable'],1)*100:.1f}%)")
        logger.info(f"   高质量(≥0.6): {stats['high_quality']} ({stats['high_quality']/max(stats['readable'],1)*100:.1f}%)")
        logger.info(f"   优秀质量(≥0.8): {stats['excellent_quality']} ({stats['excellent_quality']/max(stats['readable'],1)*100:.1f}%)")
        logger.info(f"   实体总数: {stats['total_entities']}")
        logger.info(f"   平均实体/文档: {stats['total_entities']/max(stats['with_entities'],1):.1f}")
        logger.info(f"   平均质量分数: {stats['avg_quality_score']:.3f}")
        logger.info(f"   实体类型: {len(stats['entity_types'])}种 - {', '.join(stats['entity_types'])}")

        if stats['common_issues']:
            logger.info(f"\n⚠️ 常见问题:")
            for issue, count in stats['common_issues'].items():
                logger.info(f"   {issue}: {count}次")

        logger.info(f"\n💡 调优建议:")
        for i, rec in enumerate(result['recommendations'], 1):
            logger.info(f"   {i}. {rec}")

        # 保存详细分析结果
        output_file = f"/tmp/patent_quality_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 详细分析结果已保存到: {output_file}")

        # 推荐质量阈值
        recommended_threshold = max(0.4, stats['avg_quality_score'] - 0.1)
        logger.info(f"\n🎯 推荐质量阈值: {recommended_threshold:.2f}")

    except Exception as e:
        logger.info(f"\n❌ 分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n👋 分析被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.info(f"\n❌ 分析异常: {e}")
        sys.exit(1)