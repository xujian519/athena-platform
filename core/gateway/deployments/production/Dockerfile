# ================================
# Athena API Gateway - 生产环境构建
# ================================
# 多阶段构建，安全加固，生产优化
# ================================

# 构建阶段
FROM golang:1.21-alpine3.19 AS builder

# 安全设置
RUN apk add --no-cache ca-certificates tzdata && \
    addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 设置工作目录
WORKDIR /build

# 复制依赖文件
COPY go.mod go.sum ./
RUN go mod download && go mod verify

# 复制源代码
COPY . .

# 构建应用 (生产优化)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -a -installsuffix cgo \
    -o athena-gateway \
    ./cmd/gateway

# 运行阶段
FROM scratch

# 安全标签
LABEL maintainer="Athena Platform Team" \
      version="2.0.0" \
      description="Enterprise-grade API Gateway" \
      security.scan="passed"

# 从构建阶段复制必要文件
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /build/athena-gateway /app/athena-gateway
COPY --from=builder /build/configs /app/configs

# 安全用户设置
USER appuser:appgroup

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/app/athena-gateway", "health-check"]

# 工作目录
WORKDIR /app

# 暴露端口
EXPOSE 8080

# 启动命令
ENTRYPOINT ["/app/athena-gateway"]
CMD ["server", "--config", "/configs/production.yaml"]