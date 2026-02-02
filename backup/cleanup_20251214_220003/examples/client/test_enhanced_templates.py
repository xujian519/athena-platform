#!/usr/bin/env python3
"""
测试增强版提示词模板
Test Enhanced Prompt Templates
验证参数匹配是否正常
"""

import requests
import json
import time


def test_template_matching():
    """测试各种查询类型的模板匹配"""

    base_url = "http://localhost:8089"

    print("="*60)
    print("🧪 测试增强版提示词模板参数匹配")
    print("="*60)

    # 测试用例
    test_cases = [
        {
            "name": "专利新创性分析",
            "query_type": "novelty",
            "query": "请分析专利CN202312345678的新创性",
            "patent_info": {
                "patent_id": "CN202312345678",
                "title": "一种新型数据加密方法",
                "field": "信息安全"
            },
            "expected_params": ["patent_info", "query", "jurisdiction"]
        },
        {
            "name": "专利侵权分析",
            "query_type": "infringement",
            "query": "产品A是否侵犯专利B的专利权",
            "context": {
                "claims": "1. 一种加密方法，其特征在于...",
                "accused_product": "产品A采用了AES加密技术",
                "jurisdiction": "CN"
            },
            "expected_params": ["claims", "accused_product", "jurisdiction"]
        },
        {
            "name": "专利有效性评估",
            "query_type": "validity",
            "query": "评估专利的稳定性",
            "context": {
                "patent_text": "本发明涉及一种新技术...",
                "prior_art": ["现有技术1", "现有技术2"],
                "jurisdiction": "CN"
            },
            "expected_params": ["patent_text", "prior_art", "jurisdiction"]
        },
        {
            "name": "专利撰写指导",
            "query_type": "drafting",
            "query": "帮我撰写专利申请文件",
            "context": {
                "technical_disclosure": "本发明是一种创新技术...",
                "background_art": "现有技术存在...",
                "invention_points": ["创新点1", "创新点2"]
            },
            "expected_params": ["technical_disclosure", "background_art", "invention_points"]
        },
        {
            "name": "通用咨询",
            "query_type": "general",
            "query": "专利申请需要多长时间？",
            "context": {
                "patent_info": "关于发明专利申请"
            }
        }
    ]

    # 启动服务提示
    print("\n📌 请先启动增强版知识检索服务:")
    print("   cd services/yunpat-agent")
    print("   python3 enhanced_knowledge_retrieval.py")
    print("\n等待服务启动...")
    time.sleep(3)

    # 运行测试
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"📝 测试 {i}: {test_case['name']}")
        print(f"{'='*60}")

        # 准备请求数据
        request_data = {
            "query": test_case["query"],
            "query_type": test_case["query_type"],
            "patent_info": test_case.get("patent_info", {}),
            "context": test_case.get("context", {}),
            "user_id": "test_user"
        }

        try:
            # 发送请求
            response = requests.post(
                f"{base_url}/api/v1/knowledge/enhanced-retrieve",
                json=request_data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()

                print(f"✅ 请求成功")
                print(f"   查询ID: {result['query_id']}")
                print(f"   填充参数数量: {len(result['parameters_filled'])}")
                print(f"   缺失参数: {result['missing_parameters'] if result['missing_parameters'] else '无'}")

                # 显示部分提示词
                prompt = result['dynamic_prompt']
                print(f"\n📄 生成的提示词预览:")
                print("   " + "-"*50)
                preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
                print(f"   {preview}")
                print("   " + "-"*50)

                # 验证期望参数
                if test_case.get("expected_params"):
                    filled = set(result['parameters_filled'])
                    expected = set(test_case['expected_params'])
                    missing_expected = expected - filled

                    if missing_expected:
                        print(f"\n⚠️  缺少期望参数: {missing_expected}")
                    else:
                        print(f"\n✅ 所有期望参数已填充")

            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   错误信息: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务 (端口8089)")
            print("   请确保增强版知识检索服务正在运行")
            break
        except Exception as e:
            print(f"❌ 测试异常: {e}")

        # 测试间隔
        if i < len(test_cases):
            time.sleep(1)


def show_template_requirements():
    """显示模板参数要求"""

    print("\n" + "="*60)
    print("📋 模板参数要求说明")
    print("="*60)

    try:
        response = requests.get("http://localhost:8089/api/v1/templates/requirements", timeout=5)

        if response.status_code == 200:
            data = response.json()

            print("\n📝 可用模板:")
            for template in data['available_templates']:
                print(f"   • {template}")

            print("\n📌 参数要求:")
            for template, params in data['template_requirements'].items():
                print(f"\n{template}:")
                for param in params:
                    print(f"   - {param}")

    except:
        print("无法获取模板要求信息")


def demonstrate_customization():
    """演示模板自定义"""

    print("\n" + "="*60)
    print("🎨 模板自定义示例")
    print("="*60)

    # 自定义示例
    custom_request = {
        "template_name": "novelty",
        "custom_context": {
            "query": "分析这个区块链专利的新创性",
            "patent_info": {
                "title": "基于区块链的数据存储方法",
                "field": "区块链技术"
            },
            "jurisdiction": "CN",
            "technical_background": "区块链是分布式账本技术...",
            "custom_requirement": "特别关注技术实现细节"
        }
    }

    print("\n📝 自定义请求示例:")
    print(json.dumps(custom_request, ensure_ascii=False, indent=2))

    try:
        response = requests.post(
            "http://localhost:8089/api/v1/templates/customize",
            json=custom_request,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()

            print("\n✅ 自定义成功:")
            print(f"   模板: {result['template_name']}")
            print(f"   使用参数: {result['used_parameters']}")

            if result['suggestions']:
                print("\n💡 改进建议:")
                for suggestion in result['suggestions']:
                    print(f"   • {suggestion}")

            print("\n📄 自定义提示词预览:")
            print("   " + "-"*50)
            preview = result['customized_prompt'][:200] + "..." if len(result['customized_prompt']) > 200 else result['customized_prompt']
            print(f"   {preview}")
            print("   " + "-"*50)

    except Exception as e:
        print(f"❌ 自定义失败: {e}")


def main():
    """主函数"""
    print("🚀 增强版提示词模板测试")
    print("-" * 60)

    # 测试模板匹配
    test_template_matching()

    # 显示参数要求
    show_template_requirements()

    # 演示自定义
    demonstrate_customization()

    print("\n" + "="*60)
    print("💡 总结:")
    print("1. 增强版服务自动处理缺失参数")
    print("2. 为每个参数提供合理的默认值")
    print("3. 支持模板自定义和参数扩展")
    print("4. 提供参数验证和改进建议")
    print("="*60)


if __name__ == "__main__":
    main()