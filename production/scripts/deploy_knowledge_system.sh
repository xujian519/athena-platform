#!/bin/bash
# 生产环境部署脚本 - 法律与专利知识系统

set -e

echo "========================================================================"
echo "生产环境部署 - 法律与专利知识系统"
echo "========================================================================"
echo "部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ============================================================
# 1. 服务健康检查
# ============================================================
echo "1️⃣  服务健康检查"
echo "------------------------------------------------------------------------"

echo "Docker 容器状态:"
docker ps --filter "name=qdrant" --filter "name=nebula" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "服务连接测试:"
echo -n "  Qdrant (localhost:6333): "
if curl -s -f http://localhost:6333/health > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "❌ 不可用"
fi

echo -n "  NebulaGraph (localhost:9669): "
if docker exec athena_nebula_graph_min nebula-console --addr=127.0.0.1:9669 -u root -p nebula -e "SHOW HOSTS;" > /dev/null 2>&1; then
    echo "✅ 运行中"
else
    echo "⚠️  未验证"
fi

# ============================================================
# 2. 配置持久化存储
# ============================================================
echo ""
echo "2️⃣  配置持久化存储"
echo "------------------------------------------------------------------------"

BACKUP_BASE="/Users/xujian/Athena工作平台/production/backups"
mkdir -p "$BACKUP_BASE/qdrant"
mkdir -p "$BACKUP_BASE/nebula"
mkdir -p "$BACKUP_BASE/logs"

echo "  ✅ 备份目录: $BACKUP_BASE"

# ============================================================
# 3. 配置环境变量
# ============================================================
echo ""
echo "3️⃣  配置环境变量"
echo "------------------------------------------------------------------------"

ENV_FILE="/Users/xujian/Athena工作平台/production/.env.knowledge"

cat > "$ENV_FILE" << 'ENVEOF'
# 知识系统生产环境配置
# 生成时间: 2025-12-23

# Qdrant 配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_URL=http://localhost:6333
QDRANT_LEGAL_COLLECTION=legal_laws_enhanced
QDRANT_PATENT_COLLECTION=patent_rules_complete

# NebulaGraph 配置
NEBULA_HOST=127.0.0.1
NEBULA_PORT=9669
NEBULA_USER=root
NEBULA_PASSWORD=nebula
NEBULA_LEGAL_SPACE=legal_kg
NEBULA_PATENT_SPACE=patent_kg_extended

# 嵌入模型配置
EMBEDDING_MODEL_PATH=/Users/xujian/Athena工作平台/models/converted/bge-large-zh-v1.5
EMBEDDING_DIM=1024

# 监控配置
LOG_PATH=/Users/xujian/Athena工作平台/production/logs
ENVEOF

echo "  ✅ 环境配置: $ENV_FILE"

# ============================================================
# 4. 创建监控脚本
# ============================================================
echo ""
echo "4️⃣  创建监控脚本"
echo "------------------------------------------------------------------------"

MONITOR_SCRIPT="/Users/xujian/Athena工作平台/production/dev/scripts/monitor_knowledge.sh"

cat > "$MONITOR_SCRIPT" << 'MONITOREOF'
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
MONITOREOF

chmod +x "$MONITOR_SCRIPT"
echo "  ✅ 监控脚本: $MONITOR_SCRIPT"

# ============================================================
# 5. 创建备份脚本
# ============================================================
echo ""
echo "5️⃣  创建备份脚本"
echo "------------------------------------------------------------------------"

BACKUP_SCRIPT="/Users/xujian/Athena工作平台/production/dev/scripts/backup_knowledge.sh"

cat > "$BACKUP_SCRIPT" << 'BACKUPEOF'
#!/bin/bash
# 知识系统备份脚本

BACKUP_BASE="/Users/xujian/Athena工作平台/production/backups"
DATE=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="$BACKUP_BASE/backup.log"

mkdir -p "$BACKUP_BASE/qdrant"
mkdir -p "$BACKUP_BASE/nebula"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [BACKUP] $*" | tee -a "$LOG_FILE"
}

backup_qdrant() {
    log "备份 Qdrant 数据..."
    
    # 导出集合信息
    python3 << 'PYEOF'
from qdrant_client import QdrantClient
import json

client = QdrantClient(url='http://localhost:6333')
collections = client.get_collections()

stats = {}
for col in collections.collections:
    info = client.get_collection(col.name)
    stats[col.name] = {
        'points': info.points_count,
        'status': info.status
    }

with open('/Users/xujian/Athena工作平台/production/backups/qdrant/stats.json', 'w') as f:
    json.dump(stats, f, indent=2)
PYEOF

    log "Qdrant 备份完成: $BACKUP_BASE/qdrant/stats.json"
}

backup_nebula() {
    log "备份 NebulaGraph 数据..."
    
    python3 << 'PYEOF'
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config
import json

config = Config()
connection_pool = ConnectionPool()
connection_pool.init([('127.0.0.1', 9669)], config)
session = connection_pool.get_session('root', 'nebula')

spaces = ['legal_kg', 'patent_kg_extended']
stats = {}

for space in spaces:
    session.execute(f'USE {space};')
    
    # 获取标签统计
    result = session.execute('SHOW TAGS;')
    tags = []
    if result.is_succeeded():
        for row in result:
            tags.append(row.values()[0].as_string())
    
    tag_stats = {}
    for tag in tags:
        result = session.execute(f'MATCH (v:{tag}) RETURN count(v) AS count;')
        if result.is_succeeded():
            for row in result:
                tag_stats[tag] = row.values()[0].as_int()
    
    stats[space] = tag_stats

with open('/Users/xujian/Athena工作平台/production/backups/nebula/stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

session.release()
connection_pool.close()
PYEOF

    log "NebulaGraph 备份完成: $BACKUP_BASE/nebula/stats.json"
}

cleanup_old_backups() {
    log "清理 30 天前的备份日志..."
    find "$BACKUP_BASE/logs" -name "*.log" -mtime +30 -delete 2>/dev/null || true
}

# 主备份流程
log "========== 开始备份 =========="
backup_qdrant
backup_nebula
cleanup_old_backups
log "========== 备份完成 =========="
BACKUPEOF

chmod +x "$BACKUP_SCRIPT"
echo "  ✅ 备份脚本: $BACKUP_SCRIPT"

# ============================================================
# 6. 创建性能测试脚本
# ============================================================
echo ""
echo "6️⃣  创建性能测试脚本"
echo "------------------------------------------------------------------------"

PERF_SCRIPT="/Users/xujian/Athena工作平台/production/dev/scripts/knowledge_perf_test.py"

cat > "$PERF_SCRIPT" << 'PERFEOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识系统性能测试
"""

import time
import statistics
from qdrant_client import QdrantClient
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

def test_qdrant_perf():
    """测试 Qdrant 性能"""
    client = QdrantClient(url='http://localhost:6333')
    
    times = []
    for i in range(100):
        start = time.time()
        client.scroll(
            collection_name='legal_laws_enhanced',
            limit=10,
            with_payload=True,
            with_vectors=False
        )
        times.append((time.time() - start) * 1000)
    
    return {
        'avg': round(statistics.mean(times), 2),
        'p95': round(statistics.quantiles(times, n=20)[18], 2),
        'max': round(max(times), 2)
    }

def test_nebula_perf():
    """测试 NebulaGraph 性能"""
    config = Config()
    connection_pool = ConnectionPool()
    connection_pool.init([('127.0.0.1', 9669)], config)
    session = connection_pool.get_session('root', 'nebula')
    session.execute('USE legal_kg;')
    
    times = []
    for i in range(100):
        start = time.time()
        session.execute('MATCH (l:Law) RETURN count(l) AS count;')
        times.append((time.time() - start) * 1000)
    
    session.release()
    connection_pool.close()
    
    return {
        'avg': round(statistics.mean(times), 2),
        'p95': round(statistics.quantiles(times, n=20)[18], 2),
        'max': round(max(times), 2)
    }

if __name__ == '__main__':
    print('=' * 60)
    print('知识系统性能测试')
    print('=' * 60)
    
    print('\nQdrant 向量搜索性能 (100次):')
    qdrant = test_qdrant_perf()
    for k, v in qdrant.items():
        print(f'  {k}: {v}ms')
    
    print('\nNebulaGraph 图查询性能 (100次):')
    nebula = test_nebula_perf()
    for k, v in nebula.items():
        print(f'  {k}: {v}ms')
    
    print('\n性能评估:')
    if qdrant['p95'] < 100 and nebula['p95'] < 100:
        print('  ✅ 性能优秀 (P95 < 100ms)')
    elif qdrant['p95'] < 500 and nebula['p95'] < 500:
        print('  ✅ 性能良好 (P95 < 500ms)')
    else:
        print('  ⚠️  需要优化')
PERFEOF

chmod +x "$PERF_SCRIPT"
echo "  ✅ 性能测试: $PERF_SCRIPT"

# ============================================================
# 7. 配置 Docker 网络
# ============================================================
echo ""
echo "6️⃣  Docker 配置"
echo "------------------------------------------------------------------------"

docker network create athena-knowledge-net 2>/dev/null && echo "  ✅ 创建网络: athena-knowledge-net" || echo "  ℹ️  网络已存在"

# ============================================================
# 8. 完成
# ============================================================
echo ""
echo "========================================================================"
echo "✅ 生产环境配置完成"
echo "========================================================================"
echo ""
echo "配置文件:"
echo "  环境变量: $ENV_FILE"
echo "  监控脚本: $MONITOR_SCRIPT"
echo "  备份脚本: $BACKUP_SCRIPT"
echo "  性能测试: $PERF_SCRIPT"
echo ""
echo "后续操作:"
echo "  1. 启动监控: $MONITOR_SCRIPT &"
echo "  2. 执行备份: $BACKUP_SCRIPT"
echo "  3. 性能测试: python3 $PERF_SCRIPT"
echo ""
echo "服务地址:"
echo "  - Qdrant: http://localhost:6333"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:19090"
echo ""
echo "========================================================================"
