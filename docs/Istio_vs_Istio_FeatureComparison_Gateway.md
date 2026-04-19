Note: Please see Linkerd vs Istio Roadmap for gateway comparison. This document provides a focused feature comparison between Istio and Linkerd in gateway scenarios.

- mTLS: Istio supports mTLS across the mesh by default; Linkerd provides mTLS with lightweight footprint.
- Traffic Shaping: Istio offers rich traffic splitting, fault injection, and complex routing; Linkerd provides simpler traffic splitting options.
- Observability: Istio has strong telemetry and dashboards; Linkerd has lightweight observability with good defaults.
- Policy & Authorization: Istio provides fine-grained AuthorizationPolicy; Linkerd has simpler policy controls.
- Operations: Istio has richer control plane but higher learning curve; Linkerd is simpler and easier to operate.
- Performance: Linkerd typically incurs lower latency overhead; Istio can incur more due to richer features.
