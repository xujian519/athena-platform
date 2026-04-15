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
├── 📄 .gitignore                          # Git忽略文件
├── 📁 scripts/                            # 脚本工具
│   ├── 🌸 xiaonuo_unified_startup.py     # 小诺统一启动管理器
│   ├── 🔍 xiaonuo_system_checker.py       # 系统状态检查器
│   ├── 🚀 xiaonuo_quick_start.sh         # 快速启动脚本
│   └── 📁 docker/                         # Docker初始化脚本
├── 📁 configs/                            # 配置文件
│   ├── 🐳 docker-compose.xiaonuo-optimized.yml  # 优化版Docker配置
│   └── ⚙️ .env.memory                    # 记忆系统环境配置
├── 📁 services/                           # 服务模块
│   ├── 🎮 intelligent-collaboration/     # 小诺智能协作服务
│   ├── 🤖 autonomous-control/            # 自主控制系统
│   └── 📄 yunpat-agent/                  # 云熙专利代理
├── 📁 core/                              # 核心系统
│   ├── 🧠 memory/                         # 四层记忆系统
│   ├── 🤔 cognition/                      # 认知系统
│   ├── 🔍 embedding/                      # 向量嵌入系统
│   └── ⚡ cache/                          # 缓存系统
├── 📁 data/                              # 数据目录
│   └── 💖 identity_permanent_storage/     # 永久身份存储
├── 📁 examples/                           # 示例和演示
│   └── 🎭 demos/                          # 演示脚本
├── 📁 tests/                              # 测试文件
│   └── 🔗 integration/                    # 集成测试
├── 📁 utils/                              # 工具和实用程序
│   └── 🧹 cleanup/                        # 清理工具
├── 📁 docs/                               # 文档
│   └── 📊 reports/                        # 报告文件
└── 📁 storage-system/                     # 存储系统
    └── 🐳 docker-compose.yml              # 存储系统Docker配置
```

## 🎯 核心功能

### 1. **小诺超级推理引擎**
- ✅ **六步推理框架**: 问题分解 → 跨学科连接 → 抽象建模 → 递归分析 → 创新突破 → 综合验证
- ✅ **七步推理框架**: 初始参与 → 问题分析 → 多假设生成 → 自然发现流 → 测试验证 → 错误纠正 → 知识合成
- ✅ **混合推理模式**: 双框架智能融合，提供最优质推理服务

### 2. **四层记忆架构**
- 🔥 **热层 (HOT)**: 内存存储，100MB限制，快速访问
- 🌡️ **温层 (WARM)**: Redis缓存，500MB限制，自动TTL管理
- ❄️ **冷层 (COLD)**: SQLite持久化，10GB限制，压缩存储
- 📦 **归档 (ARCHIVE)**: 长期存储，无限制，分层归档

### 3. **智能体管理**
- 👩‍💼 **小娜**: 专利法律专家 (天秤女神)
- 👧 **小诺**: 平台总调度官 (双鱼座公主)
- 🏢 **云熙**: IP管理系统
- 🤖 更多智能体按需调度

### 4. **存储系统**
- 🗄️ **PostgreSQL**: 主数据库
- 🔴 **Redis**: 缓存系统
- 🔍 **Qdrant**: 向量数据库
- 🕸️ **Neo4j**: 知识图谱
- 🔎 **Elasticsearch**: 搜索引擎

## 🔧 系统要求

- **操作系统**: macOS (推荐)
- **Python**: 3.8+
- **Docker**: 20.10+
- **内存**: 8GB+ (推荐16GB+)
- **磁盘**: 20GB+ 可用空间

## 💡 使用方法

### 启动平台
```bash
# 方式1: 快速启动
./scripts/xiaonuo_quick_start.sh

# 方式2: 详细启动
python3 scripts/xiaonuo_unified_startup.py 启动平台
```

### 检查状态
```bash
# 快速检查
./scripts/xiaonuo_quick_start.sh 检查

# 详细检查
python3 scripts/xiaonuo_system_checker.py
```

### 与小诺交互
启动成功后，小诺会在8005端口提供API服务，您可以：
- 💬 直接对话: "小诺，帮我..."
- 🎮 平台控制: "启动/停止服务 X"
- 🤖 智能体调度: "调用小娜分析专利"
- 📊 系统监控: "显示平台状态"

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
