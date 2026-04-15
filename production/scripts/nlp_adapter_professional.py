#!/usr/bin/env python3
"""
专业数据NLP适配器
Professional Data NLP Adapter

将生产环境的NLP系统适配到专业数据构建的需求

作者: Athena平台团队
创建时间: 2025-12-20
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import re

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfessionalNLPAdapter:
    """专业数据NLP适配器"""

    def __init__(self, nlp_url: str = "http://localhost:8001"):
        self.nlp_url = nlp_url
        self.session = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def encode_text(self, text: str, model: str = "patent_bert") -> list[float]:
        """文本编码（生成向量）"""
        try:
            # 使用规则生成1024维向量作为基础
            # 注意：这里使用简化的哈希向量方法，实际应用中应该使用专业的嵌入模型
            vector = self._generate_hash_vector(text)

            # 添加一些语义特征
            semantic_features = self._extract_semantic_features(text)

            # 合并向量
            full_vector = vector[:768] + semantic_features[:256]

            logger.debug(f"文本编码完成，向量维度: {len(full_vector)}")
            return full_vector

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            # 返回默认向量
            return [0.0] * 1024

    async def extract_entities(self, text: str, domain: str = "patent") -> list[dict]:
        """提取实体"""
        try:
            # 调用NLP服务进行意图分析
            async with self.session.post(
                f"{self.nlp_url}/process",
                json={
                    "text": text,
                    "user_id": f"entity_extraction_{domain}",
                    "session_id": "extraction_session"
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    nlp_result = await response.json()
                    intent = nlp_result.get('intent', '').lower()
                    confidence = nlp_result.get('confidence', 0.0)

                    # 基于NLP结果和规则提取实体
                    entities = self._extract_entities_with_rules(text, domain, intent)

                    # 添加NLP置信度信息
                    for entity in entities:
                        entity['nlp_confidence'] = confidence
                        entity['nlp_intent'] = intent

                    return entities
                else:
                    # 仅使用规则提取
                    return self._extract_entities_with_rules(text, domain)

        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            # 降级到纯规则提取
            return self._extract_entities_with_rules(text, domain)

    async def extract_relations(self, text: str, entities: list[dict], domain: str = "patent") -> list[dict]:
        """提取关系"""
        try:
            # 调用NLP服务分析上下文
            async with self.session.post(
                f"{self.nlp_url}/process",
                json={
                    "text": text,
                    "user_id": f"relation_extraction_{domain}",
                    "session_id": "relation_session"
                },
                timeout=30
            ) as response:
                if response.status == 200:
                    nlp_result = await response.json()
                    context_info = {
                        "intent": nlp_result.get('intent', ''),
                        "dev/tools": nlp_result.get('selected_tools', []),
                        "confidence": nlp_result.get('confidence', 0.0)
                    }

                    # 基于上下文和规则提取关系
                    relations = self._extract_relations_with_rules(text, entities, domain, context_info)
                    return relations
                else:
                    return self._extract_relations_with_rules(text, entities, domain)

        except Exception as e:
            logger.error(f"关系提取失败: {e}")
            return self._extract_relations_with_rules(text, entities, domain)

    async def smart_chunk(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
        """智能分块"""
        # 使用规则分块，结合语义边界
        chunks = self._semantic_chunking(text, chunk_size, overlap)

        # 对每个块进行NLP分析
        analyzed_chunks = []
        for i, chunk_text in enumerate(chunks):
            try:
                async with self.session.post(
                    f"{self.nlp_url}/process",
                    json={
                        "text": chunk_text,
                        "user_id": "chunking",
                        "session_id": f"chunk_{i}"
                    },
                    timeout=10
                ) as response:
                    if response.status == 200:
                        nlp_result = await response.json()

                        analyzed_chunks.append({
                            "chunk_id": f"chunk_{i}",
                            "content": chunk_text,
                            "metadata": {
                                "chunk_index": i,
                                "char_count": len(chunk_text),
                                "intent": nlp_result.get('intent', ''),
                                "confidence": nlp_result.get('confidence', 0.0),
                                "keywords": self._extract_keywords(chunk_text)
                            }
                        })
                    else:
                        analyzed_chunks.append({
                            "chunk_id": f"chunk_{i}",
                            "content": chunk_text,
                            "metadata": {
                                "chunk_index": i,
                                "char_count": len(chunk_text)
                            }
                        })
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                # 如果NLP失败，只保存基本分块信息
                analyzed_chunks.append({
                    "chunk_id": f"chunk_{i}",
                    "content": chunk_text,
                    "metadata": {
                        "chunk_index": i,
                        "char_count": len(chunk_text)
                    }
                })

        return analyzed_chunks

    def _generate_hash_vector(self, text: str) -> list[float]:
        """生成哈希向量（后备方案）"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        vector = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            val = int(hex_pair, 16) / 255.0
            vector.append(val)

        # 扩展到所需维度
        while len(vector) < 1024:
            vector.extend(vector[:1024 - len(vector)])
        return vector[:1024]

    def _extract_semantic_features(self, text: str) -> list[float]:
        """提取语义特征"""
        features = []

        # 特征1：文本长度归一化
        text_len = len(text)
        features.append(min(text_len / 10000, 1.0))

        # 特征2：数字比例
        num_chars = sum(c.isdigit() for c in text)
        features.append(num_chars / max(len(text), 1))

        # 特征3：大写字母比例（英文）
        upper_chars = sum(c.isupper() for c in text)
        features.append(upper_chars / max(len(text), 1))

        # 特征4：关键词密度
        keywords = ["发明", "专利", "技术", "方法", "系统", "装置", "权利要求"]
        keyword_count = sum(text.count(k) for k in keywords)
        features.append(min(keyword_count / 10, 1.0))

        # 特征5-256：其他特征
        for _i in range(252):
            features.append(0.0)

        return features

    def _extract_entities_with_rules(self, text: str, domain: str, intent: str = "") -> list[dict]:
        """使用规则提取实体"""
        entities = []

        if domain == "patent" or domain == "patent_review":
            # 专利号
            patent_patterns = [
                r"CN(\d{9,13})\.?\d*[A-Z]?",
                r"ZL\s*(\d{9,13})\.?\d*[A-Z]?",
                r"(\d{9,13})\.(\d)"
            ]
            for pattern in patent_patterns:
                for match in re.finditer(pattern, text):
                    entities.append({
                        "text": match.group(),
                        "type": "PATENT_NUMBER",
                        "position": match.start(),
                        "confidence": 0.9
                    })

            # IPC分类号
            ipc_pattern = r"([A-H]\d{2}[A-Z](?:\s*\d{1,3}/\d{2})?)"
            for match in re.finditer(ipc_pattern, text):
                entities.append({
                    "text": match.group(),
                    "type": "IPC_CLASS",
                    "position": match.start(),
                    "confidence": 0.95
                })

            # 法律条款
            law_pattern = r"专利法第([一二三四五六七八九十百千万\d]+)条"
            for match in re.finditer(law_pattern, text):
                entities.append({
                    "text": match.group(),
                    "type": "LEGAL_BASIS",
                    "position": match.start(),
                    "confidence": 0.9
                })

            # 技术特征
            tech_features = ["技术方案", "技术特征", "技术效果", "技术领域", "背景技术"]
            for feature in tech_features:
                if feature in text:
                    pos = text.find(feature)
                    entities.append({
                        "text": feature,
                        "type": "TECH_FEATURE",
                        "position": pos,
                        "confidence": 0.7
                    })

        elif domain == "ipc":
            # IPC相关的实体
            entities.extend(self._extract_ipc_entities(text))

        elif domain == "technical_dictionary":
            # 技术术语
            entities.extend(self._extract_technical_terms(text))

        # 去重
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity["text"], entity["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def _extract_ipc_entities(self, text: str) -> list[dict]:
        """提取IPC相关实体"""
        entities = []

        # IPC分类号
        ipc_full_pattern = r"([A-H])(\d{2})([A-Z])\s*(\d{1,3})/(\d{2})"
        for match in re.finditer(ipc_full_pattern, text):
            entities.append({
                "text": f"{match.group(1)}{match.group(2)}{match.group(3)} {match.group(4)}/{match.group(5)}",
                "type": "IPC_FULL",
                "position": match.start(),
                "confidence": 0.95
            })

        # 技术领域
        tech_areas = ["人类生活必需", "作业；运输", "化学；冶金", "纺织；造纸",
                     "固定建筑物", "机械工程", "物理", "电学"]
        for area in tech_areas:
            if area in text:
                entities.append({
                    "text": area,
                    "type": "TECH_AREA",
                    "position": text.find(area),
                    "confidence": 0.8
                })

        return entities

    def _extract_technical_terms(self, text: str) -> list[dict]:
        """提取技术术语"""
        entities = []

        # 英文术语模式
        english_pattern = r"\b([A-Z][a-z_a-Z\s\-]+)\b"
        for match in re.finditer(english_pattern, text):
            term = match.group().strip()
            if len(term) > 2:  # 过滤短词
                entities.append({
                    "text": term,
                    "type": "ENGLISH_TERM",
                    "position": match.start(),
                    "confidence": 0.6
                })

        # 定义模式
        definition_patterns = ["是指", "定义为", "指的是", "即", "也就是"]
        for pattern in definition_patterns:
            if pattern in text:
                parts = text.split(pattern)
                if len(parts) >= 2:
                    term = parts[0].strip()
                    if term:
                        entities.append({
                            "text": term,
                            "type": "DEFINED_TERM",
                            "position": 0,
                            "confidence": 0.8
                        })

        return entities

    def _extract_relations_with_rules(self, text: str, entities: list[dict],
                                     domain: str, context: dict = None) -> list[dict]:
        """使用规则提取关系"""
        relations = []

        # 实体位置映射
        entity_positions = {e["position"]: e for e in entities}

        # 基于位置邻近性的关系
        sorted_entities = sorted(entities, key=lambda x: x["position"])

        for i, entity1 in enumerate(sorted_entities):
            for entity2 in sorted_entities[i+1:]:
                distance = entity2["position"] - entity1["position"]

                # 在一定距离内的实体可能有关联
                if distance < 200:
                    # 根据实体类型推断关系
                    relation_type = self._infer_relation_type(entity1, entity2, domain)

                    if relation_type:
                        relations.append({
                            "subject": entity1["text"],
                            "object": entity2["text"],
                            "type": relation_type,
                            "confidence": max(0.5, 1.0 - distance / 200),
                            "distance": distance
                        })

        # 基于文本模式的关系
        if domain == "patent":
            relations.extend(self._extract_patent_relations(text, entities))

        return relations

    def _infer_relation_type(self, entity1: dict, entity2: dict, domain: str) -> str | None:
        """推断关系类型"""
        type1, type2 = entity1["type"], entity2["type"]

        # 专利领域的关系推断
        if domain == "patent":
            if type1 == "PATENT_NUMBER" and type2 in ["TECH_FEATURE", "LEGAL_BASIS"]:
                return "HAS_FEATURE"
            elif type1 == "LEGAL_BASIS" and type2 == "PATENT_NUMBER":
                return "APPLIES_TO"
            elif type1 == "IPC_CLASS" and type2 == "TECH_FEATURE":
                return "CLASSIFIES"

        # IPC领域的关系推断
        elif domain == "ipc":
            if type1 == "TECH_AREA" and type2 == "IPC_FULL":
                return "CONTAINS"

        return "RELATED_TO"

    def _extract_patent_relations(self, text: str, entities: list[dict]) -> list[dict]:
        """提取专利特定的关系"""
        relations = []

        # 查找"基于"、"根据"、"按照"等模式
        pattern_words = ["基于", "根据", "按照", "依据"]
        for word in pattern_words:
            if word in text:
                # 在模式前后查找实体
                pos = text.find(word)
                before_entities = [e for e in entities if e["position"] < pos]
                after_entities = [e for e in entities if e["position"] > pos]

                if before_entities and after_entities:
                    relations.append({
                        "subject": after_entities[0]["text"],
                        "object": before_entities[0]["text"],
                        "type": "BASED_ON",
                        "confidence": 0.7
                    })

        return relations

    def _semantic_chunking(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """语义分块"""
        chunks = []

        # 按段落分割
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查是否需要新块
            if current_size + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())

                # 保留重叠
                if overlap > 0:
                    words = current_chunk.split()
                    overlap_words = words[-len(words)//4:]  # 保留25%的词
                    current_chunk = " ".join(overlap_words) + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size = len(current_chunk)
            else:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += len(paragraph)

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 专利相关关键词
        patent_keywords = [
            "发明", "实用新型", "外观设计", "专利权", "专利申请",
            "权利要求", "说明书", "附图", "摘要", "技术方案",
            "现有技术", "对比文件", "创造性", "新颖性", "实用性",
            "专利法", "实施细则", "审查指南"
        ]

        keywords = []
        text_lower = text.lower()
        for keyword in patent_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords[:10]  # 最多返回10个

# 使用示例
async def example_usage():
    """使用示例"""
    adapter = ProfessionalNLPAdapter()

    async with adapter:
        # 文本编码
        text = "一种数据处理方法，包括数据接收、预处理和优化算法处理步骤。"
        vector = await adapter.encode_text(text)
        print(f"向量维度: {len(vector)}")

        # 实体提取
        entities = await adapter.extract_entities(text, "patent")
        print(f"提取实体: {entities}")

        # 关系提取
        relations = await adapter.extract_relations(text, entities, "patent")
        print(f"提取关系: {relations}")

        # 智能分块
        long_text = text * 10  # 模拟长文本
        chunks = await adapter.smart_chunk(long_text)
        print(f"分块数: {len(chunks)}")

if __name__ == "__main__":
    asyncio.run(example_usage())
