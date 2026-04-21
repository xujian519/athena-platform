# CI/CD测试管道设置指南

> **创建时间**: 2026-04-21  
> **状态**: ✅ 已完成

---

## 📊 概述

Athena平台已配置完整的CI/CD测试管道，包括：

- ✅ GitHub Actions工作流
- ✅ Pre-commit hooks
- ✅ 本地测试脚本
- ✅ 覆盖率报告
- ✅ 质量门禁

---

## 🚀 GitHub Actions工作流

### 主要工作流文件

#### 1. test-pipeline.yml（主测试管道）

**位置**: `.github/workflows/test-pipeline.yml`

**触发条件**:
- Push到main或develop分支
- Pull Request创建/更新
- 手动触发

**包含作业**:

| 作业 | 说明 | 超时 |
|------|------|------|
| unit-tests | 单元测试（快速） | 15分钟 |
| integration-tests | 集成测试（需要PostgreSQL+Redis） | 20分钟 |
| code-quality | 代码质量检查（Ruff+Mypy） | 10分钟 |
| coverage-summary | 覆盖率汇总 | - |
| quality-gate | 质量门禁检查 | - |

**运行命令**:
```bash
# 单元测试
poetry run pytest tests/ -m unit -v \
  --cov=core \
  --cov-report=xml \
  --cov-report=term-missing \
  --cov-report=html

# 集成测试
poetry run pytest tests/ -m integration -v

# 代码质量检查
poetry run ruff check . --select=E9,F63,F7,F82
poetry run mypy core/ --ignore-missing-imports
```

#### 2. test-coverage.yml（覆盖率报告）

**位置**: `.github/workflows/test-coverage.yml`

**功能**:
- 生成覆盖率报告
- 上传覆盖率XML
- 70%覆盖率阈值（警告，不阻塞）

---

## 🔧 Pre-commit Hooks

### 配置文件

**位置**: `.pre-commit-config.yaml`

### 包含的Hook

| Hook | 功能 | 自动修复 |
|------|------|---------|
| Ruff语法检查 | 检查语法错误 | ❌ |
| Ruff代码检查 | 检查代码风格 | ✅ |
| Ruff格式化 | 代码格式化 | ✅ |
| Mypy类型检查 | 类型检查 | ❌ |
| JSON/YAML/TOML检查 | 配置文件验证 | ❌ |
| 大文件检查 | 防止>1MB文件 | ❌ |
| 调试语句检查 | 防止提交debug代码 | ❌ |

### 安装步骤

```bash
# 1. 安装pre-commit
pip install pre-commit

# 2. 安装hooks
pre-commit install

# 3. 手动运行所有hooks
pre-commit run --all-files

# 4. 运行特定hook
pre-commit run ruff --files core/llm/unified_llm_manager.py
```

### 配置更新

**更新到最新版本**:
```bash
pre-commit autoupdate
```

**跳过hooks（不推荐）**:
```bash
git commit --no-verify -m "临时跳过hooks"
```

---

## 🧪 本地测试脚本

### 测试运行脚本

**位置**: `scripts/run_tests.sh`

### 使用方法

```bash
# 显示帮助
./scripts/run_tests.sh --help

# 运行所有测试
./scripts/run_tests.sh

# 只运行单元测试
./scripts/run_tests.sh --unit

# 只运行集成测试
./scripts/run_tests.sh --integration

# 生成覆盖率报告
./scripts/run_tests.sh --coverage

# 排除慢速测试
./scripts/run_tests.sh --mark "not slow"

# 运行特定目录的测试
./scripts/run_tests.sh tests/core/llm/

# 并行运行测试
./scripts/run_tests.sh --parallel

# 详细输出
./scripts/run_tests.sh --verbose
```

### 常用命令组合

```bash
# 快速测试（单元测试，无覆盖率）
./scripts/run_tests.sh -u

# 完整测试（所有测试+覆盖率）
./scripts/run_tests.sh -c

# CI模拟（单元测试+集成测试+覆盖率）
./scripts/run_tests.sh -c -k

# 开发快速反馈（单元测试+并行）
./scripts/run_tests.sh -u -n
```

---

## 📈 覆盖率报告

### 生成覆盖率

```bash
# 生成HTML报告
poetry run pytest --cov=core --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 覆盖率目标

| 模块 | 当前覆盖率 | 目标 | 状态 |
|------|-----------|------|------|
| unified_llm_manager.py | 70.11% | >80% | ⚠️ 接近 |
| base_agent.py | 82.67% | >80% | ✅ 达成 |
| enhanced_memory_system.py | 61.43% | >70% | ⚠️ 需改进 |

### 提升覆盖率

**优先级**:
1. 核心模块（agents, llm, memory）
2. 工具模块（tools, execution）
3. 业务模块（patent, legal）

---

## 🔍 质量门禁

### 检查项

| 检查项 | 阻塞 | 说明 |
|--------|------|------|
| 单元测试通过 | ✅ 是 | 必须通过 |
| 集成测试通过 | ❌ 否 | 允许失败 |
| 代码质量检查 | ❌ 否 | 警告级别 |
| 覆盖率阈值 | ❌ 否 | 70%警告 |

### 质量指标

**通过标准**:
- ✅ 所有单元测试通过
- ⚠️ 覆盖率 ≥ 70%
- ⚠️ 无关键安全问题
- ⚠️ 无语法错误

---

## 🎯 开发工作流

### 推荐流程

1. **开发新功能**
   ```bash
   # 创建功能分支
   git checkout -b feature/new-function
   
   # 开发代码...
   ```

2. **本地测试**
   ```bash
   # 运行单元测试
   ./scripts/run_tests.sh -u
   
   # 运行pre-commit检查
   pre-commit run --all-files
   ```

3. **提交代码**
   ```bash
   # Pre-commit hooks自动运行
   git add .
   git commit -m "feat: 新功能"
   ```

4. **推送到远程**
   ```bash
   git push origin feature/new-function
   ```

5. **CI自动运行**
   - GitHub Actions自动触发
   - 运行测试管道
   - 生成覆盖率报告
   - 质量门禁检查

6. **查看结果**
   - GitHub Actions标签页
   - PR评论中的覆盖率摘要
   - Artifacts中的测试报告

---

## 🛠️ 故障排查

### 常见问题

#### 1. Pre-commit hook失败

**问题**: `pre-commit` hook失败

**解决**:
```bash
# 查看详细错误
pre-commit run --all-files --verbose

# 跳过特定hook
SKIP=mypy pre-commit run --all-files

# 更新hooks
pre-commit autoupdate
pre-commit run --all-files
```

#### 2. 测试超时

**问题**: CI测试超时

**解决**:
```bash
# 本地运行慢速测试
./scripts/run_tests.sh --mark "slow"

# 使用pytest超时
poetry run pytest --timeout=300
```

#### 3. 覆盖率下降

**问题**: 新代码导致覆盖率下降

**解决**:
```bash
# 检查覆盖率变化
poetry run pytest --cov=core --cov-report=term-missing

# 查看未覆盖的行
poetry run pytest --cov=core --cov-report=annotate

# 为新代码添加测试
```

---

## 📚 相关文档

- [pytest配置](../pyproject.toml)
- [测试编写指南](../tests/README.md)
- [代码质量标准](../docs/development/CODE_QUALITY_STANDARDS.md)

---

**维护者**: 徐健 (xujian519@gmail.com)  
**最后更新**: 2026-04-21
