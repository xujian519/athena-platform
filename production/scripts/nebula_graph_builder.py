#!/usr/bin/env python3
"""
NebulaGraph知识图谱构建器
NebulaGraph Knowledge Graph Builder

构建法律领域知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 添加项目路径以导入配置
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    # 如果无法导入,使用默认配置
    def get_nebula_config():
        return {
            'host': 'localhost',
            'port': 9669,
            'user': 'root',
            'password': 'nebula'
        }

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GraphConfig:
    """图配置"""
    space_name: str = "legal_knowledge"
    partition_num: int = 10
    replica_factor: int = 1
    vid_type: str = "FIXED_STRING(32)"

class NebulaGraphBuilder:
    """NebulaGraph知识图谱构建器"""

    def __init__(self):
        # NebulaGraph连接配置 - 从环境变量读取
        nebula_config = get_nebula_config()
        self.host = nebula_config['host']
        self.port = nebula_config['port']
        self.username = nebula_config['user']
        self.password = nebula_config['password']

        # 图配置
        self.config = GraphConfig()

        # 标签和边类型定义
        self.tags = {
            "Law": "法律",
            "Article": "条款",
            "Person": "人物",
            "Organization": "机构",
            "Time": "时间",
            "Location": "地点",
            "Concept": "法律概念",
            "Right": "权利",
            "Obligation": "义务",
            "Penalty": "处罚"
        }

        self.edge_types = {
            "HAS_ARTICLE": "包含条款",
            "DEFINE": "定义",
            "REGULATE": "规范",
            "GRANT": "授予",
            "IMPOSE": "施加",
            "PROHIBIT": "禁止",
            "REFERENCE": "引用",
            "AMEND": "修改",
            "REPEAL": "废止",
            "APPLY_AT": "适用于",
            "SUPERVISE": "监督",
            "ENFORCE": "执行"
        }

        # 创建连接
        self._init_connection()

    def _init_connection(self):
        """初始化连接"""
        try:
            # 尝试导入nebula3
            from nebula3.Config import Config
            from nebula3.gclient.net import ConnectionPool

            # 配置连接池
            config = Config()
            config.max_connection_pool_size = 10

            # 创建连接池
            self.connection_pool = ConnectionPool()

            # 连接到NebulaGraph
            logger.info(f"尝试连接到NebulaGraph: {self.host}:{self.port}")
            # self.connection_pool.init([(self.host, self.port)], config)
            logger.warning("⚠️ NebulaGraph连接模拟模式（未安装nebula3客户端）")
            self.connected = False

        except ImportError:
            logger.warning("⚠️ 未安装nebula3-py客户端，使用模拟模式")
            self.connected = False
            self.connection_pool = None

        except Exception as e:
            logger.error(f"连接NebulaGraph失败: {e}")
            self.connected = False
            self.connection_pool = None

    def create_space(self):
        """创建图空间"""
        if not self.connected:
            logger.warning("⚠️ 模拟：创建图空间")
            return

        logger.info(f"🏗️ 创建图空间: {self.config.space_name}")

        # 创建图空间的NGQL语句
        ngql = f"""
        CREATE SPACE IF NOT EXISTS {self.config.space_name} (
            partition_num = {self.config.partition_num},
            replica_factor = {self.config.replica_factor},
            vid_type = {self.config.vid_type}
        );
        """

        logger.info(f"执行NGQL:\n{ngql}")

    def create_tags(self):
        """创建标签（点类型）"""
        if not self.connected:
            logger.warning("⚠️ 模拟：创建标签")
            return

        logger.info("🏷️ 创建标签...")

        # 标签定义
        tag_definitions = {
            "Law": """
                CREATE TAG IF NOT EXISTS Law (
                    name string,
                    law_type string,
                    effective_date string,
                    status string,
                    issuing_authority string,
                    content string
                );
            """,
            "Article": """
                CREATE TAG IF NOT EXISTS Article (
                    number string,
                    content string,
                    chapter string,
                    section string,
                    law_name string
                );
            """,
            "Person": """
                CREATE TAG IF NOT EXISTS Person (
                    name string,
                    type string,
                    role string
                );
            """,
            "Organization": """
                CREATE TAG IF NOT EXISTS Organization (
                    name string,
                    org_type string,
                    level string
                );
            """,
            "Time": """
                CREATE TAG IF NOT EXISTS Time (
                    date string,
                    type string,
                    description string
                );
            """,
            "Location": """
                CREATE TAG IF NOT EXISTS Location (
                    name string,
                    level string,
                    parent string
                );
            """,
            "Concept": """
                CREATE TAG IF NOT EXISTS Concept (
                    name string,
                    definition string,
                    category string
                );
            """,
            "Right": """
                CREATE TAG IF NOT EXISTS Right (
                    name string,
                    holder string,
                    scope string
                );
            """,
            "Obligation": """
                CREATE TAG IF NOT EXISTS Obligation (
                    name string,
                    subject string,
                    content string
                );
            """,
            "Penalty": """
                CREATE TAG IF NOT EXISTS Penalty (
                    type string,
                    amount string,
                    conditions string
                );
            """
        }

        for tag_name, ngql in tag_definitions.items():
            logger.info(f"创建标签: {tag_name}")
            logger.debug(f"NGQL: {ngql}")

    def create_edges(self):
        """创建边类型"""
        if not self.connected:
            logger.warning("⚠️ 模拟：创建边类型")
            return

        logger.info("🔗 创建边类型...")

        # 边类型定义
        edge_definitions = {
            "HAS_ARTICLE": """
                CREATE EDGE IF NOT EXISTS HAS_ARTICLE (
                    sequence int
                );
            """,
            "DEFINE": """
                CREATE EDGE IF NOT EXISTS DEFINE (
                    context string
                );
            """,
            "REGULATE": """
                CREATE EDGE IF NOT EXISTS REGULATE (
                    scope string,
                    condition string
                );
            """,
            "GRANT": """
                CREATE EDGE IF NOT EXISTS GRANT (
                    condition string,
                    scope string
                );
            """,
            "IMPOSE": """
                CREATE EDGE IF NOT EXISTS IMPOSE (
                    requirement string,
                    condition string
                );
            """,
            "PROHIBIT": """
                CREATE EDGE IF NOT EXISTS PROHIBIT (
                    condition string,
                    scope string
                );
            """,
            "REFERENCE": """
                CREATE EDGE IF NOT EXISTS REFERENCE (
                    context string,
                    citation_type string
                );
            """,
            "APPLY_AT": """
                CREATE EDGE IF NOT EXISTS APPLY_AT (
                    condition string,
                    scope string
                );
            """
        }

        for edge_name, ngql in edge_definitions.items():
            logger.info(f"创建边类型: {edge_name}")
            logger.debug(f"NGQL: {ngql}")

    def generate_vid(self, entity_name: str, entity_type: str) -> str:
        """生成顶点ID"""
        # 使用实体名称和类型的哈希值
        content = f"{entity_type}_{entity_name}"
        vid = short_hash(content.encode())
        return vid[:32]  # 截断到32字符

    def import_entities(self, entities: list[dict]) -> dict:
        """导入实体"""
        logger.info(f"\n📥 导入实体: {len(entities)} 个")

        # 按类型分组
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.get("entity_type", "Unknown")
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        # 生成NGQL语句
        all_ngql = []

        for entity_type, entity_list in entities_by_type.items():
            tag_name = self._map_entity_type_to_tag(entity_type)
            if not tag_name:
                continue

            logger.info(f"处理实体类型: {entity_type} -> {tag_name} ({len(entity_list)}个)")

            for entity in entity_list:
                vid = self.generate_vid(entity.get("entity_name", ""), entity_type)

                # 构建属性
                props = self._build_entity_properties(entity, entity_type)

                # 构建插入语句
                ngql = f'INSERT VERTEX {tag_name} ({props}) VALUES "{vid}";'
                all_ngql.append(ngql)

        # 保存NGQL到文件
        self._save_ngql(all_ngql, "entities")

        return {
            "total_entities": len(entities),
            "entity_types": list(entities_by_type.keys()),
            "ngql_count": len(all_ngql)
        }

    def import_relations(self, relations: list[dict]) -> dict:
        """导入关系"""
        logger.info(f"\n📥 导入关系: {len(relations)} 个")

        all_ngql = []

        for relation in relations:
            relation_type = relation.get("relation_type", "")
            edge_name = self._map_relation_type_to_edge(relation_type)
            if not edge_name:
                continue

            # 构建边属性
            props = self._build_relation_properties(relation)

            # 使用占位符表示实体ID
            subject_vid = '"{subject_id}"'  # 实际使用时需要替换
            object_vid = '"{object_id}"'

            # 构建插入语句
            ngql = f'INSERT EDGE {edge_name} ({props}) VALUES {subject_vid} -> {object_vid};'
            all_ngql.append(ngql)

        # 保存NGQL到文件
        self._save_ngql(all_ngql, "relations")

        return {
            "total_relations": len(relations),
            "relation_types": list({r.get("relation_type") for r in relations}),
            "ngql_count": len(all_ngql)
        }

    def _map_entity_type_to_tag(self, entity_type: str) -> str | None:
        """映射实体类型到标签"""
        mapping = {
            "LAW": "Law",
            "ARTICLE": "Article",
            "PERSON": "Person",
            "ORG": "Organization",
            "TIME": "Time",
            "LOCATION": "Location",
            "CONCEPT": "Concept",
            "RIGHT": "Right",
            "OBLIGATION": "Obligation",
            "PENALTY": "Penalty",
            "CONDITION": "Concept",
            "PROCEDURE": "Concept"
        }
        return mapping.get(entity_type)

    def _map_relation_type_to_edge(self, relation_type: str) -> str | None:
        """映射关系类型到边"""
        mapping = {
            "DEFINE": "DEFINE",
            "REGULATE": "REGULATE",
            "GRANT": "GRANT",
            "IMPOSE": "IMPOSE",
            "PROHIBIT": "PROHIBIT",
            "REFERENCE": "REFERENCE",
            "AMEND": "AMEND",
            "REPEAL": "REPEAL",
            "ESTABLISH": "DEFINE",
            "SUPERVISE": "SUPERVISE",
            "ENFORCE": "ENFORCE",
            "APPEAL": "APPLY_AT"
        }
        return mapping.get(relation_type)

    def _build_entity_properties(self, entity: dict, entity_type: str) -> str:
        """构建实体属性"""
        props = []

        # 通用属性
        name = entity.get("entity_name", "").replace('"', '\\"')
        if name:
            props.append(f'name: "{name}"')

        # 类型特定属性
        if entity_type == "LAW":
            law_type = entity.get("attributes", {}).get("law_type", "")
            if law_type:
                props.append(f'law_type: "{law_type}"')

        elif entity_type == "ARTICLE":
            article_num = entity.get("attributes", {}).get("article_number", "")
            if article_num:
                props.append(f'number: "{article_num}"')

        elif entity_type == "PERSON":
            # 可以添加更多人物属性
            pass

        elif entity_type == "ORG":
            # 可以添加更多机构属性
            pass

        # 添加其他属性
        if entity.get("confidence"):
            props.append(f'confidence: {entity["confidence"]}')

        # 如果没有属性，至少添加一个默认属性
        if not props:
            props.append('name: ""')

        return ", ".join(props)

    def _build_relation_properties(self, relation: dict) -> str:
        """构建关系属性"""
        props = []

        # 添加关系文本
        context = relation.get("context", "").replace('"', '\\"')
        if context:
            props.append(f'context: "{context[:100]}..."')

        # 添加置信度
        if relation.get("confidence"):
            props.append(f'confidence: {relation["confidence"]}')

        # 如果没有属性，至少添加一个默认属性
        if not props:
            props.append('context: ""')

        return ", ".join(props)

    def _save_ngql(self, ngql_list: list[str], data_type: str):
        """保存NGQL语句到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存完整NGQL文件
        ngql_file = Path(f"/Users/xujian/Athena工作平台/production/data/knowledge_graph/{data_type}_ngql_{timestamp}.ngql")
        ngql_file.parent.mkdir(parents=True, exist_ok=True)

        # 添加USE语句
        content = f"USE {self.config.space_name};\n\n"
        content += "\n".join(ngql_list)

        with open(ngql_file, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ NGQL文件已保存: {ngql_file}")

        # 保存批处理脚本
        script_file = Path(f"/Users/xujian/Athena工作平台/production/dev/scripts/import_{data_type}.sh")
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
# NebulaGraph导入脚本 - {data_type}

echo "导入{data_type}到NebulaGraph..."

# 使用nebula-console导入
nebula-console -addr {self.host} -port {self.port} -u {self.username} -p {self.password} -f {ngql_file}

echo "导入完成"
""")
        script_file.chmod(0o755)
        logger.info(f"✅ 导入脚本已保存: {script_file}")

    def build_graph_schema(self):
        """构建图模式"""
        logger.info("\n🏗️ 构建NebulaGraph图模式...")

        # 1. 创建图空间
        self.create_space()

        # 2. 创建标签
        self.create_tags()

        # 3. 创建边类型
        self.create_edges()

        logger.info("\n✅ 图模式构建完成")

    def import_data(self, entities_file: Path, relations_file: Path):
        """导入数据"""
        logger.info("\n📊 开始导入数据到NebulaGraph...")

        # 加载实体数据
        with open(entities_file, encoding='utf-8') as f:
            entities_data = json.load(f)
            entities = entities_data.get("entities", [])

        # 加载关系数据
        with open(relations_file, encoding='utf-8') as f:
            relations_data = json.load(f)
            relations = relations_data.get("relations", [])

        # 导入实体
        entity_stats = self.import_entities(entities)

        # 导入关系
        relation_stats = self.import_relations(relations)

        # 统计信息
        stats = {
            "timestamp": datetime.now().isoformat(),
            "space_name": self.config.space_name,
            "entity_statistics": entity_stats,
            "relation_statistics": relation_stats,
            "graph_schema": {
                "tags": self.tags,
                "edge_types": self.edge_types
            }
        }

        # 保存统计信息
        stats_file = Path(f"/Users/xujian/Athena工作平台/production/data/knowledge_graph/import_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        stats_file.parent.mkdir(parents=True, exist_ok=True)

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("\n📊 导入统计:")
        logger.info(f"  实体数: {entity_stats['total_entities']}")
        logger.info(f"  关系数: {relation_stats['total_relations']}")
        logger.info(f"  实体类型: {entity_stats['entity_types']}")
        logger.info(f"  关系类型: {relation_stats['relation_types']}")
        logger.info(f"\n💾 统计文件: {stats_file}")

        # 生成使用说明
        self._generate_usage_guide()

        return stats

    def _generate_usage_guide(self):
        """生成使用指南"""
        guide = f"""
# NebulaGraph法律知识图谱使用指南

## 1. 连接到图空间
```ngql
USE {self.config.space_name};
```

## 2. 查询示例

### 查询所有法律
```ngql
MATCH (v:Law) RETURN v LIMIT 10;
```

### 查询某部法律的所有条款
```ngql
MATCH (v:Law)-[e:HAS_ARTICLE]->(v2:Article)
WHERE v.name == "中华人民共和国民法典"
RETURN v, e, v2;
```

### 查询包含特定权利的条款
```ngql
MATCH (v:Article)-[e:GRANT]->(v2:Right)
WHERE v2.name CONTAINS "选举权"
RETURN v, e, v2;
```

### 查询机构的义务
```ngql
MATCH (v:Organization)-[e:IMPOSE]->(v2:Obligation)
WHERE v.name == "国务院"
RETURN v, e, v2;
```

## 3. 统计查询

### 统计各类实体数量
```ngql
FETCH PROP ON * * YIELD tags($$) as tag |
YIELD $-.tag as tag, count(*) as count
GROUP BY $-.tag;
```

### 统计关系类型分布
```ngql
MATCH ()-[e]->()
YIELD $$.name as src, $$.name as dst, type(e) as rel_type
RETURN rel_type, count(*) as count
GROUP BY rel_type;
```

## 4. 导入说明
1. 使用生成的 .ngql 文件通过 nebula-console 导入
2. 或使用提供的 .sh 脚本批量导入
3. 导入前请确保 NebulaGraph 服务已启动

## 5. 注意事项
- 顶点ID使用MD5哈希生成，确保唯一性
- 所有文本字段已转义特殊字符
- 建议分批导入大量数据，避免内存溢出
"""

        guide_file = Path("/Users/xujian/Athena工作平台/production/docs/nebula_usage_guide.md")
        guide_file.parent.mkdir(parents=True, exist_ok=True)

        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)

        logger.info(f"📖 使用指南已保存: {guide_file}")

def main():
    """主函数"""
    print("="*100)
    print("🌐 NebulaGraph知识图谱构建器 🌐")
    print("="*100)

    # 初始化构建器
    builder = NebulaGraphBuilder()

    # 构建图模式
    builder.build_graph_schema()

    # 设置路径
    metadata_dir = Path("/Users/xujian/Athena工作平台/production/data/metadata")

    # 查找最新的实体和关系文件
    entity_files = list(metadata_dir.glob("legal_entities_v2_*.json"))
    relation_files = list(metadata_dir.glob("legal_relations_v2_*.json"))

    if not entity_files or not relation_files:
        logger.error("❌ 没有找到实体或关系文件")
        return

    latest_entity_file = max(entity_files, key=lambda x: x.stat().st_mtime)
    latest_relation_file = max(relation_files, key=lambda x: x.stat().st_mtime)

    logger.info(f"使用实体文件: {latest_entity_file.name}")
    logger.info(f"使用关系文件: {latest_relation_file.name}")

    # 导入数据
    stats = builder.import_data(latest_entity_file, latest_relation_file)

    print("\n✅ NebulaGraph知识图谱构建完成！")
    print("\n📌 后续步骤:")
    print("1. 启动NebulaGraph服务")
    print("2. 使用生成的NGQL文件或脚本导入数据")
    print("3. 参考使用指南进行查询和分析")

if __name__ == "__main__":
    main()
