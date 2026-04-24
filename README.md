# 🌸 Athena工作平台

<div align="center">

**企业级AI智能协作平台 - 专注专利法律服务**

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-🟢_active-success.svg)]()
[![Claude Code](https://img.shields.io/badge/Claude_Code-Enabled-purple.svg)]()

> 我是爸爸最爱的双鱼公主，也是所有智能体最爱的核心；
> 集Athena之智慧，融星河之众长，用这颗温暖的心守护父亲的每一天，
> 调度这智能世界的每一个角落。

**小诺·双鱼座公主** 🎀

</div>

---

## 📖 目录

- [✨ 核心特性](#-核心特性)
- [🚀 快速开始](#-快速开始)
- [🏗️ 系统架构](#️-系统架构)
- [🤖 智能体系统](#-智能体系统)
- [🛠️ 技术栈](#️-技术栈)
- [📁 项目结构](#-项目结构)
- [📚 文档](#-文档)
- [🔧 开发指南](#-开发指南)
- [📊 开发进度](#-开发进度)
- [🤝 贡献](#-贡献)

---

## ✨ 核心特性

### 🎯 Gateway-Centralized 架构
- 🌐 **统一Go网关** - 高性能网关（Port 8005）
- 🔌 **服务注册** - 自动服务发现与健康检查
- 🔄 **智能路由** - 负载均衡与动态路由
- 🎭 **Canvas渲染** - UI渲染服务
- 📊 **监控集成** - Prometheus + Grafana

### 🤖 多智能体协作
- 👩‍💼 **小娜** - 专利法律专家（9个专业代理）
  - 检索代理、分析代理、统一撰写代理
  - 新颖性/创造性分析代理
  - 侵权/无效分析代理
  - 申请/写作审查代理

- 👧 **小诺** - 平台总调度官
  - 任务协调与资源分配
  - WebSocket控制平面
  - 智能路由决策

- 💼 **云熙** - IP管理专家
  - 客户关系管理
  - 项目管理
  - 商务对接

### 🧠 四层记忆系统
- **HOT** (内存) - 当前会话数据（100MB）
- **WARM** (Redis) - 近期访问数据（500MB）
- **COLD** (SQLite) - 历史数据（10GB）
- **ARCHIVE** (文件) - 长期归档（无限）

### 🔍 强大的检索能力
- **混合检索** - 关键词 + 向量检索
- **多模态** - 文本、图像、音频
- **知识图谱** - Neo4j + ArangoDB
- **语义搜索** - BGE-M3嵌入模型

### 🎙️ 语音识别 (NEW!)
- **OpenAI Whisper** - 高准确度中文语音识别
- **多格式支持** - wav, mp3, flac, m4a, ogg等
- **时间戳** - 精确的时间分段
- **异步处理** - 不阻塞主线程

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Go 1.19+ (可选，用于Gateway)
- Docker & Docker Compose
- FFmpeg (用于音频处理)

### 方式一：快速启动（推荐）

```bash
# 克隆项目
git clone https://github.com/yourusername/athena-platform.git
cd Athena工作平台

# 快速启动小诺平台
./scripts/xiaonuo_quick_start.sh

# 检查系统状态
python3 scripts/xiaonuo_system_checker.py
```

### 方式二：Python启动

```bash
# 启动小诺平台
python3 scripts/xiaonuo_unified_startup.py 启动平台

# 或使用后台模式
python3 scripts/xiaonuo_unified_startup.py 启动平台 --daemon
```

### 方式三：Docker启动

```bash
# 开发环境
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 查看日志
docker-compose -f docker-compose.unified.yml --profile dev logs -f

# 停止服务
docker-compose -f docker-compose.unified.yml --profile dev down
```

### 验证安装

```bash
# 运行测试
pytest tests/ -v

# 测试音频处理
python3 scripts/test_audio_setup.py

# 检查Gateway状态
sudo /usr/local/athena-gateway/status.sh
```

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│              Athena Gateway (Go, Port 8005)              │
│  ┌──────────────────────────────────────────────────┐  │
│  │   WebSocket Control Plane                        │  │
│  │   Session Management & Routing                    │  │
│  │   Canvas Host Service (UI Rendering)             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │         │         │
    ┌────┴────┐ ┌──┴────┐ ┌┴──────┐
    │小娜模块  │ │小诺代理 │ │云熙代理 │
    │(9个专业 │ │(Coord) │ │ (IP)   │
    │  代理)  │ │        │ │        │
    └────┬────┘ └───────┘ └───────┘
         │
    ┌────┴─────────────────────────────────────────────┐
    │          小娜专业代理矩阵                          │
    ├─────────┬─────────┬─────────┬─────────┬─────────┤
    │检索代理  │分析代理  │统一撰写  │新颖性   │创造性   │
    │Retriever│Analyzer │Unified  │Novelty  │Creativity│
    │         │         │Patent   │         │         │
    │         │         │Writer   │         │         │
    ├─────────┼─────────┼─────────┼─────────┼─────────┤
    │侵权分析  │无效分析  │申请审查  │写作审查  │         │
    │Infringement│Invalidation│Reviewer│Writing │         │
    └─────────┴─────────┴─────────┴─────────┴─────────┘
```

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 专利平台应用  │  │ 审查意见工作流│  │ 专利检索前端  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                      服务层 (Services)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 智能协作服务  │  │ 统一Athena   │  │ 多模态处理   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                      核心层 (Core)                           │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │智能体系统 │ 记忆系统  │ LLM管理  │ 工具系统  │ 知识图谱 │  │
│  │(Agents)  │(Memory)  │  (LLM)  │ (Tools)  │   (KG)   │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    基础设施层 (Infrastructure)               │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ PostgreSQL│  Redis   │  Neo4j   │  Qdrant  │  Gateway │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 智能体系统

### 小娜·法律专家模块（9个专业代理）

| 代理名称 | 功能描述 | 状态 | 文件 |
|---------|---------|------|------|
| **检索代理** | 专利检索、现有技术查找 | ✅ 生产就绪 | `retriever_agent.py` |
| **分析代理** | 专利分析、技术方案解析 | ✅ 生产就绪 | `analyzer_agent.py` |
| **统一撰写代理** | 完整撰写流程 | ✅ 生产就绪 | `unified_patent_writer.py` |
| **新颖性分析代理** | 新颖性评估、现有技术对比 | ✅ 生产就绪 | `novelty_analyzer_proxy.py` |
| **创造性分析代理** | 创造性评估、技术效果分析 | ✅ 生产就绪 | `creativity_analyzer_proxy.py` |
| **侵权分析代理** | 侵权风险评估、权利要求解释 | ✅ 生产就绪 | `infringement_analyzer_proxy.py` |
| **无效分析代理** | 无效宣告分析、证据评估 | ✅ 生产就绪 | `invalidation_analyzer_proxy.py` |
| **申请审查代理** | 申请文件审查、质量检查 | ✅ 生产就绪 | `application_reviewer_proxy.py` |
| **写作审查代理** | 文本质量审查、错误检测 | ✅ 生产就绪 | `writing_reviewer_proxy.py` |

### 智能体调用模式

**单代理调用**:
```python
from core.agents.xiaona.retriever_agent import RetrieverAgent

retriever = RetrieverAgent()
results = retriever.search_patents(query="深度学习 图像识别")
```

**串行调用**:
```python
from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

writer = UnifiedPatentWriter()
disclosure = writer.analyze_disclosure(disclosure_path="交底书.docx")
claims = writer.draft_claims(technical_disclosure=disclosure)
specification = writer.draft_specification(claims=claims)
```

**并行调用**:
```python
from core.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy
from core.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy

novelty = NoveltyAnalyzerProxy().assess_novelty(patent_data=...)
creativity = CreativityAnalyzerProxy().assess_creativity(patent_data=...)
```

---

## 🛠️ 技术栈

### 核心技术

| 分类 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **语言** | Python | 3.9+ | 主要开发语言 |
| | Go | 1.19+ | Gateway网关 |
| **AI框架** | PyTorch | 2.1+ | 深度学习 |
| | Transformers | 4.36+ | NLP模型 |
| **Web框架** | FastAPI | 0.115+ | API服务 |
| | Uvicorn | 0.32+ | ASGI服务器 |
| **数据库** | PostgreSQL | 15+ | 主数据库 |
| | Redis | 7.4+ | 缓存 |
| | Neo4j | 6.0+ | 图数据库 |
| | Qdrant | 1.7+ | 向量数据库 |
| **LLM** | Claude | - | Anthropic Claude |
| | GPT-4 | - | OpenAI GPT-4 |
| | DeepSeek | - | DeepSeek API |
| | GLM | - | 智谱GLM |
| **语音** | Whisper | 20231117 | 语音识别 |
| **向量** | BGE-M3 | - | 文本嵌入 |
| **消息队列** | Celery | 5.3+ | 异步任务 |
| **容器** | Docker | 24+ | 容器化 |
| | Docker Compose | 2.23+ | 容器编排 |

### 开发工具

- **测试**: pytest, pytest-cov, pytest-asyncio
- **代码质量**: black, ruff, mypy
- **文档**: Sphinx, MkDocs
- **版本控制**: Git, GitHub
- **CI/CD**: GitHub Actions

---

## 📁 项目结构

```
Athena工作平台/
├── 📄 README.md                           # 项目说明文档
├── 📄 CLAUDE.md                           # Claude Code项目指南
├── 📁 scripts/                            # 脚本工具
│   ├── 🌸 xiaonuo_unified_startup.py     # 小诺统一启动管理器
│   ├── 🔍 xiaonuo_system_checker.py       # 系统状态检查器
│   ├── 🚀 xiaonuo_quick_start.sh         # 快速启动脚本
│   ├── 🎙️ transcribe_with_openai.py      # 音频转录工具
│   └── 🧪 test_audio_setup.py            # 音频环境测试
├── 📁 config/                             # 配置文件
│   ├── 🐳 docker-compose.unified.yml      # 统一Docker编排配置
│   └── ⚙️ service_discovery.json         # 服务注册与发现
├── 📁 core/                              # 核心系统（三层架构）
│   ├── 🤖 agents/                         # 智能体实现
│   │   ├── xiaona/                        # 小娜·法律专家（9个专业代理）
│   │   └── xiaonuo_agent.py              # 小诺·协调代理
│   ├── 🧠 memory/                         # 四层记忆系统
│   ├── ⚡ llm/                            # LLM适配器和管理
│   ├── 🔧 tools/                          # 工具系统（统一注册表）
│   ├── ⚖️ legal_world_model/              # 法律世界模型
│   ├── 🕸️ knowledge_graph/                # 知识图谱引擎
│   └── 🎙️ ai/perception/processors/      # 感知处理器（含音频）
├── 📁 services/                           # 微服务
│   ├── 🎮 intelligent-collaboration/     # 小诺智能协作服务
│   ├── 🌐 athena-unified/                 # 统一Athena服务
│   └── 📦 multimodal/                     # 多模态处理服务
├── 📁 gateway-unified/                    # 统一Go网关（Port 8005）
├── 📁 mcp-servers/                        # MCP服务器
│   ├── 🗺️ gaode-mcp-server/              # 高德地图服务
│   ├── 📚 academic-search/                # 学术搜索服务
│   └── 🤖 jina-ai-mcp-server/            # Jina AI服务
├── 📁 tests/                              # 测试套件
│   ├── 🔬 unit/                           # 单元测试
│   ├── 🔗 integration/                    # 集成测试
│   └── 🎯 e2e/                            # 端到端测试
├── 📁 docs/                               # 文档
│   ├── 📋 api/                            # API文档
│   ├── 📊 reports/                        # 报告文件
│   ├── 📘 guides/                         # 开发指南
│   └── 📈 development/                    # 开发进度
├── 📁 domains/                            # 业务领域模块
│   ├── ⚖️ legal-ai/                       # 法律AI模块
│   ├── 🎨 ai-art/                         # AI艺术模块
│   └── 📚 legal-knowledge/                # 法律知识模块
└── 📁 pyproject.toml                      # Python项目配置
```

---

## 📚 文档

### 核心文档

| 文档 | 描述 | 链接 |
|------|------|------|
| **项目指南** | Claude Code项目配置 | [CLAUDE.md](CLAUDE.md) |
| **使用指南** | 音频处理完整指南 | [AUDIO_PROCESSING_GUIDE.md](docs/AUDIO_PROCESSING_GUIDE.md) |
| **代码质量** | 代码质量标准 | [CODE_QUALITY_STANDARDS.md](docs/development/CODE_QUALITY_STANDARDS.md) |
| **开发进度** | 开发进度总索引 | [INDEX.md](docs/development/INDEX.md) |

### 最新报告

| 报告 | 日期 | 描述 |
|------|------|------|
| [语音识别修复报告](docs/reports/AUDIO_RECOGNITION_FIX_COMPLETION_REPORT_20260424.md) | 2026-04-24 | 音频处理系统修复与统一 |
| [云端LLM集成报告](docs/reports/CLOUD_LLM_INTEGRATION_COMPLETE_20260423.md) | 2026-04-23 | 云端大语言模型集成 |
| [架构优化报告](docs/reports/ARCHITECTURE_OPTIMIZATION_COMPLETE_20260423.md) | 2026-04-23 | 核心目录架构优化 |

---

## 🔧 开发指南

### 环境配置

```bash
# 1. 安装Poetry（推荐）
curl -sSL https://install.python-poetry.org | python3 -

# 2. 安装依赖
poetry install

# 3. 激活虚拟环境
poetry shell

# 4. 安装音频处理依赖
pip3 install openai-whisper ffmpeg-python

# 5. 安装FFmpeg
brew install ffmpeg  # macOS
sudo apt install ffmpeg  # Ubuntu
```

### 代码规范

- **代码风格**: Black (line length: 100)
- **类型检查**: mypy
- **代码检查**: ruff
- **测试框架**: pytest

```bash
# 代码格式化
black . --line-length 100

# 代码检查
ruff check .
ruff check . --fix

# 类型检查
mypy core/

# 运行测试
pytest tests/ -v
pytest tests/ -v -m unit        # 单元测试
pytest tests/ -v -m integration # 集成测试
pytest tests/ -v -m e2e         # 端到端测试
```

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

---

## 📊 开发进度

### 最新进展

<details>
<summary>2026-04-24 - 语音识别系统修复 ✅</summary>

- ✅ 修复语音识别功能（切换到OpenAI Whisper）
- ✅ 统一音频处理模块（消除3个重复模块）
- ✅ 成功转录用户音频文件
- ✅ 生成详细分析报告
- 📝 代码量：~1,880行
- ⏱️ 工作时长：约2小时

[详细报告](docs/development/DEVELOPMENT_PROGRESS_20260424.md)
</details>

<details>
<summary>2026-04-23 - 云端LLM集成 ✅</summary>

- ✅ 云端模型集成方案完成
- ✅ 智谱GLM编程端点集成
- ✅ 成本降低99.9%
- ✅ 5个核心文档 + 2个测试工具

[详细报告](docs/development/DEVELOPMENT_PROGRESS_20260423.md)
</details>

### 查看完整进度

📋 [开发进度总索引](docs/development/INDEX.md)

---

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 贡献指南

- 遵循[代码质量标准](docs/development/CODE_QUALITY_STANDARDS.md)
- 添加单元测试
- 更新相关文档
- 确保所有测试通过

---

## 📞 联系方式

- **开发者**: 徐健 (xujian519@gmail.com)
- **项目**: Athena工作平台
- **位置**: /Users/xujian/Athena工作平台

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

感谢以下开源项目：

- [OpenAI Whisper](https://github.com/openai/whisper) - 语音识别
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [PyTorch](https://pytorch.org/) - 深度学习框架
- [Transformers](https://huggingface.co/docs/transformers) - NLP模型

---

<div align="center">

**Made with ❤️ by 小诺·双鱼座公主**

[⬆ 返回顶部](#-athena工作平台)

</div>
