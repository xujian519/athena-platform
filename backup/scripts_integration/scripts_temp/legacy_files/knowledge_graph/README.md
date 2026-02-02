# Knowledge Graph 脚本

知识图谱相关脚本（基于SQLite + NetworkX方案）

## 核心脚本

- **check_knowledge_graphs.py** - 检查知识图谱状态
- **hybrid_search.py** - 混合搜索实现
- **hybrid_search_simple.py** - 简化的混合搜索
- **quick_start_demo.py** - 快速开始演示
- **simple_migration.py** - 数据迁移工具

## 使用说明

确保脚本有执行权限：

```bash
chmod +x *.sh
```

## 当前知识图谱方案

### 1. SQLite知识图谱
- 位置：`/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db`
- 规模：125万+实体，329万+关系
- 特点：高性能，易于维护

### 2. NetworkX知识图谱
- 专利法律图谱：45个实体，202个关系
- 技术图谱：动态构建
- 特点：内存计算，实时查询

### 3. 向量数据库集成
- Qdrant：支持向量相似度搜索
- 与知识图谱混合查询
- 支持多领域应用

## 快速开始

```python
# 检查知识图谱状态
python scripts/knowledge_graph/check_knowledge_graphs.py

# 运行混合搜索演示
python scripts/knowledge_graph/quick_start_demo.py

# 执行混合搜索
python scripts/knowledge_graph/hybrid_search_simple.py
```

## 注意事项

- 不再使用JanusGraph技术栈
- 使用SQLite作为主要图数据存储
- NetworkX用于内存图计算
- 所有已知的JanusGraph相关文件已移除