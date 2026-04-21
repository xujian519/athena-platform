# 依赖管理指南

> **最后更新**: 2026-04-21
> **第1阶段 Day 7: 依赖管理统一**

---

## 📦 依赖管理架构

Athena工作平台采用**分层依赖管理**策略：

```
┌─────────────────────────────────────┐
│     核心平台 (Core Platform)         │
│  pyproject.toml + requirements.txt   │
└─────────────────────────────────────┘
         │         │         │
    ┌────┴────┐ ┌──┴────┐ ┌─┴──────┐
    │ 微服务1  │ │ 微服务2│ │ 微服务3 │
    │  API    │ │  API   │ │  API   │
    └─────────┘ └───────┘ └────────┘
  services/*/requirements.txt
```

---

## 🎯 依赖管理文件

### 1. 核心平台依赖

#### `pyproject.toml` (Poetry管理)
**用途**: 核心平台依赖的完整管理

**优势**:
- ✅ 依赖锁定（poetry.lock）
- ✅ 虚拟环境管理
- ✅ 依赖解析和冲突检测
- ✅ 开发依赖和生产依赖分离

**使用方法**:
```bash
# 安装依赖
poetry install

# 添加依赖
poetry add package-name

# 更新依赖
poetry update
```

#### `requirements.txt` (pip管理)
**用途**: 快速安装核心平台依赖

**特点**:
- 从 pyproject.toml 导出
- 用于不使用 Poetry 的场景
- 包含核心平台的所有依赖

**使用方法**:
```bash
# 安装核心依赖
pip install -r requirements.txt

# 导出（从 pyproject.toml）
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### 2. 微服务依赖

#### `services/*/requirements.txt`
**用途**: 各微服务的独立依赖管理

**微服务列表**:
```
services/
├── xiaonuo-agent-api/requirements.txt        # 小诺智能体API
├── xiaona-agent-api/requirements.txt         # 小娜智能体API
├── tool-registry-api/requirements.txt        # 工具注册表API
├── browser_automation_service/requirements.txt # 浏览器自动化服务
└── article-writer-service/requirements.txt    # 文章写作服务
```

**使用方法**:
```bash
# 安装特定服务依赖
pip install -r services/xiaonuo-agent-api/requirements.txt
```

---

## 🔧 依赖管理最佳实践

### 1. 开发环境

**推荐使用 Poetry**:
```bash
# 初始化项目
poetry install

# 激活虚拟环境
poetry shell

# 运行代码
poetry run python scripts/your_script.py
```

### 2. 生产环境

**选项1: 使用 Poetry**
```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install --no-dev
```

**选项2: 使用 pip**
```bash
# 导出 requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes

# 安装依赖
pip install -r requirements.txt
```

### 3. 微服务部署

**独立部署**:
```bash
# 进入服务目录
cd services/xiaonuo-agent-api/

# 安装服务依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

---

## 📝 依赖更新流程

### 添加新依赖

1. **核心平台依赖**:
   ```bash
   # 使用 Poetry
   poetry add package-name

   # 更新 requirements.txt
   poetry export -f requirements.txt --output requirements.txt --without-hashes
   ```

2. **微服务依赖**:
   ```bash
   # 编辑 services/{service}/requirements.txt
   echo "package-name==version" >> services/{service}/requirements.txt
   ```

### 更新现有依赖

```bash
# 更新所有依赖
poetry update

# 更新特定包
poetry update package-name

# 导出新的 requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

---

## 📊 依赖清单

### 核心平台依赖

| 类别 | 主要依赖 | 用途 |
|------|---------|------|
| Web框架 | FastAPI, Uvicorn | API服务 |
| 数据库 | asyncpg, psycopg2, Redis | 数据持久化 |
| AI/ML | scikit-learn, numpy, pandas | 数据处理 |
| 向量数据库 | qdrant-client | 向量检索 |
| 图数据库 | neo4j | 知识图谱 |
| NLP | jieba | 中文分词 |
| 工具库 | loguru, httpx, aiohttp | 通用工具 |

### 微服务依赖

各微服务的依赖见对应的 `requirements.txt` 文件。

---

## ⚠️ 注意事项

### 1. 依赖冲突

**问题**: 不同服务可能依赖不同版本的同一个包

**解决方案**:
- 使用独立的虚拟环境
- 使用容器化部署（Docker）
- 定期同步依赖版本

### 2. 安全更新

**定期更新**:
```bash
# 检查过时的依赖
poetry show --outdated

# 更新依赖
poetry update
```

### 3. 生产部署

**锁定版本**:
- ✅ 使用 `poetry.lock` 锁定核心依赖
- ✅ 使用固定版本号（`==`）而非范围（`>=`）
- ✅ 定期测试更新

---

## 🔄 迁移历史

### 2026-04-21 - 第1阶段 Day 7统一

**变更**:
- ✅ 统一使用 `pyproject.toml` 管理核心依赖
- ✅ 创建根目录 `requirements.txt` 用于快速安装
- ✅ 保留 `services/*/requirements.txt` 用于微服务独立部署
- ✅ 更新依赖管理文档

**策略**:
- 核心平台: Poetry (pyproject.toml) + pip (requirements.txt)
- 微服务: 独立 requirements.txt

---

## 🎯 下一步优化

### 短期 (第2阶段)
- [ ] 添加依赖安全扫描
- [ ] 自动化依赖更新
- [ ] 依赖文档生成

### 长期 (第3-4阶段)
- [ ] 私有PyPI仓库
- [ ] 依赖版本监控
- [ ] 自动化测试依赖更新

---

**文档创建时间**: 2026-04-21
**执行阶段**: 第1阶段 Day 7
**维护者**: 徐健 (xujian519@gmail.com)
