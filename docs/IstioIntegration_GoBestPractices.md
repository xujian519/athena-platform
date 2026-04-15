Istio Integration - Go Best Practices

目标
- 给出 Go 应用在 Istio 集成中的最佳实践清单，覆盖部署、路由、观测、性能与安全性等方面。

建议要点
- 部署与路由
  - 使用命名空间级自动注入（Istio 自动注入）以确保一致性，必要时对特定服务使用手动注入以实现细粒度控制。
  - 在网关/入口处定义 Gateway 与 VirtualService，以实现对 Athena Gateway 的清晰路由语义。
- 观测与追踪
  - 集成 Prometheus/Grafana、Jaeger/Zipkin，确保端到端的调用链可观测。
  - 启用 Istio 的 Mixer/Telemetry 的观测点，确保性能指标可追踪。
- 安全性
  - 强制 mTLS、使用 SPIFFE 身份、并实施 API 级别的访问策略。
- 性能与资源
  - 注意 Sidecar 的资源分配，合理配置 CPU/内存配额以避免资源竞争。
-  CI/CD 与测试
  - 将网格相关的配置纳入版本控制，使用基线测试和回滚策略。

示例片段
- Istio Gateway、VirtualService 的最小化路由定义。
- 资源配额和安全策略的模板。
