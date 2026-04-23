Benchmark Plan for Athena Gateway Mesh PoC

- Goals: quantify latency, throughput, and overhead of mesh integration.
- Scenarios: baseline (no mesh), PoC (mesh with minimal routing), full mesh (production-like routing).
- Tools: wrk/stress-ng, hey, k6; tracing with Jaeger/Zipkin; Prometheus for metrics.
- Success criteria: SLA adherence, latency delta within acceptable range, no regression in error rate.
