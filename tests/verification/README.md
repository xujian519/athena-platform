# Athena平台验证测试套件

> **最后更新**: 2026-04-18
> **作者**: 徐健
> **版本**: v1.0

本目录包含Athena平台统一网关架构的完整验证测试套件，覆盖知识库、工具库和网关兼容性的所有关键功能。

---

## 📋 目录

- [测试概述](#测试概述)
- [快速开始](#快速开始)
- [测试模块](#测试模块)
- [详细测试用例](#详细测试用例)
- [性能测试](#性能测试)
- [测试报告](#测试报告)
- [故障排查](#故障排查)

---

## 测试概述

### 测试范围

| 模块 | 测试类别 | 测试数量 | 验证重点 |
|------|---------|---------|---------|
| **知识库** | KB-CONN-01~08 | 8个 | 连通性(后端服务、网关路由) |
| | KB-ACC-01~06 | 6个 | 准确性(检索结果、黄金查询集) |
| | KB-PERF-01~05 | 5个 | 并发性能(QPS、P95延迟) |
| | KB-SYNC-01~04 | 4个 | 数据同步(集合一致性、图谱-向量) |
| **工具库** | TOOL-CONN-01~10 | 10个 | 连通性(MCP服务器、工具注册中心) |
| | TOOL-PARAM-01~06 | 6个 | 参数传递(简单、嵌套、中文编码) |
| | TOOL-ERR-01~06 | 6个 | 容错机制(服务不可用、超时、熔断) |
| | TOOL-PERF-01~06 | 6个 | 响应时间(内置工具、MCP工具) |
| **网关** | GW-ROUTE-01~10 | 10个 | 路由转发(13个旧网关→1个统一网关) |
| | GW-AUTH-01~06 | 6个 | 认证兼容性(IP白名单、API Key、Token) |
| | GW-MW-01~05 | 5个 | 中间件(请求ID、CORS、限流) |
| | GW-PROTO-01~05 | 5个 | 协议兼容性(HTTP/1.1、HTTP/2、WebSocket) |
| **总计** | - | **77个** | 全功能覆盖 |

### 测试架构

```
tests/verification/
├── knowledge_base_verification.py    # 知识库验证 (KB-*)
├── tool_library_verification.py      # 工具库验证 (TOOL-*)
├── gateway_compatibility_verification.py  # 网关兼容性验证 (GW-*)
├── quick_test.sh                     # Bash快速测试脚本
├── locust_kb_performance.py          # 性能测试脚本
├── README.md                         # 本文档
├── test_data/                        # 测试数据
│   └── golden_queries.json           # 黄金查询集
└── reports/                          # 测试报告输出
    ├── kb_verification_*.json
    ├── tool_verification_*.json
    └── gateway_verification_*.json
```

---

## 快速开始

### 1. 环境准备

```bash
# 1. 启动Docker服务
docker-compose up -d

# 2. 等待服务就绪
docker-compose ps

# 3. 安装Python测试依赖
cd /Users/xujian/Athena工作平台
poetry install

# 或使用pip
pip install pytest pytest-asyncio httpx qdrant-client neo4j redis psycopg[pool]
```

### 2. 快速连通性测试 (推荐首次运行)

```bash
# 运行Bash快速测试脚本 (约30秒)
./tests/verification/quick_test.sh
```

**输出示例**:
```
============================================================================
  Athena平台验证测试 - 快速测试
============================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  知识库连通性测试 (KB-CONN-01~08)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KB-CONN-01: 知识图谱服务 ... ✅ PASS [KB-CONN-01] 知识图谱服务 (HTTP 200)
KB-CONN-02: Qdrant向量库 ... ✅ PASS [KB-CONN-02] Qdrant向量库 (7 个集合)
KB-CONN-03: PostgreSQL ... ✅ PASS [KB-CONN-03] PostgreSQL (accepting connections)
...
```

### 3. 完整Python测试套件

```bash
# 运行所有测试
pytest tests/verification/ -v

# 运行单个模块
pytest tests/verification/knowledge_base_verification.py -v
pytest tests/verification/tool_library_verification.py -v
pytest tests/verification/gateway_compatibility_verification.py -v

# 运行特定测试类
pytest tests/verification/knowledge_base_verification.py::TestKnowledgeBaseConnectivity -v

# 运行特定测试用例
pytest tests/verification/knowledge_base_verification.py::TestKnowledgeBaseConnectivity::test_kb_conn_01_knowledge_graph -v

# 生成HTML覆盖率报告
pytest tests/verification/ --cov=core --cov-report=html
```

### 4. 性能测试

```bash
# 使用Locust进行并发性能测试
cd tests/verification
locust -f locust_kb_performance.py --host=http://localhost:8005

# 或使用headless模式
locust -f locust_kb_performance.py --headless --users=100 --spawn-rate=10 --run-time=60s
```

---

## 测试模块

### 1. 知识库验证 (`knowledge_base_verification.py`)

**功能**: 验证知识库后端服务的连通性、检索准确性和并发性能

**测试类**:
- `TestKnowledgeBaseConnectivity`: 连通性测试 (KB-CONN-01~08)
- `TestKnowledgeBaseAccuracy`: 准确性验证 (KB-ACC-01~06)

**运行示例**:
```bash
pytest tests/verification/knowledge_base_verification.py -v -s
```

### 2. 工具库验证 (`tool_library_verification.py`)

**功能**: 验证工具注册中心、MCP服务器、参数传递和容错机制

**测试类**:
- `TestToolConnectivity`: 连通性测试 (TOOL-CONN-01~10)
- `TestToolParameterPassing`: 参数传递测试 (TOOL-PARAM-01~06)
- `TestToolErrorHandling`: 容错机制测试 (TOOL-ERR-01~06)

**运行示例**:
```bash
pytest tests/verification/tool_library_verification.py -v -s
```

### 3. 网关兼容性验证 (`gateway_compatibility_verification.py`)

**功能**: 验证统一网关的路由转发、认证和中间件

**测试类**:
- `TestGatewayRouting`: 路由转发测试 (GW-ROUTE-01~10)
- `TestGatewayAuthentication`: 认证兼容性测试 (GW-AUTH-01~06)
- `TestGatewayMiddleware`: 中间件测试 (GW-MW-01~05)
- `TestGatewayProtocol`: 协议兼容性测试 (GW-PROTO-01~05)

**运行示例**:
```bash
pytest tests/verification/gateway_compatibility_verification.py -v -s
```

---

## 详细测试用例

### 知识库测试用例

#### KB-CONN-01~08: 连通性测试

| 编号 | 测试项 | 验证方法 | 预期结果 | 优先级 |
|------|--------|---------|---------|--------|
| KB-CONN-01 | 知识图谱HTTP连通性 | `curl http://localhost:8100/health` | 返回200, status=healthy | P0 |
| KB-CONN-02 | Qdrant向量库连通性 | `curl http://localhost:6333/collections` | 返回200, 含7个集合 | P0 |
| KB-CONN-03 | PostgreSQL连通性 | `docker-compose exec postgres pg_isready` | accepting connections | P0 |
| KB-CONN-04 | Redis连通性 | `docker-compose exec redis redis-cli ping` | PONG | P0 |
| KB-CONN-05 | BGE-M3嵌入服务 | `UnifiedEmbeddingService.encode("测试")` | 返回768维向量 | P0 |
| KB-CONN-06 | 网关→知识图谱路由 | `POST /api/v1/kg/query` | 正确转发至8100端口 | P0 |
| KB-CONN-07 | 网关→向量搜索路由 | `POST /api/v1/vector/search` | 正确转发至Qdrant | P0 |
| KB-CONN-08 | 网关→法律搜索路由 | `POST /api/v1/legal/search` | 正确转发至法律向量API | P1 |

#### KB-ACC-01~06: 准确性验证

| 编号 | 测试项 | 验收标准 | 优先级 |
|------|--------|---------|--------|
| KB-ACC-01 | 专利语义搜索 | 与合并前结果一致率 > 95% | P0 |
| KB-ACC-02 | 法律条文检索 | 准确返回目标条文，排名Top-3 | P0 |
| KB-ACC-03 | 知识图谱路径查询 | 返回正确的关系链 | P0 |
| KB-ACC-04 | 混合检索（向量+图谱） | 向量结果与图谱结果正确融合 | P1 |
| KB-ACC-05 | RAG多策略检索 | 每种策略返回合理结果 | P1 |
| KB-ACC-06 | 跨集合检索 | 结果覆盖相关集合 | P1 |

#### KB-PERF-01~05: 并发性能测试

| 编号 | 并发数 | 持续时间 | 验收标准 | 优先级 |
|------|--------|---------|---------|--------|
| KB-PERF-01 | 10 | 60s | QPS > 50, P95 < 200ms | P0 |
| KB-PERF-02 | 50 | 60s | QPS > 80, P95 < 500ms | P0 |
| KB-PERF-03 | 100 | 120s | QPS > 100, P95 < 1s, 错误率 < 1% | P1 |
| KB-PERF-04 | 200 | 30s | 系统不崩溃，限流生效 | P1 |
| KB-PERF-05 | 80读+20写 | 120s | 读写均正常，无死锁 | P1 |

### 工具库测试用例

#### TOOL-CONN-01~10: 连通性测试

| 编号 | 测试项 | 验证方法 | 预期结果 | 优先级 |
|------|--------|---------|---------|--------|
| TOOL-CONN-01 | 工具注册中心可用性 | `tool_registry.list_tools()` | 返回所有已注册工具列表 | P0 |
| TOOL-CONN-02 | MCP管理器连通性 | `mcp_manager.list_servers()` | 返回5个MCP服务器 | P0 |
| TOOL-CONN-03 | 高德地图MCP | 调用 `geocode` 工具 | 返回地理编码结果 | P1 |
| TOOL-CONN-04 | 专利下载MCP | 调用 `get_patent_info` 工具 | 返回专利信息 | P1 |
| TOOL-CONN-05 | Jina AI MCP | 调用 `read_web` 工具 | 返回网页内容 | P1 |
| TOOL-CONN-06 | 学术搜索MCP | 调用 `search_papers` 工具 | 返回论文列表 | P1 |
| TOOL-CONN-08 | 本地搜索引擎 | `curl http://localhost:3003/health` | 返回200 | P0 |
| TOOL-CONN-09 | 网关→工具API路由 | `curl http://localhost:8005/api/v1/tools` | 返回工具列表 | P0 |
| TOOL-CONN-10 | 网关→工具执行路由 | `POST /api/v1/tools/{id}/execute` | 正确执行并返回结果 | P0 |

#### TOOL-PARAM-01~06: 参数传递测试

| 编号 | 测试项 | 验收标准 | 优先级 |
|------|--------|---------|--------|
| TOOL-PARAM-01 | 简单参数传递 | 参数值无丢失、无编码错误 | P0 |
| TOOL-PARAM-02 | 复杂嵌套参数 | 嵌套结构完整保留 | P0 |
| TOOL-PARAM-03 | 中文参数编码 | 中文正确编码/解码 | P0 |
| TOOL-PARAM-04 | 特殊字符处理 | 特殊字符正确转义 | P1 |
| TOOL-PARAM-05 | 大参数体 | 网关不截断，正确转发 (>1MB) | P1 |
| TOOL-PARAM-06 | 数组参数 | 数组顺序和内容不变 | P1 |

### 网关测试用例

#### GW-ROUTE-01~10: 路由转发测试

| 编号 | 原13网关路由 | 统一网关路由 | 目标服务 | 优先级 |
|------|-------------|-------------|---------|--------|
| GW-ROUTE-01 | `/api/legal/*` | `/api/legal/*` | 小娜法律分析 | P0 |
| GW-ROUTE-02 | `/api/search` | `/api/search` | 统一搜索服务 | P0 |
| GW-ROUTE-03 | `/api/v1/kg/*` | `/api/v1/kg/*` | 知识图谱服务 | P0 |
| GW-ROUTE-04 | `/api/v1/vector/*` | `/api/v1/vector/*` | 向量搜索服务 | P0 |
| GW-ROUTE-05 | `/api/v1/legal/*` | `/api/v1/legal/*` | 法律向量API | P0 |
| GW-ROUTE-06 | `/api/v1/tools/*` | `/api/v1/tools/*` | 工具服务 | P0 |
| GW-ROUTE-07 | `/api/v1/services/*` | `/api/v1/services/*` | 服务管理 | P1 |
| GW-ROUTE-10 | `/api/v1/auth/*` | `/api/v1/auth/*` | 认证服务 | P0 |

#### GW-AUTH-01~06: 认证兼容性测试

| 编号 | 测试项 | 验证方法 | 预期结果 | 优先级 |
|------|--------|---------|---------|--------|
| GW-AUTH-01 | IP白名单 | 从白名单IP请求 | 请求通过 | P0 |
| GW-AUTH-02 | API Key认证 | 携带有效API Key请求 | 请求通过 | P0 |
| GW-AUTH-03 | Bearer Token认证 | 携带有效Token请求 | 请求通过 | P0 |
| GW-AUTH-04 | Basic Auth认证 | 携带有效凭据请求 | 请求通过 | P0 |
| GW-AUTH-05 | 无认证请求 | 不携带任何凭据请求公开路由 | 公开路由通过，保护路由拒绝 | P0 |
| GW-AUTH-06 | 无效Token | 携带过期/无效Token | 返回401 | P0 |

---

## 性能测试

### Locust性能测试脚本

```python
# tests/verification/locust_kb_performance.py

from locust import HttpUser, task, between

class KnowledgeBaseUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8005"

    @task(3)
    def vector_search(self):
        """向量搜索 (高频)"""
        self.client.post("/api/v1/vector/search", json={
            "collection_name": "patent_rules_1024",
            "query_text": "发明专利创造性",
            "limit": 10
        })

    @task(2)
    def knowledge_graph_query(self):
        """知识图谱查询 (中频)"""
        self.client.post("/api/v1/kg/query", json={
            "cypher": "MATCH (n:Concept) RETURN n LIMIT 10"
        })

    @task(1)
    def legal_search(self):
        """法律搜索 (低频)"""
        self.client.post("/api/v1/legal/search", json={
            "query": "专利法第22条",
            "limit": 10
        })
```

**运行方式**:

```bash
# Web UI模式
locust -f tests/verification/locust_kb_performance.py

# Headless模式 (100用户, 持续60秒)
locust -f tests/verification/locust_kb_performance.py \
  --headless \
  --users=100 \
  --spawn-rate=10 \
  --run-time=60s \
  --host=http://localhost:8005
```

**性能基准**:

| 并发数 | 目标QPS | 目标P95延迟 | 目标错误率 |
|--------|---------|------------|----------|
| 10 | >50 | <200ms | <0.1% |
| 50 | >80 | <500ms | <0.1% |
| 100 | >100 | <1s | <1% |

---

## 测试报告

### 报告格式

所有测试报告以JSON格式保存在 `tests/verification/reports/` 目录:

```bash
reports/
├── kb_verification_20260418_143025.json
├── tool_verification_20260418_143155.json
└── gateway_verification_20260418_143342.json
```

### 报告结构

```json
{
  "timestamp": "2026-04-18T14:30:25.123456",
  "summary": {
    "total": 77,
    "passed": 72,
    "failed": 3,
    "warned": 2,
    "pass_rate": "93.5%"
  },
  "results": [
    {
      "test_id": "KB-CONN-01",
      "test_name": "知识图谱HTTP连通性",
      "status": "PASS",
      "duration_ms": 45.2,
      "details": {
        "status": "healthy"
      },
      "timestamp": "2026-04-18T14:30:25.123456"
    }
  ]
}
```

### 查看测试报告

```bash
# 查看最新报告
cat tests/verification/reports/kb_verification_*.json | jq '.summary'

# 对比前后两次测试的差异
diff <(cat reports/before.json | jq '.summary') \
     <(cat reports/after.json | jq '.summary')
```

---

## 故障排查

### 常见问题

#### 1. 知识图谱连接失败

**错误信息**:
```
FAILED: KB-CONN-01: 知识图谱HTTP连通性 - Connection refused
```

**解决方案**:
```bash
# 检查知识图谱服务状态
docker-compose ps knowledge-graph

# 查看知识图谱日志
docker-compose logs knowledge-graph

# 重启知识图谱服务
docker-compose restart knowledge-graph
```

#### 2. Qdrant集合数量不足

**错误信息**:
```
WARN: KB-CONN-02: Qdrant向量库 - 仅找到3个集合 (预期≥7)
```

**解决方案**:
```bash
# 检查Qdrant集合
curl http://localhost:6333/collections | jq '.result.collections[] | .name'

# 重新初始化Qdrant集合
python3 scripts/init_qdrant_collections.py
```

#### 3. PostgreSQL连接超时

**错误信息**:
```
FAILED: KB-CONN-03: PostgreSQL - Connection timeout
```

**解决方案**:
```bash
# 检查PostgreSQL状态
docker-compose ps postgres

# 测试连接
docker-compose exec postgres psql -U athena -d athena -c "SELECT 1"

# 重启PostgreSQL
docker-compose restart postgres
```

#### 4. 网关路由404

**错误信息**:
```
FAILED: GW-ROUTE-03: 知识图谱路由 - HTTP 404
```

**解决方案**:
```bash
# 检查网关配置
cat gateway-unified/config.yaml | grep -A5 "/api/v1/kg"

# 检查网关日志
tail -f /usr/local/athena-gateway/logs/gateway.log

# 重启网关
sudo systemctl restart athena-gateway
```

#### 5. MCP服务器不可达

**错误信息**:
```
FAILED: TOOL-CONN-03: 高德地图MCP - Service unavailable
```

**解决方案**:
```bash
# 检查MCP服务器状态
docker-compose ps | grep mcp

# 查看MCP服务器日志
docker-compose logs gaode-mcp-server

# 重启MCP服务器
docker-compose restart gaode-mcp-server
```

### 调试模式

```bash
# 启用详细日志
pytest tests/verification/ -v -s --log-cli-level=DEBUG

# 只运行失败的测试
pytest tests/verification/ --lf

# 遇到第一个失败时停止
pytest tests/verification/ -x

# 显示本地变量
pytest tests/verification/ -l
```

---

## 最佳实践

### 1. 测试执行顺序

```bash
# 第1步: 快速连通性测试 (约30秒)
./tests/verification/quick_test.sh

# 第2步: 如果快速测试通过, 运行完整测试套件
pytest tests/verification/ -v

# 第3步: 如果所有测试通过, 运行性能测试
locust -f tests/verification/locust_kb_performance.py --headless --users=100 --run-time=60s
```

### 2. 持续集成 (CI)

```yaml
# .github/workflows/verification.yml
name: Athena Verification Tests

on: [push, pull_request]

jobs:
  verification:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Run quick test
        run: ./tests/verification/quick_test.sh
      - name: Run full test suite
        run: pytest tests/verification/ -v --junitxml=reports.xml
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: tests/verification/reports/
```

### 3. 测试数据管理

```bash
# 准备测试数据
cp test_data/golden_queries.json.example test_data/golden_queries.json

# 更新黄金查询集
vim test_data/golden_queries.json

# 验证测试数据格式
cat test_data/golden_queries.json | jq '.'
```

---

## 附录

### A. 测试编号对照表

| 前缀 | 模块 | 测试数量 |
|------|------|---------|
| KB-CONN-* | 知识库连通性 | 8 |
| KB-ACC-* | 知识库准确性 | 6 |
| KB-PERF-* | 知识库性能 | 5 |
| KB-SYNC-* | 知识库同步 | 4 |
| TOOL-CONN-* | 工具库连通性 | 10 |
| TOOL-PARAM-* | 工具库参数 | 6 |
| TOOL-ERR-* | 工具库容错 | 6 |
| TOOL-PERF-* | 工具库性能 | 6 |
| GW-ROUTE-* | 网关路由 | 10 |
| GW-AUTH-* | 网关认证 | 6 |
| GW-MW-* | 网关中间件 | 5 |
| GW-PROTO-* | 网关协议 | 5 |

### B. 依赖项

```bash
# Python依赖 (pyproject.toml)
[tool.poetry.dev-dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
pytest-cov = "^4.1"
httpx = "^0.24"
qdrant-client = "^1.7"
neo4j = "^5.14"
redis = {extras = ["hiredis"], version = "^5.0"}
psycopg = {extras = ["pool"], version = "^3.1"}
websockets = "^12.0"

# 性能测试依赖
locust = "^2.17"
```

### C. 相关文档

- [统一网关验证与优化方案](../../docs/reports/UNIFIED_GATEWAY_VERIFICATION_AND_OPTIMIZATION_PLAN.md)
- [Athena平台技术文档](../../docs/)
- [Gateway架构文档](../../gateway-unified/README.md)

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-18
