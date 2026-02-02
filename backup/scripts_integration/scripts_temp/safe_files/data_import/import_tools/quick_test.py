#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试知识图谱API服务
"""

import requests
import json

# 测试API服务
print("🔧 测试知识图谱API服务...")
print("=" * 50)

# 1. 测试根路径
try:
    response = requests.get("http://localhost:8080/")
    print(f"\n1. 根路径测试: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
except Exception as e:
    print(f"错误: {e}")

# 2. 测试搜索功能（使用实际存在的路径）
print("\n2. 测试专利搜索...")
try:
    response = requests.get(
        "http://localhost:8080/api/patent/search",
        params={
            "query": "深度学习",
            "limit": 5
        }
    )
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"搜索结果: {len(result.get('results', []))} 条")
    else:
        print(f"响应: {response.text}")
except Exception as e:
    print(f"错误: {e}")

# 3. 列出可用的API路径
print("\n3. 尝试其他常见路径...")
paths = [
    "/api/v1",
    "/api/v1/health",
    "/health",
    "/docs",
    "/redoc"
]

for path in paths:
    try:
        response = requests.get(f"http://localhost:8080{path}", timeout=2)
        print(f"{path}: {response.status_code}")
    except:
        print(f"{path}: 连接超时")

# 4. 显示API文档地址
print("\n4. 访问API文档:")
print("   Swagger UI: http://localhost:8080/docs")
print("   ReDoc: http://localhost:8080/redoc")