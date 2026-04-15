#!/usr/bin/env python3
"""
高质量专利知识图谱构建器
High-Quality Patent Knowledge Graph Builder

利用本地NLP系统和大模型构建专利知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import aiohttp

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatentEntity:
    """专利实体"""
    entity_id: str
    entity_type: str
    entity_name: str
    normalized_name: str
    attributes: dict
    confidence: float
    source_chunk: str

@dataclass
class PatentRelation:
    """专利关系"""
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: str
    attributes: dict
    confidence: float
    source_chunk: str

class HighQualityPatentBuilder:
    """高质量专利知识图谱构建器"""

    def __init__(self):
        # NLP服务配置
        self.nlp_url = "http://localhost:8001"
        self.nlp_model = "patent_legal"  # 使用专利法律模型

        # 实体类型定义
        self.entity_types = {
            "PATENT": "专利",
            "APPLICATION": "专利申请",
            "INVENTION": "发明",
            "UTILITY_MODEL": "实用新型",
            "DESIGN": "外观设计",
            "CLAIM": "权利要求",
            "INDEPENDENT_CLAIM": "独立权利要求",
            "DEPENDENT_CLAIM": "从属权利要求",
            "PRIOR_ART": "现有技术",
            "COMPARISON_DOCUMENT": "对比文件",
            "EVIDENCE": "证据",
            "LEGAL_BASIS": "法律依据",
            "PATENT_LAW": "专利法",
            "IMPLEMENTATION_RULE": "专利法实施细则",
            "GUIDELINE": "审查指南",
            "DECISION": "决定",
            "REVIEW_DECISION": "复审决定",
            "INVALIDATION_DECISION": "无效宣告决定",
            "APPLICANT": "申请人",
            "PATENTEE": "专利权人",
            "INVENTOR": "发明人",
            "ASSIGNEE": "受让人",
            "REVIEWER": "审查员",
            "EXAMINER": "审查员",
            "BOARD": "合议组",
            "TECHNICAL_FIELD": "技术领域",
            "IPC_CLASS": "IPC分类",
            "CPC_CLASS": "CPC分类",
            "NOVELTY": "新颖性",
            "INVENTIVE_STEP": "创造性",
            "INDUSTRIAL_APPLICABILITY": "实用性",
            "DISCLOSURE": "公开不充分",
            "SUPPORT": "支持",
            "OPPOSITION": "反对",
            "INVALIDATION": "无效",
            "REVOCATION": "撤销",
            "INFRINGEMENT": "侵权",
            "LICENSING": "许可",
            "TECH_FEATURE": "技术特征",
            "PARAMETER": "参数",
            "ADVANTAGE": "优势",
            "EFFECT": "效果"
        }

        # 关系类型定义
        self.relation_types = {
            "HAS_CLAIM": "包含权利要求",
            "DEPENDS_ON": "依赖于",
            "CITES": "引用",
            "REFERENCES": "参考",
            "BASED_ON": "基于",
            "ACCORDING_TO": "根据",
            "APPLIES_TO": "适用于",
            "RELATED_TO": "相关于",
            "SIMILAR_TO": "类似于",
            "DIFFERENT_FROM": "区别于",
            "INVALIDATES": "无效",
            "MAINTAINS": "维持",
            "REVOKES": "撤销",
            "OPPOSES": "反对",
            "SUPPORTS": "支持",
            "CHALLENGES": "挑战",
            "PROVES": "证明",
            "DISPROVES": "反驳",
            "PRIORITY": "优先权",
            "FAMILY": "专利族",
            "ASSIGNED_TO": "转让给",
            "LICENSED_TO": "许可给",
            "INFRINGES": "侵犯",
            "DISCLOSES": "公开",
            "TEACHES": "教导",
            "COMBINES": "组合",
            "IMPROVES": "改进",
            "MODIFIES": "修改",
            "SUBSTITUTES": "替代",
            "REPLACES": "替换"
        }

        # 正则表达式模式
        self.patterns = {
            # 专利号模式
            "patent_number_cn": r"CN\s*(\d{9,13})\s*[A-Z]",
            "patent_number_pct": r"ZL\s*\d{9,13}\s*[A-Z]",
            "patent_application": r"(\d{9,13})\.(\d)",

            # IPC/CPC分类
            "ipc_full": r"([A-H]\d{2}[A-Z]\s*\d{1,3}/\d{2})",
            "ipc_section": r"([A-H])\s*(\d{2})",
            "cpc_full": r"([A-Y]\d{2}[A-Z]\d{1,4}/\d{2})",


            # 法律条款
            "patent_law": r"专利法第([一二三四五六七八九十百千万\d]+)条",
            "patent_rule": r"专利法实施细则第([一二三四五六七八九十百千万\d]+)条",
            "guideline": r"专利审查指南第[一二三四五六七八九十百千万\d]+部分",

            # 审查决定类型
            "decision_types": [
                r"(复审请求审查决定书)",
                r"(无效宣告请求审查决定书)",
                r"(驳回决定书)",
                r"(授予发明专利权通知书)"
            ],

            # 审理程序
            "procedures": [
                r"(口头审理)",
                r"(合议组)",
                r"(公告)",
                r"(实质审查)",
                r"(初步审查)"
            ]
        }

    async def extract_entities_with_nlp(self, text: str, chunk_id: str) -> list[PatentEntity]:
        """使用NLP服务提取实体"""
        entities = []

        try:
            # 调用NLP服务进行实体识别
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": text,
                    "task": "extract_entities",
                    "domain": "patent",
                    "model": self.nlp_model
                }

                async with session.post(
                    f"{self.nlp_url}/extract_entities",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        nlp_entities = data.get("entities", [])

                        # 转换为PatentEntity格式
                        for nlp_entity in nlp_entities:
                            entity = PatentEntity(
                                entity_id=self._generate_entity_id(nlp_entity.get("text", ""), chunk_id),
                                entity_type=nlp_entity.get("type", "UNKNOWN").upper(),
                                entity_name=nlp_entity.get("text", ""),
                                normalized_name=nlp_entity.get("normalized", ""),
                                attributes={
                                    "position": nlp_entity.get("position", 0),
                                    "context": nlp_entity.get("context", ""),
                                    "confidence_nlp": nlp_entity.get("confidence", 0.8)
                                },
                                confidence=nlp_entity.get("confidence", 0.8),
                                source_chunk=chunk_id
                            )
                            entities.append(entity)
                    else:
                        logger.warning(f"NLP实体提取失败: {response.status}")

        except Exception as e:
            logger.error(f"NLP调用失败: {e}")
            # 使用规则提取作为后备
            entities = self._extract_entities_with_rules(text, chunk_id)

        return entities

    def _extract_entities_with_rules(self, text: str, chunk_id: str) -> list[PatentEntity]:
        """使用规则提取实体（后备方案）"""
        entities = []

        # 提取专利号
        for match in re.finditer(self.patterns["patent_number_cn"], text):
            entity = PatentEntity(
                entity_id=self._generate_entity_id(match.group(), chunk_id),
                entity_type="PATENT",
                entity_name=f"CN{match.group(1)}",
                normalized_name=f"CN{match.group(1)}",
                attributes={
                    "number": match.group(1),
                    "type": "Chinese Patent"
                },
                confidence=0.9,
                source_chunk=chunk_id
            )
            entities.append(entity)

        # 提取IPC分类
        for match in re.finditer(self.patterns["ipc_full"], text):
            entity = PatentEntity(
                entity_id=self._generate_entity_id(match.group(), chunk_id),
                entity_type="IPC_CLASS",
                entity_name=match.group(),
                normalized_name=match.group().replace(" ", ""),
                attributes={
                    "section": match.group()[0],
                    "class_num": match.group()[1:3],
                    "subclass": match.group()[3],
                    "group": match.group()[5:8],
                    "version": match.group()[9:]
                },
                confidence=0.95,
                source_chunk=chunk_id
            )
            entities.append(entity)

        return entities

    async def extract_relations_with_nlp(self, text: str, entities: list[PatentEntity], chunk_id: str) -> list[PatentRelation]:
        """使用NLP服务提取关系"""
        relations = []

        try:
            # 准备实体信息
            entity_texts = [e.entity_name for e in entities]

            # 调用NLP服务进行关系提取
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": text,
                    "entities": [{"name": e.entity_name, "type": e.entity_type} for e in entities],
                    "task": "extract_relations",
                    "domain": "patent",
                    "model": self.nlp_model
                }

                async with session.post(
                    f"{self.nlp_url}/extract_relations",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        nlp_relations = data.get("relations", [])

                        # 转换为PatentRelation格式
                        for nlp_relation in nlp_relations:
                            # 查找对应的实体ID
                            subject_id = self._find_entity_id(
                                nlp_relation.get("subject", ""), entities
                            )
                            object_id = self._find_entity_id(
                                nlp_relation.get("object", ""), entities
                            )

                            if subject_id and object_id:
                                relation = PatentRelation(
                                    relation_id=self._generate_relation_id(
                                        subject_id, object_id,
                                        nlp_relation.get("type", "RELATED_TO")
                                    ),
                                    subject_id=subject_id,
                                    object_id=object_id,
                                    relation_type=nlp_relation.get("type", "RELATED_TO"),
                                    attributes={
                                        "confidence_nlp": nlp_relation.get("confidence", 0.7),
                                        "context": nlp_relation.get("context", ""),
                                        "evidence": nlp_relation.get("evidence", "")
                                    },
                                    confidence=nlp_relation.get("confidence", 0.7),
                                    source_chunk=chunk_id
                                )
                                relations.append(relation)

                    else:
                        logger.warning(f"NLP关系提取失败: {response.status}")

        except Exception as e:
            logger.error(f"NLP关系调用失败: {e}")
            # 使用规则提取作为后备
            relations = self._extract_relations_with_rules(text, entities, chunk_id)

        return relations

    def _extract_relations_with_rules(self, text: str, entities: list[PatentEntity], chunk_id: str) -> list[PatentRelation]:
        """使用规则提取关系（后备方案）"""
        relations = []
        entity_map = {e.entity_name: e for e in entities}

        # 提取法律引用关系
        for entity in entities:
            if entity.entity_type == "LEGAL_BASIS":
                # 查找相关决定
                for decision_entity in [e for e in entities if e.entity_type == "DECISION"]:
                    if self._entities_nearby(text, entity, decision_entity, 100):
                        relation = PatentRelation(
                            relation_id=self._generate_relation_id(
                                decision_entity.entity_id, entity.entity_id, "BASED_ON"
                            ),
                            subject_id=decision_entity.entity_id,
                            object_id=entity.entity_id,
                            relation_type="BASED_ON",
                            attributes={
                                "reason": "法律依据引用"
                            },
                            confidence=0.8,
                            source_chunk=chunk_id
                        )
                        relations.append(relation)

        return relations

    def _generate_entity_id(self, text: str, chunk_id: str) -> str:
        """生成实体ID"""
        content = f"{text}_{chunk_id}"
        return short_hash(content.encode())[:16]

    def _generate_relation_id(self, subject_id: str, object_id: str, relation_type: str) -> str:
        """生成关系ID"""
        content = f"{subject_id}_{object_id}_{relation_type}"
        return short_hash(content.encode())[:16]

    def _find_entity_id(self, entity_name: str, entities: list[PatentEntity]) -> str | None:
        """查找实体ID"""
        for entity in entities:
            if entity.entity_name == entity_name or entity.normalized_name == entity_name:
                return entity.entity_id
        return None

    def _entities_nearby(self, text: str, entity1: PatentEntity, entity2: PatentEntity, max_distance: int) -> bool:
        """检查两个实体是否在文本中相邻"""
        pos1 = entity1.attributes.get("position", 0)
        pos2 = entity2.attributes.get("position", 0)
        return abs(pos1 - pos2) < max_distance

    async def process_document_batch(self, docs: list[dict], output_dir: Path):
        """批量处理文档"""
        logger.info(f"开始批量处理 {len(docs)} 个文档")

        all_entities = []
        all_relations = []

        for i, doc in enumerate(docs[:100]):  # 限制处理数量
            logger.info(f"处理文档 {i+1}/{min(100, len(docs))}: {doc.get('title', 'Unknown')}")

            # 获取文档内容
            content = self._extract_content(doc)
            if not content:
                continue

            # 分块处理
            chunks = self._split_document(content)
            chunk_id_prefix = f"doc_{i}"

            # 处理每个块
            for j, chunk in enumerate(chunks):
                chunk_id = f"{chunk_id_prefix}_chunk_{j}"

                # 提取实体
                entities = await self.extract_entities_with_nlp(chunk, chunk_id)
                all_entities.extend(entities)

                # 提取关系
                relations = await self.extract_relations_with_nlp(chunk, entities, chunk_id)
                all_relations.extend(relations)

        # 统计信息
        entity_stats = Counter(e.entity_type for e in all_entities)
        relation_stats = Counter(r.relation_type for r in all_relations)

        logger.info("\n📊 处理统计:")
        logger.info(f"  总实体数: {len(all_entities)}")
        logger.info(f"  总关系数: {len(all_relations)}")

        # 保存结果
        self._save_results(all_entities, all_relations, entity_stats, relation_stats, output_dir)

    def _extract_content(self, doc: dict) -> str:
        """从文档中提取文本内容"""
        if "content" in doc:
            return doc["content"]
        elif "text" in doc:
            return doc["text"]
        elif "body" in doc:
            return doc["body"]
        elif isinstance(doc, str):
            return doc
        else:
            return json.dumps(doc, ensure_ascii=False)

    def _split_document(self, content: str, chunk_size: int = 800) -> list[str]:
        """智能分块"""
        # 按段落分块
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查是否需要分块
            if current_size + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # 保留50%重叠
                words = current_chunk.split()
                overlap_words = words[-len(words)//2:]
                current_chunk = " ".join(overlap_words) + "\n\n" + paragraph
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

    def _save_results(self, entities: list[PatentEntity], relations: list[PatentRelation],
                      entity_stats: Counter, relation_stats: Counter, output_dir: Path):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        output_dir = output_dir / "patent_knowledge_graph"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        entities_file = output_dir / f"patent_entities_{timestamp}.json"
        entities_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "高质量专利知识图谱实体",
                "total_entities": len(entities),
                "entity_types": dict(entity_stats)
            },
            "entities": [asdict(e) for e in entities]
        }
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = output_dir / f"patent_relations_{timestamp}.json"
        relations_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "高质量专利知识图谱关系",
                "total_relations": len(relations),
                "relation_types": dict(relation_stats)
            },
            "relations": [asdict(r) for r in relations]
        }
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)

        # 保存统计
        stats_file = output_dir / f"patent_stats_{timestamp}.json"
        stats = {
            "timestamp": datetime.now().isoformat(),
            "entity_types": self.entity_types,
            "relation_types": self.relation_types,
            "entity_statistics": dict(entity_stats),
            "relation_statistics": dict(relation_stats)
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("💾 数据已保存:")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  统计文件: {stats_file}")

async def main():
    """主函数"""
    print("="*100)
    print("🏗️ 高质量专利知识图谱构建器 🏗️")
    print("="*100)

    builder = HighQualityPatentBuilder()

    # 模拟文档数据
    sample_docs = [
        {
            "title": "专利复审决定 CN202000000000.0",
            "content": """
            复审请求审查决定书

            专利号：CN202000000000.0
            申请号：202000000000.0
            发明名称：一种数据处理方法

            复审请求人：某某公司
            专利权人：某某公司

            决定要点：
            基于专利法第22条第3款的规定，本申请的技术方案具有创造性。
            对比文件1：CN1099999999A公开了一种类似的技术方案。

            合议组认为，权利要求1-3具备创造性，予以支持。
            """
        }
    ]

    # 处理文档
    output_dir = Path("/Users/xujian/Athena工作平台/production/data")
    await builder.process_document_batch(sample_docs, output_dir)

    print("\n✅ 高质量专利知识图谱构建完成！")

if __name__ == "__main__":
    asyncio.run(main())
