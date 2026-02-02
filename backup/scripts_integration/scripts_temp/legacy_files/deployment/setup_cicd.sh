#!/bin/bash
# CI/CD自动化部署配置脚本
# CI/CD Automated Deployment Configuration for Athena

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
GITHUB_REPO="${GITHUB_REPO:-xujian519/Athena工作平台}"
DEPLOY_SERVER="${DEPLOY_SERVER:-172.20.0.10}"
DEPLOY_USER="${DEPLOY_USER:-deploy}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/athena}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查CI/CD依赖..."

    # 检查Git
    if ! command -v git &> /dev/null; then
        log_error "Git未安装，请先安装Git"
        exit 1
    fi

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi

    log_success "CI/CD依赖检查完成"
}

# 创建GitHub Actions工作流
create_github_workflows() {
    log_info "创建GitHub Actions工作流..."

    # 创建工作流目录
    mkdir -p "$PROJECT_ROOT/.github/workflows"

    # 基础CI工作流
    cat > "$PROJECT_ROOT/.github/workflows/ci.yml" << 'EOF'
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: 缓存依赖
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: 安装依赖
        run: |
          python -m pip install --upgrade pip
          pip install -r services/requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: 运行测试
        run: |
          pytest services/ -v --cov=services --cov-report=xml

      - name: 上传覆盖率
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: 安装依赖
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black isort pylint bandit safety

      - name: 运行代码格式检查
        run: |
          black --check services/
          isort --check-only services/

      - name: 运行代码质量检查
        run: |
          flake8 services/
          pylint services/ || true

      - name: 运行安全检查
        run: |
          bandit -r services/ -f json -o bandit-report.json
          safety check

      - name: 上传安全报告
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: bandit-report.json

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 运行Trivy漏洞扫描
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: 上传Trivy扫描结果
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
EOF

    # Docker镜像构建工作流
    cat > "$PROJECT_ROOT/.github/workflows/docker.yml" << 'EOF'
name: Docker Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: registry.cn-hangzhou.aliyuncs.com/athena
  IMAGE_NAME: multimodal-api

jobs:
  build:
    name: Build and Push
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: 登录到容器注册表
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: 提取元数据
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: 构建并推送镜像
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
EOF

    log_success "GitHub Actions工作流创建完成"
}

# 创建部署脚本
create_deploy_scripts() {
    log_info "创建部署脚本..."

    # 主部署脚本
    cat > "$PROJECT_ROOT/scripts/deploy.sh" << 'EOF'
#!/bin/bash
# 自动化部署脚本

set -e

# 配置
REMOTE_SERVER=${DEPLOY_SERVER:-172.20.0.10}
REMOTE_USER=${DEPLOY_USER:-deploy}
REMOTE_PATH=${DEPLOY_PATH:-/opt/athena}
BRANCH=${BRANCH:-main}
ENVIRONMENT=${ENVIRONMENT:-production}

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# 部署前检查
pre_deploy_check() {
    log_info "执行部署前检查..."

    # 检查本地代码
    if [ -n "$(git status --porcelain)" ]; then
        log_error "本地代码有未提交的更改"
        exit 1
    fi

    # 拉取最新代码
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH

    # 运行测试
    log_info "运行测试..."
    if command -v pytest &> /dev/null; then
        pytest services/ -x -v
    fi

    log_success "部署前检查完成"
}

# 同步代码
sync_code() {
    log_info "同步代码到服务器..."

    # 同步代码到远程服务器
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='logs' \
        --exclude='data' \
        --exclude='.env' \
        ./ ${REMOTE_USER}@${REMOTE_SERVER}:${REMOTE_PATH}/

    log_success "代码同步完成"
}

# 远程部署
remote_deploy() {
    log_info "在远程服务器上执行部署..."

    ssh ${REMOTE_USER}@${REMOTE_SERVER} << EOF
        set -e

        # 进入部署目录
        cd ${REMOTE_PATH}

        # 设置环境变量
        export ENVIRONMENT=${ENVIRONMENT}
        export BRANCH=${BRANCH}

        # 构建Docker镜像
        if [ -f "scripts/build_docker_images.sh" ]; then
            bash scripts/build_docker_images.sh
        fi

        # 部署服务
        if [ -f "scripts/deploy_docker.sh" ]; then
            bash scripts/deploy_docker.sh --skip-init
        fi

        # 运行健康检查
        if [ -f "scripts/health_check.sh" ]; then
            bash scripts/health_check.sh
        fi

        echo "远程部署完成"
EOF

    if [ $? -eq 0 ]; then
        log_success "远程部署完成"
    else
        log_error "远程部署失败"
        exit 1
    fi
}

# 部署后验证
post_deploy_verify() {
    log_info "执行部署后验证..."

    # 等待服务启动
    sleep 30

    # 检查服务健康状态
    if curl -f http://${REMOTE_SERVER}/health >/dev/null 2>&1; then
        log_success "服务健康检查通过"
    else
        log_error "服务健康检查失败"
        exit 1
    fi

    # 运行烟雾测试
    if command -v curl &> /dev/null; then
        log_info "运行烟雾测试..."
        curl -X POST http://${REMOTE_SERVER}/api/v1/test \
            -H "Content-Type: application/json" \
            -d '{"test": true}' || true
    fi

    log_success "部署后验证完成"
}

# 发送通知
send_notification() {
    log_info "发送部署通知..."

    MESSAGE="✅ Athena ${ENVIRONMENT} 环境部署成功\n分支: ${BRANCH}\n时间: $(date)"

    # 发送Slack通知
    if [ -n "${SLACK_WEBHOOK_URL}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"${MESSAGE}\"}" \
            ${SLACK_WEBHOOK_URL} || true
    fi

    # 发送邮件通知
    if [ -n "${NOTIFICATION_EMAIL}" ] && command -v mail &> /dev/null; then
        echo "${MESSAGE}" | mail -s "Athena部署通知" ${NOTIFICATION_EMAIL} || true
    fi

    log_success "通知发送完成"
}

# 主函数
main() {
    echo "============================================"
    echo "     Athena自动化部署"
    echo "     环境: ${ENVIRONMENT}"
    echo "     分支: ${BRANCH}"
    echo "     时间: $(date)"
    echo "============================================"

    pre_deploy_check
    sync_code
    remote_deploy
    post_deploy_verify
    send_notification

    echo "============================================"
    log_success "部署完成！"
    echo "============================================"
}

main "$@"
EOF

    # 回滚脚本
    cat > "$PROJECT_ROOT/scripts/rollback.sh" << 'EOF'
#!/bin/bash
# 回滚脚本

set -e

# 配置
REMOTE_SERVER=${DEPLOY_SERVER:-172.20.0.10}
REMOTE_USER=${DEPLOY_USER:-deploy}
REMOTE_PATH=${DEPLOY_PATH:-/opt/athena}
BACKUP_VERSION=${BACKUP_VERSION:-""}

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# 确认回滚
confirm_rollback() {
    echo "⚠️  警告：您即将回滚Athena生产环境"
    echo "这将撤销最近的部署更改"
    echo ""

    if [ -z "$BACKUP_VERSION" ]; then
        echo "请指定要回滚的版本:"
        ssh ${REMOTE_USER}@${REMOTE_SERVER} << EOF
            cd ${REMOTE_PATH}
            ls -la backups/ | grep -E "rollback_|backup_" | tail -10
EOF
        echo ""
        read -p "请输入备份版本 (例如: rollback_20231212_120000): " BACKUP_VERSION
    fi

    read -p "确定要回滚到版本 ${BACKUP_VERSION} 吗? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "回滚已取消"
        exit 0
    fi
}

# 执行回滚
execute_rollback() {
    log_info "执行回滚..."

    ssh ${REMOTE_USER}@${REMOTE_SERVER} << EOF
        set -e
        cd ${REMOTE_PATH}

        # 创建当前版本的备份
        BACKUP_NAME="rollback_$(date +%Y%m%d_%H%M%S)"
        docker-compose -f docker-compose.prod.yml down
        tar -czf "backups/\${BACKUP_NAME}.tar.gz" \
            docker-compose.prod.yml \
            .env.prod \
            configs/

        # 恢复备份版本
        if [ -f "backups/${BACKUP_VERSION}.tar.gz" ]; then
            tar -xzf "backups/${BACKUP_VERSION}.tar.gz"
            log_info "恢复配置文件完成"
        else
            log_error "备份文件不存在: backups/${BACKUP_VERSION}.tar.gz"
            exit 1
        fi

        # 恢复数据库（如果有）
        if [ -f "backups/${BACKUP_VERSION}_db.sql" ]; then
            docker-compose -f docker-compose.prod.yml exec postgres-primary \
                psql -U athena_user -d athena_production < "backups/${BACKUP_VERSION}_db.sql"
            log_info "数据库恢复完成"
        fi

        # 启动服务
        docker-compose -f docker-compose.prod.yml up -d

        # 等待服务启动
        sleep 30

        # 健康检查
        if curl -f http://localhost/health >/dev/null 2>&1; then
            log_success "服务启动成功"
        else
            log_error "服务启动失败"
            exit 1
        fi

        echo "回滚完成"
EOF

    if [ $? -eq 0 ]; then
        log_success "回滚执行成功"
    else
        log_error "回滚执行失败"
        exit 1
    fi
}

# 验证回滚
verify_rollback() {
    log_info "验证回滚结果..."

    # 检查服务状态
    if curl -f http://${REMOTE_SERVER}/health >/dev/null 2>&1; then
        log_success "回滚验证成功"
    else
        log_error "回滚验证失败"
        exit 1
    fi
}

# 发送通知
send_notification() {
    log_info "发送回滚通知..."

    MESSAGE="🔄 Athena生产环境已回滚\n版本: ${BACKUP_VERSION}\n时间: $(date)"

    # 发送Slack通知
    if [ -n "${SLACK_WEBHOOK_URL}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"${MESSAGE}\"}" \
            ${SLACK_WEBHOOK_URL} || true
    fi

    log_success "通知发送完成"
}

# 主函数
main() {
    echo "============================================"
    echo "     Athena回滚操作"
    echo "============================================"

    confirm_rollback
    execute_rollback
    verify_rollback
    send_notification

    echo "============================================"
    log_success "回滚完成！"
    echo "============================================"
}

main "$@"
EOF

    # 健康检查脚本
    cat > "$PROJECT_ROOT/scripts/health_check.sh" << 'EOF'
#!/bin/bash
# 健康检查脚本

SERVICES=(
    "nginx-lb:80:/health"
    "api-gateway:8020:/health"
    "dolphin-parser:8013:/health"
    "glm-vision:8091:/health"
    "multimodal-processor:8012:/"
    "xiao-nuo-control:9001:/health"
    "athena-platform:9000:/health"
    "platform-monitor:9090:/health"
)

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

check_service() {
    local service=$1
    local port=$2
    local path=$3

    if curl -f --max-time 10 "http://localhost:${port}${path}" >/dev/null 2>&1; then
        log_success "✓ $service"
        return 0
    else
        log_error "✗ $service"
        return 1
    fi
}

main() {
    echo "============================================"
    echo "     Athena健康检查"
    echo "     时间: $(date)"
    echo "============================================"

    failed_services=0

    for service_info in "${SERVICES[@]}"; do
        IFS=':' read -r service port path <<< "$service_info"
        check_service "$service" "$port" "$path" || ((failed_services++))
    done

    echo ""

    if [ $failed_services -eq 0 ]; then
        log_success "所有服务健康"
        exit 0
    else
        log_error "$failed_services 个服务异常"
        exit 1
    fi
}

main "$@"
EOF

    chmod +x "$PROJECT_ROOT/scripts/deploy.sh"
    chmod +x "$PROJECT_ROOT/scripts/rollback.sh"
    chmod +x "$PROJECT_ROOT/scripts/health_check.sh"

    log_success "部署脚本创建完成"
}

# 创建配置文件模板
create_config_templates() {
    log_info "创建配置文件模板..."

    # GitHub Actions配置模板
    cat > "$PROJECT_ROOT/.github/workflows.template.yml" << 'EOF'
# GitHub Actions配置模板
# 请复制到 .github/workflows/ 目录并根据需要修改

name: Deploy Template

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置环境变量
        run: |
          echo "DEPLOY_SERVER=${{ secrets.DEPLOY_SERVER }}" >> $GITHUB_ENV
          echo "DEPLOY_USER=${{ secrets.DEPLOY_USER }}" >> $GITHUB_ENV
          echo "DEPLOY_PATH=${{ secrets.DEPLOY_PATH }}" >> $GITHUB_ENV

      - name: 部署到服务器
        run: |
          bash scripts/deploy.sh
EOF

    # 部署配置模板
    cat > "$PROJECT_ROOT/deploy.config.template" << 'EOF'
# 部署配置模板
# 请复制为 deploy.config 并填写实际值

# 服务器配置
DEPLOY_SERVER=172.20.0.10
DEPLOY_USER=deploy
DEPLOY_PATH=/opt/athena

# 环境配置
ENVIRONMENT=production
BRANCH=main

# 通知配置
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
NOTIFICATION_EMAIL=admin@athena.multimodal.ai

# Docker配置
REGISTRY=registry.cn-hangzhou.aliyuncs.com/athena
IMAGE_VERSION=latest

# 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=athena_production
DB_USER=athena_user

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
EOF

    # 环境变量模板
    cat > "$PROJECT_ROOT/.env.template" << 'EOF'
# 环境变量模板
# 请复制为 .env 并填写实际值

# 应用配置
APP_NAME=athena-prod
APP_VERSION=2.0.0
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://athena_user:password@localhost:5432/athena_production

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
JWT_SECRET=your-secret-key

# SSL配置
SSL_CERT_PATH=/etc/ssl/certs/athena.multimodal.ai.crt
SSL_KEY_PATH=/etc/ssl/private/athena.multimodal.ai.key

# 监控配置
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/athena/app.log

# 文件存储配置
UPLOAD_PATH=/data/athena/uploads
PROCESSED_PATH=/data/athena/processed

# API配置
API_RATE_LIMIT=1000
API_MAX_FILE_SIZE=200MB

# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@athena.multimodal.ai
SMTP_PASSWORD=your-smtp-password
EOF

    log_success "配置文件模板创建完成"
}

# 设置服务器SSH密钥
setup_ssh_keys() {
    log_info "设置SSH密钥..."

    # 生成SSH密钥对
    if [ ! -f "$HOME/.ssh/athena_deploy" ]; then
        ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/athena_deploy" -N "" -C "athena-deploy@$(hostname)"
        log_success "SSH密钥对已生成"
    else
        log_info "SSH密钥对已存在"
    fi

    # 显示公钥
    log_info "请将以下公钥添加到部署服务器的 ~/.ssh/authorized_keys:"
    echo ""
    cat "$HOME/.ssh/athena_deploy.pub"
    echo ""

    # 创建SSH配置
    cat >> "$HOME/.ssh/config" << EOF

# Athena部署服务器
Host athena-deploy
    HostName ${DEPLOY_SERVER}
    User ${DEPLOY_USER}
    Port 22
    IdentityFile ~/.ssh/athena_deploy
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF

    log_success "SSH配置完成"
}

# 主函数
main() {
    echo -e "${BLUE}🚀 Athena多模态文件系统CI/CD配置${NC}"
    echo "============================================"
    echo -e "${CYAN}开始时间: $(date)${NC}"
    echo ""

    # 检查依赖
    check_dependencies

    # 创建GitHub工作流
    create_github_workflows

    # 创建部署脚本
    create_deploy_scripts

    # 创建配置模板
    create_config_templates

    # 设置SSH密钥
    setup_ssh_keys

    echo ""
    echo -e "${GREEN}✅ CI/CD配置完成！${NC}"
    echo ""
    echo -e "${BLUE}📋 下一步操作:${NC}"
    echo -e "  1. 将SSH公钥添加到部署服务器"
    echo -e "  2. 在GitHub仓库设置中添加必要的secrets:"
    echo -e "     - DOCKER_USERNAME: Docker用户名"
    echo -e "     - DOCKER_PASSWORD: Docker密码"
    echo -e "     - DEPLOY_SERVER: 部署服务器地址"
    echo -e "     - DEPLOY_USER: 部署服务器用户"
    echo -e "     - DEPLOY_PATH: 部署路径"
    echo -e "     - SLACK_WEBHOOK_URL: Slack通知地址"
    echo -e "  3. 复制配置模板并填写实际值"
    echo -e "  4. 测试部署流程"
    echo ""
    echo -e "${BLUE}🔧 管理命令:${NC}"
    echo -e "  🚀 部署: ${YELLOW}bash scripts/deploy.sh${NC}"
    echo -e "  🔄 回滚: ${YELLOW}bash scripts/rollback.sh${NC}"
    echo -e "  ❤️ 健康检查: ${YELLOW}bash scripts/health_check.sh${NC}"
    echo ""
    echo -e "${PURPLE}✨ CI/CD系统已配置完成！${NC}"
}

# 执行主函数
main "$@"