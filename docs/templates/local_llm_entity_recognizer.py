#!/usr/bin/env python3
"""
基于本地大模型的专利实体识别器
Local LLM-based Patent Entity Recognizer

支持通过环境变量配置本地部署的大模型
作者: Athena AI系统
创建时间: 2025-12-12
版本: 1.0.0
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

import requests

# 设置日志
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
    source: str  # 'rule' 或 'llm'
    attributes: dict[str, Any] = None

class LocalLLMEntityRecognizer:
    """基于本地LLM的专利实体识别器"""

    def __init__(self):
        """初始化识别器"""
        # 初始化属性
        self.llm_config = {}
        self.entity_patterns = {}
        self.domain_vocab = {}

        # 加载环境变量配置
        self.llm_config = self._load_llm_config()

        # 初始化规则识别器
        self._init_rule_recognizer()

        # 验证LLM连接
        self.llm_available = self._test_llm_connection()

        logger.info("实体识别器初始化完成")
        logger.info("规则模式: ✓")
        logger.info(f"LLM模式: {'✓' if self.llm_available else '✗'}")

    def _load_llm_config(self) -> dict[str, Any]:
        """从环境变量加载LLM配置"""
        config = {
            'api_url': os.getenv('LLM_API_URL', ''),
            'model': os.getenv('LLM_MODEL', ''),
            'api_key': os.getenv('LLM_API_KEY', 'not-required'),
            'timeout': int(os.getenv('LLM_TIMEOUT', '30')),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.1')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '2000'))
        }

        # 支持多种本地LLM服务
        if not config['api_url']:
            # 自动检测常见的本地LLM服务
            local_services = [
                'http://localhost:8000/v1/chat/completions',  # v_llm
                'http://localhost:11434/v1/chat/completions',  # LM Studio
                'http://localhost:5000/v1/chat/completions',  # FastChat
                'http://192.168.1.100:8000/v1/chat/completions'  # 远程服务器
            ]

            for service in local_services:
                try:
                    response = requests.get(f"{service}/models", timeout=3)
                    if response.status_code == 200:
                        config['api_url'] = service
                        break
                except Exception:
                    continue

            if not config['api_url']:
                logger.warning('未检测到本地LLM服务')

        # 设置默认模型
        if not config['model']:
            config['model'] = self._get_default_model()

        return config

    def _get_default_model(self) -> str:
        """获取默认模型名称"""
        model = os.getenv('LLM_MODEL')
        if model:
            return model

        # 根据API URL推测模型
        api_url = self.llm_config.get('api_url', '')
        if 'ollama' in api_url.lower():
            return 'llama3.1:8b'  # Ollama默认
        elif 'vllm' in api_url.lower():
            return 'chatglm3-6b'  # vLLM常用模型
        else:
            return 'chatglm3-6b'  # 通用默认

    def _test_llm_connection(self) -> bool:
        """测试LLM连接"""
        if not self.llm_config['api_url']:
            return False

        try:
            test_url = f"{self.llm_config['api_url']}".replace('/chat/completions', '/models')
            response = requests.get(test_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"LLM连接测试失败: {e}")
            return False

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
                # 带附图标记
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
                # 材料名称
                r"(铜|铝|钢|铁|金|银|铂|钛|镍|锌|锡|铅)板",
                r"(铜|铝|钢|铁|金|银|铂|钛|镍|锌|锡|铅)合金",
                # 复合材料
                r"([^，。；:]+?)复合材料"
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
                r"([^，。；:]+?]固定部位",
                r"([^，。；:]+?]连接端"
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
                r"(?:凹|凸)槽",
                r"(?:通|盲)孔",
                r"(?:安装|定位|螺纹)孔",
                r"(?:密封|定位)槽"
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
                r"(?:焊接|铆接|粘接|螺栓连接)方法",
                r"(?:热处理|表面处理)工艺",
                r"(?:制造|加工|制备)过程"
            ],
            '功能': [
                r"([^，。；:]+?]功能",
                r"([^，。；:]+?]作用",
                r"([^，。；:]+?]效果",
                r"([^，。；:]+?]能力",
                # 具体功能
                r"(?:控制|调节|驱动|连接|固定|支撑)功能",
                r"(?:密封|绝缘|导电|传热)作用",
                r"(?:优化|增强|改善)效果"
            ]
        }

        # 专利领域词汇
        self.domain_vocab = {
            '部件': [
                '母线本体', '导杆', '接触铜板', '电极', '触点', '接线端子',
                '半导体芯片', '集成电路', '传感器', '执行器', '控制器',
                '处理器', '存储器', '显示器', '键盘', '鼠标',
                '齿轮', '轴承', '轴', '凸轮', '连杆', '曲轴',
                '制动器', '离合器', '传动轴', '减速器'
            ],
            '材料': [
                '铜铝复合材料', '不锈钢', '钛合金', '碳纤维', '工程塑料',
                '绝缘材料', '导电材料', '半导体材料', '磁性材料',
                '纳米材料', '复合材料', '高温合金', '超导材料',
                '环氧树脂', '硅橡胶', '陶瓷材料', '玻璃纤维'
            ],
            '方法': [
                '焊接方法', '粘接工艺', '热处理工艺', '表面处理技术',
                '3D打印', '激光加工', '电镀工艺', '喷涂工艺',
                '装配方法', '测试技术', '检测方法', '校准方法',
                '制造工艺', '加工工艺', '合成工艺', '分离工艺'
            ],
            '功能': [
                '智能控制', '自动调节', '精确测量', '实时监控',
                '高效传输', '快速响应', '稳定运行', '安全保护',
                '节能环保', '可靠耐用', '易于维护', '操作便捷'
            ]
        }

    def recognize_entities(self, text: str, use_llm: bool = None) -> list[Entity]:
        """
        识别文本中的实体

        Args:
            text: 输入文本
            use_llm: 是否使用LLM，None表示自动判断

        Returns:
            识别的实体列表
        """
        # 规则识别
        rule_entities = self._recognize_by_rules(text)

        # 决定是否使用LLM
        if use_llm is None:
            use_llm = self.llm_available

        # LLM识别
        if use_llm and self.llm_available:
            llm_entities = self._recognize_by_llm(text)
            # 合并结果
            all_entities = rule_entities + llm_entities
            # 去重和融合
            merged_entities = self._merge_entities(all_entities)
        else:
            merged_entities = rule_entities

        # 按位置排序
        merged_entities.sort(key=lambda x: x.start)

        return merged_entities

    def _recognize_by_rules(self, text: str) -> list[Entity]:
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

    def _recognize_by_llm(self, text: str) -> list[Entity]:
        """使用LLM识别实体"""
        entities = []

        # 构建提示词
        prompt = self._build_llm_prompt(text)

        try:
            # 调用LLM API
            response = self._call_llm(prompt)

            # 解析响应
            if response:
                llm_entities = self._parse_llm_response(response, text)
                entities.extend(llm_entities)

        except Exception as e:
            logger.warning(f"LLM识别失败: {e}")

        return entities

    def _build_llm_prompt(self, text: str) -> str:
        """构建LLM提示词"""
        prompt = f"""你是一个专业的专利实体识别专家。请从以下专利文本中识别所有技术实体。

实体类型包括：
1. 部件：各种组件、装置、设备、机构、单元、模块等
2. 材料：各种材料、合金、复合材料、涂层等
3. 位置：各种区域、位置、部位、端部、表面等
4. 结构：各种槽、孔、口、腔、缝、凸起、凹陷等
5. 参数：各种数值参数（长度、温度、压力、电压等）
6. 方法：各种工艺、方法、步骤、过程、技术等
7. 功能：各种功能、作用、效果、能力等

请以JSON格式返回识别结果：
{{
    'entities': [
        {{
            'text': '实体文本',
            'label': '实体类型',
            'start': 开始位置,
            'end': 结束位置,
            'confidence': 置信度(0-1),
            'description': '简要描述'
        }}
    ]
}}

专利文本：
{text[:500]}...
"""
        return prompt

    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        headers = {
            'Content-Type': 'application/json'
        }

        if self.llm_config['api_key'] != 'not-required':
            headers['Authorization'] = f"Bearer {self.llm_config['api_key']}"

        payload = {
            'model': self.llm_config['model'],
            'messages': [
                {
                    'role': 'system',
                    'content': '你是专业的专利实体识别专家，能够准确识别专利文本中的各种技术实体。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': self.llm_config['temperature'],
            'max_tokens': self.llm_config['max_tokens'],
            'stream': False
        }

        response = requests.post(
            self.llm_config['api_url'],
            headers=headers,
            json=payload,
            timeout=self.llm_config['timeout']
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.error(f"LLM API调用失败: {response.status_code}")
            return None

    def _parse_llm_response(self, response: str, original_text: str) -> list[Entity]:
        """解析LLM响应"""
        entities = []

        try:
            # 尝试解析JSON
            if '{' in response and '}' in response:
                # 提取JSON部分
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]

                parsed = json.loads(json_str)

                for ent in parsed.get('entities', []):
                    # 在原文中查找实体位置
                    text = ent['text']
                    start = original_text.find(text)

                    if start != -1:
                        entity = Entity(
                            text=text,
                            label=ent['label'],
                            start=start,
                            end=start + len(text),
                            confidence=ent.get('confidence', 0.8),
                            source='llm',
                            attributes={
                                'description': ent.get('description', '')
                            }
                        )
                        entities.append(entity)

        except json.JSONDecodeError:
            logger.warning('LLM响应不是有效的JSON格式')
        except Exception as e:
            logger.warning(f"解析LLM响应失败: {e}")

        return entities

    def _extract_attributes(self, text: str, label: str) -> dict[str, Any]:
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
            materials = ['铜', '铝', '钢', '铁', '金', '银', '钛', '镍', '锌', '锡', '铅']
            for material in materials:
                if material in text:
                    attributes['material_type'] = material
                    break

        return attributes

    def _merge_entities(self, entities: list[Entity]) -> list[Entity]:
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
                    # 如果置信度相同，优先选择LLM识别的结果
                    if entity.source == 'llm':
                        current = entity
            else:
                merged.append(current)
                current = entity

        merged.append(current)

        return merged

    def _entities_overlap(self, e1: Entity, e2: Entity) -> bool:
        """检查两个实体是否重叠"""
        return not (e1.end <= e2.start or e2.end <= e1.start)

    def get_config_status(self) -> dict[str, Any]:
        """获取配置状态"""
        status = {
            'llm_available': self.llm_available,
            'llm_config': {
                'api_url': self.llm_config['api_url'] or '未配置',
                'model': self.llm_config['model'] or '未配置',
                'timeout': self.llm_config['timeout'],
                'temperature': self.llm_config['temperature']
            },
            'rule_patterns': {
                'entity_types': len(self.entity_patterns),
                'total_patterns': sum(len(patterns) for patterns in self.entity_patterns.values())
            },
            'domain_vocab': {
                'total_vocab': sum(len(vocab) for vocab in self.domain_vocab.values())
            }
        }
        return status

# 测试和使用示例
def test_recognizer():
    """测试识别器"""
    logger.info(str('=' * 60))
    logger.info('本地LLM专利实体识别器测试')
    logger.info(str('=' * 60))

    # 创建识别器
    recognizer = LocalLLMEntityRecognizer()

    # 显示配置状态
    config_status = recognizer.get_config_status()
    logger.info("\n配置状态:")
    logger.info(f"  LLM可用性: {'✓' if config_status['llm_available'] else '✗'}")
    logger.info(f"  API地址: {config_status['llm_config']['api_url']}")
    logger.info(f"  模型: {config_status['llm_config']['model']}")
    logger.info(f"  规则模式: {config_status['rule_patterns']['entity_types']}种实体类型")
    logger.info(f"  词汇量: {config_status['domain_vocab']['total_vocab']}个术语")

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

        # 先只用规则识别
        rule_entities = recognizer.recognize_entities(text, use_llm=False)
        logger.info(f"规则识别 ({len(rule_entities)}个):")
        for entity in rule_entities:
            logger.info(f"  • {entity.text} [{entity.label}] 置信度: {entity.confidence:.2f}")

        # 如果LLM可用，使用混合识别
        if recognizer.llm_available:
            mixed_entities = recognizer.recognize_entities(text, use_llm=True)
            logger.info(f"\n混合识别 ({len(mixed_entities)}个):")
            for entity in mixed_entities:
                source_icon = '🤖' if entity.source == 'llm' else '⚙️'
                logger.info(f"  {source_icon} {entity.text} [{entity.label}] 置信度: {entity.confidence:.2f}")

        print()

if __name__ == '__main__':
    # 设置环境变量示例
    logger.info("\n环境变量配置示例:")
    logger.info('export LLM_API_URL=http://localhost:8000/v1/chat/completions')
    logger.info('export LLM_MODEL=chatglm3-6b')
    logger.info('export LLM_TIMEOUT=30')
    logger.info('export LLM_TEMPERATURE=0.1')
    logger.info('export LLM_MAX_TOKENS=2000')
    logger.info('export LLM_API_KEY=not-required')
    logger.info('')

    # 运行测试
    test_recognizer()
