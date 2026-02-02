#!/bin/bash
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
