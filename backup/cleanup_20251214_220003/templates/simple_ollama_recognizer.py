#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Ollama专利实体识别器
Simplified Ollama Patent Entity Recognizer
"""

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """实体类"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    source: str  # 'rule' 或 'ollama'
    attributes: Dict[str, Any] = None

class SimpleOllamaRecognizer:
    """简化的Ollama专利实体识别器"""

    def __init__(self, model_name: str = 'qwen:7b'):
        self.model_name = model_name
        self.ollama_available = False
        self.model_pulled = False

        # 初始化规则模式
        self.patterns = {
            '部件': [
                r"\w+本体",
                r"\w+部件",
                r"\w+组件",
                r"\w+装置",
                r"\w+设备",
                r"\w+传感器",
                r"\w+控制器",
                r"\w+执行器",
            ],
            '材料': [
                r"\w+材料",
                r"\w+合金",
                r"\w+塑料",
                r"\w+橡胶",
                r"\w+陶瓷",
                r"铜\w*",
                r"铝\w*",
                r"钢\w*",
                r"碳纤维\w*",
            ],
            '位置': [
                r"\w+区域",
                r"\w+位置",
                r"\w+部位",
                r"\w+端部",
                r"\w+侧部",
                r"\w+中部",
                r"\w+顶部",
                r"\w+底部",
                r"\w+表面",
            ],
            '结构': [
                r"\w+槽",
                r"\w+孔",
                r"\w+口",
                r"\w+腔",
                r"\w+室",
                r"\w+道",
                r"\w+管",
                r"\w+沟",
                r"\w+缝",
            ],
            '参数': [
                r"\d+\.?\d*\s*mm",
                r"\d+\.?\d*\s*cm",
                r"\d+\.?\d*\s*μm",
                r"\d+\.?\d*\s*℃",
                r"\d+\.?\d*\s*MPa",
                r"\d+\.?\d*\s*V",
                r"\d+\.?\d*\s*A",
                r"\d+\.?\d*\s*%",
            ],
            '方法': [
                r"\w+方法",
                r"\w+工艺",
                r"\w+步骤",
                r"\w+过程",
                r"\w+技术",
                r"\w+手段",
            ],
            '功能': [
                r"\w+功能",
                r"\w+作用",
                r"\w+效果",
                r"\w+能力",
            ]
        }

        # 检查Ollama
        self._check_ollama()

    def _check_ollama(self):
        """检查Ollama状态"""
        try:
            # 检查Ollama是否安装
            result = subprocess.run(
                ['ollama', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info(f"Ollama已安装: {result.stdout.strip()}")
                self.ollama_available = True

                # 检查模型
                self._check_model()
            else:
                logger.warning('Ollama未安装')
                self.ollama_available = False

        except Exception as e:
            logger.error(f"检查Ollama失败: {e}")
            self.ollama_available = False

    def _check_model(self):
        """检查模型是否已下载"""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                if self.model_name in result.stdout:
                    logger.info(f"模型 {self.model_name} 已下载")
                    self.model_pulled = True
                else:
                    logger.warning(f"模型 {self.model_name} 未下载")
                    self.model_pulled = False

        except Exception as e:
            logger.error(f"检查模型失败: {e}")
            self.model_pulled = False

    def recognize_entities(self, text: str, use_ollama: bool = None) -> List[Entity]:
        """识别实体"""
        # 规则识别
        rule_entities = self._recognize_by_rules(text)

        # Ollama识别
        if use_ollama is None:
            use_ollama = self.ollama_available and self.model_pulled

        if use_ollama and self.ollama_available and self.model_pulled:
            ollama_entities = self._recognize_by_ollama(text)
            all_entities = rule_entities + ollama_entities
            merged_entities = self._merge_entities(all_entities)
        else:
            merged_entities = rule_entities

        # 按位置排序
        merged_entities.sort(key=lambda x: x.start)
        return merged_entities

    def _recognize_by_rules(self, text: str) -> List[Entity]:
        """基于规则识别"""
        entities = []

        for label, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity = Entity(
                        text=match.group(0),
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.85,
                        source='rule'
                    )

                    # 提取属性
                    entity.attributes = self._extract_attributes(match.group(0), label)
                    entities.append(entity)

        return entities

    def _extract_attributes(self, text: str, label: str) -> Dict[str, Any]:
        """提取属性"""
        attributes = {}

        # 提取附图标记
        ref_match = re.search(r"（(\d+)）", text)
        if ref_match:
            attributes['reference_number'] = ref_match.group(1)

        # 提取数值和单位
        if label == '参数':
            num_match = re.search(r"(\d+\.?\d*)", text)
            if num_match:
                attributes['value'] = float(num_match.group(1))

            unit_match = re.search(r"(mm|cm|μm|℃|MPa|V|A|%)", text)
            if unit_match:
                attributes['unit'] = unit_match.group(1)

        return attributes

    def _recognize_by_ollama(self, text: str) -> List[Entity]:
        """使用Ollama识别"""
        entities = []

        prompt = f"""从以下专利文本中识别技术实体，以JSON格式返回：

实体类型：部件、材料、位置、结构、参数、方法、功能

格式：
{{
    'entities': [
        {{'text': '实体文本', 'label': '实体类型', 'confidence': 0.9}}
    ]
}}

文本：{text[:200]}...
"""

        try:
            cmd = ['ollama', 'run', self.model_name, prompt]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                entities = self._parse_ollama_response(result.stdout, text)

        except Exception as e:
            logger.warning(f"Ollama识别失败: {e}")

        return entities

    def _parse_ollama_response(self, response: str, original_text: str) -> List[Entity]:
        """解析Ollama响应"""
        entities = []

        try:
            # 提取JSON
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                data = json.loads(json_str)

                for ent in data.get('entities', []):
                    text = ent['text']
                    start_pos = original_text.find(text)

                    if start_pos != -1:
                        entity = Entity(
                            text=text,
                            label=ent['label'],
                            start=start_pos,
                            end=start_pos + len(text),
                            confidence=ent.get('confidence', 0.8),
                            source='ollama'
                        )
                        entities.append(entity)

        except Exception as e:
            logger.warning(f"解析响应失败: {e}")

        return entities

    def _merge_entities(self, entities: List[Entity]) -> List[Entity]:
        """合并实体"""
        if not entities:
            return []

        entities.sort(key=lambda x: (x.start, x.end))

        merged = []
        current = entities[0]

        for entity in entities[1:]:
            if self._entities_overlap(current, entity):
                if entity.confidence > current.confidence:
                    current = entity
                elif entity.confidence == current.confidence and entity.source == 'ollama':
                    current = entity
            else:
                merged.append(current)
                current = entity

        merged.append(current)
        return merged

    def _entities_overlap(self, e1: Entity, e2: Entity) -> bool:
        """检查重叠"""
        return not (e1.end <= e2.start or e2.end <= e1.start)

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'ollama_available': self.ollama_available,
            'model_pulled': self.model_pulled,
            'current_model': self.model_name,
        }

# 测试
def test_simple_recognizer():
    logger.info(str('=' * 60))
    logger.info('简化版Ollama专利实体识别器测试')
    logger.info(str('=' * 60))

    recognizer = SimpleOllamaRecognizer()

    status = recognizer.get_status()
    logger.info(f"\n状态:")
    logger.info(f"  Ollama: {'✓' if status['ollama_available'] else '✗'}")
    logger.info(f"  模型: {'✓' if status['model_pulled'] else '✗'} ({status['current_model']})")

    # 测试文本
    test_text = '1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。'

    logger.info(f"\n测试文本:")
    logger.info(str(test_text[:100] + '...'))

    # 识别
    entities = recognizer.recognize_entities(test_text)

    logger.info(f"\n识别结果 ({len(entities)}个):")
    for i, entity in enumerate(entities, 1):
        icon = '🤖' if entity.source == 'ollama' else '⚙️'
        logger.info(f"  {i}. {icon} {entity.text} [{entity.label}] 置信度: {entity.confidence:.2f}")
        if entity.attributes:
            attrs = ', '.join([f"{k}: {v}" for k, v in entity.attributes.items()])
            logger.info(f"     属性: {attrs}")

    logger.info("\n✅ 测试完成！")

if __name__ == '__main__':
    test_simple_recognizer()