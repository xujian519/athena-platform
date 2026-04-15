# 人机协作专利分析系统架构设计
# Human-in-the-Loop Patent Analysis System Architecture

作者: Athena平台团队
创建时间: 2025-12-30
版本: 1.0.0

---

## 一、核心设计理念

### 1.1 问题认知

**现实情况**：
- 专利无效分析是人类高难度专业工作
- 即便人类专家，单一案例成功率也难以保证
- AI不应追求"替代人类"，而应"增强人类"

**设计原则**：
```
┌─────────────────────────────────────────────────────────────┐
│  AI负责：可验证的机械性任务    人类负责：需要判断的决策任务  │
│  ✓ 特征提取                  ✓ 争议焦点界定                  │
│  ✓ 证据对比                  ✓ 法律条款选择                  │
│  ✓ 格式生成                  ✓ 结论判断                      │
│                              ✓ 风险评估                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 任务分解策略

将复杂案例分解为**原子化可验证任务**：

```
复杂案例分析
    ↓ 分解
┌──────────┬──────────┬──────────┬──────────┐
│ 任务1    │ 任务2    │ 任务3    │ 任务4    │
│ 案件分类 │ 证据提取 │ 对比分析 │ 结论生成 │
│ (AI+验证)│ (AI主导) │ (混合)   │ (人类决策)│
└──────────┴──────────┴──────────┴──────────┘
```

---

## 二、系统架构

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        人机协作专利分析系统                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   1. 任务分解层 (Task Decomposer)           │ │
│  │  - 人类选择分析维度                                         │ │
│  │  - 系统自动生成子任务序列                                   │ │
│  │  - 每个任务定义输入/输出/验证标准                          │ │
│  └───────────────────────┬────────────────────────────────────┘ │
│                          ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   2. 任务执行层 (Task Executor)             │ │
│  │  ┌─────────────┬─────────────┬─────────────┬─────────────┐ │ │
│  │  │ 任务类型A   │ 任务类型B   │ 任务类型C   │ 任务类型D   │ │ │
│  │  │ AI主导      │ AI+验证     │ 混合        │ 人类决策    │ │ │
│  │  │ 特征提取    │ 证据对比    │ 法律推理    │ 最终结论    │ │ │
│  │  └─────────────┴─────────────┴─────────────┴─────────────┘ │ │
│  └───────────────────────┬────────────────────────────────────┘ │
│                          ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   3. 验证反馈层 (Validation & Feedback)     │ │
│  │  - AI任务：自动验证（规则/LLM评分）                        │ │
│  │  - 人类任务：专家审核                                      │ │
│  │  - 收集反馈用于微调                                        │ │
│  └───────────────────────┬────────────────────────────────────┘ │
│                          ↓                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   4. 结果合成层 (Result Synthesizer)       │ │
│  │  - 整合所有子任务结果                                      │ │
│  │  - 生成分析报告                                            │ │
│  │  - 标注置信度和依据                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 任务分类体系

```python
# 任务类型定义
TASK_TYPES = {
    "AI_AUTOMATIC": {
        "任务": "证据提取、特征识别、文本分类",
        "验证方式": "自动验证（规则/正则）",
        "置信度要求": ">90%",
        "示例": "从案由中提取专利号、证据列表"
    },
    "AI_WITH_VALIDATION": {
        "任务": "相似度计算、要素对比",
        "验证方式": "LLM评分 + 规则校验",
        "置信度要求": ">70%",
        "示例": "对比涉案专利与证据1的技术特征"
    },
    "HUMAN_GUIDED_AI": {
        "任务": "法律推理、因果关系分析",
        "验证方式": "人类设定框架，AI填充细节",
        "置信度要求": "人类主导",
        "示例": "根据人类选定的法条分析创造性"
    },
    "HUMAN_DECISION": {
        "任务": "最终结论、风险评估",
        "验证方式": "专家审核 + 责任签字",
        "置信度要求": "人类决策",
        "示例": "综合判断专利是否全部无效"
    }
}
```

---

## 三、核心组件设计

### 3.1 任务分解器 (TaskDecomposer)

```python
class PatentTaskDecomposer:
    """专利案例任务分解器"""

    def __init__(self):
        self.task_templates = {
            "novelty": [
                {
                    "task_id": "extract_claims",
                    "type": "AI_AUTOMATIC",
                    "description": "提取涉案专利权利要求",
                    "input": "案由描述",
                    "output": "结构化权利要求列表",
                    "validator": "ClaimsValidator"
                },
                {
                    "task_id": "extract_evidence",
                    "type": "AI_AUTOMATIC",
                    "description": "提取对比文件证据",
                    "input": "案由描述",
                    "output": "证据列表（编号+内容）",
                    "validator": "EvidenceValidator"
                },
                {
                    "task_id": "claim_comparison",
                    "type": "AI_WITH_VALIDATION",
                    "description": "权利要求与证据逐条对比",
                    "input": "权利要求 + 证据",
                    "output": "对比矩阵",
                    "validator": "ComparisonValidator"
                },
                {
                    "task_id": "novelty_conclusion",
                    "type": "HUMAN_DECISION",
                    "description": "新颖性结论判断",
                    "input": "对比矩阵 + 法律条款",
                    "output": "新颖性结论",
                    "validator": "HumanExpert"
                }
            ],
            "creative": [
                {
                    "task_id": "extract_technical_problem",
                    "type": "AI_WITH_VALIDATION",
                    "description": "提取发明要解决的技术问题",
                    "input": "说明书摘要",
                    "output": "技术问题陈述",
                    "validator": "LLMScorer"
                },
                {
                    "task_id": "identify_differences",
                    "type": "AI_WITH_VALIDATION",
                    "description": "识别与现有技术的区别特征",
                    "input": "权利要求 + 对比文件",
                    "output": "区别特征列表",
                    "validator": "LLMScorer"
                },
                {
                    "task_id": "obviousness_analysis",
                    "type": "HUMAN_GUIDED_AI",
                    "description": "显而易见性分析",
                    "input": "区别特征 + 现有技术",
                    "output": "创造性分析报告",
                    "validator": "HumanExpert"
                },
                {
                    "task_id": "creative_conclusion",
                    "type": "HUMAN_DECISION",
                    "description": "创造性结论判断",
                    "input": "分析报告",
                    "output": "创造性结论",
                    "validator": "HumanExpert"
                }
            ]
        }

    def decompose(self, case_info: dict, case_type: str) -> list:
        """分解案例为任务序列"""
        template = self.task_templates[case_type]
        tasks = []
        for i, task_spec in enumerate(template):
            task = {
                "task_id": f"{case_type}_{task_spec['task_id']}",
                "sequence": i,
                "type": task_spec["type"],
                "description": task_spec["description"],
                "input": self._prepare_input(case_info, task_spec),
                "output_schema": task_spec["output"],
                "validator": task_spec["validator"],
                "status": "pending"
            }
            tasks.append(task)
        return tasks
```

### 3.2 任务执行器 (TaskExecutor)

```python
class PatentTaskExecutor:
    """专利任务执行器"""

    def __init__(self):
        self.ai_executor = AIExecutor()
        self.human_interface = HumanInterface()
        self.validator_registry = ValidatorRegistry()

    def execute_task(self, task: dict, context: dict) -> dict:
        """执行单个任务"""

        # 根据任务类型选择执行方式
        if task["type"] == "AI_AUTOMATIC":
            # AI自动执行
            result = self.ai_executor.execute(
                task=task,
                context=context
            )
            # 自动验证
            validation = self.validator_registry.get(
                task["validator"]
            ).validate(result)
            return {
                "result": result,
                "validation": validation,
                "confidence": validation["score"]
            }

        elif task["type"] == "AI_WITH_VALIDATION":
            # AI执行 + 验证
            result = self.ai_executor.execute(task, context)
            validation = self.validator_registry.get(
                task["validator"]
            ).validate(result)

            # 如果置信度低，请求人类复核
            if validation["score"] < 0.7:
                human_review = self.human_interface.request_review(
                    task=task,
                    ai_result=result,
                    validation=validation
                )
                return {
                    "result": human_review["result"],
                    "validation": human_review["validation"],
                    "confidence": human_review["confidence"],
                    "human_intervention": True
                }
            return {
                "result": result,
                "validation": validation,
                "confidence": validation["score"],
                "human_intervention": False
            }

        elif task["type"] == "HUMAN_GUIDED_AI":
            # 人类设定框架，AI填充
            framework = self.human_interface.get_framework(task)
            ai_filled = self.ai_executor.fill_framework(
                task=task,
                framework=framework,
                context=context
            )
            return {
                "result": ai_filled,
                "validation": {"score": 1.0},  # 人类框架，无需验证
                "confidence": "human_guided",
                "human_intervention": True
            }

        elif task["type"] == "HUMAN_DECISION":
            # 人类直接决策
            decision = self.human_interface.make_decision(
                task=task,
                context=context
            )
            return {
                "result": decision,
                "validation": {"score": 1.0},
                "confidence": "human_expert",
                "human_intervention": True
            }
```

### 3.3 人类交互接口 (HumanInterface)

```python
class HumanInterface:
    """人类交互接口"""

    def __init__(self):
        self.pending_reviews = Queue()
        self.decision_queue = Queue()

    def request_review(self, task: dict, ai_result: dict,
                      validation: dict) -> dict:
        """请求人类复核AI结果"""

        review_item = {
            "task_id": task["task_id"],
            "description": task["description"],
            "ai_result": ai_result,
            "validation": validation,
            "confidence": validation["score"],
            "actions": [
                "accept",  # 接受AI结果
                "modify",  # 修改AI结果
                "reject"   # 拒绝，重新执行
            ]
        }

        # 发送到人类界面
        self.pending_reviews.put(review_item)

        # 等待人类响应（阻塞或超时）
        response = self._wait_for_response(review_item["id"])

        return response

    def get_framework(self, task: dict) -> dict:
        """获取人类设定的分析框架"""

        framework_request = {
            "task_id": task["task_id"],
            "description": task["description"],
            "required_elements": self._get_required_elements(task),
            "example_framework": self._get_example_framework(task)
        }

        # 发送到人类界面
        self.decision_queue.put(framework_request)
        response = self._wait_for_response(framework_request["id"])

        return response["framework"]

    def make_decision(self, task: dict, context: dict) -> dict:
        """请求人类决策"""

        decision_request = {
            "task_id": task["task_id"],
            "description": task["description"],
            "context": {
                "previous_results": context.get("results", []),
                "summary": self._generate_summary(context)
            },
            "decision_options": self._get_decision_options(task)
        }

        self.decision_queue.put(decision_request)
        response = self._wait_for_response(decision_request["id"])

        return response["decision"]
```

### 3.4 结果合成器 (ResultSynthesizer)

```python
class ResultSynthesizer:
    """结果合成器"""

    def synthesize(self, case_id: str, tasks: list,
                   task_results: list) -> dict:
        """合成最终分析报告"""

        report = {
            "case_id": case_id,
            "metadata": {
                "total_tasks": len(tasks),
                "ai_executed": sum(1 for r in task_results
                                 if not r.get("human_intervention")),
                "human_intervened": sum(1 for r in task_results
                                      if r.get("human_intervention")),
                "avg_confidence": self._calc_avg_confidence(task_results)
            },
            "task_breakdown": [
                {
                    "task_id": t["task_id"],
                    "description": t["description"],
                    "result": r["result"],
                    "confidence": r["confidence"],
                    "human_intervention": r.get("human_intervention", False)
                }
                for t, r in zip(tasks, task_results)
            ],
            "final_conclusion": self._extract_conclusion(task_results),
            "confidence_breakdown": self._generate_confidence_report(task_results),
            "recommendations": self._generate_recommendations(task_results)
        }

        return report

    def _generate_confidence_report(self, results: list) -> dict:
        """生成置信度报告"""
        return {
            "high_confidence": sum(1 for r in results
                                  if isinstance(r.get("confidence"), float)
                                  and r["confidence"] > 0.8),
            "medium_confidence": sum(1 for r in results
                                    if isinstance(r.get("confidence"), float)
                                    and 0.5 <= r["confidence"] <= 0.8),
            "low_confidence": sum(1 for r in results
                                 if isinstance(r.get("confidence"), float)
                                 and r["confidence"] < 0.5),
            "human_verified": sum(1 for r in results
                                 if r.get("confidence") in
                                 ["human_guided", "human_expert"])
        }

    def _generate_recommendations(self, results: list) -> list:
        """生成改进建议"""
        recommendations = []

        # 分析低置信度任务
        low_conf_tasks = [
            r for r in results
            if isinstance(r.get("confidence"), float)
            and r["confidence"] < 0.6
        ]

        if low_conf_tasks:
            recommendations.append({
                "type": "low_confidence",
                "message": f"发现{len(low_conf_tasks)}个低置信度任务，建议人工复核",
                "task_ids": [t["task_id"] for t in low_conf_tasks]
            })

        # 分析人类干预点
        human_tasks = [
            r for r in results
            if r.get("human_intervention")
        ]

        if human_tasks:
            recommendations.append({
                "type": "human_intervention",
                "message": f"{len(human_tasks)}个任务需要人类介入",
                "task_ids": [t["task_id"] for t in human_tasks]
            })

        return recommendations
```

---

## 四、实际应用场景

### 4.1 新颖性分析工作流

```python
# 新颖性分析任务分解
case = {
    "case_id": "CN1234567A",
    "background": "...案由描述...",
    "case_type": "novelty"
}

# 分解任务
tasks = decomposer.decompose(case, case_type="novelty")

# 执行工作流
context = {}
results = []

for task in tasks:
    print(f"\n执行任务: {task['description']}")
    print(f"任务类型: {task['type']}")

    result = executor.execute_task(task, context)
    results.append(result)

    # 更新上下文
    context[f"task_{task['task_id']}"] = result

    # 如果是人类决策点，等待确认
    if task['type'] == 'HUMAN_DECISION':
        print(f"✓ 人类已决策: {result['result']}")
    else:
        print(f"✓ 完成 (置信度: {result['confidence']})")

# 合成最终报告
report = synthesizer.synthesize(case['case_id'], tasks, results)
```

### 4.2 任务分配策略

```
┌─────────────────────────────────────────────────────────────┐
│  案例批量处理 - 智能任务分配                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  待处理案例队列:                                             │
│  ┌──────┬──────┬──────┬──────┬──────┐                       │
│  │ 案例1│ 案例2│ 案例3│ 案例4│ 案例5│                       │
│  └──┬───┴──┬───┴──┬───┴──┬───┴──┬───┘                       │
│     │      │      │      │      │                            │
│     ↓      ↓      ↓      ↓      ↓                            │
│  ┌──────────────────────────────────────────────┐            │
│  │  任务分解器                                  │            │
│  │  案例1 → 4个任务 (AI自动:2, 人类决策:1)     │            │
│  │  案例2 → 4个任务 (AI自动:1, 人类决策:2)     │            │
│  └──────────────────────────────────────────────┘            │
│     │      │      │      │      │                            │
│     ↓      ↓      ↓      ↓      ↓                            │
│  ┌──────────────────────────────────────────────┐            │
│  │  智能任务分配器                              │            │
│  │  - AI任务 → 自动处理池 (并行)               │            │
│  │  - 人类任务 → 待分配队列 (优先级排序)       │            │
│  └──────────────────────────────────────────────┘            │
│                                                              │
│  AI自动处理池:     人类专家队列:                              │
│  ┌─────┬─────┐    ┌────────────────────┐                   │
│  │任务A │任务B │    │ 1. 案例2最终结论   │ ← 高优先级        │
│  │(自动)│(自动)│    │ 2. 案例1最终结论   │                   │
│  └──┬──┴──┬──┘    │ 3. 案例3框架设定   │                   │
│     │     │       └────────────────────┘                   │
│     ↓     ↓                                                  │
│  ┌──────────────────────────────────────┐                   │
│  │  结果汇总                            │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 五、系统优势

### 5.1 效率提升

| 任务类型 | 传统方式 | 人机协作 | 提升 |
|---------|---------|---------|------|
| 案例分类 | 30分钟 | 2分钟 (AI) | 15x |
| 证据提取 | 60分钟 | 5分钟 (AI) | 12x |
| 对比分析 | 120分钟 | 30分钟 (AI+复核) | 4x |
| 最终结论 | 60分钟 | 30分钟 (人类决策) | 2x |
| **总计** | **270分钟** | **67分钟** | **4x** |

### 5.2 质量保证

```
多层次验证机制:

Level 1: AI自动验证 (规则/正则)
  ✓ 格式正确性
  ✓ 字段完整性

Level 2: LLM交叉验证
  ✓ 逻辑一致性
  ✓ 内容相关性

Level 3: 人类专家审核
  ✓ 关键决策点
  ✓ 低置信度任务
  ✓ 最终结论

Level 4: 双人复核 (重要案件)
  ✓ 高价值案件
  ✓ 复杂法律问题
```

### 5.3 可解释性

```
每个案例的分析报告包含:

1. 任务执行轨迹
   - 哪些任务由AI完成
   - 哪些任务经过人类复核
   - 每个任务的置信度

2. 决策依据
   - 使用的法律条款
   - 对比的证据
   - 推理过程

3. 置信度报告
   - 高置信度任务: X个
   - 中置信度任务: Y个
   - 低置信度任务: Z个 (需要关注)

4. 改进建议
   - 哪些任务需要人工复核
   - 哪些环节可以优化
```

---

## 六、实施路线图

### Phase 1: 基础框架 (2周)
- [x] 任务分解器原型
- [ ] 任务执行器原型
- [ ] 简单人类交互界面
- [ ] 结果合成器原型

### Phase 2: 核心功能 (4周)
- [ ] AI自动任务模块
- [ ] 人类交互界面完善
- [ ] 验证器注册表
- [ ] DSPy集成 (可选AI加速)

### Phase 3: 集成优化 (2周)
- [ ] 与现有系统集成
- [ ] 批量处理能力
- [ ] 性能优化
- [ ] 用户测试

### Phase 4: 高级功能 (按需)
- [ ] 智能任务分配
- [ ] 优先级队列
- [ ] 反馈学习机制
- [ ] 多人协作

---

## 七、关键代码示例

### 7.1 完整工作流示例

```python
# 1. 初始化系统
decomposer = PatentTaskDecomposer()
executor = PatentTaskExecutor()
synthesizer = ResultSynthesizer()

# 2. 加载案例
case = load_case("CN1234567A_novelty.json")

# 3. 任务分解
tasks = decomposer.decompose(case, case_type="novelty")
print(f"分解为 {len(tasks)} 个任务")

# 4. 执行任务
results = []
context = {"case_info": case}

for task in tasks:
    print(f"\n[{task['sequence']+1}/{len(tasks)}] {task['description']}")
    print(f"类型: {task['type']}")

    if task['type'] == 'AI_AUTOMATIC':
        # AI自动执行
        result = executor.execute_task(task, context)
        print(f"✓ 完成 (置信度: {result['confidence']:.2%})")

    elif task['type'] == 'HUMAN_DECISION':
        # 人类决策
        print("⏳ 等待专家决策...")
        result = executor.execute_task(task, context)
        print(f"✓ 专家已决策: {result['result']}")

    results.append(result)
    context[f"task_{task['task_id']}"] = result

# 5. 生成报告
report = synthesizer.synthesize(case['case_id'], tasks, results)

# 6. 输出报告
print("\n" + "="*70)
print("分析报告")
print("="*70)
print(f"案例ID: {report['case_id']}")
print(f"总任务数: {report['metadata']['total_tasks']}")
print(f"AI执行: {report['metadata']['ai_executed']}")
print(f"人类介入: {report['metadata']['human_intervened']}")
print(f"平均置信度: {report['metadata']['avg_confidence']:.2%}")
print("\n最终结论:")
print(report['final_conclusion'])
print("\n置信度分布:")
for key, value in report['confidence_breakdown'].items():
    print(f"  - {key}: {value}")

if report['recommendations']:
    print("\n建议:")
    for rec in report['recommendations']:
        print(f"  - {rec['message']}")
```

---

## 八、总结

本架构通过**任务分解**和**人机分工**，将复杂的专利分析工作拆解为：

1. **AI擅长**的机械性任务 (自动执行)
2. **AI辅助**的分析任务 (人类验证)
3. **人类决策**的关键任务 (专家把关)

既发挥了AI的**效率优势**，又保留了人类的**决策价值**，是更务实的工业级解决方案。

---

**下一步行动**:
1. 评审本架构设计
2. 确认优先实施的功能模块
3. 制定详细的开发计划
