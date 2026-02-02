#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速上线的专利实体识别器
Quick Start Patent Entity Recognizer

规则 + 预训练BERT模型组合方案
作者: Athena AI系统
创建时间: 2025-12-12
版本: 1.0.0
"""

import json
import logging
import os
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 抑制警告
warnings.filterwarnings('ignore')

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 检查并安装必要的包
INSTALL_COMMANDS = """
# 安装transformers库（如果未安装）
pip install transformers torch

# 或者CPU版本
pip install transformers torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装其他依赖
pip install numpy
"""

try:
    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
    logger.info('✅ transformers库已安装')
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning('❌ transformers库未安装，将仅使用规则识别')
    logger.info('请运行以下命令安装：')
    logger.info(str(INSTALL_COMMANDS))

@dataclass
class Entity:
    """实体类"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    source: str  # 'rule' 或 'bert'
    attributes: Dict[str, Any] = None

class QuickStartEntityRecognizer:
    """快速上线的实体识别器"""

    def __init__(self, use_bert: bool = True, model_name: str = None):
        """
        初始化识别器

        Args:
            use_bert: 是否使用BERT模型
            model_name: BERT模型名称，默认使用中文NER模型
        """
        self.use_bert = use_bert and TRANSFORMERS_AVAILABLE
        self.model_name = model_name or 'ckiplab/bert-base-chinese-ner'

        # 初始化规则识别器
        self._init_rule_recognizer()

        # 初始化BERT识别器
        if self.use_bert:
            self._init_bert_recognizer()

        logger.info(f"实体识别器初始化完成 - 规则模式: ✓, BERT模式: {'✓' if self.use_bert else '✗'}")

    def _init_rule_recognizer(self):
        """初始化规则识别器"""
        # 专利领域实体模式
        self.entity_patterns = {
            '部件': [
                r"([^，。；:]+?)本体",
                r"([^，。；:]+?]部件",
                r"([^，。；:]+?]组件",
                r"([^，。；:]+?]装置",
                r"([^，。；:]+?]设备",
                r"([^，。；:]+?]机构",
                r"([^，。；:]+?]单元",
                r"([^，。；:]+?]模块",
                r"([^，。；:]+?]器",
                r"([^，。；:]+?]机",
                # 带附图标记的部件
                r"([^，。；:]*?)（\d+）"
            ],
            '材料': [
                r"([^，。；:]+?]板",
                r"([^，。；:]+?]层",
                r"([^，。；:]+?]膜",
                r"([^，。；:]+?]材料",
                r"([^，。；:]+?]合金",
                r"([^，。；:]+?]塑料",
                r"([^，。；:]+?]橡胶",
                r"([^，。；:]+?]陶瓷",
                r"([^，。；:]+?]涂层",
                # 材料名称
                r"(铜|铝|钢|铁|金|银|铂|钛|镍|锌|锡|铅)板",
                r"(铜|铝|钢|铁|金|银|铂|钛|镍|锌|锡|铅)合金"
            ],
            '位置': [
                r"([^，。；:]+?]区域",
                r"([^，。；:]+?]位置",
                r"([^，。；:]+?]部位",
                r"([^，。；:]+?]端部",
                r"([^，。；:]+?]侧部",
                r"([^，。；:]+?]中部",
                r"([^，。；:]+?]顶部",
                r"([^，。；:]+?]底部",
                r"([^，。；:]+?]表面",
                # 具体位置
                r"([^，。；:]+?]接触区域",
                r"([^，。；:]+?]安装位置",
                r"([^，。；:]+?]固定部位"
            ],
            '结构': [
                r"([^，。；:]+?]槽",
                r"([^，。；:]+?]孔",
                r"([^，。；:]+?]口",
                r"([^，。；:]+?]腔",
                r"([^，。；:]+?]室",
                r"([^，。；:]+?]道",
                r"([^，。；:]+?]管",
                r"([^，。；:]+?]沟",
                r"([^，。；:]+?]缝",
                # 具体结构
                r"(凹|凸)槽",
                r"(通|盲)孔",
                r"(安装|定位|螺纹)孔"
            ],
            '参数': [
                # 数值参数
                r"(\d+\.?\d*)\s*mm",
                r"(\d+\.?\d*)\s*cm",
                r"(\d+\.?\d*)\s*μm",
                r"(\d+\.?\d*)\s*nm",
                # 温度参数
                r"(\d+\.?\d*)\s*[℃°C]",
                # 压力参数
                r"(\d+\.?\d*)\s*MPa",
                r"(\d+\.?\d*)\s*Pa",
                r"(\d+\.?\d*)\s*k_pa",
                # 电学参数
                r"(\d+\.?\d*)\s*V",
                r"(\d+\.?\d*)\s*A",
                r"(\d+\.?\d*)\s*Ω",
                # 其他参数
                r"(\d+\.?\d*)\s*Hz",
                r"(\d+\.?\d*)\s*%",
                r"(\d+\.?\d*)\s*度"
            ],
            '方法': [
                r"([^，。；:]+?]方法",
                r"([^，。；:]+?]工艺",
                r"([^，。；:]+?]步骤",
                r"([^，。；:]+?]过程",
                r"([^，。；:]+?]技术",
                r"([^，。；:]+?]手段",
                # 具体方法
                r"(焊接|铆接|粘接|螺栓连接)方法",
                r"(热处理|表面处理)工艺",
                r"(制造|加工|制备)过程"
            ],
            '功能': [
                r"([^，。；:]+?]功能",
                r"([^，。；:]+?]作用",
                r"([^，。；:]+?]效果",
                r"([^，。；:]+?]能力",
                # 具体功能
                r"(控制|调节|驱动|连接|固定|支撑)功能",
                r"(密封|绝缘|导电|传热)作用",
                r"(优化|增强|改善)效果"
            ]
        }

        # 专利领域高频词汇
        self.domain_vocab = {
            '部件': [
                '母线本体', '导杆', '接触铜板', '电极', '触点', '接线端子',
                '半导体芯片', '集成电路', '传感器', '执行器', '控制器',
                '齿轮', '轴承', '轴', '凸轮', '连杆', '曲轴',
                '处理器', '存储器', '显示器', '键盘', '鼠标'
            ],
            '材料': [
                '铜铝复合材料', '不锈钢', '钛合金', '碳纤维', '工程塑料',
                '绝缘材料', '导电材料', '半导体材料', '磁性材料',
                '纳米材料', '复合材料', '高温合金', '超导材料'
            ],
            '方法': [
                '焊接方法', '粘接工艺', '热处理工艺', '表面处理技术',
                '3D打印', '激光加工', '电镀工艺', '喷涂工艺',
                '装配方法', '测试技术', '检测方法', '校准方法'
            ]
        }

    def _init_bert_recognizer(self):
        """初始化BERT识别器"""
        try:
            logger.info(f"正在加载BERT模型: {self.model_name}")

            # 使用CPU模式，避免GPU依赖
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)

            # 创建NER pipeline
            self.ner_pipeline = pipeline(
                'ner',
                model=self.model,
                tokenizer=self.tokenizer,
                aggregation_strategy='simple',
                device=-1  # 使用CPU
            )

            # 映射BERT标签到专利实体类型
            self.bert_label_mapping = {
                'B-PER': '人员',
                'I-PER': '人员',
                'B-ORG': '组织',
                'I-ORG': '组织',
                'B-LOC': '地点',
                'I-LOC': '地点',
                'B-MISC': '其他',
                'I-MISC': '其他',
                # 如果模型有更多标签，在这里添加映射
            }

            logger.info('✅ BERT模型加载成功')

        except Exception as e:
            logger.error(f"❌ BERT模型加载失败: {e}")
            logger.info('将仅使用规则识别器')
            self.use_bert = False

    def recognize_entities(self, text: str) -> List[Entity]:
        """
        识别文本中的实体

        Args:
            text: 输入文本

        Returns:
            识别的实体列表
        """
        # 规则识别
        rule_entities = self._recognize_by_rules(text)

        # BERT识别
        if self.use_bert:
            bert_entities = self._recognize_by_bert(text)
            # 合并结果
            all_entities = rule_entities + bert_entities
            # 去重和融合
            merged_entities = self._merge_entities(all_entities)
        else:
            merged_entities = rule_entities

        # 按位置排序
        merged_entities.sort(key=lambda x: x.start)

        return merged_entities

    def _recognize_by_rules(self, text: str) -> List[Entity]:
        """基于规则识别实体"""
        entities = []

        # 使用模式匹配
        for label, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity = Entity(
                        text=match.group(0),
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.85,  # 规则匹配置信度较高
                        source='rule'
                    )

                    # 提取属性
                    entity.attributes = self._extract_attributes(match.group(0), label)

                    entities.append(entity)

        # 使用领域词汇增强
        for label, vocab in self.domain_vocab.items():
            for term in vocab:
                start = text.find(term)
                if start != -1:
                    entity = Entity(
                        text=term,
                        label=label,
                        start=start,
                        end=start + len(term),
                        confidence=0.75,  # 词汇匹配置信度稍低
                        source='rule_vocab'
                    )
                    entities.append(entity)

        return entities

    def _recognize_by_bert(self, text: str) -> List[Entity]:
        """使用BERT识别实体"""
        entities = []

        try:
            # 使用pipeline进行NER
            results = self.ner_pipeline(text)

            for result in results:
                # 映射标签
                patent_label = self.bert_label_mapping.get(result['entity_group'], '其他')

                # 过滤掉不相关的实体类型
                if patent_label in ['其他']:
                    continue

                entity = Entity(
                    text=result['word'],
                    label=patent_label,
                    start=result['start'],
                    end=result['end'],
                    confidence=result['score'],
                    source='bert'
                )

                entities.append(entity)

        except Exception as e:
            logger.warning(f"BERT识别出错: {e}")

        return entities

    def _extract_attributes(self, text: str, label: str) -> Dict[str, Any]:
        """提取实体属性"""
        attributes = {}

        # 提取附图标记
        ref_match = re.search(r"（(\d+)）", text)
        if ref_match:
            attributes['reference_number'] = ref_match.group(1)

        # 提取数值信息
        if label == '参数':
            # 提取数值
            num_match = re.search(r"(\d+\.?\d*)", text)
            if num_match:
                attributes['value'] = float(num_match.group(1))

            # 提取单位
            unit_match = re.search(r"(mm|cm|μm|nm|℃|MPa|Pa|k_pa|V|A|Ω|Hz|%)", text)
            if unit_match:
                attributes['unit'] = unit_match.group(1)

        # 提取材料信息
        if label == '材料':
            materials = ['铜', '铝', '钢', '铁', '金', '银', '钛', '镍', '锌']
            for material in materials:
                if material in text:
                    attributes['material_type'] = material
                    break

        return attributes

    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并多个识别器的结果"""
        if not entities:
            return []

        # 按位置排序
        entities.sort(key=lambda x: (x.start, x.end))

        merged = []
        current = entities[0]

        for entity in entities[1:]:
            # 检查是否有重叠
            if self._entities_overlap(current, entity):
                # 选择置信度更高的
                if entity.confidence > current.confidence:
                    current = entity
                elif entity.confidence == current.confidence:
                    # 如果置信度相同，优先选择规则识别的结果
                    if entity.source == 'rule':
                        current = entity
            else:
                merged.append(current)
                current = entity

        merged.append(current)

        return merged

    def _entities_overlap(self, e1: Entity, e2: Entity) -> bool:
        """检查两个实体是否重叠"""
        return not (e1.end <= e2.start or e2.end <= e1.start)

    def batch_recognize(self, texts: List[str], batch_size: int = 10) -> List[List[Entity]]:
        """批量识别实体"""
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = []

            for text in batch:
                entities = self.recognize_entities(text)
                batch_results.append(entities)

            results.extend(batch_results)

            if i % (batch_size * 5) == 0:
                logger.info(f"已处理 {i + batch_size}/{len(texts)} 条文本")

        return results

    def export_entities(self, entities: List[Entity], format: str = 'json') -> str:
        """导出识别结果"""
        if format == 'json':
            result = {
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
                ],
                'statistics': {
                    'total_count': len(entities),
                    'source_distribution': self._get_source_distribution(entities),
                    'label_distribution': self._get_label_distribution(entities)
                }
            }
            return json.dumps(result, ensure_ascii=False, indent=2)

        elif format == 'csv':
            lines = ['文本,标签,开始位置,结束位置,置信度,来源,属性']
            for e in entities:
                attrs = str(e.attributes) if e.attributes else ''
                lines.append(f''{e.text}','{e.label}',{e.start},{e.end},{e.confidence},{e.source},'{attrs}'')
            return "\n".join(lines)

        else:
            return str(entities)

    def _get_source_distribution(self, entities: List[Entity]) -> Dict[str, int]:
        """获取来源分布统计"""
        distribution = {}
        for entity in entities:
            distribution[entity.source] = distribution.get(entity.source, 0) + 1
        return distribution

    def _get_label_distribution(self, entities: List[Entity]) -> Dict[str, int]:
        """获取标签分布统计"""
        distribution = {}
        for entity in entities:
            distribution[entity.label] = distribution.get(entity.label, 0) + 1
        return distribution

# 测试和使用示例
def test_recognizer():
    """测试识别器"""
    logger.info(str('=' * 60))
    logger.info('专利实体识别器测试')
    logger.info(str('=' * 60))

    # 创建识别器
    recognizer = QuickStartEntityRecognizer()

    # 测试用例
    test_cases = [
        '1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。',
        '本发明涉及一种高性能锂电池，包括正极材料、负极材料和电解液，其特征在于所述正极材料为镍钴锰酸锂，工作温度范围为-20℃至60℃，电压为3.7V。',
        '一种汽车制动系统，包括制动盘（10）、制动片（20）和液压控制单元（30），其特征在于所述制动盘（10）采用碳纤维复合材料制成，厚度为25mm。'
    ]

    # 处理测试用例
    for i, text in enumerate(test_cases, 1):
        logger.info(f"\n测试用例 {i}:")
        logger.info(str('-' * 40))
        logger.info(str(text))
        logger.info("\n识别结果:")

        entities = recognizer.recognize_entities(text)

        for entity in entities:
            logger.info(f"  • {entity.text} [{entity.label}]")
            logger.info(f"    位置: {entity.start}-{entity.end}")
            logger.info(f"    置信度: {entity.confidence:.2f}")
            logger.info(f"    来源: {entity.source}")
            if entity.attributes:
                logger.info(f"    属性: {entity.attributes}")
            print()

# 快速开始示例
def quick_start_example():
    """快速开始示例"""
    logger.info(str("\n" + '=' * 60))
    logger.info('快速开始示例')
    logger.info(str('=' * 60))

    # 1. 创建识别器
    recognizer = QuickStartEntityRecognizer()

    # 2. 输入专利文本
    patent_text = """
    本发明涉及一种智能温控系统，包括温度传感器（1）、控制器（2）和执行器（3）。
    其特征在于：所述温度传感器（1）采用热敏电阻，测量范围为0-100℃，精度为±0.5℃；
    所述控制器（2）为单片机，工作电压为5V；所述执行器（3）包括加热元件和风扇。
    """

    # 3. 识别实体
    entities = recognizer.recognize_entities(patent_text)

    # 4. 查看结果
    logger.info("\n识别的实体:")
    logger.info(str('-' * 40))
    for i, entity in enumerate(entities, 1):
        logger.info(f"{i}. {entity.text} - {entity.label} (置信度: {entity.confidence:.2f})")

    # 5. 导出结果
    logger.info("\n导出JSON格式:")
    logger.info(str('-' * 40))
    json_result = recognizer.export_entities(entities, format='json')
    logger.info(str(json_result[:500] + '...' if len(json_result)) > 500 else json_result)

    # 6. 保存到文件
    output_path = Path('patent_entities_output.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_result)
    logger.info(f"\n✅ 结果已保存到: {output_path}")

if __name__ == '__main__':
    # 安装检查
    if not TRANSFORMERS_AVAILABLE:
        logger.info("\n⚠️  检测到transformers库未安装")
        logger.info('请运行以下命令安装：')
        logger.info('pip install transformers torch')
        logger.info("\n或者使用CPU版本：")
        logger.info('pip install transformers torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu')
        logger.info("\n继续使用规则识别器...")

    # 运行测试
    test_recognizer()

    # 运行快速开始示例
    quick_start_example()