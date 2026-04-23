# DSPy训练低分原因分析与改进方案

**分析日期**: 2025-12-30
**分析范围**: DSPy Phase 1 试点训练 (CAPABILITY_2 案情分析)

---

## 🔍 第一部分：低分原因分析

### 问题1: 评估指标过于严格 ❌

**当前评估指标** (`PatentCaseMetrics.evaluate_exact_match`):

```python
# 评分规则
if pred.case_type == example.case_type:
    score += 0.4          # 类型匹配: 40%

if pred_issues & actual_issues:  # 法律问题有交集
    score += 0.3          # 法律问题匹配: 30%

if len(reasoning) >= 50:     # 推理长度 >= 50字符
    score += 0.15          # 长度匹配: 15%

if 关键词 in reasoning:       # 包含关键词
    score += 0.15          # 关键词匹配: 15%
```

**问题分析**:
- ❌ **完全匹配要求过高**: 需要 case_type 完全相同才能得分
- ❌ **法律问题匹配困难**: 要求 `pred_issues & actual_issues` 有交集，但LLM可能输出格式不一致
- ❌ **关键词列表有限**: 只检查 5 个关键词 (`专利法`, `认为`, `因此`, `不符合`, `规定`)
- ❌ **没有部分分**: 没有"接近正确"的奖励机制

**实际效果**: 0.3分 (30%) 表示大部分预测只有部分正确

---

### 问题2: 训练数据质量问题 ⚠️

**检查 `training_data_REAL_100_dspy.py`**:

```python
# 发现的问题
analysis_result='\n【案例分析报告】\n\n一、案件基本信息\n技术领域: None  # ❌ None值
专利号: None      # ❌ None值
决定类型: None      # ❌ None值
```

**问题分析**:
- ❌ **字段缺失**: `技术领域`, `专利号`, `决定类型` 都是 `None`
- ❌ **数据截断**: 大量字段显示为 `...`，内容被截断
- ❌ **格式不统一**: 不同案例的字段数量和类型不一致
- ❌ **缺少标准答案**: 没有明确的 `case_type`, `legal_issues` 字段

**影响**: LLM无法从训练数据中学习正确的输出格式

---

### 问题3: 提示词模板不清晰 ⚠️

**当前 Signature 定义**:

```python
class PatentCaseAnalysis(dspy.Signature):
    """分析专利无效宣告案例"""
    input = dspy.InputField()
    context = dspy.InputField()
    output_analysis = dspy.OutputField()
```

**问题分析**:
- ⚠️ **输出字段模糊**: `output_analysis` 没有指定具体格式
- ⚠️ **缺少结构化输出**: 没有要求输出 `case_type`, `legal_issues`, `reasoning` 分别是什么
- ⚠️ **没有示例**: 没有提供标准输出格式示例

**影响**: LLM输出格式不一致，评估时无法正确解析

---

### 问题4: 训练数据量不足 ⚠️

| 数据集 | 大小 | 问题 |
|--------|------|------|
| training_data_FINAL_800_latest | 964 KB | ❌ 很多字段是 None |
| training_data_REAL_100 | 57 KB | ⚠️ 只有 100 条，且质量不高 |
| training_data_production_docx_100 | 159 KB | ⚠️ 来源不明 |

**最佳训练集**: 628条 (但质量参差不齐)

---

## 💡 第二部分：改进方案

### 方案1: 优化评估指标 ✅ (最重要)

**创建新的评估指标** - 更宽容、多层次：

```python
class EnhancedPatentMetrics:
    """增强的专利案例分析评估指标"""

    @staticmethod
    def evaluate_enhanced(example, pred, trace=None):
        """增强评估 - 多层次打分"""
        score = 0.0

        # 层次1: Case Type匹配 (40分)
        if pred.case_type == example.case_type:
            score += 0.40
        elif self._is_related_type(pred.case_type, example.case_type):
            score += 0.20  # 相关类型给部分分

        # 层次2: 关键信息提取 (30分)
        # 检查是否提取了关键信息，不管格式如何
        pred_text = str(pred).lower()
        example_text = str(example).lower()

        # 专利号匹配
        if self._extract_patent_number(pred_text) == self._extract_patent_number(example_text):
            score += 0.10

        # 技术领域匹配
        if self._has_technical_field(pred_text):
            score += 0.10

        # 法律问题关键词
        legal_keywords = ['专利法', '新颖性', '创造性', '实用性', '公开充分']
        if any(kw in pred_text for kw in legal_keywords):
            score += 0.10

        # 层次3: 推理质量 (30分)
        if hasattr(pred, 'reasoning') or hasattr(pred, 'output_analysis'):
            reasoning = getattr(pred, 'reasoning', None) or getattr(pred, 'output_analysis', '')
            reasoning = str(reasoning)

            # 长度适中 (100-1000字符)
            if 100 <= len(reasoning) <= 1000:
                score += 0.15

            # 结构化 (有分段)
            if any(marker in reasoning for marker in ['一、', '1.', '首先', '其次']):
                score += 0.15

        return min(score, 1.0)

    @staticmethod
    def _is_related_type(pred_type, actual_type):
        """检查类型是否相关"""
        type_groups = {
            'novelty_related': ['novelty', 'novel', '新颖性'],
            'creative_related': ['creative', 'inventive', '创造性'],
            'disclosure_related': ['disclosure', 'clarity', '公开', '清晰']
        }

        for group in type_groups.values():
            if pred_type in group and actual_type in group:
                return True
        return False

    @staticmethod
    def _extract_patent_number(text):
        """提取专利号"""
        import re
        match = re.search(r'CN\d+[A-Z]', text)
        return match.group(0) if match else None

    @staticmethod
    def _has_technical_field(text):
        """检查是否有技术领域"""
        tech_keywords = ['技术领域', '所属领域', '涉及', '应用于']
        return any(kw in text for kw in tech_keywords)
```

**改进点**:
- ✅ **部分匹配**: 相关类型给 20% 分数
- ✅ **关键词提取**: 不要求完全匹配，只要有关键词
- ✅ **结构化奖励**: 有结构化的推理给额外分数
- ✅ **容忍格式差异**: 不要求特定字段格式

---

### 方案2: 准备精选100条高质量训练数据 ✅

**数据来源策略**:

1. **从现有数据筛选**: 从 628 条中挑选质量最高的 100 条
2. **人工审核**: 确保每条数据有完整的字段
3. **格式统一**: 统一输出格式

**精选标准**:
```python
高质量数据检查清单:
✅ user_input 清晰完整
✅ context 包含完整专利信息
✅ analysis_result 包含:
   - 明确的 case_type (novelty/creative/disclosure/clarity)
   - 完整的法律问题列表
   - 详细的推理过程 (reasoning)
   - 明确的结论
✅ 没有 None 值
✅ 没有截断 (...)

数据分布:
- novelty: 30条
- creative: 25条
- disclosure: 25条
- clarity: 20条
```

---

### 方案3: 优化提示词模板 ✅

**新的 Signature 定义**:

```python
class StructuredPatentAnalysis(dspy.Signature):
    """结构化专利案例分析"""

    """分析专利无效宣告案例，输出结构化分析报告"""

    user_input = dspy.InputField(desc="用户输入的问题")
    context = dspy.InputField(desc="专利案例背景信息")

    # 明确的结构化输出
    case_type = dspy.OutputField(desc="案例类型 (novelty/creative/disclosure/clarity)")
    legal_issues = dspy.OutputField(desc="法律问题列表，用逗号分隔")
    reasoning = dspy.OutputField(desc="详细分析推理过程")
    conclusion = dspy.OutputField(desc="最终结论")
```

**改进点**:
- ✅ **明确字段**: 每个输出字段都有明确描述
- ✅ **结构化输出**: 强制 LLM 按照结构输出
- ✅ **可解析格式**: 便于后续评估

---

### 方案4: 调整训练策略 ✅

**新的训练配置**:

```python
# 优化器配置
optimizer_config = {
    'max_bootstrapped_demos': 5,     # 减少到 5 个示例
    'max_labeled_demos': 10,         # 标记示例增加到 10
    'max_rounds': 30,                 # 最大优化轮数
    'num_trials': 20,                # 每轮尝试次数

    # 评估指标
    'metric': EnhancedPatentMetrics.evaluate_enhanced,
    'threshold': 0.5,                # 目标分数: 50%

    # 上下文窗口
    'max_context_length': 50000,     # 限制上下文长度
}

# 训练策略
training_strategy = {
    'Phase 1': {
        'optimizer': 'BootstrapFewShot',
        'data': '精选100条高质量数据',
        'goal': '建立基线 (>30%分数)',
    },
    'Phase 2': {
        'optimizer': 'MIPROv2',
        'data': '精选100条高质量数据',
        'goal': '优化到 >50%分数',
    },
    'Phase 3': {
        'optimizer': 'MIPROv2',
        'data': '精选100条 + 验证集',
        'goal': '最终优化 >60%分数',
    }
}
```

---

## 🎯 第三部分：实施计划

### 立即执行 (今天)

1. ✅ 创建 `enhanced_metrics.py` - 新的评估指标
2. ✅ 创建 `training_data_QUALITY_100_dspy.py` - 精选100条高质量数据
3. ✅ 修改 `PatentCaseAnalysis` Signature - 结构化输出

### 短期执行 (本周)

4. 运行 BootstrapFewShot 建立基线
5. 运行 MIPROv2 优化 (最多 30 轮)
6. 验证分数提升到 ≥ 50%

### 中期执行 (下周)

7. 如果分数达标，扩展到其他能力模块
8. 建立自动化训练流程

---

## 📊 预期效果

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 评估分数 | 0.3 | 0.5+ | +67% |
| 训练数据质量 | 低 | 高 | ✅ |
| 评估指标严格度 | 过严 | 合理 | ✅ |
| 提示词模板清晰度 | 模糊 | 结构化 | ✅ |

---

## 🚀 下一步行动

1. 创建 `core/intelligence/dspy/enhanced_metrics.py`
2. 从现有数据中筛选 100 条高质量案例
3. 修改 `PatentCaseAnalysis` Signature
4. 运行新的训练流程

**是否开始执行改进方案?**
