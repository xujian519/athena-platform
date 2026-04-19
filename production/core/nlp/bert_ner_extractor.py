#!/usr/bin/env python3
from __future__ import annotations
"""
BERT命名实体识别模块
BERT Named Entity Recognition Module

使用BERT模型进行中文专利无效复审决定的实体抽取
支持MPS加速
"""

import asyncio
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class BertNERExtractor:
    """
    BERT命名实体识别器

    用于从专利无效复审决定中抽取结构化实体

    支持的实体类型:
    - PATENT_NUMBER: 专利号
    - PERSON: 人名(请求人、专利权人、审查员)
    - ORGANIZATION: 机构名(代理机构、法院)
    - DATE: 日期
    - LAW_ARTICLE: 法条
    - IPC_CODE: IPC分类号
    """

    def __init__(self, model_path: str | None = None, device: str = "auto"):
        """
        初始化BERT NER模型

        Args:
            model_path: 模型路径
            device: 设备 ('auto', 'mps', 'cuda', 'cpu')
        """
        self.model_path = (
            model_path
            or "/Users/xujian/Athena工作平台/models/converted/hfl/chinese-roberta-wwm-ext-large"
        )
        self.device_preference = device
        self.model = None
        self.tokenizer = None
        self._initialized = False

        # 实体类型定义
        self.entity_types = {
            "PATENT_NUMBER": "专利号",
            "PERSON": "人名",
            "ORGANIZATION": "机构名",
            "DATE": "日期",
            "LAW_ARTICLE": "法条",
            "IPC_CODE": "IPC分类号",
        }

    async def initialize(self):
        """异步初始化模型"""
        if self._initialized:
            return

        try:
            from transformers import AutoModelForTokenClassification, AutoTokenizer

            # 确定设备
            if self.device_preference == "auto":
                import torch

                if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                    logger.info("🔥 BGE-M3 NER使用MPS加速")
                elif torch.cuda.is_available():
                    self.device = "cuda"
                    logger.info("🎮 BGE-M3 NER使用CUDA加速")
                else:
                    self.device = "cpu"
                    logger.info("💻 BGE-M3 NER使用CPU")
            else:
                self.device = self.device_preference

            logger.info(f"🔄 加载BERT NER模型: {self.model_path}")

            # 加载模型和分词器
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForTokenClassification.from_pretrained(
                self.model_path, num_labels=len(self.entity_types)
            )

            self.model.to(self.device)
            self.model.eval()

            self._initialized = True
            logger.info("✅ BERT NER模型加载成功")

        except Exception as e:
            logger.error(f"❌ BERT NER模型加载失败: {e}")
            logger.info("💡 将使用基于规则的后备方案")
            self._initialize_rule_based()

    def _initialize_rule_based(self) -> Any:
        """初始化基于规则的后备方案"""
        logger.info("🔄 使用基于规则的NER")
        self.use_rule_based = True
        self._initialized = True

    async def extract_entities(
        self, text: str, entity_types: list[str] = None
    ) -> list[dict[str, Any]]:
        """
        从文本中抽取实体

        Args:
            text: 输入文本
            entity_types: 要抽取的实体类型列表,None表示全部

        Returns:
            实体列表,每个实体包含:
            - text: 实体文本
            - type: 实体类型
            - start: 起始位置
            - end: 结束位置
            - confidence: 置信度
        """
        if not self._initialized:
            await self.initialize()

        if getattr(self, "use_rule_based", False):
            return self._extract_entities_rule_based(text, entity_types)

        # TODO: 实现BERT NER
        # 暂时使用基于规则的方法
        return self._extract_entities_rule_based(text, entity_types)

    async def extract_entities_batch(
        self, texts: list[str], entity_types: list[str] | None = None
    ) -> list[list[dict[str, Any]]]:
        """
        批量从多个文本中抽取实体

        Args:
            texts: 输入文本列表
            entity_types: 要抽取的实体类型列表,None表示全部

        Returns:
            实体列表的列表,每个子列表对应一个输入文本
        """
        if not self._initialized:
            await self.initialize()

        # 并行处理多个文本
        results = await asyncio.gather(
            *[self.extract_entities(text, entity_types) for text in texts]
        )

        return results

    def _extract_entities_rule_based(
        self, text: str, entity_types: list[str] = None
    ) -> list[dict[str, Any]]:
        """基于规则的实体抽取(后备方案)"""
        entities = []

        # 如果没有指定实体类型,则抽取所有类型
        if entity_types is None:
            entity_types = list(self.entity_types.keys())

        # 1. 专利号抽取
        if "PATENT_NUMBER" in entity_types:
            patent_pattern = re.compile(r"(?:专利号\s*[::]?\s*)?[\d.]+")
            for match in patent_pattern.finditer(text):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "PATENT_NUMBER",
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.95,
                    }
                )

        # 2. 人名抽取
        if "PERSON" in entity_types:
            # 常见的中文姓氏模式
            person_patterns = [
                r"(?:无效宣告请求人|专利权人|合议组组长|主审员|参审员)\s*[]\s*([^\s\n]{2]",
            ]
            for pattern in person_patterns:
                for match in re.finditer(pattern, text):
                    name = match.group(1)
                    entities.append(
                        {
                            "text": name,
                            "type": "PERSON",
                            "start": match.start(1),
                            "end": match.end(1),
                            "confidence": 0.85,
                        }
                    )

        # 3. 日期抽取
        if "DATE" in entity_types:
            date_pattern = re.compile(r"\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{1,2}-\d{1,2}")
            for match in date_pattern.finditer(text):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "DATE",
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.98,
                    }
                )

        # 4. 法条抽取
        if "LAW_ARTICLE" in entity_types:
            law_pattern = re.compile(r"专利法\s*第\s*\d+\s*条")
            for match in law_pattern.finditer(text):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "LAW_ARTICLE",
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.99,
                    }
                )

        # 5. IPC分类号抽取
        if "IPC_CODE" in entity_types:
            ipc_pattern = re.compile(r"[A-Z]\d+[A-Z]?\d+/\d+")
            for match in ipc_pattern.finditer(text):
                entities.append(
                    {
                        "text": match.group(),
                        "type": "IPC_CODE",
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.90,
                    }
                )

        # 按起始位置排序
        entities.sort(key=lambda x: x["start"])

        return entities

    async def extract_relations(
        self, text: str, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        抽取实体间的关系

        Args:
            text: 输入文本
            entities: 实体列表

        Returns:
            关系列表,每个关系包含:
            - subject: 主体实体
            - predicate: 谓词/关系类型
            - object: 客体实体
            - confidence: 置信度
        """
        relations = []

        # 创建实体字典以便快速查找
        entity_by_type = {}
        for entity in entities:
            etype = entity["type"]
            if etype not in entity_by_type:
                entity_by_type[etype] = []
            entity_by_type[etype].append(entity)

        # 1. 决定 -> 专利 关系
        if "PATENT_NUMBER" in entity_by_type:
            patent_entities = entity_by_type["PATENT_NUMBER"]
            for patent_entity in patent_entities[:1]:  # 通常只有一个主专利号
                relations.append(
                    {
                        "subject": patent_entity["text"],
                        "predicate": "is_patent_of_decision",
                        "object": "decision",
                        "confidence": 0.95,
                    }
                )

        # 2. 人 -> 决定 关系
        if "PERSON" in entity_by_type:
            person_entities = entity_by_type["PERSON"]
            for person_entity in person_entities:
                # 根据上下文判断关系类型
                text_before = text[max(0, person_entity["start"] - 20) : person_entity["start"]]
                if "无效宣告请求人" in text_before:
                    relations.append(
                        {
                            "subject": person_entity["text"],
                            "predicate": "files_invalid_request",
                            "object": "decision",
                            "confidence": 0.90,
                        }
                    )
                elif "专利权人" in text_before:
                    relations.append(
                        {
                            "subject": person_entity["text"],
                            "predicate": "is_patent_owner",
                            "object": "decision",
                            "confidence": 0.90,
                        }
                    )
                elif "合议组组长" in text_before:
                    relations.append(
                        {
                            "subject": person_entity["text"],
                            "predicate": "is_committee_chief",
                            "object": "decision",
                            "confidence": 0.90,
                        }
                    )

        # 3. 决定 -> 法条 关系
        if "LAW_ARTICLE" in entity_by_type:
            law_entities = entity_by_type["LAW_ARTICLE"]
            for law_entity in law_entities:
                relations.append(
                    {
                        "subject": "decision",
                        "predicate": "based_on",
                        "object": law_entity["text"],
                        "confidence": 0.95,
                    }
                )

        return relations

    async def extract_entities_and_relations(self, text: str) -> dict[str, Any]:
        """
        同时抽取实体和关系

        Args:
            text: 输入文本

        Returns:
            包含entities和relations的字典
        """
        entities = await self.extract_entities(text)
        relations = await self.extract_relations(text, entities)

        return {"entities": entities, "relations": relations}


# 全局单例
_ner_instance: BertNERExtractor | None = None


async def get_ner_extractor() -> BertNERExtractor:
    """获取NER抽取器实例"""
    global _ner_instance

    if _ner_instance is None:
        _ner_instance = BertNERExtractor()
        await _ner_instance.initialize()

    return _ner_instance


# 测试代码
async def test_bert_ner():
    """测试BERT NER抽取器"""
    print("=" * 60)
    print("🧪 测试BERT NER抽取器")
    print("=" * 60)

    try:
        extractor = BertNERExtractor()
        await extractor.initialize()

        # 测试文本
        test_text = """
        决定号:第13352号
        专利号:200630196783.1
        申请日:2006年11月28日
        无效宣告请求人:叶仕民
        专利权人:郑海燕
        合议组组长:徐清平
        主审员:刘路尧
        参审员:向琳
        法律依据:专利法第23条
        """

        print(f"\n📝 测试文本:\n{test_text}")

        # 抽取实体
        result = await extractor.extract_entities_and_relations(test_text)

        print(f"\n✅ 抽取到 {len(result['entities'])} 个实体:")
        for entity in result["entities"]:
            print(f"   - {entity['type']}: {entity['text']} (置信度: {entity['confidence']:.2f})")

        print(f"\n✅ 抽取到 {len(result['relations'])} 个关系:")
        for relation in result["relations"]:
            print(f"   - {relation['subject']} {relation['predicate']} {relation['object']}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bert_ner())
