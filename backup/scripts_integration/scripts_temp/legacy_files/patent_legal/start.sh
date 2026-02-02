#!/bin/bash
# 专利法律法规向量和知识图谱构建快速启动脚本
# Patent Legal Vector and KG Construction Quick Start Script

echo "🚀 专利法律法规向量和知识图谱构建"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi

# 安装必要的库
echo "📦 安装必要的Python库..."
pip3 install sentence-transformers numpy scikit-learn aiofiles python-docx PyPDF2 networkx qdrant-client gremlinpython

# 检查服务
echo "🔍 检查服务状态..."

# 检查Qdrant
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    echo "✅ Qdrant服务正常"
else
    echo "⚠️ Qdrant服务未运行，请先启动Qdrant"
fi

# 检查JanusGraph
if curl -s http://localhost:8182 > /dev/null 2>&1; then
    echo "✅ JanusGraph服务正常"
else
    echo "⚠️ JanusGraph服务未运行，请先启动JanusGraph"
fi

# 执行完整流水线
echo "🏃 执行完整流水线..."
cd /Users/xujian/Athena工作平台
python3 scripts/patent_legal/run_full_pipeline.py

echo "✅ 执行完成！"