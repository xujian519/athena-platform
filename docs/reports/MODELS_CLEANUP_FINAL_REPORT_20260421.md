# models目录清理完成报告

> **日期**: 2026-04-21  
> **清理原因**: BGE-M3模型使用8766端口API服务，不需要本地文件

---

## 📊 **清理结果**

### 清理前后对比

| 项目 | 清理前 | 清理后 | 改善 |
|------|--------|--------|------|
| **子目录数** | 14个 | **4个** | **71.4% ↓** |
| **目录大小** | 511MB | **510MB** | 基本不变 |
| **删除目录** | - | **7个** | - |

---

## ✅ **已删除的目录** (7个)

| 目录 | 原因 |
|------|------|
| `embedding/` | 未使用，BGE-M3使用8766端口API |
| `image_generation/` | 未使用 |
| `llm/` | 未使用 |
| `modelscope/` | 未使用 |
| `multimodal/` | 未使用 |
| `preloaded/` | 未使用 |
| `speech/` | 未使用 |

---

## ✅ **保留的目录** (4个)

| 目录 | 大小 | 用途 | 状态 |
|------|------|------|------|
| **intent_recognition/** | 120MB | 意图识别 | ✅ 正在使用 |
| **roberta-base-finetuned-chinanews-chinese/** | 390MB | NER命名实体识别 | ✅ 正在使用 |
| **custom/** | 小 | 自定义模型 | ✅ 保留 |
| **invalidation_prediction/** | 小 | 无效预测 | ⚠️ 待确认 |

---

## 🔍 **BGE-M3模型使用方式**

### 当前架构

```
应用代码
    ↓
HTTP API调用
    ↓
localhost:8766 (BGE-M3嵌入服务)
    ↓
返回1024维向量
```

### 配置文件

**ollama.yaml**:
```yaml
# Embedding: http://127.0.0.1:8766/v1 (BGE-M3 MLX 4bit, 1024维)
service_url: "http://127.0.0.1:8766"
```

**mlx.yaml**:
```yaml
# Embedding: http://127.0.0.1:8766/v1 (BGE-M3 MLX 4bit, 1024维)
service_url: "http://127.0.0.1:8766"
```

### 代码引用

**core/tools/vector_search_handler.py**:
```python
api_url = "http://127.0.0.1:8766/v1/embeddings"
```

**core/llm/adapters/mlx_adapter.py**:
```python
MLX_EMBEDDING_BASE_URL = "http://127.0.0.1:8766"
```

### 未来迁移

**目标端口**: 8009

**配置**: 已在 `config/llm_model_registry.json` 中配置

---

## ⚠️ **后续优化建议**

### 1. 端口迁移准备

**当前**: 8766端口  
**未来**: 8009端口

**建议**: 创建配置别名或环境变量

```python
# 建议修改为配置化
BGE_M3_SERVICE_URL = os.getenv(
    "BGE_M3_SERVICE_URL",
    "http://127.0.0.1:8766"  # 当前
    # "http://127.0.0.1:8009"  # 未来
)
```

### 2. 清理硬编码路径

**问题代码** (40处):
```python
# 不存在的本地路径
model_path = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3/"
```

**修复建议**:
```python
# 使用API服务
BGE_M3_API_URL = "http://127.0.0.1:8766/v1/embeddings"
```

### 3. 检查invalidation_prediction目录

**建议**: 检查是否使用，未使用可删除

```bash
# 检查使用情况
grep -r "invalidation_prediction" core/ --include="*.py"
```

---

## 📝 **总结**

### 清理成果

- ✅ 删除7个未使用的目录
- ✅ 保留2个正在使用的模型
- ✅ 目录大小从511MB减少到510MB
- ✅ 目录结构更清晰

### BGE-M3模型

- ✅ **不使用本地文件**
- ✅ **使用8766端口API服务**
- ✅ **未来迁移到8009端口**
- ⚠️ **代码中有硬编码路径需要修复**

### 保留的模型

1. **intent_recognition** (120MB) - 意图识别
2. **roberta-base-finetuned-chinanews-chinese** (390MB) - NER
3. **custom/** - 自定义模型

---

**清理完成时间**: 2026-04-21  
**清理脚本**: `scripts/cleanup_models_final.sh`  
**models目录大小**: 510MB  
**保留模型**: 2个正在使用 + 1个自定义
