#!/bin/bash
# Athena紧急回滚脚本
# 功能：一键回滚到迁移前的安全状态
# 使用：./emergency_rollback.sh [--quick|--full|--data-only]

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="/backup"
LOG_FILE="/migration/rollback_$(date +%Y%m%d_%H%M%S).log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $*" | tee -a "$LOG_FILE"
}

# 横幅
banner() {
    echo ""
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║         🚨 Athena紧急回滚系统 🚨                     ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 确认函数
confirm() {
    local message="$1"
    local response

    while true; do
        read -p "$(echo -e ${YELLOW}⚠️  ${message} (yes/no): ${NC})" response
        case "$response" in
            [Yy][Ee][Ss]|[Yy])
                return 0
                ;;
            [Nn][Oo]|[Nn])
                return 1
                ;;
            *)
                echo "请输入 yes 或 no"
                ;;
        esac
    done
}

# 解析参数
ROLLBACK_TYPE="quick"
case "${1:-}" in
    --quick)
        ROLLBACK_TYPE="quick"
        ;;
    --full)
        ROLLBACK_TYPE="full"
        ;;
    --data-only)
        ROLLBACK_TYPE="data"
        ;;
esac

# 开始回滚流程
banner

log "🚨 启动紧急回滚流程"
log "回滚类型: ${ROLLBACK_TYPE}"
log "========================================"

# 步骤1: 最终确认
if ! confirm "确定要执行紧急回滚吗？此操作将影响系统运行。"; then
    log "❌ 回滚已取消"
    exit 0
fi

# 步骤2: 记录当前系统状态
log "📊 记录当前系统状态..."
info "当前时间: $(date)"
info "当前Git分支: $(git branch --show-current 2>/dev/null || echo 'N/A')"
info "当前流量比例: ${GATEWAY_TRAFFIC_RATIO:-0.0}"

# 步骤3: 流量回滚 (最紧急)
log "🔄 [1/4] 执行流量回滚..."
export GATEWAY_TRAFFIC_RATIO=0.0

# 停止Gateway服务
if docker ps | grep -q "athena-gateway"; then
    info "停止Gateway服务..."
    docker stop athena-gateway 2>/dev/null || true
    log "✅ Gateway服务已停止"
else
    info "Gateway服务未运行，跳过"
fi

# 重启现有系统服务
info "重启现有系统服务..."
docker-compose restart web 2>/dev/null || warn "Web服务重启失败"
log "✅ 流量已切换回现有系统"

# 步骤4: Git代码回滚 (如果需要)
if [ "$ROLLBACK_TYPE" = "full" ]; then
    log "🔄 [2/4] 执行代码回滚..."

    # 查找最新的迁移前标签
    LATEST_TAG=$(git tag -l "pre-migration-baseline-*" | sort -r | head -1)

    if [ -n "$LATEST_TAG" ]; then
        info "回滚到Git标签: $LATEST_TAG"

        # 创建回滚分支
        ROLLBACK_BRANCH="rollback-$(date +%Y%m%d_%H%M%S)"
        git checkout -b "$ROLLBACK_BRANCH"
        git reset --hard "$LATEST_TAG"

        log "✅ 代码已回滚到 $LATEST_TAG"
        log "📍 当前分支: $ROLLBACK_BRANCH"

        # 询问是否强制推送
        if confirm "是否强制推送到远程？(⚠️  这将覆盖远程分支)"; then
            git push -f origin "$ROLLBACK_BRANCH"
            log "✅ 已推送到远程: $ROLLBACK_BRANCH"
        fi
    else
        warn "未找到迁移前基线标签，跳过代码回滚"
    fi
else
    info "跳过代码回滚 (使用 --full 参数执行完整回滚)"
fi

# 步骤5: 数据库回滚 (谨慎操作)
if [ "$ROLLBACK_TYPE" = "full" ] || [ "$ROLLBACK_TYPE" = "data" ]; then
    log "🔄 [3/4] 数据库回滚..."

    # 列出可用备份
    log "可用的PostgreSQL备份:"
    ls -lht "${BACKUP_ROOT}/postgres/"*.sql 2>/dev/null | head -5 || warn "未找到PostgreSQL备份"

    if confirm "是否需要回滚数据库？"; then
        # 选择备份文件
        LATEST_BACKUP=$(find "${BACKUP_ROOT}/postgres" -name "*.sql" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

        if [ -n "$LATEST_BACKUP" ] && [ -f "$LATEST_BACKUP" ]; then
            info "使用备份: $LATEST_BACKUP"

            # 创建紧急备份
            EMERGENCY_BACKUP="/backup/postgres/emergency_before_rollback_$(date +%Y%m%d_%H%M%S).sql"
            info "创建紧急备份: $EMERGENCY_BACKUP"
            pg_dump -h localhost -U postgres -d athena_db -f "$EMERGENCY_BACKUP" 2>/dev/null || warn "紧急备份创建失败"

            # 确认最终回滚
            if confirm "⚠️  最后确认：回滚数据库将覆盖当前所有数据！"; then
                # 停止所有服务
                docker-compose stop web gateway 2>/dev/null || true

                # 重建数据库
                info "重建数据库..."
                dropdb -U postgres athena_db 2>/dev/null || true
                createdb -U postgres athena_db

                # 恢复备份
                info "恢复备份数据..."
                psql -U postgres -d athena_db -f "$LATEST_BACKUP" > /dev/null 2>&1

                log "✅ 数据库回滚完成"
            else
                warn "数据库回滚已取消"
            fi
        else
            error "未找到有效的备份文件"
        fi
    else
        info "跳过数据库回滚"
    fi
else
    info "跳过数据库回滚 (使用 --data-only 或 --full 参数执行数据库回滚)"
fi

# 步骤6: 验证回滚结果
log "🔍 [4/4] 验证回滚结果..."

# 检查服务状态
if docker ps | grep -q "athena-web"; then
    log "✅ Web服务运行正常"
else
    error "❌ Web服务未运行"
fi

# 检查数据库连接
if pg_isready -h localhost -p 5432 -U postgres > /dev/null 2>&1; then
    log "✅ 数据库连接正常"
else
    error "❌ 数据库连接失败"
fi

# 生成回滚报告
cat > "/migration/rollback_report_$(date +%Y%m%d_%H%M%S).txt" <<EOF
Athena紧急回滚报告
==================

回滚时间: $(date)
回滚类型: ${ROLLBACK_TYPE}
执行用户: $(whoami)
当前目录: $(pwd)

回滚操作:
- 流量切换: ✅
- Gateway停止: ✅
- 代码回滚: $([ "$ROLLBACK_TYPE" = "full" ] && echo "✅" || echo "跳过")
- 数据库回滚: $([ "$ROLLBACK_TYPE" = "full" ] || [ "$ROLLBACK_TYPE" = "data" ] && echo "✅" || echo "跳过")

系统状态:
$(docker ps --format "table {{.Names}}\t{{.Status}}")

建议后续步骤:
1. 检查所有核心功能是否正常
2. 验证数据完整性
3. 分析回滚原因
4. 制定修复计划
5. 准备重新迁移

EOF

log "========================================"
log "✅ 紧急回滚完成！"
log "回滚日志: $LOG_FILE"
log ""
log "📋 后续步骤:"
log "1. 检查系统功能: ./scripts/health/check_system.sh"
log "2. 验证数据完整性: ./scripts/backup/verify_data.sh"
log "3. 查看回滚报告: cat /migration/rollback_report_*.txt"
log ""
warn "⚠️  请记录回滚原因，并通知相关人员！"

# 发送通知 (如果配置了)
if [ -n "${ALERT_WEBHOOK:-}" ]; then
    curl -X POST "$ALERT_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "{\"text\":\"🚨 Athena紧急回滚已执行 - $(date)\"}" \
        2>/dev/null || true
fi

exit 0
