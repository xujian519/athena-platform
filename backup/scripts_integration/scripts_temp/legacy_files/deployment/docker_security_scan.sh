#!/bin/bash

# Athena AI平台 - Docker安全扫描脚本
# 生成时间: 2025-12-11
# 功能: 容器安全扫描、漏洞检测、合规检查

set -euo pipefail

# ================================
# 配置变量
# ================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
IMAGE_NAME="${1:-athena-app:latest}"
SCAN_TYPE="${2:-all}"  # all, vulnerabilities, compliance, secrets
OUTPUT_DIR="$PROJECT_ROOT/security_reports"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# ================================
# 初始化
# ================================
init_scan() {
    log_info "初始化安全扫描..."

    # 创建输出目录
    mkdir -p "$OUTPUT_DIR"

    # 检查Docker是否运行
    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行"
        exit 1
    fi

    # 检查镜像是否存在
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^$IMAGE_NAME$"; then
        log_error "Docker镜像不存在: $IMAGE_NAME"
        exit 1
    fi

    # 检查扫描工具
    check_scan_tools

    log_success "安全扫描初始化完成"
}

# ================================
# 检查扫描工具
# ================================
check_scan_tools() {
    log_info "检查安全扫描工具..."

    local tools_available=true

    # 检查Trivy
    if ! command -v trivy &> /dev/null; then
        log_warning "Trivy未安装，正在安装..."
        install_trivy
    fi

    # 检查Docker Bench
    if ! command -v docker-bench-security &> /dev/null; then
        log_warning "Docker Bench Security未安装，正在安装..."
        install_docker_bench
    fi

    # 检查hadolint
    if ! command -v hadolint &> /dev/null; then
        log_warning "Hadolint未安装，正在安装..."
        install_hadolint
    fi

    log_success "扫描工具检查完成"
}

# ================================
# 安装扫描工具
# ================================
install_trivy() {
    log_info "安装Trivy漏洞扫描器..."

    # 安装Trivy
    sudo apt-get update
    sudo apt-get install wget apt-transport-https gnupg lsb-release
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
    sudo apt-get update
    sudo apt-get install trivy

    log_success "Trivy安装完成"
}

install_docker_bench() {
    log_info "安装Docker Bench Security..."

    if [[ ! -d "$HOME/docker-bench-security" ]]; then
        git clone https://github.com/docker/docker-bench-security.git "$HOME/docker-bench-security"
    fi

    sudo chmod +x "$HOME/docker-bench-security/docker-bench-security.sh"

    log_success "Docker Bench Security安装完成"
}

install_hadolint() {
    log_info "安装Hadolint Dockerfile检查器..."

    # 安装Hadolint
    sudo wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
    sudo chmod +x /usr/local/bin/hadolint

    log_success "Hadolint安装完成"
}

# ================================
# 漏洞扫描
# ================================
vulnerability_scan() {
    log_info "执行漏洞扫描..."

    local output_file="$OUTPUT_DIR/vulnerability_scan_$(date +%Y%m%d_%H%M%S).json"
    local html_file="$OUTPUT_DIR/vulnerability_scan_$(date +%Y%m%d_%H%M%S).html"

    log_info "扫描镜像: $IMAGE_NAME"

    # 扫描镜像漏洞
    trivy image --format json --output "$output_file" "$IMAGE_NAME" || {
        log_error "漏洞扫描失败"
        return 1
    }

    # 生成HTML报告
    trivy image --format template --template "@contrib/html.tpl" --output "$html_file" "$IMAGE_NAME" || {
        log_warning "HTML报告生成失败"
    }

    # 分析结果
    analyze_vulnerability_results "$output_file"

    log_success "漏洞扫描完成，报告保存至: $output_file"
}

# ================================
# 分析漏洞扫描结果
# ================================
analyze_vulnerability_results() {
    local json_file="$1"

    log_info "分析漏洞扫描结果..."

    # 提取漏洞统计
    local critical_count=$(jq -r '.Results[]? | .Vulnerabilities[]? | select(.Severity == "CRITICAL") | .VulnerabilityID' "$json_file" | wc -l || echo "0")
    local high_count=$(jq -r '.Results[]? | .Vulnerabilities[]? | select(.Severity == "HIGH") | .VulnerabilityID' "$json_file" | wc -l || echo "0")
    local medium_count=$(jq -r '.Results[]? | .Vulnerabilities[]? | select(.Severity == "MEDIUM") | .VulnerabilityID' "$json_file" | wc -l || echo "0")
    local low_count=$(jq -r '.Results[]? | .Vulnerabilities[]? | select(.Severity == "LOW") | .VulnerabilityID' "$json_file" | wc -l || echo "0")

    echo
    log_info "=== 漏洞扫描统计 ==="
    echo "严重 (CRITICAL): $critical_count"
    echo "高危 (HIGH): $high_count"
    echo "中危 (MEDIUM): $medium_count"
    echo "低危 (LOW): $low_count"

    # 检查是否存在严重漏洞
    if [[ $critical_count -gt 0 ]]; then
        log_error "发现 $critical_count 个严重漏洞！"
        echo "严重漏洞列表:"
        jq -r '.Results[]? | .Vulnerabilities[]? | select(.Severity == "CRITICAL") | "- \(.VulnerabilityID): \(.Title)"' "$json_file"

        log_error "建议立即修复严重漏洞后再部署"
        return 1
    elif [[ $high_count -gt 5 ]]; then
        log_warning "发现 $high_count 个高危漏洞，建议修复后再部署"
    fi

    # 生成漏洞报告摘要
    local summary_file="$OUTPUT_DIR/vulnerability_summary.txt"
    cat > "$summary_file" << EOF
Athena AI平台 Docker镜像漏洞扫描报告
========================================
扫描时间: $(date '+%Y-%m-%d %H:%M:%S')
镜像名称: $IMAGE_NAME

漏洞统计:
- 严重 (CRITICAL): $critical_count
- 高危 (HIGH): $high_count
- 中危 (MEDIUM): $medium_count
- 低危 (LOW): $low_count

建议措施:
EOF

    if [[ $critical_count -gt 0 ]]; then
        echo "- 立即修复所有严重漏洞" >> "$summary_file"
    fi

    if [[ $high_count -gt 0 ]]; then
        echo "- 尽快修复高危漏洞" >> "$summary_file"
    fi

    if [[ $medium_count -gt 10 ]]; then
        echo "- 计划修复中危漏洞" >> "$summary_file"
    fi

    log_success "漏洞分析完成"
}

# ================================
# Dockerfile安全检查
# ================================
dockerfile_security_check() {
    log_info "执行Dockerfile安全检查..."

    local dockerfile_path="${DOCKERFILE_PATH:-$PROJECT_ROOT/deployment/docker/Dockerfile.optimized}"
    local output_file="$OUTPUT_DIR/dockerfile_security_$(date +%Y%m%d_%H%M%S).txt"

    if [[ ! -f "$dockerfile_path" ]]; then
        log_warning "Dockerfile不存在: $dockerfile_path"
        return 1
    fi

    # 执行Hadolint检查
    hadolint "$dockerfile_path" > "$output_file" 2>&1 || {
        log_warning "Dockerfile安全检查发现问题"
    }

    # 分析检查结果
    analyze_dockerfile_results "$output_file"

    log_success "Dockerfile安全检查完成，报告保存至: $output_file"
}

# ================================
# 分析Dockerfile检查结果
# ================================
analyze_dockerfile_results() {
    local output_file="$1"

    log_info "分析Dockerfile安全检查结果..."

    if [[ ! -s "$output_file" ]]; then
        log_success "✓ Dockerfile安全检查通过，未发现问题"
        return 0
    fi

    local issue_count=$(wc -l < "$output_file")

    echo
    log_info "=== Dockerfile安全检查 ==="
    echo "发现 $issue_count 个问题:"

    # 显示关键安全问题
    grep -i "root\|password\|secret\|token" "$output_file" || true
    grep -i "latest\|no-cache\|verify" "$output_file" || true

    if [[ $issue_count -gt 10 ]]; then
        log_warning "Dockerfile存在较多安全问题 ($issue_count 个)，建议优化"
    else
        log_info "Dockerfile安全性良好 ($issue_count 个小问题)"
    fi
}

# ================================
# Docker安全基准检查
# ================================
docker_security_benchmark() {
    log_info "执行Docker安全基准检查..."

    local output_dir="$OUTPUT_DIR/docker_bench_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$output_dir"

    # 运行Docker Bench Security
    if [[ -x "$HOME/docker-bench-security/docker-bench-security.sh" ]]; then
        sudo "$HOME/docker-bench-security/docker-bench-security.sh" -f json -o "$output_dir" || {
            log_warning "Docker安全基准检查执行失败"
        }

        analyze_docker_bench_results "$output_dir"
    else
        log_error "Docker Bench Security未正确安装"
        return 1
    fi

    log_success "Docker安全基准检查完成，报告保存至: $output_dir"
}

# ================================
# 分析Docker基准检查结果
# ================================
analyze_docker_bench_results() {
    local output_dir="$1"

    log_info "分析Docker安全基准检查结果..."

    # 查找JSON报告文件
    local json_file=$(find "$output_dir" -name "*.json" -type f | head -1)

    if [[ -n "$json_file" && -f "$json_file" ]]; then
        # 统计结果
        local pass_count=$(jq -r '.tests[]? | select(.result == "pass") | .desc' "$json_file" | wc -l || echo "0")
        local fail_count=$(jq -r '.tests[]? | select(.result == "fail") | .desc' "$json_file" | wc -l || echo "0")
        local warn_count=$(jq -r '.tests[]? | select(.result == "warn") | .desc' "$json_file" | wc -l || echo "0")
        local info_count=$(jq -r '.tests[]? | select(.result == "info") | .desc' "$json_file" | wc -l || echo "0")

        echo
        log_info "=== Docker安全基准统计 ==="
        echo "通过 (PASS): $pass_count"
        echo "失败 (FAIL): $fail_count"
        echo "警告 (WARN): $warn_count"
        echo "信息 (INFO): $info_count"

        # 显示失败项
        if [[ $fail_count -gt 0 ]]; then
            echo
            log_warning "失败的检查项目:"
            jq -r '.tests[]? | select(.result == "fail") | "- \(.desc)"' "$json_file" | head -10
        fi

        # 安全评分
        local total=$((pass_count + fail_count + warn_count + info_count))
        local score=$((pass_count * 100 / total))

        echo
        if [[ $score -ge 80 ]]; then
            log_success "✓ Docker安全评分: $score/100 (优秀)"
        elif [[ $score -ge 60 ]]; then
            log_warning "⚠ Docker安全评分: $score/100 (良好)"
        else
            log_error "✗ Docker安全评分: $score/100 (需要改进)"
        fi
    else
        log_warning "未找到Docker基准检查结果文件"
    fi
}

# ================================
# 敏感信息扫描
# ================================
secrets_scan() {
    log_info "执行敏感信息扫描..."

    local output_file="$OUTPUT_DIR/secrets_scan_$(date +%Y%m%d_%H%M%S).txt"

    # 扫描镜像中的敏感信息
    log_info "扫描镜像中的敏感信息..."

    # 创建临时容器
    local container_id=$(docker create "$IMAGE_NAME" /bin/true)

    # 扫描常见敏感信息模式
    echo "Athena AI平台 敏感信息扫描报告" > "$output_file"
    echo "扫描时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$output_file"
    echo "镜像名称: $IMAGE_NAME" >> "$output_file"
    echo "========================================" >> "$output_file"

    # 扫描环境变量
    echo "=== 环境变量检查 ===" >> "$output_file"
    docker inspect "$container_id" | jq -r '.[0].Config.Env[]' | grep -i -E "(password|secret|token|key|auth)" || echo "未发现敏感环境变量" >> "$output_file"

    # 扫描文件系统
    echo "=== 文件系统扫描 ===" >> "$output_file"
    docker run --rm "$IMAGE_NAME" find /app -type f \( -name "*.conf" -o -name "*.config" -o -name "*.json" -o -name "*.yml" -o -name "*.yaml" \) -exec grep -l -i -E "(password|secret|token|key|auth)" {} \; 2>/dev/null || echo "未发现敏感配置文件" >> "$output_file"

    # 清理临时容器
    docker rm "$container_id"

    analyze_secrets_results "$output_file"

    log_success "敏感信息扫描完成，报告保存至: $output_file"
}

# ================================
# 分析敏感信息扫描结果
# ================================
analyze_secrets_results() {
    local output_file="$1"

    log_info "分析敏感信息扫描结果..."

    # 检查是否发现敏感信息
    if grep -q -i -E "(password|secret|token|key|auth)" "$output_file" | grep -v "未发现"; then
        log_warning "发现潜在敏感信息，请检查报告文件"

        echo
        log_warning "发现的敏感信息类型:"
        grep -i -E "(password|secret|token|key|auth)" "$output_file" | grep -v "未发现" | head -5
    else
        log_success "✓ 未发现敏感信息泄露"
    fi
}

# ================================
# 生成综合报告
# ================================
generate_summary_report() {
    log_info "生成安全扫描综合报告..."

    local summary_file="$OUTPUT_DIR/security_summary_$(date +%Y%m%d_%H%M%S).md"

    cat > "$summary_file" << EOF
# Athena AI平台 安全扫描综合报告

**扫描时间**: $(date '+%Y-%m-%d %H:%M:%S')
**镜像名称**: $IMAGE_NAME
**扫描类型**: $SCAN_TYPE

## 执行的扫描项目

EOF

    # 添加各扫描项目的链接
    for report_file in "$OUTPUT_DIR"/*_$(date +%Y%m%d)*; do
        if [[ -f "$report_file" ]]; then
            local filename=$(basename "$report_file")
            echo "- [$filename]($filename)" >> "$summary_file"
        fi
    done

    cat >> "$summary_file" << EOF

## 安全建议

### 1. 漏洞修复
- 定期更新基础镜像
- 及时修复高危漏洞
- 使用最小权限原则

### 2. 配置安全
- 禁用不必要的服务
- 使用非root用户运行
- 配置资源限制

### 3. 监控和审计
- 启用容器日志记录
- 配置安全监控告警
- 定期执行安全扫描

### 4. 合规要求
- 遵循CIS Docker基准
- 满足行业安全标准
- 定期安全评估

## 扫描工具版本信息

EOF

    # 添加工具版本信息
    trivy --version 2>/dev/null | head -1 >> "$summary_file" || echo "Trivy: 未安装" >> "$summary_file"
    echo "Docker Bench Security: $(git -C "$HOME/docker-bench-security" describe --tags 2>/dev/null || echo "未知版本")" >> "$summary_file"
    hadolint --version 2>/dev/null >> "$summary_file" || echo "Hadolint: 未安装" >> "$summary_file"

    log_success "综合报告生成完成: $summary_file"
}

# ================================
# 主函数
# ================================
main() {
    echo "=============================================="
    echo "🔒 Athena AI平台 Docker安全扫描脚本"
    echo "镜像: $IMAGE_NAME"
    echo "扫描类型: $SCAN_TYPE"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="
    echo

    # 初始化扫描
    init_scan

    # 根据扫描类型执行相应扫描
    case "$SCAN_TYPE" in
        vulnerabilities)
            vulnerability_scan
            ;;
        dockerfile)
            dockerfile_security_check
            ;;
        benchmark)
            docker_security_benchmark
            ;;
        secrets)
            secrets_scan
            ;;
        all)
            vulnerability_scan
            dockerfile_security_check
            docker_security_benchmark
            secrets_scan
            ;;
        *)
            log_error "不支持的扫描类型: $SCAN_TYPE"
            echo "支持的扫描类型: all, vulnerabilities, dockerfile, benchmark, secrets"
            exit 1
            ;;
    esac

    # 生成综合报告
    generate_summary_report

    echo
    log_success "🎉 安全扫描完成！"
    echo
    echo "=== 报告文件位置 ==="
    echo "安全报告目录: $OUTPUT_DIR"
    echo "综合报告: $OUTPUT_DIR/security_summary_$(date +%Y%m%d_%H%M%S).md"
    echo
    echo "=== 查看报告 ==="
    echo "ls -la $OUTPUT_DIR/"
    echo
}

# ================================
# 信号处理
# ================================
trap 'log_error "安全扫描被中断"; exit 1' INT TERM

# ================================
# 执行主函数
# ================================
main "$@"