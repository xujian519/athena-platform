#!/usr/bin/env python3
"""
增强版智能实体识别器
Enhanced Intelligent Entity Recognizer

集成多种NLP技术，实现智能化的专利实体识别
作者: Athena AI系统
创建时间: 2025-12-12
版本: 2.0.0
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

# 深度学习相关

# NLP库
try:
    import jieba
    import jieba.posseg as pseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Transformer模型
try:
    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# LLaMA或其他大模型
try:
    import requests
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RecognizedEntity:
    """识别的实体"""
    text: str
    label: str
    start: int
    end: int
    confidence: float
    source: str  # 来源：rule/bert/spacy/llm
    attributes: dict[str, Any] = None

class PatentEntityRecognizer:
    """专利实体识别器"""

    def __init__(self):
        """初始化识别器"""
        self.recognizers = []
        self.domain_vocab = self._load_domain_vocabulary()
        self.patterns = self._load_entity_patterns()

        # 初始化各种识别器
        self._init_rule_based_recognizer()

        if SPACY_AVAILABLE:
            self._init_spacy_recognizer()

        if TRANSFORMERS_AVAILABLE:
            self._init_bert_recognizer()

        if API_AVAILABLE:
            self._init_llm_recognizer()

    def _load_domain_vocabulary(self) -> dict[str, list[str]:
        """加载领域词汇"""
        return {
            '部件': [
                # 通用部件
                '本体', '部件', '组件', '装置', '设备', '机构', '单元', '模块',
                # 专用部件
                '处理器', '控制器', '传感器', '执行器', '驱动器', '电机', '发动机',
                '齿轮', '轴承', '轴', '凸轮', '连杆', '曲轴', '传动轴',
                '电路板', '芯片', '集成电路', '半导体', '晶体管', '二极管',
                # 专利常见
                '母线本体', '导杆', '接触铜板', '凹槽', '电极', '触点'
            ],
            '材料': [
                # 金属材料
                '铜', '铝', '钢', '铁', '合金', '不锈钢', '铝合金', '铜合金',
                # 非金属材料
                '塑料', '橡胶', '陶瓷', '玻璃', '复合材料', '聚合物',
                # 涂层和薄膜
                '涂层', '镀层', '薄膜', '氧化层', '绝缘层'
            ],
            '位置': [
                # 基本位置
                '位置', '区域', '部位', '端部', '侧部', '中部', '顶部', '底部', '表面',
                # 技术位置
                '接触区域', '安装位置', '固定部位', '连接端', '接口', '端口'
            ],
            '结构': [
                # 基本结构
                '槽', '孔', '口', '腔', '室', '道', '管', '沟', '槽', '缝',
                '凹槽', '通孔', '盲孔', '螺纹孔', '定位孔', '安装孔',
                '凸起', '凹陷', '台阶', '倒角', '圆角'
            ],
            '参数': [
                # 物理参数
                '温度', '压力', '湿度', '速度', '频率', '功率', '电压', '电流',
                '电阻', '电容', '电感', '阻抗',
                # 几何参数
                '长度', '宽度', '高度', '厚度', '直径', '半径', '角度',
                # 化学参数
                '浓度', '纯度', 'pH值', '密度', '粘度', '硬度'
            ],
            '方法': [
                # 处理方法
                '处理', '制造', '制备', '合成', '提取', '分离', '纯化',
                '干燥', '加热', '冷却', '固化', '成型',
                # 检测方法
                '检测', '测量', '测试', '验证', '校准', '标定'
            ],
            '功能': [
                # 基本功能
                '控制', '调节', '驱动', '连接', '固定', '支撑', '导向',
                '密封', '绝缘', '导电', '传热', '散热', '缓冲',
                # 高级功能
                '识别', '判断', '处理', '计算', '分析', '优化'
            ]
        }

    def _load_entity_patterns(self) -> dict[str, list[str]:
        """加载实体识别模式"""
        return {
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
                # 带附图标记的模式
                r"([^，。；:]*?)（\d+）"
            ],
            '材料': [
                r"([^，。；:]+?]板",
                r"([^，。；:]+?]层",
                r"([^，。；:]+?]膜",
                r"([^，。；:]+?]涂层",
                r"([^，。；:]+?]材料",
                r"([^，。；:]+?]合金",
                r"([^，。；:]+?]塑料",
                r"([^，。；:]+?]橡胶"
            ],
            '位置': [
                r"([^，。；:]+?]区域",
                r"([^，。；:]+?]位置",
                r"([^，。；:]+?]部位",
                r"([^，。；:]+?]端部",
                r"([^，。；:]+?]侧部",
                r"([^，。；:]+?]中部",
                r"([^，。；:]+?]表面"
            ],
            '参数': [
                r"(\d+\.?\d*)\s*mm",
                r"(\d+\.?\d*)\s*cm",
                r"(\d+\.?\d*)\s*μm",
                r"(\d+\.?\d*)\s*℃",
                r"(\d+\.?\d*)\s*MPa",
                r"(\d+\.?\d*)\s*V",
                r"(\d+\.?\d*)\s*A"
            ]
        }

    def _init_rule_based_recognizer(self) -> Any:
        """初始化基于规则的识别器"""
        self.recognizers.append({
            'name': 'rule_based',
            'recognize_func': self._recognize_by_rules
        })

    def _init_spacy_recognizer(self) -> Any:
        """初始化Spacy识别器"""
        try:
            self.spacy_nlp = spacy.load('zh_core_web_sm')
            self.recognizers.append({
                'name': 'spacy',
                'recognize_func': self._recognize_by_spacy
            })
            logger.info('Spacy识别器初始化成功')
        except Exception as e:
            logger.warning(f"Spacy识别器初始化失败: {e}")

    def _init_bert_recognizer(self) -> Any:
        """初始化BERT识别器"""
        try:
            # 使用预训练的中文NER模型
            model_name = 'ckiplab/bert-base-chinese-ner'
            self.ner_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.ner_model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline('ner',
                                         model=self.ner_model,
                                         tokenizer=self.ner_tokenizer,
                                         aggregation_strategy='simple')
            self.recognizers.append({
                'name': 'bert',
                'recognize_func': self._recognize_by_bert
            })
            logger.info('BERT识别器初始化成功')
        except Exception as e:
            logger.warning(f"BERT识别器初始化失败: {e}")

    def _init_llm_recognizer(self) -> Any:
        """初始化大语言模型识别器"""
        # 配置LLM API（例如本地部署的LLaMA或ChatGLM）
        self.llm_config = {
            'api_url': os.getenv('LLM_API_URL', 'http://localhost:8000/v1/chat/completions'),
            'model': os.getenv('LLM_MODEL', 'chatglm3-6b'),
            'api_key': os.getenv('LLM_API_KEY', 'not-required')
        }
        self.recognizers.append({
            'name': 'llm',
            'recognize_func': self._recognize_by_llm
        })
        logger.info('LLM识别器初始化成功')

    def recognize_entities(self, text: str, use_all: bool = True) -> list[RecognizedEntity]:
        """
        识别实体

        Args:
            text: 输入文本
            use_all: 是否使用所有识别器

        Returns:
            识别的实体列表
        """
        all_entities = []

        for recognizer in self.recognizers:
            try:
                entities = recognizer['recognize_func'](text)
                # 记录来源
                for entity in entities:
                    entity.source = recognizer['name']
                all_entities.extend(entities)

                if not use_all:
                    break

            except Exception as e:
                logger.warning(f"识别器 {recognizer['name']} 运行失败: {e}")

        # 去重和融合
        fused_entities = self._fuse_entities(all_entities)

        return fused_entities

    def _recognize_by_rules(self, text: str) -> list[RecognizedEntity]:
        """基于规则识别实体"""
        entities = []

        for label, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity = RecognizedEntity(
                        text=match.group(0),
                        label=label,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.8 if label in ['部件', '材料', '位置', '结构'] else 0.6,
                        source='rule',
                        attributes={}
                    )

                    # 提取附图标记
                    ref_match = re.search(r"（(\d+)）", match.group(0))
                    if ref_match:
                        entity.attributes['reference_number'] = ref_match.group(1)

                    entities.append(entity)

        # 使用领域词汇增强
        for label, vocab_list in self.domain_vocab.items():
            for vocab in vocab_list:
                if vocab in text:
                    start = text.find(vocab)
                    entity = RecognizedEntity(
                        text=vocab,
                        label=label,
                        start=start,
                        end=start + len(vocab),
                        confidence=0.7,
                        source='rule_vocab',
                        attributes={}
                    )
                    entities.append(entity)

        return entities

    def _recognize_by_spacy(self, text: str) -> list[RecognizedEntity]:
        """使用Spacy识别实体"""
        entities = []

        doc = self.spacy_nlp(text)

        for ent in doc.ents:
            # 映射Spacy标签到专利领域标签
            patent_label = self._map_spacy_label(ent.label_)

            entity = RecognizedEntity(
                text=ent.text,
                label=patent_label,
                start=ent.start_char,
                end=ent.end_char,
                confidence=0.75,
                source='spacy',
                attributes={'spacy_label': ent.label_}
            )
            entities.append(entity)

        return entities

    def _map_spacy_label(self, spacy_label: str) -> str:
        """映射Spacy标签到专利领域标签"""
        mapping = {
            'PERSON': '人员',
            'ORG': '组织',
            'GPE': '地点',
            'PRODUCT': '产品',
            'EVENT': '事件',
            'DATE': '日期',
            'MONEY': '金额',
            'CARDINAL': '数量',
            'QUANTITY': '参数',
            'FAC': '设施',
            'LAW': '法律',
            'LANGUAGE': '语言',
            'NORP': '国籍',
            'ORDINAL': '序号',
            'PERCENT': '百分比',
            'TIME': '时间',
            'WORK_OF_ART': '作品'
        }
        return mapping.get(spacy_label, '其他')

    def _recognize_by_bert(self, text: str) -> list[RecognizedEntity]:
        """使用BERT识别实体"""
        entities = []

        # BERT NLP Pipeline
        ner_results = self.ner_pipeline(text)

        for result in ner_results:
            # 映射BERT标签到专利领域标签
            patent_label = self._map_bert_label(result['entity_group'])

            entity = RecognizedEntity(
                text=result['word'],
                label=patent_label,
                start=result['start'],
                end=result['end'],
                confidence=result['score'],
                source='bert',
                attributes={'bert_label': result['entity_group']}
            )
            entities.append(entity)

        return entities

    def _map_bert_label(self, bert_label: str) -> str:
        """映射BERT标签到专利领域标签"""
        # 根据具体的BERT模型调整映射
        mapping = {
            'B-PER': '人员',
            'I-PER': '人员',
            'B-ORG': '组织',
            'I-ORG': '组织',
            'B-LOC': '地点',
            'I-LOC': '地点',
            'B-MISC': '其他',
            'I-MISC': '其他'
        }
        return mapping.get(bert_label, '其他')

    def _recognize_by_llm(self, text: str) -> list[RecognizedEntity]:
        """使用大语言模型识别实体"""
        entities = []

        prompt = f"""
请从以下专利文本中识别技术实体，包括部件、材料、位置、参数、方法等。
请以JSON格式返回，格式如下：
{{
    'entities': [
        {{
            'text': '实体文本',
            'label': '实体类型',
            'start': 开始位置,
            'end': 结束位置,
            'description': '简要描述'
        }}
    ]
}}

专利文本：
{text[:500]}...
"""

        try:
            # 调用LLM API
            response = requests.post(
                self.llm_config['api_url'],
                json={
                    'model': self.llm_config['model'],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.1
                },
                headers={'Authorization': f"Bearer {self.llm_config['api_key']}"}
            )

            if response.status_code == 200:
                result = response.json()
                llm_entities = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')

                # 解析LLM返回的JSON
                try:
                    parsed = json.loads(llm_entities)
                    for ent in parsed.get('entities', []):
                        entity = RecognizedEntity(
                            text=ent['text'],
                            label=ent['label'],
                            start=ent.get('start', 0),
                            end=ent.get('end', 0),
                            confidence=0.85,  # LLM通常置信度较高
                            source='llm',
                            attributes={'description': ent.get('description', '')}
                        )
                        entities.append(entity)
                except json.JSONDecodeError:
                    logger.warning('LLM返回的不是有效的JSON格式')

        except Exception as e:
            logger.warning(f"LLM识别器运行失败: {e}")

        return entities

    def _fuse_entities(self, entities: list[RecognizedEntity]) -> list[RecognizedEntity]:
        """融合多个识别器的结果"""
        if not entities:
            return []

        # 按位置排序
        entities.sort(key=lambda x: (x.start, x.end))

        fused = []
        current = entities[0]

        for entity in entities[1:]:
            # 检查是否有重叠
            if self._entities_overlap(current, entity):
                # 融合实体
                current = self._merge_entities(current, entity)
            else:
                fused.append(current)
                current = entity

        fused.append(current)

        # 按置信度排序
        fused.sort(key=lambda x: x.confidence, reverse=True)

        return fused

    def _entities_overlap(self, e1: RecognizedEntity, e2: RecognizedEntity) -> bool:
        """检查两个实体是否重叠"""
        return not (e1.end <= e2.start or e2.end <= e1.start)

    def _merge_entities(self, e1: RecognizedEntity, e2: RecognizedEntity) -> RecognizedEntity:
        """合并两个实体"""
        # 选择置信度更高的标签
        if e1.confidence >= e2.confidence:
            merged = e1
        else:
            merged = e2

        # 合并属性
        if merged.attributes is None:
            merged.attributes = {}

        # 保留所有来源信息
        sources = [merged.source]
        if e1.source != e2.source:
            sources.append(e2.source)
        merged.attributes['sources'] = sources

        return merged

    def extract_entities_with_context(self, text: str, context_window: int = 50) -> list[dict[str, Any]:
        """提取实体并保留上下文"""
        entities = self.recognize_entities(text)

        results = []
        for entity in entities:
            # 获取上下文
            start_context = max(0, entity.start - context_window)
            end_context = min(len(text), entity.end + context_window)

            context = text[start_context:end_context]

            result = {
                'entity': {
                    'text': entity.text,
                    'label': entity.label,
                    'confidence': entity.confidence,
                    'source': entity.source
                },
                'position': {
                    'start': entity.start,
                    'end': entity.end
                },
                'context': {
                    'text': context,
                    'window_size': context_window
                },
                'attributes': entity.attributes or {}
            }

            results.append(result)

        return results

    def batch_recognize(self, texts: list[str], batch_size: int = 10) -> list[list[RecognizedEntity]:
        """批量识别实体"""
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_results = []

            for text in batch:
                entities = self.recognize_entities(text)
                batch_results.append(entities)

            results.extend(batch_results)

        return results

# 使用示例
if __name__ == '__main__':
    # 创建识别器
    recognizer = PatentEntityRecognizer()

    # 示例文本
    sample_text = """
    1、一种铜铝复合阳极母线，包括母线本体（1），其特征在于：所述母线本体（1）与导杆（6）的接触区域设置有凹槽（2），所述凹槽（2）内固定设置有接触铜板（4），所述接触铜板（4）与母线本体（1）表面平齐，所述接触铜板（4）宽度方向大于导杆（6）宽度。
    """

    # 识别实体
    entities = recognizer.recognize_entities(sample_text)

    # 输出结果
    logger.info('=== 智能实体识别结果 ===')
    for entity in entities:
        logger.info(f"- {entity.text} [{entity.label}] 置信度: {entity.confidence:.2f} 来源: {entity.source}")
        if entity.attributes:
            logger.info(f"  属性: {entity.attributes}")

    # 保存结果
    result = {
        'text': sample_text,
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
    }

    with open('intelligent_entity_recognition_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info("\n结果已保存到 intelligent_entity_recognition_result.json")
