# 法律提示词融合系统部署运维指南

## 1. 适用范围

本指南适用于部署以下能力：

- 法律世界模型 + LLM Wiki 提示词融合 API
- PostgreSQL / Neo4j / Obsidian Wiki 统一知识访问
- wiki 版本感知与提示词模板联动

## 2. 关键模块

- `core/legal_prompt_fusion/`
- `core/api/legal_prompt_fusion_routes.py`
- `core/api/main.py`

## 3. 依赖要求

### 3.1 Python 依赖

建议确保以下依赖可用：

- `fastapi`
- `uvicorn`
- `psycopg2` 或 `psycopg2-binary`
- `neo4j`

可选依赖：

- `watchdog`
- 向量数据库客户端
- 文本重排模型相关依赖

### 3.2 外部服务

- PostgreSQL
- Neo4j
- Athena API 主服务
- 本地 Obsidian wiki 挂载目录

## 4. 环境变量

建议配置：

```bash
export LEGAL_PG_DSN="postgresql://user:password@localhost:5432/legal_db"
export LEGAL_PG_SCHEMA="public"

export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your_password"
export NEO4J_DATABASE="neo4j"

export LEGAL_WIKI_ROOT="/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库"
export LEGAL_WIKI_WATCH_ENABLED="false"

export LEGAL_FUSION_TOP_K="5"
export LEGAL_FUSION_MAX_EVIDENCE="12"
export LEGAL_FUSION_CACHE_TTL="900"
```

## 5. 数据准备

## 5.1 PostgreSQL

建议至少准备 `legal_documents` 表，字段建议：

- `id`
- `title`
- `article_title`
- `content`
- `article_text`
- `summary`
- `updated_at`

建议索引：

```sql
CREATE INDEX IF NOT EXISTS idx_legal_documents_tsv
ON legal_documents
USING GIN (
  to_tsvector(
    'simple',
    COALESCE(title, '') || ' ' || COALESCE(content, '') || ' ' || COALESCE(summary, '')
  )
);
```

## 5.2 Neo4j

建议至少保证以下节点类型存在：

- `ScenarioRule`
- `LegalDocument`
- `ReferenceCase`
- `LegalConcept`

建议索引：

```cypher
CREATE INDEX scenario_rule_key IF NOT EXISTS
FOR (n:ScenarioRule) ON (n.domain, n.task_type, n.phase);
```

## 5.3 Wiki

确保以下目录可读：

- `/Users/xujian/Library/Mobile Documents/iCloud~md~obsidian/Documents/宝宸知识库`

建议运维规则：

- 重要专题页保持稳定命名
- 每个专题页带一级标题
- 关键页增加标签与索引页引用

## 6. 启动方式

如果使用现有主 API 服务，新的路由会在 `core/api/main.py` 启动时自动注册。

本地开发示例：

```bash
PYTHONPATH=/Users/xujian/Athena工作平台 \
python3 -m core.api.main
```

或按项目现有方式启动主服务。

## 7. 健康检查

### 7.1 服务健康

```bash
curl http://localhost:8000/api/v1/legal-prompt-fusion/health
```

### 7.2 同步状态

```bash
curl http://localhost:8000/api/v1/legal-prompt-fusion/sync/status
```

### 7.3 上下文生成

```bash
curl -X POST http://localhost:8000/api/v1/legal-prompt-fusion/context/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "请分析该专利方案是否具备创造性",
    "domain": "patent",
    "scenario": "creativity_analysis",
    "additional_context": {"jurisdiction": "CN"},
    "top_k_per_source": 5
  }'
```

## 8. 运维建议

## 8.1 日志

建议新增以下日志维度：

- query
- scenario
- wiki_revision
- template_version
- evidence_count
- source_distribution
- fallback_reason

## 8.2 缓存

建议将以下内容接入 Redis：

- wiki revision 状态
- query 检索结果
- 已渲染 prompt context

缓存 key 建议：

- `legal_fusion:wiki_revision`
- `legal_fusion:evidence:{hash(query)}`
- `legal_fusion:prompt:{template_version}:{hash(query)}`

## 8.3 性能告警

建议设置阈值：

- 单次上下文生成 > 1500ms 告警
- wiki 扫描 > 5000ms 告警
- PostgreSQL 检索失败率 > 5% 告警
- Neo4j 检索失败率 > 5% 告警

## 8.4 回滚策略

当融合链路异常时：

1. 保留原 `prompt_system_routes.py`
2. 关闭新路由调用入口
3. 将 `LEGAL_FUSION_ENABLE_*` 逐项置为 `false`
4. 回退到仅场景规则提示词模式

## 9. 测试执行

当前新增的基础测试可用以下方式执行：

```bash
pytest tests/unit/test_legal_prompt_fusion.py -v
```

建议在接入真实数据库后新增：

- 集成测试
- 压测
- wiki 变更触发测试
- 缓存失效测试

## 10. 常见问题

### Q1: wiki 扫描很慢怎么办？

- 首先改用增量索引
- 只扫描目标专题目录
- 将大文档切片并持久化缓存

### Q2: PostgreSQL 查不到数据怎么办？

- 检查 `LEGAL_PG_DSN`
- 检查 `legal_documents` 表是否存在
- 检查全文索引是否建立

### Q3: Neo4j 没有返回结果怎么办？

- 检查节点标签和字段名
- 检查数据库名是否为 `NEO4J_DATABASE`
- 检查用户权限和 Bolt 连接

## 11. 下一步运维增强

建议后续补充：

- 定时 reindex 任务
- Prometheus 指标暴露
- 版本漂移告警
- query 热点预热
- A/B 实验面板
