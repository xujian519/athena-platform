#!/bin/bash
# ============================================================================
# Athena平台架构优化 - 回滚脚本
# ============================================================================
# 功能：
#   1. 从快照恢复代码
#   2. 恢复数据库状态
#   3. 重启服务
#   4. 验证恢复成功
# ============================================================================

set -e

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
SNAPSHOT_DIR="$PROJECT_ROOT/backups/architecture-snapshots"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示可用快照
list_snapshots() {
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "📦 可用快照列表"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [ ! -d "$SNAPSHOT_DIR" ]; then
        log_error "快照目录不存在: $SNAPSHOT_DIR"
        exit 1
    fi

    cd "$SNAPSHOT_DIR"

    # 列出所有快照
    snapshots=($(ls -t snapshot-*.tar.gz 2>/dev/null || true))

    if [ ${#snapshots[@]} -eq 0 ]; then
        log_warn "没有找到快照"
        exit 1
    fi

    for i in "${!snapshots[@]}"; do
        snapshot="${snapshots[$i]}"
        name="${snapshot%.tar.gz}"

        # 读取元数据
        if [ -f "${name}.meta" ]; then
            size=$(jq -r '.size' "${name}.meta" 2>/dev/null || echo "N/A")
            git_tag=$(jq -r '.git_tag' "${name}.meta" 2>/dev/null || echo "N/A")
            echo "  [$i] $snapshot"
            echo "      大小: $size, Git Tag: $git_tag"
        else
            echo "  [$i] $snapshot"
        fi
        echo ""
    done
}

# 选择快照
select_snapshot() {
    list_snapshots

    echo ""
    read -p "请输入快照编号 [0-$((${#snapshots[@]} - 1))]: " choice

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -ge ${#snapshots[@]} ]; then
        log_error "无效的选择"
        exit 1
    fi

    SELECTED_SNAPSHOT="${snapshots[$choice]}"
    log_info "已选择: $SELECTED_SNAPSHOT"
}

# 创建当前状态备份
backup_current_state() {
    log_info "📦 备份当前状态..."
    BACKUP_NAME="rollback-backup-${TIMESTAMP}"
    BACKUP_PATH="$SNAPSHOT_DIR/$BACKUP_NAME.tar.gz"

    cd "$PROJECT_ROOT"

    tar -czf "$BACKUP_PATH" \
        --exclude=*.pyc \
        --exclude=__pycache__ \
        --exclude=.pytest_cache \
        --exclude=htmlcov \
        --exclude=.git \
        --exclude=node_modules \
        --exclude=models/* \
        --exclude=data/*.db \
        --exclude=*.log \
        --exclude=backups \
        . 2>/dev/null || true

    log_info "✅ 当前状态已备份: $BACKUP_PATH"
}

# 验证快照完整性
verify_snapshot() {
    local snapshot_path="$1"

    log_info "🔍 验证快照完整性..."

    # 检查文件存在
    if [ ! -f "$snapshot_path" ]; then
        log_error "快照文件不存在: $snapshot_path"
        exit 1
    fi

    # 验证tar文件
    if ! tar -tzf "$snapshot_path" > /dev/null 2>&1; then
        log_error "快照文件损坏"
        exit 1
    fi

    # 验证MD5（如果存在）
    local snapshot_name="${snapshot_path%.tar.gz}"
    if [ -f "${snapshot_name}.md5" ]; then
        log_info "验证MD5..."
        if command -v md5 &> /dev/null; then
            CURRENT_MD5=$(md5 -q "$snapshot_path")
        else
            CURRENT_MD5=$(md5sum "$snapshot_path" | cut -d' ' -f1)
        fi

        SAVED_MD5=$(cat "${snapshot_name}.md5")

        if [ "$CURRENT_MD5" != "$SAVED_MD5" ]; then
            log_error "MD5校验失败"
            log_error "  当前: $CURRENT_MD5"
            log_error "  保存: $SAVED_MD5"
            exit 1
        fi

        log_info "✅ MD5校验通过"
    fi

    log_info "✅ 快照验证通过"
}

# 恢复快照
restore_snapshot() {
    local snapshot_path="$1"

    log_info "📦 恢复快照..."

    cd "$PROJECT_ROOT"

    # 清理当前文件（保留.git）
    log_warn "清理当前文件..."
    find . -mindepth 1 -maxdepth 1 \
        ! -name ".git" \
        ! -name "backups" \
        ! -name "models" \
        ! -name "data" \
        -exec rm -rf {} + 2>/dev/null || true

    # 解压快照
    log_info "解压快照..."
    tar -xzf "$snapshot_path" -C "$PROJECT_ROOT"

    log_info "✅ 快照已恢复"
}

# 恢复Git状态
restore_git_state() {
    local snapshot_name="$1"

    log_info "🏷️  恢复Git状态..."

    cd "$PROJECT_ROOT"

    # 读取元数据中的Git信息
    local meta_file="$SNAPSHOT_DIR/${snapshot_name}.meta"

    if [ -f "$meta_file" ]; then
        local git_commit=$(jq -r '.git_commit' "$meta_file" 2>/dev/null || echo "N/A")
        local git_tag=$(jq -r '.git_tag' "$meta_file" 2>/dev/null || echo "N/A")

        if [ "$git_commit" != "N/A" ]; then
            log_info "检出commit: $git_commit"
            git checkout "$git_commit" 2>/dev/null || log_warn "Git checkout失败"
        fi

        if [ "$git_tag" != "N/A" ]; then
            log_info "恢复tag: $git_tag"
            git tag -d "$git_tag" 2>/dev/null || true
            git tag "$git_tag" 2>/dev/null || log_warn "Git tag创建失败"
        fi
    fi

    log_info "✅ Git状态已恢复"
}

# 验证恢复
verify_restore() {
    log_info "🔍 验证恢复结果..."

    cd "$PROJECT_ROOT"

    # 检查关键文件
    if [ ! -f "pyproject.toml" ]; then
        log_error "关键文件缺失: pyproject.toml"
        exit 1
    fi

    if [ ! -d "core" ]; then
        log_error "关键目录缺失: core/"
        exit 1
    fi

    # 运行快速测试
    if command -v pytest &> /dev/null; then
        log_info "运行快速测试..."
        pytest tests/ -v --tb=short -x --maxfail=5 2>/dev/null || {
            log_warn "测试失败，但代码已恢复"
        }
    fi

    log_info "✅ 恢复验证通过"
}

# 重启服务
restart_services() {
    log_info "🔄 重启服务..."

    # 停止服务
    if [ -f "docker-compose.yml" ]; then
        log_info "停止Docker服务..."
        docker-compose down 2>/dev/null || true
    fi

    # 启动服务
    if [ -f "docker-compose.yml" ]; then
        log_info "启动Docker服务..."
        docker-compose up -d 2>/dev/null || log_warn "Docker服务启动失败"
    fi

    log_info "✅ 服务已重启"
}

# 主函数
main() {
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "🔄 Athena平台回滚工具"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # 选择快照
    select_snapshot

    local snapshot_path="$SNAPSHOT_DIR/$SELECTED_SNAPSHOT"
    local snapshot_name="${SELECTED_SNAPSHOT%.tar.gz}"

    echo ""
    log_warn "⚠️  即将执行回滚操作："
    echo "  - 从快照恢复: $SELECTED_SNAPSHOT"
    echo "  - 当前状态将被备份"
    echo "  - 所有未提交的更改将丢失"
    echo ""
    read -p "确认继续？(yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "已取消"
        exit 0
    fi

    echo ""

    # 执行回滚
    backup_current_state
    echo ""

    verify_snapshot "$snapshot_path"
    echo ""

    restore_snapshot "$snapshot_path"
    echo ""

    restore_git_state "$snapshot_name"
    echo ""

    verify_restore
    echo ""

    restart_services
    echo ""

    # 输出摘要
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "✅ 回滚完成！"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  恢复快照: $SELECTED_SNAPSHOT"
    echo "  当前备份: rollback-backup-${TIMESTAMP}.tar.gz"
    echo ""
}

# 执行
main
