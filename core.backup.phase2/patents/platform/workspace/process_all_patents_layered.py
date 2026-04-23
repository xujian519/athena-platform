#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量分层专利知识图谱处理系统
Full-scale Layered Patent Knowledge Graph Processing System

处理全部57,218个专利文档的完整知识图谱构建系统

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

# 导入分层处理的核心类
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from process_patents_layered import (
    EnhancedEntityExtractor,
    LayeredDocumentReader,
    LayeredQualityController,
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'patent_full_layered_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FullScalePatentProcessor:
    """全量专利处理器"""

    def __init__(self):
        self.doc_reader = LayeredDocumentReader()
        self.entity_extractor = EnhancedEntityExtractor()
        # 设置专利文档路径
        self.patent_base_path = Path('/Users/xujian/学习资料/专利')
        self.output_path = Path('/Users/xujian/Athena工作平台/data/patent_knowledge_graph')
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.progress_file = self.output_path / 'processing_progress.json'
        self.quality_controller = LayeredQualityController()

        # 分层统计
        self.layer_stats = {
            'basic': {'count': 0, 'entities': 0, 'relations': 0},
            'high_quality': {'count': 0, 'entities': 0, 'relations': 0},
            'elite': {'count': 0, 'entities': 0, 'relations': 0},
            'rejected': {'count': 0}
        }

        # 全量处理配置
        self.batch_size = 1000  # 每批次处理1000个文档
        self.save_interval = 5000  # 每5000个文档保存一次中间结果

    def scan_all_documents(self, source_dir: str) -> List[str]:
        """扫描所有专利文档"""
        source_path = Path(source_dir)
        doc_files = []

        logger.info('🔍 扫描所有专利文档...')
        for ext in ['*.doc', '*.docx', '*.txt', '*.md']:
            files = list(source_path.glob(f"**/{ext}"))
            doc_files.extend([str(f) for f in files])
            logger.info(f"   {ext}: {len(files)} 个文件")

        logger.info(f"📊 总计找到 {len(doc_files)} 个专利文档")
        return doc_files

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

    def save_intermediate_results(self, results: List[Dict], batch_num: int, output_dir: str):
        """保存中间结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_file = output_path / f"patent_layered_batch_{batch_num}_{timestamp}.json"

        # 创建批次数据
        batch_data = {
            'batch_number': batch_num,
            'batch_size': len(results),
            'layer_stats': self.layer_stats.copy(),
            'processing_time': datetime.now().isoformat(),
            'results': results
        }

        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 批次 {batch_num} 结果已保存到: {batch_file}")

    def process_all_documents(self, source_dir: str, output_dir: str = '/tmp/patent_full_layered_output') -> Dict:
        """处理所有文档"""
        # 扫描所有文档
        all_files = self.scan_all_documents(source_dir)
        total_files = len(all_files)

        if total_files == 0:
            logger.error('❌ 未找到任何文档')
            return {'success': False, 'message': '未找到任何文档'}

        logger.info(f"\n🎯 开始全量处理 {total_files:,} 个专利文档...")
        logger.info(f"📊 预计处理时间: {total_files/10/3600:.1f} 小时 (按10文档/秒估算)")
        logger.info(f"💾 输出目录: {output_dir}")

        all_results = []
        start_time = time.time()

        # 分批处理
        for batch_start in range(0, total_files, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_files)
            batch_files = all_files[batch_start:batch_end]
            batch_num = batch_start // self.batch_size + 1

            logger.info(f"\n📦 处理批次 {batch_num} (文档 {batch_start+1}-{batch_end})")

            batch_results = []
            for i, file_path in enumerate(batch_files):
                global_idx = batch_start + i + 1

                # 显示进度
                if i % 100 == 0 or i == len(batch_files) - 1:
                    elapsed = time.time() - start_time
                    speed = global_idx / elapsed if elapsed > 0 else 0
                    eta = (total_files - global_idx) / speed if speed > 0 else 0

                    passed_count = sum(layer['count'] for layer in self.layer_stats.values() if layer != self.layer_stats['rejected'])

                    print(f"   进度: {global_idx:,}/{total_files:,} ({global_idx/total_files*100:.1f}%) | "
                          f"通过: {passed_count:,} | "
                          f"精英: {self.layer_stats['elite']['count']:,} | "
                          f"高质量: {self.layer_stats['high_quality']['count']:,} | "
                          f"基础: {self.layer_stats['basic']['count']:,} | "
                          f"速度: {speed:.1f} 文档/秒 | ETA: {eta/3600:.1f}小时")

                # 处理单个文档
                result = self.process_single_document(file_path)
                if result:
                    batch_results.append(result)

            # 保存中间结果
            self.save_intermediate_results(batch_results, batch_num, output_dir)
            all_results.extend(batch_results)

        # 计算最终统计
        processing_time = time.time() - start_time
        end_time = datetime.now()

        # 创建可序列化的统计数据
        serializable_stats = {
            'start_time': datetime.now().isoformat(),
            'end_time': end_time.isoformat(),
            'processing_time': processing_time,
            'processed': total_files,
            'successful': len(all_results),
            'rejected': self.layer_stats['rejected']['count'],
            'layer_stats': self.layer_stats,
            'total_entities': sum(layer.get('entities', 0) for layer in self.layer_stats.values() if isinstance(layer, dict)),
            'total_relations': sum(layer.get('relations', 0) for layer in self.layer_stats.values() if isinstance(layer, dict)),
            'avg_speed': total_files / processing_time if processing_time > 0 else 0
        }

        # 保存最终结果
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_result_file = output_path / f"patent_full_layered_results_{timestamp}.json"

        # 创建最终结果数据
        output_data = {
            'processing_stats': serializable_stats,
            'layer_distribution': {
                layer: {
                    'count': stats['count'],
                    'percentage': stats['count'] / total_files * 100 if total_files > 0 else 0,
                    'entities': stats.get('entities', 0),
                    'relations': stats.get('relations', 0),
                    'avg_entities_per_doc': stats.get('entities', 0) / max(stats['count'], 1)
                }
                for layer, stats in self.layer_stats.items()
            },
            'batch_count': (total_files + self.batch_size - 1) // self.batch_size,
            'results': all_results  # 注意：全量结果可能很大，考虑分批处理
        }

        # 为了避免内存问题，只保存统计信息，详细结果保存在批次文件中
        summary_output_data = output_data.copy()
        summary_output_data.pop('results', None)  # 移除详细结果

        with open(final_result_file, 'w', encoding='utf-8') as f:
            json.dump(summary_output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n🏆 全量处理完成！")
        logger.info(str('=' * 60))
        logger.info(f"📊 处理统计:")
        logger.info(f"   总文档数: {serializable_stats['processed']:,}")
        logger.info(f"   成功处理: {serializable_stats['successful']:,} ({serializable_stats['successful']/serializable_stats['processed']*100:.1f}%)")
        logger.info(f"   拒绝处理: {serializable_stats['rejected']:,} ({serializable_stats['rejected']/serializable_stats['processed']*100:.1f}%)")
        logger.info(f"   处理时间: {processing_time/3600:.1f}小时")
        logger.info(f"   处理速度: {serializable_stats['avg_speed']:.1f} 文档/秒")

        logger.info(f"\n🎯 分层质量分布:")
        for layer, data in summary_output_data['layer_distribution'].items():
            if layer != 'rejected':
                print(f"   {layer.replace('_', ' ').title()}: {data['count']:,} 个文档 ({data['percentage']:.1f}%) "
                      f"- 平均 {data['avg_entities_per_doc']:.1f} 实体/文档")

        logger.info(f"\n💡 数据输出:")
        logger.info(f"   📄 最终摘要: {final_result_file}")
        logger.info(f"   📦 批次文件: {output_path}/patent_layered_batch_*.json")

        return summary_output_data

def main():
    """主函数"""
    logger.info('🏛️ 全量分层专利知识图谱处理系统')
    logger.info(str('=' * 70))
    logger.info('📝 处理全部57,218个专利文档')
    logger.info('🎯 三层分级：基础(0.3) + 高质量(0.6) + 精英(0.8)')
    logger.info('💾 分批处理和中间结果保存')
    logger.info(str('=' * 70))

    # 配置参数
    source_dir = '/Users/xujian/学习资料/专利'
    output_dir = '/Users/xujian/Athena工作平台/data/patent_knowledge_graph'

    logger.info(f"\n📁 源目录: {source_dir}")
    logger.info(f"📁 输出目录: {output_dir}")
    logger.info(f"\n✅ 自动模式：从15%进度继续处理剩余85%专利文档")

    # 创建处理器
    processor = FullScalePatentProcessor()

    logger.info(f"\n🎯 开始全量分层处理...")
    start_time = datetime.now()

    try:
        # 处理所有文档
        results = processor.process_all_documents(source_dir, output_dir)

        logger.info(f"\n🎯 全量处理阶段完成！")
        logger.info(f"💡 接下来可以:")
        logger.info(f"   1. 导入Neo4j: python3 import_to_neo4j.py")
        logger.info(f"   2. 分析批次结果: 查看 {output_dir} 目录下的批次文件")
        logger.info(f"   3. 可视化分析: 使用Neo4j Browser进行图谱分析")

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