# 提示词优化系统使用指南

> 版本: v1.0 | 作者: 小诺·双鱼公主 | 日期: 2026-04-05

## 一、快速开始

### 1.1 安装依赖

```python
# 无需额外依赖，使用标准库
from core.prompts import get_prompt, get_minimal_prompt
```

### 1.2 获取提示词

```python
# 最小上下文（~5K tokens）- 用于初始对话
prompt = get_minimal_prompt()

# 专利撰写任务（~15K tokens）
prompt = get_prompt(task_type="patent_writing", complexity="medium")

# OA答复任务（~25K tokens）
prompt = get_prompt(task_type="office_action", complexity="complex")
```

## 二、优化效果

### 2.1 Token消耗对比

| 场景 | 原始 | 优化后 | 节省 |
|------|------|--------|------|
| 全部加载 | ~125K | - | - |
| 最小上下文 | - | ~1.7K | **98.6%** |
| 专利撰写 | - | ~15K | 88.0% |
| OA答复 | - | ~25K | 80.0% |

### 2.2 关键指标

```
✅ Token节省: 98.6%
✅ 缓存命中率: 60%+
✅ 加载速度: <1ms (缓存命中)
```

## 三、API参考

### 3.1 核心函数

```python
# 获取完整提示词
def get_prompt(
    task_type: str = "general",      # 任务类型
    complexity: str = "medium",      # 复杂度
    domain: str = "general",         # 领域
    include_data_layer: bool = False # 是否包含数据层
) -> str

# 获取最小上下文
def get_minimal_prompt() -> str

# 获取能力层
def get_capability_prompt(capabilities: list[str]) -> str

# 获取业务层
def get_business_prompt(task_type: str) -> str

# 评估提示词质量
def evaluate_prompt(prompt: str) -> QualityReport
```

### 3.2 任务类型

```python
TASK_TYPES = [
    "general",            # 通用
    "patent_writing",     # 专利撰写
    "office_action",      # 审查意见答复
    "invalidity",         # 无效宣告
    "prior_art_search",   # 现有技术检索
    "claims_analysis",    # 权利要求分析
]
```

### 3.3 复杂度级别

```python
COMPLEXITY_LEVELS = [
    "simple",    # 简单查询
    "medium",    # 标准任务
    "complex",   # 复杂任务（OA答复等）
]
```

## 四、最佳实践

### 4.1 分阶段加载

```python
# 阶段1: 初始对话 - 最小上下文
system_prompt = get_minimal_prompt()

# 阶段2: 识别任务类型后 - 按需加载
if task_type == "patent_writing":
    # 加载专利撰写相关能力
    capability_prompt = get_capability_prompt(["retrieval", "analysis", "writing"])
    system_prompt += "\n" + capability_prompt

# 阶段3: 执行具体任务时 - 加载业务层
business_prompt = get_business_prompt("patent_writing")
system_prompt += "\n" + business_prompt
```

### 4.2 缓存利用

```python
# 相同任务类型会自动缓存
# 第一次调用会加载，后续调用直接返回缓存结果

for i in range(10):
    # 只有第一次会加载，后续9次都是缓存命中
    prompt = get_prompt(task_type="patent_writing")
```

### 4.3 质量评估

```python
from core.prompts import evaluate_prompt

# 评估提示词质量
report = evaluate_prompt(my_prompt)

print(f"总分: {report.overall_score:.1%}")
print(f"清晰度: {report.clarity.score:.1%}")
print(f"完整性: {report.completeness.score:.1%}")

# 查看优化建议
for rec in report.recommendations:
    print(f"- {rec}")
```

## 五、文件结构

```
core/prompts/
├── __init__.py              # 统一入口
├── progressive_loader.py    # 渐进式加载器
├── quality_evaluator.py     # 质量评估器
└── test_optimization.py     # 测试脚本

prompts/
├── foundation/
│   ├── xiaona_core_v3_compressed.md  # 小娜核心（精简版）
│   ├── xiaonuo_core_v3_compressed.md # 小诺核心（精简版）
│   └── hitl_protocol_v3_mandatory.md # HITL协议
├── capability/
│   ├── cap01_retrieval.md
│   ├── cap02_analysis.md
│   └── ...
└── business/
    ├── task_1_1_understand_disclosure.md
    ├── task_2_1_analyze_office_action.md
    └── ...
```

## 六、常见问题

### Q1: 为什么初始tokens这么少？

A: 使用渐进式加载，初始只加载最小上下文（~1.7K tokens），按需加载更多内容。

### Q2: 如何调整压缩比？

A: 创建加载器时指定 `compression_ratio` 参数：

```python
loader = ProgressivePromptLoader(
    prompts_dir="prompts",
    compression_ratio=0.3,  # 更激进的压缩
)
```

### Q3: 缓存在哪里？

A: 默认在 `/tmp/prompt_cache/`，可通过 `cache_dir` 参数指定。

## 七、性能监控

```python
from core.prompts import get_system_stats

stats = get_system_stats()
print(f"缓存统计: {stats['cache_stats']}")
print(f"核心缓存大小: {stats['core_cache_size']}")
```

---

*最后更新: 2026-04-05*
