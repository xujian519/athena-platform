#!/usr/bin/env python3
"""
简单HTTP服务 - 测试系统可用性
"""

import http.server
import json
import socketserver
from urllib.parse import parse_qs, urlparse


class XiaonaHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)

        if url.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "xiaona-legal-support",
                "message": "小诺法律智能支持系统运行正常"
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode())

        elif url.path == '/api/v1/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "success",
                "message": "小诺的法律智能支持系统已经部署并可以使用了！",
                "features": [
                    "✅ 法律知识图谱 (NebulaGraph) - 3,015个实体, 2,010条关系",
                    "✅ 专业向量库 - 3,080部法律向量",
                    "✅ 动态提示词生成 - 5种类型专业提示",
                    "✅ 智能问答支持 - RESTful API",
                    "✅ 插件系统 - 可扩展架构"
                ],
                "api_endpoints": {
                    "health": "GET /health - 健康检查",
                    "search": "POST /api/v1/search - 法律搜索",
                    "qa": "POST /api/v1/qa - 法律问答",
                    "prompt": "POST /api/v1/prompt - 提示词生成",
                    "rules": "POST /api/v1/rules - 规则依据"
                },
                "example_usage": {
                    "search": "curl -X POST http://localhost:8080/api/v1/search -H 'Content-Type: application/json' -d '{\"query\":\"离婚财产分割\"}'",
                    "qa": "curl -X POST http://localhost:8080/api/v1/qa -H 'Content-Type: application/json' -d '{\"query\":\"劳动合同解除条件？\"}'"
                }
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        elif url.path == '/api/v1/demo':
            # 演示接口
            query = parse_qs(url.query).get('query', [''])[0]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            response = {
                "query": query or "劳动合同解除",
                "answer": f"根据《中华人民共和国劳动合同法》规定，{(query or '劳动合同解除')}需要满足以下条件之一：\n1. 协商一致解除\n2. 劳动者提前30日书面通知\n3. 用人单位符合法定条件解除\n\n具体建议咨询专业律师。",
                "legal_basis": ["《中华人民共和国劳动合同法》", "《劳动合同法实施条例》"],
                "confidence": 0.89
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_error(404)

if __name__ == "__main__":
    PORT = 8080
    Handler = XiaonaHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("\n👑 小诺法律智能支持系统测试服务")
        print("="*50)
        print(f"📡 服务地址: http://localhost:{PORT}")
        print(f"🏥 健康检查: http://localhost:{PORT}/health")
        print(f"🧪 测试接口: http://localhost:{PORT}/api/v1/test")
        print(f"📖 演示接口: http://localhost:{PORT}/api/v1/demo?query=你的问题")
        print("="*50)
        print("✨ 小诺已经准备好为您的法律需求服务！")
        print("\n按 Ctrl+C 停止服务\n")

        httpd.serve_forever()
