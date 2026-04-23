# PROJECT KNOWLEDGE BASE

**生成时间**: 2026-02-20 00:47:49
**Commit**: 未提交
**分支**: main

## 概述

Athena工作平台是一个复杂的企业级AI智能体协作平台，集成多语言技术栈、四层记忆系统、多智能体管理和专利法律服务。

## 结构

```
Athena工作平台/
├── 📄 README.md                           # 项目说明文档
├── 📄 .gitignore                          # Git忽略文件
├── 📁 scripts/                            # 脚本工具
│   ├── 🌸 xiaonuo_unified_startup.py     # 小诺统一启动管理器
│   ├── 🔍 xiaonuo_system_checker.py       # 系统状态检查器
│   └── 🚀 xiaonuo_quick_start.sh         # 快速启动脚本
├── 📁 configs/                           # 配置文件
├── 📁 services/                           # 服务模块
│   ├── 🎮 intelligent-collaboration/     # 小诺智能协作服务
│   ├── 🤖 autonomous-control/            # 自主控制系统
│   └── 📄 yunpat-agent/                  # 云熙专利代理
├── 📁 core/                              # 核心系统
│   ├── 🧠 memory/                         # 四层记忆系统
│   ├── 🤔 cognition/                      # 认知系统
│   ├── 🔍 embedding/                      # 向量嵌入系统
│   ├── ⚡ cache/                          # 缓存系统
│   ├── 🧠 nlp/                           # 自然语言处理
│   ├── 📊 perception/                     # 感知系统
│   └── 📄 patent/                        # 专利处理
├── 📁 data/                              # 数据目录
├── 📁 examples/                           # 示例和演示
├── 📁 tests/                              # 测试文件
├── 📁 utils/                              # 工具和实用程序
├── 📁 docs/                               # 文档
├── 📁 mcp-servers/                        # MCP服务器集合
├── 📁 knowledge/                          # 知识库
├── 📁 tools/                              # 工具集
└── 📁 production/                         # 生产环境配置
```

## 在哪里查找

| 任务 | 位置 | 备注 |
|------|--------|-------|
| 启动平台 | scripts/xiaonuo_quick_start.sh 或 scripts/xiaonuo_unified_startup.py | 主要启动入口 |
| 核心逻辑 | core/ | 四层记忆、认知、嵌入、缓存系统 |
| 配置管理 | configs/ | Docker配置和环境变量 |
| 服务部署 | services/ | 智能协作、自主控制、专利代理 |
| 数据存储 | data/ | 永久身份存储、数据库文件 |
| MCP服务器 | mcp-servers/ | 各类MCP服务器实现 |
| 知识库 | knowledge/ | 设计模式、法律知识等 |
| 文档 | docs/ | 报告、迁移指南等 |
| 生产环境 | production/ | 生产脚本、配置、日志 |

## 代码映射

| 符号 | 类型 | 位置 | 引用数 | 角色 |
|--------|------|--------|------|------|
| XiaonuoStartup | Class | scripts/xiaonuo_unified_startup.py | 15 | 平台总调度器 |
| MemorySystem | Interface | core/memory/ | 23 | 四层记忆架构 |
| CognitionEngine | Class | core/cognition/ | 18 | 认知处理核心 |
| EmbeddingService | Class | core/embedding/ | 12 | 向量嵌入服务 |
| PatentProcessor | Class | core/patent/ | 25 | 专利数据处理 |
| YunpatAgent | Class | services/yunpat-agent/ | 8 | 云熙专利代理 |

## 约定

### 项目特定规则
- **多语言支持**: Python 3.8+, TypeScript, JavaScript, Shell脚本
- **命名规范**: 目录名支持中文+emoji，但代码文件使用英文命名
- **文档标准**: README.md为主要文档，配合emoji图标增强可读性
- **配置管理**: 使用configs/目录统一管理环境配置
- **测试结构**: tests/目录包含集成测试和单元测试

### 开发工具链
- **代码格式化**: Black (Python), Prettier (JS/TS)
- **类型检查**: mypy (Python), TypeScript编译器
- **代码检查**: ruff (Python), ESLint (JS/TS)
- **依赖管理**: pip (Python), npm/yarn (Node.js)

## 反模式（本项目）

### 禁止的模式
- **使用sudo**: 在工作流脚本中避免使用sudo，可能导致权限问题
- **硬编码路径**: 避免使用绝对路径，使用相对路径或环境变量
- **忽略错误**: 在Shell脚本中必须使用set -euo pipefail
- **未固定版本**: actions/checkout等必须使用固定版本号
- **中文目录名**: 虽然允许，但在自动化脚本中需注意转义

### DEPRECATED标记
- **DEMO_DEPRECATED_**: 演示用已废弃标记，应从生产代码中移除
- **DEPRECATED NOTICE**: Neo4j相关组件废弃通知
- **NEBULA_DEPRECATED**: NebulaGraph旧版本废弃标记

## 独特风格

### 雅典娜命名体系
- 小娜·天秤女神: 专利法律专家
- 小诺·双鱼座: 平台总调度官  
- 云熙: IP管理系统

### 四层记忆架构
- 热层(HOT): 内存存储，100MB限制
- 温层(WARM): Redis缓存，500MB限制
- 冷层(COLD): SQLite持久化，10GB限制
- 归档(ARCHIVE): 长期存储，无限制

## 命令

```bash
# 启动平台
./scripts/xiaonuo_quick_start.sh

# 检查系统状态
python3 scripts/xiaonuo_system_checker.py

# 统一启动管理
python3 scripts/xiaonuo_unified_startup.py 启动平台

# 代码格式化
black . --line-length 100
ruff check .

# 类型检查
mypy core/
tsc --noEmit

# 运行测试
pytest tests/
```

## 注意事项

- **路径兼容性**: emoji和中文目录名在部分Linux系统可能导致路径问题
- **依赖版本**: Python要求3.8+，Node.js建议使用LTS版本
- **内存管理**: 四层记忆系统有明确的容量限制和TTL策略
- **端口配置**: 默认服务端口8005，避免冲突
- **权限控制**: 生产环境配置在production/目录下
- **日志管理**: 大量日志文件在logs/目录，定期清理

---
*Athena工作平台智能体知识库 - 2026-02-20*