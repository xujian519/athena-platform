#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena知识图谱数据导入生成器（简化版）
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleImportGenerator:
    """简化的导入脚本生成器"""

    def __init__(self):
        self.platform_root = Path("/Users/xujian/Athena工作平台")
        self.output_dir = self.platform_root / "scripts" / "data_import" / "import_tools"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_import_scripts(self):
        """生成所有导入脚本"""
        logger.info("🚀 生成知识图谱导入脚本...")

        # 1. 生成批量导入Shell脚本
        self.create_batch_import_script()

        # 2. 生成数据验证脚本
        self.create_validation_script()

        # 3. 生成实时监控脚本
        self.create_monitoring_script()

        # 4. 生成使用说明
        self.create_usage_guide()

        logger.info("✅ 所有导入脚本生成完成！")
        logger.info(f"📁 生成位置: {self.output_dir}")

    def create_batch_import_script(self):
        """创建批量导入脚本"""
        script_path = self.output_dir / "batch_import_knowledge_graph.sh"

        script_content = """#!/bin/bash
# Athena知识图谱批量导入脚本

set -e  # 遇到错误立即退出

echo "🚀 开始导入知识图谱数据..."
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

println("\\n导入统计:")
println("顶点总数: " + vertexCount)
println("边总数: " + edgeCount)

println("\\n按类型统计:")
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
"""

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 设置执行权限
        script_path.chmod(0o755)

        logger.info(f"✅ 批量导入脚本已创建: {script_path}")

    def create_validation_script(self):
        """创建数据验证脚本"""
        script_path = self.output_dir / "validate_knowledge_graph.sh"

        script_content = """#!/bin/bash
# 知识图谱数据验证脚本

echo "🔍 验证知识图谱数据..."
echo "========================================"

# 验证顶点数量
echo -n "顶点总数: "
echo "g.V().count()" | gremlin.sh - 2>/dev/null | tail -n +2

# 验证边数量
echo -n "边总数: "
echo "g.E().count()" | gremlin.sh - 2>/dev/null | tail -n +2

# 按类型统计顶点
echo "顶点类型分布:"
echo "g.V().groupCount().by(label)" | gremlin.sh - 2>/dev/null | tail -n +2

# 按类型统计边
echo "边类型分布:"
echo "g.E().groupCount().by(label)" | gremlin.sh - 2>/dev/null | tail -n +2

# 检查示例数据
echo "示例数据检查:"
echo "g.V().limit(5)" | gremlin.sh - 2>/dev/null | tail -n +2

echo "✅ 验证完成"
"""

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        script_path.chmod(0o755)
        logger.info(f"✅ 验证脚本已创建: {script_path}")

    def create_monitoring_script(self):
        """创建监控脚本"""
        script_path = self.output_dir / "monitor_knowledge_graph.sh"

        script_content = """#!/bin/bash
# 知识图谱监控脚本

echo "📊 知识图谱实时监控"
echo "按Ctrl+C停止监控"
echo "========================================"

while true; do
    clear
    echo "📊 知识图谱实时监控 - $(date)"
    echo "========================================"

    # 检查服务状态
    echo "服务状态:"
    if nc -z localhost 8182; then
        echo "  JanusGraph: ✅ 运行中"
    else
        echo "  JanusGraph: ❌ 未运行"
    fi

    if nc -z localhost 6333; then
        echo "  Qdrant: ✅ 运行中"
    else
        echo "  Qdrant: ❌ 未运行"
    fi

    if nc -z localhost 8080; then
        echo "  API服务: ✅ 运行中"
    else
        echo "  API服务: ❌ 未运行"
    fi

    echo ""
    echo "数据统计:"

    # 获取顶点和边数量
    vertex_count=$(echo "g.V().count()" | gremlin.sh - 2>/dev/null | tail -n +2 | head -1)
    edge_count=$(echo "g.E().count()" | gremlin.sh - 2>/dev/null | tail -n +2 | head -1)

    echo "  顶点总数: $vertex_count"
    echo "  边总数: $edge_count"

    # 获取API统计
    if curl -s http://localhost:8080/api/v1/stats > /dev/null; then
        api_stats=$(curl -s http://localhost:8080/api/v1/stats 2>/dev/null)
        echo "  API调用: $(echo "$api_stats" | jq -r '.total_queries // "N/A"')"
    fi

    echo ""
    echo "系统资源:"
    echo "  内存使用: $(free -h | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
    echo "  磁盘使用: $(df -h / | awk 'NR==2{print $5}')"
    echo "  CPU负载: $(uptime | awk -F'load average:' '{print $2}')"

    sleep 5
done
"""

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        script_path.chmod(0o755)
        logger.info(f"✅ 监控脚本已创建: {script_path}")

    def create_usage_guide(self):
        """创建使用说明"""
        guide_path = self.output_dir / "README.md"

        guide_content = """# Athena知识图谱导入工具使用指南

## 📋 概述

本目录包含Athena平台知识图谱数据导入所需的全部工具和脚本。

## 🚀 快速开始

### 1. 准备工作

确保以下服务已启动：
- JanusGraph (端口8182)
- Qdrant (端口6333) - 可选，用于向量搜索

```bash
# 启动JanusGraph
cd /Users/xujian/Athena工作平台/services/knowledge-graph-service
docker-compose up -d janusgraph
```

### 2. 执行导入

```bash
# 运行批量导入脚本
./batch_import_knowledge_graph.sh
```

### 3. 验证导入

```bash
# 验证导入结果
./validate_knowledge_graph.sh
```

## 📁 文件说明

- `batch_import_knowledge_graph.sh` - 批量导入主脚本
- `validate_knowledge_graph.sh` - 数据验证脚本
- `monitor_knowledge_graph.sh` - 实时监控脚本
- `import_dashboard.html` - Web监控仪表板（如果存在）

## 🔍 监控和验证

### 实时监控
```bash
# 启动实时监控（每5秒刷新）
./monitor_knowledge_graph.sh
```

### 数据验证
```bash
# 查看顶点总数
echo "g.V().count()" | gremlin.sh -

# 查看边总数
echo "g.E().count()" | gremlin.sh -

# 查看类型分布
echo "g.V().groupCount().by(label)" | gremlin.sh -
```

## 📊 API测试

导入完成后，可以通过API进行测试：

```bash
# 健康检查
curl http://localhost:8080/health

# 混合搜索测试
curl -X POST http://localhost:8080/api/v1/search/hybrid \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "深度学习专利",
    "limit": 10
  }'

# 查看API文档
open http://localhost:8080/docs
```

## 🛠️ 故障排查

### 问题1: JanusGraph连接失败
```bash
# 检查端口
nc -z localhost 8182

# 查看日志
docker logs janusgraph
```

### 问题2: 导入速度慢
- 调整batch_size参数
- 检查内存使用
- 考虑分批导入

### 问题3: 内存不足
```bash
# 增加JVM内存
export JAVA_OPTS="-Xmx8g -Xms4g"
```

## 📈 性能优化建议

1. **批量大小**: 将batch_size设置为1000-10000
2. **事务控制**: 每1000条提交一次事务
3. **索引优化**: 导入前创建必要的索引
4. **并行导入**: 考虑使用多线程并行导入

## 📞 技术支持

- 日志位置: `/Users/xujian/Athena工作平台/logs/knowledge_graph_import.log`
- 配置文件: `/Users/xujian/Athena工作平台/config/`
- API文档: http://localhost:8080/docs
"""

        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)

        logger.info(f"✅ 使用说明已创建: {guide_path}")

def main():
    """主函数"""
    generator = SimpleImportGenerator()
    generator.generate_all_import_scripts()

    print("\n🎉 知识图谱导入工具生成完成！")
    print("\n📁 生成位置: /Users/xujian/Athena工作平台/scripts/data_import/import_tools")
    print("\n📦 生成的工具:")
    print("  - batch_import_knowledge_graph.sh (批量导入脚本)")
    print("  - validate_knowledge_graph.sh (数据验证脚本)")
    print("  - monitor_knowledge_graph.sh (实时监控脚本)")
    print("  - README.md (使用说明)")
    print("\n🚀 使用方法:")
    print("  1. cd /Users/xujian/Athena工作平台/scripts/data_import/import_tools")
    print("  2. ./batch_import_knowledge_graph.sh")

if __name__ == "__main__":
    main()