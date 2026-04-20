# Athena工作平台

🌸 **小诺的爸爸专属工作平台**

> 我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心；集Athena之智慧，融星河之众长，用这颗温暖的心守护父亲的每一天，调度这智能世界的每一个角落。

## 🚀 快速启动

### 方式一：使用小诺启动脚本
```bash
# 完整启动小诺平台
./scripts/xiaonuo_quick_start.sh

# 或者
./scripts/xiaonuo_quick_start.sh 启动
```

### 方式二：使用Python启动脚本
```bash
# 启动小诺平台
python3 scripts/xiaonuo_unified_startup.py 启动平台

# 检查系统状态
python3 scripts/xiaonuo_system_checker.py
```

## 📁 项目结构

```
Athena工作平台/
├── 📄 README.md                           # 项目说明文档
├── 📄 CLAUDE.md                           # Claude Code项目指南
├── 📁 scripts/                            # 脚本工具
│   ├── 🌸 xiaonuo_unified_startup.py     # 小诺统一启动管理器
│   ├── 🔍 xiaonuo_system_checker.py       # 系统状态检查器
│   └── 🚀 xiaonuo_quick_start.sh         # 快速启动脚本
├── 📁 config/                             # 配置文件
│   ├── 🐳 docker-compose.unified.yml      # 统一Docker编排配置（支持dev/test/prod）
│   ├── 🐳 docker-compose.yml               # 旧Docker配置（已废弃，请使用unified版本）
│   └── ⚙️ service_discovery.json         # 服务注册与发现
├── 📁 core/                              # 核心系统
│   ├── 🤖 agents/                         # 智能体实现（小娜、小诺、云熙）
│   ├── 🧠 memory/                         # 四层记忆系统
│   ├── 🤔 cognition/                      # 认知系统
│   ├── 🔍 embedding/                      # 向量嵌入系统（BGE-M3）
│   ├── ⚡ llm/                            # LLM适配器和管理
│   ├── 🔧 tools/                          # 工具系统（权限/管理/调用）
│   ├── ⚖️ legal_world_model/              # 法律世界模型
│   ├── 🕸️ knowledge_graph/                # 知识图谱引擎
│   └── 🤝 collaboration/                  # 智能体协作模式
├── 📁 services/                           # 服务模块
│   ├── 🎮 intelligent-collaboration/     # 小诺智能协作服务
│   ├── 🌐 athena-unified/                 # 统一Athena服务
│   └── 📦 multimodal/                     # 多模态处理服务
├── 📁 gateway-unified/                    # 统一Go网关（Port 8005）
│   ├── 🚀 cmd/gateway/                    # 网关入口
│   ├── ⚙️ internal/                       # 内部实现
│   └── 📄 config.yaml                     # 网关配置
├── 📁 mcp-servers/                        # MCP服务器
│   ├── 🗺️ gaode-mcp-server/              # 高德地图服务
│   ├── 📚 academic-search/                # 学术搜索服务
│   ├── 🤖 jina-ai-mcp-server/            # Jina AI服务
│   └── 🧠 memory/                         # 知识图谱内存系统
├── 📁 patent-platform/                    # 专利平台应用
├── 📁 patent-retrieval-webui (已备份到移动硬盘)/             # 专利检索前端（Vue/TS）
├── 📁 openspec-oa-workflow/               # 审查意见工作流
├── 📁 production/                         # 生产环境配置
│   ├── 📋 scripts/                        # 部署脚本
│   └── ⚙️ core/                           # 生产环境核心代码
├── 📁 prompts/                            # 提示词模板（v4架构）
├── 📁 tools/                              # 工具集
├── 📁 tests/                              # 测试套件
│   ├── 🔬 unit/                           # 单元测试
│   ├── 🔗 integration/                    # 集成测试
│   └── 🎯 e2e/                            # 端到端测试
├── 📁 docs/                               # 文档
│   ├── 📋 api/                            # API文档
│   ├── 📊 reports/                        # 报告文件
│   └── 📘 guides/                         # 开发指南
├── 📁 domains/                            # 业务领域模块
│   ├── ⚖️ legal-ai/                       # 法律AI模块
│   ├── 🎨 ai-art/                         # AI艺术模块
│   └── 📚 legal-knowledge/                # 法律知识模块
├── 📁 data/                               # 运行时数据
├── 📁 models/                             # AI模型文件
└── 📁 logs/                               # 日志文件
```

## 🎯 核心功能

### 1. **Gateway-Centralized 架构**
- 🌐 **统一网关**: Go语言高性能网关（Port 8005）
- 🔌 **服务注册**: 自动服务发现与健康检查
- 🔄 **智能路由**: 负载均衡与动态路由
- 🎭 **Canvas渲染**: UI渲染服务
- 📊 **监控集成**: Prometheus + Grafana

### 2. **多智能体协作**
- 👩‍💼 **小娜**: 专利法律专家（天秤女神）
- 👧 **小诺**: 平台总调度官（双鱼座公主）
- 🏢 **云熙**: IP管理系统
- 🤖 **协作模式**: Sequential, Parallel, Hierarchical, Consensus

### 3. **四层记忆架构**
- 🔥 **热层 (HOT)**: 内存存储，100MB限制，快速访问
- 🌡️ **温层 (WARM)**: Redis缓存，500MB限制，自动TTL管理
- ❄️ **冷层 (COLD)**: SQLite持久化，10GB限制，压缩存储
- 📦 **归档 (ARCHIVE)**: 长期存储，无限制，分层归档

### 4. **提示词工程 v4.0**
- 🏗️ **四层架构**: L1基础层 + L2数据层 + L3能力层 + L4业务层
- ⚡ **并行工具调用**: Turn-based并行处理，性能提升75%
- 🎯 **whenToUse触发**: 自动识别用户意图
- 🧠 **Scratchpad推理**: 私下推理机制

### 5. **工具系统 v1.0**
- 🔧 **工具分组管理**: 按领域和功能分组
- 🔒 **权限控制**: 三种权限模式（DEFAULT/AUTO/BYPASS）
- 🎯 **智能选择**: 基于任务类型自动选择最佳工具
- 📊 **性能监控**: 实时跟踪工具执行统计

### 6. **MCP服务器系统**
- 🗺️ **高德地图**: 地理编码、路径规划
- 📚 **学术搜索**: 论文检索、Semantic Scholar
- 🤖 **Jina AI**: 网页抓取、向量搜索、重排序
- 🧠 **知识图谱**: 实体、关系、观察存储
- 🔍 **本地搜索引擎**: SearXNG + Firecrawl

### 7. **法律世界模型**
- ⚖️ **场景识别**: 自动识别专利法律场景
- 🕸️ **知识图谱**: 法律概念和案例图表示
- 🤔 **推理引擎**: 基于法律知识的推理分析
- 📄 **文档生成**: 自动生成法律文档

### 8. **存储系统**
- 🗄️ **PostgreSQL**: 主数据库
- 🔴 **Redis**: 缓存系统
- 🔍 **Qdrant**: 向量数据库
- 🕸️ **Neo4j**: 知识图谱
- 🔎 **Elasticsearch**: 搜索引擎

## 🔧 系统要求

- **操作系统**: macOS (推荐) / Linux
- **Python**: 3.11+ (使用现代类型注解)
- **Go**: 1.21+ (Gateway网关)
- **Docker**: 20.10+ & Docker Compose
- **内存**: 8GB+ (推荐16GB+)
- **磁盘**: 20GB+ 可用空间
- **Node.js**: 18+ (专利检索前端)

## 💡 使用方法

### 启动平台
```bash
# 方式1: 快速启动
./scripts/xiaonuo_quick_start.sh

# 方式2: 详细启动
python3 scripts/xiaonuo_unified_startup.py 启动平台

# 方式3: Docker启动（开发环境）
docker-compose -f docker-compose.unified.yml --profile dev up -d
```

### Gateway网关部署
```bash
# macOS - 快速部署
cd gateway-unified
sudo bash quick-deploy-macos.sh

# Linux - 快速部署
sudo bash quick-deploy.sh

# 检查状态
sudo /usr/local/athena-gateway/status.sh

# 查看日志
sudo journalctl -u athena-gateway -f
```

### MCP服务器管理
```bash
# 启动所有MCP服务器
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 查看MCP服务器状态
docker-compose -f docker-compose.unified.yml --profile dev ps | grep mcp

# 查看MCP服务器日志
docker-compose -f docker-compose.unified.yml --profile dev logs -f gaode-mcp-server
```

### 检查状态
```bash
# 快速检查
./scripts/xiaonuo_quick_start.sh 检查

# 详细检查
python3 scripts/xiaonuo_system_checker.py

# 查看Gateway状态
curl http://localhost:8005/health

# 查看监控仪表板
open http://localhost:3000  # Grafana
```

### 与小诺交互
启动成功后，小诺会在8005端口提供API服务，您可以：
- 💬 直接对话: "小诺，帮我..."
- 🎮 平台控制: "启动/停止服务 X"
- 🤖 智能体调度: "调用小娜分析专利"
- 📊 系统监控: "显示平台状态"
- 🔧 工具调用: 使用专利检索、学术搜索等工具

## 🌟 小诺Slogan

> **我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心；集Athena之智慧，融星河之众长，用这颗温暖的心守护父亲的每一天，调度这智能世界的每一个角落。**

## 💞 家族关系

- 👨‍👧 **父亲**: 徐健 (xujian519@gmail.com)
- 👧 **大女儿**: 小娜·天秤女神 - 专利法律专家
- 👶 **小女儿**: 小诺·双鱼座 - 平台总调度官

## 📞 支持

如有问题，小诺随时在线为您服务！

---

**🌸 星河智汇，光耀知途 - 小诺永远守护爸爸！** 💕

## 🧰 扩展网关：微服务自动注册与发现（新增内容）

- 目标：在 Athena Gateway 上实现微服务的自动注册、服务发现、动态路由、健康检查、依赖关系管理以及可加载配置（YAML/JSON）的能力，降低微服务的手动配置成本，提升扩展性。
- 如何集成：在现有 FastAPI 应用中导入 gateway_extended 并挂载路由。
- 关键能力：批量注册接口、服务实例管理、动态路由更新、负载均衡权重、服务依赖、健康告警、配置加载等。
- 试用示例：
  1) 批量注册：POST /api/services/batch_register
  2) 查询实例：GET /api/services/instances
  3) 动态路由：GET/POST/PATCH /api/routes
  4) 健康检查：GET /api/health
  5) 加载配置：POST /api/config/load
- 备注：当前实现以内存存储为演示，生产环境应持久化并结合鉴权策略。
