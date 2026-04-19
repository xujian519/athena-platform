# Athena API Gateway Makefile

.PHONY: help build test docker-build docker-up docker-down clean fmt lint vet coverage

# 默认目标
.DEFAULT_GOAL := help

# 变量定义
BINARY_NAME=gateway
BUILD_DIR=build
DOCKER_IMAGE=athena-gateway
DOCKER_TAG=latest

# Go相关变量
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
GOMOD=$(GOCMD) mod
GOFMT=gofmt

# 构建标志
LDFLAGS=-ldflags "-X main.Version=$(shell git describe --tags --always --dirty 2>/dev/null || echo 'dev')"

# 帮助信息
help: ## 显示帮助信息
	@echo "Athena API Gateway 开发工具"
	@echo ""
	@echo "可用命令:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

# 安装依赖
deps: ## 安装Go依赖
	@echo "安装依赖..."
	$(GOMOD) download
	$(GOMOD) verify

# 代码格式化
fmt: ## 格式化Go代码
	@echo "格式化代码..."
	$(GOFMT) -s -w .

# 代码检查
lint: ## 运行代码检查
	@echo "运行代码检查..."
	@if ! command -v golangci-lint &> /dev/null; then \
		echo "安装golangci-lint..."; \
		go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest; \
	fi
	golangci-lint run

# 静态分析
vet: ## 运行go vet
	@echo "运行go vet..."
	$(GOCMD) vet ./...

# 运行测试
test: ## 运行单元测试
	@echo "运行测试..."
	$(GOTEST) -v -race -coverprofile=coverage.out ./...

# 运行基准测试
benchmark: ## 运行基准测试
	@echo "运行基准测试..."
	$(GOTEST) -bench=. -benchmem ./...

# 测试覆盖率
coverage: test ## 生成测试覆盖率报告
	@echo "生成覆盖率报告..."
	$(GOCMD) tool cover -html=coverage.out -o coverage.html
	@echo "覆盖率报告: coverage.html"

# 构建应用
build: ## 构建二进制文件
	@echo "构建应用..."
	@mkdir -p $(BUILD_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME) cmd/gateway/main.go
	@echo "构建完成: $(BUILD_DIR)/$(BINARY_NAME)"

# 交叉编译
build-all: ## 交叉编译所有平台
	@echo "交叉编译..."
	@mkdir -p $(BUILD_DIR)
	@echo "构建Linux AMD64..."
	GOOS=linux GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-linux-amd64 cmd/gateway/main.go
	@echo "构建Darwin AMD64..."
	GOOS=darwin GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-darwin-amd64 cmd/gateway/main.go
	@echo "构建Windows AMD64..."
	GOOS=windows GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BUILD_DIR)/$(BINARY_NAME)-windows-amd64.exe cmd/gateway/main.go

# 构建Docker镜像
docker-build: ## 构建Docker镜像
	@echo "构建Docker镜像..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# 推送Docker镜像
docker-push: docker-build ## 推送Docker镜像到仓库
	@echo "推送Docker镜像..."
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

# 启动Docker服务
docker-up: ## 启动Docker Compose服务
	@echo "启动Docker服务..."
	docker-compose up -d

# 停止Docker服务
docker-down: ## 停止Docker Compose服务
	@echo "停止Docker服务..."
	docker-compose down

# 查看Docker日志
docker-logs: ## 查看Docker服务日志
	@echo "查看Docker日志..."
	docker-compose logs -f athena-gateway

# 重启Docker服务
docker-restart: docker-down docker-up ## 重启Docker Compose服务

# Docker健康检查
docker-health: ## 检查Docker服务健康状态
	@echo "检查服务健康状态..."
	curl -f http://localhost:8080/health || echo "❌ 网关不健康"

# 本地开发环境
dev: ## 启动本地开发环境
	@echo "启动开发环境..."
	$(MAKE) deps
	$(MAKE) fmt
	$(MAKE) docker-up
	@echo "开发环境已启动"
	@echo "API网关: http://localhost:8080"
	@echo "监控指标: http://localhost:9090/metrics"

# 生产环境构建
prod: ## 构建生产环境
	@echo "构建生产环境..."
	CGO_ENABLED=0 GOOS=linux $(GOBUILD) $(LDFLAGS) -a -installsuffix cgo -o $(BUILD_DIR)/$(BINARY_NAME) cmd/gateway/main.go
	@echo "生产构建完成"

# 代码质量检查
quality: fmt lint vet test ## 运行所有代码质量检查

# CI流水线
ci: deps quality build ## 运行CI流水线

# 清理构建文件
clean: ## 清理构建文件
	@echo "清理构建文件..."
	$(GOCLEAN)
	rm -rf $(BUILD_DIR)
	rm -f coverage.out coverage.html
	@echo "清理完成"

# 清理Docker资源
docker-clean: ## 清理Docker资源
	@echo "清理Docker资源..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "Docker资源清理完成"

# 安装开发工具
install-tools: ## 安装开发工具
	@echo "安装开发工具..."
	@echo "安装golangci-lint..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	@echo "安装mockgen..."
	go install github.com/golang/mock/mockgen@latest
	@echo "安装swag..."
	go install github.com/swaggo/swag/cmd/swag@latest
	@echo "安装开发工具完成"

# 生成mock文件
mocks: ## 生成mock文件
	@echo "生成mock文件..."
	mockgen -source=internal/services/manager.go -destination=tests/mocks/services_mock.go -package=mocks

# 生成API文档
docs: ## 生成API文档
	@echo "生成API文档..."
	swag init -g cmd/gateway/main.go
	swag info -g cmd/gateway/main.go
	swag go -g cmd/gateway/main.go

# 运行应用
run: ## 运行应用
	@echo "运行应用..."
	$(BUILD_DIR)/$(BINARY_NAME) -config config/config.yaml

# 运行应用并监控
run-debug: ## 运行应用（调试模式）
	@echo "运行应用（调试模式）..."
	$(BUILD_DIR)/$(BINARY_NAME) -config config/config.yaml -debug

# 数据库迁移
migrate: ## 运行数据库迁移
	@echo "运行数据库迁移..."
	$(BUILD_DIR)/$(BINARY_NAME) -config config/config.yaml migrate

# 备份数据
backup: ## 备份数据库
	@echo "备份数据库..."
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U athena athena_gateway > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "备份完成"

# 检查依赖安全
security-scan: ## 扫描依赖安全漏洞
	@echo "扫描依赖安全漏洞..."
	@go list -json -m all | nancy sleuth

# 性能分析
profile: ## 运行性能分析
	@echo "运行性能分析..."
	$(GOTEST) -cpuprofile=cpu.prof -memprofile=mem.prof -bench=. ./...
	@echo "性能文件已生成: cpu.prof, mem.prof"
	@echo "使用 'go tool pprof cpu.prof' 查看CPU性能"
	@echo "使用 'go tool pprof mem.prof' 查看内存性能"

# 查看项目信息
info: ## 显示项目信息
	@echo "项目信息:"
	@echo "名称: Athena API Gateway"
	@echo "版本: $(shell git describe --tags --always --dirty 2>/dev/null || echo 'dev')"
	@echo "Go版本: $(shell go version)"
	@echo "构建目录: $(BUILD_DIR)"
	@echo "Docker镜像: $(DOCKER_IMAGE):$(DOCKER_TAG)"

# Git钩子安装
install-hooks: ## 安装Git钩子
	@echo "安装Git钩子..."
	@mkdir -p .git/hooks
	@echo "#!/bin/sh" > .git/hooks/pre-commit
	@echo "make fmt" >> .git/hooks/pre-commit
	@echo "make lint" >> .git/hooks/pre-commit
	@echo "make vet" >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Git钩子安装完成"

# 快速修复
fix: ## 快速修复常见问题
	@echo "快速修复..."
	$(MAKE) fmt
	$(MAKE) vet
	@echo "修复完成"

# 更新依赖
update-deps: ## 更新依赖
	@echo "更新依赖..."
	$(GOMOD) get -u
	$(GOMOD) tidy
	@echo "依赖更新完成"

# 验证依赖
verify-deps: ## 验证依赖
	@echo "验证依赖..."
	$(GOMOD) verify
	@echo "依赖验证完成"