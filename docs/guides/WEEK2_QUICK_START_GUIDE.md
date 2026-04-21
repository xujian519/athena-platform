# Phase 4 Week 2 快速启动指南

> **开始时间**: 建议从Week 2 Day 1开始
> **预计用时**: 10个工作日
> **目标**: 覆盖率 6.64% → 10%+

---

## 🚀 立即开始

### 方式1: 自动化执行（推荐）
```bash
# 使用OMC自动化执行
cd /Users/xujian/Athena工作平台

# Week 2 Day 1任务已在任务队列中
# 查看任务: #67
```

### 方式2: 手动执行
```bash
# 1. 查看任务清单
cat docs/plans/PHASE4_WEEK2_3_TASK_CHECKLIST.md

# 2. 开始第一个任务
# Week 2 Day 1: time_utils + common_functions

# 读取模块
cat core/utils/time_utils.py

# 创建测试文件
touch tests/core/utils/test_time_utils.py

# 编写测试（参考已完成的test_json_utils.py和test_path_utils.py）

# 运行测试
poetry run pytest tests/core/utils/test_time_utils.py -v

# 检查覆盖率
poetry run pytest tests/core/utils/test_time_utils.py --cov=core.utils.time_utils --cov-report=term-missing
```

---

## 📋 Week 2任务概览

### Day 1: time_utils + common_functions
- **模块**: time_utils.py, common_functions.py
- **难度**: ⭐ 简单
- **预计测试**: 45个
- **预计时间**: 2小时

### Day 2: decorator_utils + paths
- **模块**: decorator_utils.py, paths.py
- **难度**: ⭐⭐ 中等
- **预计测试**: 50个
- **预计时间**: 2.5小时

### Day 3: retry_utils + task_manager
- **模块**: retry_utils.py, task_manager.py
- **难度**: ⭐⭐ 中等
- **预计测试**: 55个
- **预计时间**: 2.5小时

### Day 4: agent_identity_manager + error_handler
- **模块**: agent_identity_manager.py, error_handler.py
- **难度**: ⭐⭐⭐ 较复杂
- **预计测试**: 60个
- **预计时间**: 3小时

### Day 5: error_handling + safe_evaluator
- **模块**: error_handling.py, safe_evaluator.py
- **难度**: ⭐⭐⭐ 较复杂
- **预计测试**: 65个
- **预计时间**: 3小时

---

## ✅ 测试编写模板

### 模板1: 简单函数测试
```python
#!/usr/bin/env python3
"""模块名称测试"""

import pytest
from core.utils.module_name import function_name, ClassName


class TestFunctionName:
    """function_name函数测试"""

    def test_normal_case(self):
        """测试正常情况"""
        result = function_name(normal_input)
        assert result == expected_output

    def test_edge_case_empty(self):
        """测试空输入"""
        result = function_name("")
        assert result is None  # 或其他期望值

    def test_error_case_invalid_type(self):
        """测试无效类型"""
        with pytest.raises(TypeError):
            function_name(invalid_input)


class TestClassName:
    """ClassName类测试"""

    def test_initialization(self):
        """测试初始化"""
        obj = ClassName(param1="value1")
        assert obj.param1 == "value1"

    def test_method(self):
        """测试方法"""
        obj = ClassName()
        result = obj.method_name()
        assert result == expected
```

### 模板2: 复杂类测试
```python
class TestComplexClass:
    """复杂类测试"""

    @pytest.fixture
    def instance(self):
        """创建测试实例"""
        return ComplexClass(config={"key": "value"})

    def test_method_normal(self, instance):
        """测试正常方法调用"""
        result = instance.method(input_data)
        assert result.status == "success"

    def test_method_with_mock(self, instance, mocker):
        """测试带Mock的方法"""
        mock_func = mocker.patch('core.utils.module.external_func')
        mock_func.return_value = mocked_value

        result = instance.method()
        assert mock_func.called
```

---

## 🎯 质量检查清单

### 代码质量
- [ ] 所有测试通过（pytest -v）
- [ ] 覆盖率达标（简单>90%, 中等>80%, 复杂>70%）
- [ ] 代码风格检查通过（ruff check）
- [ ] 类型注解正确
- [ ] 文档字符串完整

### Git提交
- [ ] 修改的文件已添加
- [ ] 提交信息规范
- [ ] 包含测试数量和覆盖率
- [ ] 相关文档已更新

### 文档更新
- [ ] 任务清单已更新
- [ ] 进度跟踪已更新
- [ ] 每日总结已创建

---

## 📊 进度跟踪

### 实时查看进度
```bash
# 查看所有测试
poetry run pytest tests/ --collect-only -q | wc -l

# 查看覆盖率
poetry run pytest tests/ --cov=core --cov-report=term | grep "TOTAL"

# 查看今日新增测试
git diff --stat HEAD~1 tests/core/utils/
```

### 更新进度
```bash
# 每日结束时更新
echo "## Week 2 Day X 进度" >> docs/reports/WEEK2_DAILY_LOG.md
echo "- 完成模块: module1, module2" >> docs/reports/WEEK2_DAILY_LOG.md
echo "- 新增测试: XX个" >> docs/reports/WEEK2_DAILY_LOG.md
echo "- 覆盖率: XX%" >> docs/reports/WEEK2_DAILY_LOG.md
```

---

## 🆘 常见问题

### Q1: 如何确定测试用例数量？
**A**:
- 简单函数: 3-5个测试
- 复杂函数: 5-10个测试
- 类: 每个方法3-5个测试
- 总计: 大约代码行数的30-50%

### Q2: 如何处理依赖外部服务的函数？
**A**:
- 使用pytest.mock模拟外部服务
- 或者创建integration测试（标记为integration）
- 或者跳过这些函数（标记为skip）

### Q3: 测试失败怎么办？
**A**:
1. 查看错误信息
2. 检查测试代码是否有误
3. 检查被测试的代码是否有bug
4. 如果是代码bug，修复代码
5. 如果是测试问题，修复测试

### Q4: 如何提高覆盖率？
**A**:
1. 运行`pytest --cov-report=html`生成HTML报告
2. 打开htmlcov/index.html查看未覆盖的行
3. 为这些行添加测试
4. 重点关注分支条件、异常处理

### Q5: 测试执行太慢怎么办？
**A**:
1. 使用pytest.mark.skip标记慢速测试
2. 使用pytest-xdist并行执行
3. 将慢速测试移到integration目录
4. 使用mock替代真实IO操作

---

## 📞 获取帮助

### 查看已完成的示例
```bash
# 查看已完成的测试
cat tests/core/utils/test_json_utils.py
cat tests/core/utils/test_path_utils.py
cat tests/core/errors/test_exceptions.py
```

### 查看任务清单
```bash
# 查看完整任务清单
cat docs/plans/PHASE4_WEEK2_3_TASK_CHECKLIST.md

# 查看Week 1总结
cat docs/reports/PHASE4_WEEK1_FINAL_SUMMARY_20260421.md
```

### 查看Git历史
```bash
# 查看最近的提交
git log --oneline -10

# 查看特定提交
git show 95b1353d  # Day 3提交
```

---

## 🎉 开始编码！

### 第一步：选择任务
```bash
# 查看今日任务
# Week 2 Day 1: time_utils + common_functions
```

### 第二步：读取模块
```bash
# 读取模块代码
cat core/utils/time_utils.py
```

### 第三步：编写测试
```bash
# 创建测试文件
vim tests/core/utils/test_time_utils.py
# 或使用你喜欢的编辑器
```

### 第四步：运行验证
```bash
# 运行测试
poetry run pytest tests/core/utils/test_time_utils.py -v

# 检查覆盖率
poetry run pytest tests/core/utils/test_time_utils.py --cov=core.utils.time_utils --cov-report=term-missing
```

### 第五步：提交代码
```bash
# 添加文件
git add tests/core/utils/test_time_utils.py

# 提交
git commit -m "test: 添加time_utils.py测试

- 新增XX个测试用例
- 覆盖率：XX%
- 测试功能：[列出主要功能]

相关模块: core/utils/time_utils.py"
```

---

**准备好了吗？让我们开始Week 2的工作！** 🚀

**记住**：
- 每天完成2个模块
- 质量优于数量
- 测试驱动发现bug
- 保持代码简洁

**祝你好运！** 💪
