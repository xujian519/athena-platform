# Athena工作平台 - 测试覆盖率指南

## 📋 测试概览

平台包含丰富的测试套件：

| 测试类型 | 文件数量 | 说明 |
|---------|---------|------|
| 单元测试 | 800+ | 测试单个函数和类 |
| 集成测试 | 300+ | 测试模块间交互 |
| 性能测试 | 100+ | 测试系统性能 |
| NLP测试 | 60+ | 测试自然语言处理 |

## 🚀 快速开始

### 1. 安装测试依赖

```bash
pip install pytest pytest-cov pytest-asyncio pytest-xdist
```

### 2. 运行所有测试

```bash
# 基础运行
pytest

# 详细输出
pytest -v

# 并行运行
pytest -n auto
```

### 3. 生成覆盖率报告

```bash
# 使用提供的脚本
./generate_coverage_report.sh

# 或手动运行
pytest --cov=. --cov-report=html --cov-report=term
```

### 4. 查看报告

```bash
# 在浏览器中打开HTML报告
open reports/coverage/html/index.html

# Mac系统
open reports/coverage/html/index.html

# Linux系统
xdg-open reports/coverage/html/index.html
```

## 📊 覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|---------|
| 核心模块 | 80%+ | 待测试 |
| API服务 | 85%+ | 待测试 |
| NLP模块 | 75%+ | 待测试 |
| 数据库层 | 90%+ | 待测试 |
| 工具函数 | 70%+ | 待测试 |

## 🔧 测试命令

### 运行特定测试

```bash
# 测试单个文件
pytest dev/tests/test_specific.py

# 测试特定目录
pytest dev/tests/unit/

# 测试特定函数
pytest dev/tests/test_module.py::test_function

# 使用关键字匹配
pytest -k "test_api"
```

### 带标记的测试

```bash
# 只运行快速测试
pytest -m fast

# 跳过慢速测试
pytest -m "not slow"

# 运行集成测试
pytest -m integration
```

### 调试测试

```bash
# 失败时进入pdb
pytest --pdb

# 显示打印输出
pytest -s

# 在第一个失败时停止
pytest -x

# 显示本地变量
pytest -l
```

## 📈 CI/CD集成

### GitHub Actions示例

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements-unified.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 💡 最佳实践

1. **测试命名**: 使用描述性的测试名称
   ```python
   def test_user_login_with_valid_credentials():
       pass
   ```

2. **使用fixtures**: 复用测试数据
   ```python
   @pytest.fixture
   def test_user():
       return User(name="测试用户")
   ```

3. **测试隔离**: 每个测试应该独立运行

4. **Mock外部依赖**: 使用pytest-mock
   ```python
   from unittest.mock import Mock
   def test_with_mock(mocker):
       mock_func = mocker.patch('module.function')
       mock_func.return_value = 42
   ```

5. **参数化测试**: 使用参数化减少重复
   ```python
   @pytest.mark.parametrize("input,expected", [
       (1, 2),
       (2, 4),
       (3, 6),
   ])
   def test_multiply(input, expected):
       assert multiply(input, 2) == expected
   ```

## 🔗 相关资源

- [pytest文档](https://docs.pytest.org/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- 测试脚本: `./generate_coverage_report.sh`
- 测试目录: `dev/tests/`
