# 商标规则数据库系统

## 📚 概述

商标规则数据库系统是基于Athena工作平台构建的商标法律法规智能检索和分析系统。该系统整合了PostgreSQL、Qdrant和NebulaGraph三大数据库，提供结构化存储、语义检索和知识图谱查询能力。

## 🏗️ 系统架构

```
商标规则数据库系统
├── PostgreSQL (端口5441)     # 结构化数据存储
│   ├── trademark_norms       # 法规表
│   ├── trademark_articles    # 条款表
│   └── trademark_vectors     # 向量文档表
│
├── Qdrant (端口6333)         # 向量数据库
│   └── trademark_rules       # 向量集合
│
└── NebulaGraph (端口9669)    # 知识图谱
    ├── trademark_norm        # 法规节点
    ├── trademark_article     # 条款节点
    └── trademark_concept     # 概念节点
```

## 📁 文件结构

```
trademark_rules_system/
├── __init__.py              # 包初始化
├── models.py                # 数据模型定义
├── database_manager.py      # 数据库管理器
├── pdf_splitter.py          # 大PDF分割器
├── markdown_processor.py    # MD文件处理器
├── vector_store.py          # Qdrant向量存储
├── graph_builder.py         # NebulaGraph图谱构建
├── pipeline.py              # 主管道
└── README.md                # 本文档
```

## 🚀 快速开始

### 1. 环境准备

确保以下服务正在运行：

```bash
# PostgreSQL (端口5441)
psql -p 5441

# Qdrant
docker run -p 6333:6333 qdrant/qdrant

# NebulaGraph
# 参考项目配置启动
```

### 2. 安装依赖

```bash
pip install psycopg2-binary qdrant-client nebula3-python pymupdf tqdm
```

### 3. 配置数据库连接

编辑 `pipeline.py` 中的配置：

```python
config = {
    'database': {
        'pg_host': 'localhost',
        'pg_port': 5441,
        'pg_database': 'trademark_database',
        'pg_user': 'postgres',
        'pg_password': 'your_password',  # 修改为实际密码
        'qdrant_url': 'http://localhost:6333',
        'nebula_hosts': ['127.0.0.1'],
        'nebula_port': 9669,
        'nebula_user': 'root',
        'nebula_password': 'nebula',
        'nebula_space': 'trademark_graph'
    }
}
```

### 4. 准备数据

将商标相关文件放在 `./data/商标/` 目录：
- 法律法规MD文件
- 商标审查审理指南PDF（大文件）

### 5. 运行管道

```bash
# 完整管道
python -m production.scripts.trademark_rules_system.pipeline

# 或者单独运行各组件
python -m production.scripts.trademark_rules_system.pdf_splitter
python -m production.scripts.trademark_rules_system.markdown_processor
```

## 📊 处理流程

```
1. PDF分割 (大文件>10MB)
   ↓
2. MD文件解析
   ↓
3. 结构化存储 (PostgreSQL)
   ↓
4. 向量化存储 (Qdrant)
   ↓
5. 知识图谱构建 (NebulaGraph)
```

## 🔧 配置选项

### PDF分割器配置

```python
{
    'pdf_path': 'path/to/large.pdf',
    'output_dir': './temp',
    'chunk_size': 50,           # 每50页一块
    'enable_ocr': False,        # 是否启用OCR
    'progress_file': './progress.json'
}
```

### MD处理器配置

```python
{
    'data_dir': './data/商标',
    'output_dir': './processed',
    'chunk_size': 1000,         # 文本块大小
    'chunk_overlap': 200        # 重叠大小
}
```

## 📈 数据统计

处理完成后，系统会生成统计信息：

```json
{
    "start_time": "2025-01-15T...",
    "processed_files": 11,
    "total_norms": 11,
    "total_articles": 500,
    "total_vectors": 1500,
    "total_graph_nodes": 2000,
    "total_graph_edges": 2500,
    "end_time": "2025-01-15T..."
}
```

## 🔍 查询示例

### PostgreSQL查询

```sql
-- 查询所有现行有效的法规
SELECT * FROM trademark_norms WHERE status = '现行有效';

-- 查询特定条款
SELECT * FROM trademark_articles WHERE article_number = '第十条';
```

### Qdrant向量搜索

```python
results = vector_store.search_similar(
    query="商标注册的条件",
    limit=10,
    score_threshold=0.7
)
```

### NebulaGraph图查询

```cypher
MATCH (n:trademark_norm)-[:has_article]->(a:trademark_article)
WHERE n.document_type == "法律"
RETURN n, a
LIMIT 10
```

## 🛠️ 故障排查

### 问题1: PostgreSQL连接失败

```bash
# 检查PostgreSQL是否运行
psql -p 5441 -h localhost

# 检查端口占用
lsof -i :5441
```

### 问题2: Qdrant连接失败

```bash
# 检查Qdrant服务
curl http://localhost:6333/

# 重启Docker容器
docker restart <qdrant_container_id>
```

### 问题3: 大PDF处理内存不足

- 减小 `chunk_size` 参数
- 增加系统内存
- 启用分页处理模式

## 📝 注意事项

1. **密码安全**: 请勿将数据库密码硬编码，使用环境变量
2. **大文件处理**: 80M+ PDF文件需要分页处理，避免内存溢出
3. **断点续传**: PDF分割器支持断点续传，处理中断可继续
4. **数据备份**: 处理前请备份原始数据

## 🔄 更新日志

### v1.0.0 (2025-01-15)
- 初始版本发布
- 支持PDF分割处理
- 支持MD文件解析
- PostgreSQL/Qdrant/NebulaGraph三库存储
- 完整的知识图谱构建

## 📧 技术支持

如有问题，请参考：
- Athena工作平台文档: `/Users/xujian/Athena工作平台/README.md`
- 数据库配置: `/Users/xujian/Athena工作平台/config/database_config.yaml`
