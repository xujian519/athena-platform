Service Mesh Routing Mapping for Athena Gateway

概览
- 将 Athena Gateway 的路由语义映射到服务网格（Istio/Linkerd）中的原语，以实现集中化的流量控制、可观测性和策略执行。

映射原则
- 保留现有 API 路径、方法、认证语义，尽量不改变对外行为。
- 使用网格原语统一管理路由、熔断、超时、重试、流量分发等策略。
- 将网关入口的路由决策迁移到 VirtualService/RouteConfiguration 的配置上，后端服务的路由由 DestinationRule 和服务发现管理。

组件对比映射表
- Athena Gateway 组件 -> mesh 原语
  - Ingress/入口：Istio Gateway 或 Linkerd IngressGateway -> 入口流量暴露与 TLS 配置
  - 路由决策：VirtualService（Istio）/ ServiceRoute（Linkerd） -> 将路径、主机、权重、匹配条件映射到网格路由
  - 后端目标：DestinationRule（Istio）/ ServiceProfile（Linkerd） -> 指定负载均衡、超时、重试、熔断策略
  - 证书与 TLS：Gateway TLS 设置、Peer Authentication 的策略配置
  - 策略：AuthorizationPolicy（Istio）/ Policy（Linkerd） -> 访问控制
  - 观测：Telemetry 与 Prometheus/Jaeger 集成点
  - 安全标识：SPIFFE 标识与服务账号映射

示例：梯形路由映射（简化）
- 场景：/api/v1/users 映射到 athena-gateway.users.svc.cluster.local:8080，使用 30s 超时，重试 2 次。
- Istio YAML 片段（伪示例，需替换名称和命名空间）

apiVersion: networking.istio.io/v1alpha3
kind: Gateway
metadata:
  name: athena-gateway-ingress
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: athena-gateway-tls
      minProtocolVersion: TLSV1_2
    hosts:
    - "gateway.athena.example.com"

apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: athena-gateway
  namespace: default
spec:
  hosts:
  - "gateway.athena.example.com"
  gateways:
  - athena-gateway-ingress
  http:
  - match:
    - uri:
        prefix: "/api/v1/users"
    route:
    - destination:
        host: athena-gateway.default.svc.cluster.local
        port:
          number: 8080
    timeout: 30s
    retries:
      attempts: 2
      perTryTimeout: 5s

产出
- 1) 可追踪的路由映射模板，用于逐步替换现有路由配置
- 2) 路由策略的版本控制与审计日志记录
- 3) 针对新的网格路由的测试用例与回滚点

落地建议
- 先在开发/测试命名空间进行路由映射的 PoC，确保对外接口行为保持一致。
- 将现有路由策略逐步迁移到网格配置，避免一次性大规模修改。
- 记录变更日志与回滚步骤，确保可追溯。
