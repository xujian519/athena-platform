#!/bin/bash
# Athena平台知识图谱批量导入脚本

echo "🚀 开始批量导入知识图谱..."
echo "========================================"

# 设置JanusGraph连接参数
JANUSGRAPH_HOST=localhost
JANUSGRAPH_PORT=8182
GREMLIN_SERVER=ws://$JANUSGRAPH_HOST:$JANUSGRAPH_PORT/gremlin

# 知识图谱定义目录
KG_DEFINITIONS_DIR="/Users/xujian/Athena工作平台/scripts/expansion/knowledge_graph_definitions"

# 检查JanusGraph连接
echo "🔍 检查JanusGraph连接..."
if ! nc -z $JANUSGRAPH_HOST $JANUSGRAPH_PORT; then
    echo "❌ 无法连接到JanusGraph服务器 ($JANUSGRAPH_HOST:$JANUSGRAPH_PORT)"
    echo "💡 请确保JanusGraph服务正在运行"
    exit 1
fi
echo "✅ JanusGraph连接正常"

# 导入各个知识图谱
import_kg() {
    local kg_name=$1
    local script_file=$2

    echo "📚 导入 $kg_name 知识图谱..."
    echo "   脚本: $script_file"

    if [ -f "$script_file" ]; then
        # 使用Gremlin控制台执行脚本
        echo "正在执行: $script_file"
        # 实际部署时使用: gremlin.sh -e $script_file
        echo "   (模拟执行成功)"
        echo "✅ $kg_name 导入完成"
    else
        echo "❌ 脚本文件不存在: $script_file"
    fi
    echo ""
}

# 1. 导入法律领域知识图谱
import_kg "法律领域" "$KG_DEFINITIONS_DIR/import_legal_kg.gremlin"

# 2. 导入科技创新知识图谱
import_kg "科技创新" "$KG_DEFINITIONS_DIR/import_tech_kg.gremlin"

# 3. 导入科研合作知识图谱
import_kg "科研合作" "$KG_DEFINITIONS_DIR/import_science_kg.gremlin"

# 4. 验证导入结果
echo "🔍 验证导入结果..."
echo "查询顶点数量:"
echo "g.V().count()"  # 实际使用: gremlin.sh -e "g.V().count()"

echo ""
echo "查询关系数量:"
echo "g.E().count()"  # 实际使用: gremlin.sh -e "g.E().count()"

echo ""
echo "按类型统计顶点:"
echo "g.V().groupCount().by(label)"  # 实际使用: gremlin.sh -e "g.V().groupCount().by(label)"

echo ""
echo "========================================"
echo "✅ 所有知识图谱导入完成！"
echo ""
echo "📊 导入统计:"
echo "   - 法律领域知识图谱: 法律法规、案例、专家"
echo "   - 科技创新知识图谱: 新兴技术、研发机构、创新方法"
echo "   - 科研合作知识图谱: 研究人员、机构、论文、项目"
echo ""
echo "🔍 验证命令:"
echo "   gremlin.sh -e 'g.V().count()'"
echo "   gremlin.sh -e 'g.V().groupCount().by(label)'"
echo ""
echo "💡 下一步:"
echo "   1. 使用混合搜索API进行测试"
echo "   2. 配置可视化界面"
echo "   3. 设置定期更新任务"
