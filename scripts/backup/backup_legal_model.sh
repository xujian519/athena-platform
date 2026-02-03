#!/bin/bash
# 法律世界模型备份脚本
# 功能：备份法律世界模型，支持增量备份和Git版本控制

set -euo pipefail

# 配置
SOURCE_DIR="/Users/xujian/Athena工作平台/core/legal_world_model"
BACKUP_ROOT="/backup/legal_world_model"
GIT_REPO="/backup/legal_world_model_git"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 日志函数
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "开始备份法律世界模型..."

# 检查源目录
if [ ! -d "${SOURCE_DIR}" ]; then
    log "错误: 源目录不存在: ${SOURCE_DIR}"
    exit 1
fi

# 1. 增量备份
log "执行增量备份..."
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"

# 使用rsync进行增量备份，只复制修改过的文件
if rsync -av --progress \
    --backup-dir="${BACKUP_ROOT}/deleted/${TIMESTAMP}" \
    --delete \
    --checksum \
    "${SOURCE_DIR}/" \
    "${BACKUP_DIR}/" > /tmp/legal_model_backup.log 2>&1; then
    log "✅ 增量备份完成: ${BACKUP_DIR}"
else
    log "❌ 增量备份失败"
    cat /tmp/legal_model_backup.log
    exit 1
fi

# 2. 计算校验和
log "计算文件校验和..."
CHECKSUM_FILE="${BACKUP_DIR}/checksums.txt"
cd "${BACKUP_DIR}"
find . -type f -exec shasum -a 256 {} \; > "${CHECKSUM_FILE}"
log "✅ 校验和计算完成"

# 3. Git版本控制备份
log "执行Git备份..."

# 初始化Git仓库（如果不存在）
if [ ! -d "${GIT_REPO}/.git" ]; then
    log "初始化Git仓库..."
    mkdir -p "${GIT_REPO}"
    cd "${GIT_REPO}"
    git init
    git config user.name "Athena Backup System"
    git config user.email "backup@athena.local"
else
    cd "${GIT_REPO}"
fi

# 复制文件到Git仓库
log "同步文件到Git仓库..."
rsync -av --delete "${SOURCE_DIR}/" "${GIT_REPO}/" > /dev/null 2>&1

# Git提交
if [ -n "$(git status --porcelain)" ]; then
    log "检测到变化，创建Git提交..."
    git add -A
    git commit -m "Auto backup: ${TIMESTAMP}

Backup location: ${BACKUP_DIR}
Checksum file: ${CHECKSUM_FILE}"
    git tag -a "backup-${TIMESTAMP}" -m "Backup tag for ${TIMESTAMP}"
    log "✅ Git提交完成: backup-${TIMESTAMP}"
else
    log "未检测到变化，跳过Git提交"
fi

# 4. 统计信息
FILE_COUNT=$(find "${BACKUP_DIR}" -type f | wc -l)
DIR_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)

log "备份统计:"
log "  文件数量: ${FILE_COUNT}"
log "  目录大小: ${DIR_SIZE}"
log "  备份位置: ${BACKUP_DIR}"
log "  Git标签: backup-${TIMESTAMP}"

log "✅ 法律世界模型备份完成"

exit 0
