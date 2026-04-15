# 代码质量审查报告 - 2026-04-14 宝宸知识库集成 & 嵌入模型切换

> 审查范围：今天新建/修改的所有文件（3 个独立脚本 + 5 个核心模块 + 4 个配置/嵌入服务）
> 审查标准：正确性、健壮性、安全性、性能、可维护性

---

## 审查结果概览

| 严重级别 | 数量 | 说明 |
|---------|------|------|
| **Critical** | 9 | 会导致运行时崩溃或数据损坏 |
| **High** | 21 | 可能导致功能异常或性能严重退化 |
| **Medium** | 28 | 代码质量和健壮性问题 |
| **Low** | 14 | 代码风格和可维护性问题 |

---

## Critical 问题（必须立即修复）

### C1. `baochen_sync_scheduler.py` upsert payload 引用不存在的 key
- **位置**: 第 164 行
- **问题**: payload 中引用 `"chunk_text"`，但 `_mkchunk()` 生成的 dict 使用 `"text"` 作为键名
- **影响**: **每次 upsert 都会抛出 KeyError，增量同步完全不可用**
- **修复**: 将 `"chunk_text"` 改为 `"text"`

### C2. 三个脚本间大量代码重复导致 bug 传播
- **位置**: `baochen_sync_scheduler.py` + `sync_baochen_kb_standalone.py`
- **问题**: `collect_files`、`split_into_chunks`、`infer_source`、`embed_texts`、`upsert_batch` 等函数在两个文件中几乎完全相同。C1 即为复制粘贴时的遗漏
- **修复**: 提取共享代码到 `scripts/baochen_sync_common.py`

### C3. `qdrant_writer.py` `delete_all()` 方法不生效
- **位置**: 第 134-146 行
- **问题**: 使用 `{"filter": {"must": []}}` 空条件删除，Qdrant 中空 must 不匹配任何文档
- **影响**: 全量重建时旧数据不会被清除，产生重复/孤立数据
- **修复**: 改为删除 collection 再重建，或使用 scroll + delete by IDs

### C4. `sync_manager.py` 硬编码绝对路径
- **位置**: 第 23 行 `DEFAULT_WIKI_PATH = "/Users/xujian/projects/宝宸知识库/Wiki"`
- **影响**: 其他环境全部失败
- **修复**: 从环境变量读取

### C5. `bge_embedding_service.py` API 降级不可恢复
- **位置**: 第 169-179 行 `initialize()`
- **问题**: 启动时一次性检测 API 可用性，降级后即使 API 恢复也不会切回
- **修复**: 在 `encode()` 中增加重试机制，API 恢复后自动切回

### C6. `bge_embedding_service.py` 单文本 encode 返回值类型不一致
- **位置**: 第 249-261 行
- **问题**: 单文本时返回 `list[float]`（一维），批量时返回 `list[list[float]]`（二维）。调用方用 `result.embeddings[0]` 访问，单文本时得到 `float` 而非向量
- **修复**: 统一返回 `list[list[float]]`，不拆包

### C7. `bge_m3_loader.py` 缺少 `load_bge_m3_model` 函数
- **位置**: 文件末尾导出区域
- **问题**: 调用方 `production/core/judgment_vector_db/data_processing/vectorizer.py` 导入 `load_bge_m3_model`，但该函数不存在
- **影响**: ImportError 运行时崩溃
- **修复**: 添加此函数导出

### C8. `chunk_processor.py` `_split_by_paragraphs` 无超长保护
- **位置**: 第 214-234 行
- **问题**: 单个段落超过 `chunk_size` 时直接作为整个 chunk 返回，可能远超限制
- **修复**: 对超长段落做字符级或句子级截断

### C9. `baochen_retriever.py` async 方法中使用同步 requests
- **位置**: 第 102 行、第 172 行
- **问题**: `async def search()` 内部调用 `self.session.post()` 是同步阻塞操作，会阻塞事件循环
- **修复**: 改用 `httpx.AsyncClient` 或 `asyncio.to_thread()`

---

## High 问题（尽快修复）

### H1. 嵌入失败时写入全零向量（scheduler + standalone）
- 零向量经 L2 归一化后变成 NaN，污染 Qdrant 索引
- 修复: 失败时跳过 chunk 并记录错误日志

### H2. `sync_manager.py` 增量同步批次失败导致数据永久丢失
- 中间批次失败时状态文件仍被更新，失败的文件不会被重试
- 修复: 失败时标记状态为不完整

### H3. `qdrant_writer.py` `_ensure_collection` 失败静默通过
- 构造函数中 Qdrant 不可用时对象仍被创建，后续操作静默失败

### H4. `baochen_retriever.py` `_embed_query` 输入类型可能不匹配
- 传入 `str` 但 `UnifiedEmbeddingService.encode` 可能期望 `list[str]`

### H5. `bge_embedding_service.py` `_encode_via_api` 缺少重试机制
- 单次失败导致整个 batch 数据丢失

### H6. `bge_m3_loader.py` dummy 向量静默返回假数据
- simple_backend 模式下所有文本返回相同随机向量，语义搜索完全失效，且无任何告警

### H7. `vector_config.py` `bert_chinese` 维度声明错误
- `bert-base-chinese` 实际维度为 768，配置为 1024，会导致向量索引创建失败

### H8. `bge_model_config.py` `is_model_available()` 在 API 模式下语义错误
- 只检查本地路径，API 模式下永远返回 False

### H9. 状态文件写入非原子操作（scheduler + standalone + sync_manager）
- 中断时损坏状态文件，下次启动丢失全部历史状态

### H10. `baochen_sync_scheduler.py` cron 移除逻辑不完善
- 注释行和 cron 行之间有空行时注释不会被移除

### H11. `infer_source` 返回 None 未处理
- 三个文件的 `infer_source` 在 kb_cat 不在预定义字典时返回 `(None, None)`

---

## 修复优先级建议

### P0 — 立即修复（阻塞功能使用）

| # | 问题 | 文件 | 工作量 |
|---|------|------|--------|
| 1 | C1: chunk_text → text | `baochen_sync_scheduler.py:164` | 1 行 |
| 2 | C7: 添加 `load_bge_m3_model` 导出 | `bge_m3_loader.py` | 5 行 |
| 3 | C6: 统一 encode 返回值类型 | `bge_embedding_service.py` | ~10 行 |

### P1 — 本周修复（数据正确性）

| # | 问题 | 文件 | 工作量 |
|---|------|------|--------|
| 4 | C3: 修复 delete_all | `qdrant_writer.py` | ~20 行 |
| 5 | C4: 环境变量配置化 | `sync_manager.py` + scripts | ~15 行 |
| 6 | H1: 零向量→跳过+日志 | 两个脚本 | ~10 行 |
| 7 | H9: 原子写入状态文件 | 3 个文件 | ~15 行 |
| 8 | C9: async→httpx | `baochen_retriever.py` | ~30 行 |

### P2 — 下个迭代修复（质量改善）

| # | 问题 | 文件 |
|---|------|------|
| 9 | C2: 提取共享代码 | scripts/ |
| 10 | C5: API 降级恢复 | `bge_embedding_service.py` |
| 11 | H2: 批次失败保护 | `sync_manager.py` |
| 12 | H7: 修正 bert 维度 | `vector_config.py` |
| 13 | H8: API 模式检查 | `bge_model_config.py` |
| 14 | C8: 超长 chunk 截断 | `chunk_processor.py` |

---

## 审查的完整文件清单

### 新建文件（7个）
- `scripts/baochen_sync_scheduler.py`
- `scripts/sync_baochen_kb_standalone.py`
- `scripts/sync_baochen_kb.py`
- `core/knowledge_sync/__init__.py`
- `core/knowledge_sync/chunk_processor.py`
- `core/knowledge_sync/qdrant_writer.py`
- `core/knowledge_sync/sync_manager.py`
- `core/knowledge_sync/baochen_retriever.py`
- `prompts/foundation/baochen_legal_prompts.yaml`

### 修改文件（5个）
- `config/bge_model_config.py`
- `config/vector_config.py`
- `core/nlp/bge_embedding_service.py`
- `core/nlp/bge_m3_loader.py`
- `core/config/unified_config.py`
