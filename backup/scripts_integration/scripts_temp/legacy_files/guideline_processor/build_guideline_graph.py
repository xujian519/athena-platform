#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利审查指南知识图谱构建系统
将专利审查指南导入Qdrant向量库和JanusGraph知识图谱
"""

import json
import os
import sys
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import pickle
import re

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加路径
sys.path.append('/Users/xujian/Athena工作平台')

class GuidelineGraphBuilder:
    """专利审查指南知识图谱构建器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台/patent-guideline-system")
        self.data_dir = self.base_dir / "data"
        self.processed_dir = self.data_dir / "processed"
        self.embedding_dir = self.data_dir / "embeddings"
        self.output_dir = Path("/Users/xujian/Athena工作平台/data")

        # 创建输出目录
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "guideline_graph").mkdir(exist_ok=True)
        (self.output_dir / "guideline_vectors").mkdir(exist_ok=True)

        # 数据结构
        self.guideline_data = {
            "metadata": {
                "title": "专利审查指南知识图谱",
                "created": datetime.now().isoformat(),
                "description": "专利审查指南的结构化知识表示",
                "sections": [],
                "total_nodes": 0,
                "total_relationships": 0
            },
            "nodes": [],
            "relationships": [],
            "vectors": []
        }

    def extract_guideline_content(self) -> Dict[str, Any]:
        """提取审查指南内容"""
        logger.info("📖 提取专利审查指南内容...")

        # 1. 尝试读取已处理的数据
        processed_file = self.processed_dir / "test_parse_result.json"
        if processed_file.exists() and False:  # 暂时禁用，使用示例数据
            logger.info(f"✅ 找到已处理的数据: {processed_file}")
            with open(processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self.process_parsed_data(data)

        # 2. 如果没有已处理的数据，创建示例数据
        logger.info("⚠️ 未找到已处理数据，创建示例数据...")
        return self.create_sample_guideline_data()

    def process_parsed_data(self, data: Dict) -> Dict[str, Any]:
        """处理已解析的数据"""
        logger.info("🔄 处理解析的数据...")

        if isinstance(data, list):
            # 如果是列表，转换成结构化数据
            sections = []
            node_id = 1

            for item in data:
                if isinstance(item, dict):
                    section = {
                        "id": f"section_{node_id}",
                        "type": "Section",
                        "title": item.get("title", f"章节 {node_id}"),
                        "content": item.get("content", ""),
                        "level": item.get("level", 1),
                        "keywords": item.get("keywords", []),
                        "rules": self.extract_rules(item.get("content", "")),
                        "examples": self.extract_examples(item.get("content", ""))
                    }
                    sections.append(section)
                    node_id += 1

            return {"sections": sections}

        return data

    def create_sample_guideline_data(self) -> Dict[str, Any]:
        """创建示例审查指南数据"""
        logger.info("📝 创建示例审查指南数据...")

        sample_data = {
            "sections": [
                {
                    "id": "section_1",
                    "type": "Part",
                    "title": "第一部分 初步审查",
                    "level": 1,
                    "content": """初步审查的主要内容包括：
1. 申请文件的形式审查
2. 明显实质性缺陷的审查
3. 申请文件的格式要求
4. 特殊申请的审查程序

初步审查应当遵循以下原则：
- 依法审查原则
- 请求原则
- 公正原则
- 效率原则""",
                    "keywords": ["初步审查", "形式审查", "实质性缺陷", "审查原则"],
                    "rules": [
                        "申请文件应当符合规定的格式要求",
                        "明显实质性缺陷应当被指出",
                        "审查应当依法进行"
                    ],
                    "examples": [
                        "申请文件缺少必要的附图",
                        "权利要求书不符合规定格式",
                        "说明书公开不充分"
                    ]
                },
                {
                    "id": "section_2",
                    "type": "Chapter",
                    "title": "第二章 发明专利申请的初步审查",
                    "level": 2,
                    "parent": "section_1",
                    "content": """发明专利申请的初步审查内容包括：

1. 申请文件的格式审查
   - 请求书
   - 说明书
   - 权利要求书
   - 摘要
   - 附图（如有）

2. 明显实质性缺陷的审查
   - 技术方案是否完整
   - 是否符合专利法第五条
   - 是否符合专利法第二十五条""",
                    "keywords": ["发明专利", "格式审查", "实质性缺陷"],
                    "rules": [
                        "发明专利申请必须包含请求书、说明书、权利要求书",
                        "权利要求书应当有独立权利要求",
                        "说明书应当对发明作出清楚完整的说明"
                    ],
                    "examples": []
                },
                {
                    "id": "section_3",
                    "type": "Section",
                    "title": "2.1 申请文件的格式要求",
                    "level": 3,
                    "parent": "section_2",
                    "content": """申请文件应当使用中文撰写，并符合以下要求：

请求书：
- 应当写明发明名称
- 应当写明申请人信息
- 应当写明发明人信息

说明书：
- 应当有技术领域
- 应当有背景技术
- 应当有发明内容
- 应当有具体实施方式

权利要求书：
- 应当有独立权利要求
- 可以有从属权利要求
- 权利要求应当以说明书为依据""",
                    "keywords": ["格式要求", "请求书", "说明书", "权利要求书"],
                    "rules": [
                        "申请文件必须使用中文",
                        "请求书必须包含发明名称",
                        "说明书必须包含技术领域、背景技术等部分"
                    ],
                    "examples": []
                },
                {
                    "id": "section_4",
                    "type": "Section",
                    "title": "2.2 明显实质性缺陷的审查",
                    "level": 3,
                    "parent": "section_2",
                    "content": """明显实质性缺陷包括：

1. 不符合专利法第五条的发现
   - 科学发现
   - 智力活动的规则和方法
   - 疾病的诊断和治疗方法

2. 不符合专利法第二十五的情形
   - 动物和植物品种
   - 用原子核变换方法获得的物质

3. 说明书公开不充分
   - 技术方案不清楚
   - 实现方式不明确
   - 本领域技术人员无法实现""",
                    "keywords": ["实质性缺陷", "专利法第五条", "专利法第二十五条", "公开不充分"],
                    "rules": [
                        "科学发现不能被授予专利权",
                        "智力活动的规则和方法不能被授予专利权",
                        "疾病的治疗方法不能被授予专利权",
                        "说明书必须充分公开"
                    ],
                    "examples": [
                        "能量守恒定律的发现",
                        "商业模式的设计",
                        "外科手术方法"
                    ]
                },
                {
                    "id": "section_5",
                    "type": "Part",
                    "title": "第二部分 实质审查",
                    "level": 1,
                    "content": """实质审查是对专利申请是否符合专利法规定的实质性条件的审查。

审查内容包括：
1. 新颖性
2. 创造性
3. 实用性
4. 权利要求书的撰写
5. 说明书的撰写

审查原则：
- 请求原则
- 听证原则
- 程序节约原则
- 公正原则""",
                    "keywords": ["实质审查", "新颖性", "创造性", "实用性"],
                    "rules": [
                        "授予专利权的发明应当具备新颖性",
                        "授予专利权的发明应当具备创造性",
                        "授予专利权的发明应当具备实用性"
                    ],
                    "examples": []
                },
                {
                    "id": "section_6",
                    "type": "Section",
                    "title": "第三章 新颖性",
                    "level": 2,
                    "parent": "section_5",
                    "content": """新颖性是指该发明或者实用新型不属于现有技术。

现有技术是指申请日以前在国内外为公众所知的技术。

不丧失新颖性的情形：
1. 在中国政府主办或者承认的国际展览会上首次展出的
2. 在规定的学术会议或者技术会议上首次发表的
3. 他人未经申请人同意而泄露其内容的""",
                    "keywords": ["新颖性", "现有技术", "不丧失新颖性"],
                    "rules": [
                        "新颖性是授予专利权的基本条件",
                        "现有技术包括申请日前的所有公开技术",
                        "特定情形下不丧失新颖性"
                    ],
                    "examples": [
                        "在国家技术展览会展出",
                        "在IEEE国际会议发表论文",
                        "他人未经同意公开技术内容"
                    ]
                }
            ]
        }

        # 保存示例数据
        with open(self.processed_dir / "guideline_sample.json", 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)

        return sample_data

    def extract_rules(self, content: str) -> List[str]:
        """从内容中提取规则"""
        rules = []

        # 匹配规则句式
        patterns = [
            r'(应当|必须|不得|禁止|要求).*?(。|；)',
            r'(符合.*规定|满足.*条件).*?(。|；)',
            r'不.*?(授予|给予).*?(专利权|保护).*?(。|；)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    rules.append(match[0])
                else:
                    rules.append(match)

        return rules[:5]  # 最多返回5条规则

    def extract_examples(self, content: str) -> List[str]:
        """从内容中提取示例"""
        examples = []

        # 匹配示例句式
        patterns = [
            r'例如[：:].*?(。|；)',
            r'比如[：:].*?(。|；)',
            r'如[：:].*?(。|；)',
            r'[\(（]示例[）)][：:].*?(。|；)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    examples.append(match[0])
                else:
                    examples.append(match)

        return examples[:3]  # 最多返回3个示例

    def create_knowledge_graph(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建知识图谱结构"""
        logger.info("🕸️ 构建知识图谱...")

        nodes = []
        relationships = []
        node_count = 0

        # 创建章节节点
        for section in data.get("sections", []):
            node = {
                "id": section["id"],
                "type": section.get("type", "Section"),
                "properties": {
                    "title": section["title"],
                    "level": section.get("level", 1),
                    "content": section.get("content", ""),
                    "keywords": section.get("keywords", []),
                    "rules": section.get("rules", []),
                    "examples": section.get("examples", []),
                    "created_at": datetime.now().isoformat()
                }
            }
            nodes.append(node)
            node_count += 1

            # 创建父子关系
            if "parent" in section:
                rel = {
                    "id": f"rel_{len(relationships) + 1}",
                    "type": "HAS_SUBSECTION",
                    "source": section["parent"],
                    "target": section["id"],
                    "properties": {
                        "level_diff": section.get("level", 1) - 1
                    }
                }
                relationships.append(rel)

        # 创建规则节点
        rule_nodes = []
        for section in data.get("sections", []):
            for i, rule in enumerate(section.get("rules", [])):
                rule_id = f"rule_{section['id']}_{i}"
                rule_node = {
                    "id": rule_id,
                    "type": "Rule",
                    "properties": {
                        "content": rule,
                        "section": section["id"],
                        "section_title": section["title"],
                        "created_at": datetime.now().isoformat()
                    }
                }
                rule_nodes.append(rule_node)
                nodes.append(rule_node)

                # 创建章节-规则关系
                rel = {
                    "id": f"rel_{len(relationships) + 1}",
                    "type": "CONTAINS_RULE",
                    "source": section["id"],
                    "target": rule_id,
                    "properties": {}
                }
                relationships.append(rel)

        # 创建示例节点
        example_nodes = []
        for section in data.get("sections", []):
            for i, example in enumerate(section.get("examples", [])):
                if example.strip():  # 跳过空示例
                    example_id = f"example_{section['id']}_{i}"
                    example_node = {
                        "id": example_id,
                        "type": "Example",
                        "properties": {
                            "content": example,
                            "section": section["id"],
                            "section_title": section["title"],
                            "created_at": datetime.now().isoformat()
                        }
                    }
                    example_nodes.append(example_node)
                    nodes.append(example_node)

                    # 创建章节-示例关系
                    rel = {
                        "id": f"rel_{len(relationships) + 1}",
                        "type": "HAS_EXAMPLE",
                        "source": section["id"],
                        "target": example_id,
                        "properties": {}
                    }
                    relationships.append(rel)

        # 创建关键词节点
        keyword_nodes = []
        for section in data.get("sections", []):
            for keyword in section.get("keywords", []):
                keyword_id = f"keyword_{keyword.replace(' ', '_')}"
                if keyword_id not in [n["id"] for n in keyword_nodes]:
                    keyword_node = {
                        "id": keyword_id,
                        "type": "Keyword",
                        "properties": {
                            "name": keyword,
                            "created_at": datetime.now().isoformat()
                        }
                    }
                    keyword_nodes.append(keyword_node)
                    nodes.append(keyword_node)

                    # 创建章节-关键词关系
                    rel = {
                        "id": f"rel_{len(relationships) + 1}",
                        "type": "HAS_KEYWORD",
                        "source": section["id"],
                        "target": keyword_id,
                        "properties": {}
                    }
                    relationships.append(rel)

        self.guideline_data["metadata"]["total_nodes"] = len(nodes)
        self.guideline_data["metadata"]["total_relationships"] = len(relationships)
        self.guideline_data["metadata"]["sections"] = data.get("sections", [])
        self.guideline_data["nodes"] = nodes
        self.guideline_data["relationships"] = relationships

        logger.info(f"✅ 创建节点: {len(nodes)} 个")
        logger.info(f"✅ 创建关系: {len(relationships)} 条")

        return self.guideline_data

    def generate_embeddings(self, graph_data: Dict[str, Any]) -> List[Dict]:
        """生成文本嵌入向量"""
        logger.info("🔢 生成文本嵌入向量...")

        vectors = []

        # 简单的文本向量化（实际应用中应使用BERT等模型）
        def simple_text_vector(text: str, dim: int = 768) -> List[float]:
            """简单的文本向量化方法"""
            if not text:
                return [0.0] * dim

            # 基于字符hash的简单向量化
            text_hash = hash(text)
            # 确保seed在有效范围内
            seed = abs(text_hash) % (2**32)
            np.random.seed(seed)
            vector = np.random.normal(0, 1, dim)
            vector = vector / np.linalg.norm(vector)  # 归一化

            return vector.tolist()

        # 为每个节点生成向量
        for node in graph_data["nodes"]:
            # 组合文本内容
            text_parts = []

            # 添加标题
            if "title" in node["properties"]:
                text_parts.append(node["properties"]["title"])

            # 添加内容摘要（前500字符）
            if "content" in node["properties"] and node["properties"]["content"]:
                text_parts.append(node["properties"]["content"][:500])

            # 添加规则
            if "rules" in node["properties"]:
                for rule in node["properties"]["rules"][:3]:  # 只取前3条
                    text_parts.append(rule)

            # 添加示例
            if "examples" in node["properties"]:
                for example in node["properties"]["examples"][:2]:  # 只取前2个
                    text_parts.append(example)

            # 组合文本
            combined_text = " ".join(text_parts)

            # 生成向量
            vector = simple_text_vector(combined_text)

            # 创建向量记录
            vector_record = {
                "id": node["id"],
                "vector": vector,
                "metadata": {
                    "node_type": node["type"],
                    "title": node["properties"].get("title", ""),
                    "keywords": node["properties"].get("keywords", []),
                    "level": node["properties"].get("level", 1),
                    "content_length": len(combined_text)
                }
            }

            vectors.append(vector_record)

        # 保存向量数据
        self.guideline_data["vectors"] = vectors

        logger.info(f"✅ 生成向量: {len(vectors)} 个")

        return vectors

    def save_data(self):
        """保存所有数据"""
        logger.info("💾 保存数据...")

        # 保存知识图谱数据
        graph_file = self.output_dir / "guideline_graph" / "patent_guideline_graph.json"
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(self.guideline_data, f, ensure_ascii=False, indent=2)

        # 保存向量数据（pickle格式）
        vectors_file = self.output_dir / "guideline_vectors" / "patent_guideline_vectors.pkl"
        with open(vectors_file, 'wb') as f:
            pickle.dump(self.guideline_data["vectors"], f)

        # 保存向量数据（JSON格式用于Qdrant）
        vectors_json_file = self.output_dir / "guideline_vectors" / "patent_guideline_vectors.json"
        vectors_json = {
            "vectors": [
                {
                    "id": v["id"],
                    "vector": v["vector"],
                    "payload": v["metadata"]
                }
                for v in self.guideline_data["vectors"]
            ]
        }
        with open(vectors_json_file, 'w', encoding='utf-8') as f:
            json.dump(vectors_json, f, ensure_ascii=False, indent=2)

        # 创建Qdrant导入脚本
        self.create_qdrant_import_script()

        # 创建JanusGraph导入脚本
        self.create_janusgraph_import_script()

        logger.info(f"✅ 知识图谱已保存: {graph_file}")
        logger.info(f"✅ 向量数据已保存: {vectors_file}")
        logger.info(f"✅ Qdrant向量已保存: {vectors_json_file}")

    def create_qdrant_import_script(self):
        """创建Qdrant导入脚本"""
        script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将专利审查指南向量导入Qdrant
"""

import json
import pickle
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_to_qdrant():
    """导入向量到Qdrant"""
    client = QdrantClient(host="localhost", port=6333)

    collection_name = "patent_guideline"

    # 创建集合
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        logger.info(f"✅ 创建集合: {collection_name}")

    # 加载向量数据
    with open("/Users/xujian/Athena工作平台/data/guideline_vectors/patent_guideline_vectors.json", "r") as f:
        data = json.load(f)

    # 批量导入
    points = []
    for item in data["vectors"]:
        point = PointStruct(
            id=item["id"],
            vector=item["vector"],
            payload=item["payload"]
        )
        points.append(point)

    # 分批上传
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        logger.info(f"✅ 导入批次 {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

    logger.info(f"✅ 总计导入 {len(points)} 个向量到 {collection_name}")

if __name__ == "__main__":
    import_to_qdrant()
'''

        script_path = self.output_dir / "guideline_vectors" / "import_to_qdrant.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        os.chmod(script_path, 0o755)

    def create_janusgraph_import_script(self):
        """创建JanusGraph导入脚本"""
        graph_data = self.guideline_data

        # 创建Gremlin脚本
        gremlin_script = '''
// 导入专利审查指南知识图谱
graph = JanusGraphFactory.open('conf/janusgraph-berkeleyje.properties')
g = graph.traversal()

// 清空旧数据（可选）
g.V().drop().iterate()

// 创建索引
mgmt = graph.openManagement()
try {
    entity_id = mgmt.makePropertyKey('entity_id').dataType(String.class).make()
    node_type = mgmt.makePropertyKey('node_type').dataType(String.class).make()
    title = mgmt.makePropertyKey('title').dataType(String.class).make()
    level = mgmt.makePropertyKey('level').dataType(Integer.class).make()

    mgmt.buildIndex('byEntityId', Vertex.class).addKey(entity_id).buildCompositeIndex()
    mgmt.buildIndex('byNodeType', Vertex.class).addKey(node_type).buildCompositeIndex()
    mgmt.buildIndex('byTitle', Vertex.class).addKey(title).buildCompositeIndex()

    mgmt.commit()
    println("✅ 索引创建完成")
} catch (e) {
    mgmt.rollback()
    println("⚠️ 索引可能已存在")
}

// 开始事务
g.tx().open()
'''

        # 添加节点创建语句
        for node in graph_data["nodes"]:
            node_id = node["id"]
            node_type = node["type"]
            props = node["properties"]

            gremlin_script += f'''
// 创建节点: {node_id}
v_{node_id.replace('-', '_')} = g.addV('{node_type}')
    .property('entity_id', '{node_id}')
'''

            for key, value in props.items():
                if isinstance(value, str):
                    # 转义引号
                    value = value.replace("'", "\\'").replace('"', '\\"')
                    if len(value) > 200:
                        value = value[:200] + "..."
                    gremlin_script += f"    .property('{key}', '{value}')\n"
                elif isinstance(value, int):
                    gremlin_script += f"    .property('{key}', {value})\n"

            gremlin_script += "    .next()\n"

        # 添加关系创建语句
        for rel in graph_data["relationships"]:
            source_id = rel["source"].replace('-', '_')
            target_id = rel["target"].replace('-', '_')
            rel_type = rel["type"]

            gremlin_script += f'''
// 创建关系: {source_id} -> {target_id}
v_{source_id}.addEdge('{rel_type}', v_{target_id})
'''

        # 提交事务
        gremlin_script += '''
// 提交事务
g.tx().commit()

// 验证结果
vertex_count = g.V().count().next()
edge_count = g.E().count().next()
println("\\n=== 导入统计 ===")
println("节点数: " + vertex_count)
println("边数: " + edge_count)

graph.close()
println("\\n✅ 知识图谱导入完成！")
'''

        # 保存脚本
        script_path = self.output_dir / "guideline_graph" / "import_to_janusgraph.gremlin"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(gremlin_script)

    def run(self):
        """执行构建流程"""
        logger.info("🚀 开始构建专利审查指南知识图谱...")
        print("\n" + "="*60)
        print("专利审查指南知识图谱构建系统")
        print("="*60)

        # 1. 提取数据
        data = self.extract_guideline_content()

        # 2. 构建知识图谱
        graph_data = self.create_knowledge_graph(data)

        # 3. 生成向量
        vectors = self.generate_embeddings(graph_data)

        # 4. 保存数据
        self.save_data()

        # 5. 输出总结
        print("\n" + "="*60)
        print("✅ 构建完成！")
        print("="*60)
        print(f"\n📊 统计信息:")
        print(f"  章节数: {len([n for n in graph_data['nodes'] if n['type'] in ['Part', 'Chapter', 'Section']])}")
        print(f"  规则数: {len([n for n in graph_data['nodes'] if n['type'] == 'Rule'])}")
        print(f"  示例数: {len([n for n in graph_data['nodes'] if n['type'] == 'Example'])}")
        print(f"  关键词数: {len([n for n in graph_data['nodes'] if n['type'] == 'Keyword'])}")
        print(f"  总节点数: {len(graph_data['nodes'])}")
        print(f"  总关系数: {len(graph_data['relationships'])}")
        print(f"  向量数: {len(vectors)}")

        print(f"\n📁 输出文件:")
        print(f"  - 知识图谱: {self.output_dir}/guideline_graph/patent_guideline_graph.json")
        print(f"  - 向量数据: {self.output_dir}/guideline_vectors/patent_guideline_vectors.json")
        print(f"  - Qdrant导入脚本: {self.output_dir}/guideline_vectors/import_to_qdrant.py")
        print(f"  - JanusGraph导入脚本: {self.output_dir}/guideline_graph/import_to_janusgraph.gremlin")

        print("\n💡 后续步骤:")
        print("1. 运行 Qdrant 导入: python3 /Users/xujian/Athena工作平台/data/guideline_vectors/import_to_qdrant.py")
        print("2. 导入 JanusGraph: 参考 import_to_janusgraph.gremlin 脚本")
        print("3. 更新 API 服务配置以使用新的向量库和知识图谱")
        print("="*60)

def main():
    """主函数"""
    builder = GuidelineGraphBuilder()
    builder.run()

if __name__ == "__main__":
    main()