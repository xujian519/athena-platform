#!/bin/bash
# 知识系统监控脚本

LOG_FILE="/Users/xujian/Athena工作平台/production/logs/monitor.log"
ALERT_FILE="/Users/xujian/Athena工作平台/production/logs/alerts.log"

mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [MONITOR] $*" | tee -a "$LOG_FILE"
}

check_qdrant() {
    if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
        log "Qdrant: OK"
    else
        log "ALERT: Qdrant 服务不可用"
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ALERT] Qdrant down!" >> "$ALERT_FILE"
    fi
}

check_nebula() {
    status=$(docker ps --filter "name=nebula" --format "{{.Status}}" | grep "Up" | wc -l | tr -d ' ')
    if [ "$status" -ge 3 ]; then
        log "NebulaGraph: OK ($status containers running)"
    else
        log "ALERT: NebulaGraph 容器状态异常 ($status containers)"
    fi
}

check_disk_space() {
    usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    log "Disk usage: $usage%"
    if [ "$usage" -gt 80 ]; then
        log "ALERT: 磁盘使用率超过 80%"
    fi
}

check_data_stats() {
    # 检查数据量
    python3 << 'PYEOF'
try:
    from qdrant_client import QdrantClient
    client = QdrantClient(url='http://localhost:6333')
    
    legal_count = 0
    patent_count = 0
    
    collections = client.get_collections()
    for col in collections.collections:
        if 'legal' in col.name.lower():
            info = client.get_collection(col.name)
            legal_count += info.points_count
        elif 'patent' in col.name.lower():
            info = client.get_collection(col.name)
            patent_count += info.points_count
    
    with open('/Users/xujian/Athena工作平台/production/logs/monitor.log', 'a') as f:
        f.write(f\"Data Stats: Legal={legal_count}, Patent={patent_count}\\n\")
except Exception as e:
    with open('/Users/xujian/Athena工作平台/production/logs/monitor.log', 'a') as f:
        f.write(f\"Data Stats check failed: {e}\\n\")
PYEOF
}

# 主监控循环
log "========== 监控启动 =========="

while true; do
    check_qdrant
    check_nebula
    check_disk_space
    check_data_stats
    sleep 300  # 每5分钟检查一次
done
