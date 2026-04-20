# semantic_analysis工具使用指南

> **工具名称**: 文本语义分析 (semantic_analysis)
> **版本**: v1.0.0
> **创建日期**: 2026-04-19

---

## 快速开始

### 1. 获取工具

```python
from core.tools.unified_registry import get_unified_registry

# 获取工具注册表
registry = get_unified_registry()

# 获取semantic_analysis工具
tool = registry.get("semantic_analysis")
```

### 2. 基础使用

#### 计算文本相似度

```python
result = tool.function(
    action="calculate_similarity",
    text1="帮我写个故事",
    text2="创作文案内容"
)

print(f"相似度: {result['similarity']:.4f}")
# 输出: 相似度: 0.7234

print(f"解释: {result['interpretation']}")
# 输出: 解释: 相似 - 语义较为相关
```

#### 意图识别

```python
result = tool.function(
    action="find_best_intent",
    text1="检索人工智能相关专利",
    intent_examples={
        "patent_search": ["检索专利", "搜索专利"],
        "creative_writing": ["写故事", "创作文案"]
    },
    train_model=True  # 重新训练模型
)

print(f"最佳意图: {result['best_intent']}")
# 输出: 最佳意图: patent_search

print(f"置信度: {result['confidence']:.4f}")
# 输出: 置信度: 0.8156
```

#### 意图排序

```python
result = tool.function(
    action="rank_intents",
    text1="帮我写个故事",
    top_k=3
)

print("意图排序结果:")
for i, item in enumerate(result['ranked_intents'], 1):
    print(f"{i}. {item['intent']}: {item['score']:.4f}")
```

---

## 完整API参考

### action参数说明

#### 1. calculate_similarity - 计算文本相似度

**参数**:
- `action` (必需): "calculate_similarity"
- `text1` (必需): 第一个文本
- `text2` (必需): 第二个文本

**返回**:
```python
{
    "status": "success",
    "action": "calculate_similarity",
    "similarity": 0.7234,  # 相似度分数 (0-1)
    "text1": "帮我写个故事",
    "text2": "创作文案内容",
    "interpretation": "相似 - 语义较为相关"  # 解释文本
}
```

**示例**:
```python
result = tool.function(
    action="calculate_similarity",
    text1="专利检索",
    text2="搜索专利"
)
```

---

#### 2. find_best_intent - 意图识别

**参数**:
- `action` (必需): "find_best_intent"
- `text1` (必需): 待识别的文本
- `intent_examples` (可选): 意图示例字典
  ```python
  {
      "intent_type": ["example1", "example2", ...]
  }
  ```
- `train_model` (可选): 是否重新训练模型 (默认: False)

**返回**:
```python
{
    "status": "success",
    "action": "find_best_intent",
    "text": "检索人工智能相关专利",
    "best_intent": "patent_search",  # 最佳匹配意图
    "confidence": 0.8156,  # 置信度 (0-1)
    "interpretation": "高置信度 - 匹配结果非常可靠",
    "available_intents": ["patent_search", "creative_writing", ...]
}
```

**示例**:
```python
result = tool.function(
    action="find_best_intent",
    text1="检索人工智能相关专利",
    intent_examples={
        "patent_search": ["检索专利", "搜索专利", "查找专利"],
        "creative_writing": ["写故事", "创作文案", "生成内容"],
        "data_analysis": ["分析数据", "统计结果", "数据可视化"]
    },
    train_model=True
)
```

---

#### 3. rank_intents - 意图排序

**参数**:
- `action` (必需): "rank_intents"
- `text1` (必需): 待匹配的文本
- `intent_examples` (可选): 意图示例字典
- `top_k` (可选): 返回前K个结果 (默认: 5)

**返回**:
```python
{
    "status": "success",
    "action": "rank_intents",
    "text": "帮我写个故事",
    "ranked_intents": [
        {"intent": "creative_writing", "score": 0.7234},
        {"intent": "code_generation", "score": 0.5123},
        {"intent": "explanation_query", "score": 0.3891}
    ],
    "total_intents": 9  # 总意图数
}
```

**示例**:
```python
result = tool.function(
    action="rank_intents",
    text1="帮我写个故事",
    top_k=3
)
```

---

#### 4. add_examples - 添加意图示例

**参数**:
- `action` (必需): "add_examples"
- `intent_examples` (必需): 意图示例字典

**返回**:
```python
{
    "status": "success",
    "action": "add_examples",
    "added_intents": ["patent_analysis", "legal_advice"],
    "message": "意图示例已添加，使用train_model=True重新训练模型"
}
```

**示例**:
```python
result = tool.function(
    action="add_examples",
    intent_examples={
        "patent_analysis": ["分析专利创造性", "评估专利新颖性"],
        "legal_advice": ["提供法律建议", "法律咨询"]
    }
)
```

---

#### 5. train_model - 训练模型

**参数**:
- `action` (必需): "train_model"

**返回**:
```python
{
    "status": "success",
    "action": "train_model",
    "message": "语义模型训练完成",
    "total_intents": 9,
    "is_trained": True
}
```

**示例**:
```python
result = tool.function(
    action="train_model"
)
```

---

## 便捷函数

工具提供了两个便捷函数，简化常见操作：

### calculate_text_similarity

计算两个文本的语义相似度。

```python
from core.tools.semantic_analysis_handler import calculate_text_similarity

similarity = calculate_text_similarity("文本1", "文本2")
print(f"相似度: {similarity:.4f}")
```

### find_text_intent

识别文本的意图。

```python
from core.tools.semantic_analysis_handler import find_text_intent

intent, confidence = find_text_intent(
    "检索人工智能专利",
    intent_examples={
        "patent_search": ["检索专利", "搜索专利"],
        "creative_writing": ["写故事", "创作文案"]
    }
)
print(f"意图: {intent}, 置信度: {confidence:.4f}")
```

---

## 使用场景

### 场景1: 用户意图识别

```python
# 用户输入
user_input = "帮我检索人工智能相关的专利"

# 识别意图
result = tool.function(
    action="find_best_intent",
    text1=user_input,
    intent_examples={
        "patent_search": ["检索专利", "搜索专利", "查找专利"],
        "patent_analysis": ["分析专利", "评估创造性"],
        "patent_drafting": ["撰写专利", "写专利申请"]
    },
    train_model=True
)

# 根据意图执行相应操作
if result['best_intent'] == 'patent_search':
    print("执行专利检索...")
elif result['best_intent'] == 'patent_analysis':
    print("执行专利分析...")
elif result['best_intent'] == 'patent_drafting':
    print("执行专利撰写...")
```

### 场景2: 文本相似度匹配

```python
# 比对两个专利文本的相似度
patent1_abstract = "一种基于深度学习的图像识别方法..."
patent2_abstract = "使用神经网络进行图像识别的技术..."

result = tool.function(
    action="calculate_similarity",
    text1=patent1_abstract,
    text2=patent2_abstract
)

if result['similarity'] > 0.7:
    print("⚠️ 两个专利高度相似，可能存在冲突")
else:
    print("✅ 两个专利差异较大")
```

### 场景3: 语义搜索重排序

```python
# 初始搜索结果（基于关键词）
search_results = [
    {"doc_id": 1, "title": "专利检索方法", "score": 0.8},
    {"doc_id": 2, "title": "写故事技巧", "score": 0.7},
    {"doc_id": 3, "title": "专利分析指南", "score": 0.6}
]

# 用户查询
query = "检索专利"

# 使用语义相似度重排序
for result in search_results:
    semantic_score = tool.function(
        action="calculate_similarity",
        text1=query,
        text2=result['title']
    )['similarity']

    # 综合关键词分数和语义分数
    result['final_score'] = 0.6 * result['score'] + 0.4 * semantic_score

# 按最终分数重新排序
search_results.sort(key=lambda x: x['final_score'], reverse=True)

print("重排序后的结果:")
for i, result in enumerate(search_results, 1):
    print(f"{i}. {result['title']} (分数: {result['final_score']:.4f})")
```

### 场景4: 自定义意图训练

```python
# 添加自定义意图示例
custom_intents = {
    "patent_invalidity": [
        "专利无效宣告",
        "请求宣告专利无效",
        "专利无效分析"
    ],
    "patent_infringement": [
        "专利侵权分析",
        "产品是否侵权",
        "侵权风险评估"
    ],
    "patent_transaction": [
        "专利转让",
        "专利许可",
        "专利价值评估"
    ]
}

# 批量添加
for intent_name, examples in custom_intents.items():
    result = tool.function(
        action="add_examples",
        intent_examples={intent_name: examples}
    )
    print(f"✅ 添加意图: {intent_name}")

# 重新训练模型
result = tool.function(
    action="train_model"
)
print(f"✅ {result['message']}")

# 测试新意图
test_query = "分析这个产品是否侵权"
result = tool.function(
    action="find_best_intent",
    text1=test_query
)
print(f"查询: {test_query}")
print(f"识别意图: {result['best_intent']}")
print(f"置信度: {result['confidence']:.4f}")
```

---

## 错误处理

### 常见错误

#### 1. 缺少必需参数

```python
result = tool.function(
    action="calculate_similarity",
    text1="只有一个文本"
    # 缺少text2参数
)

# 返回
{
    "status": "error",
    "error": "text1和text2参数不能为空",
    "code": "MISSING_PARAMS"
}
```

#### 2. 未知的操作类型

```python
result = tool.function(
    action="unknown_action"
)

# 返回
{
    "status": "error",
    "error": "未知的操作类型: unknown_action",
    "code": "UNKNOWN_ACTION",
    "supported_actions": [
        "calculate_similarity",
        "find_best_intent",
        "rank_intents",
        "add_examples",
        "train_model"
    ]
}
```

#### 3. 没有可用的意图

```python
result = tool.function(
    action="find_best_intent",
    text1="检索专利"
    # 没有提供intent_examples，且模型未训练

# 返回
{
    "status": "error",
    "error": "没有可用的意图类型，请先添加意图示例",
    "code": "NO_INTENTS"
}
```

### 错误处理最佳实践

```python
def safe_semantic_analysis(action, **kwargs):
    """带错误处理的语义分析"""

    try:
        result = tool.function(action=action, **kwargs)

        if result['status'] == 'success':
            return result
        else:
            # 处理业务错误
            print(f"❌ 错误: {result.get('error')}")
            print(f"📋 错误代码: {result.get('code')}")
            return None

    except Exception as e:
        # 处理系统异常
        print(f"❌ 系统异常: {e}")
        return None

# 使用示例
result = safe_semantic_analysis(
    action="calculate_similarity",
    text1="文本1",
    text2="文本2"
)

if result:
    print(f"相似度: {result['similarity']:.4f}")
```

---

## 性能优化建议

### 1. 减少模型训练次数

```python
# ❌ 不好的做法：每次都训练
for query in queries:
    result = tool.function(
        action="find_best_intent",
        text1=query,
        train_model=True  # 每次都训练
    )

# ✅ 好的做法：只训练一次
# 先添加所有示例
for intent, examples in intent_dict.items():
    tool.function(
        action="add_examples",
        intent_examples={intent: examples}
    )

# 统一训练一次
tool.function(action="train_model")

# 然后使用
for query in queries:
    result = tool.function(
        action="find_best_intent",
        text1=query
        # 不需要train_model
    )
```

### 2. 使用便捷函数

```python
# ✅ 使用便捷函数（更简洁、更快）
from core.tools.semantic_analysis_handler import calculate_text_similarity

similarity = calculate_text_similarity("文本1", "文本2")

# 而不是
result = tool.function(
    action="calculate_similarity",
    text1="文本1",
    text2="文本2"
)
similarity = result['similarity']
```

### 3. 批量处理

```python
# ✅ 批量计算相似度（向量化操作）
texts = ["文本1", "文本2", "文本3"]
query = "查询文本"

similarities = [
    calculate_text_similarity(query, text)
    for text in texts
]

# 找到最相似的
best_match = max(zip(texts, similarities), key=lambda x: x[1])
print(f"最佳匹配: {best_match[0]} (相似度: {best_match[1]:.4f})")
```

---

## 技术细节

### 算法原理

1. **文本预处理**: 使用jieba分词进行中文分词
2. **向量化**: TF-IDF（max_features=3000, ngram_range=(1,2)）
3. **相似度计算**: 余弦相似度
4. **优化**: 避免SVD数值不稳定问题

### 性能指标

| 操作 | 平均耗时 |
|-----|---------|
| calculate_similarity | ~50ms |
| find_best_intent | ~100ms |
| rank_intents | ~80ms |
| train_model | ~200ms |

### 资源占用

- **内存**: ~50MB
- **CPU**: 低（单线程）
- **磁盘**: ~5MB（模型缓存）

---

## 常见问题 (FAQ)

### Q1: 如何提高意图识别准确率？

**A**: 添加更多相关的训练示例：

```python
tool.function(
    action="add_examples",
    intent_examples={
        "patent_search": [
            "检索专利",
            "搜索专利",
            "查找专利",
            "专利检索",
            "现有技术搜索",
            "专利数据库检索"  # 更多示例
        ]
    }
)
tool.function(action="train_model")
```

### Q2: 支持英文文本吗？

**A**: 当前版本主要优化中文，但也可以处理英文文本。建议为英文添加专门的意图示例。

### Q3: 如何持久化训练的模型？

**A**: 当前版本模型在内存中，重启后需要重新训练。如需持久化，可以保存intent_examples到文件：

```python
import json

# 保存
with open("intent_examples.json", "w") as f:
    json.dump(intent_examples, f)

# 加载
with open("intent_examples.json") as f:
    intent_examples = json.load(f)

tool.function(
    action="add_examples",
    intent_examples=intent_examples
)
tool.function(action="train_model")
```

### Q4: 相似度阈值如何设置？

**A**: 根据场景调整：

- **高精度场景**: threshold ≥ 0.7
- **一般场景**: threshold ≥ 0.5
- **召回优先**: threshold ≥ 0.3

---

## 更新日志

### v1.0.0 (2026-04-19)

- ✅ 初始版本发布
- ✅ 支持5种操作类型
- ✅ 基于StableSemanticSimilarity实现
- ✅ 完整的错误处理和日志记录
- ✅ 提供便捷函数

---

## 相关文档

- [验证报告](./docs/reports/SEMANTIC_ANALYSIS_TOOL_VERIFICATION_REPORT_20260419.md)
- [工具系统API文档](./docs/api/UNIFIED_TOOL_REGISTRY_API.md)
- [NLP模块文档](./core/nlp/)

---

**维护者**: Athena平台团队
**最后更新**: 2026-04-19
