Istio TLS Configuration Best Practices for Go Services

目标
- 提供在 Athena Gateway 场景下 Istio 的 TLS/mTLS 配置最佳实践，包括入口 TLS、网格内 mTLS、超时/重试、以及证书管理。

核心要点
- 授权与身份：在命名空间级别启用 PeerAuthentication STRICT 模式，默认强制 mTLS。
- 入口 TLS：Gateway 的 TLS 使用 SIMPLE 模式，并结合证书管理（如 cert-manager）实现证书轮换。
- 路由和超时：VirtualService 级别设定超时、重试策略，避免单点超时拖垮请求。
- 证书与密钥：推荐使用 SDS（Secret Discovery Service）及自动轮换，减少人工干预。
- 兼容性：Go 服务不应依赖仅存在于特定协议栈中的自定义 TLS 行为，保持与 Envoy 侧车的 TLS 兼容。

示例配置要点
- PeerAuthentication:
  mtls: STRICT
- DestinationRule:
  trafficPolicy:
    connectionPool:
      http:
        http1MaxPendingRequests: 100
- Gateway TLS: 使用 k8s secret 作为证书来源，确保证书轮换可自动化。
- VirtualService：设置超时、重试、以及可能的断路策略。

落地建议
- 在 PoC 阶段使用最小集的 TLS 配置，逐步扩展覆盖更多入口与路径。
- 与证书管理工具集成，确保证书轮换可自动化。
- 定期审计 TLS 设置与加密强度，确保符合安全策略。
