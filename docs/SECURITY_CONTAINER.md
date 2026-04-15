# Security hardening: container images and deployment for Athena API Gateway

## 目标
- 生产环境的容器镜像最小化、权限最小化、密钥管理与运行时防护，确保合规性与可审计性。
- 与现有配置管理和结构化日志实现对齐，保持与现有基础设施的兼容性。

## 组件概览
- 多阶段构建镜像：docker/Dockerfile.secure，减少运行时镜像体积，降低攻击面。
- 运行时非 root 用户：镜像和 Kubernetes 部署均采用非 root 用户执行，最小权限。
- 静态与动态漏洞扫描：CI/CD 集成 Trivy 扫描，阻断高严重性漏洞的合并与部署。
- 运行时防护：AppArmor、seccomp 策略绑定，以及只读根文件系统配置。
- 秘密管理：通过 Kubernetes Secrets 集成，镜像不含敏感信息。
- 网络安全：通过 NetworkPolicy、mTLS（如 Istio/Linkerd）实现分段和双向认证。

## 关键实现要点
- 构建镜像
  - 使用多阶段静态构建，builder 阶段安装依赖，运行时镜像仅包含应用代码与最小运行时依赖。
  - 以非 root 用户运行应用，避免特权提升风险。
  - 去除非运行时工具，确保只暴露必要端口（如 8000）。
- 安全扫描
  - 在 CI 中对 secure 镜像执行 Trivy 扫描， HIGH/CRITICAL 漏洞导致构建失败。
- Kubernetes 部署
  - 将敏感信息通过 Secrets 提供，挂载到 /secrets，避免镜像中明文凭据。
  - Pod/容器运行时上下文启用 readOnlyRootFilesystem、drop 能力集、Seccomp、AppArmor。
- 运行时策略
  - 使用 RuntimeDefault seccomp 配置，外部加载自定义 seccomp.json（如 athena-gateway-seccomp.json）。
  - AppArmor profile 绑定到 athena-api-gateway 容器。
- 网络策略
  - 限制 Ingress/ Egress，默认拒绝非授权来源，结合服务网格实现 mTLS。

## 验证步骤
- 本地/CI 构建 img: docker/Dockerfile.secure → athena-api-gateway-secure:latest
- 使用 Trivy 对镜像进行漏洞扫描，确保 HIGH/CRITICAL 为 0 或被接受的数量。
- 部署到 k8s，检查：容器以非 root 用户运行、只读根文件系统、seccomp 与 AppArmor 策略生效。
- 秘密通过 Secrets 挂载，确保容器内无敏感信息暴露。
- 应用访问通过 mTLS，以及网络策略生效。
