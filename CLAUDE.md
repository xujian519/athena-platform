# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Athena工作平台** is an enterprise-level AI agent collaboration platform focused on patent legal services. It integrates multiple intelligent agents (小娜/Xiaona - legal expert module with 9 specialized agents, 小诺/Xiaonuo - coordinator, 云熙/Yunxi - IP management) through a centralized Gateway architecture.

**Key Characteristics:**
- Multi-language tech stack: Python 3.11+, Go, TypeScript/JavaScript
- Four-tier memory system: HOT (memory) → WARM (Redis) → COLD (SQLite) → ARCHIVE
- Multi-agent architecture with WebSocket-based coordination
- **Specialized Agent System**: 小娜拆解为9个专业代理，覆盖专利全生命周期
- Patent-focused domain knowledge and workflows

## Common Development Commands

### Platform Startup

```bash
# Method 1: Quick start script
./scripts/xiaonuo_quick_start.sh

# Method 2: Python unified startup
python3 scripts/xiaonuo_unified_startup.py 启动平台

# Check system status
python3 scripts/xiaonuo_system_checker.py
```

### Python Development

```bash
# Install dependencies (使用 Poetry)
poetry install

# Code formatting (line length: 100)
black . --line-length 100

# Linting
ruff check .
ruff check . --fix  # Auto-fix issues

# Type checking
mypy core/

# Run tests (所有测试标记定义在 pyproject.toml)
pytest tests/ -v
pytest tests/ -v -m unit        # 单元测试（无外部依赖）
pytest tests/ -v -m integration # 集成测试（需要外部服务）
pytest tests/ -v -m e2e         # 端到端测试
pytest tests/ -v -m "not slow"  # 排除慢速测试
pytest tests/ -v -k "test_name" # 按名称匹配
pytest tests/ -n auto           # 并行测试（需要 pytest-xdist）

# 测试覆盖率
pytest --cov=core --cov-report=html  # 生成HTML报告
```

### Go Development (Gateway)

```bash
# In gateway-unified/
make build          # Build binary
make run-dev        # Run in development mode
make test           # Run tests
make fmt            # Format code
make lint           # Run linter
make docker-build   # Build Docker image
```

### Docker Operations

```bash
# Main docker-compose (开发环境)
docker-compose -f docker-compose.unified.yml --profile dev up -d
docker-compose -f docker-compose.unified.yml --profile dev logs -f
docker-compose -f docker-compose.unified.yml --profile dev down

# 测试环境
docker-compose -f docker-compose.unified.yml --profile test up -d

# 生产环境
docker-compose -f docker-compose.unified.yml --profile prod up -d

# Production deployment
./production/scripts/deploy_production.sh deploy
./production/scripts/status.sh           # Check service status
```

### Gateway Deployment
```bash
# macOS - Quick deploy
cd gateway-unified
sudo bash quick-deploy-macos.sh

# Linux - Quick deploy
sudo bash quick-deploy.sh

# Manual deployment
sudo bash deploy.sh

# Check status
sudo /usr/local/athena-gateway/status.sh

# View logs
sudo journalctl -u athena-gateway -f

# Stop service
sudo systemctl stop athena-gateway

# Restart service
sudo systemctl restart athena-gateway
```

### Database Operations

```bash
# PostgreSQL (via docker-compose)
docker-compose -f docker-compose.unified.yml --profile dev exec postgres psql -U athena -d athena

# Redis
docker-compose -f docker-compose.unified.yml --profile dev exec redis redis-cli -a ${REDIS_PASSWORD:-redis123}

# Qdrant
curl http://localhost:6333/collections
```

## High-Level Architecture

### Gateway-Centralized Architecture

The platform uses a centralized Gateway pattern for multi-agent coordination:

```
┌─────────────────────────────────────────────────────────┐
│              Athena Gateway (Port 8005)                  │
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

**代理调用模式**：
- **单代理调用**：直接调用特定专业代理
- **串行调用**：检索→分析→撰写（如专利申请流程）
- **并行调用**：新颖性+创造性同时评估（如可专利性评估）
- **组合调用**：多个代理协作完成复杂任务

### Directory Structure

```
Athena工作平台/
├── core/                    # Core system modules
│   ├── agents/             # Agent implementations (Xiaona, Xiaonuo, etc.)
│   ├── llm/                # LLM adapters and management
│   ├── embedding/          # Vector embedding services (BGE-M3)
│   ├── memory/             # Four-tier memory system
│   ├── cognition/          # Cognitive processing engine
│   ├── nlp/                # NLP services
│   ├── perception/         # Perception modules
│   ├── patent/             # Patent processing (含 drawing/)
│   ├── database/           # Database connection pooling
│   ├── collaboration/      # Agent collaboration patterns
│   ├── legal_world_model/  # 法律世界模型
│   └── knowledge_graph/    # 知识图谱引擎
├── services/               # Microservices
│   ├── intelligent-collaboration/  # Xiaonuo coordination service
│   ├── athena-unified/     # Unified Athena services
│   ├── multimodal/         # Multimodal processing service
│   └── legal-support/      # 法律支持服务
├── gateway-unified/        # 统一Go网关 (Port 8005) ⭐
├── domains/                # 业务领域模块 (legal-ai, ai-art, legal-knowledge)
├── tools/                  # 工具集
├── patent-platform/        # Patent platform application
├── patent_hybrid_retrieval/# Patent hybrid retrieval system
├── patent-retrieval-webui/ # 专利检索前端 (Vue/TS)
├── openspec-oa-workflow/   # 审查意见工作流
├── production/             # Production configurations and scripts
├── config/                 # 统一配置文件
├── mcp-servers/            # Model Context Protocol servers
├── prompts/                # 提示词模板
├── scripts/                # 脚本 (含 standalone/ 归并脚本)
├── tests/                  # Test suites (unit, integration, performance)
├── docs/                   # Documentation
├── reports/                # 报告输出
├── skills/                 # 技能定义
├── data/                   # 运行时数据 (.gitignore)
├── models/                 # AI模型文件 (.gitignore)
├── docker-compose.unified.yml  # 统一Docker编排配置（支持dev/test/prod/monitoring）
├── docker-compose.yml       # 旧Docker配置（已废弃）
├── pyproject.toml          # Python项目配置
└── start_xiaona.py         # 启动入口
```

### Core Systems

**1. Agent System** (`core/agents/`)

**1.1 基础架构**
- **Base Agent**: `base_agent.py` - Foundation for all agents
- **Base Component**: `agents/xiaona/base_component.py` - 专业代理基类

**1.2 核心智能体**
- **Xiaonuo (小诺·双鱼座)**: Platform coordinator agent - 平台总调度官
- **Yunxi (云熙)**: IP management agent - IP管理专家

**1.3 小娜专业代理模块（9个专业代理）**

小娜已从单一代理拆解为9个专业代理，覆盖专利全生命周期：

| 代理名称 | 文件 | 功能 | 状态 |
|---------|------|------|------|
| **检索代理** | `retriever_agent.py` | 专利检索、现有技术查找 | ✅ 生产就绪 |
| **分析代理** | `analyzer_agent.py` | 专利分析、技术方案解析 | ✅ 生产就绪 |
| **统一撰写代理** | `unified_patent_writer.py` | 完整撰写流程（交底书分析→权利要求→说明书），整合原WriterAgent和PatentDraftingProxy | ✅ 生产就绪 |
| **新颖性分析代理** | `novelty_analyzer_proxy.py` | 新颖性评估、现有技术对比 | ✅ 生产就绪 |
| **创造性分析代理** | `creativity_analyzer_proxy.py` | 创造性评估、技术效果分析 | ✅ 生产就绪 |
| **侵权分析代理** | `infringement_analyzer_proxy.py` | 侵权风险评估、权利要求解释 | ✅ 生产就绪 |
| **无效分析代理** | `invalidation_analyzer_proxy.py` | 无效宣告分析、证据评估 | ✅ 生产就绪 |
| **申请审查代理** | `application_reviewer_proxy.py` | 申请文件审查、质量检查 | ✅ 生产就绪 |
| **写作审查代理** | `writing_reviewer_proxy.py` | 文本质量审查、错误检测 | ✅ 生产就绪 |

**架构特点**：
- 每个代理独立部署、独立调用
- 共享 `base_component.py` 基类能力
- 支持组合调用完成复杂任务
- 统一健康检查和监控接口

**1.4 专业代理调用示例**

```python
# 单代理调用 - 专利检索
from core.agents.xiaona.retriever_agent import RetrieverAgent
retriever = RetrieverAgent()
results = retriever.search_patents(query="深度学习 图像识别")

# 串行调用 - 专利申请流程（使用统一撰写代理）
from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter
writer = UnifiedPatentWriter()
disclosure = writer.analyze_disclosure(disclosure_path="交底书.docx")
claims = writer.draft_claims(technical_disclosure=disclosure)
specification = writer.draft_specification(claims=claims)

# 并行调用 - 可专利性评估
from core.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy
from core.agents.xiaona.creativity_analyzer_proxy import CreativityAnalyzerProxy
novelty = NoveltyAnalyzerProxy().assess_novelty(patent_data=...)
creativity = CreativityAnalyzerProxy().assess_creativity(patent_data=...)

# 组合调用 - 无效宣告分析
from core.agents.xiaona.invalidation_analyzer_proxy import InvalidationAnalyzerProxy
invalidation = InvalidationAnalyzerProxy()
analysis = invalidation.analyze_invalidation(
    patent_number="CN201921401279.9",
    evidence_list=["D1", "D2", "D3"]
)
```

**1.5 专业代理协作模式**

| 任务类型 | 代理组合 | 调用模式 | 示例 |
|---------|---------|---------|------|
| 专利申请 | 检索→分析→统一撰写→审查 | 串行 | 交底书→申请文件 |
| 可专利性评估 | 新颖性+创造性 | 并行 | 技术方案→评估报告 |
| 无效宣告 | 检索→无效分析→侵权分析 | 混合 | 证据组合→无效报告 |
| 专利撰写 | 统一撰写代理+写作审查 | 串行 | 初稿→审查→定稿 |
| FTO分析 | 检索→侵权分析 | 串行 | 技术方案→FTO报告 |

**2. LLM Management** (`core/llm/`)
- **Unified Manager**: `unified_llm_manager.py` - Central LLM orchestration
- **Adapters**: Support for Claude, GPT-4, DeepSeek, GLM, Qwen, Ollama
- **Response Cache**: Caching layer for LLM responses
- **Model Selector**: Intelligent model routing

**3. Embedding System** (`core/embedding/`)
- **BGE-M3**: Primary embedding model (768 dimensions)
- **Unified Service**: `unified_embedding_service.py`
- **Multimodal**: Image + text vectorization support

**4. Memory System** (`core/memory/`)
- Four-tier architecture: HOT → WARM → COLD → ARCHIVE
- Capacity limits with TTL policies
- Automatic promotion/demotion between tiers

**5. Collaboration Patterns** (`core/collaboration/`)
- **Patterns**: Sequential, Parallel, Hierarchical, Consensus
- **Orchestrator**: On-demand agent spawning
- **Protocol**: Enhanced agent communication

**6. Legal World Model** (`core/legal_world_model/`)
- **Scenario Identifier**: Automatic recognition of patent legal scenarios (侵权分析, 无效宣告, 权利要求)
- **Knowledge Graph**: Legal concepts and case graph representation
- **Reasoning Engine**: Legal knowledge-based reasoning and analysis
- **Document Generator**: Automatic generation of legal documents (分析报告, 意见书)
- **Persistence**: Triple-database architecture (PostgreSQL + Neo4j + Qdrant) for legal knowledge persistence

**7. Knowledge Graph System** (`core/knowledge_graph/`)
- **Integration Layer**: `kg_integration.py` - 统一API和数据模型
- **Graph Engines**: Neo4j (`neo4j_graph_engine.py`) and ArangoDB (`arango_engine.py`) support
- **Legal Reasoning**: `legal_kg_reasoning_enhancer.py` - 法律知识图谱推理增强
- **Data Import**: `patent_guideline_importer.py` - 专利审查指南导入
- **Architecture Note**: 采用扁平架构（不同于 `core/llm/` 的分层架构），适配多种图数据库和业务特性
- **Documentation**: 详细架构说明见 `docs/architecture/knowledge_graph.md`

### Data Flow

```
User Request → Gateway (8005) → Intent Recognition
                            ↓
                    Agent Selection (Xiaonuo)
                            ↓
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
    Xiaona (Legal)    Knowledge Base      LLM Inference
    Patent Analysis    Vector Search       Context Generation
        ↓                   ↓                   ↓
    Result Aggregation ← Response Formatting ← Output
```

## Code Conventions

### Python Code Style

- **Line length**: 100 characters (Black config in pyproject.toml)
- **Python version**: 3.11+ (使用现代类型注解: `list[str]`, `dict[str, int]`, `str | None`)
- **Import order**: stdlib → third-party → local
- **Docstrings**: Google style for all public functions
- **Naming**: snake_case for modules/functions, PascalCase for classes

### Go Code Style (Gateway)

- Standard `go fmt` formatting
- Error handling with explicit checks
- Context propagation for async operations

### Configuration

- **Environment**: Use `.env` files (see `.env.template`)
- **Docker**: Multiple compose files for different environments
- **Service Discovery**: JSON-based service registry in `config/service_discovery.json`

## MCP服务器系统 (Model Context Protocol)

The platform includes multiple MCP servers for extended functionality:

### 已集成的MCP服务器
| 服务器名称 | 功能 | 端口 | 状态 |
|---------|---------|---------|---------|
| gaode-mcp-server | 高德地图服务(地理编码, 路径规划) | 8899 | active |
| academic-search | 学术搜索服务(论文检索, Semantic Scholar) | 可配置 | active |
| jina-ai-mcp-server | Jina AI服务(网页抓取, 向量搜索, 重排序) | 可配置 | active |
| memory | 知识图谱内存系统(实体, 关系, 观察) | 可配置 | active |
| local-search-engine | 本地搜索引擎(SearXNG+Firecrawl, 搜索+抓取) | 3003 | active |

### MCP使用示例
```python
# 通过MCP客户端调用服务
# 1. 学术搜索 - 查找论文
papers = mcp_academic_search_search_papers(
    query="machine learning patents",
    limit=10,
    year="2024"
)

# 2. 网页抓取 - 获取内容
content = mcp_jina_ai_read_web(
    url="https://patents.google.com/patent/CN123456"
)

# 3. 向量搜索 - 语义检索
results = mcp_jina_ai_vector_search(
    query="专利侵权判定",
    documents=patent_documents,
    top_k=5
)

# 4. 网络搜索 - 多引擎搜索
search_results = mcp_jina_ai_web_search(
    query="最新专利法修订",
    limit=10
)
```

### 本地搜索引擎 (SearXNG + Firecrawl)

本地搜索引擎提供搜索和网页抓取功能，无需外部API密钥。

| 服务 | 地址 | 说明 |
|------|------|------|
| Gateway REST API | `http://localhost:3003` | 统一入口 |
| Gateway MCP SSE | `http://localhost:3003/sse` | MCP端点 |
| SearXNG | `http://localhost:8080` | 搜索引擎 |
| Firecrawl | `http://localhost:3002` | 页面抓取 |

**MCP工具**:
- `web_search` - 搜索互联网，返回标题+摘要
- `web_scrape` - 抓取网页转为Markdown
- `web_search_and_scrape` - 搜索+抓取全文

**管理命令**:
```bash
# 启动/停止
cd ~/projects/local-search-engine && docker compose up -d
cd ~/projects/local-search-engine && docker compose down

# 查看状态
docker ps --filter "name=lse"

# 查看日志
docker compose -f ~/projects/local-search-engine/docker-compose.yml logs -f gateway
```

### MCP配置文件
MCP服务器配置位于 `mcp-servers/` 目录,每个服务器都有独立的配置和启动脚本。

## Testing Strategy

### Test Types

```bash
# Unit tests (fast, no external dependencies)
pytest tests/ -m unit

# Integration tests (require external services)
pytest tests/ -m integration

# End-to-end tests (complete workflows)
pytest tests/ -m e2e

# Performance tests
pytest tests/ -m performance

# Specific test file
pytest tests/test_specific_module.py -v
```

### Test Coverage

- Target: >70% overall, >80% for core modules
- Use `pytest-cov` for coverage reports
- HTML report: `pytest --cov=core --cov-report=html`

## 监控和性能基准

### 监控系统访问
- **Grafana**: 可视化仪表板 at `http://localhost:3000` (admin/admin123)
- **Prometheus**: 指标收集 at `http://localhost:9090/metrics`
- **Alertmanager**: 告警管理 at `http://localhost:9093`

### 当前性能基准 (2026-03-19)
| 指标 | 目标 | 当前 | 状态 |
|-----|-----|-----|-----|
| API响应时间 | <100ms (P95) | ~150ms | ⚠️ 需优化 |
| 向量检索延迟 | <50ms | ~80ms | ⚠️ 需优化 |
| 缓存命中率 | >90% | ~89.7% | ✅ 接近目标 |
| 查询吞吐量 | >100 QPS | ~85 QPS | ⚠️ 需优化 |
| 错误率 | <0.1% | ~0.15% | ⚠️ 需优化 |

### 监控命令
```bash
# 查看Grafana仪表板
open http://localhost:3000

# 查看Prometheus指标
curl http://localhost:9090/metrics

# 查看Alertmanager告警
open http://localhost:9093
```

## Gateway-Unified System (Go语言网关)

The platform includes a high-performance Go-based gateway system located in `gateway-unified/`:

### 核心特性
- **服务注册与发现**: Automatic service registration and health checking
- **智能路由**: Exact match, wildcard, and path stripping support
- **负载均衡**: Round-robin load balancing
- **优雅关机**: Two-phase graceful shutdown (stop accepting → drain connections)
- **监控集成**: Built-in Prometheus metrics and Grafana dashboards
- **安全特性**: Multi-layer authentication (IP whitelist, API Key, Bearer Token, Basic Auth)
- **日志管理**: Log rotation and compression support

### 关键配置
```yaml
# gateway-unified/config.yaml
server:
  port: 8005
  production: false
  read_timeout: 30
  write_timeout: 30
  idle_timeout: 120

gateway:
  routes:
    - path: /api/legal/*
      strip_path: true
      target_service: "xiaona-legal"
```

### 部署命令
```bash
# macOS部署
sudo bash gateway-unified/quick-deploy-macos.sh

# Linux部署
sudo bash gateway-unified/quick-deploy.sh

# 查看状态
sudo /usr/local/athena-gateway/status.sh

# 查看日志
sudo journalctl -u athena-gateway -f
```

### Language Rules

- **Response language**: Simplified Chinese (简体中文) for all user-facing content
- **Code comments**: Chinese for code explanations
- **Technical terms**: Keep English, provide Chinese explanation

### Security Considerations

- Gateway defaults to localhost binding (127.0.0.1)
- Remote access requires SSH tunnel
- API keys stored encrypted
- SQL injection prevention via parameterized queries
- No sensitive data in logs

### Common Patterns

**Agent Integration**:
```python
from core.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
```

**Gateway Service (Go)**: 服务通过 `config/service_discovery.json` 注册

### Performance Considerations

- Database queries use connection pooling
- Vector searches limited to top-k results
- LLM responses cached when appropriate
- Async operations for I/O-bound tasks

## 工具系统 (Tool System v2.0 - 统一注册表)

Athena平台使用**统一工具注册表** (UnifiedToolRegistry)，整合所有工具管理功能，提供单一、高效、易用的接口。

### 核心特性

- 🏗️ **统一注册表**: 整合4个独立注册表，代码减少42%
- ⚡ **懒加载机制**: 工具按需加载，启动时间降低52%
- 🔍 **自动发现**: 使用@tool装饰器自动注册工具
- 💚 **健康监控**: 自动监控工具健康状态
- 🔒 **线程安全**: RLock保证并发安全
- 📈 **性能提升**: 并发性能提升147%，内存占用降低47%
- 🔄 **向后兼容**: 保留兼容层，平滑迁移

### 快速开始

```python
# 获取统一注册表
from core.tools.unified_registry import get_unified_registry

registry = get_unified_registry()

# 使用@tool装饰器自动注册工具
from core.tools.decorators import tool

@tool(name="patent_search", category="patent")
def search_patents(query: str) -> dict:
    """搜索专利"""
    return {"results": []}

# 获取并调用工具
tool = registry.get("patent_search")
result = tool.function(query="人工智能")
```

### 统一注册表API

**核心方法**:
```python
# 获取工具
tool = registry.get("tool_name")
tool = registry.require("tool_name")  # 不存在时抛出异常

# 查找工具
tools = registry.find(category="patent")
tools = registry.find(name_pattern="*search*")

# 列出所有工具
all_tools = registry.list_tools()

# 健康检查
health = registry.check_health("tool_name")
report = registry.health_check_all()

# 获取统计信息
stats = registry.get_statistics()
```

**懒加载**:
```python
# 注册懒加载工具
registry.register_lazy(
    tool_id="heavy_tool",
    import_path="core.tools.heavy_implementations",
    function_name="heavy_computation"
)

# 工具在第一次使用时才加载
tool = registry.get("heavy_tool")
```

### 文档资源

- 📖 **迁移指南**: `docs/guides/UNIFIED_TOOL_REGISTRY_MIGRATION_GUIDE.md`
- 📚 **API文档**: `docs/api/UNIFIED_TOOL_REGISTRY_API.md`
- 🎓 **培训指南**: `docs/training/TOOL_REGISTRY_TRAINING.md`
- 📊 **实施报告**: `docs/reports/UNIFIED_TOOL_REGISTRY_FINAL_REPORT.md`

### 工具权限系统 (保留)

统一注册表保留了完整的权限控制功能：

**权限模式**：
- `DEFAULT`: 默认模式，未匹配规则时需要用户确认
- `AUTO`: 自动模式，未匹配规则时自动拒绝
- `BYPASS`: 绕过模式，允许所有调用（谨慎使用）

**权限规则**：
- 支持通配符模式匹配（如 `bash:*` 或 `*search`）
- 基于优先级的冲突解决
- 运行时权限检查

**使用示例**：
```python
from core.tools.permissions import (
    ToolPermissionContext,
    PermissionMode,
    PermissionRule
)

# 创建权限上下文
ctx = ToolPermissionContext(mode=PermissionMode.AUTO)

# 添加允许规则
ctx.add_rule("allow", PermissionRule(
    rule_id="safe-read",
    pattern="*:read",
    description="允许所有读操作",
    priority=10
))

# 添加拒绝规则
ctx.add_rule("deny", PermissionRule(
    rule_id="dangerous-rm",
    pattern="bash:*rm*",
    description="拒绝包含rm的bash命令",
    priority=100
))

# 检查权限
decision = ctx.check_permission("file:read", parameters={"path": "/tmp/file.txt"})
print(f"允许: {decision.allowed}, 原因: {decision.reason}")
```

### 工具分组系统 (增强版)

统一注册表保留了完整的工具分组功能：

**工具组类型**：
- `patent`: 专利检索、分析、翻译
- `legal`: 法律分析、案例检索
- `academic`: 学术搜索、论文分析
- `general`: 通用工具（文件操作、网络搜索等）

**使用示例**：
```python
from core.tools.tool_manager import ToolManager

# 获取工具管理器
manager = ToolManager()

# 激活工具组
manager.activate_group("patent")

# 自动选择工具组
await manager.auto_activate_group_for_task(
    task_description="分析专利CN123456789A的创造性",
    task_type="patent_analysis",
    domain="patent"
)

# 获取最佳工具
result = await manager.select_best_tool(
    task_description="检索相关专利",
    task_type="patent_search"
)
```

### 工具调用管理 (增强版)

统一注册表保留了完整的工具调用管理功能：

**核心功能**：
- 统一调用接口
- 调用日志记录
- 错误处理和重试
- 结果验证
- 性能监控

**使用示例**：
```python
from core.tools.tool_call_manager import get_tool_manager, call_tool

# 获取管理器
manager = get_tool_manager()

# 调用工具
result = await call_tool(
    "patent_analyzer",
    parameters={
        "patent_id": "CN123456789A",
        "analysis_type": "creativity"
    }
)

print(f"状态: {result.status.value}")
print(f"结果: {result.result}")
print(f"执行时间: {result.execution_time:.2f}秒")
```

### 附加文档

- **权限系统API**: `docs/api/PERMISSION_SYSTEM_API.md`
- **工具管理API**: `docs/api/TOOL_MANAGER_API.md`
- **使用示例**: `examples/tools/permission_examples.py`
- **开发指南**: `docs/guides/TOOL_SYSTEM_GUIDE.md`

---

## 提示词工程系统 (v4.0)

Athena平台使用**四层提示词架构**，基于Claude Code Playbook设计模式。

### 核心特性

- 🏗️ **四层架构**: L1基础层 + L2数据层 + L3能力层 + L4业务层
- ⚡ **并行工具调用**: Turn-based并行处理，性能提升75%
- 🎯 **whenToUse触发**: 自动识别用户意图，智能加载模块
- 🧠 **Scratchpad推理**: 私下推理机制，仅保留摘要给用户
- 🔒 **约束重复**: 关键规则在开头和结尾重复强调

### 文档位置

- **系统架构**: `prompts/README.md`
- **v4架构设计**: `prompts/README_V4_ARCHITECTURE.md`
- **实施报告**: `docs/reports/PROMPT_ENGINE_V4_IMPLEMENTATION_REPORT_20260419.md`
- **代码质量报告**: `docs/reports/CODE_QUALITY_FIX_COMPLETE_REPORT_20260419.md`
- **质量标准**: `docs/development/CODE_QUALITY_STANDARDS.md`

### 使用Scratchpad代理

```python
from core.agents.xiaona_agent_with_scratchpad import XiaonaAgentWithScratchpad

# 创建带Scratchpad的代理
agent = XiaonaAgentWithScratchpad()

# 处理任务
result_json = agent.process("帮我分析专利CN123456789A的创造性")
result = json.loads(result_json)

# 输出包含：
# - output: 用户看到的内容
# - reasoning_summary: 推理摘要
# - scratchpad_available: 是否可查看完整Scratchpad
```

### 提示词加载

```python
from production.services.unified_prompt_loader_v4 import UnifiedPromptLoaderV4

# 初始化v4加载器
loader = UnifiedPromptLoaderV4()

# 加载提示词（静态/动态分离）
system_prompt = loader.load_system_prompt(
    agent_type="xiaona",
    session_context={
        "session_id": "SESSION_001",
        "cwd": "/Users/xujian/Athena工作平台"
    }
)
```

### 代码质量要求

所有Python代码必须遵循：

1. **类型注解**: 使用`Dict[str, Any]`而非`dict`
2. **异步规范**: 只在真正需要异步I/O时使用`async`
3. **错误处理**: JSON解析必须有try-except
4. **事件循环**: 检测并处理嵌套事件循环
5. **Python版本**: 兼容Python 3.9+

详见: `docs/development/CODE_QUALITY_STANDARDS.md`

---

## Troubleshooting

### Common Issues

**1. Port conflicts (default: 8005)**
- Check: `lsof -i :8005`
- Solution: Change port in configs or stop conflicting service

**2. Database connection errors**
- Verify Docker containers running: `docker-compose ps`
- Check connection string in `.env`
- Ensure PostgreSQL is accepting connections

**3. Import errors**
- Set PYTHONPATH: `export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH`
- Install dependencies: `pip install -r requirements.txt`

**4. Memory system errors**
- Check tier capacity limits (HOT: 100MB, WARM: 500MB, COLD: 10GB)
- Verify Redis connection for WARM tier
- Check SQLite file permissions for COLD tier

**5. Gateway启动失败**
```bash
# 查看服务状态
sudo /usr/local/athena-gateway/status.sh

# 查看日志 (macOS)
tail -50 /usr/local/athena-gateway/logs/gateway-error.log

# 查看日志 (Linux)
sudo journalctl -u athena-gateway -f

# 检查配置文件
cat /usr/local/athena-gateway/config.yaml

# 检查端口占用
lsof -i :8005
```

**6. MCP服务器连接失败**
```bash
# 检查MCP服务器状态
docker-compose ps | grep mcp

# 查看MCP服务器日志
docker-compose logs -f gaode-mcp-server

# 重启MCP服务器
docker-compose restart gaode-mcp-server
```

### Debug Commands

```bash
# Check all services status
python3 scripts/xiaonuo_system_checker.py

# View Gateway logs
docker-compose logs -f gateway

# View specific agent logs
docker-compose logs -f xiaonuo

# Database health check
docker-compose exec postgres pg_isready -U athena

# Redis health check
docker-compose exec redis redis-cli ping
```

## Key Files

### Agent System

| File | Purpose |
|------|---------|
| `core/agents/base_agent.py` | Base agent class |
| `core/agents/xiaona/base_component.py` | 专业代理基类 |
| `core/agents/xiaona/retriever_agent.py` | 检索代理 - 专利检索 |
| `core/agents/xiaona/analyzer_agent.py` | 分析代理 - 专利分析 |
| `core/agents/xiaona/unified_patent_writer.py` | 统一撰写代理 - 完整撰写流程（整合原writer_agent和patent_drafting_proxy） |
| `core/agents/xiaona/novelty_analyzer_proxy.py` | 新颖性分析代理 |
| `core/agents/xiaona/creativity_analyzer_proxy.py` | 创造性分析代理 |
| `core/agents/xiaona/infringement_analyzer_proxy.py` | 侵权分析代理 |
| `core/agents/xiaona/invalidation_analyzer_proxy.py` | 无效分析代理 |
| `core/agents/xiaona/application_reviewer_proxy.py` | 申请审查代理 |
| `core/agents/xiaona/writing_reviewer_proxy.py` | 写作审查代理 |

### Core Systems

| File | Purpose |
|------|---------|
| `scripts/xiaonuo_unified_startup.py` | Main platform startup script |
| `core/llm/unified_llm_manager.py` | LLM orchestration |
| `core/embedding/unified_embedding_service.py` | Embedding service |
| `core/memory/` | Memory system implementation |
| `core/legal_world_model/` | Legal world model for patent analysis |
| `core/knowledge_graph/` | Knowledge graph integration (Neo4j/ArangoDB) |
| `core/knowledge_graph/kg_integration.py` | Knowledge graph API and data models |
| `core/knowledge_graph/neo4j_graph_engine.py` | Neo4j graph engine |
| `core/knowledge_graph/arango_engine.py` | ArangoDB engine |
| `core/knowledge_graph/legal_kg_reasoning_enhancer.py` | Legal knowledge graph reasoning |
| `core/tools/` | Tool system (permissions, manager, registry) |
| `core/tools/permissions.py` | Tool permission system |
| `core/tools/tool_manager.py` | Tool group management |
| `core/tools/tool_call_manager.py` | Tool call orchestration |
| `core/tools/base.py` | Tool definitions and registry |
| `gateway-unified/` | Unified Go gateway system ⭐ |
| `mcp-servers/` | MCP servers (gaode, academic-search, jina-ai, etc.) |
| `config/service_discovery.json` | Service registry |
| `config/agent_registry.json` | Agent registry (9个专业代理配置) |
| `docker-compose.yml` | Main Docker configuration |
| `pyproject.toml` | Python project config |
| `tests/pytest.ini` | Test configuration |

---

## 写作风格指南

当为Athena平台撰写文章、回答或内容时，请遵循以下写作风格：

### 语言风格
- **主要语言**: 简体中文回答，代码使用英文编写并附带中文注释
- **专业性与人文性平衡**: 既有法律工作者的严谨理性，又有文学爱好者的温度情怀
- **真诚坦率**: 不矫揉造作，可以适当展示困惑和思考过程

### 文章类型适配

**个人感悟类文章**：
- 开头：引用名言或生活场景建立共鸣
- 结构：名言/场景引入 → 个人经历 → 价值升华
- 结尾：哲学式总结

**专业分析类文章**：
- 开头：陈述法律条文或理论框架
- 结构：法理引入 → 案件分析 → 程序展开 → 要点总结
- 风格：客观中立，使用"首先、其次、再次"的结构化表达

### 可复用的写作模式

| 模式 | 结构 | 适用场景 |
|-----|------|---------|
| 故事化开场 | 引用名言 → 场景描写 → 提出问题 | 公众号文章、个人分享 |
| 对比式结构 | 普遍认知 → 个人实践 → 反差呈现 | 打破刻板印象 |
| 法理引入式 | 法律条文 → 理论阐述 → 实务问题 | 专业文章、案例分析 |
| 要点式总结 | 首先 → 其次 → 再次 → 结论 | 实务建议、案例分析 |

---

## 技术债务跟踪

### 当前状态 (2026-04-06更新)

**已完成**:
- ✅ 测试基础设施修复 (测试可收集: 0→1459)
- ✅ 语法错误修复 (19处→0)
- ✅ 废弃代码警告处理 (4处已正确标记)
- ✅ Ruff总错误修复 (18,764→968, 降低94.8%)
- ✅ F821 undefined-name全部修复 (2,076→0)
- ✅ E722 bare-except全部修复 (89→0)
- ✅ P1问题修复 (B025/F403/F405/F402/B905共253处→0)
- ✅ UP类型现代化 (6,892→~50)
- ✅ Pre-commit更新为ruff

### 剩余 (P2/P3)

| 问题 | 数量 | 优先级 | 说明 |
|------|------|--------|------|
| F401 unused-import | 439 | P2 | 部分是条件导入 |
| F841 unused-variable | 153 | P2 | 未使用的变量 |
| B007 unused-loop-var | 87 | P3 | 未使用循环变量 |
| 其他 | 289 | P3 | 各类低优先级 |
| TODO清单 | ~191 | P2 | 按模块实现 |
| 依赖版本分散 | 5个requirements.txt | P2 | 统一到poetry |

**详细报告**: `docs/reports/TECHNICAL_DEBT_RESOLUTION_REPORT_20260406.md`

---

## 项目进度

### Gateway架构转型 (90天计划)

- **Phase 0** (Day 1-7): 资产盘点、备份系统、回滚测试 ✅
- **Phase 1** (Day 8-30): Gateway接口设计、WebSocket控制平面 ⏳
- **Phase 2** (Day 31-60): 灰度切流 (10% → 50% → 100%) ⏳
- **Phase 3** (Day 61-90): 稳定运行、旧系统下线 ⏳

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-03
