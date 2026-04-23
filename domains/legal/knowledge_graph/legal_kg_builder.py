#!/usr/bin/env python3
from __future__ import annotations

"""
法律知识图谱构建工具 - 使用BERT-NER提取实体和关系 (NebulaGraph版本)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

⚠️ 迁移说明 ⚠️
此文件使用NebulaGraph实现,推荐迁移到Neo4j版本。
新版本配置请参考下方Neo4j配置部分。

构建法律领域的知识图谱并存储到图数据库

作者: Athena平台团队
创建时间: 2025-01-06
更新时间: 2026-01-25 (TD-001: 标记为迁移)
"""

import re

# 添加项目路径
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import psycopg2
from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

from core.logging_config import setup_logging

sys.path.append(str(Path(__file__).parent.parent))
from legal_kg.legal_text_parser import LegalTextParser

# ==================== 配置 ====================
# PostgreSQL配置
DB_CONFIG = {
    "host": "localhost",
    "port": 15432,
    "database": "phoenix_prod",
    "user": "phoenix_user",
    "password": "phoenix_secure_password_2024",
}

# NebulaGraph配置 (TD-001: 已废弃,推荐使用Neo4j)
# 安全验证:space名称必须符合NebulaGraph命名规则(字母、数字、下划线)
_SPACE_NAME = "legal_knowledge"
if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", _SPACE_NAME):
    raise ValueError(f"Invalid space name: {_SPACE_NAME}")

NEBULA_CONFIG = {
    "address": ("127.0.0.1", 9669),
    "user": "root",
    "password": "nebula",
    "space": _SPACE_NAME,
}

# ========== Neo4j配置 (TD-001: 推荐) ==========
# 安全验证:database名称必须符合Neo4j命名规则
_DATABASE_NAME = "legal_knowledge"
if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", _DATABASE_NAME):
    raise ValueError(f"Invalid database name: {_DATABASE_NAME}")

NEO4J_CONFIG = {
    "uri": "bolt://127.0.0.1:7687",  # Neo4j默认端口
    "user": "neo4j",
    "password": "password",  # 请修改为实际密码
    "database": _DATABASE_NAME,
}
# =========================================

# 日志配置
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class LegalEntity:
    """法律实体"""

    id: str
    type: str  # Law, Article, Concept, Organization, etc.
    name: str
    properties: dict


@dataclass
class LegalRelation:
    """法律关系"""

    source_id: str
    target_id: str
    relation_type: str
    properties: dict


class ChineseLegalNER:
    """
    中文法律命名实体识别
    基于规则和法律领域知识
    """

    # 法律实体类型
    ENTITY_TYPES = {
        "law": "法律",
        "article": "条款",
        "concept": "法律概念",
        "organization": "机构",
        "person": "人员",
        "time": "时间",
        "amount": "金额",
        "behavior": "行为",
        "right": "权利",
        "obligation": "义务",
    }

    # 法律概念关键词
    LEGAL_CONCEPTS = {
        # 民法概念
        "民事权利",
        "民事义务",
        "民事责任",
        "民事行为",
        "民事法律关系",
        "法人",
        "自然人",
        "民事主体",
        "民事权利能力",
        "民事行为能力",
        "合同",
        "侵权",
        "物权",
        "债权",
        "继承",
        "婚姻",
        "收养",
        "违约责任",
        "侵权责任",
        "连带责任",
        "补充责任",
        # 刑法概念
        "犯罪",
        "刑罚",
        "刑事责任",
        "故意犯罪",
        "过失犯罪",
        "有期徒刑",
        "无期徒刑",
        "死刑",
        "罚金",
        "剥夺政治权利",
        "没收财产",
        "缓刑",
        "假释",
        "减刑",
        # 行政法概念
        "行政许可",
        "行政处罚",
        "行政强制",
        "行政复议",
        "行政诉讼",
        "行政机关",
        "行政相对人",
        "行政行为",
        "行政不作为",
        # 程法概念
        "管辖",
        "证据",
        "举证责任",
        "审判",
        "判决",
        "裁定",
        "原告",
        "被告",
        "第三人",
        "代理人",
        "辩护人",
        "起诉",
        "上诉",
        "申诉",
        "抗诉",
        "执行",
        # 知识产权
        "专利",
        "商标",
        "著作权",
        "商业秘密",
        "集成电路布图设计",
        "发明专利",
        "实用新型",
        "外观设计",
        "独占实施权",
        # 其他
        "国家赔偿",
        "仲裁",
        "公证",
        "调解",
    }

    # 权利关键词
    RIGHT_KEYWORDS = {
        "权": ["权利", "权力", "职权", "权限", "权益"],
        "自由": ["自由"],
        "利益": ["利益", "福利"],
    }

    # 义务关键词
    OBLIGATION_KEYWORDS = {
        "义务": ["义务", "职责", "责任"],
        "禁止": ["禁止", "不得", "严禁"],
        "应当": ["应当", "必须", "有义务"],
    }

    # 机构名称模式
    ORGANIZATION_PATTERNS = [
        r"最高人民法院",
        r"最高人民检察院",
        r"国务院",
        r"公安部",
        r"司法部",
        r"人民法院",
        r"人民检察院",
        r"公安机关",
        r"行政部门",
        r"工商行政管理部门",
        r"专利行政部门",
        r"商标局",
        r"版权局",
    ]

    def __init__(self):
        self.parser = LegalTextParser()

    def extract_entities(self, text: str, doc_id: str) -> list[LegalEntity]:
        """从文本中提取法律实体"""
        entities = []

        # 1. 提取法律概念
        for concept in self.LEGAL_CONCEPTS:
            if concept in text:
                entity_id = f"{doc_id}_concept_{hash(concept)}"
                entities.append(
                    LegalEntity(
                        id=entity_id,
                        type="concept",
                        name=concept,
                        properties={"category": "法律概念", "doc_id": doc_id},
                    )
                )

        # 2. 提取权利
        for right_type, keywords in self.RIGHT_KEYWORDS.items():
            for keyword in keywords:
                pattern = f"{keyword}[^,。;,;]*"
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match.strip()) > 2:
                        entity_id = f"{doc_id}_right_{hash(match)}"
                        entities.append(
                            LegalEntity(
                                id=entity_id,
                                type="right",
                                name=match.strip(),
                                properties={
                                    "category": "权利",
                                    "right_type": right_type,
                                    "doc_id": doc_id,
                                },
                            )
                        )

        # 3. 提取义务
        for obl_type, keywords in self.OBLIGATION_KEYWORDS.items():
            for keyword in keywords:
                pattern = f"{keyword}[^,。;,;]*"
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match.strip()) > 2:
                        entity_id = f"{doc_id}_obligation_{hash(match)}"
                        entities.append(
                            LegalEntity(
                                id=entity_id,
                                type="obligation",
                                name=match.strip(),
                                properties={
                                    "category": "义务",
                                    "obligation_type": obl_type,
                                    "doc_id": doc_id,
                                },
                            )
                        )

        # 4. 提取机构
        for pattern in self.ORGANIZATION_PATTERNS:
            if re.search(pattern, text):
                matches = re.findall(pattern, text)
                for match in set(matches):
                    entity_id = f"{doc_id}_org_{hash(match)}"
                    entities.append(
                        LegalEntity(
                            id=entity_id,
                            type="organization",
                            name=match,
                            properties={"category": "机构", "doc_id": doc_id},
                        )
                    )

        return entities

    def extract_relations(self, text: str, entities: list[LegalEntity]) -> list[LegalRelation]:
        """从文本中提取关系"""
        relations = []

        # 创建实体名称到ID的映射
        entity_map = {e.name: e.id for e in entities}

        # 定义常见关系模式
        relation_patterns = [
            # 包含关系
            (r"(.{2,10})包含(.{2,10})", "contains"),
            (r"(.{2,10})包括(.{2,10})", "includes"),
            # 定义关系
            (r"(.{2,10})是指(.{2,20})", "defines"),
            (r"(.{2,10})定义为(.{2,20})", "defines"),
            # 违反关系
            (r"违反(.{2,10})", "violates"),
            (r"侵害(.{2,10})", "infringes"),
            # 保护关系
            (r"保护(.{2,10})", "protects"),
            (r"保障(.{2,10})", "guarantees"),
        ]

        for pattern, relation_type in relation_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                source = match.group(1)
                target = match.group(2)

                if source in entity_map and target in entity_map:
                    relations.append(
                        LegalRelation(
                            source_id=entity_map[source],
                            target_id=entity_map[target],
                            relation_type=relation_type,
                            properties={"context": match.group(0)[:100]},
                        )
                    )

        return relations


class LegalKnowledgeGraphBuilder:
    """法律知识图谱构建器"""

    def __init__(self):
        self.ner = ChineseLegalNER()
        self.entities = set()
        self.relations = set()
        self.stats = defaultdict(int)

    def setup_nebula_graph(self):
        """设置NebulaGraph图空间"""
        logger.info("📋 设置NebulaGraph图空间...")

        # 初始化连接池
        config = Config()
        config.max_connection_pool_size = 10

        connection_pool = ConnectionPool()
        connection_pool.init([NEBULA_CONFIG["address"], config)

        session = connection_pool.get_session(NEBULA_CONFIG["user"], NEBULA_CONFIG["password"])

        try:
            # 创建图空间
            # 安全说明:space名称已在模块加载时通过正则验证,只包含字母、数字和下划线
            session.execute(f"""
                IF NOT EXISTS CREATE SPACE {NEBULA_CONFIG['space']} (
                    partition_num = 10,
                    replica_factor = 1,
                    vid_type = FIXED_STRING(32)
                );
            """)

            # 使用图空间 - space名称已验证安全
            session.execute(f"USE {NEBULA_CONFIG['space']};")

            # 创建标签类型
            tag_types = [
                ("Law", "法律"),
                ("Article", "条款"),
                ("Concept", "概念"),
                ("Organization", "机构"),
                ("Right", "权利"),
                ("Obligation", "义务"),
                ("Person", "人员"),
            ]

            for tag_name, tag_desc in tag_types:
                # 安全说明:tag_name来自硬编码白名单列表,安全
                session.execute(f"""
                    IF NOT EXISTS CREATE TAG {tag_name} (
                        name string,
                        type string,
                        properties string,
                        doc_id string,
                        create_time timestamp
                    );
                """)
                logger.debug(f"✅ 创建标签: {tag_name} - {tag_desc}")

            # 创建边类型
            edge_types = [
                ("contains", "包含"),
                ("defines", "定义"),
                ("violates", "违反"),
                ("protects", "保护"),
                ("refers_to", "引用"),
                ("related_to", "相关"),
            ]

            for edge_name, edge_desc in edge_types:
                # 安全说明:edge_name来自硬编码白名单列表,安全
                session.execute(f"""
                    IF NOT EXISTS CREATE EDGE {edge_name} (
                        context string,
                        create_time timestamp
                    );
                """)
                logger.debug(f"✅ 创建边: {edge_name} - {edge_desc}")

            logger.info("✅ NebulaGraph设置完成")

        except Exception as e:
            logger.error(f"❌ NebulaGraph设置失败: {e}")
        finally:
            session.release()
            connection_pool.close()

        return connection_pool

    def fetch_documents_from_db(self) -> list[tuple]:
        """从PostgreSQL获取法律文档"""
        logger.info("📥 从PostgreSQL获取法律文档...")

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 只获取非地方法规的文档进行知识图谱构建
            cursor.execute("""
                SELECT
                    id,
                    title,
                    category,
                    content
                FROM legal_documents
                WHERE category != 'local_regulation'
                ORDER BY id
                LIMIT 1000;
            """)

            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            logger.info(f"✅ 获取 {len(rows)} 个法律文档")
            return rows

        except Exception as e:
            logger.error(f"❌ 数据库查询失败: {e}")
            return []

    def build_knowledge_graph(self, documents: list[tuple]):
        """构建知识图谱"""
        logger.info(f"\n🔍 开始构建知识图谱 ({len(documents)} 个文档)...")

        all_entities = []
        all_relations = []

        for doc_id, title, _category, content in documents:
            logger.debug(f"处理文档: {title}")

            # 提取实体
            entities = self.ner.extract_entities(
                text=content[:2000], doc_id=str(doc_id)  # 限制长度
            )
            all_entities.extend(entities)

            # 提取关系
            relations = self.ner.extract_relations(text=content[:2000], entities=entities)
            all_relations.extend(relations)

            self.stats["documents_processed"] += 1
            self.stats["entities"] += len(entities)
            self.stats["relations"] += len(relations)

            if self.stats["documents_processed"] % 100 == 0:
                logger.info(f"⏳ 进度: {self.stats['documents_processed']}/{len(documents)}")

        logger.info("\n📊 提取统计:")
        logger.info(f"   文档数: {self.stats['documents_processed']}")
        logger.info(f"   实体数: {self.stats['entities']}")
        logger.info(f"   关系数: {self.stats['relations']}")

        return all_entities, all_relations

    def save_to_nebula(self, entities: list[LegalEntity], relations: list[LegalRelation]):
        """保存到NebulaGraph"""
        logger.info("\n💾 保存知识图谱到NebulaGraph...")

        # 初始化连接
        config = Config()
        connection_pool = ConnectionPool()
        connection_pool.init([NEBULA_CONFIG["address"], config)

        session = connection_pool.get_session(NEBULA_CONFIG["user"], NEBULA_CONFIG["password"])

        try:
            # 使用图空间 - space名称已验证安全
            session.execute(f"USE {NEBULA_CONFIG['space']};")

            # 插入实体
            entity_count = 0
            for entity in entities:
                try:
                    # 根据实体类型选择标签
                    tag = entity.type.capitalize()

                    insert_sql = f'INSERT VERTEX {tag}("{entity.id}", "{entity.name}", "{entity.type}", "{entity.properties.get("doc_id", "")}", datetime())'

                    session.execute(insert_sql)
                    entity_count += 1

                    if entity_count % 100 == 0:
                        logger.debug(f"⏳ 插入实体: {entity_count}/{len(entities)}")

                except Exception as e:
                    logger.debug(f"实体插入失败: {e}")

            logger.info(f"✅ 插入 {entity_count} 个实体")

            # 插入关系
            relation_count = 0
            for relation in relations:
                try:
                    edge_type = relation.relation_type

                    insert_sql = f'INSERT EDGE {edge_type}("{relation.source_id}", "{relation.target_id}", "{relation.properties.get("context", "")}", datetime())'

                    session.execute(insert_sql)
                    relation_count += 1

                    if relation_count % 100 == 0:
                        logger.debug(f"⏳ 插入关系: {relation_count}/{len(relations)}")

                except Exception as e:
                    logger.debug(f"关系插入失败: {e}")

            logger.info(f"✅ 插入 {relation_count} 个关系")

        except Exception as e:
            logger.error(f"❌ 保存失败: {e}")
        finally:
            session.release()
            connection_pool.close()


# ==================== 主程序 ====================
def main():
    """主程序"""
    logger.info("\n" + "=" * 70)
    logger.info("📖 法律知识图谱构建工具")
    logger.info("=" * 70 + "\n")

    # 初始化构建器
    builder = LegalKnowledgeGraphBuilder()

    # 设置NebulaGraph
    builder.setup_nebula_graph()

    # 获取文档
    documents = builder.fetch_documents_from_db()

    if not documents:
        logger.error("❌ 没有找到法律文档")
        return

    # 构建知识图谱
    entities, relations = builder.build_knowledge_graph(documents)

    # 保存到NebulaGraph
    builder.save_to_nebula(entities, relations)

    logger.info("\n✅ 知识图谱构建完成!")


if __name__ == "__main__":
    main()
