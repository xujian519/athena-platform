# 多阶段构建Dockerfile
# 构建阶段
FROM golang:1.21-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装git（某些依赖需要）
RUN apk add --no-cache git

# 复制go mod文件
COPY go.mod go.sum ./

# 下载依赖
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o athena-gateway cmd/server/main.go

# 运行阶段
FROM alpine:latest

# 安装ca证书和时区数据
RUN apk --no-cache add ca-certificates tzdata

# 创建非root用户
RUN addgroup -g 1001 -S athena && \
    adduser -u 1001 -S athena -G athena

# 设置工作目录
WORKDIR /app

# 复制构建的二进制文件
COPY --from=builder /app/athena-gateway .

# 复制配置文件
COPY --from=builder /app/configs ./configs

# 创建日志目录
RUN mkdir -p /var/log/athena-gateway && \
    chown -R athena:athena /var/log/athena-gateway /app

# 切换到非root用户
USER athena

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV ATHENA_GATEWAY_ENV=production

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 启动应用
CMD ["./athena-gateway", "--config", "configs/config.yaml"]