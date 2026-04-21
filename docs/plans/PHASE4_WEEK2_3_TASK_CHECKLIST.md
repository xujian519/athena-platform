# Phase 4 Week 2-3 任务清单与检查清单

> **时间范围**: Week 2-3 (14天)
> **目标**: 覆盖率 6.64% → 15%+
> **策略**: 优先补充简单模块测试

---

## 📋 总体任务清单

### 优先级P0 - 已完成 ✅
- [x] core/utils/json_utils.py (22 tests, 84.62%)
- [x] core/utils/path_utils.py (23 tests, 91.18%)
- [x] core/errors/exceptions.py (39 tests, 99.39%)

### 优先级P1 - 简单工具模块（Week 2）
- [ ] core/utils/time_utils.py - 时间工具函数
- [ ] core/utils/common_functions.py - 通用函数
- [ ] core/utils/decorator_utils.py - 装饰器工具
- [ ] core/utils/paths.py - 路径处理
- [ ] core/utils/retry_utils.py - 重试机制
- [ ] core/utils/task_manager.py - 任务管理

### 优先级P2 - 中等复杂度模块（Week 2-3）
- [ ] core/utils/agent_identity_manager.py - Agent身份管理
- [ ] core/utils/error_handler.py - 错误处理
- [ ] core/utils/error_handling.py - 错误处理
- [ ] core/utils/safe_evaluator.py - 安全求值
- [ ] core/utils/backup_manager.py - 备份管理

### 优先级P3 - 复杂模块（Week 3）
- [ ] core/utils/api_helpers.py - API辅助函数
- [ ] core/utils/async_file_utils.py - 异步文件操作
- [ ] core/utils/ocr_patent_parser.py - OCR专利解析
- [ ] core/utils/patent_data_importer.py - 专利数据导入
- [ ] core/utils/patent_data_manager.py - 专利数据管理
- [ ] core/utils/patent_pdf_parser.py - 专利PDF解析
- [ ] core/utils/retry_mechanism.py - 重试机制

### 优先级P4 - errors和validation模块（Week 3）
- [ ] core/errors/error_handler.py - 错误处理器
- [ ] core/errors/handlers.py - 处理器集合
- [ ] core/validation/realtime_parameter_validator.py - 实时参数验证
- [ ] core/validation/realtime_validator_module.py - 实时验证模块
- [ ] core/validation/unified_parameter_validator.py - 统一参数验证

---

## 📊 每日任务分配（建议）

### Week 2 Day 1: time_utils + common_functions
- [ ] 读取并分析 time_utils.py
- [ ] 创建 test_time_utils.py
- [ ] 运行测试并验证
- [ ] 读取并分析 common_functions.py
- [ ] 创建 test_common_functions.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 2 Day 2: decorator_utils + paths
- [ ] 读取并分析 decorator_utils.py
- [ ] 创建 test_decorator_utils.py
- [ ] 运行测试并验证
- [ ] 读取并分析 paths.py
- [ ] 创建 test_paths.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 2 Day 3: retry_utils + task_manager
- [ ] 读取并分析 retry_utils.py
- [ ] 创建 test_retry_utils.py
- [ ] 运行测试并验证
- [ ] 读取并分析 task_manager.py
- [ ] 创建 test_task_manager.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 2 Day 4: agent_identity_manager + error_handler
- [ ] 读取并分析 agent_identity_manager.py
- [ ] 创建 test_agent_identity_manager.py
- [ ] 运行测试并验证
- [ ] 读取并分析 error_handler.py
- [ ] 创建 test_error_handler.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 2 Day 5: error_handling + safe_evaluator
- [ ] 读取并分析 error_handling.py
- [ ] 创建 test_error_handling.py
- [ ] 运行测试并验证
- [ ] 读取并分析 safe_evaluator.py
- [ ] 创建 test_safe_evaluator.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 3 Day 1: backup_manager + api_helpers
- [ ] 读取并分析 backup_manager.py
- [ ] 创建 test_backup_manager.py
- [ ] 运行测试并验证
- [ ] 读取并分析 api_helpers.py
- [ ] 创建 test_api_helpers.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 3 Day 2: async_file_utils + retry_mechanism
- [ ] 读取并分析 async_file_utils.py
- [ ] 创建 test_async_file_utils.py
- [ ] 运行测试并验证
- [ ] 读取并分析 retry_mechanism.py
- [ ] 创建 test_retry_mechanism.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 3 Day 3: errors模块
- [ ] 读取并分析 error_handler.py
- [ ] 创建 test_error_handler_errors.py
- [ ] 运行测试并验证
- [ ] 读取并分析 handlers.py
- [ ] 创建 test_handlers.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 3 Day 4: validation模块
- [ ] 读取并分析 realtime_parameter_validator.py
- [ ] 创建 test_realtime_parameter_validator.py
- [ ] 运行测试并验证
- [ ] 读取并分析 realtime_validator_module.py
- [ ] 创建 test_realtime_validator_module.py
- [ ] 运行测试并验证
- [ ] Git提交

### Week 3 Day 5: 统一参数验证 + 收尾
- [ ] 读取并分析 unified_parameter_validator.py
- [ ] 创建 test_unified_parameter_validator.py
- [ ] 运行测试并验证
- [ ] 运行完整覆盖率测试
- [ ] 生成覆盖率报告
- [ ] 创建Week 2-3总结报告
- [ ] Git提交

---

## ✅ 测试编写检查清单

### 第一步：模块分析
- [ ] 读取目标模块的完整代码
- [ ] 理解模块的主要功能和API
- [ ] 识别所有公开函数和类
- [ ] 识别依赖关系和外部调用
- [ ] 评估模块复杂度

### 第二步：测试设计
- [ ] 列出所有需要测试的函数/类
- [ ] 为每个函数设计测试用例：
  - [ ] 正常情况测试
  - [ ] 边缘情况测试
  - [ ] 错误情况测试
  - [ ] 集成测试
- [ ] 确定测试优先级
- [ ] 估算测试数量

### 第三步：测试实现
- [ ] 创建测试文件：tests/core/[module]/test_[filename].py
- [ ] 按功能分组测试类
- [ ] 实现测试用例
- [ ] 添加必要的fixtures
- [ ] 添加清晰的测试文档字符串

### 第四步：测试验证
- [ ] 运行测试：pytest tests/core/[module]/test_[filename].py -v
- [ ] 确保所有测试通过
- [ ] 运行覆盖率测试
- [ ] 检查覆盖率是否>80%
- [ ] 修复失败的测试

### 第五步：代码质量
- [ ] 检查代码风格（ruff）
- [ ] 检查类型注解
- [ ] 检查文档字符串
- [ ] 确保测试独立（无依赖）
- [ ] 确保测试可重复

### 第六步：文档和提交
- [ ] 更新任务清单
- [ ] 记录测试数量和覆盖率
- [ ] Git add修改的文件
- [ ] Git commit（使用规范格式）
- [ ] 更新每日总结文档

---

## 🎯 测试质量标准

### 代码覆盖率要求
- **简单模块**: >90% 覆盖率
- **中等模块**: >80% 覆盖率
- **复杂模块**: >70% 覆盖率

### 测试用例要求
- 每个公开函数至少3个测试用例
- 覆盖正常、异常、边缘情况
- 测试命名清晰描述测试内容
- 测试独立且可重复

### 文档要求
- 每个测试类有文档字符串
- 复杂测试有注释说明
- 测试文件顶部有模块说明

---

## 📈 进度跟踪

### 覆盖率目标
| 阶段 | 当前覆盖率 | 目标覆盖率 | 差距 |
|------|-----------|-----------|------|
| Week 1结束 | 6.64% | 6.64% | - |
| Week 2结束 | ? | 10% | +3.36% |
| Week 3结束 | ? | 15% | +5% |

### 测试数量目标
| 阶段 | 已有测试 | 新增测试 | 总计 |
|------|---------|---------|------|
| Week 1结束 | 311 | 84 | 395 |
| Week 2结束 | 395 | +150 | 545 |
| Week 3结束 | 545 | +150 | 695 |

---

## 🚀 快速开始

### 开始第一个任务
```bash
# 1. 读取模块
cat core/utils/time_utils.py

# 2. 创建测试文件
touch tests/core/utils/test_time_utils.py

# 3. 编写测试
# （根据模块内容编写测试）

# 4. 运行测试
poetry run pytest tests/core/utils/test_time_utils.py -v

# 5. 检查覆盖率
poetry run pytest tests/core/utils/test_time_utils.py --cov=core.utils.time_utils --cov-report=term-missing
```

### 批量运行测试
```bash
# 运行所有utils测试
poetry run pytest tests/core/utils/ -v

# 运行所有errors测试
poetry run pytest tests/core/errors/ -v

# 运行所有validation测试
poetry run pytest tests/core/validation/ -v
```

---

## 💡 最佳实践

### 测试命名规范
```python
class TestFunctionName:  # 测试类：被测试的函数名
    def test_normal_case(self):  # 测试方法：场景描述
        """测试正常情况"""
        pass

    def test_edge_case_empty_input(self):  # 测试方法：具体边缘情况
        """测试空输入情况"""
        pass

    def test_error_case_invalid_type(self):  # 测试方法：具体错误情况
        """测试无效类型错误"""
        pass
```

### Git提交规范
```
test: 添加time_utils.py测试

- 新增25个测试用例
- 覆盖率：92%
- 测试时间、格式化、解析等功能

相关模块: core/utils/time_utils.py
```

### 每日工作流
1. 晨会：查看今日任务
2. 执行：按检查清单执行
3. 验证：运行测试和覆盖率
4. 提交：Git commit和文档更新
5. 总结：更新进度跟踪

---

**创建时间**: 2026-04-21 17:30
**创建者**: Claude Code
**状态**: 准备执行
**下一步**: 开始Week 2 Day 1任务
