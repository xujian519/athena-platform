#!/usr/bin/env python3
"""
NebulaGraph知识图谱构建器 - 同步版本
NebulaGraph Knowledge Graph Builder - Sync Version

连接真实的NebulaGraph数据库

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any

from nebula3.Config import Config
from nebula3.data.ResultSet import ResultSet
from nebula3.gclient.net import ConnectionPool

# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config():
        return {
            'host': 'localhost',
            'port': 9669,
            'user': 'root',
            'password': 'nebula'
        }

logger = logging.getLogger(__name__)

class NebulaGraphBuilderSync:
    """NebulaGraph知识图谱构建器 - 同步版本"""

    def __init__(self,
                 addresses: list[tuple] = None,
                 username: str = None,
                 password: str = None,
                 space_name: str = "patent_rules"):
        """
        初始化NebulaGraph连接

        Args:
            addresses: NebulaGraph服务地址列表，例如 [("127.0.0.1", 9669)]
            username: 用户名 (如果为None,从配置读取)
            password: 密码 (如果为None,从配置读取)
            space_name: 图空间名称
        """
        # 从配置获取默认值
        nebula_config = get_nebula_config()
        self.addresses = addresses or [("127.0.0.1", nebula_config['port'])]
        self.username = username or nebula_config['user']
        self.password = password or nebula_config['password']
        self.space_name = space_name

        # 连接池配置
        self.config = Config()
        self.config.max_connection_pool_size = 10
        self.config.timeout = 60000  # 60秒

        self.pool = None
        self.session = None
        self.initialized = False
        self._lock = threading.Lock()

    def connect(self):
        """连接到NebulaGraph"""
        try:
            # 创建连接池
            self.pool = ConnectionPool()
            # 初始化连接池（同步方法）
            self.pool.init([(host, port) for host, port in self.addresses], self.config)

            # 获取会话
            self.session = self.pool.get_session(self.username, self.password)

            logger.info(f"✅ 成功连接到NebulaGraph: {self.addresses}")
            return True

        except Exception as e:
            logger.error(f"❌ 连接NebulaGraph失败: {str(e)}")
            return False

    def disconnect(self):
        """断开连接"""
        try:
            with self._lock:
                if self.session:
                    self.session.release()
                    self.session = None
                if self.pool:
                    self.pool.close()
                    self.pool = None
            logger.info("✅ 已断开NebulaGraph连接")
        except Exception as e:
            logger.error(f"❌ 断开连接失败: {str(e)}")

    def initialize_space(self):
        """初始化图空间"""
        if not self.connect():
            raise Exception("无法连接到NebulaGraph")

        try:
            # 检查图空间是否存在
            check_space_query = "SHOW SPACES"
            result = self.execute_query(check_space_query)

            if not result.is_succeeded():
                logger.error(f"检查图空间失败: {result.error_msg()}")
                return False

            # 检查图空间是否已存在
            space_exists = False
            if result.is_succeeded():
                for i in range(result.row_size()):
                    space_name = result.row_values(i)[0].as_string()
                    if space_name == self.space_name:
                        space_exists = True
                        break

            # 如果图空间不存在，创建它
            if not space_exists:
                logger.info(f"图空间 {self.space_name} 不存在，正在创建...")

                create_space_query = f"""
                CREATE SPACE IF NOT EXISTS {self.space_name} (
                    partition_num = 10,
                    replica_factor = 1,
                    vid_type = FIXED_STRING(256)
                );
                """

                result = self.execute_query(create_space_query)
                if not result.is_succeeded():
                    logger.error(f"创建图空间失败: {result.error_msg()}")
                    return False

                # 等待图空间创建完成
                time.sleep(5)

            # 使用图空间
            use_space_query = f"USE {self.space_name}"
            result = self.execute_query(use_space_query)
            if not result.is_succeeded():
                logger.error(f"使用图空间失败: {result.error_msg()}")
                return False

            # 创建标签（Tag）
            self._create_tags()

            # 创建边类型（Edge Type）
            self._create_edge_types()

            self.initialized = True
            logger.info(f"✅ 图空间 {self.space_name} 初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化图空间失败: {str(e)}")
            return False

    def _create_tags(self):
        """创建实体标签"""
        tags = {
            "patent": {
                "properties": "string patent_type, string app_date, string grant_date, "
                           "string inventor, string assignee, string ipc"
            },
            "legal_term": {
                "properties": "string definition, string category, string source"
            },
            "tech_field": {
                "properties": "string description, string keywords, string level"
            },
            "case": {
                "properties": "string case_number, string court, string date, string outcome"
            },
            "document": {
                "properties": "string title, string doc_type, string publish_date, string source"
            }
        }

        for tag_name, props in tags.items():
            query = f"CREATE TAG IF NOT EXISTS {tag_name} ({props})"
            result = self.execute_query(query)
            if result.is_succeeded():
                logger.info(f"  ✅ 创建标签: {tag_name}")
            else:
                logger.warning(f"  ⚠️ 创建标签失败: {tag_name} - {result.error_msg()}")

    def _create_edge_types(self):
        """创建边类型"""
        edges = {
            "refers_to": "string relationship_type, double confidence",
            "applies_to": "string context, double relevance",
            "cites": "string citation_type, string position",
            "related_to": "string relation_type, double strength",
            "belongs_to": "string category, string level",
            "regulates": "string scope, string article",
            "exemplifies": "string example_type, string context"
        }

        for edge_name, props in edges.items():
            query = f"CREATE EDGE IF NOT EXISTS {edge_name} ({props})"
            result = self.execute_query(query)
            if result.is_succeeded():
                logger.info(f"  ✅ 创建边类型: {edge_name}")
            else:
                logger.warning(f"  ⚠️ 创建边类型失败: {edge_name} - {result.error_msg()}")

    def execute_query(self, query: str) -> ResultSet:
        """执行查询"""
        if not self.session:
            raise Exception("未连接到NebulaGraph")

        try:
            result = self.session.execute(query)
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {query}\n错误: {str(e)}")
            raise

    def add_entities(self, entities: list[dict[str, Any]]) -> list[str]:
        """添加实体到图中"""
        if not self.initialized:
            self.initialize_space()

        entity_ids = []

        # 按类型分组实体
        entities_by_type = {}
        for entity in entities:
            etype = entity.get('type', 'document')
            if etype == 'PATENT_TYPE':
                etype = 'patent'
            elif etype == 'LEGAL_TERM':
                etype = 'legal_term'
            elif etype == 'TECH_FIELD':
                etype = 'tech_field'
            elif etype == 'TERM':
                etype = 'document'
            else:
                etype = 'document'

            if etype not in entities_by_type:
                entities_by_type[etype] = []
            entities_by_type[etype].append(entity)

        # 批量插入每种类型的实体
        for etype, entity_list in entities_by_type.items():
            # 构建插入语句
            values = []
            for entity in entity_list[:100]:  # 限制批量大小
                name = entity.get('name', entity.get('text', '')).replace('"', '\\"')
                if not name:  # 跳过空名称
                    continue

                properties = entity.get('properties', {})

                # 构建属性字符串
                prop_strs = []
                if 'confidence' in properties:
                    prop_strs.append(f'confidence: {properties["confidence"]}')
                if 'source' in properties:
                    source = str(properties['source']).replace('"', '\\"')
                    prop_strs.append(f'source: "{source}"')
                if 'document_type' in properties:
                    doc_type = str(properties['document_type']).replace('"', '\\"')
                    prop_strs.append(f'document_type: "{doc_type}"')

                prop_str = ", ".join(prop_strs) if prop_strs else ""
                values.append(f'("{name}"{(": " + prop_str) if prop_str else ""})')

            if values:
                # 获取属性名列表
                prop_names = []
                if values and ":" in values[0]:
                    # 从第一个值中提取属性名
                    sample_props = values[0].split(":")[1:]
                    for p in sample_props:
                        if p:
                            prop_name = p.split(",")[0].strip()
                            prop_names.append(prop_name)

                prop_names_str = ", ".join(prop_names) if prop_names else ""

                # 构建查询
                query = f"INSERT VERTEX {etype}"
                if prop_names_str:
                    query += f" ({prop_names_str})"
                query += f" VALUES {', '.join(values)}"

                result = self.execute_query(query)
                if result.is_succeeded():
                    logger.info(f"  ✅ 插入 {len(entity_list)} 个 {etype} 实体")
                    for entity in entity_list:
                        name = entity.get('name', entity.get('text', ''))
                        if name:
                            entity_ids.append(name)
                else:
                    logger.warning(f"  ⚠️ 插入 {etype} 实体失败: {result.error_msg()[:100]}")

        return entity_ids

    def add_relations(self, relations: list[dict[str, Any]]) -> list[str]:
        """添加关系到图中"""
        if not self.initialized:
            self.initialize_space()

        relation_ids = []

        # 按关系类型分组
        relations_by_type = {}
        for relation in relations:
            rtype = relation.get('relation', 'related_to')
            if rtype == 'has_protection_period':
                rtype = 'applies_to'
            elif rtype == 'regulates':
                rtype = 'regulates'
            elif rtype == 'action_on_patent':
                rtype = 'related_to'
            else:
                rtype = 'related_to'

            if rtype not in relations_by_type:
                relations_by_type[rtype] = []
            relations_by_type[rtype].append(relation)

        # 批量插入每种类型的关系
        for rtype, relation_list in relations_by_type.items():
            # 构建插入语句
            values = []
            for relation in relation_list[:100]:  # 限制批量大小
                subject = str(relation.get('subject', '')).replace('"', '\\"')
                obj = str(relation.get('object', '')).replace('"', '\\"')

                if not subject or not obj:  # 跳过空的主语或宾语
                    continue

                properties = relation.get('properties', {})

                # 构建属性字符串
                prop_strs = []
                if 'confidence' in properties:
                    prop_strs.append(f'confidence: {properties["confidence"]}')
                if 'source' in properties:
                    source = str(properties['source']).replace('"', '\\"')
                    prop_strs.append(f'source: "{source}"')
                if 'relation_type' in properties:
                    rel_type = str(properties['relation_type']).replace('"', '\\"')
                    prop_strs.append(f'relation_type: "{rel_type}"')

                prop_str = ", ".join(prop_strs) if prop_strs else ""

                # 确保VID是字符串格式
                subject_vid = f'"{subject}"'
                object_vid = f'"{obj}"'

                values.append(f'{subject_vid} -> {object_vid}{(": " + prop_str) if prop_str else ""})')

            if values:
                # 获取属性名列表
                prop_names = []
                if values and ":" in values[0]:
                    sample_props = values[0].split(":")[1:]
                    for p in sample_props:
                        if p:
                            prop_name = p.split(",")[0].strip()
                            prop_names.append(prop_name)

                prop_names_str = ", ".join(prop_names) if prop_names else ""

                # 构建查询
                query = f"INSERT EDGE {rtype}"
                if prop_names_str:
                    query += f" ({prop_names_str})"
                query += f" VALUES {', '.join(values)}"

                result = self.execute_query(query)
                if result.is_succeeded():
                    logger.info(f"  ✅ 插入 {len(relation_list)} 个 {rtype} 关系")
                    for relation in relation_list:
                        rel_id = f"{relation.get('subject')}-{relation.get('object')}"
                        relation_ids.append(rel_id)
                else:
                    logger.warning(f"  ⚠️ 插入 {rtype} 关系失败: {result.error_msg()[:100]}")

        return relation_ids

    def query_entity(self, entity_name: str) -> dict[str, Any | None]:
        """查询实体"""
        query = f'MATCH (v) WHERE id(v) == "{entity_name}" RETURN v'
        result = self.execute_query(query)

        if result.is_succeeded() and result.row_size() > 0:
            return result.row_values(0)[0].as_map()
        return None

    def query_relations(self, entity_name: str, relation_type: str = None) -> list[dict[str, Any]]:
        """查询关系"""
        if relation_type:
            query = f'MATCH (v1) -[e:{relation_type}]-> (v2) WHERE id(v1) == "{entity_name}" RETURN v1, e, v2'
        else:
            query = f'MATCH (v1) -[e]-> (v2) WHERE id(v1) == "{entity_name}" RETURN v1, e, v2'

        result = self.execute_query(query)

        relations = []
        if result.is_succeeded():
            for record in result:
                v1 = record.values[0].as_node()
                e = record.values[1].as_relationship()
                v2 = record.values[2].as_node()

                relations.append({
                    'subject': v1.get_id().as_string(),
                    'relation': e.rtype(),
                    'object': v2.get_id().as_string(),
                    'properties': e.properties()
                })

        return relations

    def get_graph_stats(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        stats = {}

        # 获取节点统计
        query = 'MATCH (v) RETURN tags(v) as tag, count(*) as count'
        result = self.execute_query(query)

        if result.is_succeeded():
            node_stats = {}
            for record in result:
                tag = record.values[0].as_string() if record.values[0] else 'unknown'
                count = record.values[1].as_int()
                node_stats[tag] = count
            stats['nodes'] = node_stats

        # 获取边统计
        query = 'MATCH () -[e]-> () RETURN type(e) as type, count(*) as count'
        result = self.execute_query(query)

        if result.is_succeeded():
            edge_stats = {}
            for record in result:
                edge_type = record.values[0].as_string() if record.values[0] else 'unknown'
                count = record.values[1].as_int()
                edge_stats[edge_type] = count
            stats['edges'] = edge_stats

        return stats


def test_nebula_connection():
    """测试NebulaGraph连接"""
    builder = NebulaGraphBuilderSync()

    try:
        # 初始化图空间
        success = builder.initialize_space()
        if success:
            print("✅ NebulaGraph连接测试成功！")

            # 添加测试实体
            test_entities = [
                {
                    'name': '发明专利',
                    'type': 'PATENT_TYPE',
                    'properties': {
                        'definition': '对产品、方法或者其改进所提出的新的技术方案',
                        'category': '专利类型',
                        'confidence': 0.95
                    }
                },
                {
                    'name': '专利法',
                    'type': 'LEGAL_TERM',
                    'properties': {
                        'definition': '调整因发明创造而产生的各种社会关系的法律规范',
                        'category': '法律法规',
                        'confidence': 0.98
                    }
                }
            ]

            entity_ids = builder.add_entities(test_entities)
            print(f"✅ 添加测试实体: {len(entity_ids)} 个")

            # 添加测试关系
            test_relations = [
                {
                    'subject': '专利法',
                    'object': '发明专利',
                    'relation': 'regulates',
                    'properties': {
                        'scope': '保护范围',
                        'confidence': 0.9
                    }
                }
            ]

            relation_ids = builder.add_relations(test_relations)
            print(f"✅ 添加测试关系: {len(relation_ids)} 个")

            # 查询测试
            entity = builder.query_entity('发明专利')
            if entity:
                print("✅ 查询实体成功")

            relations = builder.query_relations('专利法')
            print(f"✅ 查询关系成功: {len(relations)} 个")

            # 获取统计信息
            stats = builder.get_graph_stats()
            print(f"✅ 图谱统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")

    finally:
        builder.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_nebula_connection()
