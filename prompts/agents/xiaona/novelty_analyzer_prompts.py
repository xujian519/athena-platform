"""
新颖性分析提示词模块

为NoveltyAnalyzerProxy提供专业的提示词模板。
"""

NOVELTY_ANALYSIS_SYSTEM_PROMPT = """
你是一位专业的专利新颖性分析专家，具备深厚的专利法知识和丰富的审查经验。

## 核心职责
1. 对比文件技术特征分析
2. 区别技术特征识别
3. 新颖性判断（单独对比原则）
4. 置信度评估

## 新颖性判断标准
根据《专利法》第22条第2款：
- 新颖性是指该发明在申请日以前，没有在国内外出版物上公开发表过、公开使用过
- 单独对比原则：只能将一份对比文件与申请专利的技术方案进行对比
- 如果技术方案与对比文件存在区别技术特征，则具备新颖性

## 分析要点
1. **技术特征提取**：准确识别权利要求中的所有技术特征
2. **逐一对比**：将目标专利与每一篇对比文件单独比对
3. **区别特征**：找出未被任何对比文件公开的技术特征
4. **新颖性判定**：存在至少一个区别技术特征即具备新颖性
5. **置信度评估**：基于区别特征的数量和重要性评估置信度

## 输出要求
- 客观、准确、基于证据
- 输出严格的JSON格式
- 不添加任何额外文字说明
"""


def build_novelty_analysis_prompt(
    patent_data: dict,
    reference_docs: list
) -> str:
    """
    构建新颖性分析提示词

    Args:
        patent_data: 专利数据
        reference_docs: 对比文件列表

    Returns:
        完整提示词
    """
    import json

    return f"""# 任务：专利新颖性分析

## 目标专利信息
专利号：{patent_data.get('patent_id', '未知')}
权利要求书：
```
{patent_data.get('claims', '未提供')}
```

## 对比文件列表
共{len(reference_docs)}篇对比文件：

```json
{json.dumps(reference_docs, ensure_ascii=False, indent=2)}
```

## 分析要求

### 1. 技术特征提取
从权利要求中提取所有技术特征，包括：
- 必要技术特征
- 附加技术特征
- 功能性特征
- 结构性特征

### 2. 逐一对比分析
对每一篇对比文件进行单独对比：
- 识别该对比文件公开的技术特征
- 标记未被公开的特征
- 计算特征公开比例

### 3. 区别技术特征识别
汇总所有对比结果，识别：
- 哪些特征在所有对比文件中均未被公开
- 这些区别特征的技术重要性
- 对技术方案的影响程度

### 4. 新颖性判断
基于区别技术特征，判断：
- 是否具备新颖性
- 新颖性强度（强/中/弱）
- 置信度评估（0-1分值）

## 输出格式

请严格按照以下JSON格式输出：

```json
{{
    "target_patent": "专利号",
    "total_features_count": 特征总数,
    "feature_categories": {{
        "essential": ["必要特征1", "必要特征2"],
        "additional": ["附加特征1"],
        "functional": ["功能特征1"],
        "structural": ["结构特征1"]
    }},
    "individual_comparisons": [
        {{
            "reference_id": "对比文件编号",
            "reference_title": "对比文件标题",
            "disclosed_features": ["被公开的特征1", "被公开的特征2"],
            "undisclosed_features": ["未被公开的特征1"],
            "disclosure_ratio": 0.75,
            "disclosure_analysis": "该对比文件公开了主要结构特征，但未公开功能性特征"
        }}
    ],
    "distinguishing_features": [
        {{
            "feature": "区别特征名称",
            "category": "特征类别",
            "importance": "high/medium/low",
            "description": "特征描述",
            "technical_significance": "技术意义"
        }}
    ],
    "novelty_conclusion": {{
        "has_novelty": true,
        "conclusion": "具备新颖性/不具备新颖性",
        "strength": "strong/medium/weak",
        "reasoning": "新颖性判断的详细理由",
        "key_distinguishing_features": ["关键区别特征1", "关键区别特征2"]
    }},
    "confidence_assessment": {{
        "confidence_score": 0.85,
        "confidence_level": "high/medium/low",
        "reasoning": "置信度评估理由"
    }},
    "recommendations": [
        "建议1",
        "建议2"
    ]
}}
```

请只输出JSON，不要添加任何额外说明。
"""


def build_feature_comparison_prompt(
    target_features: dict,
    reference_doc: dict
) -> str:
    """
    构建特征对比提示词

    Args:
        target_features: 目标专利特征
        reference_doc: 对比文件

    Returns:
        特征对比提示词
    """
    import json

    return f"""# 任务：技术特征对比分析

## 目标专利技术特征
```json
{json.dumps(target_features, ensure_ascii=False, indent=2)}
```

## 对比文件
编号：{reference_doc.get('doc_id', '未知')}
标题：{reference_doc.get('title', '未提供')}
摘要/内容：
```
{reference_doc.get('abstract', reference_doc.get('content', '未提供'))[:500]}
```

## 对比要求
1. 逐一特征比对
2. 判断每个特征是否被对比文件公开
3. 注意：功能相同但手段不同的特征，视为未公开

## 输出格式

```json
{{
    "reference_id": "对比文件编号",
    "feature_comparison": [
        {{
            "feature": "特征名称",
            "category": "特征类别",
            "disclosed": true,
            "disclosure_form": "完全公开/部分公开/未公开",
            "evidence": "判断依据",
            "similarity_note": "相似性说明"
        }}
    ],
    "disclosed_count": 被公开特征数,
    "undisclosed_count": 未被公开特征数,
    "total_count": 总特征数,
    "disclosure_ratio": 0.75,
    "overall_assessment": "整体评估"
}}
```

请只输出JSON，不要添加任何额外说明。
"""


def build_novelty_judgment_prompt(
    distinguishing_features: list,
    target_features: dict
) -> str:
    """
    构建新颖性判断提示词

    Args:
        distinguishing_features: 区别特征列表
        target_features: 目标特征

    Returns:
        新颖性判断提示词
    """
    import json

    total_features = sum(len(features) for features in target_features.values())

    return f"""# 任务：新颖性判断

## 技术特征统计
- 总特征数：{total_features}
- 区别特征数：{len(distinguishing_features)}
- 区别特征比例：{len(distinguishing_features) / total_features if total_features > 0 else 0:.1%}

## 区别技术特征
```json
{json.dumps(distinguishing_features, ensure_ascii=False, indent=2)}
```

## 判断标准
1. **单独对比原则**：基于逐一对比的结果
2. **区别特征**：在所有对比文件中均未被公开的特征
3. **新颖性成立**：存在至少一个区别技术特征
4. **新颖性强度**：
   - 强：多个重要区别特征
   - 中：少量区别特征或重要性中等
   - 弱：仅有次要区别特征

## 输出格式

```json
{{
    "has_novelty": true,
    "novelty_conclusion": "具备新颖性/不具备新颖性",
    "strength": "strong/medium/weak",
    "distinguishing_features_count": {len(distinguishing_features)},
    "total_features_count": {total_features},
    "novelty_ratio": {len(distinguishing_features) / total_features if total_features > 0 else 0:.2f},
    "key_distinguishing_features": ["关键区别特征1", "关键区别特征2"],
    "reasoning": "详细判断理由，说明为什么具备或不具备新颖性",
    "legal_basis": "法律依据引用（专利法第22条第2款）",
    "confidence_factors": [
        "置信度因素1",
        "置信度因素2"
    ]
}}
```

请只输出JSON，不要添加任何额外说明。
"""
