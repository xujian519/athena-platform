# Gateway Performance Baseline - Istio vs Linkerd

- Objective: Establish baseline latency/throughput for Athena Gateway under Istio and Linkerd in gateway role.
- Test plan: baseline (no mesh), PoC mesh (Istio only), mesh with Linkerd for comparison, production-like routing.
- Metrics: p50/p95/p99 latency, throughput (req/s), error rate, CPU/memory usage, TLS handshake counts.
- Expected outcomes: measurable overhead, but acceptable within service-level objectives; trade-offs explained.
