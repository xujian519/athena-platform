#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Athena多模态文件系统使用示例
Example Usage of Athena Multimodal File System
"""

import requests
from core.async_main import async_main
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8088"

def test_multimodal_api() -> Any:
    """测试多模态文件系统API"""

    print("🌐 Athena多模态文件系统API测试")
    print("=" * 50)

    # 1. 获取服务信息
    print("\n1. 获取服务信息...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 服务: {data['service']}")
        print(f"   ✅ 版本: {data['version']}")
        print(f"   ✅ 状态: {data['status']}")
        print(f"   ✅ 端口: {data['port']}")
    else:
        print(f"   ❌ 错误: {response.status_code}")

    # 2. 健康检查
    print("\n2. 健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 状态: {data['status']}")
        print(f"   ✅ 数据库: {data['database']}")
        print(f"   ✅ 存储: {data['storage']}")
    else:
        print(f"   ❌ 错误: {response.status_code}")

    # 3. 获取文件列表
    print("\n3. 获取文件列表...")
    response = requests.get(f"{BASE_URL}/api/files/list")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 文件总数: {data['total']}")
        for file_info in data['files'][:3]:  # 显示前3个文件
            print(f"      - {file_info['original_filename']} ({file_info['file_type']}, {file_info['file_size']} bytes)")
    else:
        print(f"   ❌ 错误: {response.status_code}")

    # 4. 获取统计信息
    print("\n4. 获取统计信息...")
    response = requests.get(f"{BASE_URL}/api/stats")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 总文件数: {data['total_files']}")
        print(f"   ✅ 总大小: {data['total_size']} bytes")
        print(f"   ✅ 处理率: {data['processing_rate']:.1f}%")

        print("\n   按类型统计:")
        for type_stat in data['by_type']:
            print(f"      - {type_stat['type']}: {type_stat['count']} 个文件")
    else:
        print(f"   ❌ 错误: {response.status_code}")

    # 5. 示例：上传文件
    print("\n5. 文件上传示例...")
    print("   如需上传文件，请使用以下Python代码:")
    print("""
    import requests

    # 上传文件
    with open('example.pdf', 'rb') as f:
        files = {'file': f}
        data = {
            'tags': 'test,demo',
            'category': 'document'
        }
        response = requests.post(
            'http://localhost:8088/api/files/upload',
            files=files,
            data=data
        )

    if response.status_code == 200:
        result = response.json()
        print(f"上传成功！文件ID: {result['file_id']}")
    """)

    print("\n✅ API测试完成！")
    print("\n📖 更多信息:")
    print("   API文档: http://localhost:8088/docs")
    print("   服务地址: http://localhost:8088")

if __name__ == "__main__":
    test_multimodal_api()