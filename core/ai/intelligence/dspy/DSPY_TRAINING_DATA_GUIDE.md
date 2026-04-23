# DSPy训练数据准备指南

> 目标: 为Phase 1试点准备50个高质量训练示例
> 试点能力: CAPABILITY_2 案情分析能力
> 创建时间: 2025-12-29

---

## 第一部分：DSPy训练数据格式

### DSPy Example结构

```python
import dspy

# DSPy训练示例格式
training_example = dspy.Example(
    # 输入字段
    user_input="用户询问或案情描述",
    context="相关法条或现有技术",
    task_type="capability_2",  # 任务类型

    # 输出字段（标签）
    analysis_result="案情分析结果",
    risk_assessment="风险评估",
    recommended_actions="建议行动"

).with_inputs("user_input", "context", "task_type")
```

### 关键要点

1. **`.with_inputs()`**: 标记哪些字段是输入
2. **未标记的字段**: 自动视为输出（需要预测的目标）
3. **字段命名**: 必须与DSPy Signature的输入/输出字段匹配

---

## 第二部分：训练数据来源

### 来源1: 历史专利案例（推荐）

从Athena平台数据库获取真实案例：

```python
# 示例：从复审无效决定中提取
source = "patent_decisions"  # 308,881条记录
fields = ["案情描述", "决定要点", "法律依据"]
```

### 来源2: 人工标注案例

专利代理人提供的典型分析案例

### 来源3: 合成案例

基于真实法条构建的模拟案例

---

## 第三部分：数据收集策略

### CAPABILITY_2（案情分析）数据结构

| 字段 | 说明 | 示例 |
|------|------|------|
| case_title | 案件标题 | "某医疗器械发明专利无效案" |
| case_description | 案情描述 | 200-500字的详细描述 |
| technical_field | 技术领域 | "医疗器械" |
| prior_art | 现有技术 | 对比文件D1-D5 |
| legal_issues | 法律争议点 | ["新颖性", "创造性"] |
| analysis_result | 分析结果 | 结构化的案情分析 |
| outcome | 结果 | "专利全部无效" |

---

## 第四部分：50个示例分配方案

### 分配策略

```
总计: 50个示例

├── 新颖性案例 (15个)
│   ├── 方法新颖性 (5个)
│   ├── 产品新颖性 (5个)
│   └── 用途新颖性 (5个)
│
├── 创造性案例 (15个)
│   ├── 突出实质性特点 (8个)
│   └── 显著进步 (7个)
│
├── 充分公开案例 (10个)
│   ├── 技术方案描述 (5个)
│   └── 技术效果验证 (5个)
│
├── 清楚性案例 (5个)
│   ├── 权利要求书清楚性 (3个)
│   └── 说明书清楚性 (2个)
│
└── 综合案例 (5个)
    └── 多问题组合案例
```

---

## 第五部分：数据模板

### 模板1: 新颖性分析案例

```python
{
    "case_id": "NOV_001",
    "case_title": "某智能穿戴设备新颖性争议案",
    "technical_field": "智能穿戴设备",
    "case_description": """
    涉案专利: 一种具有健康监测功能的智能手表
    专利号: CN2018XXXXXXXU
    对比文件1: D1 - CN2017XXXXXXXU（现有智能手表）
    对比内容: D1公开了心率监测、步数计数功能
    区别特征: 涉案专利新增血氧监测功能
    """,
    "prior_art": """
    D1: CN2017XXXXXXXU
    公开内容:
    - 智能手表本体
    - 心率监测传感器
    - 步数计数模块
    - 数据显示模块
    """,
    "legal_issues": ["新颖性"],
    "analysis_result": """
    【新颖性分析】
    1. 对比文件D1公开了智能手表的基本结构和健康监测功能
    2. 区别技术特征: 血氧监测功能
    3. 判断: 血氧监测功能在D1中未公开，且不属于本领域公知常识
    4. 结论: 具备新颖性
    """,
    "risk_assessment": "低风险",
    "recommended_actions": "维持专利权有效"
}
```

### 模板2: 创造性分析案例

```python
{
    "case_id": "INV_001",
    "case_title": "某药物组合物创造性争议案",
    "technical_field": "医药化学",
    "case_description": """
    涉案专利: 一种治疗高血压的药物组合物
    权利要求: 成分A(10-30%) + 成分B(5-15%) + 载体
    对比文件1: D1公开了成分A治疗高血压
    对比文件2: D2公开了成分B治疗心血管疾病
    争议点: A+B组合是否具备创造性
    """,
    "prior_art": """
    D1: 成分A单用于高血压，有效率60%
    D2: 成分B单用于心血管疾病，有效率45%
    """,
    "legal_issues": ["创造性"],
    "analysis_result": """
    【创造性分析】
    1. 最接近现有技术: D1
    2. 区别特征: 加入成分B形成组合物
    3. 技术问题: 增强疗效，降低副作用
    4. 技术效果: 联合使用有效率提升至85%
    5. 显著性: 非显而易见，产生预料不到的技术效果
    6. 结论: 具备创造性
    """,
    "risk_assessment": "中风险",
    "recommended_actions": "重点论证协同效果"
}
```

### 模板3: 充分公开案例

```python
{
    "case_id": "DIS_001",
    "case_title": "某人工智能算法充分公开争议案",
    "technical_field": "人工智能",
    "case_description": """
    涉案专利: 一种基于深度学习的图像识别方法
    争议点: 说明书是否充分公开了算法实现细节
    """,
    "analysis_result": """
    【充分公开分析】
    1. 技术方案: CNN架构，包含卷积层、池化层、全连接层
    2. 公开程度:
       - 网络层数: 明确（8层）
       - 参数范围: 给定（学习率0.001-0.1）
       - 训练数据: 描述（ImageNet数据集）
    3. 再现性: 本领域技术人员可据此实现
    4. 结论: 符合充分公开要求
    """,
    "risk_assessment": "低风险",
    "recommended_actions": "补充实验数据增强说服力"
}
```

---

## 第六部分：数据准备工具

我将为您创建以下工具：

1. **数据生成器** - 基于模板生成训练数据
2. **数据验证器** - 检查数据质量
3. **数据导出器** - 导出为DSPy格式

---

## 第七部分：质量标准

### 完整性检查

- [ ] 所有必填字段已填写
- [ ] 案情描述清晰完整（>200字）
- [ ] 分析结果结构化
- [ ] 法律依据引用准确

### 一致性检查

- [ ] 分析逻辑与结论一致
- [ ] 法条引用与争议点匹配
- [ ] 风险评估合理

### 多样性检查

- [ ] 技术领域多样（至少5个领域）
- [ ] 法律问题类型全面
- [ ] 难度梯度分布合理

---

## 第八部分：实施计划

### 步骤1: 数据收集 (3-5天)
- 从数据库提取真实案例 (20个)
- 人工标注典型案例 (20个)
- 合成边缘案例 (10个)

### 步骤2: 数据清洗 (1-2天)
- 格式统一化
- 去重处理
- 匿名化处理

### 步骤3: 数据验证 (1天)
- 运行验证脚本
- 人工抽样检查
- 修正错误

### 步骤4: 数据分割 (0.5天)
- 训练集: 40个 (80%)
- 验证集: 5个 (10%)
- 测试集: 5个 (10%)

---

## 附录：快速开始

### 使用Python脚本生成数据

```python
from core.intelligence.dspy.training_data_generator import (
    TrainingDataGenerator,
    CaseTemplate
)

# 创建生成器
generator = TrainingDataGenerator()

# 使用模板生成案例
case = generator.generate_from_template(
    template_type="novelty",
    params={
        "technical_field": "智能汽车",
        "invention_title": "自动驾驶路径规划方法",
        # ... 其他参数
    }
)

# 转换为DSPy Example
dspy_example = case.to_dspy_example()

# 保存到文件
generator.save_examples([dspy_example], "training_data.json")
```

### 批量生成

```bash
# 运行数据生成脚本
python3 core/intelligence/dspy/generate_training_data.py \
    --count 50 \
    --output training_data.json \
    --types novelty,creative,disclosure
```

---

**下一步**: 您希望我创建数据生成工具吗？我可以实现：
1. 基于模板的案例生成器
2. 数据质量验证器
3. DSPy格式转换器
