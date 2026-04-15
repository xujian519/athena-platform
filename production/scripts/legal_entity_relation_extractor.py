#!/usr/bin/env python3
"""
法律实体关系提取器
Legal Entity-Relation Extractor

深度提取法律文档中的实体和关系

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
class LegalEntity:
    """法律实体"""
    entity_id: str
    entity_name: str
    entity_type: str
    aliases: list[str]
    attributes: dict
    context: str
    source_chunk: str
    confidence: float

@dataclass
class LegalRelation:
    """法律关系"""
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: str
    attributes: dict
    context: str
    source_chunk: str
    confidence: float

class LegalEntityRelationExtractor:
    """法律实体关系提取器"""

    def __init__(self):
        # 实体类型定义
        self.entity_types = {
            "PERSON": "人物",           # 自然人
            "ORG": "机构",             # 机构组织
            "LAW": "法律法规",         # 法律法规名称
            "ARTICLE": "条款",         # 法律条款
            "TIME": "时间",           # 时间日期
            "LOCATION": "地点",       # 地点
            "CONCEPT": "法律概念",     # 法律概念
            "RIGHT": "权利",          # 权利
            "OBLIGATION": "义务",      # 义务
            "PENALTY": "处罚",        # 处罚
            "CONDITION": "条件",      # 条件
            "PROCEDURE": "程序",      # 程序
        }

        # 关系类型定义
        self.relation_types = {
            "DEFINE": "定义关系",
            "REGULATE": "规范关系",
            "GRANT": "授予关系",
            "IMPOSE": "施加关系",
            "REQUIRE": "要求关系",
            "PROHIBIT": "禁止关系",
            "PERMIT": "允许关系",
            "REFERENCE": "引用关系",
            "AMEND": "修改关系",
            "REPEAL": "废止关系",
            "ESTABLISH": "设立关系",
            "SUPERVISE": "监督关系",
            "ENFORCE": "执行关系",
            "APPEAL": "申诉关系",
            "TRANSFER": "转移关系",
            "INHERIT": "继承关系",
            "COMPENSATE": "补偿关系",
        }

        # 实体识别模式
        self.entity_patterns = {
            "PERSON": [
                r'([^\s，。；！？、]+)(?:公民|个人|自然人|当事人|申请人|被申请人|被告人|原告人|受害人)',
                r'(?:公民|个人|自然人|当事人)([^\s，。；！？、]+)',
            ],
            "ORG": [
                r'(国务院|全国人民代表大会|最高人民法院|最高人民检察院|[\u4e00-\u9fff]+部|[\u4e00-\u9fff]+委员会|[\u4e00-\u9fff]+局|[\u4e00-\u9fff]+署|[\u4e00-\u9fff]+办公室)',
                r'([^\s，。；！？、]+)(?:公司|企业|机构|组织|协会|基金会|中心|研究院)',
            ],
            "LAW": [
                r'《([^》]+(?:法|条例|规定|办法|细则|解释|决定|决议))》',
            ],
            "ARTICLE": [
                r'第([一二三四五六七八九十百千万\d]+)条',
            ],
            "TIME": [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'([一二三四五六七八九十]+年[一二三四五六七八九十]+月[一二三四五六七八九十]+日)',
            ],
            "LOCATION": [
                r'([^\s，。；！？、]{2,}(?:省|市|县|区|镇|乡|村))',
            ],
            "RIGHT": [
                r'([^\s，。；！？、]*权[^\s，。；！？、]*)',
                r'(有权|享有|具有)([^\s，。；！？、]+)',
            ],
            "OBLIGATION": [
                r'([^\s，。；！？、]*义务[^\s，。；！？、]*)',
                r'(应当|必须|有义务)([^\s，。；！？、]+)',
            ],
            "PENALTY": [
                r'(?:处以|罚款|没收|责令|吊销|暂停|撤销)([^\s，。；！？、]+)',
                r'([^\s，。；！？、]*处罚[^\s，。；！？、]*)',
            ]
        }

        # 关系识别模式
        self.relation_patterns = [
            # 定义关系
            {
                "type": "DEFINE",
                "pattern": r'([^，。；！？、]+)(?:是指|定义为|指的是)([^，。；！？、]+)',
                "subject_pos": 1,
                "object_pos": 2
            },
            # 规范关系
            {
                "type": "REGULATE",
                "pattern": r'([^，。；！？、]+)(?:应当遵守|必须遵循|按照|依据)([^，。；！？、]+)',
                "subject_pos": 1,
                "object_pos": 2
            },
            # 授予关系
            {
                "type": "GRANT",
                "pattern": r'([^，。；！？、]+)(?:有权|享有|获得|授予)([^，。；！？、]+)',
                "subject_pos": 1,
                "object_pos": 2
            },
            # 施加关系
            {
                "type": "IMPOSE",
                "pattern": r'([^，。；！？、]+)(?:应当|必须|承担|负有)([^，。；！？、]+)',
                "subject_pos": 1,
                "object_pos": 2
            },
            # 禁止关系
            {
                "type": "PROHIBIT",
                "pattern": r'(?:禁止|不得|严禁)([^，。；！？、]+)(?:从事|进行|实施|从事)',
                "subject_pos": 2,
                "object_pos": 1
            },
            # 引用关系
            {
                "type": "REFERENCE",
                "pattern": r'《([^》]+(?:法|条例|规定|办法|细则|解释))》第([一二三四五六七八九十百千万\d]+)条',
                "subject_pos": 1,
                "object_pos": 2
            }
        ]

        # 实体标准化词典
        self.entity_normalization = {
            "ORG": {
                "国务院": ["国务院", "中央人民政府"],
                "全国人民代表大会": ["全国人大", "全国人民代表大会"],
                "最高人民法院": ["最高法", "最高人民法院"],
                "最高人民检察院": ["最高检", "最高人民检察院"],
            },
            "LAW": {
                "中华人民共和国宪法": ["宪法", "中华人民共和国宪法"],
                "中华人民共和国刑法": ["刑法", "中华人民共和国刑法"],
                "中华人民共和国民法典": ["民法典", "中华人民共和国民法典"],
                "中华人民共和国劳动合同法": ["劳动合同法", "中华人民共和国劳动合同法"],
            }
        }

    def extract_entities(self, text: str, chunk_id: str) -> list[LegalEntity]:
        """提取实体"""
        entities = []

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    # 获取匹配的文本
                    entity_name = match.group(1).strip() if match.groups() else match.group(0).strip()

                    # 跳过过短或过长的实体
                    if len(entity_name) < 2 or len(entity_name) > 50:
                        continue

                    # 标准化实体名称
                    normalized_name = self._normalize_entity_name(entity_name, entity_type)

                    # 获取上下文
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].replace('\n', ' ')

                    # 提取属性
                    attributes = self._extract_entity_attributes(entity_name, entity_type, text, match)

                    # 计算置信度
                    confidence = self._calculate_entity_confidence(entity_name, entity_type, context)

                    entity = LegalEntity(
                        entity_id=self._generate_entity_id(normalized_name, entity_type, chunk_id),
                        entity_name=normalized_name,
                        entity_type=entity_type,
                        aliases=self._get_entity_aliases(entity_name, entity_type),
                        attributes=attributes,
                        context=context,
                        source_chunk=chunk_id,
                        confidence=confidence
                    )
                    entities.append(entity)

        # 去重
        entities = self._deduplicate_entities(entities)
        return entities

    def extract_relations(self, text: str, entities: list[LegalEntity], chunk_id: str) -> list[LegalRelation]:
        """提取关系"""
        relations = []
        entity_dict = {e.entity_name: e for e in entities}

        for relation_info in self.relation_patterns:
            pattern = relation_info["pattern"]
            matches = re.finditer(pattern, text)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    # 获取主语和宾语
                    subject_name = groups[relation_info["subject_pos"] - 1].strip()
                    object_name = groups[relation_info["object_pos"] - 1].strip()

                    # 查找对应的实体
                    subject_entity = self._find_matching_entity(subject_name, entity_dict)
                    object_entity = self._find_matching_entity(object_name, entity_dict)

                    if subject_entity and object_entity:
                        # 获取上下文
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end].replace('\n', ' ')

                        # 提取关系属性
                        attributes = self._extract_relation_attributes(
                            subject_entity, object_entity, relation_info["type"], text, match
                        )

                        # 计算置信度
                        confidence = self._calculate_relation_confidence(
                            subject_entity, object_entity, relation_info["type"], context
                        )

                        relation = LegalRelation(
                            relation_id=self._generate_relation_id(
                                subject_entity.entity_id, object_entity.entity_id, relation_info["type"]
                            ),
                            subject_id=subject_entity.entity_id,
                            object_id=object_entity.entity_id,
                            relation_type=relation_info["type"],
                            attributes=attributes,
                            context=context,
                            source_chunk=chunk_id,
                            confidence=confidence
                        )
                        relations.append(relation)

        # 去重
        relations = self._deduplicate_relations(relations)
        return relations

    def _normalize_entity_name(self, name: str, entity_type: str) -> str:
        """标准化实体名称"""
        if entity_type in self.entity_normalization:
            for standard_name, aliases in self.entity_normalization[entity_type].items():
                if name in aliases:
                    return standard_name
        return name

    def _get_entity_aliases(self, name: str, entity_type: str) -> list[str]:
        """获取实体别名"""
        aliases = []
        if entity_type in self.entity_normalization:
            for standard_name, alias_list in self.entity_normalization[entity_type].items():
                if name == standard_name:
                    aliases = [a for a in alias_list if a != name]
                    break
        return aliases

    def _extract_entity_attributes(self, entity_name: str, entity_type: str, text: str, match) -> dict:
        """提取实体属性"""
        attributes = {
            "position": match.start(),
            "length": len(entity_name),
        }

        # 根据实体类型提取特定属性
        if entity_type == "ARTICLE":
            # 提取条款编号
            article_match = re.search(r'([一二三四五六七八九十百千万\d]+)', entity_name)
            if article_match:
                attributes["article_number"] = article_match.group(1)

        elif entity_type == "TIME":
            # 尝试解析时间
            try:
                # 简单的时间标准化
                attributes["normalized_time"] = entity_name
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass

        elif entity_type == "LAW":
            # 检查是否是法律、条例、规定等
            if "法" in entity_name:
                attributes["law_type"] = "法律"
            elif "条例" in entity_name:
                attributes["law_type"] = "行政法规"
            elif "规定" in entity_name or "办法" in entity_name:
                attributes["law_type"] = "部门规章"

        return attributes

    def _calculate_entity_confidence(self, entity_name: str, entity_type: str, context: str) -> float:
        """计算实体置信度"""
        base_confidence = 0.8

        # 根据实体类型调整
        if entity_type in ["LAW", "ARTICLE", "TIME"]:
            base_confidence += 0.1  # 这些类型更容易准确识别

        # 根据上下文调整
        if entity_type == "PERSON" and any(word in context for word in ["公民", "个人", "当事人"]):
            base_confidence += 0.05
        elif entity_type == "ORG" and any(word in context for word in ["机构", "组织", "部门"]):
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _extract_relation_attributes(self, subject: LegalEntity, object: LegalEntity,
                                   relation_type: str, text: str, match) -> dict:
        """提取关系属性"""
        attributes = {
            "subject_type": subject.entity_type,
            "object_type": object.entity_type,
            "position": match.start(),
            "relation_text": match.group(0),
        }

        # 根据关系类型提取特定属性
        if relation_type == "REFERENCE":
            # 提取引用的具体条款
            attributes["citation_type"] = "法律引用"
        elif relation_type == "DEFINE":
            attributes["definition_type"] = "概念定义"

        return attributes

    def _calculate_relation_confidence(self, subject: LegalEntity, object: LegalEntity,
                                      relation_type: str, context: str) -> float:
        """计算关系置信度"""
        base_confidence = 0.7

        # 根据关系类型调整
        if relation_type in ["DEFINE", "REFERENCE"]:
            base_confidence += 0.2  # 这些关系更容易准确识别
        elif relation_type in ["GRANT", "IMPOSE"]:
            base_confidence += 0.1

        # 根据实体类型组合调整
        valid_combinations = [
            ("LAW", "ARTICLE", "REFERENCE"),
            ("PERSON", "RIGHT", "GRANT"),
            ("ORG", "OBLIGATION", "IMPOSE"),
        ]

        if (subject.entity_type, object.entity_type, relation_type) in valid_combinations:
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _find_matching_entity(self, name: str, entity_dict: dict[str, LegalEntity]) -> LegalEntity | None:
        """查找匹配的实体"""
        # 精确匹配
        if name in entity_dict:
            return entity_dict[name]

        # 模糊匹配
        for entity_name, entity in entity_dict.items():
            # 检查是否包含关系
            if name in entity_name or entity_name in name:
                return entity

            # 检查别名
            if name in entity.aliases:
                return entity

        return None

    def _generate_entity_id(self, name: str, entity_type: str, chunk_id: str) -> str:
        """生成实体ID"""
        content = f"{name}_{entity_type}_{chunk_id}"
        return short_hash(content, 16)

    def _generate_relation_id(self, subject_id: str, object_id: str, relation_type: str) -> str:
        """生成关系ID"""
        content = f"{subject_id}_{object_id}_{relation_type}"
        return short_hash(content, 16)

    def _deduplicate_entities(self, entities: list[LegalEntity]) -> list[LegalEntity]:
        """去重实体"""
        seen = set()
        deduplicated = []

        for entity in entities:
            key = (entity.entity_name, entity.entity_type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)

        return deduplicated

    def _deduplicate_relations(self, relations: list[LegalRelation]) -> list[LegalRelation]:
        """去重关系"""
        seen = set()
        deduplicated = []

        for relation in relations:
            key = (relation.subject_id, relation.object_id, relation.relation_type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(relation)

        return deduplicated

    def process_chunks(self, chunks_file: Path, output_dir: Path) -> tuple[list[LegalEntity], list[LegalRelation]]:
        """处理分块文件，提取实体和关系"""
        logger.info("\n🔍 开始提取法律实体和关系")
        logger.info(f"输入文件: {chunks_file}")

        # 加载分块数据
        with open(chunks_file, encoding='utf-8') as f:
            data = json.load(f)

        chunks = data.get("chunks", [])
        logger.info(f"待处理块数: {len(chunks)}")

        all_entities = []
        all_relations = []

        for idx, chunk in enumerate(chunks[:100]):  # 限制处理数量
            content = chunk.get("content", "")
            chunk_id = chunk.get("chunk_id", f"chunk_{idx}")

            if not content:
                continue

            # 提取实体
            entities = self.extract_entities(content, chunk_id)
            all_entities.extend(entities)

            # 提取关系
            relations = self.extract_relations(content, entities, chunk_id)
            all_relations.extend(relations)

            if (idx + 1) % 10 == 0:
                logger.info(f"已处理 {idx + 1}/{min(100, len(chunks))} 块")

        # 统计信息
        entity_type_stats = Counter(e.entity_type for e in all_entities)
        relation_type_stats = Counter(r.relation_type for r in all_relations)

        logger.info("\n📊 提取统计:")
        logger.info(f"  总实体数: {len(all_entities)}")
        logger.info(f"  总关系数: {len(all_relations)}")
        logger.info("\n  实体类型分布:")
        for entity_type, count in entity_type_stats.most_common():
            logger.info(f"    {entity_type}: {count}")
        logger.info("\n  关系类型分布:")
        for relation_type, count in relation_type_stats.most_common():
            logger.info(f"    {relation_type}: {count}")

        # 保存结果
        self._save_results(all_entities, all_relations, output_dir, entity_type_stats, relation_type_stats)

        return all_entities, all_relations

    def _save_results(self, entities: list[LegalEntity], relations: list[LegalRelation],
                     output_dir: Path, entity_stats: dict, relation_stats: dict):
        """保存提取结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存实体
        entities_file = output_dir / f"legal_entities_v2_{timestamp}.json"
        entities_data = [asdict(e) for e in entities]
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_entities": len(entities),
                    "entity_types": list(entity_stats.keys())
                },
                "entities": entities_data
            }, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = output_dir / f"legal_relations_v2_{timestamp}.json"
        relations_data = [asdict(r) for r in relations]
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_relations": len(relations),
                    "relation_types": list(relation_stats.keys())
                },
                "relations": relations_data
            }, f, ensure_ascii=False, indent=2)

        # 保存统计
        stats_file = output_dir / f"er_stats_{timestamp}.json"
        stats = {
            "timestamp": datetime.now().isoformat(),
            "entity_statistics": dict(entity_stats),
            "relation_statistics": dict(relation_stats),
            "entity_type_definitions": self.entity_types,
            "relation_type_definitions": self.relation_types
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("\n💾 结果已保存:")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  统计文件: {stats_file}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("🏷️ 法律实体关系提取器 🏷️")
    print("="*100)

    # 初始化提取器
    extractor = LegalEntityRelationExtractor()

    # 设置路径
    chunks_dir = Path("/Users/xujian/Athena工作平台/production/data/processed")
    output_dir = Path("/Users/xujian/Athena工作平台/production/data/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 查找最新的分块文件
    chunk_files = list(chunks_dir.glob("legal_chunks_v2_*.json"))
    if not chunk_files:
        logger.error("没有找到分块文件")
        return

    latest_chunk_file = max(chunk_files, key=lambda x: x.stat().st_mtime)
    logger.info(f"使用分块文件: {latest_chunk_file.name}")

    # 执行提取
    entities, relations = extractor.process_chunks(latest_chunk_file, output_dir)

    # 显示示例
    print("\n📋 实体示例:")
    for i, entity in enumerate(entities[:5]):
        print(f"\n实体 {i+1}:")
        print(f"  名称: {entity.entity_name}")
        print(f"  类型: {entity.entity_type} ({extractor.entity_types.get(entity.entity_type, '未知')})")
        print(f"  置信度: {entity.confidence:.3f}")
        print(f"  上下文: {entity.context[:100]}...")

    print("\n📋 关系示例:")
    for i, relation in enumerate(relations[:5]):
        print(f"\n关系 {i+1}:")
        print(f"  类型: {relation.relation_type} ({extractor.relation_types.get(relation.relation_type, '未知')})")
        print(f"  主语ID: {relation.subject_id[:8]}...")
        print(f"  宾语ID: {relation.object_id[:8]}...")
        print(f"  置信度: {relation.confidence:.3f}")
        print(f"  上下文: {relation.context[:100]}...")

if __name__ == "__main__":
    main()
