# Athena工作平台 - 统一构建系统
# Unified Build System for Athena Platform
#
# 使用方法:
#   make help              # 显示所有可用命令
#   make certify           # 运行Agent认证
#   make test              # 运行测试套件
#   make lint              # 代码质量检查
#   make dev               # 启动开发环境

# ==================== 配置 ====================
.PHONY: help
.SILENT: help

# 项目配置
PROJECT_NAME := athena-platform
PYTHON := python3
POETRY := poetry
DOCKER_COMPOSE := docker-compose

# 目录配置
CORE_DIR := core
TESTS_DIR := tests
TOOLS_DIR := tools
REPORTS_DIR := reports
DOCS_DIR := docs

# 颜色输出
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_RED := \033[31m

# ==================== Agent认证系统 ====================
## 认证相关命令
.PHONY: certify certify-strict certify-fast certify-badges certify-report

# 默认认证
certify:
	@echo "$(COLOR_BLUE)🏆 运行Agent认证...$(COLOR_RESET)"
	@$(PYTHON) $(TOOLS_DIR)/agent_certifier.py --all --report $(REPORTS_DIR)/certification_report.json

# 严格模式认证
certify-strict:
	@echo "$(COLOR_BLUE)🏆 运行Agent认证（严格模式）...$(COLOR_RESET)"
	@$(PYTHON) $(TOOLS_DIR)/agent_certifier.py --all --strict --report $(REPORTS_DIR)/certification_report_strict.json

# 快速认证（跳过性能检查）
certify-fast:
	@echo "$(COLOR_BLUE)⚡ 运行Agent认证（快速模式）...$(COLOR_RESET)"
	@$(PYTHON) $(TOOLS_DIR)/agent_certifier.py --all --skip-performance --report $(REPORTS_DIR)/certification_report_fast.json

# 生成认证徽章
certify-badges:
	@echo "$(COLOR_BLUE)🎨 生成认证徽章...$(COLOR_RESET)"
	@$(PYTHON) $(TOOLS_DIR)/agent_certifier.py --all --generate-badges

# 查看认证报告
certify-report:
	@echo "$(COLOR_BLUE)📊 认证报告摘要:$(COLOR_RESET)"
	@if [ -f "$(REPORTS_DIR)/certification_report.json" ]; then \
		cat $(REPORTS_DIR)/certification_report.json | $(PYTHON) -m json.tool | head -50; \
	else \
		echo "$(COLOR_YELLOW)⚠️  报告不存在，请先运行 'make certify'$(COLOR_RESET)"; \
	fi

# ==================== 测试系统 ====================
## 测试相关命令
.PHONY: test test-unit test-integration test-e2e test-cov test-watch

# 运行所有测试
test:
	@echo "$(COLOR_BLUE)🧪 运行测试套件...$(COLOR_RESET)"
	@$(POETRY) run pytest $(TESTS_DIR) -v

# 单元测试
test-unit:
	@echo "$(COLOR_BLUE)🧪 运行单元测试...$(COLOR_RESET)"
	@$(POETRY) run pytest $(TESTS_DIR) -v -m unit

# 集成测试
test-integration:
	@echo "$(COLOR_BLUE)🧪 运行集成测试...$(COLOR_RESET)"
	@$(POETRY) run pytest $(TESTS_DIR) -v -m integration

# 端到端测试
test-e2e:
	@echo "$(COLOR_BLUE)🧪 运行端到端测试...$(COLOR_RESET)"
	@$(POETRY) run pytest $(TESTS_DIR) -v -m e2e

# 测试覆盖率
test-cov:
	@echo "$(COLOR_BLUE)📊 生成测试覆盖率报告...$(COLOR_RESET)"
	@$(POETRY) run pytest $(TESTS_DIR) --cov=$(CORE_DIR) --cov-report=html --cov-report=term
	@echo "$(COLOR_GREEN)✅ 覆盖率报告: htmlcov/index.html$(COLOR_RESET)"

# 监视模式测试
test-watch:
	@echo "$(COLOR_BLUE)👀 监视模式测试...$(COLOR_RESET)"
	@$(POETRY) run pytest $(TESTS_DIR) -v -f

# ==================== 代码质量 ====================
## 代码检查和格式化
.PHONY: lint lint-fix format format-check type-check security-check

# 代码质量检查（ruff）
lint:
	@echo "$(COLOR_BLUE)🔍 运行代码质量检查...$(COLOR_RESET)"
	@$(POETRY) run ruff check .
	@$(POETRY) run ruff format --check .

# 自动修复lint问题
lint-fix:
	@echo "$(COLOR_BLUE)🔧 自动修复代码问题...$(COLOR_RESET)"
	@$(POETRY) run ruff check . --fix
	@$(POETRY) run ruff format .

# 代码格式化
format:
	@echo "$(COLOR_BLUE)✨ 格式化代码...$(COLOR_RESET)"
	@$(POETRY) run ruff format .

# 检查格式
format-check:
	@echo "$(COLOR_BLUE)📝 检查代码格式...$(COLOR_RESET)"
	@$(POETRY) run ruff format --check .

# 类型检查
type-check:
	@echo "$(COLOR_BLUE)🔬 运行类型检查...$(COLOR_RESET)"
	@$(POETRY) run mypy $(CORE_DIR)

# 安全检查
security-check:
	@echo "$(COLOR_BLUE)🔒 运行安全检查...$(COLOR_RESET)"
	@$(POETRY) run bandit -r $(CORE_DIR)

# ==================== 依赖管理 ====================
## 依赖安装和更新
.PHONY: install install-dev update-deps lock-deps

# 安装依赖
install:
	@echo "$(COLOR_BLUE)📦 安装项目依赖...$(COLOR_RESET)"
	@$(POETRY) install

# 安装开发依赖
install-dev:
	@echo "$(COLOR_BLUE)📦 安装开发依赖...$(COLOR_RESET)"
	@$(POETRY) install --with dev,test,lint

# 更新依赖
update-deps:
	@echo "$(COLOR_BLUE)🔄 更新依赖...$(COLOR_RESET)"
	@$(POETRY) update

# 锁定依赖版本
lock-deps:
	@echo "$(COLOR_BLUE)🔒 锁定依赖版本...$(COLOR_RESET)"
	@$(POETry) lock

# ==================== Docker操作 ====================
## Docker相关命令
.PHONY: docker-up docker-down docker-logs docker-restart docker-build

# 启动开发环境
docker-up:
	@echo "$(COLOR_BLUE)🐳 启动Docker开发环境...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) -f docker-compose.unified.yml --profile dev up -d

# 停止环境
docker-down:
	@echo "$(COLOR_BLUE)🐳 停止Docker环境...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) -f docker-compose.unified.yml --profile dev down

# 查看日志
docker-logs:
	@$(DOCKER_COMPOSE) -f docker-compose.unified.yml --profile dev logs -f

# 重启服务
docker-restart:
	@echo "$(COLOR_BLUE)🐳 重启Docker服务...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) -f docker-compose.unified.yml --profile dev restart

# 构建镜像
docker-build:
	@echo "$(COLOR_BLUE)🐳 构建Docker镜像...$(COLOR_RESET)"
	@$(DOCKER_COMPOSE) -f docker-compose.unified.yml build

# ==================== 开发工具 ====================
## 开发辅助命令
.PHONY: dev dev-xiaona clean clean-all docs-serve docs-build

# 启动开发环境
dev:
	@echo "$(COLOR_BLUE)🚀 启动Athena平台...$(COLOR_RESET)"
	@$(PYTHON) scripts/xiaonuo_unified_startup.py 启动平台

# 仅启动小娜
dev-xiaona:
	@echo "$(COLOR_BLUE)🚀 启动小娜Agent...$(COLOR_RESET)"
	@$(PYTHON) start_xiaona.py

# 清理临时文件
clean:
	@echo "$(COLOR_BLUE)🧹 清理临时文件...$(COLOR_RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(COLOR_GREEN)✅ 清理完成$(COLOR_RESET)"

# 深度清理
clean-all: clean
	@echo "$(COLOR_BLUE)🧹 深度清理...$(COLOR_RESET)"
	@rm -rf .venv/ 2>/dev/null || true
	@echo "$(COLOR_YELLOW)⚠️  虚拟环境已删除，请运行 'make install' 重新安装$(COLOR_RESET)"

# 启动文档服务器
docs-serve:
	@echo "$(COLOR_BLUE)📚 启动文档服务器...$(COLOR_RESET)"
	@cd $(DOCS_DIR) && $(PYTHON) -m http.server 8000

# 构建文档
docs-build:
	@echo "$(COLOR_BLUE)📚 构建文档...$(COLOR_RESET)"
	@$(MAKE) -C $(DOCS_DIR) html

# ==================== 质量门禁 ====================
## 质量检查综合命令
.PHONY: quality-gate pre-commit-check ci-check

# 质量门禁（提交前检查）
quality-gate: lint format-check test-unit certify-fast
	@echo "$(COLOR_GREEN)✅ 质量门禁通过！$(COLOR_RESET)"

# Pre-commit检查
pre-commit-check: lint-fix format-check test-unit
	@echo "$(COLOR_GREEN)✅ Pre-commit检查通过！$(COLOR_RESET)"

# CI完整检查
ci-check: lint format-check type-check test certify
	@echo "$(COLOR_GREEN)✅ CI检查通过！$(COLOR_RESET)"

# ==================== Git Hooks ====================
## Git钩子安装
.PHONY: install-hooks uninstall-hooks

# 安装Git hooks
install-hooks:
	@echo "$(COLOR_BLUE)🪝 安装Git hooks...$(COLOR_RESET)"
	@chmod +x scripts/githooks/pre-commit
	@chmod +x scripts/githooks/pre-push
	@ln -sf $$(pwd)/scripts/githooks/pre-commit .git/hooks/pre-commit
	@ln -sf $$(pwd)/scripts/githooks/pre-push .git/hooks/pre-push
	@echo "$(COLOR_GREEN)✅ Git hooks已安装$(COLOR_RESET)"

# 卸载Git hooks
uninstall-hooks:
	@echo "$(COLOR_BLUE)🪝 卸载Git hooks...$(COLOR_RESET)"
	@rm -f .git/hooks/pre-commit
	@rm -f .git/hooks/pre-push
	@echo "$(COLOR_YELLOW)⚠️  Git hooks已卸载$(COLOR_RESET)"

# ==================== 信息查看 ====================
## 显示项目信息
.PHONY: info version env-info

# 项目信息
info:
	@echo "$(COLOR_BOLD)Athena工作平台$(COLOR_RESET)"
	@echo ""
	@echo "项目名称: $(PROJECT_NAME)"
	@echo "Python版本: $$($(PYTHON) --version))"
	@echo "Poetry版本: $$($(POETRY) --version))"
	@echo "Git分支: $$(git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo "Git提交: $$(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"

# 版本信息
version:
	@echo "$(COLOR_BOLD)项目版本:$(COLOR_RESET)"
	@$(POETRY) version

# 环境信息
env-info:
	@echo "$(COLOR_BOLD)环境信息:$(COLOR_RESET)"
	@echo "Python: $$($(PYTHON) --version))"
	@echo "Poetry: $$($(POETRY) --version))"
	@echo "Docker: $$(docker --version 2>/dev/null || echo '未安装')"
	@echo "Docker Compose: $$($(DOCKER_COMPOSE) --version 2>/dev/null || echo '未安装')"

# ==================== 帮助信息 ====================
help:
	@echo "$(COLOR_BOLD)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)  Athena工作平台 - 统一构建系统$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)═══════════════════════════════════════════════════════$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)Agent认证:$(COLOR_RESET)"
	@echo "  make certify              运行Agent认证"
	@echo "  make certify-strict       严格模式认证"
	@echo "  make certify-fast         快速认证（跳过性能检查）"
	@echo "  make certify-badges       生成认证徽章"
	@echo "  make certify-report       查看认证报告"
	@echo ""
	@echo "$(COLOR_GREEN)测试:$(COLOR_RESET)"
	@echo "  make test                 运行所有测试"
	@echo "  make test-unit            单元测试"
	@echo "  make test-integration     集成测试"
	@echo "  make test-e2e             端到端测试"
	@echo "  make test-cov             测试覆盖率报告"
	@echo "  make test-watch           监视模式测试"
	@echo ""
	@echo "$(COLOR_GREEN)代码质量:$(COLOR_RESET)"
	@echo "  make lint                 代码质量检查"
	@echo "  make lint-fix             自动修复代码问题"
	@echo "  make format               格式化代码"
	@echo "  make format-check         检查代码格式"
	@echo "  make type-check           类型检查"
	@echo "  make security-check       安全检查"
	@echo ""
	@echo "$(COLOR_GREEN)依赖管理:$(COLOR_RESET)"
	@echo "  make install              安装依赖"
	@echo "  make install-dev          安装开发依赖"
	@echo "  make update-deps          更新依赖"
	@echo ""
	@echo "$(COLOR_GREEN)Docker:$(COLOR_RESET)"
	@echo "  make docker-up            启动开发环境"
	@echo "  make docker-down          停止环境"
	@echo "  make docker-logs          查看日志"
	@echo "  make docker-build         构建镜像"
	@echo ""
	@echo "$(COLOR_GREEN)开发:$(COLOR_RESET)"
	@echo "  make dev                  启动Athena平台"
	@echo "  make dev-xiaona           启动小娜Agent"
	@echo "  make clean                清理临时文件"
	@echo "  make clean-all            深度清理"
	@echo ""
	@echo "$(COLOR_GREEN)质量门禁:$(COLOR_RESET)"
	@echo "  make quality-gate         提交前质量检查"
	@echo "  make pre-commit-check     Pre-commit检查"
	@echo "  make ci-check             CI完整检查"
	@echo ""
	@echo "$(COLOR_GREEN)Git Hooks:$(COLOR_RESET)"
	@echo "  make install-hooks        安装Git hooks"
	@echo "  make uninstall-hooks      卸载Git hooks"
	@echo ""
	@echo "$(COLOR_GREEN)信息:$(COLOR_RESET)"
	@echo "  make info                 项目信息"
	@echo "  make version              版本信息"
	@echo "  make env-info             环境信息"
	@echo ""
	@echo "$(COLOR_BOLD)═══════════════════════════════════════════════════════$(COLOR_RESET)"
