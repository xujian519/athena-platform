#!/bin/bash

# Gateway日志轮转脚本

LOG_DIR="/Users/xujian/Athena工作平台/gateway-unified/logs"
MAX_SIZE=100M      # 单个日志文件最大100MB
MAX_AGE=30         # 保留30天
MAX_FILES=10       # 最多保留10个归档文件

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 轮转函数
rotate_log() {
    local log_file="$1"
    local log_name=$(basename "$log_file")

    # 检查文件是否存在
    if [ ! -f "$log_file" ]; then
        return 0
    fi

    # 获取文件大小
    local size=$(du -b "$log_file" 2>/dev/null | cut -f1)
    local size_mb=$((size / 1024 / 1024))

    # 检查是否需要轮转
    if [ $size_mb -lt 100 ]; then
        return 0
    fi

    log_info "轮转日志: $log_name (${size_mb}MB)"

    # 移动现有归档
    for i in $(seq 9 -1 1); do
        if [ -f "${log_file}.${i}" ]; then
            if [ $i -eq 9 ]; then
                rm -f "${log_file}.${i}"
            else
                mv "${log_file}.${i}" "${log_file}.$((i+1))"
            fi
        fi
    done

    # 轮转当前日志
    mv "$log_file" "${log_file}.1"

    # 压缩归档（除了最新的）
    for i in $(seq 2 10); do
        if [ -f "${log_file}.${i}" ]; then
            gzip -f "${log_file}.${i}" 2>/dev/null
        fi
    done

    log_info "✅ 日志轮转完成: $log_name"
}

# 清理旧日志
cleanup_old_logs() {
    log_info "清理${MAX_AGE}天前的旧日志..."

    # 删除过期日志
    find "$LOG_DIR" -name "*.log.*.gz" -type f -mtime +$MAX_AGE -delete

    # 删除过多的归档
    ls -t "$LOG_DIR"/*.log.*.gz 2>/dev/null | tail -n +$((MAX_FILES + 1)) | xargs rm -f

    log_info "✅ 旧日志清理完成"
}

# 显示磁盘使用
show_disk_usage() {
    local usage=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1)
    log_info "日志目录大小: $usage"
}

# 主程序
log_info "开始日志轮转..."
log_info "================================"

# 轮转各个日志文件
rotate_log "$LOG_DIR/gateway-stdout.log"
rotate_log "$LOG_DIR/gateway-error.log"
rotate_log "$LOG_DIR/gateway.log"

# 清理旧日志
cleanup_old_logs

# 显示磁盘使用
show_disk_usage

log_info "================================"
log_info "✅ 日志轮转完成！"
