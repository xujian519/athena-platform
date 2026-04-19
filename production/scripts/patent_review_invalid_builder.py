#!/usr/bin/env python3
"""
专利复审无效知识图谱构建器
Patent Review and Invalidity Knowledge Graph Builder

构建专业的专利复审和无效决策知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

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
    attributes: dict
    source_document: str
    confidence: float

@dataclass
class PatentRelation:
    """专利关系"""
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: str
    attributes: dict
    source_document: str
    confidence: float

class PatentReviewInvalidBuilder:
    """专利复审无效知识图谱构建器"""

    def __init__(self):
        # 专利实体类型
        self.entity_types = {
            "PATENT": "专利",
            "APPLICATION": "专利申请",
            "CLAIM": "权利要求",
            "PRIOR_ART": "对比文件/现有技术",
            "DECISION": "决定",
            "EVIDENCE": "证据",
            "LEGAL_BASIS": "法律依据",
            "REVIEWER": "审查员",
            "APPLICANT": "申请人",
            "IPC_CLASS": "IPC分类",
            "TECH_FIELD": "技术领域",
            "INFRINGEMENT": "侵权",
            "NOVELTY": "新颖性",
            "INVENTIVE_STEP": "创造性",
            "INDUSTRIAL_APPLICABILITY": "实用性"
        }

        # 专利关系类型
        self.relation_types = {
            "HAS_CLAIM": "包含权利要求",
            "CITES_PRIOR_ART": "引用对比文件",
            "BASED_ON": "基于证据",
            "ACCORDING_TO": "根据法律依据",
            "MADE_BY": "由...做出",
            "APPLIED_FOR": "申请人为",
            "BELONGS_TO": "属于",
            "AFFECTS": "影响",
            "DECLARES": "宣告",
            "REVIEWS": "审查",
            "INVALIDATES": "无效",
            "MAINTAINS": "维持",
            "MODIFIES": "修改",
            "OPPOSES": "反对",
            "CHALLENGES": "挑战",
            "SUPPORTS": "支持",
            "PROVES": "证明"
        }

        # 正则表达式模式
        self.patterns = {
            # 专利号模式
            "patent_number": r"CN(\d{9,13})[A-Z]|CN\s*\d{9,13}\s*[A-Z]|\d{9,13}[A-Z]",
            "application_number": r"CN(\d{9,13})\.\d",

            # IPC分类号
            "ipc_class": r"[A-H]\d{2}[A-Z]\s*\d{1,3}/\d{2}|[A-H]\d{2}[A-Z]\s*\d{1,3}",

            # 法律条款
            "patent_law": r"专利法第([一二三四五六七八九十百千万]+)条",
            "implementation_rule": r"专利法实施细则第([一二三四五六七八九十百千万]+)条",

            # 决定类型
            "decision_type": r"(宣告专利无效|维持专利权有效|部分无效|全部无效)",

            # 审查程序
            "procedures": [
                r"(复审|无效宣告请求|口头审理|合议审查)",
                r"(驳回决定|授权决定|撤回)"
            ]
        }

        # 法律依据关键词
        self.legal_basis_keywords = [
            "专利法第22条第3款", "新颖性", "创造性", "实用性",
            "专利法第26条第3款", "公开不充分",
            "专利法第33条", "修改超出原申请范围",
            "专利法实施细则第20条第2款", "权利要求不清楚"
        ]

    def extract_patent_entities(self, text: str, doc_id: str) -> list[PatentEntity]:
        """提取专利实体"""
        entities = []

        # 提取专利号
        for match in re.finditer(self.patterns["patent_number"], text):
            entity = PatentEntity(
                entity_id=self._generate_id(f"patent_{match.group()}", doc_id),
                entity_type="PATENT",
                entity_name=match.group(),
                attributes={
                    "type": "patent_number",
                    "position": match.start(),
                    "context": text[max(0, match.start()-50):match.end()+50]
                },
                source_document=doc_id,
                confidence=0.95
            )
            entities.append(entity)

        # 提取IPC分类
        for match in re.finditer(self.patterns["ipc_class"], text):
            entity = PatentEntity(
                entity_id=self._generate_id(f"ipc_{match.group()}", doc_id),
                entity_type="IPC_CLASS",
                entity_name=match.group(),
                attributes={
                    "section": match.group()[0],
                    "description": self._get_ipc_description(match.group())
                },
                source_document=doc_id,
                confidence=0.9
            )
            entities.append(entity)

        # 提取法律依据
        for match in re.finditer(self.patterns["patent_law"], text):
            entity = PatentEntity(
                entity_id=self._generate_id(f"law_{match.group()}", doc_id),
                entity_type="LEGAL_BASIS",
                entity_name=match.group(),
                attributes={
                    "article": match.group(1),
                    "law": "专利法"
                },
                source_document=doc_id,
                confidence=0.9
            )
            entities.append(entity)

        # 提取决定类型
        for match in re.finditer(self.patterns["decision_type"], text):
            entity = PatentEntity(
                entity_id=self._generate_id(f"decision_{match.group()[:10]}", doc_id),
                entity_type="DECISION",
                entity_name=match.group(),
                attributes={
                    "decision_category": self._classify_decision(match.group())
                },
                source_document=doc_id,
                confidence=0.85
            )
            entities.append(entity)

        return entities

    def extract_patent_relations(self, text: str, entities: list[PatentEntity], doc_id: str) -> list[PatentRelation]:
        """提取专利关系"""
        relations = []

        # 构建实体位置映射
        entity_positions = {e.entity_name: e for e in entities}

        # 提取对比文件引用关系
        for i in range(len(entities) - 1):
            current_entity = entities[i]
            next_entity = entities[i + 1]

            # 检查是否是对比文件引用
            if (current_entity.entity_type == "PATENT" and
                any(word in text[current_entity.attributes.get("position", 0):next_entity.attributes.get("position", 0)]
                    for word in ["对比文件", "现有技术", "prior art"])):

                relation = PatentRelation(
                    relation_id=self._generate_id(f"cites_{current_entity.entity_id}_{next_entity.entity_id}", doc_id),
                    subject_id=current_entity.entity_id,
                    object_id=next_entity.entity_id,
                    relation_type="CITES_PRIOR_ART",
                    attributes={
                        "citation_type": "negative_prior_art",
                        "context": text[current_entity.attributes.get("position", 0)-30:next_entity.attributes.get("position", 0)+30]
                    },
                    source_document=doc_id,
                    confidence=0.8
                )
                relations.append(relation)

        # 提取法律依据关系
        for legal_entity in [e for e in entities if e.entity_type == "LEGAL_BASIS"]:
            # 查找附近的决定实体
            decision_entities = [e for e in entities if e.entity_type == "DECISION"]

            for decision in decision_entities:
                distance = abs(legal_entity.attributes.get("position", 0) - decision.attributes.get("position", 0))
                if distance < 200:  # 200个字符内认为是相关
                    relation = PatentRelation(
                        relation_id=self._generate_id(f"based_on_{decision.entity_id}_{legal_entity.entity_id}", doc_id),
                        subject_id=decision.entity_id,
                        object_id=legal_entity.entity_id,
                        relation_type="BASED_ON",
                        attributes={
                            "basis_type": "legal_ground",
                            "distance": distance
                        },
                        source_document=doc_id,
                        confidence=0.75
                    )
                    relations.append(relation)

        return relations

    def _generate_id(self, content: str, doc_id: str) -> str:
        """生成唯一ID"""
        combined = f"{content}_{doc_id}"
        return short_hash(combined.encode())[:16]

    def _get_ipc_description(self, ipc_code: str) -> str:
        """获取IPC分类描述"""
        # 简化的IPC描述映射
        ipc_descriptions = {
            "A": "人类生活必需",
            "B": "作业；运输",
            "C": "化学；冶金",
            "D": "纺织；造纸",
            "E": "固定建筑物",
            "F": "机械工程；照明；加热；武器；爆破",
            "G": "物理",
            "H": "电学"
        }

        if ipc_code and ipc_code[0] in ipc_descriptions:
            return ipc_descriptions[ipc_code[0]]
        return "未分类"

    def _classify_decision(self, decision_text: str) -> str:
        """分类决定类型"""
        if "无效" in decision_text:
            return "invalidation"
        elif "有效" in decision_text or "维持" in decision_text:
            return "maintenance"
        elif "部分" in decision_text:
            return "partial"
        else:
            return "other"

    def process_documents(self, data_dir: Path) -> tuple[list[PatentEntity], list[PatentRelation]]:
        """处理文档"""
        logger.info(f"开始处理专利文档: {data_dir}")

        all_entities = []
        all_relations = []

        # 查找文档
        doc_files = []
        for pattern in ["**/*.json", "**/*.txt", "**/*.md"]:
            doc_files.extend(data_dir.glob(pattern))

        logger.info(f"找到 {len(doc_files)} 个文档")

        for doc_path in doc_files[:100]:  # 限制处理数量
            logger.info(f"处理文档: {doc_path.name}")

            try:
                # 读取文档
                if doc_path.suffix == '.json':
                    with open(doc_path, encoding='utf-8') as f:
                        data = json.load(f)
                        text = str(data)  # 简化处理，实际应该提取特定字段
                else:
                    with open(doc_path, encoding='utf-8') as f:
                        text = f.read()

                # 提取实体
                entities = self.extract_patent_entities(text, str(doc_path))
                all_entities.extend(entities)

                # 提取关系
                relations = self.extract_patent_relations(text, entities, str(doc_path))
                all_relations.extend(relations)

            except Exception as e:
                logger.error(f"处理文档失败 {doc_path}: {e}")

        # 统计信息
        entity_stats = Counter(e.entity_type for e in all_entities)
        relation_stats = Counter(r.relation_type for r in all_relations)

        logger.info("\n📊 处理统计:")
        logger.info(f"  总实体数: {len(all_entities)}")
        logger.info(f"  总关系数: {len(all_relations)}")
        logger.info("\n  实体类型分布:")
        for entity_type, count in entity_stats.most_common():
            logger.info(f"    {entity_type}: {count}")
        logger.info("\n  关系类型分布:")
        for relation_type, count in relation_stats.most_common():
            logger.info(f"    {relation_type}: {count}")

        return all_entities, all_relations

    def save_knowledge_graph(self, entities: list[PatentEntity], relations: list[PatentRelation], output_dir: Path):
        """保存知识图谱"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        output_dir = Path(output_dir) / "patent_review_invalid"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        entities_file = output_dir / f"patent_entities_{timestamp}.json"
        entities_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "专利复审无效知识图谱实体",
                "total_entities": len(entities)
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
                "description": "专利复审无效知识图谱关系",
                "total_relations": len(relations)
            },
            "relations": [asdict(r) for r in relations]
        }
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)

        # 保存统计信息
        stats_file = output_dir / f"patent_stats_{timestamp}.json"
        stats = {
            "timestamp": datetime.now().isoformat(),
            "entity_types": dict(Counter(e.entity_type for e in entities)),
            "relation_types": dict(Counter(r.relation_type for r in relations)),
            "entity_type_definitions": self.entity_types,
            "relation_type_definitions": self.relation_types
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 数据已保存到: {output_dir}")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  统计文件: {stats_file}")

        return entities_file, relations_file

def main():
    """主函数"""
    print("="*100)
    print("📋 专利复审无效知识图谱构建器 📋")
    print("="*100)

    builder = PatentReviewInvalidBuilder()

    # 数据目录
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/patent_data")  # 假设的数据目录

    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        logger.info("请将专利数据放入该目录，或修改数据路径")
        return

    # 处理文档
    entities, relations = builder.process_documents(data_dir)

    # 保存知识图谱
    output_dir = Path("/Users/xujian/Athena工作平台/production/data/knowledge_graph")
    builder.save_knowledge_graph(entities, relations, output_dir)

    print("\n✅ 专利复审无效知识图谱构建完成！")

if __name__ == "__main__":
    main()
