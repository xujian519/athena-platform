#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama专利实体识别器演示脚本
Demo for Ollama Patent Entity Recognizer
"""

import json
import logging
import os
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ollama_entity_recognizer import OllamaEntityRecognizer
except ImportError:
    logger.info('错误：无法导入 ollama_entity_recognizer.py')
    logger.info('请确保文件在当前目录中')
    sys.exit(1)

def main():
    logger.info(str('=' * 60))
    logger.info('Ollama专利实体识别器演示')
    logger.info(str('=' * 60))
    print()

    # 创建识别器
    logger.info('正在初始化识别器...')
    recognizer = OllamaEntityRecognizer(model_name='qwen2:7b')

    # 检查状态
    status = recognizer.get_status()
    print()
    logger.info('识别器状态：')
    logger.info(f"  Ollama服务: {'✓ 运行中' if status['ollama_available'] else '✗ 未运行'}")
    logger.info(f"  模型状态: {'✓ 已下载' if status['model_pulled'] else '✗ 未下载'}")
    logger.info(f"  当前模型: {status['current_model']}")
    logger.info(f"  规则模式: {status['rule_patterns']['entity_types']}种实体类型")
    print()

    # 如果Ollama不可用或模型未下载，仅使用规则模式
    use_ollama = status['ollama_available'] and status['model_pulled']
    if not use_ollama:
        logger.info('⚠️  Ollama不可用，将仅使用规则识别')
        print()

    # 演示文本
    demo_texts = [
        {
            'title': '铜铝复合阳极母线',
            'text': '1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。'
        },
        {
            'title': '高性能锂电池',
            'text': '本发明涉及一种高性能锂电池，包括正极材料、负极材料和电解液，其特征在于所述正极材料为镍钴锰酸锂，工作温度范围为-20℃至60℃，电压为3.7V。'
        },
        {
            'title': '汽车制动系统',
            'text': '一种汽车制动系统，包括制动盘（10）、制动片（20）和液压控制单元（30），其特征在于所述制动盘（10）采用碳纤维复合材料制成，厚度为25mm。'
        }
    ]

    # 处理每个演示文本
    all_results = []

    for i, demo in enumerate(demo_texts, 1):
        logger.info(f"【演示 {i}】{demo['title']}")
        logger.info(str('-' * 40))
        logger.info(str(demo['text']))
        print()

        # 识别实体
        entities = recognizer.recognize_entities(demo['text'], use_ollama=use_ollama)

        # 显示结果
        logger.info(f"识别结果（共{len(entities)}个实体）：")
        print()

        for j, entity in enumerate(entities, 1):
            source_icon = '🤖' if 'ollama' in entity.source else '⚙️'
            logger.info(f"  {j}. {entity.text}")
            logger.info(f"     类型: {entity.label}")
            logger.info(f"     位置: {entity.start}-{entity.end}")
            logger.info(f"     置信度: {entity.confidence:.2f} {source_icon}")
            if entity.attributes:
                attrs = ', '.join([f"{k}: {v}" for k, v in entity.attributes.items()])
                logger.info(f"     属性: {attrs}")
            print()

        # 保存结果
        all_results.append({
            'title': demo['title'],
            'text': demo['text'],
            'entities': [
                {
                    'text': e.text,
                    'label': e.label,
                    'start': e.start,
                    'end': e.end,
                    'confidence': e.confidence,
                    'source': e.source,
                    'attributes': e.attributes
                }
                for e in entities
            ]
        })

    # 统计信息
    logger.info(str('=' * 60))
    logger.info('统计信息')
    logger.info(str('=' * 60))

    total_entities = sum(len(r['entities']) for r in all_results)
    logger.info(f"总识别实体数: {total_entities}")

    # 按类型统计
    label_counts = {}
    for result in all_results:
        for entity in result['entities']:
            label = entity['label']
            label_counts[label] = label_counts.get(label, 0) + 1

    logger.info("\n实体类型分布:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {label}: {count}个")

    # 保存结果
    output_file = 'demo_results.json'
    result_data = {
        'demo_time': datetime.now().isoformat(),
        'recognizer_status': status,
        'results': all_results,
        'statistics': {
            'total_entities': total_entities,
            'label_distribution': label_counts
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    logger.info(f"\n✅ 演示完成！")
    logger.info(f"结果已保存到: {output_file}")
    print()
    logger.info('提示：')
    logger.info('- 如需使用Ollama模式，请确保已安装并启动Ollama')
    logger.info("- 运行 'ollama pull qwen2:7b' 下载推荐模型")
    logger.info("- 使用 'ollama list' 查看已下载的模型")

if __name__ == '__main__':
    main()