# Athena工作平台 - 代码质量检查清单

**版本**: 1.0
**更新日期**: 2025-01-16
**适用范围**: 所有代码提交、PR审查、质量审计

---

## 使用说明

本检查清单适用于以下场景：
- ✅ 代码提交前自检
- ✅ Pull Request代码审查
- ✅ 定期质量审计
- ✅ 新功能交付验收

---

## 📋 快速检查清单（提交前5分钟）

### 必检项（未完成不得提交）

- [ ] **代码通过所有自动化检查**
  - [ ] `black` 格式检查通过
  - [ ] `ruff` 代码检查通过
  - [ ] `mypy` 类型检查通过（如适用）
  - [ ] `bandit` 安全扫描无高危问题

- [ ] **没有空的except块**
  ```bash
  # 检查命令
  grep -rn "except:" --include="*.py" . | grep -v "test" | grep -v "# ignore"
  # 应该返回0个结果
  ```

- [ ] **没有硬编码的密钥/密码**
  - [ ] 没有直接写入的API密钥
  - [ ] 没有硬编码的密码
  - [ ] 所有敏感信息使用环境变量

- [ ] **测试覆盖新增功能**
  - [ ] 单元测试通过
  - [ ] 核心逻辑有测试覆盖
  - [ ] 边界情况已测试

- [ ] **文档已更新**
  - [ ] 有清晰的docstring
  - [ ] 复杂逻辑有注释说明
  - [ ] API文档已更新（如适用）

---

## 🔍 详细检查清单（代码审查）

### 1. 代码安全性 🛡️

#### 1.1 错误处理
- [ ] **没有空的except块**
  ```python
  # ❌ 错误
  try:
      operation()
  except Exception:
      pass

  # ✅ 正确
  try:
      operation()
  except SpecificError as e:
      logger.error(f"操作失败: {e}")
      raise
  ```

- [ ] **异常处理有适当的日志记录**
- [ ] **外部调用有超时和重试机制**
- [ ] **资源正确释放（文件、数据库连接等）**

#### 1.2 注入防护
- [ ] **SQL查询使用参数化**
  ```python
  # ❌ 错误
  query = f"SELECT * FROM users WHERE name = '{user_input}'"

  # ✅ 正确
  query = "SELECT * FROM users WHERE name = %s"
  cursor.execute(query, (user_input,))
  ```

- [ ] **命令行调用避免shell注入**
- [ ] **用户输入经过验证和清理**

#### 1.3 密码学安全
- [ ] **使用安全的随机数生成器**
  ```python
  # ❌ 错误（用于安全场景）
  import random
  token = random.random()

  # ✅ 正确
  import secrets
  token = secrets.token_hex(16)
  ```

- [ ] **使用安全的哈希算法**
  ```python
  # ❌ 错误
  import hashlib
  hashlib.md5(data)

  # ✅ 正确
  hashlib.sha256(data)

  # 或明确标记非安全用途
  hashlib.md5(data, usedforsecurity=False)
  ```

#### 1.4 密钥管理
- [ ] **没有硬编码的密钥**
- [ ] **敏感数据使用环境变量或密钥管理服务**
- [ ] **配置文件不包含敏感信息**
- [ ] **日志不泄露敏感数据**

### 2. 代码质量 ⭐

#### 2.1 可读性
- [ ] **变量和函数命名清晰**
  ```python
  # ❌ 错误
  def f(x):
      return x * 2

  # ✅ 正确
  def double_value(value):
      return value * 2
  ```

- [ ] **函数单一职责**
- [ ] **避免深层嵌套（不超过3层）**
- [ ] **函数长度合理（一般不超过50行）**

#### 2.2 复杂度
- [ ] **圈复杂度不超过10**
- [ ] **避免重复代码（DRY原则）**
- [ ] **复杂逻辑有清晰注释**

#### 2.3 类型注解
- [ ] **公共函数有类型注解**
  ```python
  # ✅ 正确
  def calculate_metrics(data: List[Dict]) -> Dict[str, float]:
      ...

  # 可选：简单内部函数
  def _helper(x):
      return x * 2
  ```

- [ ] **使用typing模块提供的类型**
- [ ] **避免使用Any类型（除非必要）**

#### 2.4 文档
- [ ] **所有公共函数有docstring**
  ```python
  def process_patent(patent_id: str) -> Patent:
      """
      处理专利数据

      Args:
          patent_id: 专利ID

      Returns:
          处理后的专利对象

      Raises:
          PatentNotFoundError: 专利不存在
      """
      ...
  ```

- [ ] **复杂算法有说明注释**
- [ ] **API变更更新了文档**

### 3. 测试覆盖 🧪

#### 3.1 单元测试
- [ ] **核心逻辑100%覆盖**
- [ ] **边界情况已测试**
- [ ] **错误路径已测试**
- [ ] **测试独立可重复**

#### 3.2 集成测试
- [ ] **服务间交互已测试**
- [ ] **数据库操作已测试**
- [ ] **外部API调用已mock**

#### 3.3 测试质量
- [ ] **测试命名清晰**
  ```python
  # ✅ 正确
  def test_patent_analysis_returns_correct_result():
      ...

  def test_patent_analysis_raises_error_on_invalid_input():
      ...
  ```

- [ ] **测试数据独立**
- [ ] **测试运行快速（单元测试<1秒）**

### 4. 性能考虑 ⚡

- [ ] **避免不必要的循环嵌套**
- [ ] **使用适当的数据结构**
  ```python
  # ❌ 低效（O(n)查找）
  items = [...]
  if target in items:  # O(n)

  # ✅ 高效（O(1)查找）
  items = set([...])
  if target in items:  # O(1)
  ```

- [ ] **数据库查询优化**
  - [ ] 避免N+1查询
  - [ ] 使用索引
  - [ ] 只查询需要的字段

- [ ] **大文件处理使用流式或分块**
- [ ] **缓存策略合理**

### 5. 依赖管理 📦

- [ ] **新依赖已添加到pyproject.toml**
- [ ] **依赖版本已固定**
- [ ] **没有不必要的依赖**
- [ ] **开源依赖许可证兼容**

### 6. 配置管理 ⚙️

- [ ] **配置使用环境变量**
  ```python
  # ❌ 错误
  DATABASE_URL = "postgresql://localhost/db"

  # ✅ 正确
  DATABASE_URL = os.getenv("DATABASE_URL")
  ```

- [ ] **敏感配置不提交到代码库**
- [ ] **默认值合理**
- [ ] **配置验证完善**

### 7. Git规范 📝

- [ ] **提交信息清晰**
  ```
  feat: 添加专利分析功能

  - 实现基于AI的专利分析
  - 添加单元测试
  - 更新API文档

  Closes #123
  ```

- [ ] **提交粒度合理**
- [ ] **没有大文件提交（>1MB）**
- [ ] **提交前rebase过**

---

## 🔧 工具使用指南

### Pre-commit钩子

```bash
# 安装pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行所有检查
pre-commit run --all-files

# 跳过钩子（不推荐）
git commit --no-verify -m "message"
```

### Bandit安全扫描

```bash
# 运行扫描
bandit -r core/

# 只检查高危问题
bandit -r core/ -ll

# 输出JSON格式
bandit -r core/ -f json -o report.json
```

### Ruff代码检查

```bash
# 运行检查
ruff check core/

# 自动修复
ruff check core/ --fix

# 格式化代码
ruff format core/
```

### Mypy类型检查

```bash
# 运行检查
mypy core/

# 检查特定文件
mypy core/module.py
```

---

## 📊 质量指标

### 目标指标

| 指标 | 当前目标 | 理想值 |
|------|---------|--------|
| 测试覆盖率 | 60% | 80%+ |
| Bandit高危问题 | 0 | 0 |
| 空的except块 | 0 | 0 |
| 类型注解覆盖率 | 80% | 95%+ |
| 文档覆盖率 | 70% | 90%+ |

### 每周检查

- [ ] 运行完整安全扫描
- [ ] 检查测试覆盖率趋势
- [ ] 审查技术债务清单
- [ ] 更新质量指标仪表板

---

## 🚨 常见问题

### Q: 如何处理legacy代码中的安全问题？

**A**:
1. 在新代码中严格遵循安全规范
2. 优先修复高危安全问题
3. 为legacy代码添加安全测试
4. 逐步重构，不要一次性大改

### Q: 测试覆盖率100%是必须的吗？

**A**: 不是。目标应该是：
- 核心业务逻辑：90%+
- 工具函数：70%+
- 配置/常量：0%（不需要）
- 整体：60-80%

### Q: Pre-commit太慢怎么办？

**A**:
1. 使用`pre-commit run --files`只检查变更的文件
2. 调整钩子顺序，快速检查放前面
3. 使用缓存（pre-commit默认支持）

### Q: 如何快速上手？

**A**: 建议流程：
1. **第1天**: 配置pre-commit，运行一次所有检查
2. **第2-3天**: 修复所有高危安全问题
3. **第1周**: 适应自动化检查流程
4. **第2-4周**: 逐步提升代码质量
5. **第2个月**: 建立质量习惯

---

## 📚 参考资料

- [Python安全编码最佳实践](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Bandit文档](https://bandit.readthedocs.io/)
- [Ruff文档](https://docs.astral.sh/ruff/)
- [Pre-commit文档](https://pre-commit.com/)

---

**检查清单维护**: 技术团队
**最后更新**: 2025-01-16
**下次审核**: 2025-02-16（每月）
