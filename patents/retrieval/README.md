# 专利混合检索基线系统

## 📋 项目概述

本项目实现了一个专利混合检索基线系统，整合了三种检索策略：
1. **BM25全文搜索** - 基于关键词匹配的传统检索
2. **向量语义检索** - 基于embedding的语义相似度检索
3. **知识图谱增强** - 利用专利关联关系的图检索

## 🏗️ 系统架构

### 核心组件

```
专利混合检索系统
├── fulltext_adapter.py     # PostgreSQL全文搜索适配器（BM25实现）
├── simple_hybrid_retrieval_demo.py  # 简化版演示系统
├── patent_hybrid_retrieval.py       # 完整版检索系统
└── README.md              # 本文档
```

### 技术栈

基于Athena平台现有技术栈：
- **PostgreSQL** - 全文搜索和专利数据存储
- **Qdrant** - 向量数据库（使用现有adapter）
- **Neo4j** - 知识图谱（使用现有manager）
- **Python** - 核心开发语言

## 🚀 快速开始

### 运行演示

```bash
# 简化版演示（独立运行）
python3 patent_hybrid_retrieval/simple_hybrid_retrieval_demo.py
```

### 检索流程

1. **查询输入** - 用户输入查询文本
2. **多路检索** - 并行执行三种检索策略
3. **结果融合** - 加权合并检索结果
4. **排序输出** - 返回Top-K最相关专利

## 📊 检索策略对比

| 策略 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| BM25全文搜索 | 精确匹配、速度快 | 无法理解语义 | 关键词明确查询 |
| 向量语义检索 | 语义理解强 | 计算资源消耗大 | 概念性查询 |
| 知识图谱 | 关系推理、可解释 | 构建成本高 | 复杂关联查询 |
| **混合检索** | **综合优势** | **系统复杂** | **推荐使用** |

## 🎯 性能指标

### 检索权重配置
```python
weights = {
    'fulltext': 0.4,  # PostgreSQL全文搜索权重
    'vector': 0.5,    # Qdrant向量检索权重
    'keyword': 0.1    # 关键词匹配权重
}
```

### 预期效果
- **召回率**: 95%+ (通过多策略覆盖)
- **精确度**: 85%+ (通过融合排序)
- **响应时间**: <500ms (并行检索)

## 📈 优化建议

### 短期优化（1-3个月）
1. **提升中文分词精度**
   - 集成jieba或pkuseg专业分词工具
   - 构建专利领域专用词典

2. **增强向量表示**
   - 使用预训练的中文BERT模型
   - 在专利语料上微调embedding

3. **优化BM25参数**
   - 调整k1和b参数适应专利文本
   - 实现动态参数调整

### 中期优化（3-6个月）
1. **构建知识图谱**
   - 完整的专利引用关系
   - IPC/CPC分类层次
   - 技术术语关联

2. **学习排序（Learning to Rank）**
   - 收集用户点击数据
   - 训练排序模型
   - 实现个性化权重

3. **查询理解增强**
   - 意图识别
   - 查询扩展
   - 错误纠正

## 🔧 开发指南

### 添加新的检索策略

```python
def custom_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
    # 实现自定义检索逻辑
    results = []
    # ... 检索实现 ...
    return results

# 在_search方法中添加
custom_results = self.custom_search(query, top_k * 2)
```

### 调整融合权重

```python
# 修改权重配置
self.weights = {
    'bm25': 0.3,      # 降低BM25权重
    'vector': 0.6,    # 提高向量权重
    'keyword': 0.1
}
```

## 📚 参考资料

### 核心论文
- **BM25**: "Probabilistic Relevance Framework" - Robertson & Walker
- **DPR**: "Dense Passage Retrieval for Open-Domain QA" - Karpukhin et al.
- **ColBERT**: "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction"

### 相关项目
- **Elasticsearch**: 开源搜索引擎，支持全文检索
- **FAISS**: Facebook的向量相似度搜索库
- **Anserini**: 信息检索研究工具包

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境
- Python 3.8+
- PostgreSQL 12+
- 推荐使用虚拟环境

### 代码规范
- 遵循PEP 8
- 添加类型注解
- 编写单元测试

## 📄 许可证

MIT License

---

*最后更新: 2025-12-12*