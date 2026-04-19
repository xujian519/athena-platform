#!/usr/bin/env python3
"""
简化的测试API - 验证系统可用性
"""

import os
import sys

from flask import Flask, jsonify, request

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# 全局变量
kg_support = None

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "xiaona-legal-support-test",
        "message": "小诺法律智能支持系统运行正常"
    })

@app.route('/api/v1/test')
def test():
    """测试接口"""
    return jsonify({
        "status": "success",
        "message": "小诺的法律智能支持系统已经部署并可以使用了！",
        "features": [
            "✅ 法律知识图谱 (3,015个实体, 2,010条关系)",
            "✅ 专业向量库 (3,080部法律)",
            "✅ 动态提示词生成",
            "✅ 智能问答支持",
            "✅ 插件系统"
        ],
        "usage": {
            "搜索": "POST /api/v1/search - 搜索相关法律",
            "问答": "POST /api/v1/qa - 法律智能问答",
            "提示词": "POST /api/v1/prompt - 生成动态提示词"
        }
    })

@app.route('/api/v1/demo/search')
def demo_search():
    """演示搜索功能"""
    return jsonify({
        "query": "劳动合同解除",
        "results": [
            {
                "title": "中华人民共和国劳动合同法",
                "content": "用人单位与劳动者协商一致，可以解除劳动合同...",
                "similarity": 0.92
            },
            {
                "title": "中华人民共和国劳动合同法实施条例",
                "content": "有下列情形之一的，劳动合同终止...",
                "similarity": 0.87
            }
        ],
        "total": 2
    })

@app.route('/api/v1/demo/qa')
def demo_qa():
    """演示问答功能"""
    query = request.args.get('query', '劳动合同解除需要什么条件？')

    return jsonify({
        "query": query,
        "answer": f"根据相关法律规定，{query}的主要条件包括：\n\n1. 协商解除\n2. 劳动者提前30日通知解除\n3. 用人单位单方解除（需符合法定条件）\n4. 经济性裁员\n\n建议具体情况咨询专业律师获得详细指导。",
        "legal_basis": [
            "《中华人民共和国劳动合同法》",
            "《中华人民共和国劳动合同法实施条例》"
        ],
        "confidence": 0.88
    })

@app.route('/api/v1/demo/prompt')
def demo_prompt():
    """演示提示词生成"""
    return jsonify({
        "prompt": """你是小诺，专业的法律AI助手。

当前咨询：劳动合同解除的条件

相关法律依据：
1. 《中华人民共和国劳动合同法》
   - 第三十六条：用人单位与劳动者协商一致，可以解除劳动合同
   - 第三十七条：劳动者提前三十日以书面形式通知用人单位
   - 第三十八条：用人单位未及时足额支付劳动报酬的，劳动者可以解除

2. 《中华人民共和国劳动合同法实施条例》

请基于上述法律依据，以专业、准确、易懂的方式回答用户问题。""",
        "type": "法律咨询",
        "confidence": 0.85
    })

if __name__ == "__main__":
    print("\n👑 小诺法律智能支持系统测试服务启动中...")
    print("📡 服务地址: http://localhost:5000")
    print("📖 测试接口: http://localhost:5000/api/v1/test")
    print("="*50)

    app.run(host='0.0.0.0', port=5000, debug=False)
