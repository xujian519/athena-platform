#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Ollama响应格式
"""

import requests
import json

def test_ollama_response():
    """测试ollama响应"""
    ollama_url = "http://localhost:11434/api"
    model_name = "qwen:7b"

    # 测试简单的JSON响应
    system_prompt = """你是一个数据分析助手。请用纯JSON格式回答，不要任何额外的文字说明。"""

    prompt = """
请分析以下数据：
列名：档案号, 申请号, 专利名称, 案源人, 代理人, 类型, 申请日, 法律状态

请返回JSON格式的列映射：
{
    "档案号": "archive_number",
    "申请号": "application_number",
    "专利名称": "patent_title",
    "案源人": "client_name",
    "代理人": "agent",
    "类型": "patent_type",
    "申请日": "filing_date",
    "法律状态": "legal_status"
}

请直接返回上面的JSON，不要添加任何其他文字。
"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }

    try:
        print("🔍 测试Ollama响应...")
        response = requests.post(f"{ollama_url}/generate", json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("response", "")

            print("\n📝 AI原始响应:")
            print(ai_response)
            print("\n" + "="*60)

            # 尝试解析JSON
            json_part = ai_response.strip()
            if "```json" in json_part:
                json_part = json_part.split("```json")[1].split("```")[0].strip()
            elif "```" in json_part:
                json_part = json_part.split("```")[1].strip()

            # 尝试查找JSON对象
            start_idx = json_part.find('{')
            end_idx = json_part.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_part = json_part[start_idx:end_idx]

            print("\n🔧 提取的JSON部分:")
            print(json_part)
            print("\n" + "="*60)

            try:
                parsed = json.loads(json_part)
                print("\n✅ JSON解析成功:")
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
                return True
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON解析失败: {e}")
                print(f"错误位置: 第{e.lineno}行，第{e.colno}列")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_ollama_response()