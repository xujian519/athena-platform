# Neo4j到Nebula图数据库迁移指南

## 📋 文档信息

| 项目 | 内容 |
|------|------|
| **文档版本** | v1.0 |
| **创建日期** | 2025-12-25 |
| **废弃日期** | 2025-12-25 |
| **目标完成** | 2025-06-30 |
| **负责人** | Athena AI团队 |

---

## 🎯 迁移概述

### 背景

Athena工作平台决定将图数据库技术栈从**Neo4j**迁移至**NebulaGraph**，主要原因：

1. **性能优势**：NebulaGraph在分布式场景下性能更优
2. **成本效益**：开源协议更友好，无企业版限制
3. **技术自主**：国产图数据库，技术栈可控
4. **生态整合**：与现有Qdrant向量库配合更好

### 影响范围

| 层级 | 组件 | 状态 |
|------|------|------|
| 核心API | `optimized_kg_api.py` | ⚠️ 6个月内迁移 |
| 查询服务 | `knowledge_graph_query_api.py` | ⚠️ 3个月内迁移 |
| 连接管理 | `connection_manager.py` | ✅ 已废弃 |
| 专利检索 | `patent_hybrid_retrieval.py` | ✅ 已更新 |
| 知识连接器 | `patent_knowledge_connector.py` | ✅ 已更新 |

---

## 🔄 技术对比

### 驱动和连接

| 特性 | Neo4j | NebulaGraph |
|------|-------|-------------|
| **Python驱动** | `neo4j-python` | `nebula3-python` |
| **连接协议** | Bolt | TCP |
| **连接池** | 内置 | 需自行管理 |
| **异步支持** | `AsyncGraphDatabase` | 需手动封装 |

### 查询语言对比

| 操作 | Neo4j (Cypher) | NebulaGraph (nGQL) |
|------|----------------|-------------------|
| **创建节点** | `CREATE (n:Person {name: "Alice"})` | `INSERT VERTEX Person(name) VALUES "Alice"` |
| **创建关系** | `CREATE (a)-[:KNOWS]->(b)` | `INSERT EDGE KNOWS()` |
| **查询节点** | `MATCH (n:Person) RETURN n` | `GO FROM "vid" OVER KNOWS` |
| **路径查询** | `MATCH p=(a)-[*..3]->(b) RETURN p` | `GO FROM "a" OVER * 1 TO 3 YIELD path` |
| **更新属性** | `SET n.name = "Bob"` | `UPDATE VERTEX "vid" SET name="Bob"` |

### 数据模型差异

| 特性 | Neo4j | NebulaGraph |
|------|-------|-------------|
| **节点ID** | 自动生成long id | 需手动指定或使用UUID |
| **标签系统** | 多标签 | 单标签 |
| **属性类型** | 动态类型 | 需预先定义Schema |
| **索引** | 自动创建 | 需手动创建 |

---

## 📝 迁移步骤

### 阶段1：环境准备（1周）

#### 1.1 安装NebulaGraph

```bash
# Docker方式部署
cd /Users/xujian/Athena工作平台/infrastructure/infrastructure/docker/compose/
docker-compose -f nebula.yml up -d

# 验证部署
docker ps | grep nebula
```

#### 1.2 安装Python客户端

```bash
pip install nebula3-python
```

#### 1.3 创建图空间

```python
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

# 初始化连接池
pool = ConnectionPool()
pool.init([('127.0.0.1', 9669)], Config())

# 获取会话
session = pool.get_session('root', 'nebula')

# 创建图空间
session.execute("""
CREATE SPACE IF NOT EXISTS patent_knowledge (
    partition_num = 10,
    replica_factor = 1,
    vid_type = FIXED_STRING(32)
);
USE patent_knowledge;
""")

# 创建标签和边类型
session.execute("""
CREATE TAG IF NOT EXISTS patent(title, abstract, applicant, date);
CREATE TAG IF NOT EXISTS company(name, type);
CREATE EDGE IF NOT EXISTS cites(strength);
CREATE EDGE IF NOT EXISTS belongs_to(since);
""")
```

---

### 阶段2：数据迁移（2-4周）

#### 2.1 导出Neo4j数据

```python
# 从Neo4j导出数据
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    # 导出节点
    nodes = session.run("MATCH (n) RETURN n")
    for record in nodes:
        node = record["n"]
        # 保存为JSON或CSV

    # 导出关系
    rels = session.run("MATCH ()-[r]->() RETURN r")
    for record in rels:
        rel = record["r"]
        # 保存为JSON或CSV
```

#### 2.2 转换数据格式

```python
def convert_neo4j_to_nebula(neo4j_data):
    """转换Neo4j数据为Nebula格式"""
    nebula_data = {
        'vertices': [],
        'edges': []
    }

    # 转换节点
    for node in neo4j_data['nodes']:
        vid = generate_vid(node.id)  # 生成固定长度的VID
        tags = [{
            'name': node.label,
            'props': node.properties
        }]
        nebula_data['vertices'].append((vid, tags))

    # 转换边
    for edge in neo4j_data['edges']:
        nebula_data['edges'].append({
            'src': generate_vid(edge.start_id),
            'dst': generate_vid(edge.end_id),
            'type': edge.type,
            'props': edge.properties
        })

    return nebula_data
```

#### 2.3 导入到Nebula

```python
# 批量导入节点
def import_vertices(pool, vertices, batch_size=1000):
    session = pool.get_session('root', 'nebula')
    session.execute('USE patent_knowledge;')

    for i in range(0, len(vertices), batch_size):
        batch = vertices[i:i+batch_size]
        for vid, tags in batch:
            for tag in tags:
                props_str = ','.join([f"{k}:{json.dumps(v)}" for k, v in tag['props'].items()])
                nGQL = f'INSERT VERTEX {tag["name"]}({props_str}) VALUES "{vid}";'
                session.execute(nGQL)

    session.release()

# 批量导入边
def import_edges(pool, edges, batch_size=1000):
    session = pool.get_session('root', 'nebula')
    session.execute('USE patent_knowledge;')

    for i in range(0, len(edges), batch_size):
        batch = edges[i:i+batch_size]
        for edge in batch:
            props_str = ','.join([f"{k}:{json.dumps(v)}" for k, v in edge['props'].items()])
            nGQL = f'INSERT EDGE {edge["type"]}({props_str}) VALUES "{edge["src"]}"->"{edge["dst"]}";'
            session.execute(nGQL)

    session.release()
```

---

### 阶段3：代码迁移（4-8周）

#### 3.1 Neo4j → Nebula 代码映射

**旧代码（Neo4j）**:
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    result = session.run("MATCH (p:Patent {id: $id}) RETURN p", id="CN12345")
    for record in result:
        print(record["p"])
```

**新代码（Nebula）**:
```python
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

pool = ConnectionPool()
pool.init([("127.0.0.1", 9669)], Config())

session = pool.get_session("root", "nebula")
result = session.execute("""
    GO FROM "vid_cn12345" OVER * YIELD vertices(edge) as p
""")

for record in result:
    print(record)
```

#### 3.2 封装Nebula客户端

创建统一的图数据库接口：

```python
# core/infrastructure/infrastructure/database/nebula_adapter.py

from contextlib import contextmanager
from typing import List, Dict, Any

class NebulaAdapter:
    """Nebula图数据库适配器"""

    def __init__(self, config: Dict):
        self.pool = ConnectionPool()
        self.pool.init(
            [config['address']],
            Config()
        )

    @contextmanager
    def session(self, user: str, password: str):
        """获取会话"""
        sess = self.pool.get_session(user, password)
        try:
            yield sess
        finally:
            sess.release()

    def execute_query(self, nGQL: str) -> List[Dict]:
        """执行查询"""
        with self.session("root", "nebula") as session:
            result = session.execute(nGQL)
            return self._parse_result(result)

    def search_patents(self, keyword: str, limit: int = 10) -> List[Dict]:
        """搜索专利"""
        nGQL = f"""
        LOOKUP ON patent
        WHERE patent.title CONTAINS "{keyword}"
        YIELD vertex as v
        LIMIT {limit};
        """
        return self.execute_query(nGQL)
```

---

### 阶段4：验证测试（2-4周）

#### 4.1 功能验证清单

| 功能 | Neo4j | Nebula | 状态 |
|------|-------|--------|------|
| 节点创建 | ✅ | ✅ | ⬜ 待验证 |
| 关系创建 | ✅ | ✅ | ⬜ 待验证 |
| 路径查询 | ✅ | ✅ | ⬜ 待验证 |
| 聚合统计 | ✅ | ✅ | ⬜ 待验证 |
| 索引优化 | ✅ | ✅ | ⬜ 待验证 |

#### 4.2 性能对比测试

```python
import time

def benchmark_query(driver, query, iterations=100):
    """性能基准测试"""
    times = []

    for _ in range(iterations):
        start = time.time()

        # 执行查询
        result = driver.execute(query)

        elapsed = time.time() - start
        times.append(elapsed)

    return {
        'avg': sum(times) / len(times),
        'min': min(times),
        'max': max(times),
        'p95': sorted(times)[int(len(times) * 0.95)]
    }
```

---

## 📊 迁移进度追踪

### 已完成 ✅

- [x] 环境部署（Nebula Docker集群）
- [x] 连接管理器更新（移除Neo4j代码）
- [x] 配置文件更新（添加Nebula配置）
- [x] 混合检索模块更新（切换到Nebula）
- [x] 知识连接器更新（添加Nebula支持）

### 进行中 🔄

- [ ] 数据导出和转换
- [ ] 知识图谱API服务迁移
- [ ] 单元测试更新

### 待开始 ⬜

- [ ] 性能验证测试
- [ ] 文档更新
- [ ] 生产环境切换
- [ ] Neo4j服务下线

---

## 🚨 风险和缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 数据丢失 | 高 | 低 | 迁移前全量备份，分阶段验证 |
| 性能下降 | 中 | 中 | 提前压测，优化nGQL查询 |
| 功能不兼容 | 高 | 中 | 充分测试，准备降级方案 |
| 延期交付 | 中 | 中 | 分阶段迁移，保留Neo4j作为备份 |

---

## 📚 参考资源

### 官方文档

- [NebulaGraph官方文档](https://docs.nebula-graph.io/)
- [nGQL语法手册](https://docs.nebula-graph.io/3.5.0/ngql/README.md)
- [Python客户端文档](https://github.com/vesoft-inc/nebula-python)

### 内部文档

- [Nebula配置文件](/Users/xujian/Athena工作平台/config/nebula_graph_config.py)
- [Nebula管理器](/Users/xujian/Athena工作平台/modules/patent/modules/patent/patent_knowledge_system/src/nebula_manager.py)
- [Nebula服务](/Users/xujian/Athena工作平台/domains/patent-ai/services/nebula_graph_service.py)

---

## 📞 联系方式

如有问题，请联系：

- **技术负责人**: Athena AI团队
- **文档维护**: DevOps团队
- **紧急联系**: 查看项目README.md

---

*最后更新: 2025-12-25*
