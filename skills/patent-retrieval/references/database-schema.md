# Patent Database Schema Reference

## 📋 patents表完整结构

### 表基本信息

| 属性 | 值 |
|------|-----|
| 表名 | patents |
| 数据库 | patent_db |
| 记录数 | 75,217,242 条 |
| 表大小 | 228 GB |
| 主键 | id (UUID) |

---

## 📊 字段定义

### 核心标识字段

| 字段名 | 类型 | 是否空 | 说明 |
|--------|------|--------|------|
| id | uuid | NOT NULL | 主键，自动生成 |
| application_number | text | NOT NULL | 申请号 |
| publication_number | text | | 公开号 |
| authorization_number | text | | 授权号 |

### 基本信息

| 字段名 | 类型 | 是否空 | 说明 |
|--------|------|--------|------|
| patent_name | text | NOT NULL | 专利名称 |
| patent_type | text | | 专利类型 (发明/实用新型/外观设计) |
| abstract | text | | 摘要 |
| claims_content | text | | 权利要求内容 |
| claims | text | | 权利要求 |

### 日期信息

| 字段名 | 类型 | 是否空 | 说明 |
|--------|------|--------|------|
| application_date | date | | 申请日期 |
| publication_date | date | | 公开日期 |
| authorization_date | date | | 授权日期 |
| source_year | integer | NOT NULL | 数据来源年份 |

### 申请人信息

| 字段名 | 类型 | 是否空 | 说明 |
|--------|------|--------|------|
| applicant | text | NOT NULL | 申请人 |
| applicant_type | text | | 申请人类型 |
| applicant_address | text | | 申请人地址 |
| applicant_region | text | | 申请人地区 |
| applicant_city | text | | 申请人城市 |
| applicant_district | text | | 申请人区县 |
| current_assignee | text | | 当前专利权人 |
| current_assignee_address | text | | 当前专利权人地址 |
| assignee_type | text | | 专利权人类型 |
| credit_code | text | | 统一社会信用代码 |

### 发明人信息

| 字段名 | 类型 | 是否空 | 说明 |
|--------|------|--------|------|
| inventor | text | | 发明人 |

### IPC分类

| 字段名 | 类型 | 是否空 | 说明 |
|--------|------|--------|------|
| ipc_code | text | | IPC分类号 |
| ipc_main_class | text | | IPC主分类 |
| ipc_classification | text | | IPC完整分类 |

### 引用统计

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| citation_count | integer | 0 | 引用次数 |
| cited_count | integer | 0 | 被引次数 |
| self_citation_count | integer | 0 | 自引次数 |
| other_citation_count | integer | 0 | 他引次数 |
| cited_by_self_count | integer | 0 | 自被引次数 |
| cited_by_others_count | integer | 0 | 他被引次数 |
| family_citation_count | integer | 0 | 族引次数 |
| family_cited_count | integer | 0 | 族被引次数 |

### 索引字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| search_vector | tsvector | 全文检索向量 (GIN索引) |

### 向量字段

| 字段名 | 类型 | 维度 | 说明 |
|--------|------|------|------|
| embedding_title | vector(768) | 768 | 标题向量 |
| embedding_abstract | vector(768) | 768 | 摘要向量 |
| embedding_claims | vector(768) | 768 | 权利要求向量 |
| embedding_combined | vector(768) | 768 | 组合向量 |

### 元数据字段

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| source_file | text | | 数据来源文件 |
| file_hash | text | | 文件哈希 |
| pdf_path | text | | PDF文件路径 |
| pdf_source | varchar(50) | | PDF来源 |
| created_at | timestamp | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | timestamp | CURRENT_TIMESTAMP | 更新时间 |
| vectorized_at | timestamp | | 向量化时间 |

---

## 📇 索引列表

### GIN索引 (全文检索)

| 索引名 | 字段 | 大小 |
|--------|------|------|
| idx_patents_abstract_fulltext | to_tsvector('chinese', abstract) | 36 GB |
| idx_patents_patent_name_fulltext | to_tsvector('chinese', patent_name) | 3.2 GB |
| idx_patents_search_vector_gin | search_vector | 5.4 GB |
| idx_patents_applicant_gin | applicant gin_trgm_ops | 99 MB |

### B-tree索引 (精确匹配)

| 索引名 | 字段 | 大小 |
|--------|------|------|
| patents_pkey | id | 3.4 GB |
| idx_patents_application_number | application_number | 2.1 GB |
| idx_patents_publication_number | publication_number | 1.7 GB |
| idx_patents_authorization_number | authorization_number | 1.3 GB |
| idx_patents_applicant_btree | applicant | 715 MB |
| idx_patents_current_assignee | current_assignee | 699 MB |
| idx_patents_ipc_main_class | ipc_main_class | 510 MB |
| idx_patents_patent_type | patent_type | 502 MB |
| idx_patents_application_date | application_date | 500 MB |
| idx_patents_source_year | source_year | 497 MB |

---

## 🔍 常用查询示例

### 按申请号精确查询

```sql
SELECT * FROM patents
WHERE application_number = 'CN202310123456.7';
```

### 按日期范围查询

```sql
SELECT patent_name, application_date
FROM patents
WHERE application_date BETWEEN '2023-01-01' AND '2023-12-31'
ORDER BY application_date DESC;
```

### 按IPC分类统计

```sql
SELECT ipc_main_class, COUNT(*) as count
FROM patents
WHERE ipc_main_class IS NOT NULL
GROUP BY ipc_main_class
ORDER BY count DESC
LIMIT 20;
```

### 按申请人统计

```sql
SELECT applicant, COUNT(*) as patent_count
FROM patents
WHERE applicant IS NOT NULL
GROUP BY applicant
ORDER BY patent_count DESC
LIMIT 20;
```

---

## 📊 数据分布统计

### 专利类型分布

| 类型 | 约占比例 |
|------|---------|
| 发明专利 | ~40% |
| 实用新型 | ~35% |
| 外观设计 | ~25% |

### 时间分布

| 年份 | 专利数量 |
|------|---------|
| 2024 | 3,126,324 |
| 2023 | 4,919,832 |
| 2022 | 11,463,726 |
| 2021 | 11,621,547 |

### IPC分类热门 (Top 10)

| IPC分类 | 说明 | 专利数量 |
|---------|------|---------|
| G06F | 电数字数据处理 | 254,625 |
| G01N | 化学或物理测试 | 195,557 |
| G06K9/00 | 图像识别 | 152,390 |
| B01D | 分离 | 136,433 |
| A61K | 医药制剂 | 131,297 |

---

## ⚠️ 查询优化建议

1. **使用LIMIT**: 始终使用LIMIT子句限制返回结果
2. **选择合适索引**: 根据查询类型选择合适的检索方式
3. **避免SELECT ***: 只选择需要的字段
4. **使用WHERE子句**: 尽早过滤数据
5. **常见词策略**: 对于常见词，考虑使用关键词检索而非全文检索
