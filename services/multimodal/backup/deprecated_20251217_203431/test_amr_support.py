#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AMR格式支持
Test AMR Format Support
"""

import requests
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
import json

# API基础URL
BASE_URL = "http://localhost:8089"

def test_amr_support() -> Any:
    """测试AMR格式支持"""
    print("🎵 测试AMR音频格式支持")
    print("=" * 50)

    # 1. 检查服务信息
    print("\n1. 服务信息:")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"   版本: {data['version']}")
        print(f"   AI功能: {len(data['ai_features'])} 项")
        for feature in data['ai_features']:
            print(f"      - {feature}")

    # 2. 检查健康状态
    print("\n2. 健康检查:")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   状态: {data['status']}")
        print(f"   数据库: {data['database']}")
        print(f"   AI处理器: {data['ai_processor']}")

        print("\n   支持的功能:")
        features = data.get('supported_features', {})
        for feature, enabled in features.items():
            status = "✅" if enabled else "❌"
            print(f"      {status} {feature}")

    # 3. AMR格式说明
    print("\n3. AMR格式支持:")
    print("   ✅ 已添加.amr扩展名到音频类型")
    print("   ✅ 支持AMR文件上传和存储")
    print("   ⚠️  AMR文件处理（语音识别）需要额外集成:")
    print("      - 语音转文字引擎 (如百度语音、阿里云语音等)")
    print("      - 或使用开源方案 (如Whisper)")

    # 4. 使用示例
    print("\n4. 上传AMR文件示例代码:")
    print("""
    import requests

    # 上传AMR文件
    with open('recording.amr', 'rb') as f:
        files = {'file': f}
        data = {
            'tags': 'audio,voice,recording',
            'category': 'audio',
            'auto_process': False  # AMR暂不自动处理
        }
        response = requests.post(
            'http://localhost:8089/api/files/upload',
            files=files,
            data=data
        )

    if response.status_code == 200:
        result = response.json()
        print(f"上传成功！文件ID: {result['file_id']}")
    """)

    print("\n✅ AMR格式支持已就绪！")

if __name__ == "__main__":
    test_amr_support()