#!/usr/bin/env python3
"""
法律知识图谱增强器 (NebulaGraph版本 - 已废弃)

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

⚠️ 迁移说明 ⚠️
此文件使用NebulaGraph实现,推荐迁移到Neo4j版本。

提供法律知识图谱的实时更新、语义推理和智能关联分析

作者: Athena平台团队
创建时间: 2025-01-06
更新时间: 2026-01-25 (TD-001: 标记为迁移)
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from core.async_main import async_main
from core.logging_config import setup_logging

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from nebula3.common import *
    from nebula3.Config import Config
    from nebula3.gclient.net import ConnectionPool

    NEBULA_AVAILABLE = True
except ImportError:
    print("⚠️ NebulaGraph库未安装")
    NEBULA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("⚠️ sentence-transformers未安装")
    TRANSFORMERS_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class LegalKnowledgeEnhancer:
    """法律知识图谱增强器"""

    def __init__(self):
        self.connection_pool = None
        self.embedding_model = None
        self.legal_entities = {}
        self.relation_patterns = {}
        self.inference_rules = {}

    @staticmethod
    def _escape_nql_string(value: str) -> str:
        """转义nGQL字符串中的特殊字符,防止注入"""
        if value is None:
            return ""
        # 转义反斜杠和引号
        value = str(value)
        value = value.replace("\\", "\\\\")
        value = value.replace('"', '\\"')
        return value

    def _load_legal_ontology(self) -> Any:
        """加载法律本体知识"""
        try:
            # 法律实体类型
            self.legal_entities = {
                "法律法规": ["民法典", "专利法", "商标法", "著作权法", "民事诉讼法", "刑事诉讼法"],
                "司法机关": ["最高人民法院", "地方各级法院", "检察院", "仲裁委员会"],
                "法律行为": ["起诉", "应诉", "上诉", "申诉", "执行", "仲裁", "调解"],
                "法律文书": ["判决书", "裁定书", "调解书", "起诉状", "答辩状"],
                "法律概念": ["民事权利", "民事义务", "侵权责任", "合同义务", "知识产权"],
                "诉讼程序": ["一审", "二审", "再审", "执行程序", "仲裁程序"],
            }

            # 关系模式
            self.relation_patterns = {
                "引用关系": [
                    r"《([^》]+)》第([一二三四五六七八九十百千万\d]+)条",
                    r"根据([^,。;:!?\n]+)规定",
                    r"参照([^,。;:!?\n]+)条款",
                ],
                "适用关系": [
                    r"适用于([^,。;:!?\n]+)",
                    r"适用([^,。;:!?\n]+)情况",
                    r"在([^,。;:!?\n]+)中适用",
                ],
                "约束关系": [
                    r"不得([^,。;:!?\n]+)",
                    r"应当([^,。;:!?\n]+)",
                    r"可以([^,。;:!?\n]+)",
                    r"禁止([^,。;:!?\n]+)",
                ],
                "时间关系": [
                    r"自([^,。;:!?\n]+)起",
                    r"在([^,。;:!?\n]+)内",
                    r"超过([^,。;:!?\n]+)",
                ],
            }

            # 推理规则
            self.inference_rules = {
                "权利义务推理": {
                    "rule": "如果A享有权利,则B对应承担义务",
                    "conditions": ["享有权利", "承担义务"],
                    "conclusion": "形成权利义务关系",
                },
                "侵权责任推理": {
                    "rule": "如果存在违法行为且造成损害,则应承担侵权责任",
                    "conditions": ["违法行为", "损害结果", "因果关系"],
                    "conclusion": "承担侵权责任",
                },
                "合同效力推理": {
                    "rule": "如果合同满足法定要件,则合同有效",
                    "conditions": ["当事人适格", "意思表示真实", "内容合法"],
                    "conclusion": "合同有效",
                },
            }

            logger.info("✅ 法律本体知识加载完成")

        except Exception as e:
            logger.error(f"❌ 法律本体知识加载失败: {e}")

    def _init_embedding_model(self) -> Any:
        """初始化嵌入模型"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ 嵌入模型不可用")
            return

        try:
            model_path = "/Users/xujian/Athena工作平台/models/BAAI/bge-m3"
            if Path(model_path).exists():
                self.embedding_model = SentenceTransformer(model_path)
                logger.info("✅ BGE嵌入模型加载成功")
            else:
                self.embedding_model = SentenceTransformer("BAAI/BAAI/bge-m3")
                logger.info("✅ 在线BGE嵌入模型加载成功")

        except Exception as e:
            logger.error(f"❌ 嵌入模型初始化失败: {e}")
            self.embedding_model = None

    async def initialize(self):
        """初始化增强器"""
        if not NEBULA_AVAILABLE:
            logger.error("❌ NebulaGraph不可用")
            return False

        try:
            # 创建连接池
            config = Config()
            config.max_connection_pool_size = 10
            self.connection_pool = ConnectionPool()

            # 连接到NebulaGraph
            if not self.connection_pool.init([("127.0.0.1", 9669)], config):
                logger.error("❌ NebulaGraph连接失败")
                return False

            logger.info("✅ 法律知识图谱增强器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 法律知识图谱增强器初始化失败: {e}")
            return False

    async def extract_legal_entities(self, text: str) -> list[dict[str, Any]]:
        """提取法律实体"""
        entities = []

        for entity_type, entity_list in self.legal_entities.items():
            for entity in entity_list:
                # 查找所有匹配
                matches = re.finditer(entity, text, re.IGNORECASE)
                for match in matches:
                    entities.append(
                        {
                            "type": entity_type,
                            "name": match.group(),
                            "start": match.start(),
                            "end": match.end(),
                            "confidence": 0.8,
                        }
                    )

        return entities

    async def extract_legal_relations(self, text: str) -> list[dict[str, Any]]:
        """提取法律关系"""
        relations = []

        for relation_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    relations.append(
                        {
                            "type": relation_type,
                            "text": match.group(),
                            "groups": match.groups() if match.groups() else [],
                            "start": match.start(),
                            "end": match.end(),
                        }
                    )

        return relations

    async def semantic_similarity_analysis(self, text1: str, text2: str) -> float:
        """语义相似度分析"""
        if self.embedding_model is None:
            return 0.0

        try:
            # 生成文本向量
            embedding1 = self.embedding_model.encode([text1])
            embedding2 = self.embedding_model.encode([text2])

            # 计算余弦相似度
            similarity = np.dot(embedding1, embedding2.T)[0][0]
            return float(similarity)

        except Exception as e:
            logger.error(f"❌ 语义相似度分析失败: {e}")
            return 0.0

    async def update_legal_knowledge(
        self, legal_text: str, source: str = "manual"
    ) -> dict[str, Any]:
        """更新法律知识"""
        try:
            # 提取实体
            entities = await self.extract_legal_entities(legal_text)

            # 提取关系
            relations = await self.extract_legal_relations(legal_text)

            # 文本向量化
            text_vector = None
            if self.embedding_model:
                text_vector = self.embedding_model.encode([legal_text])[0].tolist()

            # 构建知识更新
            knowledge_update = {
                "text": legal_text,
                "source": source,
                "entities": entities,
                "relations": relations,
                "vector": text_vector,
                "timestamp": datetime.now().isoformat(),
            }

            # 存储到知识图谱
            if NEBULA_AVAILABLE and self.connection_pool:
                await self._store_to_graph(knowledge_update)

            logger.info(
                f"✅ 法律知识更新完成,识别到 {len(entities)} 个实体,{len(relations)} 个关系"
            )
            return knowledge_update

        except Exception as e:
            logger.error(f"❌ 法律知识更新失败: {e}")
            return {"error": str(e)}

    async def _store_to_graph(self, knowledge: dict[str, Any]):
        """存储到知识图谱"""
        try:
            session = self.connection_pool.get_session("root", "nebula")

            # 使用法律知识空间
            result = session.execute("USE legal_kg")
            if not result.is_succeeded():
                # 创建法律知识空间
                result = session.execute("""
                    CREATE SPACE IF NOT EXISTS legal_kg (
                        partition_num = 20,
                        replica_factor = 1,
                        vid_type = FIXED_STRING(256)
                    )
                """)
                await asyncio.sleep(10)  # 等待空间创建完成
                session.execute("USE legal_kg")

                # 创建标签类型
                session.execute("""
                    CREATE TAG IF NOT EXISTS legal_entity (
                        name string,
                        type string,
                        description string,
                        source string,
                        timestamp timestamp
                    )
                """)

                session.execute("""
                    CREATE TAG IF NOT EXISTS legal_text (
                        content string,
                        source string,
                        vector string,
                        timestamp timestamp
                    )
                """)

                session.execute("""
                    CREATE EDGE IF NOT EXISTS has_relation (
                        type string,
                        confidence double,
                        description string,
                        timestamp timestamp
                    )
                """)

            # 插入法律文本节点
            text_id = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            vector_str = json.dumps(knowledge.get("vector")) if knowledge.get("vector") else ""

            # 转义用户输入,防止nGQL注入
            escaped_text = self._escape_nql_string(knowledge["text"][:200])
            escaped_source = self._escape_nql_string(knowledge["source"])
            escaped_vector = self._escape_nql_string(vector_str)

            session.execute(f"""
                INSERT VERTEX legal_text (content, source, vector, timestamp)
                VALUES "{text_id}", "{escaped_text}", "{escaped_source}", "{escaped_vector}", datetime()
            """)

            # 插入实体节点和关系
            for entity in knowledge["entities"]:
                entity_id = f"entity_{entity['name']}_{hash(entity['name'])}"
                # 转义用户输入,防止nGQL注入
                escaped_entity_name = self._escape_nql_string(entity["name"])
                escaped_entity_type = self._escape_nql_string(entity["type"])
                escaped_entity_source = self._escape_nql_string(knowledge["source"])

                session.execute(f"""
                    INSERT VERTEX legal_entity (name, type, description, source, timestamp)
                    VALUES "{entity_id}", "{escaped_entity_name}", "{escaped_entity_type}", "", "{escaped_entity_source}", datetime()
                """)

                # 创建文本-实体关系
                # 转义关系描述,防止nGQL注入
                escaped_relation_desc = self._escape_nql_string("文本包含实体")

                session.execute(f"""
                    INSERT EDGE has_relation (type, confidence, description, timestamp)
                    VALUES "{text_id}"->"{entity_id}": ("contains", {entity['confidence']}, "{escaped_relation_desc}", datetime())
                """)

            # 插入实体间关系
            for relation in knowledge["relations"]:
                # 简化处理:基于关系文本创建关系
                if len(relation["groups"]) >= 2:
                    source_id = f"entity_{relation['groups'][0]}_{hash(relation['groups'][0])}"
                    target_id = f"entity_{relation['groups'][1]}_{hash(relation['groups'][1])}"

                    # 转义用户输入,防止nGQL注入
                    escaped_rel_type = self._escape_nql_string(relation["type"])
                    escaped_rel_text = self._escape_nql_string(relation["text"])

                    session.execute(f"""
                        INSERT EDGE has_relation (type, confidence, description, timestamp)
                        VALUES "{source_id}"->"{target_id}": ("{escaped_rel_type}", 0.8, "{escaped_rel_text}", datetime())
                    """)

            session.release()
            logger.info("✅ 知识已存储到图谱")

        except Exception as e:
            logger.error(f"❌ 存储到图谱失败: {e}")

    async def legal_reasoning(self, query: str, context: str | None = None) -> dict[str, Any]:
        """法律推理"""
        try:
            reasoning_results = []

            # 提取查询中的法律要素
            query_entities = await self.extract_legal_entities(query)

            # 应用推理规则
            for rule_name, rule in self.inference_rules.items():
                # 检查条件满足情况
                satisfied_conditions = []
                for condition in rule["conditions"]:
                    if any(
                        condition in query or condition in (context or "")
                        for condition in [condition]
                    ):
                        satisfied_conditions.append(condition)

                # 如果满足大部分条件,应用推理
                if len(satisfied_conditions) >= len(rule["conditions"]) * 0.6:
                    reasoning_results.append(
                        {
                            "rule": rule_name,
                            "rule_description": rule["rule"],
                            "satisfied_conditions": satisfied_conditions,
                            "conclusion": rule["conclusion"],
                            "confidence": len(satisfied_conditions) / len(rule["conditions"]),
                        }
                    )

            # 语义相似度推理
            if self.embedding_model and context:
                similarity = await self.semantic_similarity_analysis(query, context)
                if similarity > 0.7:
                    reasoning_results.append(
                        {
                            "rule": "语义相似性推理",
                            "rule_description": "基于语义相似性的案例分析",
                            "similarity": similarity,
                            "conclusion": f"查询内容与上下文高度相似({similarity:.2f})",
                            "confidence": similarity,
                        }
                    )

            return {
                "query": query,
                "context": context,
                "extracted_entities": query_entities,
                "reasoning_results": reasoning_results,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 法律推理失败: {e}")
            return {"error": str(e)}

    async def search_similar_cases(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """搜索相似案例"""
        if not NEBULA_AVAILABLE or not self.connection_pool:
            return []

        try:
            session = self.connection_pool.get_session("root", "nebula")
            session.execute("USE legal_kg")

            # 生成查询向量
            query_vector = None
            if self.embedding_model:
                query_vector = self.embedding_model.encode([query])[0].tolist()

            # 执行相似性搜索
            similar_cases = []

            if query_vector:
                # 基于向量的相似性搜索
                # 注意:这里需要NebulaGraph支持向量搜索,简化处理
                result = session.execute("""
                    MATCH (v:legal_text)
                    RETURN v.content AS content, v.source AS source, v.timestamp AS timestamp
                    LIMIT 20
                """)

                if result.is_succeeded():
                    for i in range(result.row_size()):
                        content = result.row_values(i)[0].as_string()
                        source = result.row_values(i)[1].as_string()
                        timestamp = result.row_values(i)[2].as_string()

                        # 计算语义相似度
                        if self.embedding_model:
                            content_vector = self.embedding_model.encode([content])[0]
                            similarity = np.dot(query_vector, content_vector)
                        else:
                            similarity = 0.0

                        if similarity > 0.5:
                            similar_cases.append(
                                {
                                    "content": content,
                                    "source": source,
                                    "timestamp": timestamp,
                                    "similarity": float(similarity),
                                }
                            )

            # 按相似度排序
            similar_cases.sort(key=lambda x: x["similarity"], reverse=True)

            session.release()
            return similar_cases[:limit]

        except Exception as e:
            logger.error(f"❌ 相似案例搜索失败: {e}")
            return []

    async def get_knowledge_statistics(self) -> dict[str, Any]:
        """获取知识图谱统计"""
        if not NEBULA_AVAILABLE or not self.connection_pool:
            return {"error": "NebulaGraph不可用"}

        try:
            session = self.connection_pool.get_session("root", "nebula")
            session.execute("USE legal_kg")

            stats = {}

            # 统计节点数量
            result = session.execute("MATCH (v) RETURN count(v) as total_vertices")
            if result.is_succeeded():
                stats["total_vertices"] = result.row_values(0)[0].as_int()

            # 统计边数量
            result = session.execute("MATCH ()-[e]->() RETURN count(e) as total_edges")
            if result.is_succeeded():
                stats["total_edges"] = result.row_values(0)[0].as_int()

            # 统计实体类型分布
            result = session.execute(
                "MATCH (v:legal_entity) RETURN v.type as type, count(*) as count"
            )
            if result.is_succeeded():
                entity_distribution = {}
                for i in range(result.row_size()):
                    entity_type = result.row_values(i)[0].as_string()
                    count = result.row_values(i)[1].as_int()
                    entity_distribution[entity_type] = count
                stats["entity_distribution"] = entity_distribution

            # 统计关系类型分布
            result = session.execute(
                "MATCH ()-[e:has_relation]->() RETURN e.type as type, count(*) as count"
            )
            if result.is_succeeded():
                relation_distribution = {}
                for i in range(result.row_size()):
                    relation_type = result.row_values(i)[0].as_string()
                    count = result.row_values(i)[1].as_int()
                    relation_distribution[relation_type] = count
                stats["relation_distribution"] = relation_distribution

            session.release()
            stats["timestamp"] = datetime.now().isoformat()

            return stats

        except Exception as e:
            logger.error(f"❌ 获取知识统计失败: {e}")
            return {"error": str(e)}

    async def close(self):
        """关闭连接"""
        if self.connection_pool:
            self.connection_pool.close()
            logger.info("✅ 法律知识图谱增强器已关闭")


@async_main
async def main():
    """测试法律知识图谱增强器"""
    print("⚖️ 测试法律知识图谱增强器...")

    enhancer = LegalKnowledgeEnhancer()

    # 初始化
    if not await enhancer.initialize():
        print("❌ 增强器初始化失败")
        return 1

    try:
        # 测试法律文本
        test_text = """
        根据《中华人民共和国民法典》第一千一百六十五条规定,行为人因过错侵害他人民事权益
        造成损害的,应当承担侵权责任。依照法律规定推定行为人有过错,其不能证明自己没有过错的,
        应当承担侵权责任。
        """

        print("📝 测试法律知识更新...")
        update_result = await enhancer.update_legal_knowledge(test_text, "test")
        if "error" not in update_result:
            print(f"✅ 知识更新成功,识别到 {len(update_result['entities'])} 个实体")
        else:
            print(f"❌ 知识更新失败: {update_result['error']}")

        print("\n🧠 测试法律推理...")
        reasoning_result = await enhancer.legal_reasoning(
            "某人因过错造成他人损害是否需要承担责任?", test_text
        )
        if "error" not in reasoning_result:
            print(f"✅ 法律推理完成,得到 {len(reasoning_result['reasoning_results'])} 个推理结果")
            for result in reasoning_result["reasoning_results"]:
                print(
                    f"   - {result['rule']}: {result['conclusion']} (置信度: {result['confidence']:.2f})"
                )
        else:
            print(f"❌ 法律推理失败: {reasoning_result['error']}")

        print("\n🔍 测试相似案例搜索...")
        similar_cases = await enhancer.search_similar_cases("侵权责任的构成要件", limit=3)
        print(f"✅ 找到 {len(similar_cases)} 个相似案例")
        for case in similar_cases:
            print(f"   - 相似度: {case['similarity']:.2f}, 来源: {case['source']}")

        print("\n📊 获取知识图谱统计...")
        stats = await enhancer.get_knowledge_statistics()
        if "error" not in stats:
            print("✅ 知识图谱统计:")
            print(f"   - 节点总数: {stats.get('total_vertices', 0)}")
            print(f"   - 边总数: {stats.get('total_edges', 0)}")
            print(f"   - 实体类型: {len(stats.get('entity_distribution', {}))}")
            print(f"   - 关系类型: {len(stats.get('relation_distribution', {}))}")
        else:
            print(f"❌ 获取统计失败: {stats['error']}")

        print("\n🎉 法律知识图谱增强器测试完成!")
        return 0

    finally:
        await enhancer.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
