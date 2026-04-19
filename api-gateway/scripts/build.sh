#!/bin/bash

# Athena API Gateway 构建脚本
# 用途: 构建和打包API网关

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 默认配置
VERSION=${VERSION:-"1.0.0"}
BUILD_ENV=${BUILD_ENV:-"development"}
OUTPUT_DIR=${OUTPUT_DIR:-"./dist"}

# 显示帮助信息
show_help() {
    cat << EOF
Athena API Gateway 构建脚本

用法: $0 [选项]

选项:
    -v, --version VERSION    指定版本号 (默认: 1.0.0)
    -e, --env ENV         指定构建环境 (development|production, 默认: development)
    -o, --output DIR      指定输出目录 (默认: ./dist)
    -h, --help           显示帮助信息

示例:
    $0                                    # 使用默认配置构建
    $0 -v 1.2.0 -e production          # 构建生产版本 1.2.0
    $0 --version 2.0.0 --env production # 构建生产版本 2.0.0

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -e|--env)
                BUILD_ENV="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_DIR="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查环境
check_environment() {
    log_info "检查构建环境..."
    
    # 检查Go版本
    if ! command -v go &> /dev/null; then
        log_error "Go未安装或不在PATH中"
        exit 1
    fi
    
    GO_VERSION=$(go version | awk '{print $3}')
    log_info "Go版本: $GO_VERSION"
    
    # 检查Go模块
    if [[ ! -f "go.mod" ]]; then
        log_error "go.mod文件不存在"
        exit 1
    fi
    
    # 创建输出目录
    mkdir -p "$OUTPUT_DIR"
    
    log_success "环境检查完成"
}

# 清理旧的构建文件
clean_build() {
    log_info "清理旧的构建文件..."
    rm -rf "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
    log_success "清理完成"
}

# 下载依赖
download_deps() {
    log_info "下载Go模块依赖..."
    go mod download
    go mod tidy
    log_success "依赖下载完成"
}

# 运行测试
run_tests() {
    if [[ "$BUILD_ENV" == "production" ]]; then
        log_info "运行测试..."
        go test -v ./...
        log_success "测试通过"
    else
        log_warn "跳过测试（开发环境）"
    fi
}

# 构建二进制文件
build_binary() {
    log_info "构建二进制文件..."
    
    # 设置构建参数
    BUILD_TIME=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    
    # 构建标志
    LDFLAGS="-X main.Version=$VERSION -X main.BuildTime=$BUILD_TIME -X main.GitCommit=$GIT_COMMIT"
    
    # 根据环境设置构建参数
    if [[ "$BUILD_ENV" == "production" ]]; then
        CGO_ENABLED=0 GOOS=linux go build \
            -ldflags "$LDFLAGS" \
            -a -installsuffix cgo \
            -o "$OUTPUT_DIR/athena-gateway" \
            cmd/server/main.go
    else
        go build \
            -ldflags "$LDFLAGS" \
            -o "$OUTPUT_DIR/athena-gateway" \
            cmd/server/main.go
    fi
    
    log_success "二进制文件构建完成"
}

# 复制配置文件
copy_configs() {
    log_info "复制配置文件..."
    
    # 复制所有配置文件
    cp -r configs "$OUTPUT_DIR/"
    
    # 根据环境复制特定配置
    if [[ "$BUILD_ENV" == "production" ]]; then
        cp "$OUTPUT_DIR/configs/config.prod.yaml" "$OUTPUT_DIR/configs/config.yaml"
    else
        cp "$OUTPUT_DIR/configs/config.dev.yaml" "$OUTPUT_DIR/configs/config.yaml"
    fi
    
    log_success "配置文件复制完成"
}

# 创建发布包
create_package() {
    if [[ "$BUILD_ENV" == "production" ]]; then
        log_info "创建发布包..."
        
        PACKAGE_NAME="athena-gateway-${VERSION}-${BUILD_ENV}"
        PACKAGE_DIR="$OUTPUT_DIR/$PACKAGE_NAME"
        
        # 创建包目录
        mkdir -p "$PACKAGE_DIR"
        
        # 复制文件
        cp "$OUTPUT_DIR/athena-gateway" "$PACKAGE_DIR/"
        cp -r "$OUTPUT_DIR/configs" "$PACKAGE_DIR/"
        cp -r deployments "$PACKAGE_DIR/"
        cp README.md "$PACKAGE_DIR/" 2>/dev/null || true
        cp LICENSE "$PACKAGE_DIR/" 2>/dev/null || true
        
        # 创建启动脚本
        cat > "$PACKAGE_DIR/start.sh" << 'EOF'
#!/bin/bash
./athena-gateway --config configs/config.yaml
EOF
        chmod +x "$PACKAGE_DIR/start.sh"
        
        # 创建压缩包
        cd "$OUTPUT_DIR"
        tar -czf "${PACKAGE_NAME}.tar.gz" "$PACKAGE_NAME"
        rm -rf "$PACKAGE_NAME"
        
        log_success "发布包创建完成: ${PACKAGE_NAME}.tar.gz"
    fi
}

# 显示构建信息
show_build_info() {
    log_info "构建信息:"
    echo "  版本: $VERSION"
    echo "  环境: $BUILD_ENV"
    echo "  输出目录: $OUTPUT_DIR"
    echo "  构建时间: $BUILD_TIME"
    echo "  Git提交: $GIT_COMMIT"
    echo ""
}

# 主函数
main() {
    log_info "开始构建Athena API Gateway..."
    
    parse_args "$@"
    check_environment
    show_build_info
    clean_build
    download_deps
    run_tests
    build_binary
    copy_configs
    create_package
    
    log_success "构建完成!"
    
    if [[ "$BUILD_ENV" == "production" ]]; then
        log_info "发布包位置: $OUTPUT_DIR/athena-gateway-${VERSION}-${BUILD_ENV}.tar.gz"
    else
        log_info "二进制文件位置: $OUTPUT_DIR/athena-gateway"
    fi
}

# 运行主函数
main "$@"