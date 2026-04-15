# Patent Retrieval Skill

从Athena平台本地7500万专利数据库中快速检索专利信息。

## 🚀 快速开始

### 使用命令行工具

```bash
# 关键词检索
python skills/patent-retrieval/scripts/patent_search_cli.py keyword 人工智能

# IPC分类检索
python skills/patent-retrieval/scripts/patent_search_cli.py ipc G06F

# 申请人检索
python skills/patent-retrieval/scripts/patent_search_cli.py applicant 腾讯

# 全文检索
python skills/patent-retrieval/scripts/patent_search_cli.py fulltext "医疗 & 器械"

# 统计信息
python skills/patent-retrieval/scripts/patent_search_cli.py stats
```

### 使用SQL查询

```bash
# 连接数据库
psql -h localhost -p 5432 -U postgres -d patent_db

# 关键词检索
SELECT patent_name, applicant FROM patents
WHERE patent_name ILIKE '%人工智能%' LIMIT 10;
```

### 运行示例脚本

```bash
# 运行交互式示例
chmod +x skills/patent-retrieval/examples/basic_search.sh
./skills/patent-retrieval/examples/basic_search.sh
```

## 📁 技能结构

```
skills/patent-retrieval/
├── SKILL.md                    # 技能定义文件
├── README.md                   # 本文件
├── scripts/
│   └── patent_search_cli.py    # 命令行检索工具
├── references/
│   └── database-schema.md      # 数据库结构参考
└── examples/
    └── basic_search.sh         # 基础检索示例
```

## 🔍 支持的检索类型

| 检索类型 | 命令 | 性能 |
|---------|------|------|
| 关键词搜索 | `keyword` | < 10ms |
| IPC分类检索 | `ipc` | < 10ms |
| 申请人检索 | `applicant` | < 200ms |
| 全文检索 | `fulltext` | < 5秒 (罕见词) |

## 📊 数据库信息

- **数据库名**: patent_db
- **记录数**: 75,217,242 条
- **表大小**: 228 GB
- **全文索引**: 28,029,272 条 (37.3%)

## 📚 相关文档

- [SKILL.md](./SKILL.md) - 技能完整定义
- [references/database-schema.md](./references/database-schema.md) - 数据库结构
- [docs/reports/patent_retrieval_final_report.md](../../../docs/reports/patent_retrieval_final_report.md) - 验证报告

## 🔧 Python API

```python
from skills.patent_retrieval.scripts.patent_search_cli import PatentSearchCLI

# 创建检索工具
cli = PatentSearchCLI()

# 关键词检索
results = cli.search_by_keyword("人工智能", limit=10)

# IPC分类检索
results = cli.search_by_ipc("G06F", limit=10)

# 申请人检索
results = cli.search_by_applicant("腾讯", limit=10)

# 全文检索
results = cli.fulltext_search("医疗", limit=10)

# 获取统计信息
stats = cli.get_statistics()

# 关闭连接
cli.close()
```

## ⚠️ 注意事项

1. 常见词(如"人工智能"、"医疗")的全文检索可能需要2-3分钟
2. 建议使用LIMIT子句限制返回结果数量
3. 全文检索仅覆盖约37%的记录
