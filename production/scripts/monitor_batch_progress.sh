#!/bin/bash
# 监控批处理进度的脚本

LOG_FILE="/Users/xujian/Athena工作平台/logs/doc_batch_processing.log"
PID_FILE="/tmp/doc_batch_processing.pid"

echo "============================================================"
echo "📊 专利无效决定批处理进度监控"
echo "============================================================"
echo ""

# 检查进程是否运行
if ps -p 55379 > /dev/null 2>&1; then
    echo "✅ 批处理进程运行中 (PID: 55379)"
else
    echo "⚠️ 批处理进程未运行"
fi

echo ""
echo "------------------------------------------------------------"
echo "📈 当前进度"
echo "------------------------------------------------------------"

# 从日志中提取最新的进度信息
echo ""
tail -3 "$LOG_FILE" | grep -E "📄 进度:|处理文件:|解析完成:|保存成功:|向量保存:|知识图谱保存成功:"

echo ""
echo "------------------------------------------------------------"
echo "📊 统计信息"
echo "------------------------------------------------------------"

# 统计已处理的文件数
PROCESSED=$(grep "✅ 完成.*个向量保存" "$LOG_FILE" | wc -l | tr -d ' ')
echo "已处理文件: $PROCESSED"

# 统计PostgreSQL记录数
PG_COUNT=$(psql -h 127.0.0.1 -p 5432 -U postgres -d patent_legal_db -t -c "SELECT COUNT(*) FROM patent_invalid_decisions;" 2>/dev/null | tr -d ' ')
echo "PostgreSQL记录: $PG_COUNT"

# 统计Qdrant向量数
QDRANT_COUNT=$(curl -s http://localhost:6333/collections/patent_decisions | jq -r '.result.points_count // 0' 2>/dev/null)
echo "Qdrant向量数: $QDRANT_COUNT"

# 统计NebulaGraph顶点和边
VERTEX_COUNT=$(PGPASSWORD=nebula nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula -e "USE patent_rules; MATCH (v) RETURN count(v) AS cnt;" 2>/dev/null | grep "^[0-9]" | tr -d ' ')
EDGE_COUNT=$(PGPASSWORD=nebula nebula-console -addr 127.0.0.1 -port 9669 -u root -p nebula -e "USE patent_rules; MATCH ()-[e]->() RETURN count(e) AS cnt;" 2>/dev/null | grep "^[0-9]" | tr -d ' ')
echo "NebulaGraph顶点: $VERTEX_COUNT"
echo "NebulaGraph边: $EDGE_COUNT"

echo ""
echo "------------------------------------------------------------"
echo "⏱️  预估剩余时间"
echo "------------------------------------------------------------"

# 计算处理速度和预估时间
if [ "$PROCESSED" -gt 10 ]; then
    # 获取日志文件的起始和当前时间
    START_TIME=$(stat -f "%Sm" -t "%s" "$LOG_FILE")
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    if [ "$ELAPSED" -gt 0 ]; then
        SPEED=$((PROCESSED * 60 / ELAPSED))
        REMAINING=$((31790 - PROCESSED))
        ESTIMATED_MINUTES=$((REMAINING * 60 / SPEED / 60))

        echo "处理速度: 约 $SPEED 文件/分钟"
        echo "剩余文件: $REMAINING"
        echo "预估时间: 约 $ESTIMATED_MINUTES 分钟"
    fi
fi

echo ""
echo "============================================================"
echo "💡 提示: 使用 'tail -f $LOG_FILE' 查看实时日志"
echo "============================================================"
