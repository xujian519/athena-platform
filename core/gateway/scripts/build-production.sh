#!/bin/bash
# Athena API Gateway - 生产环境构建脚本
# 安全构建 + 扫描 + 推送
set -euo pipefail

# 配置变量
REGISTRY=${REGISTRY:-"your-registry.com"}
IMAGE_NAME="athena-gateway"
VERSION=${VERSION:-"v2.0.0"}
FULL_TAG="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
LATEST_TAG="${REGISTRY}/${IMAGE_NAME}:latest"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# 检查依赖
check_dependencies() {
    log "检查构建依赖..."
    
    command -v docker >/dev/null 2>&1 || error "Docker 未安装"
    command -v trivy >/dev/null 2>&1 || error "Trivy 安全扫描工具未安装"
    
    success "依赖检查完成"
}

# 清理旧镜像
cleanup_old_images() {
    log "清理旧镜像..."
    docker rmi -f "${FULL_TAG}" 2>/dev/null || true
    docker rmi -f "${LATEST_TAG}" 2>/dev/null || true
    docker system prune -f
    success "清理完成"
}

# 构建镜像
build_image() {
    log "开始构建生产镜像..."
    
    # 构建生产镜像
    docker build \
        --file deployments/production/Dockerfile \
        --tag "${FULL_TAG}" \
        --tag "${LATEST_TAG}" \
        --build-arg VERSION="${VERSION}" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        . || error "构建失败"
    
    success "镜像构建完成: ${FULL_TAG}"
}

# 安全扫描
security_scan() {
    log "执行安全扫描..."
    
    # 创建扫描报告目录
    mkdir -p security-reports
    
    # Trivy 漏洞扫描
    trivy image \
        --format json \
        --output "security-reports/trivy-report-${VERSION}.json" \
        --severity HIGH,CRITICAL \
        "${FULL_TAG}"
    
    # 检查关键漏洞
    critical_vulns=$(trivy image --quiet --format json "${FULL_TAG}" | jq '.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL") | .VulnerabilityID' | wc -l)
    high_vulns=$(trivy image --quiet --format json "${FULL_TAG}" | jq '.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH") | .VulnerabilityID' | wc -l)
    
    if [ "${critical_vulns}" -gt 0 ]; then
        error "发现 ${critical_vulns} 个关键漏洞，请修复后重新构建"
    fi
    
    if [ "${high_vulns}" -gt 5 ]; then
        warning "发现 ${high_vulns} 个高危漏洞，建议修复"
    fi
    
    success "安全扫描完成 (高危: ${high_vulns}, 关键: ${critical_vulns})"
}

# 镜像测试
test_image() {
    log "测试镜像功能..."
    
    # 启动测试容器
    container_id=$(docker run -d \
        --name "athena-test-${VERSION}" \
        -p 8081:8080 \
        -e GIN_MODE=release \
        -e LOG_LEVEL=info \
        "${FULL_TAG}")
    
    # 等待容器启动
    sleep 10
    
    # 健康检查
    if curl -f http://localhost:8081/health > /dev/null 2>&1; then
        success "健康检查通过"
    else
        error "健康检查失败"
    fi
    
    # 清理测试容器
    docker stop "${container_id}" && docker rm "${container_id}"
    
    success "镜像测试完成"
}

# 推送镜像
push_image() {
    log "推送镜像到仓库..."
    
    # 推送版本标签
    docker push "${FULL_TAG}" || error "版本标签推送失败"
    
    # 推送最新标签
    docker push "${LATEST_TAG}" || error "最新标签推送失败"
    
    success "镜像推送完成"
}

# 生成构建报告
generate_report() {
    log "生成构建报告..."
    
    cat > "build-reports/build-report-${VERSION}.md" << EOF
# Athena API Gateway - 生产构建报告

## 构建信息
- **镜像名称**: ${FULL_TAG}
- **构建时间**: $(date)
- **Git提交**: $(git rev-parse HEAD)
- **构建环境**: $(uname -a)

## 安全扫描结果
- **关键漏洞**: ${critical_vulns}
- **高危漏洞**: ${high_vulns}

## 镜像信息
\`\`\`bash
docker images | grep ${IMAGE_NAME}
\`\`\`

## 部署命令
\`\`\`bash
kubectl set image deployment/athena-gateway athena-gateway=${FULL_TAG} -n athena-gateway
\`\`\`
EOF
    
    success "构建报告已生成: build-reports/build-report-${VERSION}.md"
}

# 主函数
main() {
    log "Athena API Gateway - 生产环境构建开始"
    log "版本: ${VERSION}"
    log "镜像: ${FULL_TAG}"
    
    # 创建必要目录
    mkdir -p build-reports security-reports
    
    # 执行构建流程
    check_dependencies
    cleanup_old_images
    build_image
    security_scan
    test_image
    
    # 交互式推送确认
    read -p "是否推送到镜像仓库? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        push_image
    fi
    
    generate_report
    
    success "生产构建完成！"
    log "镜像标签: ${FULL_TAG}"
    log "安全报告: security-reports/trivy-report-${VERSION}.json"
    log "构建报告: build-reports/build-report-${VERSION}.md"
}

# 错误处理
trap 'error "构建过程中发生错误，退出码: $?"' ERR

# 执行主函数
main "$@"