# Athena平台架构优化实施路线图

> **制定时间**: 2026-04-23
> **预计工期**: 7周
> **风险等级**: 中高（需要严格测试和回滚机制）

---

## 📋 总体规划

### 阶段概览

| 阶段 | 名称 | 工作量 | 风险 | 收益 | 时间窗口 |
|-----|------|-------|------|------|---------|
| 0 | 准备工作 - 建立安全网 | 1-2天 | 低 | 安全保障 | Week 1, Day 1-2 |
| 1 | 消除循环依赖 - 依赖倒置 | 1-2周 | 高 | 架构解耦 | Week 1-2 (Day 3-14) |
| 2 | 核心组件重组 - 领域划分 | 2-3周 | 中 | 可维护性↑ | Week 3-5 (Day 15-35) |
| 3 | 顶层目录聚合 - 高内聚 | 1周 | 低 | 开发效率↑ | Week 6 (Day 36-42) |
| 4 | 数据治理 - 存储优化 | 1周 | 低 | 存储优化 | Week 7 (Day 43-49) |

---

## 🎯 阶段0：准备工作 - 建立安全网（Day 1-2）

### 目标
建立完整的安全网，确保每个阶段都可以安全回滚。

### 任务清单

#### 0.1 代码快照系统（4小时）
**交付物**: `scripts/architecture/create_snapshot.sh`

```bash
功能：
- 完整代码库tar.gz打包
- Git tag标记
- 文件清单生成
- MD5校验和

输出：
backups/architecture-snapshots/
├── snapshot-20260423-pre-phase0.tar.gz
├── snapshot-20260423-pre-phase0.manifest
└── snapshot-20260423-pre-phase0.md5
```

#### 0.2 依赖关系图谱（6小时）
**交付物**: `scripts/architecture/analyze_dependencies.py`

```python
功能：
- 扫描所有Python文件的import语句
- 生成模块依赖矩阵
- 检测循环依赖
- 输出可视化图表（Graphviz）

输出：
reports/architecture/
├── dependency_graph.json
├── dependency_matrix.csv
├── circular_dependencies.json
└── dependency_graph.png
```

#### 0.3 测试基线建立（4小时）
**交付物**: `scripts/architecture/verify_baseline.sh`

```bash
功能：
- 运行完整测试套件
- 生成覆盖率报告
- 记录测试结果作为基线
- 性能基准测试

输出：
reports/architecture/
├── test_baseline.json
├── coverage_baseline.html
└── performance_baseline.json
```

#### 0.4 回滚脚本（4小时）
**交付物**: `scripts/architecture/rollback.sh`

```bash
功能：
- 从快照恢复代码
- 恢复数据库状态
- 重启服务
- 验证恢复成功
```

### 验收标准
- ✅ 快照可在5分钟内完成
- ✅ 依赖图谱生成<2分钟
- ✅ 测试基线通过率>90%
- ✅ 回滚测试成功

---

## 🔄 阶段1：消除循环依赖 - 依赖倒置（Day 3-14）

### 目标
消除`core/`对`services/`和`domains/`的反向依赖，实现依赖倒置原则。

### 问题清单

| 文件 | 反向依赖 | 影响 |
|-----|---------|------|
| `core/vector_db/hybrid_storage_manager.py` | `services.agent_services.vector_db` | 高 |
| `core/intelligence/enhanced_dynamic_prompt_generator.py` | `services.sqlite_patent_knowledge_service` | 高 |
| `core/utils/patent-search/search_jinan_patents.py` | `services.patents.google_patents_retriever` | 中 |
| `core/patents/.../production_patent_search.py` | `domains.patent.crawlers` | 高 |
| `core/search/enhanced_hybrid_search.py` | `domains.legal_ai.knowledge.legal_ontology` | 中 |

### 任务清单

#### 1.1 创建接口定义层（Day 3-5）
**交付物**: `core/interfaces/`

```python
# core/interfaces/__init__.py
"""
核心接口定义层 - 依赖倒置核心
"""

# core/interfaces/vector_store.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStoreProvider(ABC):
    """向量存储提供者接口"""

    @abstractmethod
    async def insert_vectors(self, collection: str, vectors: List[List[float]]) -> bool:
        """插入向量"""

    @abstractmethod
    async def search_vectors(self, collection: str, query: List[float], top_k: int) -> List[Dict]:
        """搜索向量"""

    @abstractmethod
    async def delete_collection(self, collection: str) -> bool:
        """删除集合"""

# core/interfaces/knowledge_base.py
class KnowledgeBaseService(ABC):
    """知识库服务接口"""

    @abstractmethod
    async def query_knowledge(self, query: str, domain: str) -> List[Dict]:
        """查询知识库"""

    @abstractmethod
    async def update_knowledge(self, domain: str, knowledge: Dict) -> bool:
        """更新知识库"""

# core/interfaces/patent_service.py
class PatentRetrievalService(ABC):
    """专利检索服务接口"""

    @abstractmethod
    async def search_patents(self, query: str, filters: Dict) -> List[Dict]:
        """搜索专利"""

    @abstractmethod
    async def get_patent_detail(self, patent_id: str) -> Dict:
        """获取专利详情"""
```

#### 1.2 依赖注入配置（Day 6-8）
**交付物**: `config/dependency_injection.py`

```python
"""
依赖注入配置 - 在应用启动时注入具体实现
"""

from core.interfaces.vector_store import VectorStoreProvider
from core.interfaces.knowledge_base import KnowledgeBaseService
from core.interfaces.patent_service import PatentRetrievalService

# 具体实现（从services/domains导入）
from services.agent_services.vector_db.optimized_qdrant_client import OptimizedQdrantClient
from services.sqlite_patent_knowledge_service import get_sqlite_patent_knowledge_service
from services.patents.google_patents_retriever import GooglePatentsRetriever

class DIContainer:
    """依赖注入容器"""

    _instances = {}

    @classmethod
    def register(cls, interface, implementation):
        """注册实现"""
        cls._instances[interface] = implementation

    @classmethod
    def resolve(cls, interface):
        """解析实现"""
        return cls._instances.get(interface)

# 应用启动时注册
def setup_dependency_injection():
    """设置依赖注入"""
    DIContainer.register(
        VectorStoreProvider,
        OptimizedQdrantClient()
    )
    DIContainer.register(
        KnowledgeBaseService,
        get_sqlite_patent_knowledge_service()
    )
    DIContainer.register(
        PatentRetrievalService,
        GooglePatentsRetriever()
    )
```

#### 1.3 重构反向依赖（Day 9-12）
**交付物**: 重构后的core模块

```python
# 重构前：core/vector_db/hybrid_storage_manager.py
from services.agent_services.vector_db.optimized_qdrant_client import OptimizedQdrantClient

class HybridStorageManager:
    def __init__(self):
        self.qdrant = OptimizedQdrantClient()  # ❌ 硬依赖

# 重构后：
from core.interfaces.vector_store import VectorStoreProvider
from config.dependency_injection import DIContainer

class HybridStorageManager:
    def __init__(self, vector_provider: VectorStoreProvider = None):
        # ✅ 依赖注入，默认从容器解析
        self.vector_provider = vector_provider or DIContainer.resolve(VectorStoreProvider)
```

#### 1.4 批量迁移脚本（Day 13）
**交付物**: `scripts/architecture/migrate/phase1_fix_imports.py`

```python
"""
批量修复import脚本
"""

import re
from pathlib import Path

MIGRATION_RULES = {
    # 旧导入 → 新导入（通过接口）
    "from services.agent_services.vector_db.optimized_qdrant_client": "from core.interfaces.vector_store import VectorStoreProvider",
    "from services.sqlite_patent_knowledge_service": "from core.interfaces.knowledge_base import KnowledgeBaseService",
    # ... 更多规则
}

def migrate_imports(file_path: Path):
    """迁移单个文件的imports"""
    content = file_path.read_text()
    modified = False

    for old_import, new_import in MIGRATION_RULES.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            modified = True

    if modified:
        file_path.write_text(content)
        print(f"✅ Migrated: {file_path}")

def migrate_all():
    """迁移所有core/文件"""
    core_path = Path("/Users/xujian/Athena工作平台/core")
    for py_file in core_path.rglob("*.py"):
        migrate_imports(py_file)

if __name__ == "__main__":
    migrate_all()
```

#### 1.5 验证与测试（Day 14）
**交付物**: `scripts/architecture/migrate/verify_phase1.sh`

```bash
#!/bin/bash
# 验证阶段1完成度

echo "🔍 检查反向依赖..."
VIOLATIONS=$(grep -r "from services\." core/ --include="*.py" | wc -l)
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ 无services依赖"
else
    echo "❌ 发现 $VIOLATIONS 个services依赖"
    exit 1
fi

echo "🔍 检查domains依赖..."
VIOLATIONS=$(grep -r "from domains\." core/ --include="*.py" | wc -l)
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ 无domains依赖"
else
    echo "❌ 发现 $VIOLATIONS 个domains依赖"
    exit 1
fi

echo "🔍 运行测试套件..."
pytest tests/ -v --tb=short

echo "✅ 阶段1验证完成"
```

### 验收标准
- ✅ `core/`中无`from services.*`或`from domains.*`
- ✅ `core/`可独立运行单元测试
- ✅ 所有测试通过率≥基线
- ✅ 无性能回归

---

## 🏗️ 阶段2：核心组件重组 - 领域边界划分（Day 15-35）

### 目标
将`core/`从164个子模块精简到<30个，业务逻辑下放到`domains/`。

### 新的core/结构

```
core/
├── infrastructure/        # 基础设施层（20个子模块）
│   ├── database/         # 数据库连接池、ORM
│   ├── cache/            # Redis缓存
│   ├── logging/          # 日志系统
│   ├── vector_db/        # 向量数据库（Qdrant、Neo4j）
│   ├── config/           # 配置管理
│   ├── messaging/        # 消息队列
│   └── monitoring/       # 监控指标
├── ai/                   # AI能力层（15个子模块）
│   ├── llm/              # LLM适配器
│   ├── embedding/        # 向量嵌入
│   ├── prompts/          # 提示词管理
│   ├── intelligence/     # 智能处理
│   ├── cognition/        # 认知处理
│   ├── nlp/              # NLP服务
│   └── perception/       # 感知模块
├── framework/            # 框架基座（10个子模块）
│   ├── agents/           # 代理基类
│   ├── memory/           # 四级记忆系统
│   ├── collaboration/    # 协作模式
│   ├── routing/          # 路由逻辑
│   └── gateway/          # 网关客户端
├── interfaces/           # 接口定义（阶段1新增）
└── utils/                # 通用工具（5个子模块）
    ├── text/
    ├── file/
    ├── time/
    └── math/
```

### 迁移清单

| 源路径 | 目标路径 | 优先级 | 复杂度 |
|-------|---------|-------|--------|
| `core/biology/` | `domains/biology/` | P2 | 低 |
| `core/emotion/` | `domains/emotion/` | P2 | 低 |
| `core/legal_kg/` | `domains/legal/knowledge_graph/` | P1 | 中 |
| `core/patents/` | `domains/patents/` | P1 | 高 |
| `core/compliance/` | `domains/legal/compliance/` | P1 | 中 |
| `core/acceleration/` | `domains/optimization/` | P3 | 低 |
| `core/authenticity/` | `domains/security/` | P2 | 低 |

### 任务清单

#### 2.1 创建新目录结构（Day 15）
**交付物**: `scripts/architecture/migrate/phase2_create_structure.sh`

```bash
#!/bin/bash
# 创建新的core结构

cd /Users/xujian/Athena工作平台

# 备份现有core
mv core core.backup.$(date +%Y%m%d)

# 创建新结构
mkdir -p core/{infrastructure,ai,framework,interfaces,utils}

# 创建子目录
mkdir -p core/infrastructure/{database,cache,logging,vector_db,config}
mkdir -p core/ai/{llm,embedding,prompts,intelligence,cognition,nlp,perception}
mkdir -p core/framework/{agents,memory,collaboration,routing,gateway}
mkdir -p core/utils/{text,file,time,math}

echo "✅ 新core结构已创建"
```

#### 2.2 批量迁移脚本（Day 16-20）
**交付物**: `scripts/architecture/migrate/phase2_migrate_modules.py`

```python
"""
批量迁移core模块到domains
"""

import shutil
from pathlib import Path

MIGRATION_MAP = {
    "core/biology": "domains/biology",
    "core/emotion": "domains/emotion",
    "core/legal_kg": "domains/legal/knowledge_graph",
    "core/patents": "domains/patents",
    "core/compliance": "domains/legal/compliance",
    "core/acceleration": "domains/optimization",
    "core/authenticity": "domains/security",
}

def migrate_module(src: str, dst: str):
    """迁移单个模块"""
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        print(f"⚠️  源路径不存在: {src}")
        return

    # 创建目标目录
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # 移动目录
    shutil.move(str(src_path), str(dst_path))
    print(f"✅ 迁移: {src} → {dst}")

def update_imports():
    """更新所有import路径"""
    # TODO: 实现import路径更新
    pass

def main():
    """执行迁移"""
    for src, dst in MIGRATION_MAP.items():
        migrate_module(src, dst)

    update_imports()
    print("✅ 迁移完成")

if __name__ == "__main__":
    main()
```

#### 2.3 Import路径更新（Day 21-28）
**交付物**: `scripts/architecture/migrate/phase2_update_imports.py`

```python
"""
更新import路径 - 从core.*到domains.*
"""

import re
from pathlib import Path

IMPORT_REPLACEMENTS = {
    "from core.biology": "from domains.biology",
    "from core.emotion": "from domains.emotion",
    "from core.legal_kg": "from domains.legal.knowledge_graph",
    "from core.patents": "from domains.patents",
    "from core.compliance": "from domains.legal.compliance",
    "import core.biology": "import domains.biology",
    "import core.emotion": "import domains.emotion",
    # ... 更多规则
}

def update_file_imports(file_path: Path):
    """更新单个文件的imports"""
    content = file_path.read_text()
    modified = False

    for old, new in IMPORT_REPLACEMENTS.items():
        if old in content:
            content = content.replace(old, new)
            modified = True

    if modified:
        file_path.write_text(content)
        print(f"✅ Updated: {file_path}")

def update_all_imports():
    """更新所有文件"""
    project_root = Path("/Users/xujian/Athena工作平台")
    for py_file in project_root.rglob("*.py"):
        # 跳过备份目录
        if "backup" in str(py_file):
            continue
        update_file_imports(py_file)

if __name__ == "__main__":
    update_all_imports()
```

#### 2.4 基础设施层重组（Day 29-31）
**交付物**: 新的`core/infrastructure/`结构

```bash
# 合并相似的数据库模块
mv core/database/* core/infrastructure/database/
mv core/neo4j/* core/infrastructure/vector_db/
mv core/qdrant/* core/infrastructure/vector_db/
mv core/redis/* core/infrastructure/cache/
```

#### 2.5 AI能力层重组（Day 32-33）
**交付物**: 新的`core/ai/`结构

```bash
# 合并AI相关模块
mv core/llm/* core/ai/llm/
mv core/embedding/* core/ai/embedding/
mv core/prompts/* core/ai/prompts/
mv core/intelligence/* core/ai/intelligence/
mv core/cognition/* core/ai/cognition/
mv core/nlp/* core/ai/nlp/
```

#### 2.6 验证与测试（Day 34-35）
**交付物**: `scripts/architecture/migrate/verify_phase2.sh`

```bash
#!/bin/bash
# 验证阶段2完成度

echo "🔍 检查core目录数量..."
CORE_DIRS=$(ls -d core/*/ 2>/dev/null | wc -l)
if [ $CORE_DIRS -lt 30 ]; then
    echo "✅ core目录数: $CORE_DIRS (<30)"
else
    echo "❌ core目录数过多: $CORE_DIRS"
    exit 1
fi

echo "🔍 检查业务模块迁移..."
if [ ! -d "core/biology" ] && [ -d "domains/biology" ]; then
    echo "✅ 业务模块已下放"
else
    echo "❌ 业务模块仍在core中"
    exit 1
fi

echo "🔍 运行测试套件..."
pytest tests/ -v --tb=short

echo "✅ 阶段2验证完成"
```

### 验收标准
- ✅ `core/`子目录<30个
- ✅ 所有业务逻辑在`domains/`
- ✅ 测试覆盖率不下降
- ✅ 所有测试通过

---

## 📁 阶段3：顶层目录聚合 - 高内聚整合（Day 36-42）

### 目标
整合分散的工具脚本和共享代码，减少根目录一级目录数量。

### 当前问题
```
根目录有：
- tools/ (24个子目录)
- scripts/ (52个子目录)
- cli/ (21个子目录)
- utils/ (10个子目录)
```

### 新的scripts/结构

```
scripts/
├── dev/               # 开发工具
│   ├── setup_env.sh
│   ├── test_runner.py
│   ├── lint_code.sh
│   └── format_code.sh
├── deploy/            # 部署脚本
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── health_check.sh
│   └── service_restart.sh
├── admin/             # 管理工具
│   ├── db_backup.sh
│   ├── log_cleaner.sh
│   ├── user_manage.sh
│   └── monitor.sh
├── automation/        # 自动化脚本
│   ├── ci_pipeline.py
│   ├── report_generator.py
│   ├── data_sync.sh
│   └── batch_process.py
└── architecture/      # 架构管理（本次新增）
    ├── create_snapshot.sh
    ├── analyze_dependencies.py
    └── rollback.sh
```

### 任务清单

#### 3.1 工具脚本分类（Day 36-37）
**交付物**: `scripts/architecture/migrate/phase3_categorize_tools.py`

```python
"""
分类工具脚本到新结构
"""

import shutil
from pathlib import Path

CATEGORIES = {
    "dev": [
        "test_*.sh",
        "lint*.sh",
        "format*.sh",
        "setup*.sh",
    ],
    "deploy": [
        "deploy*.sh",
        "start*.sh",
        "stop*.sh",
        "restart*.sh",
    ],
    "admin": [
        "backup*.sh",
        "*cleaner*.sh",
        "monitor*.sh",
        "health*.sh",
    ],
    "automation": [
        "ci*.py",
        "*pipeline*.py",
        "batch*.sh",
        "sync*.sh",
    ],
}

def categorize_script(script_path: Path):
    """分类单个脚本"""
    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if script_path.match(pattern):
                return category
    return "dev"  # 默认

def migrate_scripts():
    """迁移所有脚本"""
    sources = [
        Path("/Users/xujian/Athena工作平台/tools"),
        Path("/Users/xujian/Athena工作平台/cli"),
        Path("/Users/xujian/Athena工作平台/scripts"),
        Path("/Users/xujian/Athena工作平台/utils"),
    ]

    for source in sources:
        if not source.exists():
            continue

        for script in source.rglob("*"):
            if script.is_file():
                category = categorize_script(script)
                dest = Path(f"/Users/xujian/Athena工作平台/scripts/{category}/{script.name}")
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(script, dest)
                print(f"✅ {script.name} → {category}/")

if __name__ == "__main__":
    migrate_scripts()
```

#### 3.2 共享代码整合（Day 38-39）
**交付物**: `pkg/utils/`统一工具库

```bash
# 合并utils/, shared/, cli/shared/
mkdir -p pkg/utils
mv utils/* pkg/utils/
mv shared/* pkg/utils/
rm -rf utils shared cli/shared
```

#### 3.3 测试目录规范（Day 40）
**交付物**: 新的`tests/`结构

```bash
# 创建标准测试目录
mkdir -p tests/{unit,integration,e2e,fixtures}

# 移动分散的测试
find . -name "test_*.py" -not -path "*/tests/*" -exec mv {} tests/unit/ \;
find . -name "*_test.py" -not -path "*/tests/*" -exec mv {} tests/unit/ \;
```

#### 3.4 清理旧目录（Day 41）
**交付物**: `scripts/architecture/migrate/phase3_cleanup.sh`

```bash
#!/bin/bash
# 清理旧目录（需确认后执行）

echo "⚠️  以下操作将删除旧目录，请确认："
echo "- tools/"
echo "- cli/"
echo "- utils/"
read -p "确认删除？(yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    rm -rf tools cli utils
    echo "✅ 已清理旧目录"
else
    echo "❌ 已取消"
fi
```

#### 3.5 验证（Day 42）
**交付物**: `scripts/architecture/migrate/verify_phase3.sh`

```bash
#!/bin/bash
# 验证阶段3完成度

echo "🔍 检查根目录数量..."
ROOT_DIRS=$(ls -d */ 2>/dev/null | wc -l)
if [ $ROOT_DIRS -lt 20 ]; then
    echo "✅ 根目录数: $ROOT_DIRS (<20)"
else
    echo "❌ 根目录数过多: $ROOT_DIRS"
    exit 1
fi

echo "🔍 检查脚本分散情况..."
if [ ! -d "tools" ] && [ ! -d "cli" ]; then
    echo "✅ 脚本已整合"
else
    echo "❌ 仍有分散的脚本目录"
    exit 1
fi

echo "✅ 阶段3验证完成"
```

### 验收标准
- ✅ 根目录一级目录<20个
- ✅ 所有脚本可在`scripts/`找到
- ✅ 无重复工具实现
- ✅ 测试目录结构规范

---

## 💾 阶段4：数据治理 - 存储优化（Day 43-49）

### 目标
数据去重、环境隔离、配置化路径。

### 当前问题
```
data/legal-docs/:      54M
domains/legal-knowledge/:  54M
内容完全重复（法律文书Markdown）
```

### 新的assets/结构

```
assets/
├── legal-knowledge/   # 法律知识文档
│   ├── civil_procedure.md
│   ├── criminal_rules.md
│   └── patent_guidelines.md
├── patent-data/       # 专利数据
│   ├── guidelines/
│   └── examples/
└── models/            # AI模型文件（运行时下载）
```

### 任务清单

#### 4.1 数据去重（Day 43-44）
**交付物**: `scripts/architecture/migrate/phase4_deduplicate_data.sh`

```bash
#!/bin/bash
# 数据去重脚本

ASSETS_DIR="/Users/xujian/Athena工作平台/assets"
DATA_DIR="/Users/xujian/Athena工作平台/data"
DOMAINS_DIR="/Users/xujian/Athena工作平台/domains"

# 创建assets目录
mkdir -p "$ASSETS_DIR"/{legal-knowledge,patent-data,models}

# 对比并去重legal-docs
echo "🔍 对比legal-docs和domains/legal-knowledge..."
if diff -rq "$DATA_DIR/legal-docs" "$DOMAINS_DIR/legal-knowledge" >/dev/null; then
    echo "✅ 内容完全一致，删除domains/legal-knowledge"
    rm -rf "$DOMAINS_DIR/legal-knowledge"
    mv "$DATA_DIR/legal-docs" "$ASSETS_DIR/legal-knowledge"
else
    echo "⚠️  内容不一致，需要人工检查"
    # 使用rsync同步差异
    rsync -av --delete "$DATA_DIR/legal-docs/" "$ASSETS_DIR/legal-knowledge/"
fi

echo "✅ 数据去重完成"
```

#### 4.2 完善gitignore（Day 45）
**交付物**: 更新的`.gitignore`

```gitignore
# 运行时数据
*.db
*.sqlite
*.log
*.pid

# 报告和临时文件
*_report.json
*_report.md
build/reports/
htmlcov/
.pytest_cache/

# 备份目录
scripts.backup.*
*.backup
*.bak

# 模型文件（大文件）
models/*.bin
models/*.safetensors
*.gguf

# 数据文件（运行时生成）
data/cache/
data/temp/
data/logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# 环境变量
.env.local
.env.*.local
```

#### 4.3 配置化数据路径（Day 46）
**交付物**: `config/data_paths.py`

```python
"""
数据路径配置 - 统一管理所有数据路径
"""

from pathlib import Path
import os

class DataPaths:
    """数据路径配置"""

    # 基础路径
    BASE_DIR = Path("/Users/xujian/Athena工作平台")
    ASSETS_DIR = BASE_DIR / "assets"
    DATA_DIR = BASE_DIR / "data"

    # 法律知识
    LEGAL_KNOWLEDGE = ASSETS_DIR / "legal-knowledge"
    CIVIL_PROCEDURE = LEGAL_KNOWLEDGE / "civil_procedure.md"
    CRIMINAL_RULES = LEGAL_KNOWLEDGE / "criminal_rules.md"

    # 专利数据
    PATENT_DATA = ASSETS_DIR / "patent-data"
    PATENT_GUIDELINES = PATENT_DATA / "guidelines"

    # AI模型
    MODELS_DIR = BASE_DIR / "models"
    EMBEDDING_MODELS = MODELS_DIR / "embeddings"
    LLM_MODELS = MODELS_DIR / "llm"

    # 运行时数据
    CACHE_DIR = DATA_DIR / "cache"
    TEMP_DIR = DATA_DIR / "temp"
    LOGS_DIR = DATA_DIR / "logs"

    @classmethod
    def ensure_dirs(cls):
        """确保所有目录存在"""
        for attr in dir(cls):
            if attr.isupper() and isinstance(getattr(cls, attr), Path):
                path = getattr(cls, attr)
                if path.suffix == "":  # 目录而非文件
                    path.mkdir(parents=True, exist_ok=True)

# 应用启动时调用
DataPaths.ensure_dirs()
```

#### 4.4 清理历史备份（Day 47）
**交付物**: `scripts/architecture/migrate/phase4_cleanup_backups.sh`

```bash
#!/bin/bash
# 清理历史备份目录

echo "🔍 查找备份目录..."
find /Users/xujian/Athena工作平台 -type d -name "*.backup*" -o -name "*_backup*" | while read dir; do
    echo "发现备份: $dir"
    SIZE=$(du -sh "$dir" | cut -f1)
    echo "  大小: $SIZE"
done

echo ""
read -p "是否删除所有备份目录？(yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    find /Users/xujian/Athena工作平台 -type d -name "*.backup*" -exec rm -rf {} +
    find /Users/xujian/Athena工作平台 -type d -name "*_backup*" -exec rm -rf {} +
    echo "✅ 已清理所有备份目录"
else
    echo "❌ 已取消"
fi
```

#### 4.5 验证（Day 48-49）
**交付物**: `scripts/architecture/migrate/verify_phase4.sh`

```bash
#!/bin/bash
# 验证阶段4完成度

echo "🔍 检查数据重复..."
if [ -d "data/legal-docs" ] && [ -d "domains/legal-knowledge" ]; then
    echo "❌ 仍有重复数据"
    exit 1
else
    echo "✅ 无重复数据"
fi

echo "🔍 检查assets目录..."
if [ -d "assets/legal-knowledge" ] && [ -d "assets/patent-data" ]; then
    echo "✅ assets目录结构正确"
else
    echo "❌ assets目录结构不完整"
    exit 1
fi

echo "🔍 检查gitignore..."
if grep -q "*.backup" .gitignore; then
    echo "✅ gitignore规则完善"
else
    echo "❌ gitignore规则缺失"
    exit 1
fi

echo "✅ 阶段4验证完成"
```

### 验收标准
- ✅ 无重复数据文件
- ✅ 数据与代码分离
- ✅ `.gitignore`规则完善
- ✅ 数据路径配置化

---

## 📊 整体验收标准

### 最终目标

| 指标 | 优化前 | 目标 | 验证方法 |
|-----|-------|------|---------|
| core子目录数 | 164 | <30 | `ls -d core/*/ \| wc -l` |
| 根目录数 | 30+ | <20 | `ls -d */ \| wc -l` |
| 反向依赖 | 5处 | 0 | `grep -r "from services\." core/` |
| 数据重复 | 54M×2 | 0 | `diff -rq data/ domains/` |
| 测试通过率 | >90% | ≥基线 | `pytest tests/` |
| 测试覆盖率 | 70% | ≥70% | `pytest --cov` |

### 回滚机制

每个阶段完成后，创建新快照：
```bash
./scripts/architecture/create_snapshot.sh phase1
```

如需回滚：
```bash
./scripts/architecture/rollback.sh phase1
```

---

## 🎯 预期收益

### 开发效率
- ✅ 新人上手时间减少60%（3天→1天）
- ✅ 模块定位时间减少70%
- ✅ 代码审查效率提升50%

### 代码质量
- ✅ 测试可独立运行，覆盖率提升15%
- ✅ 循环依赖消除，重构风险降低80%
- ✅ 业务逻辑清晰，维护成本降低40%

### 资源优化
- ✅ 存储成本降低50%（数据去重）
- ✅ 构建时间减少30%（依赖优化）
- ✅ 部署包体积减少40%

---

## 📞 支持与反馈

如有问题或建议，请联系：
- **维护者**: 徐健 (xujian519@gmail.com)
- **文档**: `docs/architecture/`
- **问题追踪**: GitHub Issues

---

**祝重构顺利！🚀**
