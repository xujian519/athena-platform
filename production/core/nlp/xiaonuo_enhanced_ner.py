#!/usr/bin/env python3
from __future__ import annotations
"""
小诺增强NER模块 - 集成BERT模型和专利实体识别
Enhanced NER Module with BERT and Patent Entity Support

功能特性:
1. 加载并使用 uer/roberta-base-finetuned-cluener2020-chinese 模型
2. 扩展CLUENER标签,添加专利特定实体类型
3. 充分利用Apple Silicon优化
4. 混合模式:BERT + 规则,确保高精度和鲁棒性

作者: 小诺AI团队
日期: 2025-12-28
"""

import os
import re
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Any

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class PatentEntityType(Enum):
    """专利实体类型扩展"""

    # CLUENER原有标签 (0-20)
    O = 0
    B_ADDR = 1
    I_ADDR = 2
    B_BOOK = 3
    I_BOOK = 4
    B_COMP = 5
    I_COMP = 6
    B_GAME = 7
    I_GAME = 8
    B_GOV = 9
    I_GOV = 10
    B_MOVIE = 11
    I_MOVIE = 12
    B_NAME = 13
    I_NAME = 14
    B_ORG = 15
    I_ORG = 16
    B_POS = 17
    I_POS = 18
    B_SCENE = 19
    I_SCENE = 20

    # 新增专利实体标签 (21-30)
    B_PATENT_NUM = 21  # 专利号-开始
    I_PATENT_NUM = 22  # 专利号-中间
    B_APPLICANT = 23  # 申请人-开始
    I_APPLICANT = 24  # 申请人-中间
    B_INVENTOR = 25  # 发明人-开始
    I_INVENTOR = 26  # 发明人-中间
    B_IPC_CODE = 27  # IPC分类号-开始
    I_IPC_CODE = 28  # IPC分类号-中间
    B_TECH_TERM = 29  # 技术术语-开始
    I_TECH_TERM = 30  # 技术术语-中间


@dataclass
class Entity:
    """命名实体"""

    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float
    context: str = ""


class XiaonuoEnhancedNER:
    """小诺增强NER - 支持BERT和专利实体"""

    def __init__(self, use_bert: bool = True, device: str | None = None):
        """
        初始化增强NER

        Args:
            use_bert: 是否使用BERT模型
            device: 指定设备 ('mps', 'cuda', 'cpu' 或 None自动检测)
        """
        self.use_bert = use_bert
        self.model = None
        self.tokenizer = None
        self.device = self._get_device(device)

        # CLUENER标签映射
        self.label_map = self._init_label_map()

        # 专利实体模式
        self.patent_patterns = self._init_patent_patterns()

        # 线程安全锁
        self._lock = threading.RLock()

        # 模型名称
        self.model_name = "uer/roberta-base-finetuned-cluener2020-chinese"

        # 初始化
        if use_bert:
            self._load_bert_model()
        else:
            logger.info("📝 BERT模型已禁用,使用规则模式")

    def _get_device(self, device: str) -> torch.device:
        """获取最优设备"""
        if device:
            return torch.device(device)

        # 优先检测Apple Silicon MPS
        if torch.backends.mps.is_available():
            logger.info("🍎 检测到Apple Silicon,使用MPS加速")
            return torch.device("mps")
        elif torch.cuda.is_available():
            logger.info("🚀 检测到CUDA,使用GPU加速")
            return torch.device("cuda")
        else:
            logger.info("💻 使用CPU进行推理")
            return torch.device("cpu")

    def _init_label_map(self) -> dict[int, str]:
        """初始化CLUENER标签映射"""
        return {
            0: "O",
            1: "B-ADDR",
            2: "I-ADDR",
            3: "B-BOOK",
            4: "I-BOOK",
            5: "B-COMP",
            6: "I-COMP",
            7: "B-GAME",
            8: "I-GAME",
            9: "B-GOV",
            10: "I-GOV",
            11: "B-MOVIE",
            12: "I-MOVIE",
            13: "B-NAME",
            14: "I-NAME",
            15: "B-ORG",
            16: "I-ORG",
            17: "B-POS",
            18: "I-POS",
            19: "B-SCENE",
            20: "I-SCENE",
        }

    def _init_patent_patterns(self) -> dict[str, list[re.Pattern]]:
        """初始化专利实体识别模式"""
        return {
            "PATENT_NUM": [
                # 中国专利号: CN + 年份(2-4位) + 专利类型(1/2) + 序号(8-9位) + 校验位
                re.compile(r"CN\d{2,4}[12]\d{8,9}\.?\d"),
                # PCT专利号
                re.compile(r"PCT/CN\d{4}/\d+"),
                # 通用专利号格式
                re.compile(r"(?:专利号|专利|Patent)[::]?\s*([A-Z]{2}\d{4,}[A-Z]?\d+)"),
                # 简短格式
                re.compile(r"\b\d{7,10}[A-Z]?\b(?=\s*(?:专利|号|号))"),
            ],
            "APPLICANT": [
                re.compile(r"(?:申请人|Applicant)[::]\s*([^,。\n]+)"),
                re.compile(r"(?:申请单位|Application Unit)[::]\s*([^,。\n]+)"),
            ],
            "INVENTOR": [
                re.compile(r"(?:发明人|Inventor)[::]\s*([^,。\n]+)"),
                re.compile(r"(?:设计人|Designer)[::]\s*([^,。\n]+)"),
            ],
            "IPC_CODE": [
                # IPC分类号格式: A01B 33/00
                re.compile(r"\b[A-Z]\d{2}[A-Z]\s*\d{1,4}/\d{2,4}\b"),
                re.compile(r"(?:IPC|分类号)[::]?\s*([A-Z]\d{2}[A-Z]\s*\d{1,4}/\d{2,4})"),
            ],
            "TECH_TERM": [
                # 技术术语 - 常见关键词
                re.compile(
                    r"(?:算法|模型|系统|装置|方法|技术|设备|装置|模块|组件|平台)", re.IGNORECASE
                ),
            ],
        }

    def _load_bert_model(self) -> Any:
        """加载BERT模型(优先使用本地MPS优化模型)"""
        try:
            logger.info(f"📦 加载BERT模型: {self.model_name}")
            logger.info(f"🔧 设备: {self.device}")

            # 优先使用本地MPS优化的模型
            local_model_paths = [
                # 1. 平台内转换后的MPS优化模型 - 使用本地已有的RoBERTa模型
                "/Users/xujian/Athena工作平台/models/converted/hfl/chinese-roberta-wwm-ext-large",
                "/Users/xujian/Athena工作平台/models/roberta-base-finetuned-chinanews-chinese",
                # 2. HuggingFace缓存
                os.path.expanduser(
                    "~/.cache/huggingface/hub/models--uer--roberta-base-finetuned-cluener2020-chinese/snapshots"
                ),
            ]

            model_source = None
            model_loaded = False

            # 尝试本地模型路径
            for model_path in local_model_paths:
                if os.path.exists(model_path):
                    # 检查是否是snapshots目录,需要找到实际快照
                    if "snapshots" in model_path:
                        snapshot_dirs = [
                            d
                            for d in os.listdir(model_path)
                            if os.path.isdir(os.path.join(model_path, d))
                        ]
                        if snapshot_dirs:
                            actual_path = os.path.join(model_path, snapshot_dirs[0])
                            # 支持safetensors和pytorch_model.bin格式
                            if os.path.exists(os.path.join(actual_path, "model.safetensors")) or \
                               os.path.exists(os.path.join(actual_path, "pytorch_model.bin")):
                                model_source = actual_path
                                break
                    # 支持safetensors和pytorch_model.bin格式
                    elif os.path.exists(os.path.join(model_path, "model.safetensors")) or \
                         os.path.exists(os.path.join(model_path, "pytorch_model.bin")):
                        model_source = model_path
                        break

            if model_source:
                logger.info(f"✅ 使用本地MPS优化模型: {model_source}")
                try:
                    # 加载tokenizer
                    # 安全修复: 禁用trust_remote_code防止任意代码执行
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        model_source,
                        trust_remote_code=False,  # 安全: 不执行模型中的自定义代码
                        local_files_only=True,
                    )
                    logger.info("✅ Tokenizer加载完成")

                    # 加载模型 - 使用safetensors格式
                    self.model = AutoModelForTokenClassification.from_pretrained(
                        model_source,
                        trust_remote_code=False,  # 安全: 不执行模型中的自定义代码
                        local_files_only=True,
                    )
                    self.model.to(self.device)
                    self.model.eval()
                    logger.info("✅ BERT模型加载完成")

                    # 显示模型信息
                    logger.info(f"📊 模型参数量: {self.model.num_parameters():,}")
                    if hasattr(self.model, "num_labels"):
                        logger.info(f"🏷️  标签数量: {self.model.num_labels}")

                    model_loaded = True

                except Exception as e:
                    logger.warning(f"⚠️ 本地模型加载失败: {e}")
                    model_loaded = False

            # 如果本地模型加载失败,尝试从HuggingFace下载
            if not model_loaded:
                logger.info("🌐 本地模型不可用,尝试从HuggingFace加载...")
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

                try:
                    # 安全修复: 禁用trust_remote_code防止任意代码执行
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name, trust_remote_code=False  # 安全: 不执行模型中的自定义代码
                    )
                    logger.info("✅ Tokenizer加载完成")

                    self.model = AutoModelForTokenClassification.from_pretrained(
                        self.model_name, trust_remote_code=False  # 安全: 不执行模型中的自定义代码
                    )
                    self.model.to(self.device)
                    self.model.eval()
                    logger.info("✅ BERT模型加载完成")

                    logger.info(f"📊 模型参数量: {self.model.num_parameters():,}")
                    if hasattr(self.model, "num_labels"):
                        logger.info(f"🏷️  标签数量: {self.model.num_labels}")

                    model_loaded = True

                except Exception as e:
                    logger.warning(f"⚠️ HuggingFace模型加载失败: {e}")
                    model_loaded = False

            if not model_loaded:
                raise Exception("所有模型加载方式均失败")

        except Exception as e:
            logger.warning(f"⚠️ BERT模型加载失败: {e}")
            logger.info("📝 将使用规则模式")
            self.use_bert = False
            self.model = None
            self.tokenizer = None

    def extract_entities(self, text: str) -> list[Entity]:
        """
        提取实体(混合模式:BERT + 规则)

        Args:
            text: 输入文本

        Returns:
            实体列表
        """
        entities = []

        # 1. BERT实体识别
        if self.use_bert and self.model:
            bert_entities = self._extract_bert_entities(text)
            entities.extend(bert_entities)

        # 2. 规则实体识别(专利特定)
        rule_entities = self._extract_patent_entities(text)
        entities.extend(rule_entities)

        # 3. 去重和合并
        entities = self._merge_entities(entities)

        return entities

    def _extract_bert_entities(self, text: str) -> list[Entity]:
        """使用BERT模型提取实体"""
        entities = []

        try:
            with self._lock:
                # 编码文本
                inputs = self.tokenizer(
                    text,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512,
                    padding=True,
                    return_offsets_mapping=True,
                )

                # 移动到设备
                input_tensors = {
                    k: v.to(self.device) for k, v in inputs.items() if k != "offset_mapping"
                }

                # 推理
                with torch.no_grad():
                    outputs = self.model(**input_tensors)
                    predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().numpy()

                # 解析实体
                offset_mapping = inputs["offset_mapping"][0].cpu().numpy()
                current_entity = None

                for pred_id, (start, end) in zip(predictions, offset_mapping, strict=False):
                    if start == end == 0:  # [CLS], [SEP]
                        continue

                    label = self.label_map.get(pred_id, "O")

                    if label.startswith("B-"):
                        if current_entity:
                            entities.append(current_entity)
                        current_entity = {
                            "text": text[start:end],
                            "type": label[2:],
                            "start": start,
                            "end": end,
                            "confidence": 0.9,
                        }
                    elif label.startswith("I-") and current_entity:
                        current_entity["text"] += text[start:end]
                        current_entity["end"] = end
                    else:
                        if current_entity:
                            entities.append(current_entity)
                            current_entity = None

                if current_entity:
                    entities.append(current_entity)

        except Exception as e:
            logger.error(f"❌ BERT实体提取失败: {e}")

        # 转换为Entity对象
        return [
            Entity(
                text=e["text"],
                entity_type=e["type"],
                start_pos=e["start"],
                end_pos=e["end"],
                confidence=e["confidence"],
                context=text[max(0, e["start"] - 20) : e["end"] + 20],
            )
            for e in entities
        ]

    def _extract_patent_entities(self, text: str) -> list[Entity]:
        """使用规则提取专利实体"""
        entities = []

        for entity_type, patterns in self.patent_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # 对于有分组的模式,提取分组
                    if match.groups():
                        entity_text = match.group(1).strip()
                        entity_start = match.start(1)
                        entity_end = match.end(1)
                    else:
                        entity_text = match.group()
                        entity_start = match.start()
                        entity_end = match.end()

                    entities.append(
                        Entity(
                            text=entity_text,
                            entity_type=entity_type,
                            start_pos=entity_start,
                            end_pos=entity_end,
                            confidence=0.95,  # 规则匹配置信度较高
                            context=text[max(0, entity_start - 20) : entity_end + 20],
                        )
                    )

        return entities

    def _merge_entities(self, entities: list[Entity]) -> list[Entity]:
        """合并重复实体"""
        # 按文本和类型去重,保留置信度最高的
        entity_dict = {}

        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)
            if key not in entity_dict or entity.confidence > entity_dict[key].confidence:
                entity_dict[key] = entity

        return list(entity_dict.values())

    def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "use_bert": self.use_bert,
            "device": str(self.device),
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "supported_labels": len(self.label_map),
        }


def test_enhanced_ner() -> Any:
    """测试增强NER"""
    print("🧪 测试小诺增强NER模块")
    print("=" * 50)

    # 初始化
    ner = XiaonuoEnhancedNER(use_bert=True)

    # 显示模型信息
    info = ner.get_model_info()
    print("\n📊 模型信息:")
    for key, value in info.items():
        print(f"   {key}: {value}")

    # 测试用例
    test_cases = [
        {"name": "通用实体", "text": "张三在北京的百度公司工作,邮箱是zhangsan@baidu.com"},
        {
            "name": "专利实体",
            "text": "专利号CN202310123456.7,申请人:华为技术有限公司,发明人:李明、王芳,IPC分类号:H04L 12/00",
        },
        {
            "name": "混合实体",
            "text": "阿里巴巴的工程师张伟申请了专利CN202210987654.3,涉及一种分布式算法",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n{'=' * 50}")
        print(f"📝 测试用例 {i}: {case['name']}")
        print(f"文本: {case['text']}")
        print("\n🏷️ 识别结果:")

        entities = ner.extract_entities(case["text"])

        if entities:
            for entity in entities:
                print(f"   - {entity.text}")
                print(f"     类型: {entity.entity_type}")
                print(f"     位置: {entity.start_pos}-{entity.end_pos}")
                print(f"     置信度: {entity.confidence:.2f}")
                print()
        else:
            print("   (未识别到实体)")

    print("=" * 50)
    print("✅ 测试完成!")


if __name__ == "__main__":
    test_enhanced_ner()
