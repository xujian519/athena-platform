# Patent Platform - 专利分析平台

> 🔬 基于知识图谱和向量数据库的智能专利分析系统

---

## 🎯 系统概述

**Patent Platform** 是Athena平台的独立专利分析应用，提供基于AI的专利技术分析、IPC分类、相似度搜索等功能。

### 核心特性

- ✅ **知识图谱增强分析** - 结合技术知识图谱进行深度分析
- ✅ **向量相似度搜索** - 基于语义向量的专利检索
- ✅ **IPC自动分类** - 智能国际专利分类号识别
- ✅ **技术特征提取** - 自动提取专利技术特征点
- ✅ **创新性评估** - 多维度评估专利创新水平
- ✅ **RESTful API** - 完整的REST API接口

---

## 📁 目录结构

```
patent-platform/
└── workspace/
    ├── analysis_reports/    # 分析报告输出目录
    ├── data/               # 数据存储（向量库、知识图谱）
    └── src/
        ├── api/
        │   └── patent_analysis_api.py  # FastAPI服务 (440行)
        └── perception/
            ├── integrated_patent_analysis_system.py
            ├── advanced_technical_knowledge_graph.py
            ├── enhanced_vector_database.py
            ├── ipc_classification_system.py
            └── knowledge_enhanced_patent_analyzer.py
```

---

## 🚀 快速启动

### 方式1: 直接运行Python

```bash
cd /Users/xujian/Athena工作平台/apps/patent-platform/workspace/src/api

# 安装依赖（首次运行）
pip install fastapi uvicorn pydantic

# 启动服务
python patent_analysis_api.py
```

**服务地址**:
- API文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API根: http://localhost:8000

### 方式2: 使用Uvicorn启动

```bash
cd /Users/xujian/Athena工作平台

# 指定模块启动
uvicorn apps.patent-platform.workspace.src.api.patent_analysis_api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

### 方式3: 后台运行（生产模式）

```bash
# 使用nohup后台运行
nohup python apps/patent-platform/workspace/src/api/patent_analysis_api.py > logs/patent-api.log 2>&1 &

# 记录PID
echo $! > logs/patent-api.pid

# 查看日志
tail -f logs/patent-api.log
```

---

## 📡 API接口

### 核心端点

| 端点 | 方法 | 功能 |
|-----|------|------|
| `/` | GET | 服务信息 |
| `/api/v1/health` | GET | 健康检查 |
| `/api/v1/patent/analyze` | POST | 专利分析 |
| `/api/v1/patent/extract-features` | POST | 特征提取 |
| `/api/v1/search/similarity` | POST | 相似度搜索 |
| `/api/v1/search/tech-terms` | POST | 技术术语搜索 |
| `/api/v1/ipc/classify` | POST | IPC分类 |
| `/api/v1/kg/statistics` | GET | 知识图谱统计 |
| `/api/v1/vector/statistics` | GET | 向量库统计 |

### 使用示例

#### 1. 专利分析

```bash
curl -X POST "http://localhost:8000/api/v1/patent/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "patent_id": "CN123456789A",
    "title": "一种智能机器人控制系统",
    "abstract": "本发明涉及机器人控制技术领域...",
    "claims": ["1. 一种智能机器人控制系统，其特征在于..."]
  }'
```

#### 2. 相似度搜索

```bash
curl -X POST "http://localhost:8000/api/v1/search/similarity" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "机器人路径规划算法",
    "top_k": 10,
    "search_type": "semantic"
  }'
```

#### 3. IPC分类

```bash
curl -X POST "http://localhost:8000/api/v1/ipc/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "patent_text": "权利要求书内容...",
    "title": "专利标题",
    "abstract": "摘要内容"
  }'
```

---

## 🔧 配置说明

### 环境变量

```bash
# 可选：配置日志路径
export PATENT_API_LOG_PATH="/Users/xujian/Athena工作平台/logs"

# 可选：配置数据目录
export PATENT_DATA_DIR="/Users/xujian/Athena工作平台/apps/patent-platform/workspace/data"
```

### 依赖服务

系统依赖以下核心模块（从 `core/` 导入）:

- `core.perception.advanced_technical_knowledge_graph` - 技术知识图谱
- `core.perception.enhanced_vector_database` - 向量数据库
- `core.perception.ipc_classification_system` - IPC分类系统
- `core.perception.knowledge_enhanced_patent_analyzer` - 知识增强分析器

---

## 📊 输出格式

### 专利分析响应示例

```json
{
  "patent_id": "CN123456789A",
  "ipc_classifications": [
    {
      "code": "G05D1/00",
      "name": "船舶或类似的水上运载...",
      "confidence": 0.95
    }
  ],
  "technical_features": [
    {
      "claim_number": 1,
      "text": "包括传感器模块...",
      "type": "device",
      "importance": "high"
    }
  ],
  "knowledge_graph_analysis": {
    "matched_entities": 15,
    "related_entities": 42,
    "kg_confidence_score": 0.87
  },
  "innovation_insights": [
    "结合了深度学习与传统控制算法",
    "多传感器融合技术具有创新性"
  ],
  "scores": {
    "novelty": 7.5,
    "clarity": 8.2,
    "completeness": 7.8,
    "technical_strength": 7.0
  }
}
```

---

## 🛠️ 开发指南

### 添加新的分析功能

1. 在 `src/perception/` 中创建新的分析器模块
2. 在 `patent_analysis_api.py` 中注册新的API端点
3. 更新本文档的API接口列表

### 修改向量数据库配置

编辑 `src/perception/enhanced_vector_database.py`:
```python
# 修改向量维度
VECTOR_DIM = 768  # BGE-M3默认维度

# 修改相似度阈值
SIMILARITY_THRESHOLD = 0.75
```

---

## 🔍 故障排查

### 常见问题

**Q: 启动时提示模块导入失败**
```bash
# 确保PYTHONPATH包含项目根目录
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH
```

**Q: 知识图谱加载缓慢**
- 首次启动需要加载知识图谱数据，请耐心等待
- 可在日志中查看 "知识图谱加载完成" 确认

**Q: API返回500错误**
- 检查日志文件: `tail -f logs/api.log`
- 确认依赖服务正常运行

---

## 📈 性能指标

| 指标 | 目标值 | 当前值 |
|-----|--------|--------|
| 分析响应时间 | <3秒 | ~2.5秒 |
| IPC分类准确率 | >85% | ~88% |
| 向量检索延迟 | <500ms | ~420ms |
| 并发支持 | 10 QPS | ~8 QPS |

---

## 🔗 相关文档

- [知识图谱系统](../../core/knowledge_graph/README.md)
- [向量数据库](../../core/embedding/README.md)
- [小娜智能体](../../core/agents/xiaona/README.md)

---

## 📝 更新日志

### v1.0.0 (2025-12-05)
- ✅ 初始版本发布
- ✅ 实现核心分析功能
- ✅ 集成知识图谱和向量数据库
- ✅ 提供完整的REST API

---

**维护者**: 徐健 (xujian519@gmail.com)
**创建时间**: 2025-12-05
**文档更新**: 2026-04-22
**端口**: 8000
**状态**: ✅ 生产就绪
