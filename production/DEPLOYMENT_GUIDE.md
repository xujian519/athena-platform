# 法律与专利知识系统 - 生产环境部署指南

## 📋 系统概述

本系统包含四个核心知识库：
- **法律向量库**: 217,204 条法律文档向量
- **法律知识图谱**: 144,486 节点 + 113,599 边
- **专利向量库**: 111,911 条专利文档向量
- **专利知识图谱**: 18,419 节点 + 75 边

**总数据量**: 492,020 条记录

---

## 🚀 服务部署状态

### Docker 容器

| 服务 | 容器名 | 状态 | 端口 |
|------|--------|------|------|
| Qdrant | athena-qdrant | ✅ 运行中 | 6333-6334 |
| NebulaGraph Meta | athena_nebula_metad_min | ✅ 运行中 | 9559 |
| NebulaGraph Storage | athena_nebula_storage_min | ✅ 运行中 | 9779 |
| NebulaGraph Graph | athena_nebula_graph_min | ✅ 运行中 | 9669 |
| Grafana | phoenix-grafana | ✅ 健康 | 3000 |
| Prometheus | phoenix-prometheus | ✅ 健康 | 19090 |

### 服务地址

- **Qdrant**: http://localhost:6333
- **NebulaGraph**: localhost:9669
- **Grafana 监控**: http://localhost:3000
- **Prometheus**: http://localhost:19090

---

## 📊 性能测试结果

### Qdrant 向量搜索 (100次)
- 平均响应: 1.16ms
- P95: 1.6ms
- 最大: 3.77ms

### NebulaGraph 图查询 (100次)
- 平均响应: 7.34ms
- P95: 8.99ms
- 最大: 10.29ms

### 性能评估
✅ **性能优秀** - P95延迟均低于10ms，满足生产环境要求

---

## 🔧 配置文件

### 环境变量
```
/Users/xujian/Athena工作平台/production/.env.knowledge
```

包含以下配置：
- Qdrant 连接配置
- NebulaGraph 连接配置
- 嵌入模型路径
- 监控和日志路径

---

## 🛠️ 运维脚本

### 监控脚本
```bash
/Users/xujian/Athena工作平台/production/dev/scripts/monitor_knowledge.sh
```
- 每5分钟检查服务健康状态
- 记录日志到 `production/logs/monitor.log`
- 异常时发送告警到 `production/logs/alerts.log`

启动监控:
```bash
/Users/xujian/Athena工作平台/production/dev/scripts/monitor_knowledge.sh &
```

### 备份脚本
```bash
/Users/xujian/Athena工作平台/production/dev/scripts/backup_knowledge.sh
```
- 备份 Qdrant 集合统计信息
- 备份 NebulaGraph 图空间统计信息
- 自动清理30天前的备份日志

执行备份:
```bash
/Users/xujian/Athena工作平台/production/dev/scripts/backup_knowledge.sh
```

### 性能测试
```bash
python3 /Users/xujian/Athena工作平台/production/dev/scripts/knowledge_perf_test.py
```

---

## 📁 数据存储

### 向量库数据 (Qdrant)
- 法律增强版: `legal_laws_enhanced` (73,451条)
- 法律基础版: `legal_laws_bge` (111,407条)
- 专利规则完整版: `patent_rules_complete` (1,258条)
- 专利决定书: `patent_decisions` (104,347条)

### 知识图谱数据 (NebulaGraph)
- 法律空间: `legal_kg`
  - Law (法律): 3,088 节点
  - Chapter (章): 12,580 节点
  - Clause (条款): 128,221 节点

- 专利空间: `patent_kg_extended`
  - PatentRule (规则): 7,050 节点
  - PatentDecision (决定): 10,068 节点
  - PatentLaw (法律): 906 节点
  - PatentGuideline (指南): 395 节点

---

## 🔍 使用示例

### 法律向量搜索
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(url='http://localhost:6333')
model = SentenceTransformer('/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5')

query = "劳动合同的解除条件"
vector = model.encode([query])[0].tolist()

results = client.scroll(
    collection_name='legal_laws_enhanced',
    limit=5,
    with_payload=True
)
```

### 法律图谱查询
```python
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

config = Config()
pool = ConnectionPool()
pool.init([('127.0.0.1', 9669)], config)
session = pool.get_session('root', 'nebula')

session.execute('USE legal_kg;')
result = session.execute('''
    MATCH (l:Law)-[r1:HAS_CHAPTER]->(c:Chapter)
    RETURN l.title AS law, c.title AS chapter
    LIMIT 10
''')
```

### 专利向量搜索
```python
results = client.scroll(
    collection_name='patent_rules_complete',
    limit=5,
    with_payload=True
)
```

### 专利图谱查询
```python
session.execute('USE patent_kg_extended;')
result = session.execute('''
    MATCH (d:PatentDecision)-[r:CITES]->(r:PatentRule)
    RETURN d.decision_number, r.title
    LIMIT 10
''')
```

---

## 📈 监控和告警

### Grafana 仪表盘
访问 http://localhost:3000 查看系统监控指标

### 关键指标
- Qdrant 响应时间
- NebulaGraph 查询时间
- 磁盘使用率
- 容器健康状态

### 告警日志
```bash
tail -f /Users/xujian/Athena工作平台/production/logs/alerts.log
```

---

## 🔄 维护操作

### 启动/重启服务

```bash
# 重启 Qdrant
docker restart athena-qdrant

# 重启 NebulaGraph
docker restart athena_nebula_graph_min
docker restart athena_nebula_storage_min
docker restart athena_nebula_metad_min
```

### 查看日志

```bash
# Qdrant 日志
docker logs -f athena-qdrant

# NebulaGraph 日志
docker logs -f athena_nebula_graph_min
```

---

## 📞 技术支持

- 部署时间: 2025-12-23
- 数据总量: 492,020 条记录
- 服务状态: ✅ 全部正常

---

## ✅ 生产环境就绪确认

- [x] 服务运行正常
- [x] 数据完整性验证通过
- [x] 性能测试通过 (P95 < 10ms)
- [x] 监控脚本已部署
- [x] 备份脚本已部署
- [x] 环境配置已创建
- [x] Docker 网络已配置

**结论: 系统已具备生产环境可用性**
