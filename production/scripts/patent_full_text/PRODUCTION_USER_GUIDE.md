# 📖 专利全文处理系统 - 生产环境使用指南

**版本**: Phase 2 (生产环境稳定版)
**更新时间**: 2025-12-25
**状态**: ✅ 已验证可用

---

## 🎯 系统概述

专利全文处理系统提供完整的专利PDF处理流程，包括：
- PDF文本提取（支持OCR）
- 专利向量化（BGE中文模型）
- 三元组提取
- 知识图谱构建
- 向量数据库存储

---

## 📁 目录结构

```
/Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text/
├── vectorize_with_local_bge.py      # ✅ 推荐：向量化+知识图谱（本地BGE）
├── vectorize_save_vectors.py        # ✅ 向量化并保存向量
├── vectorize_and_build_kg.py        # ✅ 向量化并构建知识图谱
├── batch_process_patents.py         # ✅ 批量处理PDF（集成OCR）
├── build_patent_kg.py               # ✅ 构建知识图谱
├── extract_triples.py               # ✅ 提取三元组
├── smart_ocr_router.py              # OCR路由器
├── integrated_downloader.py         # 专利PDF下载器
└── phase3/                          # ⚠️ 开发中，请勿使用
    └── DEVELOPMENT_WARNING.md
```

---

## 🚀 快速开始

### 1. 向量化处理专利（推荐）

使用本地BGE模型进行专利向量化和知识图谱构建：

```bash
cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text
python3 vectorize_with_local_bge.py
```

**功能**:
- ✅ 使用本地BGE模型 (`/Users/xujian/Athena工作平台/models/bge-base-zh-v1.5`)
- ✅ 向量化专利全文
- ✅ 构建知识图谱
- ✅ 保存到Qdrant和NebulaGraph

---

### 2. 批量处理专利PDF

处理指定目录下的所有专利PDF文件：

```bash
cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text
python3 batch_process_patents.py
```

**功能**:
- ✅ 自动扫描 `/Users/xujian/apps/apps/patents/PDF/` 目录
- ✅ 智能OCR路由（自动选择最佳提取方式）
- ✅ 支持扫描版PDF
- ✅ 保存处理结果为JSON

**输入目录**: `/Users/xujian/apps/apps/patents/PDF/`
**输出目录**: `/Users/xujian/Athena工作平台/apps/apps/patents/processed/`

---

### 3. 单独构建知识图谱

如果已有向量数据，单独构建知识图谱：

```bash
cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text
python3 build_patent_kg.py
```

---

### 4. 提取三元组

从专利文本中提取技术问题-特征-效果三元组：

```bash
cd /Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text
python3 extract_triples.py
```

---

## 📊 数据库配置

### Qdrant向量数据库
- **地址**: `localhost:6333`
- **集合**: `patent_full_text`
- **向量维度**: 768 (BGE-base-zh-v1.5)
- **距离度量**: Cosine

### NebulaGraph图数据库
- **地址**: `127.0.0.1:9669`
- **空间**: `patent_kg`
- **用户**: `root`
- **密码**: `nebula`

---

## 🔧 本地BGE模型

### 模型信息
- **模型**: BAAI/bge-m3
- **路径**: `/Users/xujian/Athena工作平台/models/bge-base-zh-v1.5`
- **大小**: ~390MB
- **向量维度**: 768
- **设备**: MPS (Apple Silicon GPU加速)

### 模型加载
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    '/Users/xujian/Athena工作平台/models/bge-base-zh-v1.5',
    device='mps'  # Apple Silicon GPU加速
)

# 向量化
embedding = model.encode("专利文本")
```

---

## 📝 处理流程

### 完整流程示例

```bash
# 1. 下载专利PDF（使用专利下载MCP）
# 2. 批量处理PDF（提取文本）
python3 batch_process_patents.py

# 3. 向量化+知识图谱构建
python3 vectorize_with_local_bge.py

# 4. 验证结果
# - 检查Qdrant: http://localhost:6333/dashboard
# - 检查NebulaGraph: 使用NebulaGraph Studio
```

---

## ✅ 成功记录

| 日期 | 专利数 | 状态 | 说明 |
|------|--------|------|------|
| 2025-12-25 | 7件 | ✅ 成功 | 王玉荣项目专利处理 |
| 2025-12-25 | 5件 | ✅ 成功 | 果树采摘设备专利 |

---

## ⚠️ 重要注意事项

### 请勿使用
- ❌ **Phase 3** 目录下的代码（开发中）
- ❌ 未经验证的新功能

### 推荐使用
- ✅ Phase 2目录下的所有脚本
- ✅ 本地BGE模型
- ✅ 已验证的处理流程

---

## 📞 问题反馈

如遇到问题，请检查：
1. BGE模型是否存在：`/Users/xujian/Athena工作平台/models/bge-base-zh-v1.5`
2. Docker服务是否运行：`docker ps | grep -E "qdrant|nebula"`
3. 日志文件：查看处理过程中的错误信息

---

**最后更新**: 2025-12-25
**维护者**: Athena平台团队
