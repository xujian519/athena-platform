# 统一知识图谱服务

## 概述

本服务整合了三个核心知识图谱，为项目所有专利应用提供动态提示词和规则提取服务：

1. **SQLite专利知识图谱** (2.8GB) - 大规模专利案例知识
2. **专利法律法规知识图谱** - 法律条文和规定
3. **审查指南向量数据库** - 审查标准和指引

## 核心功能

### 1. 动态提示词生成
- 根据用户查询和专利内容生成上下文感知的提示词
- 整合多源知识，提供专业的指导
- 支持多种应用场景（审查、法律咨询、技术分析等）

### 2. 智能规则提取
- 从知识图谱中提取相关规则
- 按类别组织（新颖性、创造性、程序性等）
- 去重和优先级排序

### 3. 意图识别
- 自动识别用户查询意图
- 提供针对性的响应
- 建议后续操作

## 使用方法

### 基础使用

```python
from integrated_patent_service import get_integrated_patent_service

# 获取服务实例
service = await get_integrated_patent_service()

# 处理查询
response = await service.process_patent_query(
    query="这个专利是否具有新颖性？",
    patent_text="本发明涉及一种新材料的制备方法...",
    context_type="patent_review"
)

# 获取生成的提示词
prompts = response['prompts']
print(prompts['system_role'])
print(prompts['knowledge_guidance'])
```

### 高级功能

```python
# 批量处理
queries = [
    {"query": "如何判断创造性？", "patent_text": "..."},
    {"query": "侵权风险分析", "patent_text": "..."}
]
results = await service.batch_process_queries(queries)

# 获取服务统计
stats = await service.get_service_statistics()

# 导出知识洞察
insights = await service.export_knowledge_insights()
```

## 服务架构

```
用户查询
    ↓
意图识别
    ↓
动态提示词管理器
    ↓
统一知识图谱服务
    ├── SQLite知识图谱 (125万+实体)
    ├── 法律知识图谱 (45个实体)
    └── 审查指南向量库 (53个向量)
    ↓
生成上下文感知的提示词
    ↓
返回专业响应
```

## 支持的查询类型

1. **专利审查** (patent_review)
   - 新颖性/创造性/实用性判断
   - 审查意见生成
   - 申请文件评估

2. **法律咨询** (legal_advice)
   - 侵权风险评估
   - 维权策略建议
   - 法律依据提供

3. **技术分析** (technical_analysis)
   - 创新点识别
   - 技术可行性分析
   - 与现有技术对比

4. **专利检索** (patent_search)
   - 相似专利查找
   - 现有技术检索
   - 分类号查询

5. **专利申请** (patent_filing)
   - 申请流程指导
   - 文件准备建议
   - 程序性事项

## 知识图谱详情

### SQLite专利知识图谱
- **路径**: `/data/knowledge_graph_sqlite/databases/patent_knowledge_graph.db`
- **规模**: 2.8GB, 125万+实体, 329万+关系
- **内容**: 大规模专利案例、法律条款、程序规定
- **特点**: 最全面的专利知识库

### 法律法规知识图谱
- **路径**: `/data/patent_legal_kg_simple/`
- **规模**: 45个实体, 202个关系
- **内容**: 专利法、实施细则、条例、概念
- **特点**: 结构化法律知识

### 审查指南向量数据库
- **集合**: `patent_guideline` (Qdrant)
- **规模**: 53个向量, 768维
- **内容**: 审查指南、操作规程
- **特点**: 语义检索支持

## 缓存机制

- 提示词缓存1小时
- 规则提取结果缓存
- 会话历史保存

## 性能优化

1. **分层查询**
   - 先从缓存查找
   - 并行查询多个知识源
   - 结果去重和排序

2. **智能缓存**
   - 基于查询特征的缓存策略
   - LRU淘汰机制

3. **异步处理**
   - 非阻塞的知识图谱查询
   - 批量操作优化

## 扩展性

1. **新增知识源**
   - 实现统一接口
   - 注册到服务中

2. **自定义提示词模板**
   - 修改 `prompt_templates.json`
   - 支持变量替换

3. **新查询类型**
   - 扩展意图分类器
   - 添加处理逻辑

## 监控和维护

- 查询统计和性能监控
- 知识源健康检查
- 缓存效率分析

## API文档

详细API文档请参考 `api_documentation.md`