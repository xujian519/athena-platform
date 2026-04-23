# 依赖管理迁移指南

> **迁移日期**: 2026-04-23
> **状态**: ✅ 完成
> **影响范围**: 全项目依赖统一

---

## 概述

项目已完成从分散的依赖文件到统一Poetry管理的迁移。

### 迁移前问题

1. **依赖文件分散** - 9个独立的requirements.txt/pyproject.toml文件
2. **版本冲突** - fastapi从0.104.0到0.136.0
3. **混合构建系统** - Poetry + setuptools + pip
4. **依赖重复声明** - 相同包在多处定义

### 迁移后状态

- ✅ 统一使用Poetry
- ✅ 版本冲突解决
- ✅ 依赖按组组织
- ✅ 清理冗余文件

---

## 依赖组织结构

### 核心依赖 (`[tool.poetry.dependencies]`)

```toml
python = "^3.11"
fastapi = "^0.115.0"      # 统一版本
uvicorn = "^0.32.0"       # 统一版本
pydantic = "^2.5.0"       # 统一版本
# ... 其他核心依赖
```

### 服务依赖组

```bash
# 浏览器自动化服务
poetry install --with browser

# 脚本自动化工具
poetry install --with automation
```

### 可选依赖（extras）

```bash
# 多模态AI依赖
poetry install --extras multimodal

# 认证相关
poetry install --extras auth

# 安装所有可选依赖
poetry install --all-extras
```

---

## 已废弃的文件

以下文件已整合到主`pyproject.toml`，可安全删除：

| 文件 | 说明 | 替代方案 |
|------|------|---------|
| `services/xiaonuo-agent-api/requirements.txt` | 小诺API依赖 | `poetry install` |
| `services/tool-registry-api/requirements.txt` | 工具注册表依赖 | `poetry install` |
| `services/browser_automation_service/requirements.txt` | 浏览器服务 | `poetry install --with browser` |
| `services/article-writer-service/requirements.txt` | 文章撰写服务 | `poetry install` |
| `deploy/requirements-multimodal.txt` | 多模态部署 | `poetry install --extras multimodal` |

> ⚠️ **注意**: `requirements.txt`（根目录）保留用于Docker部署，通过`poetry export`生成

---

## 常用命令

### 开发环境安装

```bash
# 基础安装
poetry install

# 包含开发依赖
poetry install --with dev

# 包含所有服务依赖
poetry install --with dev,browser,automation

# 包含可选依赖
poetry install --all-extras
```

### 依赖更新

```bash
# 更新所有依赖
poetry update

# 更新特定包
poetry update fastapi uvicorn

# 添加新依赖
poetry add requests
poetry add pytest --group dev
```

### 导出requirements.txt

```bash
# 导出用于Docker部署
poetry export -f requirements.txt --output requirements.txt

# 仅导出核心依赖（不含开发依赖）
poetry export -f requirements.txt --output requirements.txt --without dev
```

---

## 版本变更对照

| 包名 | 迁移前范围 | 迁移后版本 | 说明 |
|------|-----------|-----------|------|
| fastapi | 0.104.0 ~ 0.136.0 | ^0.115.0 | 统一版本 |
| uvicorn | 0.24.0 ~ 0.44.0 | ^0.32.0 | 统一版本 |
| pydantic | 2.5.0 ~ 2.6.0 | ^2.5.0 | 统一版本 |
| numpy | 1.24.3 ~ 2.4.4 | ^1.24.0 | 兼容Python 3.11 |
| pillow | 10.1.0 ~ 12.2.0 | ^10.0.0 | 统一版本 |
| httpx | 0.25.1 ~ 0.28.0 | ^0.25.0 | 统一版本 |
| loguru | 0.7.0 ~ 0.7.2 | ^0.7.0 | 统一版本 |
| tenacity | 8.2.3 ~ 9.1.0 | ^8.2.0 | 统一版本 |

---

## 回滚方案

如需回滚，执行：

```bash
# 1. 恢复旧的pyproject.toml
git checkout HEAD~1 pyproject.toml

# 2. 恢复服务依赖文件
git checkout HEAD~1 services/*/requirements.txt

# 3. 重新安装
pip install -r requirements.txt
```

---

## 故障排查

### 问题：poetry install失败

```bash
# 清理缓存
poetry cache clear --all pypi

# 删除虚拟环境重建
poetry env remove python
poetry install
```

### 问题：版本冲突

```bash
# 查看依赖树
poetry show --tree

# 查看特定包依赖
poetry show fastapi
```

### 问题：导入错误

```bash
# 确保PYTHONPATH正确
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 或在虚拟环境中安装为可编辑
poetry build
pip install dist/*.tar.gz
```

---

## 后续维护

1. **添加新依赖**：始终使用`poetry add`而非`pip install`
2. **版本更新**：定期运行`poetry update`
3. **安全审计**：`poetry show --outdated`
4. **导出部署**：每次更新后运行`poetry export`

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-23
