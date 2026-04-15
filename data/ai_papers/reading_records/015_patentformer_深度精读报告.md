# Patentformer论文 - 深度精读报告

## 🎯 核心信息

- **论文标题**: Patentformer: A Novel Method to Automate the Generation of Patent Applications
- **作者**: Juanyan Wang, Sai Krishna Reddy Mudhiganti, Manali Sharma
- **机构**: Samsung Semiconductor, Inc., San Jose, CA
- **会议**: EMNLP 2024 (Industry Track)
- **GitHub**: https://github.com/juriand/patentformer ✅
- **页数**: 20页
- **数据集**: Patent-2015-2023-G06N

---

## 🔬 核心技术方法

### 1. 任务定义

**两个新任务**:
```
1. Claim-to-Specification
   输入: 专利权利要求 (Claims)
   输出: 专利说明书 (Specification)

2. Claim+Drawing-to-Specification ⭐ (主要贡献)
   输入: 权利要求 + 图纸文本 + 图纸描述
   输出: 专利说明书
```

### 2. 输入数据结构

**专利文档结构** (形式化定义):
```python
P = {
    C: {c1, c2, ..., cl},           # l个权利要求
    S: {s1, s2, ..., sm},           # m个说明书段落
    I: {i1, i2, ..., it},           # t个图纸图像
    B: {b1, b2, ..., bt},           # t个图纸简要描述
    N: {n1, n2, ..., nt}            # t个图纸的组件名和编号
}

# 每个图纸的组件:
nz = {<iname_z1, inum_z1>, <iname_z2, inum_z2>, ..., <iname_zk, inum_zk>}
```

**数据统计** (USPTO 2015-2023):
```
部分          平均tokens   最小    最大      标准差
────────────────────────────────────────────────
专利整体(P)    14.12K      317    4.56M     17.83K
权利要求(C)    1.49K       3      715.30K   1.2K
图纸描述(B)    478.2       6      276.29K   782.3
说明书(S)      12.15K      25     4.55M     17.22K
组件(N)        274.0       0      24.91K    335.0
```

### 3. 专利文档处理

#### 3.1 权利要求分解 (Claim Subtrees)

**权利要求结构**:
```
独立权利要求 (Independent Claim)
    ├─ 不依赖其他权利要求
    ├─ 描述所有必要限制
    └─ 例如: Claim 1

从属权利要求 (Dependent Claim)
    ├─ 引用前一权利要求
    ├─ 添加进一步特征或限制
    └─ 例如: Claim 2 depends on Claim 1
```

**权利要求特征提取 (Claim Feature)**:
```python
# 权利要求可能包含多个特征，用分号分隔
claim = "特征1; 特征2; 特征3"
claim_features = claim.split(';')
# 结果: ['特征1', '特征2', '特征3']

# 每个特征映射到一个说明书段落
for feature in claim_features:
    matching_paragraph = find_matching_specification(feature)
```

**上下文构建**:
```python
# 对于独立权利要求的特征:
context = remaining_features_of_same_claim

# 对于从属权利要求的特征:
context = remaining_features_of_same_claim + parent_claim
```

#### 3.2 说明书处理

**段落合并策略**:
```python
# 问题: 某些段落太短，无法完整描述权利要求特征
# 解决: 合并<50 tokens的段落与后续段落

for paragraph in specification_paragraphs:
    if len(paragraph) < 50 tokens:
        paragraph = merge_with_next_paragraph(paragraph)

    # 截断以适应模型限制
    if model == 'T5':
        paragraph = truncate(paragraph, max_tokens=512)
    elif model == 'GPT-J':
        paragraph = truncate(paragraph, max_tokens=2048)
```

#### 3.3 图纸文本提取

**图纸编号识别**:
```python
# 识别FIG.、Fig.、Figure等模式
figure_pattern = r'(FIG\.|Fig\.|Figure)\s*(\d+)'

# 一个段落可能描述多个图纸，保留后续两个段落
if paragraph.mentions_figure():
    current_figure = extract_figure_number(paragraph)
    next_2_paragraphs.figure_number = current_figure
```

**图纸-说明书对齐**:
```python
# 移除描述其他图纸的句子（专注单一图纸）
for paragraph in specification_paragraphs:
    if paragraph.describes_multiple_figures():
        # 只保留当前图纸相关的句子
        paragraph = keep_only_current_figure_sentences(paragraph)
```

#### 3.4 组件名和编号提取

**最长公共子串算法**:
```python
# 从说明书文本提取组件名
# 输入: 带特殊标签的组件编号
# 输出: 组件名和编号对

def extract_component_names(spec_text, component_numbers):
    """
    使用最长公共子串算法找到组件名

    示例:
    文本: "the processor 260a may control"
    编号: 260a
    输出: <processor, 260a>
    """
    for number in component_numbers:
        # 找到以该编号结尾的文本序列
        name = longest_common_substring_ending_with(spec_text, number)
        components.append(<name, number>)

    return components
```

### 4. 训练数据构建

#### 4.1 权利要求-说明书匹配

**相似度计算**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')

def match_claim_to_specification(claim_feature, spec_paragraph):
    # 计算嵌入
    claim_embedding = model.encode(claim_feature)
    spec_embedding = model.encode(spec_paragraph)

    # 余弦相似度
    similarity = cosine_similarity(
        normalize(claim_embedding),
        normalize(spec_embedding)
    )

    # 质量控制: 相似度<0.6的丢弃
    if similarity < 0.6:
        return None

    return (claim_feature, spec_paragraph, similarity)
```

#### 4.2 训练输入格式

**带丰富上下文的输入**:
```python
input_text = f"""
<claim_feature> {claim_feature} </claim_feature>
<claim_feature_context> {context_claims} </claim_feature_context>
<brief_draw_desc> {brief_description} </brief_draw_desc>
<prev_para_num> {previous_paragraph_number} </prev_para_num>
<prev_para> {previous_paragraph} </prev_para>
<comp_name> {component_name} </comp_name>
<comp_num> {component_number} </comp_num>
<para_num> {current_paragraph_number} </para_num>
<fig_num> {figure_number} </fig_num>
<spec>
"""

output_text = specification_paragraph
```

### 5. 模型架构

#### 5.1 使用的模型

**两种架构对比**:

| 模型 | 架构 | 参数量 | 最大token | 用途 |
|------|------|--------|-----------|------|
| **Pat_T5** | Encoder-Decoder | 未明确 | 512 | 主要推荐 |
| **Pat_GPT-J** | Decoder-only | 6B | 2048 | 对比实验 |

**训练配置**:

```yaml
Pat_T5 (推荐):
  epochs: 2 (最优)
  training_time: 54 hours / 4 GPUs
  perplexity: 3.771

Pat_GPT-J:
  epochs: 1 (最优)
  training_time: 27 hours / 3 GPUs
  perplexity: 4.875
```

#### 5.2 微调策略

**训练目标**:
```
输入: T' = (C', B', N', 上下文)
输出: S' = 说明书段落

损失: 序列生成损失 (交叉熵)
优化: 标准优化器
```

**训练数据**: Patent-2015-2023-G06N
- 时间范围: 2015-2023
- 技术领域: G06N (神经网络/人工智能)
- 来源: USPTO

### 6. 生成策略

#### 6.1 采样方法

**三种策略**:

```python
1. Greedy Sampling (贪婪采样)
   output = model.generate(do_sample=False)

2. Top-kp Sampling (Top-k + Nucleus采样)
   output = model.generate(
       do_sample=True,
       top_k=50,
       top_p=0.95
   )

3. Post-Processing Strategy (后处理) ⭐ 最优
   candidates = []
   for i in range(10):  # 生成10个候选
       candidates.append(model.generate(...))

   # 使用评分函数排序
   best = rank_candidates(candidates)
```

#### 6.2 后处理评分函数

**评分公式**:
```python
def rank_candidates(candidates, input_claim, input_components):
    scores = []

    for candidate in candidates:
        # F1: 权利要求特征支持度 (余弦相似度)
        f1 = cosine_similarity(
            encode(input_claim),
            encode(candidate)
        )

        # F2: 组件名和编号匹配度
        if len(input_components) == 0:
            f2 = 1  # 无输入组件时为1
        else:
            candidate_components = extract_components(candidate)
            overlap = len(set(input_components) & set(candidate_components))
            f2 = overlap / len(input_components)

        # F3: 无错误引用其他图纸
        if has_reference_to_other_figures(candidate):
            f3 = 0
        else:
            f3 = 1

        # 总分
        total_score = f1 + f2 + f3
        scores.append((candidate, total_score))

    # 返回最高分的候选
    return max(scores, key=lambda x: x[1])[0]
```

#### 6.3 生成长度控制

**Min/Max Token限制**:
```python
# 为了公平比较:
Pat_T5: min_tokens=100, max_tokens=512
Pat_GPT-J: min_tokens=50, max_tokens=256

# 结果平均长度:
Pat_T5: 174 tokens (训练数据: 199 tokens)
Pat_GPT-J: 206 tokens (训练数据: 194 tokens)
```

### 7. 评估方法

#### 7.1 自动评估指标

**12个NLG指标**:
```python
metrics = [
    'Perplexity',      # 困惑度
    'BLEU',            # 双语评估
    'ROUGE-1/2/L/LSum',# 召回导向评估
    'WER',             # 词错误率
    'NIST',            # 考虑信息量的BLEU
    'METEOR',          # 显式排序的翻译评估
    'ChrF',            # 字符级F分数
    'BERTScore',       # BERT语义相似度
    'COMET'            # 跨语言优化评估
]
```

#### 7.2 人工评估

**评估者**: 4位专利专家
- Komal Magsi
- Elliot Karlin
- Kamil Bojanczyk
- Joseph Findley

**评估维度**:
```yaml
1. 正确性 (Correctness):
   - 权利要求特征是否在说明书中得到支持
   - 组件名和编号是否正确引用
   - 对相关图纸的引用是否正确

2. 质量 (Quality):
   - 专利专家的主观评价
   - 仅在两个样本都正确时比较
   - Win/Tie/Loss vs 实际说明书
```

---

## 📊 实验结果详解

### 1. 自动评估结果 (Table 4)

**5000个测试样本**:

| 指标 | Pat_GPT-J_Greedy | Pat_T5*_Greedy | Pat_GPT-J_Top-kp | Pat_T5*_Top-kp | Pat_GPT-J_P | **Pat_T5*_P** ⭐ |
|------|------------------|----------------|------------------|----------------|-------------|------------------|
| BERTScore | 0.852 | 0.871 | 0.854 | 0.874 | 0.864 | **0.878** |
| BLEU | 0.164 | 0.239 | 0.146 | 0.234 | 0.179 | **0.246** |
| ChrF | 43.090 | 43.330 | 43.570 | 45.120 | 44.861 | **46.533** |
| METEOR | 0.350 | 0.370 | 0.352 | 0.380 | 0.372 | **0.393** |
| ROUGE-L | 0.296 | 0.364 | 0.272 | 0.346 | 0.299 | **0.360** |

**关键发现**:
- ✅ Pat_T5* 全面优于 Pat_GPT-J
- ✅ Post-Processing策略优于Greedy和Top-kp
- ✅ Pat_T5*_P 达到最优性能

### 2. 人工评估结果

#### 2.1 随机样本 (神经处理器领域)

**100对样本**:

| 方法 | 正确 | 不正确 | W/T/L (质量) |
|------|------|--------|--------------|
| **Pat_T5*** | **33 (66%)** | 17 | 15/6/9 |
| Pat_GPT-J | 28 (56%) | 22 | 14/5/7 |
| Actual | 67 (67%) | 33 | N/A |

**关键发现**:
- ✅ Pat_T5* 正确率达到66%，接近实际数据(67%)
- ✅ 质量方面: Pat_T5* 赢15次，平6次，输9次
- ⚠️ 实际数据的67%准确率说明训练数据本身存在对齐问题

#### 2.2 随机样本 (系统芯片领域)

**40对样本**:

| 方法 | 正确 | 不正确 | W/T/L (质量) |
|------|------|--------|--------------|
| **Pat_T5*** | **4 (20%)** | 16 | 0/1/2 |
| Pat_GPT-J | 2 (10%) | 18 | 0/0/1 |
| Actual | 14 (35%) | 26 | N/A |

**关键发现**:
- ⚠️ 系统芯片领域性能明显下降
- ⚠️ 需要针对不同技术领域进一步微调

#### 2.3 完整专利测试

**专利1 (Meta Vision技术)**: 58个样本
- Pat_T5* 正确: 53/58 (91.38%) ✅
- 缺失图纸: 11个样本
- 缺失权利要求特征: 35个样本

**专利2 (Memory技术)**: 81个样本
- Pat_T5* 正确: 13/81 (16.05%) ⚠️
- 缺失图纸: 12个样本
- 缺失权利要求特征: 17个样本

### 3. 消融实验 (Table 7)

**输入要素消融**:

| 配置 | PPL ↓ |
|------|-------|
| Pat_T5 (T'→S') | **3.790** |
| Pat_T5 (T'-C'→S') | 4.818 |
| Pat_T5 (T'-B'→S') | 3.881 |
| Pat_T5 (T'-N'→S') | 5.488 |

**关键发现**:
- 🔑 **移除组件(N')影响最大**: PPL从3.790上升到5.488
- 🔑 移除权利要求(C')也有显著影响
- 🔑 移除图纸描述(B')影响较小

**上下文消融**:

| 配置 | PPL ↓ |
|------|-------|
| Pat_T5 (T'→S') | **3.790** |
| Pat_T5 (T'-Prev_Para→S') | 3.975 |
| Pat_T5 (T'-Para_Num→S') | 4.431 |
| Pat_T5 (T'-Fig_Num→S') | 3.849 |
| Pat_T5 (T'-Context_Claims→S') | 4.354 |

**关键发现**:
- 🔑 **移除段落编号影响最大**: PPL上升到4.431
- 🔑 移除上下文权利要求也有显著影响
- 🔑 移除图纸编号影响较小，但会导致错误引用

### 4. Epoch消融 (Table 8)

| 模型 | Epochs | PPL ↓ | 训练时间 |
|------|--------|-------|----------|
| Pat_GPT-J | 1 | **4.875** | 27h/3 GPUs |
| Pat_GPT-J | 2 | 5.662 | 54h/3 GPUs |
| Pat_T5 | 1 | 3.790 | 27h/4 GPUs |
| **Pat_T5** | **2** | **3.771** | 54h/4 GPUs |
| Pat_T5 | 3 | 4.041 | 81h/4 GPUs |

**关键发现**:
- ✅ Pat_T5最优epoch=2
- ⚠️ Pat_GPT-J训练>1 epoch会过拟合
- ⏱️ 总训练时间: 54小时 (4 GPUs)

---

## 💻 代码和实现细节

### GitHub仓库
```
https://github.com/juriand/patentformer
```

### 关键代码片段

#### 1. 数据预处理
```python
# 权利要求特征提取
def extract_claim_features(claim_text):
    """用分号分割权利要求"""
    features = claim_text.split(';')
    return [f.strip() for f in features if f.strip()]

# 组件名提取
def extract_components(spec_text, component_numbers):
    """使用最长公共子串算法"""
    components = []
    for num in component_numbers:
        # 找到以该编号结尾的最长公共子串
        name = find_longest_common_substring_ending_with(
            spec_text, num
        )
        components.append((name, num))
    return components

# 相似度计算
def compute_claim_spec_similarity(claim, spec):
    """使用Sentence Transformer"""
    model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')

    claim_emb = model.encode(claim)
    spec_emb = model.encode(spec)

    similarity = cosine_similarity(
        normalize(claim_emb),
        normalize(spec_emb)
    )

    return similarity
```

#### 2. 训练输入构建
```python
def build_training_input(claim_feature, context, drawing_info, prev_para, components):
    """
    构建带丰富上下文的训练输入
    """
    input_text = f"""
<claim_feature> {claim_feature} </claim_feature>
<claim_feature_context> {context} </claim_feature_context>
<brief_draw_desc> {drawing_info['brief_desc']} </brief_draw_desc>
<prev_para_num> {prev_para['num']} </prev_para_num>
<prev_para> {prev_para['text']} </prev_para>
<comp_name> {components['name']} </comp_name>
<comp_num> {components['num']} </comp_num>
<para_num> {prev_para['num'] + 1} </para_num>
<fig_num> {drawing_info['fig_num']} </fig_num>
<spec>
"""
    return input_text
```

#### 3. 后处理排序
```python
def rank_specification_candidates(candidates, input_claim, input_components):
    """
    评分函数: F = argmax(f1 + f2 + f3)
    """
    model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')
    scores = []

    for candidate in candidates:
        # f1: 权利要求特征支持度
        claim_emb = model.encode(input_claim)
        cand_emb = model.encode(candidate)
        f1 = cosine_similarity(claim_emb, cand_emb)

        # f2: 组件匹配度
        if len(input_components) == 0:
            f2 = 1
        else:
            cand_components = extract_components_from_text(candidate)
            overlap = len(set(input_components) & set(cand_components))
            f2 = overlap / len(input_components)

        # f3: 无错误图纸引用
        f3 = 0 if has_other_figure_references(candidate) else 1

        total = f1 + f2 + f3
        scores.append((candidate, total))

    # 返回最高分候选
    return max(scores, key=lambda x: x[1])[0]
```

#### 4. 模型生成
```python
# T5模型配置
from transformers import T5ForConditionalGeneration, T5Tokenizer

model = T5ForConditionalGeneration.from_pretrained('t5-base')
tokenizer = T5Tokenizer.from_pretrained('t5-base')

# 生成配置
generation_config = {
    'max_length': 512,
    'min_length': 100,
    'do_sample': False,  # Greedy
    'num_return_sequences': 1
}

# 生成
outputs = model.generate(
    input_ids,
    **generation_config
)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

---

## 🎯 实际部署建议

### 系统架构
```
用户输入界面
    ├─ 权利要求书输入
    ├─ 图纸上传 (PowerPoint/Visio/DWG)
    ├─ 图纸简要描述
    └─ 权利要求-图纸映射

处理流程
    ├─ OCR提取图纸中的组件名和编号
    ├─ 权利要求特征分解
    ├─ 说明书生成 (Patentformer)
    └─ 后处理和质量检查

输出
    └─ 完整专利说明书
```

### 推理流程
```python
def generate_specification(claims, drawings, mapping):
    """
    实际部署的推理流程
    """
    specifications = []

    # 1. 提取权利要求特征
    claim_features = [extract_features(c) for c in claims]

    # 2. 对每个权利要求特征
    for feature in claim_features:
        # 找到相关图纸
        related_drawing = mapping[feature]

        # 提取组件
        components = ocr_extract_components(related_drawing)

        # 构建输入
        input_text = build_input(feature, related_drawing, components)

        # 生成候选 (10个)
        candidates = []
        for _ in range(10):
            output = model.generate(input_text)
            candidates.append(output)

        # 后处理选择最佳
        best_spec = rank_candidates(candidates, feature, components)

        specifications.append(best_spec)

    # 3. 合并所有段落
    full_specification = merge_paragraphs(specifications)

    return full_specification
```

---

## 📋 关键代码资源

### 已提供
- ✅ GitHub代码仓库: https://github.com/juriand/patentformer
- ✅ 数据集: Patent-2015-2023-G06N
- ✅ 预训练模型权重 (预计在仓库中)

### 核心依赖
```python
transformers  # Hugging Face Transformers
sentence-transformers  # Sentence Transformers
torch  # PyTorch
```

---

## ⚠️ 局限性和注意事项

### 技术局限
1. **仅支持单一图纸**: 一个段落只能描述一个图纸
2. **领域依赖**: 在不同技术领域性能差异大
3. **组件提取**: 假设能从图纸OCR提取组件，实际可能困难
4. **训练数据对齐**: 实际数据67%准确率说明对齐问题
5. **无多模态**: 未使用图纸图像，仅使用文本

### USPTO警告
```
⚠️ 美国专利商标局提醒:
- 使用AI起草工具需要额外谨慎
- 必须验证技术准确性
- 必须符合35 U.S.C. 112要求
- 专利代理律师仍需彻底检查生成内容
```

---

## 🚀 Athena平台应用路线图

### 阶段1: 数据准备 (1个月)
```python
1. 收集中文专利数据
   - 来源: CNIPA
   - 领域: 人工智能、半导体、通信
   - 结构: 权利要求、说明书、附图

2. 数据预处理
   - 权利要求特征提取
   - 附图OCR文本提取
   - 权利要求-说明书对齐

3. 数据集构建
   - 训练/验证/测试划分
   - 质量控制 (相似度>0.6)
```

### 阶段2: 模型训练 (2个月)
```python
1. 基础模型选择
   - ChatGLM-6B (中文优势)
   - Qwen-7B (多语言)
   - T5-base (Encoder-Decoder)

2. 微调策略
   - LoRA微调 (参数高效)
   - 全参数微调 (性能最优)
   - 混合精度训练

3. 训练配置
   - GPU: 4-8 × A100
   - 时间: 50-100小时
   - Epoch: 2-3
```

### 阶段3: 系统集成 (1个月)
```python
1. API开发
   - 输入: 权利要求 + 附图
   - 输出: 说明书
   - 格式: JSON/Markdown

2. 前端界面
   - 权利要求编辑器
   - 附图上传和标注
   - 生成结果对比

3. 质量控制
   - 自动检查 (组件一致性)
   - 人工审核界面
   - 反馈收集
```

### 阶段4: 优化迭代 (持续)
```python
1. 性能优化
   - 推理加速 (量化、蒸馏)
   - 批量处理
   - 缓存机制

2. 功能增强
   - 多模态支持 (图纸图像)
   - 多语言生成
   - 领域自适应

3. 持续学习
   - 用户反馈收集
   - 定期重新训练
   - A/B测试
```

---

**报告完成时间**: 2026-03-20
**精读深度**: 完整20页 + 代码实现细节
**可复现性**: 高 (有GitHub代码 + 详细方法描述)
