# Athena工作平台 - 数据目录

## 📊 数据概览

**总大小**: 13GB
**文件数量**: 1,756个文件
**更新日期**: 2025-12-04

## 🗂️ 目录结构

### 📚 核心数据库
- [`databases/`](databases/) - 结构化数据库文件
  - `memory_system/` - 内存系统数据库（从docs迁移）
  - `legal_laws_database.db` - 法律法规数据库
  - `patent_legal_database.db` - 专利法律数据库

### 🧠 知识图谱
- `01_知识图谱数据库/` - 主要知识图谱数据库
- `law_knowledge_graph/` - 法律知识图谱（4.3GB）
- `patent_*_knowledge_graph/` - 各种专利知识图谱
- `tugraph_knowledge_graphs/` - TuGraph知识图谱
- `multi_agent_knowledge_graph/` - 多智能体知识图谱

### 🔢 向量数据
- `law_vectors/` - 法律向量数据（487MB）
- `technical_vectors/` - 技术向量数据（批量文件，1GB+）
- `vector/` - 通用向量数据
- `vector_indexes/` - 向量索引

### 📋 处理数据
- `processed_laws*/` - 各种处理阶段的法律数据
- `03_统计数据/` - 统计数据集合
- `patent_judgment_*` - 专利判决相关数据

### 📝 其他数据
- `agent_evaluations/` - 智能体评估数据
- `constitution/` - 宪法相关数据
- `documentation/logs/` - 日志文件
- `models/` - 模型数据
- `templates/` - 模板文件
- `temp/` - 临时文件

## 💾 大文件说明

### 超大文件（>1GB）
1. **law_relations.json** (4.3GB) - 法律关系数据
2. **original_vectors_batch_*.json** (1-1.3GB) - 批量向量数据

### 大型数据库（100MB-1GB）
1. **law_vectors.json** (487MB) - 法律向量数据
2. **patent_invalid_kg.db** (272MB) - 专利无效知识图谱
3. **technical_vectors.db** (354MB) - 技术向量数据库

## 🔧 数据管理建议

### 1. 数据分类
- **热数据**: 经常访问的数据，保留在本地
- **温数据**: 偶尔访问，可考虑压缩存储
- **冷数据**: 很少访问，建议归档到云存储

### 2. 存储优化
```
建议结构：
data/
├── hot/          # 热数据（<2GB，经常访问）
├── warm/         # 温数据（压缩存储）
├── cold/         # 冷数据（归档存储）
└── archive/      # 历史数据备份
```

### 3. 清理建议
- 删除临时文件（temp/目录）
- 合并重复的向量数据
- 压缩不常用的JSON文件
- 清理过期的日志文件

## 🚨 重要提醒

1. **备份策略**: 重要数据需要定期备份
2. **访问权限**: 确保数据目录的访问权限正确
3. **版本控制**: 数据文件不应纳入版本控制
4. **监控增长**: 定期检查数据目录大小增长

## 📈 数据增长趋势

- 当前大小：13GB
- 月增长率：约2-3GB
- 预计明年：约40GB

## 🔍 数据访问指南

### 按用途查找
| 用途 | 目录 | 说明 |
|------|------|------|
| 法律分析 | law_knowledge_graph/ | 法律法规和案例 |
| 专利分析 | patent_*_knowledge_graph/ | 专利数据和分析 |
| 向量搜索 | technical_vectors/ | 向量化数据 |
| 系统日志 | documentation/logs/ | 运行日志 |
| 模型数据 | models/ | 训练好的模型 |

### 按大小查找
| 大小 | 类型 | 示例 |
|------|------|------|
| >1GB | 知识图谱 | law_relations.json |
| 100MB-1GB | 数据库 | patent_invalid_kg.db |
| 10-100MB | 向量数据 | law_vectors.json |
| <10MB | 配置文件 | 各种JSON配置 |

---

**维护者**: Athena开发团队
**最后更新**: 2025-12-04
**下次检查**: 2025-12-11