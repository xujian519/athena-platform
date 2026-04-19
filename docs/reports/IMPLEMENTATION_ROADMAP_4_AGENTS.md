# Athena平台 - 4智能体验证与优化实施路线图

> **版本**: v1.0 | **日期**: 2026-04-18 | **编制**: 徐健
> **执行模式**: 串行+并行混合 | **预计周期**: 3周

---

## 一、智能体编排架构

```
                    ┌─────────────────────────────┐
                    │     主控调度 (Main Agent)     │
                    │   任务分配 / 结果收集 / 验收   │
                    └──────────┬──────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
  Phase 1: 并行验证 (Week 1, Day 1-4)
        │                      │                      │
   ┌────┴────┐          ┌─────┴─────┐         ┌──────┴──────┐
   │ Agent A │          │ Agent B   │         │  Agent C    │
   │知识库验证│          │工具库验证  │         │网关兼容性验证│
   │         │          │           │         │             │
   │ KB-CONN │          │ TOOL-CONN │         │ GW-ROUTE    │
   │ KB-ACC  │          │ TOOL-PARAM│         │ GW-AUTH     │
   │ KB-PERF │          │ TOOL-ERR  │         │ GW-MW       │
   │ KB-SYNC │          │ TOOL-PERF │         │ GW-PROTO    │
   └────┬────┘          └─────┬─────┘         └──────┬──────┘
        │                     │                      │
        └──────────┬──────────┘──────────────────────┘
                   │
              结果汇总 + 问题清单
                   │
  Phase 2: 串行优化 (Week 2, Day 5-10)
                   │
            ┌──────┴──────┐
            │  Agent D    │
            │ 优化实施工程师│
            │             │
            │ OPT-POOL    │
            │ OPT-MON     │
            │ OPT-LOG     │
            │ OPT-RL      │
            │ OPT-CACHE   │
            │ OPT-TRACE   │
            │ OPT-DEG     │
            └──────┬──────┘
                   │
  Phase 3: 回归验收 (Week 3, Day 11-15)
                   │
            ┌──────┴──────┐
            │ Agent A+B+C │ (复用验证脚本)
            │ 全量回归测试  │
            └─────────────┘
```

---

## 二、智能体职责与任务清单

### Agent A - 知识库验证工程师

**职责**: 验证知识库全链路功能，输出测试脚本和验证报告

**输出文件**:
- `tests/verification/test_knowledge_base_connectivity.py` — 连接性测试
- `tests/verification/test_knowledge_base_accuracy.py` — 检索准确性测试
- `tests/verification/test_knowledge_base_performance.py` — 性能基准测试
- `tests/verification/test_knowledge_base_sync.py` — 数据同步测试
- `tests/verification/conftest.py` — 共享 fixture

**任务清单**:

| 序号 | 任务 | 依赖 | 预计耗时 | 检查项 |
|------|------|------|---------|--------|
| A-01 | 创建 `tests/verification/` 目录和 conftest.py | 无 | 15min | 目录存在，fixture可导入 |
| A-02 | 编写连接性测试 (KB-CONN 01~08) | A-01 | 30min | 8项测试可执行 |
| A-03 | 设计 Golden Set 基准数据 | A-01 | 20min | 3+标准查询用例 |
| A-04 | 编写检索准确性测试 (KB-ACC 01~06) | A-03 | 40min | 6项测试可执行 |
| A-05 | 编写并发性能测试 (KB-PERF 01~05) | A-01 | 40min | 5级梯度压测可执行 |
| A-06 | 编写数据同步测试 (KB-SYNC 01~04) | A-01 | 30min | 4项测试可执行 |
| A-07 | 执行全部测试并生成报告 | A-02~06 | 20min | 报告含 PASS/FAIL 汇总 |

**检查清单 (Agent A 验收标准)**:
- [ ] `tests/verification/` 目录及所有文件存在
- [ ] `pytest tests/verification/test_knowledge_base_connectivity.py -v` 可运行
- [ ] 所有测试用例有明确的 PASS/FAIL 断言
- [ ] 性能测试有阈值断言（如 `assert p95 < 1000`）
- [ ] Golden Set 包含至少3个标准查询用例
- [ ] 生成 `reports/verification_kb_report.md` 报告

---

### Agent B - 工具库验证工程师

**职责**: 验证工具库全链路功能，输出测试脚本和验证报告

**输出文件**:
- `tests/verification/test_tool_connectivity.py` — 连通性测试
- `tests/verification/test_tool_parameters.py` — 参数传递测试
- `tests/verification/test_tool_error_handling.py` — 异常容错测试
- `tests/verification/test_tool_performance.py` — 响应时间测试

**任务清单**:

| 序号 | 任务 | 依赖 | 预计耗时 | 检查项 |
|------|------|------|---------|--------|
| B-01 | 编写工具注册中心测试 (TOOL-CONN 01~02) | 无 | 15min | 注册中心可发现所有工具 |
| B-02 | 编写MCP连通性测试 (TOOL-CONN 03~07) | B-01 | 25min | 5个MCP服务器状态检查 |
| B-03 | 编写网关工具路由测试 (TOOL-CONN 08~10) | B-01 | 15min | 网关路由转发正确 |
| B-04 | 编写参数传递测试 (TOOL-PARAM 01~06) | B-01 | 30min | 6种参数类型全部正确传递 |
| B-05 | 编写异常处理测试 (TOOL-ERR 01~06) | B-01 | 35min | 6种异常场景均有兜底 |
| B-06 | 编写响应时间测试 (TOOL-PERF 01~06) | B-01 | 25min | 6类工具有延迟基准 |
| B-07 | 执行全部测试并生成报告 | B-02~06 | 20min | 报告含 PASS/FAIL 汇总 |

**检查清单 (Agent B 验收标准)**:
- [ ] 统一工具注册中心 (`unified_tool_registry.py`) 可正常发现工具
- [ ] MCP管理器可列出所有5个服务器
- [ ] 中文参数传递无编码问题
- [ ] 工具超时后返回504而非崩溃
- [ ] 熔断器在连续失败后正确打开
- [ ] 生成 `reports/verification_tool_report.md` 报告

---

### Agent C - 网关兼容性验证工程师

**职责**: 验证统一网关路由、认证、中间件的完整性和正确性

**输出文件**:
- `tests/verification/test_gateway_routes.py` — 路由转发测试
- `tests/verification/test_gateway_auth.py` — 认证授权测试
- `tests/verification/test_gateway_middleware.py` — 中间件链测试
- `tests/verification/test_gateway_protocol.py` — 协议兼容性测试

**任务清单**:

| 序号 | 任务 | 依赖 | 预计耗时 | 检查项 |
|------|------|------|---------|--------|
| C-01 | 编写路由转发测试 (GW-ROUTE 01~10) | 无 | 40min | 10条核心路由全部验证 |
| C-02 | 编写认证测试 (GW-AUTH 01~06) | C-01 | 30min | 4层认证体系全部工作 |
| C-03 | 编写中间件链测试 (GW-MW 01~05) | C-01 | 25min | 请求ID/CORS/限流/超时/恢复 |
| C-04 | 编写协议测试 (GW-PROTO 01~05) | C-01 | 20min | HTTP/1.1/H2/WS/大请求体 |
| C-05 | 利用已有 `gateway-unified/scripts/health-check.sh` 做基础验证 | 无 | 10min | 健康检查端点全部可达 |
| C-06 | 利用已有 `scripts/health_check.py` 做服务状态快照 | 无 | 10min | 6项服务状态报告 |
| C-07 | 执行全部测试并生成报告 | C-01~06 | 20min | 路由+认证+中间件全通过 |

**检查清单 (Agent C 验收标准)**:
- [ ] 10条核心路由全部正确转发
- [ ] 无认证请求访问保护路由返回401
- [ ] 有效Token请求通过认证
- [ ] 限流触发后返回429
- [ ] 请求头含 X-Request-ID
- [ ] OPTIONS请求含正确CORS头
- [ ] 利用已有 `health-check.sh` 验证通过
- [ ] 生成 `reports/verification_gateway_report.md` 报告

---

### Agent D - 优化实施工程师

**职责**: 基于验证结果实施P0/P1级优化

**触发条件**: Agent A/B/C 验证完成后串行启动

**输出文件**:
- `gateway-unified/internal/pool/integration.go` — 连接池集成
- `gateway-unified/internal/monitoring/server.go` — 监控服务器修复
- `gateway-unified/internal/gateway/rate_limiter.go` — 滑动窗口限流
- `gateway-unified/configs/optimized_config.yaml` — 优化配置
- `docs/reports/optimization_implementation_report.md` — 实施报告

**任务清单**:

| 序号 | 任务 | 依赖 | 优先级 | 预计耗时 |
|------|------|------|--------|---------|
| D-01 | 集成连接池到请求链路 (OPT-POOL-01) | Phase 1 结果 | P0 | 1h |
| D-02 | 修复监控服务器空实现 (OPT-MON-01) | 无 | P0 | 30min |
| D-03 | 实现滑动窗口限流 (OPT-RL-01) | 无 | P0 | 1h |
| D-04 | 统一JSON日志格式 (OPT-LOG-01) | 无 | P0 | 30min |
| D-05 | 按服务定制熔断器参数 | 无 | P0 | 30min |
| D-06 | 配置Prometheus告警规则 | D-02 | P1 | 30min |
| D-07 | 实现分级TTL缓存策略 (OPT-CACHE-01) | 无 | P1 | 1h |
| D-08 | 完善OpenTelemetry配置 (OPT-TRACE-01) | D-02 | P1 | 1h |
| D-09 | 生成优化实施报告 | D-01~08 | — | 20min |

**检查清单 (Agent D 验收标准)**:
- [ ] `ExtendedGateway.sendRequest()` 使用 `ConnectionPool` 而非 `http.Client{}`
- [ ] `monitoring/server.go` 的 `Start()` 方法实际暴露 `/metrics`
- [ ] 限流器使用滑动窗口算法
- [ ] 日志格式统一为JSON，含 `request_id` 字段
- [ ] 熔断器按服务类型有不同的阈值配置
- [ ] Prometheus可采集到 `athena_gateway_*` 指标
- [ ] 缓存TTL按数据类型分级（静态24h/半静态1h/动态5min）
- [ ] Go测试通过: `cd gateway-unified && go test ./...`

---

## 三、串并行执行时序图

```
时间轴 ──────────────────────────────────────────────────────────►

Week 1: 并行验证
Day 1 ─┬─ Agent A: A-01 创建目录/fixture ─┐
       ├─ Agent B: B-01 注册中心测试     ─┤
       └─ Agent C: C-05/06 利用已有脚本  ─┤
                                           │
Day 2 ─┬─ Agent A: A-02 连接性 + A-03 Golden Set
       ├─ Agent B: B-02 MCP连通 + B-03 路由
       └─ Agent C: C-01 路由转发测试
                                           │
Day 3 ─┬─ Agent A: A-04 准确性 + A-05 性能
       ├─ Agent B: B-04 参数 + B-05 异常
       └─ Agent C: C-02 认证 + C-03 中间件
                                           │
Day 4 ─┬─ Agent A: A-06 同步 + A-07 报告 ─┐
       ├─ Agent B: B-06 性能 + B-07 报告 ─┤ ← Phase 1 汇总
       └─ Agent C: C-04 协议 + C-07 报告 ─┘
                                           │
Week 2: 串行优化                           │
Day 5 ──── 汇总Phase 1问题清单 ────────────┘
                                           │
Day 6 ──── Agent D: D-01 连接池 + D-02 监控
Day 7 ──── Agent D: D-03 限流 + D-04 日志
Day 8 ──── Agent D: D-05 熔断 + D-06 告警
Day 9 ──── Agent D: D-07 缓存 + D-08 追踪
Day 10 ─── Agent D: D-09 优化报告
                                           │
Week 3: 回归验收
Day 11 ─── 执行全量回归 (复用A/B/C测试脚本)
Day 12 ─── 性能基准对比 (优化前 vs 优化后)
Day 13 ─── 编写验收报告 + 检查清单签收
```

---

## 四、依赖关系矩阵

### 可并行的任务 (Phase 1)

```
Agent A 任务流:     A-01 → A-02 ─┐
                              A-03 → A-04 ─┤→ A-07
                              A-05 ────────┤
                              A-06 ────────┘

Agent B 任务流:     B-01 → B-02 ─┐
                          B-03 ──┤→ B-07
                          B-04 ──┤
                          B-05 ──┤
                          B-06 ──┘

Agent C 任务流:     C-05/06 (独立) ─────┐
                    C-01 → C-02 ────────┤→ C-07
                    C-01 → C-03 ────────┤
                    C-01 → C-04 ────────┘
```

### 串行依赖 (Phase 1 → Phase 2)

```
Agent A 报告 ─┐
Agent B 报告 ─┼→ 问题清单 → Agent D-01~08 → 优化报告 → 回归测试
Agent C 报告 ─┘
```

---

## 五、现有基础设施复用

| 资源 | 路径 | 复用方式 |
|------|------|---------|
| HealthChecker | `scripts/health_check.py` | Agent A/C 直接调用 |
| Gateway健康检查 | `gateway-unified/scripts/health-check.sh` | Agent C 直接调用 |
| pytest conftest | `tests/conftest.py` | Agent A/B/C 共享 fixture |
| pytest markers | `pyproject.toml` | 使用 `@pytest.mark.integration` 等 |
| Go测试框架 | `gateway-unified/internal/*/` | Agent D 编写Go测试 |
| Docker Compose | `docker-compose.yml` | Agent A/B/C 启动依赖服务 |
| 测试Docker | `tests/integration/docker-compose.test.yml` | 隔离测试环境 |
| Prometheus配置 | `config/prometheus.yml` | Agent D 配置告警规则 |
| Grafana仪表板 | `gateway-unified/grafana-dashboard.json` | Agent D 更新面板 |

---

## 六、质量门禁 (Quality Gates)

### Gate 1: Phase 1 完成标准
- Agent A: 知识库测试 ≥ 20项，PASS率 ≥ 80%
- Agent B: 工具库测试 ≥ 20项，PASS率 ≥ 80%
- Agent C: 网关测试 ≥ 16项，PASS率 ≥ 90%
- 三份验证报告均已生成

### Gate 2: Phase 2 完成标准
- D-01~05 P0优化全部实施并验证
- D-06~08 P1优化 ≥ 50%实施
- Go测试全部通过
- 优化实施报告已生成

### Gate 3: Phase 3 完成标准 (最终验收)
- 全量回归测试 PASS率 ≥ 95%
- 性能基准对比: P95延迟改善 ≥ 20%
- 无P0级别遗留问题
- 最终验收报告签收

---

## 七、风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Docker服务未启动 | 高 | 阻塞验证 | 优先运行 `scripts/health_check.py` 确认环境 |
| BGE-M3模型未加载 | 中 | 嵌入测试失败 | 使用Mock嵌入服务兜底 |
| 端口冲突 | 中 | 部分测试失败 | 使用测试Docker Compose (独立端口) |
| 网关未编译 | 中 | Go测试失败 | 预先 `cd gateway-unified && make build` |
| MCP服务器离线 | 高 | 工具测试部分跳过 | 标记为 `@pytest.mark.skip(reason="MCP offline")` |

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-18
