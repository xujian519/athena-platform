# Athena API Gateway Makefile

# 变量定义
BINARY_NAME=gateway
VERSION=$(shell git describe --tags --always --dirty)
BUILD_TIME=$(shell date +%Y-%m-%dT%H:%M:%S)
GO_VERSION=$(shell go version | awk '{print $$3}')
LDFLAGS=-ldflags "-X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME) -X main.GoVersion=$(GO_VERSION)"

# 默认目标
.PHONY: all
all: clean fmt vet test build

# 构建二进制文件
.PHONY: build
build:
	@echo "Building $(BINARY_NAME)..."
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o bin/$(BINARY_NAME) cmd/gateway/main.go

# 构建本地二进制文件
.PHONY: build-local
build-local:
	@echo "Building $(BINARY_NAME) for local..."
	go build $(LDFLAGS) -o bin/$(BINARY_NAME) cmd/gateway/main.go

# 构建多平台二进制文件
.PHONY: build-all
build-all:
	@echo "Building $(BINARY_NAME) for multiple platforms..."
	
	# Linux AMD64
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o bin/$(BINARY_NAME)-linux-amd64 cmd/gateway/main.go
	
	# Linux ARM64
	CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build $(LDFLAGS) -o bin/$(BINARY_NAME)-linux-arm64 cmd/gateway/main.go
	
	# macOS AMD64
	CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build $(LDFLAGS) -o bin/$(BINARY_NAME)-darwin-amd64 cmd/gateway/main.go
	
	# macOS ARM64 (Apple Silicon)
	CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o bin/$(BINARY_NAME)-darwin-arm64 cmd/gateway/main.go
	
	# Windows AMD64
	CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o bin/$(BINARY_NAME)-windows-amd64.exe cmd/gateway/main.go

# 运行服务（开发模式）
.PHONY: run-dev
run-dev:
	@echo "Running $(BINARY_NAME) in development mode..."
	go run cmd/gateway/main.go

# 运行服务（生产模式）
.PHONY: run-prod
run-prod: build
	@echo "Running $(BINARY_NAME) in production mode..."
	./bin/$(BINARY_NAME)

# 运行测试
.PHONY: test
test:
	@echo "Running tests..."
	go test -v ./...

# 运行单元测试
.PHONY: test-unit
test-unit:
	@echo "Running unit tests..."
	go test -v -tags=unit ./...

# 运行集成测试
.PHONY: test-integration
test-integration:
	@echo "Running integration tests..."
	go test -v -tags=integration ./...

# 运行性能测试
.PHONY: benchmark
benchmark:
	@echo "Running benchmarks..."
	go test -bench=. -benchmem ./...

# 生成测试覆盖率报告
.PHONY: coverage
coverage:
	@echo "Generating coverage report..."
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# 代码格式化
.PHONY: fmt
fmt:
	@echo "Formatting code..."
	go fmt ./...

# 代码检查
.PHONY: vet
vet:
	@echo "Vetting code..."
	go vet ./...

# 静态分析
.PHONY: lint
lint:
	@echo "Running linter..."
	golangci-lint run

# 安装依赖
.PHONY: deps
deps:
	@echo "Installing dependencies..."
	go mod download
	go mod tidy

# 更新依赖
.PHONY: deps-update
deps-update:
	@echo "Updating dependencies..."
	go get -u ./...
	go mod tidy

# 生成Mock文件
.PHONY: generate
generate:
	@echo "Generating code..."
	go generate ./...

# 生成Swagger文档
.PHONY: swagger
swagger:
	@echo "Generating Swagger documentation..."
	swag init -g cmd/gateway/main.go -o docs

# 清理构建文件
.PHONY: clean
clean:
	@echo "Cleaning build files..."
	rm -rf bin/
	rm -f coverage.out coverage.html
	rm -f docs/*.yaml docs/*.json

# 安装开发工具
.PHONY: install-tools
install-tools:
	@echo "Installing development tools..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install github.com/golang/mock/mockgen@latest
	go install github.com/swaggo/swag/cmd/swag@latest
	go install github.com/air-verse/air@latest

# Docker相关命令
.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	docker build -t athena-gateway:$(VERSION) .
	docker tag athena-gateway:$(VERSION) athena-gateway:latest

.PHONY: docker-run
docker-run:
	@echo "Running Docker container..."
	docker run --rm -p 8080:8080 athena-gateway:latest

.PHONY: docker-push
docker-push:
	@echo "Pushing Docker image..."
	docker push athena-gateway:$(VERSION)
	docker push athena-gateway:latest

# 热重载开发
.PHONY: dev
dev:
	@echo "Starting hot reload development server..."
	air

# 检查环境
.PHONY: check-env
check-env:
	@echo "Checking environment..."
	@go version
	@docker --version
	@redis-cli --version || echo "Redis CLI not found"

# 初始化项目
.PHONY: init
init:
	@echo "Initializing project..."
	@if [ ! -f go.mod ]; then go mod init github.com/athena-workspace/core/gateway; fi
	@go mod tidy
	@make install-tools
	@make generate
	@echo "Project initialization complete!"

# 发布前检查
.PHONY: pre-release
pre-release: clean fmt vet test build
	@echo "Pre-release checks completed!"

# 帮助信息
.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "  Build commands:"
	@echo "    build        Build the binary for Linux"
	@echo "    build-local  Build the binary for current platform"
	@echo "    build-all    Build binaries for all supported platforms"
	@echo ""
	@echo "  Run commands:"
	@echo "    run-dev      Run in development mode"
	@echo "    run-prod     Build and run in production mode"
	@echo "    dev          Hot reload development server"
	@echo ""
	@echo "  Test commands:"
	@echo "    test         Run all tests"
	@echo "    test-unit    Run unit tests"
	@echo "    test-integration Run integration tests"
	@echo "    benchmark    Run benchmarks"
	@echo "    coverage     Generate coverage report"
	@echo ""
	@echo "  Code quality:"
	@echo "    fmt          Format code"
	@echo "    vet          Vet code"
	@echo "    lint         Run linter"
	@echo "    clean        Clean build files"
	@echo ""
	@echo "  Dependencies:"
	@echo "    deps         Install dependencies"
	@echo "    deps-update  Update dependencies"
	@echo "    install-tools Install development tools"
	@echo ""
	@echo "  Generation:"
	@echo "    generate     Generate code"
	@echo "    swagger      Generate Swagger docs"
	@echo ""
	@echo "  Docker:"
	@echo "    docker-build Build Docker image"
	@echo "    docker-run   Run Docker container"
	@echo "    docker-push  Push Docker image"
	@echo ""
	@echo "  Utilities:"
	@echo "    init         Initialize project"
	@echo "    check-env    Check environment"
	@echo "    pre-release  Run pre-release checks"
	@echo "    help         Show this help message"