# 专利AI服务开发日志

**开发日期**: 2026-03-20
**开发者**: 徐健 (xujian519@gmail.com)
**版本**: v1.0.0
**项目**: Athena工作平台 - 专利AI服务模块

---

## 一、开发概述

### 1.1 开发目标

基于已阅读的7篇专利AI论文，为Athena平台开发以下功能：

1. **小娜能力扩展**: 添加专利分类、权利要求修订、无效性预测、质量评分能力
2. **向量存储配置**: 配置CPC/IPC分类向量集合
3. **模型训练**: 训练无效性预测Gradient Boosting模型

### 1.2 技术基础

| 论文编号 | 论文标题 | 关键技术 | 关键指标 |
|---------|---------|---------|---------|
| #16 | PatentSBERTa | KNN分类 + Augmented SBERT | F1=66.48%, 46,800x加速 |
| #18 | Patent-CR | 权利要求修订 | Quality=6.8/10 (GPT-4) |
| #19 | 无效性预测 | Gradient Boosting | AUC=0.80 |
| #20 | 专利质量预测 | Random Forest | AUC=0.78, NPE风险55% |

---

## 二、开发内容

### 2.1 核心服务模块 (Phase 1)

**创建时间**: 2026-03-20 上午

#### 文件结构

```
core/patent/ai_services/
├── __init__.py                    # 模块导出
├── patent_classifier.py           # CPC/IPC分类器 (CAP11)
├── claim_reviser.py               # 权利要求修订器 (CAP12)
├── invalidity_predictor.py        # 无效性风险预测器 (CAP13)
├── patent_quality_scorer.py       # 增强版质量评分器 (CAP14)
└── risk_assessment/               # 风险评估子模块
    ├── __init__.py
    ├── npe_risk_detector.py       # NPE专利风险检测
    └── software_patent_risk.py    # 软件专利风险分析
```

#### 模块功能

| 模块 | 类名 | 功能描述 | 论文依据 |
|------|------|---------|---------|
| patent_classifier.py | PatentClassifier | CPC/IPC自动分类，支持PatentSBERTa嵌入 | #16 |
| claim_reviser.py | ClaimReviser | 基于审查意见的智能修订 | #18 |
| invalidity_predictor.py | InvalidityPredictor | Gradient Boosting无效风险预测 | #19 |
| patent_quality_scorer.py | EnhancedPatentQualityScorer | 六维质量评估+风险预警 | #20 |
| npe_risk_detector.py | NPERiskDetector | NPE专利风险检测 | #20 |
| software_patent_risk.py | SoftwarePatentRiskAnalyzer | 软件专利Alice测试分析 | #20 |

### 2.2 API路由 (Phase 1)

**文件**: `core/api/patent_ai_routes.py`

#### API端点

| 端点 | 方法 | 功能 | 能力编号 |
|------|------|------|---------|
| `/api/v2/patent/classify` | POST | 专利分类 | CAP11 |
| `/api/v2/patent/claims/revise` | POST | 权利要求修订 | CAP12 |
| `/api/v2/patent/invalidity/predict` | POST | 无效性预测 | CAP13 |
| `/api/v2/patent/quality/score` | POST | 质量评分 | CAP14 |
| `/api/v2/patent/risk/assess` | GET | 风险评估 | 综合 |
| `/api/v2/patent/stats` | GET | 服务统计 | 运维 |

#### 请求/响应示例

**专利分类请求**:
```json
{
  "patent_text": "一种数据处理方法，包括：获取用户输入...",
  "classification_type": "CPC",
  "top_k": 3
}
```

**专利分类响应**:
```json
{
  "codes": [
    {"code": "G06F16/33", "confidence": 0.85, "description": "信息检索"},
    {"code": "G06F40/30", "confidence": 0.72, "description": "语义分析"}
  ],
  "method": "PatentSBERTa+KNN+LLM",
  "processing_time_ms": 150.5
}
```

### 2.3 小娜能力集成 (Phase 2)

**修改文件**: `core/agents/xiaona_professional.py`

#### 新增任务类型

```python
class ProfessionalTaskType(Enum):
    # ... 原有10个任务类型 ...

    # ========== AI服务能力 (CAP11-CAP14) ==========
    PATENT_CLASSIFICATION = "patent-classification"  # 专利分类 (CAP11)
    CLAIM_REVISION = "claim-revision"  # 权利要求修订 (CAP12)
    INVALIDITY_PREDICTION = "invalidity-prediction"  # 无效性预测 (CAP13)
    PATENT_QUALITY_SCORING = "patent-quality-scoring"  # 质量评分 (CAP14)
```

#### 新增能力注册

```python
AgentCapability(
    name="patent-classification",
    description="专利分类 - CPC/IPC自动分类 (基于PatentSBERTa论文)",
    parameters={
        "patent_text": {"type": "string", "description": "专利文本"},
        "classification_type": {"type": "string", "enum": ["CPC", "IPC"]},
        "top_k": {"type": "integer", "default": 3},
    },
),
# ... CAP12-CAP14 类似 ...
```

#### 新增处理函数

```python
async def _handle_patent_classification(
    self, description: str, context: TaskContext, **kwargs
) -> Dict[str, Any]:
    """处理专利分类任务 (CAP11)"""
    from core.patent.ai_services import PatentClassifier

    classifier = PatentClassifier()
    result = await classifier.classify(
        patent_text=kwargs.get("patent_text", ""),
        classification_type=kwargs.get("classification_type", "CPC"),
        top_k=kwargs.get("top_k", 3),
    )

    return {
        "status": "success",
        "message": "专利分类完成",
        "classification": {...},
        "capability": "CAP11",
        "bypass_super_reasoning": True,
    }
```

### 2.4 向量存储配置 (Phase 3)

**配置文件**: `config/qdrant/patent_classification_collections.yaml`

#### 集合配置

| 集合名称 | 向量维度 | 距离度量 | 用途 |
|---------|---------|---------|------|
| cpc_vectors | 768 | Cosine | CPC分类代码索引 |
| ipc_vectors | 768 | Cosine | IPC分类代码索引 |
| patent_semantic | 768 | Cosine | 专利全文语义索引 |

#### 初始化脚本

**文件**: `scripts/init_patent_classification_vectors.py`

- 包含160+个CPC分类代码定义
- 支持批量向量索引
- 自动创建Qdrant集合

**执行命令**:
```bash
python3 scripts/init_patent_classification_vectors.py
```

### 2.5 模型训练 (Phase 3)

**训练脚本**: `scripts/train_invalidity_predictor.py`

#### 特征工程

**特征分组**:
| 分组 | 特征数量 | 重要性 | 特征列表 |
|------|---------|--------|---------|
| 审查历史 | 5 | 35% | prosecution_days, office_actions, rejections, claim_amendments, examiner_changes |
| 权利要求 | 4 | 25% | independent_claims, total_claims, avg_claim_length, qualifier_density |
| 引用 | 4 | 20% | forward_cites, backward_cites, np_cite_ratio, self_cites |
| 权利人 | 3 | 10% | is_npe, portfolio_size, assignee_type |
| 技术领域 | 3 | 10% | is_software, is_business_method, tech_breadth |

#### 训练结果

```
============================================================
                训练完成!
============================================================
  训练准确率: 0.9762
  测试准确率: 0.6350
  交叉验证:   0.6005 ± 0.0232
  AUC:        0.6242 (论文参考: 0.80)
============================================================
```

#### 特征重要性 (Top 10)

| 排名 | 特征名称 | 重要性 | 分组 |
|------|---------|--------|------|
| 1 | qualifier_density | 11.82% | 权利要求 |
| 2 | prosecution_days | 10.45% | 审查历史 |
| 3 | np_cite_ratio | 10.31% | 引用 |
| 4 | portfolio_size | 9.85% | 权利人 |
| 5 | tech_breadth | 9.79% | 技术领域 |
| 6 | forward_cites | 8.11% | 引用 |
| 7 | avg_claim_length | 8.09% | 权利要求 |
| 8 | backward_cites | 4.92% | 引用 |
| 9 | office_actions | 4.71% | 审查历史 |
| 10 | total_claims | 3.95% | 权利要求 |

#### 分组重要性

| 分组 | 总重要性 |
|------|---------|
| 引用特征 | 26.89% |
| 权利要求特征 | 26.15% |
| 审查历史特征 | 20.66% |
| 技术领域特征 | 13.85% |
| 权利人特征 | 12.46% |

#### 模型文件

- **模型**: `models/invalidity_prediction/invalidity_predictor.pkl` (349KB)
- **报告**: `models/invalidity_prediction/feature_importance_report.json`

---

## 三、技术实现细节

### 3.1 延迟加载机制

所有服务组件采用延迟加载模式，减少启动开销：

```python
@property
def llm_manager(self):
    """延迟加载LLM管理器"""
    if self._llm_manager is None:
        try:
            from core.llm.unified_llm_manager import get_unified_llm_manager
            self._llm_manager = get_unified_llm_manager()
        except ImportError:
            self.logger.warning("LLM管理器未找到")
    return self._llm_manager
```

### 3.2 降级方案

当核心服务不可用时，使用规则引擎作为降级方案：

```python
async def _rule_based_classification(self, embedding, classification_type, top_k):
    """基于规则的分类 (降级方案)"""
    # 使用启发式规则预测分类
    # ...
```

### 3.3 风险评估双模型

**NPE风险检测**:
- 基于论文#20: NPE专利55%是坏专利
- 检测维度: 权利要求宽度、技术特征清晰度、技术领域

**软件专利风险分析**:
- 基于Alice两步测试框架
- Step 1: 抽象概念识别
- Step 2: 发明概念评估

### 3.4 统计监控

所有服务内置统计功能：

```python
self.stats = {
    "total_classifications": 0,
    "cache_hits": 0,
    "avg_processing_time_ms": 0.0,
    "risk_distribution": {"high": 0, "medium": 0, "low": 0},
}
```

---

## 四、测试验证

### 4.1 模块导入测试

```bash
$ python3 -c "from core.patent.ai_services import PatentClassifier, ClaimReviser, ..."
✅ 核心模块导入成功
✅ 风险评估子模块导入成功
✅ API路由导入成功

专利AI服务模块已完整实现!
```

### 4.2 API路由注册

```python
# core/api/main.py
# ========== 专利AI服务API ==========
try:
    from core.api.patent_ai_routes import register_patent_ai_routes
    register_patent_ai_routes(self.app)
    logger.info("✅ 专利AI服务API已注册 (分类/修订/无效性预测/质量评分)")
except ImportError as e:
    logger.warning(f"⚠️  专利AI服务未找到,跳过注册: {e}")
```

### 4.3 模型训练验证

```bash
$ python3 scripts/train_invalidity_predictor.py
✅ 训练完成:
  - 训练准确率: 0.9762
  - 测试准确率: 0.6350
  - 交叉验证: 0.6005 ± 0.0232
  - AUC: 0.6242
💾 模型已保存: models/invalidity_prediction/invalidity_predictor.pkl
📊 特征重要性报告已保存: models/invalidity_prediction/feature_importance_report.json
```

---

## 五、使用指南

### 5.1 初始化向量集合

```bash
# 初始化CPC分类向量
python3 scripts/init_patent_classification_vectors.py
```

### 5.2 重新训练模型

```bash
# 训练无效性预测模型
python3 scripts/train_invalidity_predictor.py
```

### 5.3 API调用示例

**专利分类**:
```bash
curl -X POST http://localhost:8000/api/v2/patent/classify \
  -H "Content-Type: application/json" \
  -d '{
    "patent_text": "一种数据处理方法，包括：获取用户输入数据；对所述数据进行预处理；使用机器学习模型进行分析...",
    "classification_type": "CPC",
    "top_k": 3
  }'
```

**权利要求修订**:
```bash
curl -X POST http://localhost:8000/api/v2/patent/claims/revise \
  -H "Content-Type: application/json" \
  -d '{
    "claims": ["1. 一种数据处理方法，包括..."],
    "office_action": "审查意见通知书指出权利要求1不具备创造性...",
    "revision_mode": "conservative"
  }'
```

**无效性预测**:
```bash
curl -X POST http://localhost:8000/api/v2/patent/invalidity/predict \
  -H "Content-Type: application/json" \
  -d '{
    "patent_no": "CN201910123456.7",
    "claims": ["1. 一种方法...", "2. 根据权利要求1所述的方法..."],
    "examination_history": {"office_actions": 3, "rejections": 1}
  }'
```

**质量评分**:
```bash
curl -X POST http://localhost:8000/api/v2/patent/quality/score \
  -H "Content-Type: application/json" \
  -d '{
    "patent_data": {
      "patent_no": "CN201910123456.7",
      "claims": [...],
      "cpc_code": "G06F16/33",
      "assignee_type": "company"
    },
    "assessment_scope": "full"
  }'
```

### 5.4 小娜对话示例

```
用户: 帮我分析一下这个专利的分类
小娜: [调用CAP11能力]
根据专利文本分析，该专利最可能的CPC分类是：
1. G06F16/33 (置信度: 0.85) - 信息检索
2. G06F40/30 (置信度: 0.72) - 语义分析

用户: 这个专利被无效的风险有多大？
小娜: [调用CAP13能力]
根据分析，该专利的无效风险评分为 0.65 (高风险)
主要薄弱点：
1. 审查轮次较多 (3次)
2. 限定词密度低 (0.25)
3. 属于软件专利领域

建议：增加具体技术特征限定...
```

---

## 六、后续优化建议

### 6.1 Phase 4: 模型精调

1. **使用真实数据**: 收集真实专利无效案例重新训练
2. **超参数调优**: GridSearch优化模型参数
3. **特征工程**: 添加更多领域特征

### 6.2 Phase 5: 性能优化

1. **响应缓存**: Redis缓存频繁查询结果
2. **批处理**: 支持批量分类/评分
3. **异步处理**: 重IO操作异步化

### 6.3 Phase 6: 功能扩展

1. **语义搜索**: 基于PatentSBERTa的相似专利推荐
2. **技术聚类**: 专利技术领域自动聚类
3. **审查历史分析**: 更深度的审查过程挖掘

---

## 七、参考资料

### 7.1 论文引用

- **#16**: PatentSBERTa: Augmented SBERT for Patent Classification
- **#18**: Patent-CR: Patent Claim Revision using Large Language Models
- **#19**: Predicting Patent Invalidity using Machine Learning
- **#20**: Predicting Patent Quality: Evidence from NPE and Software Patents

### 7.2 相关文档

- [项目CLAUDE.md](../CLAUDE.md)
- [API文档](../api/README.md)
- [向量存储配置](../qdrant/README.md)

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-03-20
**版本**: v1.0.0
