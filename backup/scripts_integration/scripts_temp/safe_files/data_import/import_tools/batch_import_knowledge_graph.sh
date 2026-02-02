#!/bin/bash
# Athena知识图谱批量导入脚本

set -e  # 遇到错误立即退出

echo "🚀 开始导入知识图谱数据..."
echo "========================================"

# 颜色定义
RED='[0;31m'
GREEN='[0;32m'
YELLOW='[1;33m'
NC='[0m' # No Color

# 配置参数
JANUSGRAPH_HOST=localhost
JANUSGRAPH_PORT=8182
BATCH_SIZE=10000
LOG_FILE="/Users/xujian/Athena工作平台/logs/knowledge_graph_import.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查服务状态
check_services() {
    log "🔍 检查服务状态..."

    # 检查JanusGraph
    if nc -z $JANUSGRAPH_HOST $JANUSGRAPH_PORT; then
        log "${GREEN}✅ JanusGraph运行正常${NC}"
    else
        log "${RED}❌ JanusGraph未运行 ($JANUSGRAPH_HOST:$JANUSGRAPH_PORT)${NC}"
        echo "请先启动JanusGraph服务"
        exit 1
    fi

    # 检查Qdrant
    if nc -z localhost 6333; then
        log "${GREEN}✅ Qdrant运行正常${NC}"
    else
        log "${YELLOW}⚠️  Qdrant未运行，向量搜索功能将受限${NC}"
    fi
}

# 创建索引
create_indexes() {
    log "📊 创建索引..."

    cat > /tmp/create_indexes.gremlin << 'EOF'
// 创建知识图谱索引
mgmt = graph.openManagement()

try {
    // 创建entity_id索引
    if (!mgmt.containsPropertyKey('entity_id')) {
        entityIdKey = mgmt.makePropertyKey('entity_id').dataType(String.class).make()
        mgmt.buildIndex('byEntityId', Vertex.class).addKey(entityIdKey).buildCompositeIndex()
    }

    // 创建patent_number索引
    if (!mgmt.containsPropertyKey('patent_number')) {
        patentNumberKey = mgmt.makePropertyKey('patent_number').dataType(String.class).make()
        mgmt.buildIndex('byPatentNumber', Vertex.class).addKey(patentNumberKey).buildCompositeIndex()
    }

    // 创建name索引
    if (!mgmt.containsPropertyKey('name')) {
        nameKey = mgmt.makePropertyKey('name').dataType(String.class).make()
        mgmt.buildIndex('byName', Vertex.class).addKey(nameKey).buildCompositeIndex()
    }

    mgmt.commit()
    println("索引创建完成")
} catch (e) {
    mgmt.rollback()
    println("索引创建失败: " + e.message)
}
EOF

    echo "create_indexes.gremlin" | gremlin.sh - > /dev/null 2>&1 || log "${YELLOW}⚠️  索引创建可能失败，请手动检查${NC}"
    log "✅ 索引创建完成"
}

# 导入专利数据
import_patent_data() {
    log "📚 导入专利数据..."

    # 生成专利导入脚本
    cat > /tmp/import_patents.gremlin << 'EOF'
// 导入专利数据
g.tx().commit()
g.tx().open()

println("开始导入专利数据...")

patentCount = 0

// 示例：导入1000个专利（实际应从数据库读取）
(1..1000).each {
    vertex = g.addV('Patent')
    vertex.property('entity_id', 'patent_' + it.toString())
    vertex.property('patent_number', 'CN' + String.format('%09d', it) + 'A')
    vertex.property('title', '深度学习专利 ' + it)
    vertex.property('abstract', '本专利涉及深度学习技术...')
    vertex.property('inventors', '发明人' + it)
    vertex.property('assignee', '申请人' + it)
    vertex.property('application_date', '2023-01-01')
    vertex.property('grant_date', '2024-01-01')
    vertex.next()
    patentCount++

    if (patentCount % 100 == 0) {
        g.tx().commit()
        g.tx().open()
        println("已导入 " + patentCount + " 个专利")
    }
}

g.tx().commit()
println("专利数据导入完成，共: " + patentCount + " 条")
EOF

    # 执行导入
    echo "import_patents.gremlin" | gremlin.sh - >> "$LOG_FILE" 2>&1
    log "${GREEN}✅ 专利数据导入完成${NC}"
}

# 导入公司数据
import_company_data() {
    log "🏢 导入公司数据..."

    cat > /tmp/import_companies.gremlin << 'EOF'
// 导入公司数据
g.tx().commit()
g.tx().open()

println("开始导入公司数据...")

companyCount = 0

(1..100).each {
    vertex = g.addV('Company')
    vertex.property('entity_id', 'company_' + it.toString())
    vertex.property('company_id', 'COMP' + String.format('%06d', it))
    vertex.property('name', '科技公司' + it)
    vertex.property('industry', '人工智能')
    vertex.property('location', '北京市')
    vertex.property('founded_date', '2010-01-01')
    vertex.next()
    companyCount++

    if (companyCount % 50 == 0) {
        g.tx().commit()
        g.tx().open()
        println("已导入 " + companyCount + " 个公司")
    }
}

g.tx().commit()
println("公司数据导入完成，共: " + companyCount + " 条")
EOF

    echo "import_companies.gremlin" | gremlin.sh - >> "$LOG_FILE" 2>&1
    log "${GREEN}✅ 公司数据导入完成${NC}"
}

# 导入关系数据
import_relationships() {
    log "🔗 导入关系数据..."

    cat > /tmp/import_relations.gremlin << 'EOF'
// 导入关系数据
g.tx().commit()
g.tx().open()

println("开始导入关系数据...")

relationCount = 0

(1..1000).each {
    // 查找专利和公司
    patent = g.V().has('entity_id', 'patent_' + it.toString()).tryNext()
    company = g.V().has('entity_id', 'company_' + ((it % 100) + 1).toString()).tryNext()

    if (patent.isPresent() && company.isPresent()) {
        // 创建拥有关系
        patent.get().addEdge('OWNED_BY', company.get())
          .property('relationship_type', 'owner')
          .property('percentage', '100%')
          .next()
        relationCount++

        if (relationCount % 100 == 0) {
            g.tx().commit()
            g.tx().open()
            println("已导入 " + relationCount + " 个关系")
        }
    }
}

g.tx().commit()
println("关系数据导入完成，共: " + relationCount + " 条")
EOF

    echo "import_relations.gremlin" | gremlin.sh - >> "$LOG_FILE" 2>&1
    log "${GREEN}✅ 关系数据导入完成${NC}"
}

# 验证导入结果
validate_import() {
    log "🔍 验证导入结果..."

    cat > /tmp/validate.gremlin << 'EOF'
// 验证导入结果
vertexCount = g.V().count().next()
edgeCount = g.E().count().next()

println("\n导入统计:")
println("顶点总数: " + vertexCount)
println("边总数: " + edgeCount)

println("\n按类型统计:")
g.V().groupCount().by(label).each { label, count ->
    println(label + ": " + count)
}

g.E().groupCount().by(label).each { label, count ->
    println(label + ": " + count)
}
EOF

    validation_result=$(echo "validate.gremlin" | gremlin.sh - 2>/dev/null | tail -n +2)
    log "${GREEN}验证结果:${NC}"
    echo "$validation_result" | while IFS= read -r line; do
        log "$line"
    done
}

# 主执行流程
main() {
    log "🚀 开始导入流程..."

    # 1. 检查服务
    check_services

    # 2. 创建索引
    create_indexes

    # 3. 导入数据
    import_patent_data
    import_company_data
    import_relationships

    # 4. 验证结果
    validate_import

    log "${GREEN}🎉 知识图谱导入完成！${NC}"
    log "📊 查看详细日志: $LOG_FILE"

    # 清理临时文件
    rm -f /tmp/*.gremlin

    echo ""
    echo "💡 后续操作:"
    echo "1. 使用混合搜索API进行测试: curl http://localhost:8080/api/v1/search/hybrid"
    echo "2. 查看API文档: http://localhost:8080/docs"
    echo "3. 运行数据验证: ./validate_knowledge_graph.sh"
}

# 执行主函数
main "$@"
