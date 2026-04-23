# 法律世界模型与 LLM Wiki 提示词深度融合技术方案

## 1. 目标

本方案面向 Athena 现有提示词系统，构建一套可落地的法律知识融合底座，使以下三类知识源能够统一服务于动态提示词生成：

- PostgreSQL 中的结构化法律数据
- Neo4j 中的法律关系图谱与场景规则
- Obsidian Wiki 中持续演化的非结构化实务知识

目标不是简单增加一个 RAG 检索接口，而是形成“数据层统一访问 + 实时同步 + 混合检索 + 动态提示词构建 + 验证评估”的完整闭环。

## 2. 总体架构

建议采用四层架构：

### 2.1 Source Layer

- `PostgreSQL`
  - 法条、案例、裁判规则、结构化摘要
  - 适合作为高可信硬证据层
- `Neo4j`
  - 法律概念关系、场景规则、案例关联、流程关系
  - 适合作为关系推理和场景编排层
- `Obsidian Wiki`
  - 法律实务笔记、专题知识页、实务解释、索引
  - 适合作为背景解释和经验知识层

### 2.2 Knowledge Access Layer

本次新增的 `core/legal_prompt_fusion/` 作为统一接入层，主要组件包括：

- `providers.py`
  - 统一封装 PostgreSQL / Neo4j / Wiki 访问
- `wiki_indexer.py`
  - 扫描 Obsidian 目录
  - 计算 wiki 修订版本
  - 生成轻量片段索引
- `hybrid_retriever.py`
  - 多源证据融合与排序
- `sync_manager.py`
  - 知识变更映射到模板版本
- `prompt_context_builder.py`
  - 把证据编译成可直接用于提示词系统的上下文

### 2.3 Prompt Runtime Layer

- 现有动态提示词系统继续负责:
  - 场景识别
  - 场景规则提取
  - 提示词入口管理
- 新增融合层负责:
  - 拉取多源知识
  - 注入最新法律条文
  - 注入图谱关系链
  - 注入 wiki 背景知识
  - 输出带版本信息的提示词上下文

### 2.4 Governance Layer

- 知识同步状态跟踪
- 模板版本与 wiki 修订绑定
- 关联性验证
- 提示词效果指标评估

## 3. 数据层集成设计

## 3.1 统一访问接口

统一访问入口定义为：

- `UnifiedLegalKnowledgeRepository.retrieve_all(query, top_k_per_source)`
- `HybridLegalRetriever.retrieve(query, top_k_per_source)`
- `LegalPromptContextBuilder.build(request)`

这样做的好处是：

- 提示词系统不需要关心底层是 PostgreSQL、Neo4j 还是本地文件
- 后续可以在不改上层 API 的情况下替换为 pgvector、Qdrant 或全文索引引擎

## 3.2 PostgreSQL 职责

PostgreSQL 承担“结构化硬证据”角色，建议沉淀以下表：

- `legal_documents`
- `legal_articles`
- `reference_cases`
- `judgment_rules`
- `prompt_knowledge_snapshots`

查询责任：

- 最新法条
- 结构化案例摘要
- 明确的生效时间与版本
- 业务规则的结构化字段

## 3.3 Neo4j 职责

Neo4j 承担“关系推理与场景联结”角色，建议保留：

- `ScenarioRule`
- `LegalDocument`
- `ReferenceCase`
- `LegalConcept`
- `ProcedureStep`

推荐关系：

- `(:LegalConcept)-[:SUPPORTED_BY]->(:LegalDocument)`
- `(:ReferenceCase)-[:APPLIES_TO]->(:ScenarioRule)`
- `(:ProcedureStep)-[:NEXT]->(:ProcedureStep)`
- `(:ScenarioRule)-[:REQUIRES_ARTICLE]->(:LegalDocument)`

## 3.4 Obsidian Wiki 职责

Obsidian Wiki 承担“背景解释与动态经验知识”角色，适合承载：

- 创造性判断专题
- 侵权规则专题
- 专利程序与修改专题
- 裁判规则拆解页
- 索引与专题导航页

新组件 `wiki_indexer.py` 会：

- 扫描 markdown 文件
- 解析标题、标签、heading
- 提取与 query 最相关的片段
- 计算 `wiki_revision`

## 4. 动态提示词生成机制

## 4.1 生成流程

1. 提示词系统接收用户问题
2. 现有场景识别器识别 `domain + task_type + phase`
3. 新融合层发起三路检索：
   - PostgreSQL: 法条/案例
   - Neo4j: 场景规则/关系链
   - Wiki: 背景知识/实务说明
4. `HybridLegalRetriever` 对证据重新排序
5. `LegalPromptContextBuilder` 生成：
   - `system_prompt`
   - `user_prompt`
   - `context.freshness`
   - `context.diagnostics`
6. 上层 LLM 使用融合后的提示词执行回答

## 4.2 提示词上下文编排原则

建议把上下文分成四个块：

- `法律条文块`
  - 仅放高可信结构化依据
- `图谱推理块`
  - 仅放关系链和场景规则
- `wiki 背景块`
  - 仅放解释性知识
- `新鲜度块`
  - 记录当前 wiki revision 和索引文档数

这样能避免：

- 把经验性知识伪装成法条
- 把关系推理误写成确定规则
- 模型误判不同知识来源的可信等级

## 5. 知识同步与更新策略

## 5.1 触发机制

建议采用“双触发”策略：

- 被动触发
  - API 请求到来时检查 `wiki_revision`
- 主动触发
  - 文件监听器检测 Obsidian 目录变更
  - 定时任务做增量索引

## 5.2 模板版本联动

`WikiSyncManager` 通过：

- `wiki_revision`
- `template_family`

生成 `template_version`。

这样当 wiki 内容更新时：

- 提示词模板版本自动变化
- 缓存可以基于新版本失效
- 线上效果评估可按版本对比

## 5.3 关联性验证

每次生成融合上下文后，应执行验证：

- 是否命中法条证据
- 是否命中图谱关系
- 是否命中 wiki 背景
- 是否缺少任一关键维度

若三类维度全部缺失，则降级为：

- 仅场景规则提示词
- 或要求用户补充信息

## 6. 混合检索增强生成架构

## 6.1 检索策略

建议采用“结构化优先 + 关系增强 + 语义补充”的三段式检索：

### 第一段：结构化检索

- PostgreSQL 全文 / 结构化过滤
- 召回高可信法条和案例

### 第二段：图谱关系检索

- Neo4j 查相关规则节点
- 扩展一跳/两跳关系
- 补足场景链路和推理线索

### 第三段：语义补充

- Wiki 或向量库召回背景解释
- 用于提升解释性与上下文完整度

## 6.2 排序规则

当前实现使用轻量排序：

- PostgreSQL 略高权重
- Neo4j 中权重
- Wiki 作为解释性补充

后续建议升级为：

- Cross-encoder 重排
- 基于场景的权重模板
- 线上反馈驱动的学习排序

## 7. API 设计

本次已新增：

- `GET /api/v1/legal-prompt-fusion/health`
- `GET /api/v1/legal-prompt-fusion/sync/status`
- `POST /api/v1/legal-prompt-fusion/context/generate`

建议未来继续增加：

- `POST /api/v1/legal-prompt-fusion/sync/reindex`
- `POST /api/v1/legal-prompt-fusion/validate/relevance`
- `POST /api/v1/legal-prompt-fusion/evaluate/prompt`

## 8. 缓存策略

建议分三级缓存：

### L1 Request Cache

- key: `query + scenario + top_k`
- TTL: 5-15 分钟

### L2 Knowledge Revision Cache

- key: `wiki_revision + template_family`
- 只要 revision 不变即可复用

### L3 Evidence Cache

- 按 source + query 缓存检索结果
- PostgreSQL / Neo4j / wiki 分别缓存

当 `wiki_revision` 变化时：

- 失效 L2 / L3 的 wiki 部分
- 保留 PostgreSQL/Neo4j 稳定缓存

## 9. 性能优化建议

- Wiki 索引改成增量索引，避免每次全量扫描
- 对 PostgreSQL 增加 `GIN + tsvector` 索引
- 对 Neo4j 场景节点建立 `domain/task_type/phase` 组合索引
- 把 wiki 文档拆片后接入向量库，避免纯字符串匹配
- 引入后台重排队列，对热点 query 进行缓存预热

## 10. 测试验证体系

## 10.1 单元测试

已新增：

- `tests/unit/test_legal_prompt_fusion.py`

覆盖：

- wiki 扫描与 revision 生成
- sync manager 的模板版本联动
- prompt context builder 的三源融合能力

## 10.2 集成测试建议

后续应新增：

- PostgreSQL + Neo4j + wiki 联调测试
- wiki 变更后模板版本更新测试
- query 到 prompt 的端到端测试
- 缓存失效与回填测试

## 10.3 一致性检查

建议建立以下检查：

- 法条标题是否能在 PostgreSQL 找到来源
- 图谱关系节点是否能反查到规则或案例
- wiki 片段是否引用有效文件路径
- 不同源的时间戳是否超期

## 10.4 效果评估指标

- `context_evidence_coverage`
- `legal_basis_presence_rate`
- `wiki_freshness_hit_rate`
- `graph_relation_usage_rate`
- `first_answer_acceptance_rate`
- `followup_rate`

## 11. 与现有系统的接入方式

当前实现采用“最少侵入接入”：

- 保留原 `prompt_system_routes.py`
- 新增 `legal_prompt_fusion_routes.py`
- 在 `core/api/main.py` 中注册新路由

后续推荐把两条链路合并为：

- 场景识别由原系统负责
- 多源知识融合由新模块负责
- 统一由 prompt runtime 输出最终提示词

## 12. 当前落地状态

已完成：

- 统一融合模块骨架
- Obsidian wiki 扫描与 revision 计算
- PostgreSQL / Neo4j / wiki 统一访问接口
- 混合检索器
- 动态提示词上下文构建器
- 模板版本联动器
- FastAPI 路由接入
- 基础单元测试

下一阶段优先事项：

1. 将 wiki 从轻量扫描升级为增量索引与向量检索
2. 为 PostgreSQL `legal_documents` 建立明确 schema 和索引
3. 为 Neo4j 增加关系扩展查询和场景化图检索
4. 与现有 `prompt_system_routes.py` 做真正的运行时合流
