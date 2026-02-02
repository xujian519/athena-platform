# Athena工作平台数据目录结构说明

**更新日期**: 2025-12-07
**整理人**: 小娜/Athena

## 📁 数据目录总览

```
/Users/xujian/Athena工作平台/data/
├── knowledge_graph_neo4j/    # Neo4j知识图谱数据
├── vectors_qdrant/           # Qdrant向量库数据
├── support_data/             # 支撑数据
├── backup_YYYYMMDD_HHMMSS/   # 备份目录
├── constitution/             # 宪法数据
├── deprecated_*/            # 已废弃数据
├── legacy-system-prompts/    # 遗留系统提示
└── updates/                  # 更新数据
```

---

## 🔗 knowledge_graph_neo4j/ - Neo4j知识图谱数据

存放所有用于Neo4j图数据库的知识图谱数据。

### 子目录结构

#### 📂 raw_data/ - 原始知识图谱数据
包含所有原始的知识图谱数据文件：

- `patent_kg_superfast/` - 超级快速处理的专利知识图谱（115个批次文件）
- `patent_knowledge_graph/` - 专利知识图谱
- `neo4j_data/` - Neo4j原生数据
- `neo4j_import/` - Neo4j导入数据
- `knowledge_graph/` - 基础知识图谱
- `knowledge_graphs/` - 多个知识图谱集合
- `merged_knowledge_graphs/` - 合并的知识图谱
- `fixed_legal_knowledge_graph/` - 修复后的法律知识图谱
- `production_legal_knowledge_graph/` - 生产环境法律知识图谱
- `professional_knowledge_graphs/` - 专业知识图谱
- `patent_judgment_kg/` - 专利判决知识图谱
- `patent_invalid_knowledge_graph/` - 专利无效知识图谱
- `patent_legal_knowledge_graph/` - 专利法律知识图谱
- `patent_reconsideration_knowledge_graph/` - 专利复审知识图谱
- `technical_terms_knowledge_graph/` - 技术术语知识图谱
- `patent_kg/` - 专利知识图谱
- `professional_patent/` - 专业专利数据
- `patent_agency_results/` - 专利代理结果
- `processed_laws*/` - 处理后的法律数据
- `neo4j_knowledge_graphs/` - Neo4j知识图谱

#### 📂 processed_data/ - 处理后的数据
- `unified_legal_kg_import.cypher` - 统一法律知识图谱导入脚本
- `unified_legal_kg_statistics.json` - 统一法律知识图谱统计
- `unified_legal_knowledge_graph.json` - 统一法律知识图谱
- `vertices_export.csv` - 顶点导出文件

#### 📂 其他子目录
- `exports/` - 导出数据
- `import_scripts/` - 导入脚本
- `queries/` - 查询脚本
- `schemas/` - 数据模式定义

---

## 🔍 vectors_qdrant/ - Qdrant向量库数据

存放所有用于Qdrant向量数据库的向量数据和嵌入。

### 子目录结构

#### 📂 embeddings/ - 嵌入向量文件
- `ai_terminology_vectors_20251205_104422.json` - AI术语向量
- `ai_terminology_enhanced_20251205_104422.json` - 增强AI术语数据
- `ai_terminology_all_parsed.json` - 所有AI术语解析
- `ai_terminology_A_parsed.json` - AI术语A类解析
- `technical_terms_comprehensive.json` - 综合技术术语
- `technical_terms_raw.json` - 原始技术术语

#### 📂 collections/ - 向量集合
- `vectors/` - 向量数据集合
- `vector_indexes/` - 向量索引
- `vectorization-stats/` - 向量化统计
- `qdrant/` - Qdrant原数据
- `专利无效向量库/` - 专利无效向量库

#### 📂 其他子目录
- `indexes/` - 索引文件
- `metadata/` - 元数据
- `models/` - 模型文件

---

## 🛠️ support_data/ - 支撑数据

存放数据库文件、配置、日志等支撑数据。

### 子目录结构

#### 📂 databases/ - 数据库文件
- `legal_laws_database.db` - 法律法律法规数据库
- `patent_cache.db` - 专利缓存数据库
- `patent_legal_database.db` - 专利法律数据库
- `memory_active.db` - 活跃记忆数据库

#### 📂 configs/ - 配置文件
- `knowledge_base.json` - 知识库配置
- `templates/` - 模板文件

#### 📂 documentation/logs/ - 日志文件
- 各种操作日志和运行日志

#### 📂 reports/ - 报告文件
- `ai_terminology_readme.md` - AI术语说明
- `ai_terminology_all.md` - AI术语全集
- `optimization_reports/` - 优化报告

#### 📂 workspace/ - 工作空间
- `processed/` - 已处理数据
- `raw/` - 原始数据

#### 📂 其他子目录
- `cache/` - 缓存数据
- `external/` - 外部数据
- `templates/` - 模板文件

---

## 📊 数据统计

### Neo4j知识图谱数据
- 专利知识图谱批次：115个JSON文件
- 包含57,214个专利文档
- 生成149,658个三元组关系

### Qdrant向量库数据
- AI术语向量：多个版本
- 技术术语数据：综合和原始版本
- 专利向量库：专利无效相关向量

### 支撑数据
- SQLite数据库：4个
- 配置文件：多个
- 日志和报告：详细记录

---

## 🔗 数据关联

### 专利数据处理流程
1. **原始文档** → `/Users/xujian/学习资料/专利/`
2. **超级快速处理** → `knowledge_graph_neo4j/raw_data/patent_kg_superfast/`
3. **知识图谱导入** → Neo4j数据库
4. **向量化处理** → `vectors_qdrant/embeddings/`

### 数据同步关系
- Neo4j存储结构化知识图谱
- Qdrant存储向量化的相似性数据
- 两者通过专利ID等标识符关联

---

## 💡 使用建议

### 1. 数据访问
- 知识图谱查询：使用Neo4j Cypher语言
- 向量相似性搜索：使用Qdrant API
- 原始数据访问：查看相应的raw_data目录

### 2. 数据更新
- 新增专利：更新patent_kg_superfast目录
- 更新向量：重新运行向量化脚本
- 备份重要数据：定期备份整个data目录

### 3. 性能优化
- Neo4j：确保有足够的内存和索引
- Qdrant：优化向量集合的配置
- 定期清理：删除deprecated和旧版本数据

---

## 📝 注意事项

1. **备份重要性**：修改前请备份重要数据
2. **版本控制**：注意数据文件的版本和日期
3. **权限管理**：确保适当的文件访问权限
4. **存储空间**：监控磁盘使用情况

---

**最后更新**: 2025-12-07
**维护者**: 小娜/Athena