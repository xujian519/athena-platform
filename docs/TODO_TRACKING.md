# Athena平台技术债务追踪

**更新日期**: 2026-03-26
**版本**: v2.2.0

---

## 📊 TODO统计

| 类型 | 数量 | 优先级 |
|-----|------|-------|
| 功能实现 | 85 | P2 |
| 集成工作 | 45 | P2 |
| 异常处理 | 15 | P1 |
| 代码优化 | 25 | P3 |
| 测试补充 | 21 | P2 |
| **总计** | **191** | - |

---

## 🔴 高优先级 (P1) - 需要立即处理

### 异常处理TODO (需要指定具体异常类型)

| 文件 | 行号 | 当前处理 | 建议 |
|-----|------|---------|-----|
| `core/acceleration/m4_neural_engine_optimizer.py` | 60 | `except Exception` | 指定 `torch` 相关异常 |
| `core/tools/real_tool_implementations.py` | 54 | `except Exception` | 指定工具相关异常 |
| `core/xiaonuo_agent/memory/episodic_memory.py` | 195 | `except Exception` | 指定存储相关异常 |
| `core/legal_kg/legal_text_parser.py` | 243 | `except Exception` | 指定解析相关异常 |
| `core/collaboration/on_demand_agent_orchestrator.py` | 361 | `except Exception` | 指定编排相关异常 |

---

## 🟡 中优先级 (P2) - 计划中

### 集成工作TODO

| 文件 | 行号 | 描述 | 依赖 |
|-----|------|-----|-----|
| `core/pipeline/legal_book_pipeline.py` | 214 | 集成OCR引擎 | OCR SDK |
| `core/llm/rag_manager.py` | 219 | 集成Neo4j知识图谱查询 | Neo4j客户端 |
| `core/storm_integration/patent_curator.py` | 111 | 数据库连接检查 | PostgreSQL |
| `core/storm_integration/patent_curator.py` | 159 | Neo4j连接检查 | Neo4j |
| `core/storm_integration/patent_curator.py` | 207 | Qdrant连接检查 | Qdrant |
| `core/storm_integration/patent_curator.py` | 631 | 集成重排序模型 | Cohere API |
| `core/capabilities/rag_capability_adapter.py` | 115 | 集成Neo4j知识图谱查询 | Neo4j |

### 功能实现TODO

| 文件 | 行号 | 描述 |
|-----|------|-----|
| `core/thinking_modes/mode_selector.py` | 311 | 实现ReAct循环 |
| `core/thinking_modes/mode_selector.py` | 323 | 实现Plan模式 |
| `core/thinking_modes/mode_selector.py` | 335 | 实现SOPPlan模式 |
| `core/thinking_modes/mode_selector.py` | 347 | 实现Executor模式 |
| `core/thinking_modes/mode_selector.py` | 359 | 实现TreeOfThought模式 |
| `core/judgment_vector_db/storage/qdrant_client.py` | 215 | 实现过滤器逻辑 |
| `core/judgment_vector_db/retrieval/hybrid_retriever.py` | 412 | 实现更复杂的图谱遍历 |

---

## 🟢 低优先级 (P3) - 未来优化

### 代码优化TODO

| 文件 | 行号 | 描述 |
|-----|------|-----|
| `core/llm/dual_model_coordinator.py` | 262 | 实现更复杂的答案比较逻辑 |
| `core/llm/dual_model_coordinator.py` | 297 | 使用更复杂的语义相似度计算 |
| `core/fusion/vgraph_joint_index.py` | 290 | 集成NebulaGraph客户端 |

---

## ✅ 已完成的TODO

| 日期 | 文件 | 描述 | 完成者 |
|-----|------|-----|-------|
| 2026-03-26 | `core/nlp/xiaonuo_semantic_similarity.py` | 添加numpy导入 | Claude |
| 2026-03-26 | `production/core/nlp/xiaonuo_semantic_similarity.py` | 添加numpy导入 | Claude |
| 2026-03-26 | `core/nlp/bge_embedding_service.py` | 修复类型注解语法 | Claude |
| 2026-03-26 | `core/intent/keyword_engine_refactored.py` | 修复类型注解语法 | Claude |

---

## 📝 处理指南

### 如何处理异常处理TODO

1. 查看异常发生的上下文
2. 确定可能抛出的具体异常类型
3. 使用多个 `except` 块分别处理不同异常
4. 添加适当的日志记录

示例:
```python
# 修改前
except Exception as e:  # TODO
    logger.error(f"操作失败: {e}")

# 修改后
except (ConnectionError, TimeoutError) as e:
    logger.error(f"网络连接失败: {e}")
    raise ServiceUnavailableError(f"服务不可用: {e}")
except ValueError as e:
    logger.warning(f"数据格式错误: {e}")
    return None
```

---

## 🔄 更新日志

- **2026-03-26**: 初始创建，记录191个TODO项
- **2026-03-26**: 完成测试导入修复任务，记录4个已完成的TODO
