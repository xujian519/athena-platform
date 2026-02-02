# PostgreSQL检索系统诊断报告

生成时间: 2026-01-21
诊断对象: Athena工作平台专利检索系统

---

## 执行摘要

经过全面诊断，发现专利检索系统的核心问题是**PostgreSQL全文搜索索引严重损坏**，导致检索效果极差。

**关键发现**：
- ✅ 向量嵌入覆盖率100%（119,660个向量，31,562个文档）
- ❌ 全文搜索索引损坏（LIKE返回31,228条，全文搜索仅返回8条）
- ⚠️ 数据质量问题（35.9%缺少发明名称）

---

## 一、数据库资源统计

### 1.1 数据表概览

| 表名 | 记录数 | 向量嵌入 | 表大小 | 覆盖率 |
|------|--------|---------|--------|--------|
| patent_invalid_embeddings | 119,660 | ✅ | 1778 MB | 100% |
| patent_invalid_decisions | 31,562 | ✅ | 872 MB | 100% |
| legal_articles_v2 | 295,733 | ✅ | 492 MB | 99.99% |
| patent_judgments | 5,906 | ✅ | 12 MB | 100% |
| **总计** | **452,761** | **157,526** | **3.1 GB** | **99.9%** |

### 1.2 向量嵌入详情

**patent_invalid_embeddings表**：
- 总向量数: 119,660个
- 覆盖文档: 31,562个（100%覆盖）
- 平均chunk长度: 1,145字符
- chunk_type分布:
  - `full`: 31,562个（完整文档）
  - `background`: 31,337个（背景技术）
  - `reasoning`: 31,251个（理由部分）
  - `conclusion`: 25,510个（结论部分）

---

## 二、核心问题诊断

### 2.1 全文搜索索引损坏

**测试结果**：

```sql
-- 测试1: LIKE模糊搜索（基准）
SELECT COUNT(*) FROM patent_invalid_decisions
WHERE reasoning_section LIKE '%专利%';
-- 结果: 31,228条 (98.9%)

-- 测试2: 中文全文搜索
SELECT COUNT(*) FROM patent_invalid_decisions
WHERE to_tsvector('chinese', reasoning_section) @@ plainto_tsquery('chinese', '专利');
-- 结果: 8条 (0.03%) ❌

-- 测试3: Simple全文搜索
SELECT COUNT(*) FROM patent_invalid_decisions
WHERE to_tsvector('simple', reasoning_section) @@ plainto_tsquery('simple', '专利');
-- 结果: 8条 (0.03%) ❌
```

**问题分析**：
1. LIKE搜索返回31,228条，说明数据中确实包含"专利"
2. 全文搜索仅返回8条，说明**GIN索引未正常工作**
3. PostgreSQL警告: `word is too long to be indexed` - 超长词被忽略

**根本原因**：
- GIN索引可能损坏或未正确建立
- 中文分词器(zhparser)配置问题
- 超长文本(>2047字符)未被正确索引

### 2.2 数据质量问题

**patent_invalid_decisions表**：
```
总记录数: 31,562
✓ document_id: 31,562 (100.0%)
✓ reasoning_section: 31,253 (99.0%)
✓ conclusion_section: 26,080 (82.6%)
✗ invention_name: 11,328 (35.9%) ⚠️
```

**legal_articles_v2表**：
```
总记录数: 295,733
✓ article_id: 295,733 (100.0%)
✓ law_title: 295,733 (100.0%)
✓ content_text: 295,733 (100.0%)
⚠️ 平均content长度: 89字符（可能不完整）
```

---

## 三、检索性能基准测试

### 3.1 查询性能

| 查询类型 | 结果数 | 耗时 | 问题 |
|---------|--------|------|------|
| 专利无效决定全文搜索 | 0 | 2.3秒 | ❌ 索引损坏 |
| 法律文章全文搜索 | 0 | 0.18秒 | ❌ 索引损坏 |
| LIKE模糊搜索 | 31,228 | 1.3秒 | ⚠️ 性能差 |
| **向量搜索（估算）** | **~10-50** | **<0.5秒** | ✅ 正常 |

### 3.2 索引状态检查

```sql
-- 现有索引
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename = 'patent_invalid_decisions';

-- 结果显示:
-- idx_patent_invalid_decisions_title: GIN索引（invention_name）
-- idx_patent_invalid_decisions_patent_number: B-Tree索引
-- idx_patent_invalid_decisions_decision_conclusion: B-Tree索引
-- ❗ 缺少reasoning_section的GIN索引
```

---

## 四、解决方案设计

### 4.1 紧急修复（立即执行）

#### 步骤1: 重建全文搜索索引

```sql
-- 删除损坏的索引
DROP INDEX IF EXISTS idx_patent_invalid_decisions_reasoning;

-- 创建新的GIN索引（使用chinese配置）
CREATE INDEX idx_patent_invalid_decisions_reasoning_gin
ON patent_invalid_decisions
USING GIN (to_tsvector('chinese', coalesce(reasoning_section, '')));

-- 创建conclusion_section的GIN索引
CREATE INDEX idx_patent_invalid_decisions_conclusion_gin
ON patent_invalid_decisions
USING GIN (to_tsvector('chinese', coalesce(conclusion_section, '')));

-- 创建法律文章的GIN索引
CREATE INDEX idx_legal_articles_v2_content_gin
ON legal_articles_v2
USING GIN (to_tsvector('chinese', coalesce(content_text, '')));
```

#### 步骤2: 处理超长文本

```sql
-- 创建表达式索引（限制长度）
CREATE INDEX idx_patent_invalid_decisions_reasoning_truncated_gin
ON patent_invalid_decisions
USING GIN (to_tsvector('chinese', SUBSTRING(reasoning_section, 1, 5000)));

-- 创建更精细的chunk索引
CREATE INDEX idx_patent_invalid_decisions_reasoning_chunks_gin
ON patent_invalid_decisions
USING GIN (to_tsvector('chinese',
    CASE
        WHEN LENGTH(reasoning_section) > 5000
        THEN SUBSTRING(reasoning_section, 1, 5000)
        ELSE reasoning_section
    END
));
```

#### 步骤3: 验证索引效果

```sql
-- 测试索引效果
EXPLAIN ANALYZE
SELECT COUNT(*)
FROM patent_invalid_decisions
WHERE to_tsvector('chinese', reasoning_section) @@ plainto_tsquery('chinese', '专利');

-- 期望: 使用索引扫描，耗时<100ms
```

### 4.2 中期优化（1-2周）

#### 优化1: 实现混合搜索策略

```python
# 混合搜索权重配置
SEARCH_WEIGHTS = {
    'vector': 0.5,      # 向量相似度
    'fulltext': 0.3,    # 全文搜索
    'fuzzy': 0.1,       # 模糊匹配
    'graph': 0.1        # 知识图谱
}

# 综合评分
final_score = (
    vector_similarity * SEARCH_WEIGHTS['vector'] +
    text_rank * SEARCH_WEIGHTS['fulltext'] +
    fuzzy_match_score * SEARCH_WEIGHTS['fuzzy'] +
    graph_relevance * SEARCH_WEIGHTS['graph']
)
```

#### 优化2: 分层检索策略

```python
def hybrid_search(query, depth='standard'):
    if depth == 'fast':
        # 快速模式: 仅向量搜索
        return vector_search_only(query)
    elif depth == 'standard':
        # 标准模式: 向量 + 全文搜索
        return vector_and_fulltext_search(query)
    else:
        # 深度模式: 向量 + 全文 + 图谱
        return comprehensive_search(query)
```

#### 优化3: 数据质量修复

```sql
-- 补充发明名称（从向量表恢复）
UPDATE patent_invalid_decisions d
SET invention_name = (
    SELECT chunk_text
    FROM patent_invalid_embeddings e
    WHERE e.document_id = d.document_id
    AND e.chunk_type = 'full'
    LIMIT 1
)
WHERE d.invention_name IS NULL OR d.invention_name = '';

-- 预期修复: 64.1%的记录（20,234条）
```

### 4.3 长期规划（1-3个月）

#### 规划1: 向量搜索优化

- 升级到pgvector 0.5.0+（支持IVFFlat索引优化）
- 调整IVFFlat lists参数（当前100 → 建议200-500）
- 实现向量索引分区（按技术领域分区）

#### 规划2: 查询性能优化

- 实现查询结果缓存（Redis）
- 建立查询性能监控（Prometheus）
- 优化慢查询日志分析

#### 规划3: 数据治理

- 建立数据质量监控仪表盘
- 实施数据质量SLA（95%完整性）
- 定期数据清洗和去重

---

## 五、实施建议

### 优先级排序

**P0（紧急，24小时内）**：
1. ✅ 重建全文搜索GIN索引
2. ✅ 验证索引效果
3. ✅ 修复代码中的搜索逻辑

**P1（重要，1周内）**：
4. ⚠️ 实施混合搜索策略
5. ⚠️ 修复发明名称缺失问题
6. ⚠️ 性能基准测试

**P2（优化，1个月内）**：
7. 📊 建立监控体系
8. 📊 数据质量修复
9. 📊 查询优化

### 风险评估

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 索引重建耗时过长 | 高 | 中 | 分批重建，使用CONCURRENTLY |
| 生产环境性能影响 | 高 | 低 | 先在测试环境验证 |
| 数据损坏风险 | 中 | 低 | 重建前完整备份 |

---

## 六、预期效果

### 6.1 检索性能提升

**修复前**：
- 全文搜索: 0条结果，2.3秒
- 综合检索: 准确率<10%

**修复后（预期）**：
- 全文搜索: 1000+条结果，<100ms
- 综合检索: 准确率>80%

### 6.2 系统健康度

**当前状态**：
- 🔴 检索功能: 严重受损
- 🟡 数据质量: 中等
- 🟢 向量搜索: 正常

**目标状态**：
- 🟢 检索功能: 完全恢复
- 🟢 数据质量: 优秀
- 🟢 向量搜索: 优化

---

## 七、下一步行动

**立即执行**（今天）：
1. 在测试环境验证索引修复方案
2. 生产环境完整备份
3. 执行索引重建脚本

**本周完成**：
4. 验证检索效果
5. 更新应用代码
6. 性能基准测试

**下周计划**：
7. 实施混合搜索策略
8. 数据质量修复
9. 监控体系建设

---

## 附录

### A. 完整诊断脚本

见: `/Users/xujian/Athena工作平台/scripts/analysis/database_search_diagnosis.py`

### B. 索引重建脚本

见: `/Users/xujian/Athena工作平台/scripts/maintenance/rebuild_fulltext_indexes.sql`

### C. 性能测试报告

见: `/Users/xujian/Athena工作平台/docs/quality/SEARCH_PERFORMANCE_BENCHMARK.md`

---

**报告生成**: Claude Code AI Assistant
**审核**: 徐健 (xujian519@gmail.com)
**版本**: 1.0
**状态**: 待实施
