# 本地模型配置指南

## 📋 概述

本文档说明如何在Athena工作平台中配置和使用本地模型，避免每次都从Huggingface在线下载。

## 🚀 快速开始

### 1. 使用配置好的启动脚本

```bash
# 使用本地模型启动
./start_with_local_models.sh
```

### 2. 手动配置环境变量

```bash
# 加载环境变量
source dev/scripts/setup_model_environment.sh

# 设置Python路径
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
```

## 📁 模型存储结构

```
/Users/xujian/Athena工作平台/models/
├── bge-large-zh-v1.5/                 # BGE中文大模型（1024维）
│   ├── config.json
│   ├── model.safetensors
│   ├── tokenizer.json
│   └── vocab.txt
├── bge-base-zh-v1.5/                  # BGE中文基础模型（768维）
│   └── snapshots/f03589ceff5aac7111bd60cfc7d497ca17ecac65/
│       ├── config.json
│       ├── pytorch_model.bin
│       └── ...
├── chinese-legal-electra/             # 中文法律模型
├── chinese_bert/                      # 中文BERT基础模型
└── .cache/                           # Huggingface缓存目录
```

## 🔧 配置文件

### 环境变量文件 (.env_models)

```bash
# 核心缓存目录
SENTENCE_TRANSFORMERS_HOME=/Users/xujian/Athena工作平台/models
HF_HOME=/Users/xujian/Athena工作平台/models
TRANSFORMERS_CACHE=/Users/xujian/Athena工作平台/models

# 离线模式设置
TRANSFORMERS_OFFLINE=1
HF_OFFLINE=1
```

### Python配置 (core/models/local_model_config.py)

本地模型配置管理器，提供以下功能：
- 自动设置环境变量
- 检查模型可用性
- 获取本地模型路径
- 离线模式配置

## 💻 使用示例

### 在代码中使用

```python
from core.models.local_model_config import model_config
from sentence_transformers import SentenceTransformer

# 获取本地模型路径
model_path = model_config.get_sentence_transformer_model("bge-large-zh-v1.5")

# 直接使用
model = SentenceTransformer(model_path)

# 或者通过模型管理器使用
from patent_hybrid_retrieval.chinese_bert_integration.model_manager import ChineseBERTModelManager
manager = ChineseBERTModelManager()
```

### 检查模型可用性

```python
# 列出所有可用模型
models = model_config.list_available_models()
for name, info in models.items():
    print(f"{name}: {'✅' if info['available'] else '❌'}")
```

## 🛠️ 已集成的模块

以下模块已配置使用本地模型：

1. **中文BERT模型管理器** (`modules/patent/patent_hybrid_retrieval/chinese_bert_integration/model_manager.py`)
2. **多模型向量器** (`modules/patent/patent_hybrid_retrieval/chinese_bert_integration/multi_model_vectorizer.py`)
3. **审查指南向量化器** (`patent_guideline_system/src/vectorization/embedder.py`)

## 📊 性能优势

使用本地模型的优势：

1. **🚀 启动速度**：无需下载，秒级加载
2. **💾 离线工作**：无需网络连接
3. **🔒 数据安全**：模型数据本地存储
4. **⚡ 稳定性**：不受Huggingface服务器影响

## 🔍 故障排除

### 1. 模型找不到

```bash
# 检查模型路径
ls -la /Users/xujian/Athena工作平台/models/bge-large-zh-v1.5/
```

### 2. 仍尝试在线下载

```python
# 检查环境变量
import os
print(f"TRANSFORMERS_OFFLINE: {os.environ.get('TRANSFORMERS_OFFLINE')}")
print(f"HF_OFFLINE: {os.environ.get('HF_OFFLINE')}")
```

### 3. 权限问题

```bash
# 确保模型目录可读
chmod -R 755 /Users/xujian/Athena工作平台/models/
```

## 📝 添加新模型

1. 将模型下载到 `/Users/xujian/Athena工作平台/models/`
2. 在 `local_model_config.py` 中添加路径映射
3. 更新相关模块的模型配置

## 🎯 最佳实践

1. **启动项目**：始终使用 `./start_with_local_models.sh`
2. **开发环境**：确保 `PYTHONPATH` 正确设置
3. **生产环境**：设置好所有环境变量
4. **模型管理**：使用 `model_config` 统一管理模型路径

---

## 📚 相关文档

- [中文BERT专业模型集成文档](./modules/patent/modules/patent/patent_hybrid_retrieval/chinese_bert_integration/README.md)
- [专利审查指南GraphRAG系统](./patent_guideline_system/README.md)
- [项目主文档](./README.md)