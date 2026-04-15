# Athena API Gateway Makefile
# 用途: 提供常用开发和部署命令

.PHONY: help build test clean run docker-build docker-run docker-stop lint fmt vet

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
BINARY_NAME := athena-gateway
BUILD_DIR := ./dist
DOCKER_IMAGE := athena-gateway
DOCKER_TAG := latest
VERSION := 1.0.0

# Go相关变量
GOCMD := go
GOBUILD := $(GOCMD) build
GOCLEAN := $(GOCMD) clean
GOTEST := $(GOCMD) test
GOGET := $(GOCMD) get
GOMOD := $(GOCMD) mod

# 构建标志
LDFLAGS := -ldflags "-X main.Version=$(VERSION) -X main.BuildTime=$(shell date -u '+%Y-%m-%dT%H:%M:%SZ') -X main.GitCommit=$(shell git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

# 帮助信息
help: ## 显示帮助信息
	@echo "Athena API Gateway 开发工具"
	@echo ""
	@echo "可用命令:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "示例:"
	@echo "  make build           # 构建应用"
	@echo "  make test            # 运行测试"
	@echo "  make docker-build    # 构建Docker镜像"
	@echo "  make docker-run      # 运行Docker容器"

# 代码检查
fmt: ## 格式化Go代码
	$(GOCMD) fmt ./...

vet: ## 检查Go代码
	$(GOCMD) vet ./...

lint: ## 运行代码检查
	@if command -v golangci-lint >/dev/null 2>&1; then \
		golangci-lint run; \
	else \
		echo "golangci-lint未安装，跳过代码检查"; \
	fi

# 依赖管理
deps: ## 下载Go依赖
	$(GOMOD) download
	$(GOMOD) tidy

deps-update: ## 更新Go依赖
	$(GOGET) -u ./...

# 构建
build: ## 构建应用
	@echo "构建 $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) cmd/server/main.go
	@echo "构建完成: $(BUILD_DIR)/$(BINARY_NAME)"

build-linux: ## 构建Linux版本
	@echo "构建Linux版本 $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	CGO_ENABLED=0 GOOS=linux $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-linux cmd/server/main.go
	@echo "Linux版本构建完成: $(BUILD_DIR)/$(BINARY_NAME)-linux"

build-all: ## 构建所有平台版本
	@echo "构建所有平台版本..."
	@mkdir -p $(BUILD_DIR)
	
	# Linux AMD64
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 cmd/server/main.go
	
	# Linux ARM64
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-linux-arm64 cmd/server/main.go
	
	# macOS AMD64
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-darwin-amd64 cmd/server/main.go
	
	# macOS ARM64
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-darwin-arm64 cmd/server/main.go
	
	# Windows AMD64
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-windows-amd64.exe cmd/server/main.go
	
	@echo "所有平台版本构建完成"

# 测试
test: ## 运行单元测试
	$(GOTEST) -v ./...

test-race: ## 运行竞态检测测试
	$(GOTEST) -race -v ./...

test-cover: ## 运行测试并生成覆盖率报告
	$(GOTEST) -v -coverprofile=coverage.out ./...
	$(GOCMD) tool cover -html=coverage.out -o coverage.html
	@echo "覆盖率报告已生成: coverage.html"

test-integration: ## 运行集成测试
	$(GOTEST) -v -tags=integration ./tests/integration/...

test-all: ## 运行所有测试
	$(GOTEST) -v -race -coverprofile=coverage.out ./...
	$(GOTEST) -v -tags=integration ./tests/integration/...

# 运行
run: ## 运行应用（开发模式）
	$(GOCMD) run cmd/server/main.go --config configs/config.dev.yaml

run-prod: ## 运行应用（生产模式）
	$(GOCMD) run cmd/server/main.go --config configs/config.prod.yaml

# 清理
clean: ## 清理构建文件
	@echo "清理构建文件..."
	$(GOCLEAN)
	rm -rf $(BUILD_DIR)
	rm -f coverage.out coverage.html
	@echo "清理完成"

clean-docker: ## 清理Docker相关文件
	@echo "清理Docker文件..."
	docker system prune -f
	docker volume prune -f
	@echo "Docker清理完成"

# Docker
docker-build: ## 构建Docker镜像
	@echo "构建Docker镜像 $(DOCKER_IMAGE):$(DOCKER_TAG)..."
	docker build -f deployments/docker/Dockerfile -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "Docker镜像构建完成"

docker-build-multi: ## 构建多平台Docker镜像
	@echo "构建多平台Docker镜像..."
	docker buildx build --platform linux/amd64,linux/arm64 -f deployments/docker/Dockerfile -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## 运行Docker容器
	@echo "运行Docker容器..."
	docker run -d \
		--name $(BINARY_NAME) \
		-p 8080:8080 \
		-v $(PWD)/configs:/app/configs \
		-v athena_logs:/var/log/athena-gateway \
		$(DOCKER_IMAGE):$(DOCKER_TAG)

docker-stop: ## 停止Docker容器
	@echo "停止Docker容器..."
	docker stop $(BINARY_NAME) || true
	docker rm $(BINARY_NAME) || true

docker-compose-up: ## 启动Docker Compose服务
	@echo "启动Docker Compose服务..."
	cd deployments/docker && docker-compose up -d

docker-compose-down: ## 停止Docker Compose服务
	@echo "停止Docker Compose服务..."
	cd deployments/docker && docker-compose down

docker-compose-logs: ## 查看Docker Compose日志
	cd deployments/docker && docker-compose logs -f

# 安装工具
install-tools: ## 安装开发工具
	@echo "安装开发工具..."
	$(GOGET) -u github.com/golangci/golangci-lint/cmd/golangci-lint
	$(GOGET) -u github.com/air-verse/air

# 开发工具
dev: ## 启动热重载开发服务器
	@if command -v air >/dev/null 2>&1; then \
		air -c .air.toml; \
	else \
		echo "air未安装，使用 'make install-tools' 安装"; \
	fi

# 生成
generate: ## 生成代码
	@echo "生成代码..."
	@if [ -f "api/api.go" ]; then \
		swag init -g cmd/server/main.go; \
		swag gen; \
	else \
		echo "未找到API定义文件"; \
	fi

# 安全
security-scan: ## 运行安全扫描
	@echo "运行安全扫描..."
	@if command -v gosec >/dev/null 2>&1; then \
		gosec ./...; \
	else \
		echo "gosec未安装，跳过安全扫描"; \
	fi

# 性能测试
bench: ## 运行性能测试
	$(GOTEST) -bench=. -benchmem ./...

# 版本信息
version: ## 显示版本信息
	@echo "版本: $(VERSION)"
	@echo "Git提交: $(shell git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
	@echo "构建时间: $(shell date -u '+%Y-%m-%dT%H:%M:%SZ')"

# 安装
install: build ## 安装到本地
	@echo "安装 $(BINARY_NAME) 到 /usr/local/bin..."
	cp $(BUILD_DIR)/$(BINARY_NAME) /usr/local/bin/
	@echo "安装完成"

# 发布
release: clean test build ## 创建发布包
	@echo "创建发布包..."
	@mkdir -p $(BUILD_DIR)/release
	@cp $(BUILD_DIR)/$(BINARY_NAME) $(BUILD_DIR)/release/
	@cp -r configs $(BUILD_DIR)/release/
	@cp -r deployments $(BUILD_DIR)/release/
	@cp README.md $(BUILD_DIR)/release/ 2>/dev/null || true
	@cp LICENSE $(BUILD_DIR)/release/ 2>/dev/null || true
	@cd $(BUILD_DIR) && tar -czf $(BINARY_NAME)-$(VERSION).tar.gz release
	@rm -rf $(BUILD_DIR)/release
	@echo "发布包已创建: $(BUILD_DIR)/$(BINARY_NAME)-$(VERSION).tar.gz"