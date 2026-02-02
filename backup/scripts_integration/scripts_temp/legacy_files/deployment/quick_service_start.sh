#!/bin/bash
# 快速服务启动脚本
# Quick Service Startup

echo "🚀 快速启动Athena核心服务..."

# 创建必要的目录
mkdir -p logs
mkdir -p .pids

# 启动向量服务
echo "启动向量服务 (端口8082)..."
cd services/ai-models/pqai-integration
if [ -f "main.py" ]; then
    nohup python3 main.py > ../../logs/vector-service.log 2>&1 &
    echo $! > ../../.pids/vector-service.pid
    echo "✅ 向量服务已启动"
else
    echo "⚠️ 向量服务文件不存在"
fi

cd ../..

# 启动专利分析服务（简化版）
echo "启动专利分析服务 (端口8081)..."
if [ ! -d "services/patent-analysis" ]; then
    mkdir -p services/patent-analysis
fi

cd services/patent-analysis
if [ ! -f "main.py" ]; then
    cat > main.py << 'EOF'
#!/usr/bin/env python3
# 专利分析服务简化版
from flask import Flask, jsonify, request
import sys
import os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "patent-analysis"})

@app.route('/api/analyze', methods=['POST'])
def analyze_patent():
    data = request.get_json()
    patent_id = data.get('patent_id')

    # 简单的模拟分析
    result = {
        "patent_id": patent_id,
        "innovation_score": 0.85,
        "technology_category": "AI/Machine Learning",
        "market_potential": "High",
        "analysis_timestamp": "2025-12-10T23:00:00Z"
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
EOF
fi

nohup python3 main.py > ../../logs/patent-analysis.log 2>&1 &
echo $! > ../../.pids/patent-analysis.pid
echo "✅ 专利分析服务已启动"

cd ../..

# 检查服务状态
sleep 3
echo ""
echo "🔍 检查服务状态:"
echo "8080端口 (专利搜索): $(lsof -i :8080 | wc -l) 个进程"
echo "8081端口 (专利分析): $(lsof -i :8081 | wc -l) 个进程"
echo "8082端口 (向量服务): $(lsof -i :8082 | wc -l) 个进程"

echo ""
echo "📁 日志位置:"
echo "- 向量服务: logs/vector-service.log"
echo "- 专利分析: logs/patent-analysis.log"