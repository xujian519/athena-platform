# explainable_cognition_module.py 重构计划

**文件**: `core/cognition/explainable_cognition_module.py`
**当前行数**: 1178行
**目标行数**: 每个文件 <500行
**重构日期**: 2026-01-26

---

## 📋 当前文件结构

### 枚举类 (2个)
1. `ReasoningStepType` (48-58行) - 推理步骤类型
2. `FactorImportance` (61-68行) - 因子重要性级别

### 数据类 (3个)
1. `ReasoningStep` (72-103行) - 推理步骤
2. `DecisionFactor` (105-130行) - 决策因子
3. `ReasoningPath` (132-172行) - 推理路径

### 可视化类 (1个)
1. `ReasoningPathVisualizer` (174-350行) - 推理路径可视化器
   - `generate_path_diagram()` - 生成路径图
   - `generate_factor_importance_chart()` - 生成因子重要性图
   - `_hierarchical_layout()` - 分层布局
   - `_get_step_color()` - 获取步骤颜色
   - `_save_to_file()` - 保存到文件

### 主模块类 (1个)
1. `ExplainableCognitionModule` (352-1178行) - 可解释认知模块主类
   - 初始化和配置
   - 推理过程管理
   - 决策因子分析
   - 解释生成
   - 性能监控

---

## 🎯 重构方案

### 新的目录结构

```
core/cognition/explainable/
├── __init__.py           # 公共接口导出
├── types.py              # 枚举和数据类 (约200行)
├── visualizer.py         # 可视化器类 (约200行)
├── core.py               # 核心模块类 (约400行)
└── utils.py              # 工具函数 (约100行)
```

### 文件拆分详情

#### 1. `types.py` - 数据模型 (约200行)

**内容**:
- `ReasoningStepType` 枚举
- `FactorImportance` 枚举
- `ReasoningStep` 数据类
- `DecisionFactor` 数据类
- `ReasoningPath` 数据类

**职责**: 定义所有数据结构，不包含业务逻辑

#### 2. `visualizer.py` - 可视化功能 (约200行)

**内容**:
- `ReasoningPathVisualizer` 类
  - `generate_path_diagram()` - 生成路径图
  - `generate_factor_importance_chart()` - 生成因子重要性图
  - `_hierarchical_layout()` - 分层布局
  - `_get_step_color()` - 获取步骤颜色
  - `_save_to_file()` - 保存到文件

**职责**: 负责所有可视化相关的功能

#### 3. `core.py` - 核心业务逻辑 (约400行)

**内容**:
- `ExplainableCognitionModule` 主类
  - 初始化和配置管理
  - 推理过程核心逻辑
  - 决策因子分析核心方法

**职责**: 核心认知处理逻辑

#### 4. `utils.py` - 工具函数 (约100行)

**内容**:
- 辅助函数
- 性能监控工具
- 日志工具
- 数据验证函数

**职责**: 提供通用工具函数

#### 5. `__init__.py` - 公共接口

**内容**:
```python
# 数据模型
from .types import (
    ReasoningStepType,
    FactorImportance,
    ReasoningStep,
    DecisionFactor,
    ReasoningPath,
)

# 可视化
from .visualizer import ReasoningPathVisualizer

# 核心模块
from .core import ExplainableCognitionModule

__all__ = [
    "ReasoningStepType",
    "FactorImportance",
    "ReasoningStep",
    "DecisionFactor",
    "ReasoningPath",
    "ReasoningPathVisualizer",
    "ExplainableCognitionModule",
]
```

---

## 🔧 重构步骤

### 步骤1: 创建新目录结构
```bash
mkdir -p core/cognition/explainable
touch core/cognition/explainable/__init__.py
touch core/cognition/explainable/types.py
touch core/cognition/explainable/visualizer.py
touch core/cognition/explainable/core.py
touch core/cognition/explainable/utils.py
```

### 步骤2: 提取数据模型到 `types.py`
- 移动所有枚举类
- 移动所有数据类
- 保持原有接口不变

### 步骤3: 提取可视化功能到 `visualizer.py`
- 移动 `ReasoningPathVisualizer` 类
- 保持所有方法不变
- 更新内部导入

### 步骤4: 提取工具函数到 `utils.py`
- 识别所有工具函数
- 移动到 utils.py
- 保持函数签名不变

### 步骤5: 保留核心逻辑在 `core.py`
- 保留 `ExplainableCognitionModule` 主类
- 更新导入路径
- 简化代码逻辑

### 步骤6: 更新 `__init__.py`
- 导出所有公共接口
- 保持向后兼容

### 步骤7: 更新外部导入
- 查找所有使用原模块的文件
- 更新导入路径
- 测试所有功能

### 步骤8: 验证和测试
- 运行所有测试
- 检查类型注解
- 验证功能完整性

---

## ⚠️ 风险评估

### 潜在风险
1. **导入路径变更**: 可能影响其他模块的导入
2. **循环依赖**: 新的模块结构可能引入循环依赖
3. **测试失效**: 需要更新所有相关测试

### 缓解措施
1. **保持向后兼容**: 在原位置保留重定向
2. **逐步迁移**: 先创建新结构，再逐步迁移
3. **充分测试**: 确保所有测试通过

---

## 📊 预期收益

### 代码质量提升
- ✅ 单个文件 <500行
- ✅ 模块职责清晰
- ✅ 代码可读性提升
- ✅ 维护性增强

### 架构改进
- ✅ 更好的模块化
- ✅ 更清晰的依赖关系
- ✅ 更容易测试
- ✅ 更容易扩展

---

## ⏱️ 预估工时

| 任务 | 预估时间 |
|------|---------|
| 创建新目录结构 | 10分钟 |
| 提取数据模型 | 20分钟 |
| 提取可视化功能 | 30分钟 |
| 提取工具函数 | 20分钟 |
| 更新核心逻辑 | 40分钟 |
| 更新导入路径 | 30分钟 |
| 验证和测试 | 30分钟 |
| **总计** | **约3小时** |

---

## ✅ 验收标准

- [ ] 所有新文件 <500行
- [ ] 所有测试通过
- [ ] 无类型注解错误
- [ ] 无循环依赖
- [ ] 功能完全保持一致
- [ ] 性能无明显下降

---

**创建日期**: 2026-01-26
**状态**: 📋 待执行
**优先级**: P1
