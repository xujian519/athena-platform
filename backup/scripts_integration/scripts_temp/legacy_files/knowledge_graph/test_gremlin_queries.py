#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试JanusGraph Gremlin查询功能
"""

import json
import logging
import requests
import websocket
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GremlinQueryTester:
    """Gremlin查询测试器"""

    def __init__(self):
        self.gremlin_url = "ws://localhost:8182/gremlin"
        self.http_url = "http://localhost:8182/"
        self.query_results = []

    def create_sample_data(self):
        """创建示例测试数据"""
        logger.info("📝 创建示例测试数据...")

        # 定义示例数据
        sample_data = {
            "patents": [
                {
                    "id": "CN202410001234",
                    "title": "基于AI的专利分析系统",
                    "inventor": "张三",
                    "assignee": "Athena科技公司",
                    "category": "人工智能",
                    "application_date": "2024-01-01"
                },
                {
                    "id": "CN202410001235",
                    "title": "专利检索优化方法",
                    "inventor": "李四",
                    "assignee": "Athena科技公司",
                    "category": "信息检索",
                    "application_date": "2024-01-02"
                },
                {
                    "id": "CN202410001236",
                    "title": "智能法律文书生成系统",
                    "inventor": "王五",
                    "assignee": "创新法律科技",
                    "category": "法律科技",
                    "application_date": "2024-01-03"
                }
            ],
            "companies": [
                {
                    "id": "athena_tech",
                    "name": "Athena科技公司",
                    "type": "科技企业",
                    "location": "北京",
                    "founded": "2020"
                },
                {
                    "id": "innovative_legal",
                    "name": "创新法律科技",
                    "type": "法律科技",
                    "location": "上海",
                    "founded": "2019"
                }
            ],
            "inventors": [
                {
                    "id": "zhang_san",
                    "name": "张三",
                    "field": "人工智能",
                    "experience": "10年"
                },
                {
                    "id": "li_si",
                    "name": "李四",
                    "field": "信息检索",
                    "experience": "8年"
                },
                {
                    "id": "wang_wu",
                    "name": "王五",
                    "field": "法律科技",
                    "experience": "12年"
                }
            ],
            "technologies": [
                {
                    "id": "ai_tech",
                    "name": "人工智能",
                    "category": "前沿技术"
                },
                {
                    "id": "ir_tech",
                    "name": "信息检索",
                    "category": "信息技术"
                },
                {
                    "id": "legal_tech",
                    "name": "法律科技",
                    "category": "垂直应用"
                }
            ]
        }

        # 生成Gremlin创建脚本
        creation_script = []

        # 创建专利节点
        creation_script.append("// 创建专利节点")
        for patent in sample_data["patents"]:
            creation_script.append(f"""
g.addV('Patent').property('id', '{patent["id"]}')
 .property('title', '{patent["title"]}')
 .property('inventor', '{patent["inventor"]}')
 .property('assignee', '{patent["assignee"]}')
 .property('category', '{patent["category"]}')
 .property('application_date', '{patent["application_date"]}');
""")

        # 创建公司节点
        creation_script.append("\n// 创建公司节点")
        for company in sample_data["companies"]:
            creation_script.append(f"""
g.addV('Company').property('id', '{company["id"]}')
 .property('name', '{company["name"]}')
 .property('type', '{company["type"]}')
 .property('location', '{company["location"]}')
 .property('founded', '{company["founded"]}');
""")

        # 创建发明人节点
        creation_script.append("\n// 创建发明人节点")
        for inventor in sample_data["inventors"]:
            creation_script.append(f"""
g.addV('Inventor').property('id', '{inventor["id"]}')
 .property('name', '{inventor["name"]}')
 .property('field', '{inventor["field"]}')
 .property('experience', '{inventor["experience"]}');
""")

        # 创建技术节点
        creation_script.append("\n// 创建技术节点")
        for tech in sample_data["technologies"]:
            creation_script.append(f"""
g.addV('Technology').property('id', '{tech["id"]}')
 .property('name', '{tech["name"]}')
 .property('category', '{tech["category"]}');
""")

        # 创建关系
        creation_script.append("\n// 创建专利-公司关系")
        creation_script.append("g.V('CN202410001234').addE('ASSIGNED_TO').to(g.V('athena_tech'));")
        creation_script.append("g.V('CN202410001235').addE('ASSIGNED_TO').to(g.V('athena_tech'));")
        creation_script.append("g.V('CN202410001236').addE('ASSIGNED_TO').to(g.V('innovative_legal'));")

        creation_script.append("\n// 创建专利-发明人关系")
        creation_script.append("g.V('CN202410001234').addE('INVENTED_BY').to(g.V('zhang_san'));")
        creation_script.append("g.V('CN202410001235').addE('INVENTED_BY').to(g.V('li_si'));")
        creation_script.append("g.V('CN202410001236').addE('INVENTED_BY').to(g.V('wang_wu'));")

        creation_script.append("\n// 创建专利-技术关系")
        creation_script.append("g.V('CN202410001234').addE('USES_TECHNOLOGY').to(g.V('ai_tech'));")
        creation_script.append("g.V('CN202410001235').addE('USES_TECHNOLOGY').to(g.V('ir_tech'));")
        creation_script.append("g.V('CN202410001236').addE('USES_TECHNOLOGY').to(g.V('legal_tech'));")

        # 保存创建脚本
        script_path = Path("/Users/xujian/Athena工作平台/data/test_data_creation.gremlin")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(creation_script))

        logger.info(f"✅ 测试数据创建脚本已保存: {script_path}")
        return sample_data

    def generate_query_examples(self):
        """生成Gremlin查询示例"""
        logger.info("🔍 生成Gremlin查询示例...")

        queries = {
            "基础查询": [
                {
                    "name": "查看所有节点数量",
                    "gremlin": "g.V().count()",
                    "description": "统计图中所有节点的总数"
                },
                {
                    "name": "查看所有边的数量",
                    "gremlin": "g.E().count()",
                    "description": "统计图中所有关系的总数"
                },
                {
                    "name": "查看所有节点类型",
                    "gremlin": "g.V().label().dedup()",
                    "description": "获取图中所有节点的类型"
                },
                {
                    "name": "查看所有关系类型",
                    "gremlin": "g.E().label().dedup()",
                    "description": "获取图中所有关系的类型"
                }
            ],
            "专利查询": [
                {
                    "name": "查找所有专利",
                    "gremlin": "g.V().hasLabel('Patent')",
                    "description": "获取所有专利节点"
                },
                {
                    "name": "查找特定专利",
                    "gremlin": "g.V().has('id', 'CN202410001234')",
                    "description": "根据ID查找特定专利"
                },
                {
                    "name": "查找AI相关专利",
                    "gremlin": "g.V().hasLabel('Patent').has('category', '人工智能')",
                    "description": "查找人工智能领域的专利"
                },
                {
                    "name": "按发明人查找专利",
                    "gremlin": "g.V().hasLabel('Patent').has('inventor', '张三')",
                    "description": "查找特定发明人的专利"
                }
            ],
            "关系查询": [
                {
                    "name": "查找专利的所有关系",
                    "gremlin": "g.V('CN202410001234').bothE()",
                    "description": "查看特定专利的所有关系"
                },
                {
                    "name": "查找专利所属公司",
                    "gremlin": "g.V('CN202410001234').out('ASSIGNED_TO')",
                    "description": "查找专利的申请人公司"
                },
                {
                    "name": "查找公司的专利",
                    "gremlin": "g.V('athena_tech').in('ASSIGNED_TO')",
                    "description": "查找特定公司的所有专利"
                },
                {
                    "name": "查找发明人的专利",
                    "gremlin": "g.V('zhang_san').out('INVENTED_BY')",
                    "description": "查找特定发明人的专利"
                }
            ],
            "复杂查询": [
                {
                    "name": "专利-发明人-公司路径",
                    "gremlin": "g.V().hasLabel('Patent').as('p').out('INVENTED_BY').as('i').in('ASSIGNED_TO').as('c').select('p', 'i', 'c')",
                    "description": "查找专利、发明人和申请公司的完整关系"
                },
                {
                    "name": "AI专利的发明人信息",
                    "gremlin": "g.V().hasLabel('Patent').has('category', '人工智能').as('patent').out('INVENTED_BY').as('inventor').select('patent', 'inventor')",
                    "description": "查找AI专利及其发明人信息"
                },
                {
                    "name": "多步关系查找",
                    "gremlin": "g.V().hasLabel('Patent').where(__.out('USES_TECHNOLOGY').has('category', '前沿技术')).as('ai_patent').out('ASSIGNED_TO').where(__.has('location', '北京')).select('ai_patent')",
                    "description": "查找使用前沿技术且申请人在北京的专利"
                },
                {
                    "name": "聚合统计",
                    "gremlin": "g.V().hasLabel('Company').as('company').in('ASSIGNED_TO').count().as('patent_count').select('company', 'patent_count')",
                    "description": "统计每个公司拥有的专利数量"
                }
            ],
            "性能查询": [
                {
                    "name": "分页查询专利",
                    "gremlin": "g.V().hasLabel('Patent').range(0, 10)",
                    "description": "分页查询前10个专利"
                },
                {
                    "name": "按日期排序",
                    "gremlin": "g.V().hasLabel('Patent').order().by('application_date')",
                    "description": "按申请日期排序专利"
                },
                {
                    "name": "限制返回字段",
                    "gremlin": "g.V().hasLabel('Patent').values('title', 'inventor', 'assignee')",
                    "description": "只返回专利的标题、发明人和申请人"
                }
            ]
        }

        # 生成查询文档
        query_doc = "# JanusGraph Gremlin查询示例\n\n"
        query_doc += f"生成时间: {datetime.now().isoformat()}\n\n"

        for category, category_queries in queries.items():
            query_doc += f"## {category}\n\n"
            for query in category_queries:
                query_doc += f"### {query['name']}\n"
                query_doc += f"**描述**: {query['description']}\n"
                query_doc += f"**Gremlin查询**: ```gremlin\n{query['gremlin']}\n``\n\n"

        # 保存查询文档
        doc_path = Path("/Users/xujian/Athena工作平台/data/gremlin_query_examples.md")
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(query_doc)

        logger.info(f"✅ Gremlin查询示例已保存: {doc_path}")
        return queries

    def create_test_workflow(self):
        """创建测试工作流程"""
        logger.info("📋 创建测试工作流程...")

        workflow = {
            "workflow_name": "JanusGraph知识图谱测试",
            "steps": [
                {
                    "step": 1,
                    "name": "准备测试数据",
                    "description": "使用创建脚本生成测试数据",
                    "command": ":load data/test_data_creation.gremlin"
                },
                {
                    "step": 2,
                    "name": "验证数据导入",
                    "description": "检查节点和边的数量",
                    "queries": [
                        "g.V().count()",
                        "g.E().count()",
                        "g.V().label().dedup()"
                    ]
                },
                {
                    "step": 3,
                    "name": "基础查询测试",
                    "description": "执行基础查询验证功能",
                    "queries": [
                        "g.V().hasLabel('Patent')",
                        "g.V().hasLabel('Company')",
                        "g.V().hasLabel('Inventor')"
                    ]
                },
                {
                    "step": 4,
                    "name": "关系查询测试",
                    "description": "测试复杂关系查询",
                    "queries": [
                        "g.V('CN202410001234').bothE()",
                        "g.V('athena_tech').in('ASSIGNED_TO')",
                        "g.V().hasLabel('Patent').as('p').out('INVENTED_BY').as('i').select('p', 'i')"
                    ]
                },
                {
                    "step": 5,
                    "name": "性能测试",
                    "description": "测试查询性能",
                    "queries": [
                        "g.V().hasLabel('Patent').profile()",
                        "g.V().hasLabel('Patent').out('INVENTED_BY').profile()"
                    ]
                }
            ]
        }

        # 保存工作流程
        workflow_path = Path("/Users/xujian/Athena工作平台/data/janusgraph_test_workflow.json")
        with open(workflow_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 测试工作流程已保存: {workflow_path}")
        return workflow

    def generate_quick_start_guide(self):
        """生成快速开始指南"""
        logger.info("📖 生成快速开始指南...")

        guide = """
# JanusGraph Gremlin快速开始指南

## 1. 连接Gremlin控制台

### 启动JanusGraph服务
确保JanusGraph服务在8182端口运行。

### 连接控制台
```bash
# 进入JanusGraph目录
cd /Users/xujian/Athena工作平台/storage-system/janusgraph

# 启动Gremlin控制台
./bin/gremlin.sh
```

### 连接到远程服务器
```gremlin
# 在Gremlin控制台中执行
:remote connect tinkerpop.server conf/remote.yaml
:remote console
```

## 2. 创建测试数据

### 导入测试数据
```gremlin
:load /Users/xujian/Athena工作平台/data/test_data_creation.gremlin
```

### 验证数据
```gremlin
g.V().count()
g.E().count()
g.V().label().dedup()
```

## 3. 基础查询

### 查看所有节点
```gremlin
g.V()
```

### 查看专利节点
```gremlin
g.V().hasLabel('Patent')
```

### 查看所有关系
```gremlin
g.E()
```

## 4. 高级查询

### 查找AI专利
```gremlin
g.V().hasLabel('Patent').has('category', '人工智能')
```

### 查找专利关系
```gremlin
g.V('CN202410001234').bothE()
```

### 统计公司专利数
```gremlin
g.V().hasLabel('Company').as('c').in('ASSIGNED_TO').count().as('count').select('c', 'count')
```

## 5. 性能优化

### 添加索引
```gremlin
// 创建混合索引
mgmt = graph.openManagement()
name = mgmt.makePropertyKey('name').dataType(String.class).make()
mgmt.buildIndex('byNameComposite', Vertex.class).addKey(name).buildCompositeIndex()
mgmt.commit()
```

### 分析查询性能
```gremlin
g.V().hasLabel('Patent').profile()
```

## 6. 保存和恢复

### 导出图数据
```gremlin
graph.io(IoCore.gryo()).writeGraph('/tmp/graph_backup.kryo')
```

### 导入图数据
```gremlin
graph.io(IoCore.gryo()).readGraph('/tmp/graph_backup.kryo')
```

## 7. 常见问题

### 连接失败
- 确保JanusGraph服务运行在8182端口
- 检查防火墙设置
- 验证配置文件路径

### 查询超时
- 增加查询超时时间
- 添加适当的索引
- 限制查询结果数量

### 内存不足
- 调整JVM堆大小
- 使用分页查询
- 优化查询语句
"""

        guide_path = Path("/Users/xujian/Athena工作平台/data/janusgraph_quick_start.md")
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide)

        logger.info(f"✅ 快速开始指南已保存: {guide_path}")

    def run(self):
        """运行完整的测试准备流程"""
        logger.info("🚀 开始准备JanusGraph Gremlin测试...")
        logger.info("=" * 60)

        # 1. 创建示例数据
        sample_data = self.create_sample_data()

        # 2. 生成查询示例
        queries = self.generate_query_examples()

        # 3. 创建测试工作流程
        workflow = self.create_test_workflow()

        # 4. 生成快速开始指南
        self.generate_quick_start_guide()

        # 5. 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("✅ JanusGraph Gremlin测试准备完成！")
        logger.info("\n📋 生成的文件:")
        logger.info("  1. 测试数据: data/test_data_creation.gremlin")
        logger.info("  2. 查询示例: data/gremlin_query_examples.md")
        logger.info("  3. 测试流程: data/janusgraph_test_workflow.json")
        logger.info("  4. 快速指南: data/janusgraph_quick_start.md")

        logger.info(f"\n📊 测试数据统计:")
        logger.info(f"  专利节点: {len(sample_data['patents'])}")
        logger.info(f"  公司节点: {len(sample_data['companies'])}")
        logger.info(f"  发明人节点: {len(sample_data['inventors'])}")
        logger.info(f"  技术节点: {len(sample_data['technologies'])}")

        query_count = sum(len(queries) for queries in queries.values())
        logger.info(f"\n🔍 查询示例总数: {query_count}")

        return True

def main():
    """主函数"""
    tester = GremlinQueryTester()
    success = tester.run()

    if success:
        print("\n🎉 JanusGraph Gremlin测试准备成功！")
        print("\n💡 使用说明:")
        print("  1. 确保JanusGraph服务运行")
        print("  2. 参考快速开始指南连接Gremlin")
        print("  3. 导入测试数据进行查询测试")
        print("  4. 参考查询示例进行高级查询")
    else:
        print("\n❌ JanusGraph Gremlin测试准备失败")

if __name__ == "__main__":
    main()