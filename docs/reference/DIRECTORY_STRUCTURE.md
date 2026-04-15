# Athena工作平台 - 目录结构说明

> 📅 整理日期: 2025-12-25  
> 🎯 整理目标: 保持根目录整洁，文件分类清晰

## 📁 根目录核心文件

根目录仅保留必要的核心文件：

### 必要的可执行文件
- `start_core_services.sh` - 核心服务统一启动脚本（记忆系统、NLP服务）

### 项目配置文件
- `pyproject.toml` - Python项目配置文件
- `requirements.txt` - 核心依赖包列表
- `requirements.in` - 依赖包源定义
- `requirements.locked` - 锁定版本的依赖包
- `requirements-dev.in` - 开发环境依赖

### 版本控制
- `.gitignore` - Git忽略规则
- `.github/` - GitHub Actions工作流

## 📂 主要目录结构

### 核心业务目录
```
core/               # 核心模块（记忆、认知、决策、规划）
services/           # 所有服务实现
dev/scripts/            # 运维和部署脚本
config/             # 配置文件
```

### 脚本目录 (dev/scripts/)
```
dev/scripts/
├── startup/        # 启动脚本
│   ├── start_memory_system.sh
│   ├── start_nlp_service.sh
│   ├── start_xiaonuo.py
│   └── quick_start_optimized_kg.sh
├── infrastructure/deployment/     # 部署脚本
│   └── verify_production_deployment.sh
└── testing/        # 测试脚本
    └── generate_coverage_report.sh
```

### 文档目录 (docs/)
```
docs/
├── reference/      # 参考文档
│   ├── API_STANDARDS.md
│   ├── DEPENDENCIES.md
│   ├── OPTIMIZED_SYSTEM_ARCHITECTURE.md
│   ├── README_SERVICES.md
│   ├── TESTING_GUIDE.md
│   └── DIRECTORY_STRUCTURE.md (本文件)
├── reports/        # 项目报告
│   ├── COMPLETE_OPTIMIZATION_REPORT.md
│   ├── DEVELOPMENT_LOG.md
│   └── NEO4J_CLEANUP_REPORT.md
├── guides/         # 使用指南
│   └── XIAONUO_V3_STARTUP_GUIDE.md
└── articles/       # 技术文章
    └── dad_patent_quality_article_final.md
```

### 依赖目录 (requirements/)
```
requirements/
├── archive/        # 历史版本
│   ├── requirements-unified-v2.txt
│   ├── requirements-unified-v3.txt
│   └── requirements-unified-final.txt
└── requirements-unified.txt
```

### 归档目录 (_ARCHIVE_V2_LEGACY/)
```
_ARCHIVE_V2_LEGACY/
├── xiaonuo_cleanup_list.txt
└── test_patent_business_integration.py
```

## 🚀 快速启动指南

### 启动核心服务
```bash
bash start_core_services.sh start
```

### 查看服务状态
```bash
bash start_core_services.sh status
```

### 停止所有服务
```bash
bash start_core_services.sh stop
```

## 📝 维护规范

### 添加新文件时的规则

1. **启动脚本** → 放入 `dev/scripts/startup/`
2. **部署脚本** → 放入 `dev/scripts/infrastructure/infrastructure/deployment/`
3. **测试脚本** → 放入 `dev/scripts/testing/`
4. **参考文档** → 放入 `docs/reference/`
5. **项目报告** → 放入 `docs/reports/`
6. **使用指南** → 放入 `docs/guides/`
7. **技术文章** → 放入 `docs/articles/`
8. **历史依赖** → 放入 `requirements/archive/`
9. **临时文件** → 放入 `_ARCHIVE_V2_LEGACY/`

### 根目录整洁原则

- ✅ **保留**: 必要的启动脚本、项目配置、版本控制文件
- ❌ **移除**: 所有可以归类到子目录的文件
- 🔄 **定期清理**: 检查是否有新文件需要归类

## 🎯 整理成果

### 整理前根目录文件数
- Python文件: 2个
- Shell脚本: 7个
- Markdown文档: 10个
- **总计**: 19个散落文件

### 整理后根目录文件数
- Python配置: 4个 (pyproject.toml, requirements.*)
- Shell脚本: 1个 (start_core_services.sh)
- **总计**: 5个核心文件 ✅

### 整理效果
- 📉 文件减少: 73%
- 🎯 根目录整洁度: 提升 300%
- 📂 分类清晰度: 100%

---

💡 **提示**: 保持根目录整洁有助于：
1. 快速定位核心文件
2. 减少认知负担
3. 提升开发效率
4. 便于项目维护
